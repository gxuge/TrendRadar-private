# coding=utf-8
"""
报告生成模块

提供报告数据准备和 HTML 生成功能：
- prepare_report_data: 准备报告数据
- generate_html_report: 生成 HTML 报告
"""

from pathlib import Path
from typing import Dict, List, Optional, Callable
import re


def _normalize_title(title: str) -> str:
    """Normalize title for fuzzy clustering."""
    if not title:
        return ""
    t = title.lower()
    # keep CJK, letters and numbers, replace others with space
    t = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", t)
    return " ".join(t.split())


def _title_ngrams(normalized_title: str) -> set:
    """Character-level bi-grams + uni-grams for mixed Chinese/English headlines."""
    compact = normalized_title.replace(" ", "")
    if not compact:
        return set()
    grams = set()
    for i in range(len(compact)):
        grams.add(compact[i])
        if i + 1 < len(compact):
            grams.add(compact[i:i + 2])
    return grams


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _title_score(title_data: Dict) -> float:
    """Simple hotness score for choosing cluster representative."""
    count = title_data.get("count", 1) or 1
    ranks = title_data.get("ranks", []) or []
    min_rank = min(ranks) if ranks else 99
    rank_bonus = max(0, 15 - min(min_rank, 15))
    new_bonus = 2 if title_data.get("is_new", False) else 0
    return count * 2 + rank_bonus + new_bonus


def _source_authority_weight(source_name: str) -> float:
    """Heuristic source authority weight (0~1)."""
    if not source_name:
        return 0.45
    s = source_name.lower()
    high = (
        "reuters", "ap ", "associated press", "wsj", "wall street journal",
        "ft", "financial times", "economist", "bloomberg", "cnbc", "npr",
        "new york times", "washington post", "hacker news",
        "财联社", "华尔街见闻", "澎湃", "新华社", "人民日报", "经济观察"
    )
    mid = (
        "cnn", "fox", "the verge", "techcrunch", "yahoo", "知乎", "微博", "百度"
    )
    if any(k in s for k in high):
        return 0.9
    if any(k in s for k in mid):
        return 0.7
    return 0.55


def _build_event_clusters(
    processed_stats: List[Dict],
    max_clusters: int = 12,
    similarity_threshold: float = 0.42,
) -> List[Dict]:
    """Build de-duplicated event cards from keyword-grouped titles."""
    flat_items: List[Dict] = []
    for stat in processed_stats:
        keyword = stat.get("word", "")
        for td in stat.get("titles", []):
            title = td.get("title", "")
            normalized = _normalize_title(title)
            grams = _title_ngrams(normalized)
            if not grams:
                continue
            item = {
                "title": title,
                "normalized": normalized,
                "grams": grams,
                "source_name": td.get("source_name", ""),
                "url": td.get("url", ""),
                "mobile_url": td.get("mobile_url", ""),
                "count": td.get("count", 1),
                "ranks": td.get("ranks", []),
                "is_new": td.get("is_new", False),
                "keyword": keyword,
                "score": _title_score(td),
            }
            flat_items.append(item)

    if not flat_items:
        return []

    # highest score first improves representative quality
    flat_items.sort(key=lambda x: x["score"], reverse=True)

    clusters: List[Dict] = []
    for item in flat_items:
        best_idx = -1
        best_sim = 0.0
        for idx, c in enumerate(clusters):
            rep = c["rep"]
            sim = _jaccard(item["grams"], rep["grams"])
            # extra containment heuristic for near-identical long titles
            contains = (
                len(item["normalized"]) >= 8
                and (
                    item["normalized"] in rep["normalized"]
                    or rep["normalized"] in item["normalized"]
                )
            )
            if contains:
                sim = max(sim, 0.7)
            if sim > best_sim:
                best_sim = sim
                best_idx = idx

        if best_idx >= 0 and best_sim >= similarity_threshold:
            clusters[best_idx]["items"].append(item)
            # keep strongest rep
            if item["score"] > clusters[best_idx]["rep"]["score"]:
                clusters[best_idx]["rep"] = item
        else:
            clusters.append({"rep": item, "items": [item]})

    event_cards: List[Dict] = []
    for c in clusters:
        items = c["items"]
        rep = c["rep"]
        sources = sorted({x["source_name"] for x in items if x.get("source_name")})
        keywords = sorted({x["keyword"] for x in items if x.get("keyword")})
        related_titles = []
        for x in sorted(items, key=lambda y: y["score"], reverse=True):
            if x["title"] != rep["title"]:
                related_titles.append(x["title"])
            if len(related_titles) >= 3:
                break

        hot_score = round(sum(x["score"] for x in items), 1)
        source_count = len(sources)
        occurrence_count = len(items)
        keyword_count = len(keywords)
        new_ratio = sum(1 for x in items if x.get("is_new", False)) / max(len(items), 1)
        avg_count = sum((x.get("count", 1) or 1) for x in items) / max(len(items), 1)

        # scoring (0~100): hot base + spread + momentum + authority
        hot_component = min(hot_score, 80) / 80 * 42
        spread_component = min(source_count, 6) / 6 * 18 + min(keyword_count, 4) / 4 * 6
        momentum_component = new_ratio * 18 + min(avg_count, 5) / 5 * 6
        if sources:
            authority_avg = sum(_source_authority_weight(s) for s in sources) / len(sources)
        else:
            authority_avg = 0.5
        authority_component = authority_avg * 10
        total_score = round(hot_component + spread_component + momentum_component + authority_component, 1)

        event_cards.append(
            {
                "title": rep["title"],
                "url": rep.get("mobile_url") or rep.get("url", ""),
                "source_count": source_count,
                "sources": sources[:4],
                "occurrence_count": occurrence_count,
                "keywords": keywords[:3],
                "related_titles": related_titles,
                "hot_score": hot_score,
                "score_breakdown": {
                    "spread": round(spread_component, 1),
                    "momentum": round(momentum_component, 1),
                    "authority": round(authority_component, 1),
                },
                "total_score": total_score,
                "is_new": any(x.get("is_new", False) for x in items),
            }
        )

    event_cards.sort(key=lambda x: (x["total_score"], x["hot_score"], x["occurrence_count"]), reverse=True)
    return event_cards[:max_clusters]


