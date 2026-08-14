"""magic-jarvis: 贾维斯级能力（金融行情/环境感知/体育赛事）

自用定制版专属：在 main 开箱即用版基础上增加贾维斯级感知。
全部免费API，无需额外Key。
"""
from app.magic_base import create_magic_mcp, get_magic_logger
import logging

log = logging.getLogger("magic")
mcp = create_magic_mcp("magic-jarvis")


@mcp.tool()
def get_stock(symbol: str = "上证") -> str:
    """查询股票/指数行情。symbol=股票名或代码

    例: get_stock("上证") → 上证指数
        get_stock("茅台") → 贵州茅台
        get_stock("比亚迪") → 比亚迪
        get_stock("sh600519") → 按代码查
    """
    from app.finance import get_stock_text
    return get_stock_text(symbol)


@mcp.tool()
def get_market_overview() -> str:
    """获取市场概览：上证/深证/创业板/汇率"""
    from app.finance import get_stock_batch, get_forex
    indices = get_stock_batch(["上证", "深证", "创业板"])
    forex = get_forex("USDCNY")
    parts = [indices]
    if forex:
        parts.append(f"美元人民币: {forex['bid']:.4f}（买{forex['bid']}/卖{forex['ask']}）")
    return "\n".join(parts)


@mcp.tool()
def get_air_quality(city: str = "北京") -> str:
    """查询空气质量（PM2.5/AQI/紫外线）。city=城市名

    例: get_air_quality() → 北京空气质量
        get_air_quality("上海") → 上海空气质量
    """
    from app.environment import get_air_quality_text
    return get_air_quality_text(city)


@mcp.tool()
def get_earthquake_alert(min_magnitude: float = 4.5) -> str:
    """查询近24小时地震预警。min_magnitude=最低震级(默认4.5)

    例: get_earthquake_alert() → 近24h ≥4.5级地震
        get_earthquake_alert(6.0) → 近24h ≥6.0级重大地震
    """
    from app.environment import get_earthquake_text
    return get_earthquake_text(min_magnitude)


@mcp.tool()
def get_sports(league: str = "英超") -> str:
    """查询今日体育赛事。league=联赛名(英超/西甲/NBA/欧冠等)

    例: get_sports("英超") → 今日英超赛事
        get_sports("NBA") → 今日NBA
        get_sports("全部") → 今日所有赛事
    """
    from app.sports import get_events_text, get_all_sports_today
    if league in ("全部", "所有", "all"):
        return get_all_sports_today()
    return get_events_text(league)


if __name__ == "__main__":
    mcp.run()
