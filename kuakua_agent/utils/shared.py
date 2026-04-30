"""Shared utility functions used across multiple service modules.

Centralises logic that was previously duplicated in several places so that
keyword lists, parsing rules and app-name maps have a single source of truth.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Category guessing (unified from summary_service, routes, daily_summarizer,
# phone_usage_service – previously 4 independent copies with diverging lists)
# ---------------------------------------------------------------------------

_WORK_KEYWORDS: frozenset[str] = frozenset({
    # code / editors / AI assistants
    "code", "vscode", "cursor", "claude", "pycharm", "idea", "intellij",
    "webstorm", "goland", "rider", "clion", "datagrip",
    # terminals
    "terminal", "powershell", "cmd",
    # productivity / office
    "notion", "obsidian", "evernote",
    "word", "excel", "ppt", "pdf", "powerpoint", "outlook", "mail", "wps",
    # communication (work)
    "slack", "teams", "zoom", "feishu", "dingtalk", "飞书", "钉钉",
    "企业微信", "wechat work",
    # browsers (treated as work by default)
    "chrome", "edge", "firefox", "arc",
    # dev tools
    "postman", "figma", "github", "git",
})

_ENTERTAINMENT_KEYWORDS: frozenset[str] = frozenset({
    "bilibili", "douyin", "tiktok", "youtube", "netflix",
    "spotify", "music", "netease", "qqmusic", "网易云", "qq音乐",
    "steam", "epic", "lol", "game", "游戏", "原神", "genshin", "minecraft",
    "王者", "虎牙", "斗鱼", "快手",
    "discord", "weibo", "twitter", "reddit", "zhihu", "知乎",
    "微博", "小红书", "xiaohongshu", "x.com",
})


_custom_categories: dict[str, str] = {}


def load_custom_categories(raw_json: str) -> None:
    """Load custom app→category mappings (typically from preferences)."""
    import json as _json
    try:
        data = _json.loads(raw_json)
        if isinstance(data, dict):
            _custom_categories.clear()
            for k, v in data.items():
                if v in ("work", "entertainment", "other"):
                    _custom_categories[k.lower()] = v
    except Exception:
        pass


def guess_category(app_name: str) -> str:
    """Return ``"work"``, ``"entertainment"`` or ``"other"`` for a given app name.

    Custom categories set by the user take priority over built-in keywords.
    """
    lowered = app_name.lower()

    # 1. User-defined custom mapping
    if lowered in _custom_categories:
        return _custom_categories[lowered]

    # Strip .exe for matching
    key = lowered[:-4] if lowered.endswith(".exe") else lowered
    if key in _custom_categories:
        return _custom_categories[key]

    # 2. Built-in keyword matching
    if any(kw in lowered for kw in _ENTERTAINMENT_KEYWORDS):
        return "entertainment"
    if any(kw in lowered for kw in _WORK_KEYWORDS):
        return "work"
    return "other"


# ---------------------------------------------------------------------------
# Time helpers (previously duplicated in summary_service & routes)
# ---------------------------------------------------------------------------

def parse_aw_timestamp(value: object) -> datetime | None:
    """Parse an ISO-8601 timestamp from ActivityWatch, defaulting to UTC."""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def overlap_seconds(
    start: datetime,
    end: datetime,
    range_start: datetime,
    range_end: datetime,
) -> float:
    """Return the number of seconds that [*start*, *end*) overlaps with
    [*range_start*, *range_end*)."""
    o_start = max(start, range_start)
    o_end = min(end, range_end)
    return max((o_end - o_start).total_seconds(), 0.0)


# ---------------------------------------------------------------------------
# App-name normalisation (shared between summary_service & frontend validation)
# ---------------------------------------------------------------------------

APP_NAME_MAP: dict[str, str] = {
    # Browsers
    "msedge": "Microsoft Edge",
    "chrome": "Google Chrome",
    "firefox": "Mozilla Firefox",
    "arc": "Arc Browser",
    # Editors / IDEs
    "code": "Visual Studio Code",
    "cursor": "Cursor",
    "pycharm": "PyCharm",
    "idea": "IntelliJ IDEA",
    "webstorm": "WebStorm",
    "goland": "GoLand",
    "rider": "JetBrains Rider",
    "clion": "CLion",
    "datagrip": "DataGrip",
    # Terminals / system
    "terminal": "Windows Terminal",
    "powershell": "PowerShell",
    "cmd": "命令提示符",
    "explorer": "文件资源管理器",
    "electron": "Electron",
    # Office
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "outlook": "Microsoft Outlook",
    "wps": "WPS Office",
    # Communication
    "qq": "QQ",
    "wechat": "微信",
    "dingtalk": "钉钉",
    "feishu": "飞书",
    "slack": "Slack",
    "teams": "Microsoft Teams",
    "zoom": "Zoom",
    "discord": "Discord",
    # Productivity
    "notion": "Notion",
    "obsidian": "Obsidian",
    "postman": "Postman",
    "figma": "Figma",
    "github": "GitHub",
    "git": "Git",
    # Media / entertainment
    "spotify": "Spotify",
    "music": "网易云音乐",
    "qqmusic": "QQ音乐",
    "netease": "网易云音乐",
    "bilibili": "哔哩哔哩",
    "douyin": "抖音",
    "youtube": "YouTube",
    "netflix": "Netflix",
    "steam": "Steam",
    # Phone packages
    "com.xingin.xhs": "小红书",
    "com.taobao.idlefish": "闲鱼",
    "com.larus.nova": "Nova Launcher",
    "com.tencent.mm": "微信",
    "com.tencent.mobileqq": "QQ",
    "com.ss.android.ugc.aweme": "抖音",
    "com.eg.android.alipaygphone": "支付宝",
    "tv.danmaku.bili": "哔哩哔哩",
    "com.sankuai.meituan": "美团",
    "com.xunmeng.pinduoduo": "拼多多",
    "com.jingdong.app.mall": "京东",
    "com.netease.cloudmusic": "网易云音乐",
    "com.tencent.qqmusic": "QQ音乐",
}


def normalize_app_name(raw: str) -> str:
    """Return a human-friendly display name for an app/process string."""
    value = raw.strip()
    if not value:
        return "Unknown"

    lowered = value.lower()

    # Special-case Cursor helper processes
    if re.fullmatch(r"cursorloginup\d+", lowered):
        return "Cursor"

    # Strip .exe suffix if present
    key = lowered[:-4] if lowered.endswith(".exe") else lowered

    mapped = APP_NAME_MAP.get(key)
    if mapped:
        return mapped

    # Fallback: strip .exe from original casing
    if value.lower().endswith(".exe"):
        return value[:-4]
    return value