def prepare_report_data(
    stats: List[Dict],
    failed_ids: Optional[List] = None,
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    mode: str = "daily",
    rank_threshold: int = 3,
    matches_word_groups_func: Optional[Callable] = None,
    load_frequency_words_func: Optional[Callable] = None,
    show_new_section: bool = True,
) -> Dict:
    """
    准备报告数据

    Args:
        stats: 统计结果列表
        failed_ids: 失败的 ID 列表
        new_titles: 新增标题
        id_to_name: ID 到名称的映射
        mode: 报告模式 (daily/incremental/current)
        rank_threshold: 排名阈值
        matches_word_groups_func: 词组匹配函数
        load_frequency_words_func: 加载频率词函数
        show_new_section: 是否显示新增热点区域

    Returns:
        Dict: 准备好的报告数据
    """
    processed_new_titles = []

    # 在增量模式下或配置关闭时隐藏新增新闻区域
    hide_new_section = mode == "incremental" or not show_new_section

    # 只有在非隐藏模式下才处理新增新闻部分
    if not hide_new_section:
        filtered_new_titles = {}
        if new_titles and id_to_name:
            # 如果提供了匹配函数，使用它过滤
            if matches_word_groups_func and load_frequency_words_func:
                word_groups, filter_words, global_filters = load_frequency_words_func()
                for source_id, titles_data in new_titles.items():
                    filtered_titles = {}
                    for title, title_data in titles_data.items():
                        if matches_word_groups_func(title, word_groups, filter_words, global_filters):
                            filtered_titles[title] = title_data
                    if filtered_titles:
                        filtered_new_titles[source_id] = filtered_titles
            else:
                # 没有匹配函数时，使用全部
                filtered_new_titles = new_titles

            # 打印过滤后的新增热点数（与推送显示一致）
            original_new_count = sum(len(titles) for titles in new_titles.values()) if new_titles else 0
            filtered_new_count = sum(len(titles) for titles in filtered_new_titles.values()) if filtered_new_titles else 0
            if original_new_count > 0:
                print(f"频率词过滤后：{filtered_new_count} 条新增热点匹配（原始 {original_new_count} 条）")

        if filtered_new_titles and id_to_name:
            for source_id, titles_data in filtered_new_titles.items():
                source_name = id_to_name.get(source_id, source_id)
                source_titles = []

                for title, title_data in titles_data.items():
                    url = title_data.get("url", "")
                    mobile_url = title_data.get("mobileUrl", "")
                    ranks = title_data.get("ranks", [])

                    processed_title = {
                        "title": title,
                        "source_name": source_name,
                        "time_display": "",
                        "count": 1,
                        "ranks": ranks,
                        "rank_threshold": rank_threshold,
                        "url": url,
                        "mobile_url": mobile_url,
                        "is_new": True,
                    }
                    source_titles.append(processed_title)

                if source_titles:
                    processed_new_titles.append(
                        {
                            "source_id": source_id,
                            "source_name": source_name,
                            "titles": source_titles,
                        }
                    )

    processed_stats = []
    for stat in stats:
        if stat["count"] <= 0:
            continue

        processed_titles = []
        for title_data in stat["titles"]:
            processed_title = {
                "title": title_data["title"],
                "source_name": title_data["source_name"],
                "time_display": title_data["time_display"],
                "count": title_data["count"],
                "ranks": title_data["ranks"],
                "rank_threshold": title_data["rank_threshold"],
                "url": title_data.get("url", ""),
                "mobile_url": title_data.get("mobileUrl", ""),
                "is_new": title_data.get("is_new", False),
            }
            processed_titles.append(processed_title)

        processed_stats.append(
            {
                "word": stat["word"],
                "count": stat["count"],
                "percentage": stat.get("percentage", 0),
                "titles": processed_titles,
            }
        )

    event_clusters = _build_event_clusters(processed_stats)

    return {
        "stats": processed_stats,
        "event_clusters": event_clusters,
        "new_titles": processed_new_titles,
        "failed_ids": failed_ids or [],
        "total_new_count": sum(
            len(source["titles"]) for source in processed_new_titles
        ),
    }


