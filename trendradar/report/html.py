# coding=utf-8
"""
HTML 报告渲染模块

提供 HTML 格式的热点新闻报告生成功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from trendradar.report.helpers import html_escape
from trendradar.utils.time import convert_time_for_display
from trendradar.ai.formatter import render_ai_analysis_html_rich


def render_html_content(
    report_data: Dict,
    total_titles: int,
    mode: str = "daily",
    update_info: Optional[Dict] = None,
    *,
    region_order: Optional[List[str]] = None,
    get_time_func: Optional[Callable[[], datetime]] = None,
    rss_items: Optional[List[Dict]] = None,
    rss_new_items: Optional[List[Dict]] = None,
    display_mode: str = "keyword",
    standalone_data: Optional[Dict] = None,
    ai_analysis: Optional[Any] = None,
    show_new_section: bool = True,
) -> str:
    """渲染HTML内容

    Args:
        report_data: 报告数据字典，包含 stats, event_clusters, new_titles, failed_ids, total_new_count
        total_titles: 新闻总数
        mode: 报告模式 ("daily", "current", "incremental")
        update_info: 更新信息（可选）
        region_order: 区域显示顺序列表
        get_time_func: 获取当前时间的函数（可选，默认使用 datetime.now）
        rss_items: RSS 统计条目列表（可选）
        rss_new_items: RSS 新增条目列表（可选）
        display_mode: 显示模式 ("keyword"=按关键词分组, "platform"=按平台分组)
        standalone_data: 独立展示区数据（可选），包含 platforms 和 rss_feeds
        ai_analysis: AI 分析结果对象（可选），AIAnalysisResult 实例
        show_new_section: 是否显示新增热点区域

    Returns:
        渲染后的 HTML 字符串
    """
    # 默认区域顺序
    default_region_order = ["events", "hotlist", "rss", "new_items", "standalone", "ai_analysis"]
    if region_order is None:
        region_order = default_region_order
    elif "events" not in region_order:
        # Backward-compatible: old configs may not include events
        region_order = ["events"] + list(region_order)

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>热点新闻分析</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js" integrity="sha512-BNaRQnYJYiPSqHHDb58B0yaPfCu+Wgds8Gp/gU33kqBtgNS4tSPHuGibyoeqMV/TJlSKda6FXzoEyYGjTe+vXA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
                        <style>
            /* ==========================================================================
               1. Design Tokens (CSS Variables) - PREMIUM THEME
               ========================================================================== */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

            :root {
                /* Light Mode: Apple Clean & Minimal */
                --bg-body: #f5f5f7;
                --bg-card: rgba(255, 255, 255, 0.7);
                --bg-card-solid: #ffffff;
                --bg-card-hover: rgba(255, 255, 255, 0.9);
                
                --text-main: #1d1d1f;
                --text-muted: #86868b;
                --text-light: #a1a1a6;
                
                --primary: #0071e3;
                --primary-hover: #0077ed;
                --primary-bg: rgba(0, 113, 227, 0.08);
                
                --border-color: rgba(0, 0, 0, 0.04);
                --border-card: rgba(255, 255, 255, 0.5);
                
                --danger: #ff3b30;
                --danger-bg: rgba(255, 59, 48, 0.08);
                --warning: #ff9500;
                --warning-bg: rgba(255, 149, 0, 0.08);
                --success: #34c759;
                --success-bg: rgba(52, 199, 89, 0.08);
                
                --header-bg: rgba(255, 255, 255, 0.7);
                --header-text: #1d1d1f;
                
                --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.04);
                --shadow-hover: 0 10px 32px rgba(0, 0, 0, 0.08);
                --glow: none;
                
                --glass-blur: blur(20px);
                
                --font-base: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif;
                --font-mono: 'SFMono-Regular', Consolas, monospace;
            }

            body.dark-mode {
                /* Dark Mode: Vercel/Linear Tech & Glow */
                --bg-body: #000000;
                --bg-card: rgba(17, 17, 17, 0.7);
                --bg-card-solid: #111111;
                --bg-card-hover: rgba(26, 26, 26, 0.9);
                
                --text-main: #ededed;
                --text-muted: #a1a1aa;
                --text-light: #71717a;
                
                --primary: #3b82f6;
                --primary-hover: #60a5fa;
                --primary-bg: rgba(59, 130, 246, 0.15);
                
                --border-color: rgba(255, 255, 255, 0.08);
                --border-card: rgba(255, 255, 255, 0.05);
                
                --danger: #ef4444;
                --danger-bg: rgba(239, 68, 68, 0.15);
                --warning: #f59e0b;
                --warning-bg: rgba(245, 158, 11, 0.15);
                --success: #10b981;
                --success-bg: rgba(16, 185, 129, 0.15);
                
                --header-bg: rgba(10, 10, 10, 0.7);
                --header-text: #ffffff;
                
                --shadow-card: 0 0 0 1px rgba(255,255,255,0.05), 0 4px 24px rgba(0, 0, 0, 0.5);
                --shadow-hover: 0 0 0 1px rgba(255,255,255,0.1), 0 10px 40px rgba(0, 0, 0, 0.7);
                --glow: inset 0 1px 0 0 rgba(255, 255, 255, 0.05);
            }

            /* ==========================================================================
               2. Animations
               ========================================================================== */
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(16px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes pulseGlow {
                0% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.2); }
                50% { box-shadow: 0 0 40px rgba(59, 130, 246, 0.4); }
                100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.2); }
            }

            .animate-fade-in {
                animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                opacity: 0;
            }

            /* Create delays for children */
            .stagger-1 { animation-delay: 0.1s; }
            .stagger-2 { animation-delay: 0.2s; }
            .stagger-3 { animation-delay: 0.3s; }
            .stagger-4 { animation-delay: 0.4s; }

            /* ==========================================================================
               3. Base & Layout
               ========================================================================== */
            * { box-sizing: border-box; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
            body {
                font-family: var(--font-base);
                margin: 0; padding: 24px 16px;
                background: var(--bg-body); color: var(--text-main);
                line-height: 1.6; font-size: 14px;
                transition: background-color 0.4s ease, color 0.4s ease;
            }
            a { color: var(--primary); text-decoration: none; transition: color 0.2s; }
            a:hover { color: var(--primary-hover); }

            .container { max-width: 760px; margin: 0 auto; transition: max-width 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
            body.wide-mode .container { max-width: 1280px; }

            /* ==========================================================================
               4. Header (Glassmorphism & Glow)
               ========================================================================== */
            .header {
                background: var(--header-bg);
                backdrop-filter: var(--glass-blur);
                -webkit-backdrop-filter: var(--glass-blur);
                border: 1px solid var(--border-card);
                border-radius: 20px;
                padding: 40px 32px;
                text-align: center; position: relative; overflow: hidden;
                box-shadow: var(--shadow-card);
                margin-bottom: 32px;
                box-shadow: var(--glow), var(--shadow-card);
                transition: all 0.4s ease;
            }
            
            /* Add subtle gradient orbs in dark mode for that linear glow */
            body.dark-mode .header::before {
                content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
                background: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.15), transparent 50%);
                pointer-events: none; z-index: 0;
            }

            .header-watermark {
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                font-size: clamp(60px, 10vw, 120px); font-weight: 800; letter-spacing: -0.02em;
                color: rgba(150, 150, 150, 0.03); pointer-events: none; z-index: 1; user-select: none;
            }
            body.dark-mode .header-watermark { color: rgba(255, 255, 255, 0.02); }

            .header-title {
                font-size: 28px; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 32px 0;
                position: relative; z-index: 2; color: var(--header-text);
            }
            
            .header-info {
                position: relative; z-index: 2; display: flex; flex-wrap: wrap; justify-content: center; gap: 40px;
            }
            .info-item { display: flex; flex-direction: column; align-items: center; gap: 4px; }
            .info-label { font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
            .info-value { font-weight: 700; font-size: 24px; color: var(--header-text); font-family: var(--font-mono); }

            /* ==========================================================================
               5. Universal Premium Card System
               ========================================================================== */
            .card {
                background: var(--bg-card);
                backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
                border-radius: 16px;
                border: 1px solid var(--border-card);
                margin-bottom: 24px;
                box-shadow: var(--shadow-card), var(--glow);
                transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                overflow: hidden;
            }
            .card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-hover), var(--glow);
                background: var(--bg-card-hover);
            }
            
            .card-header {
                padding: 20px 24px; border-bottom: 1px solid var(--border-color);
                display: flex; align-items: center; justify-content: space-between;
                background: transparent;
            }
            .card-title { font-size: 18px; font-weight: 700; color: var(--text-main); margin: 0; letter-spacing: -0.01em;}
            .card-meta { font-size: 13px; color: var(--text-muted); font-weight: 500; display: flex; align-items: center; gap: 6px;}
            .card-body { padding: 0; }
            
            body.wide-mode .grid-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: start; }
            body.wide-mode .grid-2col .card { margin-bottom: 0; }

            /* List Items */
            .list-item {
                display: flex; gap: 16px; padding: 16px 24px;
                border-bottom: 1px solid var(--border-color); transition: background 0.2s;
                align-items: flex-start;
            }
            .list-item:last-child { border-bottom: none; }
            .list-item:hover { background: rgba(0,0,0,0.02); }
            body.dark-mode .list-item:hover { background: rgba(255,255,255,0.02); }

            .item-number {
                width: 28px; height: 28px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;
                background: var(--border-color); color: var(--text-muted); border-radius: 8px;
                font-size: 12px; font-weight: 700; font-family: var(--font-mono);
                cursor: pointer; position: relative; overflow: hidden;
                transition: all 0.2s;
            }
            .list-item:hover .item-number { background: var(--primary-bg); color: var(--primary); transform: scale(1.05); }
            .item-number.copied { background: var(--success) !important; color: white !important; transform: scale(1.1); }
            
            .item-number .num-text { transition: opacity 0.2s, transform 0.2s; }
            .item-number .copy-icon { position: absolute; opacity: 0; transition: opacity 0.2s, transform 0.2s; transform: scale(0.5); }
            .list-item:hover .item-number .num-text { opacity: 0; transform: scale(1.5); }
            .list-item:hover .item-number .copy-icon { opacity: 1; transform: scale(1); }
            .item-number.copied .num-text { opacity: 0 !important; }
            .item-number.copied .copy-icon { opacity: 1 !important; transform: scale(1) !important; }

            .item-content { flex: 1; min-width: 0; padding-top: 2px;}
            .item-header { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; align-items: center;}
            .item-title { font-size: 15px; line-height: 1.5; margin: 0; color: var(--text-main); font-weight: 500;}

            /* Modern Badges / Pills */
            .badge { 
                padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; 
                white-space: nowrap; letter-spacing: 0.02em; display: inline-flex; align-items: center;
            }
            .badge-neutral { background: var(--border-color); color: var(--text-muted); }
            .badge-primary { background: var(--primary-bg); color: var(--primary); }
            .badge-danger { background: var(--danger-bg); color: var(--danger); }
            .badge-warning { background: var(--warning-bg); color: var(--warning); }
            
            .text-sm-muted { font-size: 12px; color: var(--text-muted); font-weight: 500; }
            .text-sm-success { font-size: 12px; color: var(--success); font-weight: 600; }

            /* ==========================================================================
               6. Section Specifics
               ========================================================================== */
            /* Event Cards */
            .event-card { padding: 24px; border-bottom: 1px solid var(--border-color); }
            .event-card:last-child { border-bottom: none; }
            .event-card-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 12px; }
            .event-title { font-size: 16px; font-weight: 700; margin: 0; color: var(--text-main); line-height: 1.5; letter-spacing: -0.01em;}
            .event-meta-group { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
            .event-desc { margin-top: 12px; font-size: 14px; color: var(--text-muted); line-height: 1.6; }
            .event-desc strong { color: var(--text-main); font-weight: 600; }

            /* AI Section */
            .ai-section { background: linear-gradient(135deg, var(--primary-bg) 0%, transparent 100%); }
            .ai-block { background: var(--bg-card-solid); margin-bottom: 16px; padding: 20px; border-radius: 12px; border: 1px solid var(--border-color); }
            .ai-block:last-child { margin-bottom: 0; }
            .ai-block-title { color: var(--primary); font-weight: 700; margin-bottom: 12px; font-size: 14px; display: flex; align-items: center; gap: 8px; }
            .ai-block-content { font-size: 14px; color: var(--text-main); white-space: pre-wrap; line-height: 1.7; }

            /* Tabs - Modern Pill Style */
            .tab-bar {
                display: none; overflow-x: auto; white-space: nowrap;
                padding: 4px; gap: 8px; margin-bottom: 24px;
                -webkit-overflow-scrolling: touch; scrollbar-width: none;
                background: var(--bg-card); border-radius: 100px;
                border: 1px solid var(--border-card);
                box-shadow: var(--shadow-card);
                backdrop-filter: blur(10px);
            }
            .tab-bar::-webkit-scrollbar { display: none; }
            body.wide-mode .tab-bar { display: inline-flex; max-width: 100%; }
            body.wide-mode .tab-bar.tab-hidden { display: none; }
            
            .tab-btn {
                padding: 8px 16px; background: transparent; color: var(--text-muted);
                border: none; border-radius: 100px; font-size: 13px; font-weight: 600;
                cursor: pointer; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); 
                display: inline-flex; align-items: center; gap: 8px;
            }
            .tab-btn:hover { color: var(--text-main); background: var(--border-color); }
            .tab-btn.active { background: var(--text-main); color: var(--bg-body); box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            body.dark-mode .tab-btn.active { box-shadow: 0 2px 12px rgba(255,255,255,0.1); }
            .tab-count { background: var(--border-color); padding: 2px 8px; border-radius: 10px; font-size: 11px; }
            .tab-btn.active .tab-count { background: var(--bg-body); color: var(--text-main); }

            /* Glassmorphic Action Buttons */
            .save-buttons { position: absolute; top: 24px; right: 24px; display: flex; gap: 12px; z-index: 10; }
            .btn-action {
                background: rgba(150, 150, 150, 0.1); border: 1px solid rgba(150, 150, 150, 0.2); color: var(--header-text);
                padding: 8px 16px; border-radius: 12px; cursor: pointer; font-size: 13px; font-weight: 600;
                backdrop-filter: blur(12px); transition: all 0.3s; display: flex; align-items: center; justify-content: center;
                min-height: 36px;
            }
            .btn-action:hover { background: rgba(150, 150, 150, 0.2); transform: translateY(-1px); }
            
            .save-btn-group { display: flex; position: relative; }
            .save-btn-group .btn-action:first-child { border-radius: 12px 0 0 12px; border-right: none; }
            .save-btn-group .btn-action:last-child { border-radius: 0 12px 12px 0; padding: 8px 10px; }
            
            .dropdown-menu {
                position: absolute; top: 100%; right: 0; margin-top: 8px;
                background: var(--bg-card-solid); border: 1px solid var(--border-color); border-radius: 12px;
                box-shadow: var(--shadow-hover); padding: 6px; min-width: 140px;
                opacity: 0; visibility: hidden; transform: translateY(-8px); transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            }
            .save-btn-group:hover .dropdown-menu { opacity: 1; visibility: visible; transform: translateY(0); }
            .dropdown-item {
                display: flex; align-items: center; width: 100%; padding: 10px 14px;
                background: none; border: none; color: var(--text-main); font-size: 13px; font-weight: 500;
                cursor: pointer; border-radius: 8px; text-align: left; transition: background 0.2s;
            }
            .dropdown-item:hover { background: var(--primary-bg); color: var(--primary); }
            .dropdown-item svg { width: 16px; height: 16px; margin-right: 10px; stroke: currentColor; }

            /* Modern Search Bar */
            .search-bar { margin-bottom: 24px; display: none; }
            .search-input {
                width: 100%; padding: 16px 20px; background: var(--bg-card); border: 1px solid var(--border-color);
                border-radius: 16px; color: var(--text-main); font-size: 15px;
                outline: none; transition: all 0.3s; box-shadow: var(--shadow-card);
                backdrop-filter: blur(10px);
            }
            .search-input:focus { border-color: var(--primary); box-shadow: 0 0 0 4px var(--primary-bg); transform: translateY(-1px); }

            /* Reading Progress */
            .reading-progress {
                position: fixed; top: 0; left: 0; width: 0; height: 4px;
                background: linear-gradient(90deg, var(--primary), #8b5cf6); z-index: 9999;
                transition: width 0.1s linear; border-radius: 0 2px 2px 0;
            }
            
            /* Error */
            .error-section { background: var(--danger-bg); border: 1px solid rgba(239, 68, 68, 0.2); padding: 20px; border-radius: 16px; margin-bottom: 24px; }
            .error-title { color: var(--danger); font-size: 14px; font-weight: 700; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;}
            .error-item { color: var(--danger); font-size: 13px; font-family: var(--font-mono); margin-left: 24px; padding: 4px 0;}
            
            /* Footer */
            .footer { text-align: center; padding: 40px 0; color: var(--text-muted); font-size: 13px; font-weight: 500;}

            /* Legacy hooks for JS (DO NOT RENAME) */
            .events-more summary { cursor: pointer; font-size: 12px; color: var(--text-muted); font-weight: 600; outline: none; padding: 12px 24px; display: block; background: transparent; border-top: 1px solid var(--border-color); text-align: center; transition: background 0.2s; }
            .events-more summary:hover { background: rgba(0,0,0,0.02); }
            body.dark-mode .events-more summary:hover { background: rgba(255,255,255,0.02); }
            .events-more summary::marker, .events-more summary::-webkit-details-marker { display: none; }
            .word-group.collapsed .card-body { display: none; }
            .word-header.collapsible { cursor: pointer; transition: background 0.2s; }
            .word-header.collapsible:hover { background: rgba(0,0,0,0.02); }
            body.dark-mode .word-header.collapsible:hover { background: rgba(255,255,255,0.02); }
            .collapse-icon { font-size: 10px; margin-right: 8px; transition: transform 0.3s; display: inline-block; }
            .word-group.collapsed .collapse-icon { transform: rotate(-90deg); }

            /* FAB Bar */
            .fab-bar {
                position: fixed; bottom: 32px; right: 32px; display: flex; flex-direction: column; gap: 12px;
                z-index: 100; opacity: 0; transform: translateY(20px); transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); pointer-events: none;
            }
            .fab-bar.visible { opacity: 1; transform: translateY(0); pointer-events: auto; }
            .fab-btn {
                width: 48px; height: 48px; border-radius: 24px; background: var(--bg-card-solid); color: var(--text-main);
                border: 1px solid var(--border-color); cursor: pointer; font-size: 20px; box-shadow: var(--shadow-hover);
                display: flex; align-items: center; justify-content: center; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            }
            .fab-btn:hover { color: var(--primary); transform: translateY(-4px); box-shadow: 0 14px 40px rgba(0,0,0,0.15); }


            /* New Partitions and App Shell Layout */
            body { padding: 0; }
            .container { padding: 0 16px; margin-top: 24px; }
            .main-nav {
                position: sticky;
                top: 0;
                z-index: 100;
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border-bottom: 1px solid var(--border-color);
                padding: 12px 24px;
                display: flex;
                gap: 16px;
                margin-bottom: 24px;
                border-radius: 12px;
                box-shadow: var(--shadow-card);
            }
            .main-nav-item {
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                color: var(--text-muted);
                transition: all 0.3s;
                background: transparent;
                border: none;
                white-space: nowrap;
            }
            .main-nav-item.active { background: var(--primary); color: white; }
            .main-nav-item:hover:not(.active) { background: var(--primary-bg); color: var(--primary); }

            body[data-partition] .partition { display: none; }
            body[data-partition="overview"] .partition-overview,
            body[data-partition="overview"] .partition-hotlist,
            body[data-partition="overview"] .partition-rss,
            body[data-partition="overview"] .partition-standalone { display: block; }
            
            body[data-partition="overview"] .partition-hotlist .card:nth-of-type(n+4),
            body[data-partition="overview"] .partition-rss .card:nth-of-type(n+4),
            body[data-partition="overview"] .partition-standalone .card:nth-of-type(n+4) { display: none !important; }
            body[data-partition="overview"] .tab-bar, 
            body[data-partition="overview"] .view-more-btn { display: none !important; }

            body[data-partition="hotlist"] .partition-hotlist { display: block; }
            body[data-partition="rss"] .partition-rss { display: block; }
            body[data-partition="standalone"] .partition-standalone { display: block; }
            body[data-partition="ai_analysis"] .partition-ai_analysis { display: block; }

            /* Tab Chip Override */
            .tab-bar {
                display: flex !important; flex-wrap: wrap; gap: 8px; margin-bottom: 24px; padding: 0;
                background: transparent; border: none; box-shadow: none; white-space: normal;
                overflow: visible !important;
            }
            .tab-bar::-webkit-scrollbar { display: none; }
            .tab-btn {
                max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
                padding: 6px 12px; font-size: 13px; display: inline-flex; align-items: center; gap: 6px;
                background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px;
            }
            .hidden-chip:not(.revealed) { display: none !important; }
            .tab-expand-btn { background: var(--border-color); color: var(--text-main); font-weight: 600; cursor: pointer; }

            /* Card Hierarchy */
            .list-item { gap: 12px; padding: 12px 20px; border-bottom: 1px solid rgba(0,0,0,0.03); }
            body.dark-mode .list-item { border-bottom: 1px solid rgba(255,255,255,0.03); }
            .news-title, .rss-title {
                display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
                font-size: 15px; font-weight: 600; color: var(--text-main); line-height: 1.5; margin-top: 4px;
            }
            .text-sm-muted { font-size: 12px; color: var(--text-light); }
            .badge { padding: 2px 8px; font-size: 10px; }
            
            /* View More */
            .view-more-btn {
                width: 100%; padding: 12px; text-align: center; background: transparent;
                border: none; color: var(--primary); font-size: 13px; font-weight: 600; cursor: pointer;
                border-top: 1px solid rgba(0,0,0,0.03);
            }
            body.dark-mode .view-more-btn { border-top: 1px solid rgba(255,255,255,0.03); }
            .view-more-btn:hover { background: var(--primary-bg); }

            /* Responsive */
            @media (max-width: 1024px) {
                body.wide-mode .grid-2col, .grid-2col { grid-template-columns: 1fr !important; }
                .main-nav { overflow-x: auto; white-space: nowrap; padding: 12px 16px; border-radius: 0; margin: 0 -16px 16px -16px; }
                .tab-btn { max-width: none; }
                .btn-action { min-height: 40px; padding: 8px 20px; }
                .main-nav-item { padding: 10px 20px; font-size: 15px; }
            }
            @media (max-width: 640px) {
                body { padding: 0; background: var(--bg-body); }
                .container { border-radius: 0; }
                .header { border-radius: 0; padding: 40px 24px; margin-bottom: 16px; border-left: none; border-right: none;}
                .card { border-radius: 12px; margin: 0 12px 16px 12px; }
                .info-value { font-size: 20px; }
                .save-buttons { position: static; justify-content: center; margin-bottom: 24px; width: 100%; display: flex; }
                .save-btn-group { flex: 1; }
                .save-btn-group .btn-action:first-child { width: 100%; }
                .tab-bar { padding: 4px; margin: 0 12px 16px 12px; display: flex; overflow-x: auto; max-width: calc(100% - 24px);}
            }
        </style>
    </head>
    <body>
        <div class="reading-progress"></div>
        <div class="container">
            <div class="header">
                <div class="header-watermark">TrendRadar</div>
                <div class="save-buttons">
                    <button class="toggle-wide-btn" onclick="toggleWideMode()" title="切换宽屏/窄屏">⛶</button>
                    <button class="toggle-dark-btn" onclick="toggleDarkMode()" title="切换暗色/亮色">☽</button>
                    <div class="save-btn-group">
                        <button class="save-btn" onclick="saveAsImage()">导出</button>
                        <button class="save-dropdown-trigger">▾</button>
                        <div class="save-dropdown-menu">
                            <button class="save-dropdown-item" onclick="saveAsImage()"><svg class="dropdown-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="12" height="12" rx="2"/><circle cx="8" cy="7.5" r="2.5"/><path d="M12 4h.01"/></svg>整页截图</button>
                            <button class="save-dropdown-item" onclick="saveAsMultipleImages()"><svg class="dropdown-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="10" height="10" rx="1.5"/><path d="M5 4V2.5A1.5 1.5 0 016.5 1h7A1.5 1.5 0 0115 2.5v7a1.5 1.5 0 01-1.5 1.5H12"/></svg>分段截图</button>
                        </div>
                    </div>
                </div>
                <div class="header-title">热点新闻分析</div>
                <div class="header-info">
                    <div class="info-item">
                        <span class="info-label">报告类型</span>
                        <span class="info-value">"""

    # 处理报告类型显示（根据 mode 直接显示）
    if mode == "current":
        html += "当前榜单"
    elif mode == "incremental":
        html += "增量分析"
    else:
        html += "全天汇总"

    html += """</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">新闻总数</span>
                        <span class="info-value">"""

    html += f"{total_titles} 条"

    # 计算筛选后的热点新闻数量
    hot_news_count = sum(len(stat["titles"]) for stat in report_data["stats"])

    html += """</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">热点新闻</span>
                        <span class="info-value">"""

    html += f"{hot_news_count} 条"

    html += """</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">生成时间</span>
                        <span class="info-value">"""

    # 使用提供的时间函数或默认 datetime.now
    if get_time_func:
        now = get_time_func()
    else:
        now = datetime.now()
    html += now.strftime("%m-%d %H:%M")

    html += """</span>
                    </div>
                </div>
            </div>


            <div class="main-nav">
                <button class="main-nav-item active" data-partition="overview">总览</button>
                <button class="main-nav-item" data-partition="hotlist">热榜</button>
                <button class="main-nav-item" data-partition="rss">RSS订阅</button>
                <button class="main-nav-item" data-partition="standalone">独立展示区</button>
                <button class="main-nav-item" data-partition="ai_analysis">AI分析</button>
            </div>
            <div class="partitions-container">
                <div class="search-bar">
                    <input type="text" class="search-input" placeholder="搜索新闻标题..." oninput="handleSearch(this.value)">
                </div>"""

    # 处理失败ID错误信息
    if report_data["failed_ids"]:
        html += """
                <div class="error-section">
                    <div class="error-title">⚠️ 请求失败的平台</div>
                    <ul class="error-list">"""
        for id_value in report_data["failed_ids"]:
            html += f'<li class="error-item">{html_escape(id_value)}</li>'
        html += """
                    </ul>
                </div>"""

    # 生成热点词汇统计部分的HTML
    events_html = ""
    event_clusters = report_data.get("event_clusters", [])
    if event_clusters:
        top_n = 12
        top_events = event_clusters[:top_n]
        overflow_events = event_clusters[top_n:]

        def _render_event_card(event: Dict) -> str:
            card_html = ""
            title = html_escape(event.get("title", ""))
            url = html_escape(event.get("url", ""))
            source_count = event.get("source_count", 0)
            occurrence_count = event.get("occurrence_count", 0)
            hot_score = event.get("hot_score", 0)
            total_score = event.get("total_score", hot_score)
            breakdown = event.get("score_breakdown", {}) or {}
            spread_score = breakdown.get("spread", 0)
            momentum_score = breakdown.get("momentum", 0)
            authority_score = breakdown.get("authority", 0)
            sources = event.get("sources", [])
            keywords = event.get("keywords", [])
            related_titles = event.get("related_titles", [])
            brief = event.get("brief", "")
            why_it_matters = event.get("why_it_matters", "")
            impact = event.get("impact", "")

            if url:
                title_html = f'<a href="{url}" target="_blank" class="news-link">{title}</a>'
            else:
                title_html = title

            card_html += f"""
                        <div class="event-card card">
                            <div class="event-card-header">
                                <h3 class="event-title">{title_html}</h3>
                                <div class="badge badge-danger">Score {total_score}</div>
                            </div>
                            <div class="event-meta-group">
                                <span class="badge badge-neutral">Sources {source_count}</span>
                                <span class="badge badge-neutral">Mentions {occurrence_count}</span>
                                <span class="badge badge-neutral">Hot {hot_score}</span>
                                <span class="badge badge-neutral">Spread {spread_score}</span>
                                <span class="badge badge-neutral">Momentum {momentum_score}</span>
                                <span class="badge badge-neutral">Authority {authority_score}</span>"""

            for s in sources[:4]:
                card_html += f'<span class="badge badge-neutral">{html_escape(s)}</span>'
            for k in keywords[:3]:
                card_html += f'<span class="badge badge-neutral">#{html_escape(k)}</span>'

            card_html += "</div>"

            if brief:
                card_html += f'<div class="event-desc"><strong>Brief:</strong> {html_escape(brief)}</div>'
            if why_it_matters:
                card_html += f'<div class="event-desc"><strong>Why it matters:</strong> {html_escape(why_it_matters)}</div>'
            if impact:
                card_html += f'<div class="event-desc"><strong>Impact:</strong> {html_escape(impact)}</div>'

            if related_titles:
                related_safe = "; ".join(html_escape(x) for x in related_titles[:2])
                card_html += f'<div class="event-desc"><strong>Related:</strong> {related_safe}</div>'

            card_html += """
                        </div>"""
            return card_html

        events_html += f"""
                <div class="events-section animate-fade-in stagger-2">
                    <div class="events-section-header">
                        <div class="events-section-title">Event Cards</div>
                        <div class="events-section-count">{len(event_clusters)} items</div>
                    </div>
                    <div class="events-grid grid-2col">"""

        for event in top_events:
            events_html += _render_event_card(event)

        events_html += """
                    </div>"""

        if overflow_events:
            events_html += f"""
                    <details class="events-more">
                        <summary>More Events ({len(overflow_events)})</summary>
                        <div class="events-more-grid grid-2col">"""
            for event in overflow_events:
                events_html += _render_event_card(event)
            events_html += """
                        </div>
                    </details>"""

        events_html += """
                </div>"""
    stats_html = ""
    tab_bar_html = ""
    if report_data["stats"]:
        total_count = len(report_data["stats"])

        # 生成 Tab 栏 HTML
        tab_bar_html = '<div class="tab-bar">'
        for tab_i, tab_stat in enumerate(report_data["stats"]):
            escaped_tab_word = html_escape(tab_stat["word"])
            tab_count = tab_stat["count"]
            chip_class = "tab-btn"
            if tab_i >= 8:
                chip_class += " hidden-chip"
            tab_bar_html += f'<button class="{chip_class}" data-tab-index="{tab_i}">{escaped_tab_word}<span class="tab-count">{tab_count}</span></button>'
        if len(report_data["stats"]) > 8:
            tab_bar_html += f'<button class="tab-btn tab-expand-btn" data-expand-chips="false">+ {len(report_data["stats"]) - 8}</button>'
        tab_bar_html += '<button class="tab-btn hidden-chip" data-tab-index="all">全部</button>'
        tab_bar_html += '</div>'

        for i, stat in enumerate(report_data["stats"], 1):
            count = stat["count"]

            # 确定热度等级
            if count >= 10:
                count_class = "hot"
            elif count >= 5:
                count_class = "warm"
            else:
                count_class = ""

            escaped_word = html_escape(stat["word"])

            stats_html += f"""
                <div class="word-group card" data-tab-index="{i - 1}">
                    <div class="word-header card-header">
                        <div class="card-title">{escaped_word}</div>
                        <div class="card-meta"><span class="collapse-icon">▼</span>{count} 条 · {i}/{total_count}</div>
                    </div>
                    <div class="card-body"><div class="card-list-container">"""

            # 处理每个词组下的新闻标题，给每条新闻标上序号
            for j, title_data in enumerate(stat["titles"], 1):
                is_new = title_data.get("is_new", False)
                new_class = "new" if is_new else ""

                stats_html += f"""
                    <div class="news-item list-item {new_class}" style="display: {'none' if j > 5 else 'flex'}">
                        <div class="item-number news-number">{j}</div>
                        <div class="item-content">
                            <div class="item-header">"""

                # 根据 display_mode 决定显示来源还是关键词
                if display_mode == "keyword":
                    # keyword 模式：显示来源
                    stats_html += f'<span class="text-sm-muted">{html_escape(title_data["source_name"])}</span>'
                else:
                    # platform 模式：显示关键词
                    matched_keyword = title_data.get("matched_keyword", "")
                    if matched_keyword:
                        stats_html += f'<span class="text-sm-muted">[{html_escape(matched_keyword)}]</span>'

                # 处理排名显示
                ranks = title_data.get("ranks", [])
                if ranks:
                    min_rank = min(ranks)
                    max_rank = max(ranks)
                    rank_threshold = title_data.get("rank_threshold", 10)

                    # 确定排名等级
                    if min_rank <= 3:
                        rank_class = "top"
                    elif min_rank <= rank_threshold:
                        rank_class = "high"
                    else:
                        rank_class = ""

                    if min_rank == max_rank:
                        rank_text = str(min_rank)
                    else:
                        rank_text = f"{min_rank}-{max_rank}"

                    stats_html += f'<span class="rank-num {rank_class}">{rank_text}</span>'

                # 处理时间显示
                time_display = title_data.get("time_display", "")
                if time_display:
                    # 简化时间显示格式，将波浪线替换为~
                    simplified_time = (
                        time_display.replace(" ~ ", "~")
                        .replace("[", "")
                        .replace("]", "")
                    )
                    stats_html += (
                        f'<span class="text-sm-muted">{html_escape(simplified_time)}</span>'
                    )

                # 处理出现次数
                count_info = title_data.get("count", 1)
                if count_info > 1:
                    stats_html += f'<span class="text-sm-success">{count_info}次</span>'

                stats_html += """
                            </div>
                            <div class="item-title news-title">"""

                # 处理标题和链接
                escaped_title = html_escape(title_data["title"])
                link_url = title_data.get("mobile_url") or title_data.get("url", "")

                if link_url:
                    escaped_url = html_escape(link_url)
                    stats_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    stats_html += escaped_title

                stats_html += """
                            </div>
                        </div>
                    </div>"""


            stats_html += '</div>'
            if len(stat["titles"]) > 5:
                stats_html += f'<button class="view-more-btn" onclick="toggleViewMore(this)">查看更多 ({len(stat["titles"]) - 5})</button>'
            stats_html += """
                </div></div>"""


    # 给热榜统计添加外层包装
    if stats_html:
        stats_html = f"""
                <div class="hotlist-section animate-fade-in stagger-1">{tab_bar_html}{stats_html}
                </div>"""

    # 生成新增新闻区域的HTML
    new_titles_html = ""
    if show_new_section and report_data["new_titles"]:
        new_titles_html += f"""
                <div class="new-section animate-fade-in stagger-3">
                    <div class="new-section-title">本次新增热点 (共 {report_data['total_new_count']} 条)</div>
                    <div class="new-sources-grid grid-2col">"""

        for source_data in report_data["new_titles"]:
            escaped_source = html_escape(source_data["source_name"])
            titles_count = len(source_data["titles"])

            new_titles_html += f"""
                    <div class="new-source-group card">
                        <div class="card-header"><h3 class="card-title">{escaped_source} · {titles_count}条</h3></div>
                        <div class="card-body"><div class="card-list-container">"""

            # 为新增新闻也添加序号
            for idx, title_data in enumerate(source_data["titles"], 1):
                ranks = title_data.get("ranks", [])

                # 处理新增新闻的排名显示
                rank_class = ""
                if ranks:
                    min_rank = min(ranks)
                    if min_rank <= 3:
                        rank_class = "top"
                    elif min_rank <= title_data.get("rank_threshold", 10):
                        rank_class = "high"

                    if len(ranks) == 1:
                        rank_text = str(ranks[0])
                    else:
                        rank_text = f"{min(ranks)}-{max(ranks)}"
                else:
                    rank_text = "?"

                new_titles_html += f"""
                        <div class="new-item list-item">
                            <div class="item-number new-item-number">{idx}</div>
                            <div class="badge {rank_class}">{rank_text}</div>
                            <div class="item-content">
                                <div class="item-title">"""

                # 处理新增新闻的链接
                escaped_title = html_escape(title_data["title"])
                link_url = title_data.get("mobile_url") or title_data.get("url", "")

                if link_url:
                    escaped_url = html_escape(link_url)
                    new_titles_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    new_titles_html += escaped_title

                new_titles_html += """
                                </div>
                            </div>
                        </div></div>"""

            new_titles_html += """
                    </div>"""

        new_titles_html += """
                    </div>
                </div>"""

    # 生成 RSS 统计内容
    def render_rss_stats_html(stats: List[Dict], title: str = "RSS 订阅更新") -> str:
        """渲染 RSS 统计区块 HTML

        Args:
            stats: RSS 分组统计列表，格式与热榜一致：
                [
                    {
                        "word": "关键词",
                        "count": 5,
                        "titles": [
                            {
                                "title": "标题",
                                "source_name": "Feed 名称",
                                "time_display": "12-29 08:20",
                                "url": "...",
                                "is_new": True/False
                            }
                        ]
                    }
                ]
            title: 区块标题

        Returns:
            渲染后的 HTML 字符串
        """
        if not stats:
            return ""

        # 计算总条目数
        total_count = sum(stat.get("count", 0) for stat in stats)
        if total_count == 0:
            return ""

        rss_html = f"""
                <div class="rss-section animate-fade-in stagger-4">
                    <div class="rss-section-header">
                        <div class="rss-section-title">{title}</div>
                        <div class="rss-section-count">{total_count} 条</div>
                    </div>
                    <div class="rss-feeds-grid grid-2col">"""

        # 按关键词分组渲染（与热榜格式一致）
        for stat in stats:
            keyword = stat.get("word", "")
            titles = stat.get("titles", [])
            if not titles:
                continue

            keyword_count = len(titles)

            rss_html += f"""
                    <div class="feed-group card">
                        <div class="card-header">
                            <h3 class="card-title">{html_escape(keyword)}</h3>
                            <div class="card-meta">{keyword_count} 条</div>
                        </div>
                        <div class="card-body"><div class="card-list-container">"""

            for j, title_data in enumerate(titles, 1):
                item_title = title_data.get("title", "")
                url = title_data.get("url", "")
                time_display = title_data.get("time_display", "")
                source_name = title_data.get("source_name", "")
                is_new = title_data.get("is_new", False)

                rss_html += """
                        <div class="rss-item list-item" style="display: {'none' if j > 5 else 'flex'}">
                            <div class="item-header">"""

                if time_display:
                    rss_html += f'<span class="text-sm-muted">{html_escape(time_display)}</span>'

                if source_name:
                    rss_html += f'<span class="text-sm-muted">{html_escape(source_name)}</span>'

                if is_new:
                    rss_html += '<span class="rss-author" style="color: #dc2626;">NEW</span>'

                rss_html += """
                            </div>
                            <div class="item-title rss-title">"""

                escaped_title = html_escape(item_title)
                if url:
                    escaped_url = html_escape(url)
                    rss_html += f'<a href="{escaped_url}" target="_blank" class="rss-link">{escaped_title}</a>'
                else:
                    rss_html += escaped_title

                rss_html += """
                            </div>
                        </div>"""

            rss_html += '</div>'
            if len(titles) > 5:
                rss_html += f'<button class="view-more-btn" onclick="toggleViewMore(this)">查看更多 ({len(titles) - 5})</button>'
            rss_html += """
                    </div></div>"""

        rss_html += """
                    </div>
                </div>"""
        return rss_html

    # 生成独立展示区内容
    def render_standalone_html(data: Optional[Dict]) -> str:
        """渲染独立展示区 HTML（复用热点词汇统计区样式）

        Args:
            data: 独立展示数据，格式：
                {
                    "platforms": [
                        {
                            "id": "zhihu",
                            "name": "知乎热榜",
                            "items": [
                                {
                                    "title": "标题",
                                    "url": "链接",
                                    "rank": 1,
                                    "ranks": [1, 2, 1],
                                    "first_time": "08:00",
                                    "last_time": "12:30",
                                    "count": 3,
                                }
                            ]
                        }
                    ],
                    "rss_feeds": [
                        {
                            "id": "hacker-news",
                            "name": "Hacker News",
                            "items": [
                                {
                                    "title": "标题",
                                    "url": "链接",
                                    "published_at": "2025-01-07T08:00:00",
                                    "author": "作者",
                                }
                            ]
                        }
                    ]
                }

        Returns:
            渲染后的 HTML 字符串
        """
        if not data:
            return ""

        platforms = data.get("platforms", [])
        rss_feeds = data.get("rss_feeds", [])

        if not platforms and not rss_feeds:
            return ""

        # 计算总条目数
        total_platform_items = sum(len(p.get("items", [])) for p in platforms)
        total_rss_items = sum(len(f.get("items", [])) for f in rss_feeds)
        total_count = total_platform_items + total_rss_items

        if total_count == 0:
            return ""

        # 收集所有分组信息用于生成 tab
        all_groups = []
        for p in platforms:
            items = p.get("items", [])
            if items:
                all_groups.append({"name": p.get("name", p.get("id", "")), "count": len(items)})
        for f in rss_feeds:
            items = f.get("items", [])
            if items:
                all_groups.append({"name": f.get("name", f.get("id", "")), "count": len(items)})

        standalone_html = f"""
                <div class="standalone-section animate-fade-in stagger-4">
                    <div class="standalone-section-header">
                        <div class="standalone-section-title">独立展示区</div>
                        <div class="standalone-section-count">{total_count} 条</div>
                    </div>"""

        # 生成 tab 栏（2+ 分组时）
        if len(all_groups) >= 2:
            standalone_html += """
                    <div class="tab-bar standalone-tab-bar">"""
            for idx, g in enumerate(all_groups):
                chip_class = "tab-btn"
                if idx >= 8:
                    chip_class += " hidden-chip"
                standalone_html += f"""
                        <button class="{chip_class}" data-standalone-tab="{idx}">{html_escape(g["name"])}<span class="tab-count">{g["count"]}</span></button>"""
            if len(all_groups) > 8:
                standalone_html += f'<button class="tab-btn tab-expand-btn" data-expand-chips="false">+ {len(all_groups) - 8}</button>'
            standalone_html += f"""
                        <button class="tab-btn active hidden-chip" data-standalone-tab="all">全部<span class="tab-count">{total_count}</span></button>
                    </div>"""

        standalone_html += """
                    <div class="standalone-groups-grid grid-2col">"""

        group_idx = 0
        # 渲染热榜平台（复用 word-group 结构）
        for platform in platforms:
            platform_name = platform.get("name", platform.get("id", ""))
            items = platform.get("items", [])
            if not items:
                continue

            standalone_html += f"""
                    <div class="standalone-group card" data-standalone-tab="{group_idx}">
                        <div class="card-header">
                            <h3 class="card-title">{html_escape(platform_name)}</h3>
                            <div class="card-meta">{len(items)} 条</div>
                        </div>
                        <div class="card-body"><div class="card-list-container">"""

            # 渲染每个条目（复用 news-item 结构）
            for j, item in enumerate(items, 1):
                title = item.get("title", "")
                url = item.get("url", "") or item.get("mobileUrl", "")
                rank = item.get("rank", 0)
                ranks = item.get("ranks", [])
                first_time = item.get("first_time", "")
                last_time = item.get("last_time", "")
                count = item.get("count", 1)

                standalone_html += f"""
                        <div class="news-item" style="display: {'none' if j > 5 else 'flex'}">
                            <div class="item-number news-number">{j}</div>
                            <div class="item-content">
                                <div class="item-header">"""

                # 排名显示（复用 rank-num 样式，无 # 前缀）
                if ranks:
                    min_rank = min(ranks)
                    max_rank = max(ranks)

                    # 确定排名等级
                    if min_rank <= 3:
                        rank_class = "top"
                    elif min_rank <= 10:
                        rank_class = "high"
                    else:
                        rank_class = ""

                    if min_rank == max_rank:
                        rank_text = str(min_rank)
                    else:
                        rank_text = f"{min_rank}-{max_rank}"

                    standalone_html += f'<span class="rank-num {rank_class}">{rank_text}</span>'
                elif rank > 0:
                    if rank <= 3:
                        rank_class = "top"
                    elif rank <= 10:
                        rank_class = "high"
                    else:
                        rank_class = ""
                    standalone_html += f'<span class="rank-num {rank_class}">{rank}</span>'

                # 时间显示（复用 time-info 样式，将 HH-MM 转换为 HH:MM）
                if first_time and last_time and first_time != last_time:
                    first_time_display = convert_time_for_display(first_time)
                    last_time_display = convert_time_for_display(last_time)
                    standalone_html += f'<span class="text-sm-muted">{html_escape(first_time_display)}~{html_escape(last_time_display)}</span>'
                elif first_time:
                    first_time_display = convert_time_for_display(first_time)
                    standalone_html += f'<span class="text-sm-muted">{html_escape(first_time_display)}</span>'

                # 出现次数（复用 count-info 样式）
                if count > 1:
                    standalone_html += f'<span class="text-sm-success">{count}次</span>'

                standalone_html += """
                                </div>
                                <div class="item-title news-title">"""

                # 标题和链接（复用 news-link 样式）
                escaped_title = html_escape(title)
                if url:
                    escaped_url = html_escape(url)
                    standalone_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    standalone_html += escaped_title

                standalone_html += """
                                </div>
                            </div>
                        </div>"""

            standalone_html += '</div>'
            if len(items) > 5:
                standalone_html += f'<button class="view-more-btn" onclick="toggleViewMore(this)">查看更多 ({len(items) - 5})</button>'
            standalone_html += """
                    </div></div>"""
            group_idx += 1

        # 渲染 RSS 源（复用相同结构）
        for feed in rss_feeds:
            feed_name = feed.get("name", feed.get("id", ""))
            items = feed.get("items", [])
            if not items:
                continue

            standalone_html += f"""
                    <div class="standalone-group card" data-standalone-tab="{group_idx}">
                        <div class="card-header">
                            <h3 class="card-title">{html_escape(feed_name)}</h3>
                            <div class="card-meta">{len(items)} 条</div>
                        </div>
                        <div class="card-body"><div class="card-list-container">"""

            for j, item in enumerate(items, 1):
                title = item.get("title", "")
                url = item.get("url", "")
                published_at = item.get("published_at", "")
                author = item.get("author", "")

                standalone_html += f"""
                        <div class="news-item" style="display: {'none' if j > 5 else 'flex'}">
                            <div class="item-number news-number">{j}</div>
                            <div class="item-content">
                                <div class="item-header">"""

                # 时间显示（格式化 ISO 时间）
                if published_at:
                    try:
                        from datetime import datetime as dt
                        if "T" in published_at:
                            dt_obj = dt.fromisoformat(published_at.replace("Z", "+00:00"))
                            time_display = dt_obj.strftime("%m-%d %H:%M")
                        else:
                            time_display = published_at
                    except:
                        time_display = published_at

                    standalone_html += f'<span class="text-sm-muted">{html_escape(time_display)}</span>'

                # 作者显示
                if author:
                    standalone_html += f'<span class="text-sm-muted">{html_escape(author)}</span>'

                standalone_html += """
                                </div>
                                <div class="item-title news-title">"""

                escaped_title = html_escape(title)
                if url:
                    escaped_url = html_escape(url)
                    standalone_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    standalone_html += escaped_title

                standalone_html += """
                                </div>
                            </div>
                        </div>"""

            standalone_html += '</div>'
            if len(items) > 5:
                standalone_html += f'<button class="view-more-btn" onclick="toggleViewMore(this)">查看更多 ({len(items) - 5})</button>'
            standalone_html += """
                    </div></div>"""
            group_idx += 1

        standalone_html += """
                    </div>
                </div>"""
        return standalone_html

    # 生成 RSS 统计和新增 HTML
    rss_stats_html = render_rss_stats_html(rss_items, "RSS 订阅更新") if rss_items else ""
    rss_new_html = render_rss_stats_html(rss_new_items, "RSS 新增更新") if rss_new_items else ""

    # 生成独立展示区 HTML
    standalone_html = render_standalone_html(standalone_data)

    # 生成 AI 分析 HTML
    ai_html = render_ai_analysis_html_rich(ai_analysis) if ai_analysis else ""

    # 准备各区域内容映射

    events_html = f'<div class="partition partition-overview">{events_html}</div>' if events_html else ""
    stats_html = f'<div class="partition partition-hotlist">{stats_html}</div>' if stats_html else ""
    rss_stats_html = f'<div class="partition partition-rss">{rss_stats_html}</div>' if rss_stats_html else ""
    rss_new_html = f'<div class="partition partition-rss">{rss_new_html}</div>' if rss_new_html else ""
    new_titles_html = f'<div class="partition partition-overview">{new_titles_html}</div>' if new_titles_html else ""
    standalone_html = f'<div class="partition partition-standalone">{standalone_html}</div>' if standalone_html else ""
    ai_html = f'<div class="partition partition-ai_analysis">{ai_html}</div>' if ai_html else ""
    
    region_contents = {
        "events": events_html,
        "hotlist": stats_html,
        "rss": rss_stats_html,
        "new_items": (new_titles_html, rss_new_html),  # 元组，分别处理
        "standalone": standalone_html,
        "ai_analysis": ai_html,
    }

    def add_section_divider(content: str) -> str:
        """为内容的外层 div 添加 section-divider 类"""
        if not content or 'class="' not in content:
            return content
        first_class_pos = content.find('class="')
        if first_class_pos != -1:
            insert_pos = first_class_pos + len('class="')
            return content[:insert_pos] + "section-divider " + content[insert_pos:]
        return content

    # 按 region_order 顺序组装内容，动态添加分割线
    has_previous_content = False
    for region in region_order:
        content = region_contents.get(region, "")
        if region == "new_items":
            # 特殊处理 new_items 区域（包含热榜新增和 RSS 新增两部分）
            new_html, rss_new = content
            if new_html:
                if has_previous_content:
                    new_html = add_section_divider(new_html)
                html += new_html
                has_previous_content = True
            if rss_new:
                if has_previous_content:
                    rss_new = add_section_divider(rss_new)
                html += rss_new
                has_previous_content = True
        elif content:
            if has_previous_content:
                content = add_section_divider(content)
            html += content
            has_previous_content = True

    html += """
            </div>
            </div>

            <div class="footer">
                <div class="footer-content">
                    由 <span class="project-name">TrendRadar</span> 生成 ·
                    <a href="https://github.com/sansan0/TrendRadar" target="_blank" class="footer-link">
                        GitHub 开源项目
                    </a>"""

    if update_info:
        html += f"""
                    <br>
                    <span style="color: #ea580c; font-weight: 500;">
                        发现新版本 {update_info['remote_version']}，当前版本 {update_info['current_version']}
                    </span>"""

    html += """
                </div>
            </div>
        </div>

        <div class="fab-bar">
            <button class="fab-btn" onclick="window.scrollTo({top:0,behavior:'smooth'})" title="返回顶部">↑</button>
            <button class="fab-btn fab-help">
                <span>?</span>
                <div class="fab-tooltip">
                    <div class="tip-row"><span>切换宽屏</span><span class="tip-key">W</span></div>
                    <div class="tip-row"><span>暗色模式</span><span class="tip-key">D</span></div>
                    <div class="tip-row"><span>搜索</span><span class="tip-key">/</span></div>
                    <div class="tip-row"><span>上一个 Tab</span><span class="tip-key">←</span></div>
                    <div class="tip-row"><span>下一个 Tab</span><span class="tip-key">→</span></div>
                    <div class="tip-row"><span>序号可复制</span><span class="tip-key">点击</span></div>
                </div>
            </button>
        </div>

        <script>
            // ===== 浏览器增强功能 =====

            function toggleWideMode() {
                document.body.classList.toggle('wide-mode');
                var isWide = document.body.classList.contains('wide-mode');
                try { localStorage.setItem('trendradar-wide-mode', isWide ? '1' : '0'); } catch(e) {}
                var btn = document.querySelector('.toggle-wide-btn');
                if (btn) btn.textContent = isWide ? '⊡' : '⛶';
                initTabVisibility();
                initCollapseVisibility();
                initStandaloneTabVisibility();
            }

            function toggleDarkMode() {
                var isDark = document.body.classList.toggle('dark-mode');
                try { localStorage.setItem('trendradar-dark-mode', isDark ? '1' : '0'); } catch(e) {}
                var btn = document.querySelector('.toggle-dark-btn');
                if (btn) btn.textContent = isDark ? '☀' : '☽';
            }

            function initTabs() {
                var tabBar = document.querySelector('.tab-bar');
                if (!tabBar) return;
                var tabs = tabBar.querySelectorAll('.tab-btn');
                var groups = document.querySelectorAll('.word-group[data-tab-index]');
                initTabVisibility();

                function activateTab(index) {
                    tabs.forEach(function(t) { t.classList.remove('active'); });
                    if (index === 'all') {
                        var allBtn = tabBar.querySelector('[data-tab-index="all"]');
                        if (allBtn) allBtn.classList.add('active');
                        groups.forEach(function(g) { g.style.display = ''; });
                        try { history.replaceState(null, '', '#all'); } catch(e) {}
                        return;
                    }
                    var idx = parseInt(index);
                    tabs.forEach(function(t) {
                        if (parseInt(t.dataset.tabIndex) === idx) t.classList.add('active');
                    });
                    if (document.body.classList.contains('wide-mode') && !tabBar.classList.contains('tab-hidden')) {
                        groups.forEach(function(g) {
                            g.style.display = (parseInt(g.dataset.tabIndex) === idx) ? '' : 'none';
                        });
                    }
                    try { history.replaceState(null, '', '#tab-' + idx); } catch(e) {}
                }

                tabs.forEach(function(tab) {
                    tab.addEventListener('click', function() {
                        var idx = tab.dataset.tabIndex;
                        activateTab(idx === 'all' ? 'all' : parseInt(idx));
                    });
                });

                tabBar.addEventListener('keydown', function(e) {
                    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                        var tabsArr = Array.from(tabs);
                        var ci = tabsArr.findIndex(function(t) { return t.classList.contains('active'); });
                        var dir = e.key === 'ArrowRight' ? 1 : -1;
                        var ni = Math.max(0, Math.min(tabsArr.length - 1, ci + dir));
                        var nt = tabsArr[ni];
                        activateTab(nt.dataset.tabIndex === 'all' ? 'all' : parseInt(nt.dataset.tabIndex));
                        nt.focus();
                        e.preventDefault();
                    }
                });

                var hash = window.location.hash;
                if (hash === '#all') { activateTab('all'); }
                else if (hash.indexOf('#tab-') === 0) { activateTab(parseInt(hash.replace('#tab-', ''))); }
                else { activateTab(0); }
            }

            function initTabVisibility() {
                var tabBar = document.querySelector('.tab-bar');
                if (!tabBar) return;
                var groups = document.querySelectorAll('.word-group[data-tab-index]');
                var isWide = document.body.classList.contains('wide-mode');
                if (!isWide || groups.length <= 2) {
                    // tabBar.classList.add('tab-hidden');
                    groups.forEach(function(g) { g.style.display = ''; });
                } else {
                    // tabBar.classList.remove('tab-hidden');
                    var activeTab = tabBar.querySelector('.tab-btn.active');
                    if (activeTab) { activeTab.click(); }
                    else {
                        var firstTab = tabBar.querySelector('.tab-btn');
                        if (firstTab) firstTab.click();
                    }
                }
            }

            function handleSearch(query) {
                query = query.toLowerCase();
                document.querySelectorAll('.news-item').forEach(function(item) {
                    var title = (item.querySelector('.news-title') || {}).textContent || '';
                    item.style.display = (!query || title.toLowerCase().indexOf(query) !== -1) ? '' : 'none';
                });
                document.querySelectorAll('.rss-item').forEach(function(item) {
                    var title = (item.querySelector('.rss-title') || {}).textContent || '';
                    item.style.display = (!query || title.toLowerCase().indexOf(query) !== -1) ? '' : 'none';
                });
            }

            function initBackToTop() {
                var fabBar = document.querySelector('.fab-bar');
                if (!fabBar) return;
                window.addEventListener('scroll', function() {
                    fabBar.classList.toggle('visible', window.scrollY > 300);
                });
            }

            function initCollapse() {
                document.querySelectorAll('.word-header').forEach(function(header) {
                    header.addEventListener('click', function() {
                        var tabBar = document.querySelector('.tab-bar');
                        if (document.body.classList.contains('wide-mode') && tabBar && !tabBar.classList.contains('tab-hidden')) return;
                        var group = header.closest('.word-group');
                        if (group) group.classList.toggle('collapsed');
                    });
                });
                initCollapseVisibility();
            }

            function initCollapseVisibility() {
                var headers = document.querySelectorAll('.word-header');
                var tabBar = document.querySelector('.tab-bar');
                var isTabMode = document.body.classList.contains('wide-mode') && tabBar && !tabBar.classList.contains('tab-hidden');
                headers.forEach(function(h) {
                    if (isTabMode) { h.classList.remove('collapsible'); }
                    else { h.classList.add('collapsible'); }
                });
                if (isTabMode) {
                    document.querySelectorAll('.word-group.collapsed').forEach(function(g) {
                        g.classList.remove('collapsed');
                    });
                }
            }

            // 独立展示区 Tab 切换
            function initStandaloneTabs() {
                var tabBar = document.querySelector('.standalone-tab-bar');
                if (!tabBar) return;
                var groups = document.querySelectorAll('.standalone-group[data-standalone-tab]');
                var btns = tabBar.querySelectorAll('.tab-btn[data-standalone-tab]');

                function activateStandaloneTab(val) {
                    btns.forEach(function(b) {
                        var bVal = b.getAttribute('data-standalone-tab');
                        b.classList.toggle('active', bVal === String(val));
                    });
                    groups.forEach(function(g) {
                        var gVal = g.getAttribute('data-standalone-tab');
                        g.style.display = (val === 'all' || gVal === String(val)) ? '' : 'none';
                    });
                }

                btns.forEach(function(btn) {
                    btn.addEventListener('click', function() {
                        activateStandaloneTab(btn.getAttribute('data-standalone-tab'));
                    });
                });

                // 初始状态
                initStandaloneTabVisibility();
            }

            function initStandaloneTabVisibility() {
                var tabBar = document.querySelector('.standalone-tab-bar');
                if (!tabBar) return;
                var groups = document.querySelectorAll('.standalone-group[data-standalone-tab]');
                var isWide = document.body.classList.contains('wide-mode');
                if (!isWide || groups.length <= 1) {
                    // tabBar.classList.add('tab-hidden');
                    groups.forEach(function(g) { g.style.display = ''; });
                } else {
                    // tabBar.classList.remove('tab-hidden');
                    var activeBtn = tabBar.querySelector('.tab-btn.active');
                    if (activeBtn) activeBtn.click();
                    else { var first = tabBar.querySelector('.tab-btn'); if (first) first.click(); }
                }
            }

            function prepareForScreenshot() {
                var state = {
                    wasWide: document.body.classList.contains('wide-mode'),
                    hiddenGroups: []
                };
                document.body.classList.remove('wide-mode');
                state.wasDark = document.body.classList.contains('dark-mode');
                document.body.classList.remove('dark-mode');
                document.querySelectorAll('.word-group[data-tab-index]').forEach(function(g, i) {
                    if (g.style.display === 'none') {
                        state.hiddenGroups.push(i);
                        g.style.display = '';
                    }
                });
                state.hiddenStandaloneGroups = [];
                document.querySelectorAll('.standalone-group[data-standalone-tab]').forEach(function(g, i) {
                    if (g.style.display === 'none') {
                        state.hiddenStandaloneGroups.push(i);
                        g.style.display = '';
                    }
                });
                document.querySelectorAll('.tab-bar, .standalone-tab-bar, .search-bar, .fab-bar, .toggle-wide-btn').forEach(function(el) {
                    el.dataset.prevDisplay = el.style.display || '';
                    el.style.display = 'none';
                });
                document.querySelectorAll('.toggle-dark-btn').forEach(function(el) {
                    el.dataset.prevDisplay = el.style.display || ''; el.style.display = 'none';
                });
                document.querySelectorAll('.reading-progress').forEach(function(el) { el.style.display = 'none'; });
                document.querySelectorAll('.header-watermark').forEach(function(el) { el.style.display = 'none'; });
                return state;
            }

            function restoreAfterScreenshot(state) {
                if (state.wasWide) document.body.classList.add('wide-mode');
                if (state.wasDark) document.body.classList.add('dark-mode');
                var groups = document.querySelectorAll('.word-group[data-tab-index]');
                state.hiddenGroups.forEach(function(i) {
                    if (groups[i]) groups[i].style.display = 'none';
                });
                var standaloneGroups = document.querySelectorAll('.standalone-group[data-standalone-tab]');
                if (state.hiddenStandaloneGroups) {
                    state.hiddenStandaloneGroups.forEach(function(i) {
                        if (standaloneGroups[i]) standaloneGroups[i].style.display = 'none';
                    });
                }
                document.querySelectorAll('.tab-bar, .standalone-tab-bar, .search-bar, .fab-bar, .toggle-wide-btn').forEach(function(el) {
                    el.style.display = el.dataset.prevDisplay || '';
                    delete el.dataset.prevDisplay;
                });
                document.querySelectorAll('.toggle-dark-btn').forEach(function(el) {
                    el.style.display = el.dataset.prevDisplay || ''; delete el.dataset.prevDisplay;
                });
                document.querySelectorAll('.reading-progress').forEach(function(el) { el.style.display = ''; });
                document.querySelectorAll('.reading-progress').forEach(function(el) { el.style.display = ''; });
                document.querySelectorAll('.header-watermark').forEach(function(el) { el.style.display = ''; });
                initTabVisibility();
                initCollapseVisibility();
                initStandaloneTabVisibility();
                var fabBar = document.querySelector('.fab-bar');
                if (fabBar && window.scrollY > 300) fabBar.classList.add('visible');
            }

            // ===== 截图功能 =====

            async function saveAsImage() {
                const button = event.target;
                const originalText = button.textContent;

                try {
                    button.textContent = '生成中...';
                    button.disabled = true;
                    window.scrollTo(0, 0);

                    // 等待页面稳定
                    await new Promise(resolve => setTimeout(resolve, 200));

                    // 截图前准备：切回窄屏布局
                    var screenshotState = prepareForScreenshot();

                    // 截图前隐藏按钮
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'hidden';

                    // 再次等待确保按钮完全隐藏
                    await new Promise(resolve => setTimeout(resolve, 100));

                    const container = document.querySelector('.container');

                    const canvas = await html2canvas(container, {
                        backgroundColor: '#ffffff',
                        scale: 1.5,
                        useCORS: true,
                        allowTaint: false,
                        imageTimeout: 10000,
                        removeContainer: false,
                        foreignObjectRendering: false,
                        logging: false,
                        width: container.offsetWidth,
                        height: container.offsetHeight,
                        x: 0,
                        y: 0,
                        scrollX: 0,
                        scrollY: 0,
                        windowWidth: window.innerWidth,
                        windowHeight: window.innerHeight
                    });

                    buttons.style.visibility = 'visible';
                    restoreAfterScreenshot(screenshotState);

                    const link = document.createElement('a');
                    const now = new Date();
                    const filename = `TrendRadar_热点新闻分析_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}.png`;

                    link.download = filename;
                    link.href = canvas.toDataURL('image/png', 1.0);

                    // 触发下载
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);

                    button.textContent = '保存成功!';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);

                } catch (error) {
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'visible';
                    restoreAfterScreenshot(screenshotState);
                    button.textContent = '保存失败';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                }
            }

            async function saveAsMultipleImages() {
                const button = event.target;
                const originalText = button.textContent;
                const container = document.querySelector('.container');
                const scale = 1.5;
                const maxHeight = 5000 / scale;
                var screenshotState2 = prepareForScreenshot();

                try {
                    button.textContent = '分析中...';
                    button.disabled = true;

                    // 获取所有可能的分割元素
                    const newsItems = Array.from(container.querySelectorAll('.news-item'));
                    const wordGroups = Array.from(container.querySelectorAll('.word-group'));
                    const newSection = container.querySelector('.new-section');
                    const errorSection = container.querySelector('.error-section');
                    const header = container.querySelector('.header');
                    const footer = container.querySelector('.footer');

                    // 计算元素位置和高度
                    const containerRect = container.getBoundingClientRect();
                    const elements = [];

                    // 添加header作为必须包含的元素
                    elements.push({
                        type: 'header',
                        element: header,
                        top: 0,
                        bottom: header.offsetHeight,
                        height: header.offsetHeight
                    });

                    // 添加错误信息（如果存在）
                    if (errorSection) {
                        const rect = errorSection.getBoundingClientRect();
                        elements.push({
                            type: 'error',
                            element: errorSection,
                            top: rect.top - containerRect.top,
                            bottom: rect.bottom - containerRect.top,
                            height: rect.height
                        });
                    }

                    // 按word-group分组处理news-item
                    wordGroups.forEach(group => {
                        const groupRect = group.getBoundingClientRect();
                        const groupNewsItems = group.querySelectorAll('.news-item');

                        // 添加word-group的header部分
                        const wordHeader = group.querySelector('.word-header');
                        if (wordHeader) {
                            const headerRect = wordHeader.getBoundingClientRect();
                            elements.push({
                                type: 'word-header',
                                element: wordHeader,
                                parent: group,
                                top: groupRect.top - containerRect.top,
                                bottom: headerRect.bottom - containerRect.top,
                                height: headerRect.height
                            });
                        }

                        // 添加每个news-item
                        groupNewsItems.forEach(item => {
                            const rect = item.getBoundingClientRect();
                            elements.push({
                                type: 'news-item',
                                element: item,
                                parent: group,
                                top: rect.top - containerRect.top,
                                bottom: rect.bottom - containerRect.top,
                                height: rect.height
                            });
                        });
                    });

                    // 添加新增新闻部分
                    if (newSection) {
                        const rect = newSection.getBoundingClientRect();
                        elements.push({
                            type: 'new-section',
                            element: newSection,
                            top: rect.top - containerRect.top,
                            bottom: rect.bottom - containerRect.top,
                            height: rect.height
                        });
                    }

                    // 添加footer
                    const footerRect = footer.getBoundingClientRect();
                    elements.push({
                        type: 'footer',
                        element: footer,
                        top: footerRect.top - containerRect.top,
                        bottom: footerRect.bottom - containerRect.top,
                        height: footer.offsetHeight
                    });

                    // 计算分割点
                    const segments = [];
                    let currentSegment = { start: 0, end: 0, height: 0, includeHeader: true };
                    let headerHeight = header.offsetHeight;
                    currentSegment.height = headerHeight;

                    for (let i = 1; i < elements.length; i++) {
                        const element = elements[i];
                        const potentialHeight = element.bottom - currentSegment.start;

                        // 检查是否需要创建新分段
                        if (potentialHeight > maxHeight && currentSegment.height > headerHeight) {
                            // 在前一个元素结束处分割
                            currentSegment.end = elements[i - 1].bottom;
                            segments.push(currentSegment);

                            // 开始新分段
                            currentSegment = {
                                start: currentSegment.end,
                                end: 0,
                                height: element.bottom - currentSegment.end,
                                includeHeader: false
                            };
                        } else {
                            currentSegment.height = potentialHeight;
                            currentSegment.end = element.bottom;
                        }
                    }

                    // 添加最后一个分段
                    if (currentSegment.height > 0) {
                        currentSegment.end = container.offsetHeight;
                        segments.push(currentSegment);
                    }

                    button.textContent = `生成中 (0/${segments.length})...`;

                    // 隐藏保存按钮
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'hidden';

                    // 为每个分段生成图片
                    const images = [];
                    for (let i = 0; i < segments.length; i++) {
                        const segment = segments[i];
                        button.textContent = `生成中 (${i + 1}/${segments.length})...`;

                        // 创建临时容器用于截图
                        const tempContainer = document.createElement('div');
                        tempContainer.style.cssText = `
                            position: absolute;
                            left: -9999px;
                            top: 0;
                            width: ${container.offsetWidth}px;
                            background: white;
                        `;
                        tempContainer.className = 'container';

                        // 克隆容器内容
                        const clonedContainer = container.cloneNode(true);

                        // 移除克隆内容中的保存按钮
                        const clonedButtons = clonedContainer.querySelector('.save-buttons');
                        if (clonedButtons) {
                            clonedButtons.style.display = 'none';
                        }

                        tempContainer.appendChild(clonedContainer);
                        document.body.appendChild(tempContainer);

                        // 等待DOM更新
                        await new Promise(resolve => setTimeout(resolve, 100));

                        // 使用html2canvas截取特定区域
                        const canvas = await html2canvas(clonedContainer, {
                            backgroundColor: '#ffffff',
                            scale: scale,
                            useCORS: true,
                            allowTaint: false,
                            imageTimeout: 10000,
                            logging: false,
                            width: container.offsetWidth,
                            height: segment.end - segment.start,
                            x: 0,
                            y: segment.start,
                            windowWidth: window.innerWidth,
                            windowHeight: window.innerHeight
                        });

                        images.push(canvas.toDataURL('image/png', 1.0));

                        // 清理临时容器
                        document.body.removeChild(tempContainer);
                    }

                    // 恢复按钮显示
                    buttons.style.visibility = 'visible';

                    // 下载所有图片
                    const now = new Date();
                    const baseFilename = `TrendRadar_热点新闻分析_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;

                    for (let i = 0; i < images.length; i++) {
                        const link = document.createElement('a');
                        link.download = `${baseFilename}_part${i + 1}.png`;
                        link.href = images[i];
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);

                        // 延迟一下避免浏览器阻止多个下载
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }

                    button.textContent = `已保存 ${segments.length} 张图片!`;
                    restoreAfterScreenshot(screenshotState2);
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);

                } catch (error) {
                    console.error('分段保存失败:', error);
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'visible';
                    restoreAfterScreenshot(screenshotState2);
                    button.textContent = '保存失败';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                }
            }


            // App Shell Navigation
            document.body.dataset.partition = 'overview';
            document.querySelectorAll('.main-nav-item').forEach(function(item) {
                item.addEventListener('click', function() {
                    document.querySelectorAll('.main-nav-item').forEach(nav => nav.classList.remove('active'));
                    this.classList.add('active');
                    document.body.dataset.partition = this.dataset.partition;
                    window.scrollTo({top: 0, behavior: 'smooth'});
                });
            });

            // Tab Expand
            document.addEventListener('click', function(e) {
                if (e.target.classList.contains('tab-expand-btn')) {
                    var btn = e.target;
                    var tabBar = btn.closest('.tab-bar');
                    var isExpanded = btn.dataset.expandChips === 'true';
                    if (isExpanded) {
                        tabBar.querySelectorAll('.hidden-chip.revealed').forEach(el => el.classList.remove('revealed'));
                        btn.dataset.expandChips = 'false';
                        btn.textContent = '+ ' + (tabBar.querySelectorAll('.tab-btn').length - 1 - tabBar.querySelectorAll('.tab-expand-btn').length);
                    } else {
                        tabBar.querySelectorAll('.hidden-chip').forEach(el => el.classList.add('revealed'));
                        btn.dataset.expandChips = 'true';
                        btn.textContent = '收起';
                    }
                }
            });

            // View More
            window.toggleViewMore = function(btn) {
                var container = btn.previousElementSibling;
                var isExpanded = btn.dataset.expanded === 'true';
                if (isExpanded) {
                    container.querySelectorAll('.news-item, .rss-item').forEach((el, idx) => {
                        if (idx >= 5) el.style.display = 'none';
                    });
                    btn.dataset.expanded = 'false';
                    btn.textContent = '查看更多 (' + (container.querySelectorAll('.news-item, .rss-item').length - 5) + ')';
                } else {
                    container.querySelectorAll('.news-item, .rss-item').forEach(el => el.style.display = 'flex');
                    btn.dataset.expanded = 'true';
                    btn.textContent = '收起';
                }
            };

            document.addEventListener('DOMContentLoaded', function() {
                window.scrollTo(0, 0);

                // 自动检测宽屏模式
                var savedMode = null;
                try { savedMode = localStorage.getItem('trendradar-wide-mode'); } catch(e) {}
                if (savedMode === '1' || (savedMode === null && window.innerWidth > 768)) {
                    document.body.classList.add('wide-mode');
                    var btn = document.querySelector('.toggle-wide-btn');
                    if (btn) btn.textContent = '⊡';
                }

                // 暗色模式恢复 (默认开启)
                var savedDark = null;
                try { savedDark = localStorage.getItem('trendradar-dark-mode'); } catch(e) {}
                if (savedDark === '1' || savedDark === null) {
                    document.body.classList.add('dark-mode');
                    var darkBtn = document.querySelector('.toggle-dark-btn');
                    if (darkBtn) darkBtn.textContent = '☀';
                }

                // 启用搜索栏
                var searchBar = document.querySelector('.search-bar');
                if (searchBar) searchBar.style.display = 'block';

                // 初始化增强功能
                initTabs();
                initBackToTop();
                initCollapse();
                initStandaloneTabs();

                // 键盘快捷键
                document.addEventListener('keydown', function(e) {
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                    var helpBtn = document.querySelector('.fab-help');
                    switch(e.key) {
                        case '?':
                            if (helpBtn) {
                                helpBtn.classList.toggle('show-tip');
                                var fabBar = document.querySelector('.fab-bar');
                                if (fabBar) fabBar.classList.add('visible');
                            }
                            break;
                        case 'Escape':
                            if (helpBtn) helpBtn.classList.remove('show-tip');
                            break;
                        case 'w': case 'W': toggleWideMode(); break;
                        case 'd': case 'D': toggleDarkMode(); break;
                        case '/': e.preventDefault(); var si = document.querySelector('.search-input'); if (si) si.focus(); break;
                    }
                });

                // 阅读进度条
                var progressBar = document.querySelector('.reading-progress');
                if (progressBar) {
                    window.addEventListener('scroll', function() {
                        var h = document.documentElement.scrollHeight - window.innerHeight;
                        progressBar.style.width = (h > 0 ? (window.scrollY / h * 100) : 0) + '%';
                    });
                }

                // 一键复制：hover 时数字变复制图标
                var copySvg = '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M5 11H3.5A1.5 1.5 0 012 9.5v-7A1.5 1.5 0 013.5 1h7A1.5 1.5 0 0112 2.5V5"/></svg>';
                var checkSvg = '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="#22c55e" stroke-width="2"><path d="M3 8.5l3.5 3.5 7-7"/></svg>';
                document.querySelectorAll('.news-item .news-number').forEach(function(numEl) {
                    var item = numEl.closest('.news-item');
                    var titleEl = item ? item.querySelector('.news-title a') : null;
                    if (!titleEl) return;
                    var numText = numEl.textContent.trim();
                    numEl.innerHTML = '<span class="num-text">' + numText + '</span><span class="copy-icon">' + copySvg + '</span>';
                    numEl.title = '点击复制标题和链接';
                    numEl.addEventListener('click', function(e) {
                        e.stopPropagation();
                        var text = titleEl.textContent.trim() + ' ' + titleEl.href;
                        navigator.clipboard.writeText(text).then(function() {
                            numEl.classList.add('copied');
                            numEl.querySelector('.copy-icon').innerHTML = checkSvg;
                            setTimeout(function() {
                                numEl.classList.remove('copied');
                                numEl.querySelector('.copy-icon').innerHTML = copySvg;
                            }, 1500);
                        });
                    });
                });



                // Header watermark 鼠标跟随揭示
                (function() {
                    var header = document.querySelector('.header');
                    var watermark = document.querySelector('.header-watermark');
                    if (!header || !watermark) return;

                    var radius = 100;

                    header.addEventListener('mousemove', function(e) {
                        var rect = watermark.getBoundingClientRect();
                        var x = e.clientX - rect.left;
                        var y = e.clientY - rect.top;
                        var maskVal = 'radial-gradient(circle ' + radius + 'px at ' + x + 'px ' + y + 'px, rgba(0,0,0,1) 0%, rgba(0,0,0,0.3) 50%, rgba(0,0,0,0) 100%)';
                        watermark.style.webkitMaskImage = maskVal;
                        watermark.style.maskImage = maskVal;
                        watermark.style.color = 'rgba(255, 255, 255, 0.25)';
                    });

                    header.addEventListener('mouseleave', function() {
                        watermark.style.webkitMaskImage = 'radial-gradient(circle 0px at 50% 50%, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 100%)';
                        watermark.style.maskImage = 'radial-gradient(circle 0px at 50% 50%, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 100%)';
                        watermark.style.color = 'rgba(255, 255, 255, 0.15)';
                    });
                })();
            });
        </script>
    </body>
    </html>
    """

    return html
