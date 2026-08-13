"""历史上的今天 — Byabbe 免费 API（无需 Key）

https://byabbe.se/on-this-day/{month}/{day}/events.json
数据来源 Wikipedia，中英文都有。
"""
import datetime, logging, requests

log = logging.getLogger("magic")
_cache: dict[str, list[dict]] = {}


def get_events(month: int = None, day: int = None, lang: str = "zh") -> list[dict]:
    """获取历史上今天的事件

    返回 [{"year": "1969", "description": "...", "wikipedia": [...]}, ...]
    """
    now = datetime.date.today()
    if month is None:
        month = now.month
    if day is None:
        day = now.day
    cache_key = f"{month}/{day}/{lang}"
    if cache_key in _cache:
        return _cache[cache_key]
    try:
        r = requests.get(
            f"https://byabbe.se/on-this-day/{month}/{day}/events.json",
            timeout=10,
        )
        events = r.json().get("events", [])
        # 按年份降序排（最近的在前）
        events.sort(key=lambda e: int(e.get("year", 0)), reverse=True)
        _cache[cache_key] = events
        return events
    except Exception as e:
        log.debug(f"[on-this-day] 获取失败: {e}")
    return []


def get_events_text(month: int = None, day: int = None, count: int = 5) -> str:
    """格式化输出历史上的今天"""
    now = datetime.date.today()
    if month is None:
        month = now.month
    if day is None:
        day = now.day
    events = get_events(month, day)
    if not events:
        return f"获取{month}月{day}日的历史事件失败"
    lines = [f"历史上的{month}月{day}日："]
    for e in events[:count]:
        year = e.get("year", "?")
        desc = e.get("description", "")
        lines.append(f"  {year}年：{desc[:60]}")
    return "\n".join(lines)