def generate_html_report(
    stats: List[Dict],
    total_titles: int,
    failed_ids: Optional[List] = None,
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    mode: str = "daily",
    update_info: Optional[Dict] = None,
    rank_threshold: int = 3,
    output_dir: str = "output",
    date_folder: str = "",
    time_filename: str = "",
    render_html_func: Optional[Callable] = None,
    matches_word_groups_func: Optional[Callable] = None,
    load_frequency_words_func: Optional[Callable] = None,
) -> str:
    """
    生成 HTML 报告

    每次生成 HTML 后会：
    1. 保存时间戳快照到 output/html/日期/时间.html（历史记录）
    2. 复制到 output/html/latest/{mode}.html（最新报告）
    3. 复制到 output/index.html 和根目录 index.html（入口）

    Args:
        stats: 统计结果列表
        total_titles: 总标题数
        failed_ids: 失败的 ID 列表
        new_titles: 新增标题
        id_to_name: ID 到名称的映射
        mode: 报告模式 (daily/incremental/current)
        update_info: 更新信息
        rank_threshold: 排名阈值
        output_dir: 输出目录
        date_folder: 日期文件夹名称
        time_filename: 时间文件名
        render_html_func: HTML 渲染函数
        matches_word_groups_func: 词组匹配函数
        load_frequency_words_func: 加载频率词函数

    Returns:
        str: 生成的 HTML 文件路径（时间戳快照路径）
    """
    # 时间戳快照文件名
    snapshot_filename = f"{time_filename}.html"

    # 构建输出路径（扁平化结构：output/html/日期/）
    snapshot_path = Path(output_dir) / "html" / date_folder
    snapshot_path.mkdir(parents=True, exist_ok=True)
    snapshot_file = str(snapshot_path / snapshot_filename)

    # 准备报告数据
    report_data = prepare_report_data(
        stats,
        failed_ids,
        new_titles,
        id_to_name,
        mode,
        rank_threshold,
        matches_word_groups_func,
        load_frequency_words_func,
    )

    # 渲染 HTML 内容
    if render_html_func:
        html_content = render_html_func(
            report_data, total_titles, mode, update_info
        )
    else:
        # 默认简单 HTML
        html_content = f"<html><body><h1>Report</h1><pre>{report_data}</pre></body></html>"

    # 1. 保存时间戳快照（历史记录）
    with open(snapshot_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 2. 复制到 html/latest/{mode}.html（最新报告）
    latest_dir = Path(output_dir) / "html" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_file = latest_dir / f"{mode}.html"
    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 3. 复制到 index.html（入口）
    # output/index.html（供 Docker Volume 挂载访问）
    output_index = Path(output_dir) / "index.html"
    with open(output_index, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 根目录 index.html（供 GitHub Pages 访问）
    root_index = Path("index.html")
    with open(root_index, "w", encoding="utf-8") as f:
        f.write(html_content)

    return snapshot_file
