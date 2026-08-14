"""意图分类规则 — 单一来源，消除 voice_agent._normalize_intent 和 _classify_intent 的硬编码

LLM 原始意图 → MCP 名称映射（_normalize_intent）
关键词集合 → MCP 名称映射（_classify_intent 快速预判）

新增技能只需在此文件添加规则，无需修改 voice_agent.py 多处代码。
"""

# ── LLM 原始意图映射 ──
# raw_intent 包含任一关键词 → 对应 MCP 名
_INTENT_MAP = [
    ({"amap", "map"}, "amap-maps"),
    ({"baize", "search"}, "baize-skills"),
    ({"music"}, "magic-music"),
    ({"remind"}, "magic-reminder"),
    ({"note"}, "magic-notes"),
    ({"system"}, "magic-system"),
    ({"info"}, "magic-info"),
    ({"life"}, "magic-life"),
    ({"scenes", "scene"}, "magic-scenes"),
    ({"evolution", "learn"}, "magic-evolution"),
    ({"browser"}, "magic-browser"),
    ({"apps"}, "magic-apps"),
    ({"feishu"}, "magic-feishu"),
    ({"douyin"}, "magic-douyin"),
    ({"taobao"}, "magic-taobao"),
    ({"recipe", "cook", "菜", "食谱"}, "magic-recipe"),
    ({"wardrobe", "clothes", "穿搭"}, "magic-wardrobe"),
    ({"magic"}, "magic-music"),
    ({"ac", "air", "control"}, "ac-control"),
    ({"file", "fs"}, "filesystem"),
    ({"vision", "mimo", "screen", "截图"}, "mimo-vision"),
]


def normalize_intent(raw: str) -> str:
    """将 LLM 返回的 raw 意图字符串映射为 MCP 名。

    Args:
        raw: LLM 返回的原始意图字符串

    Returns:
        MCP 名称（如 "amap-maps"），无匹配返回 "none"
    """
    raw = (raw or "").strip().lower()
    for keywords, mcp_name in _INTENT_MAP:
        if any(kw in raw for kw in keywords):
            return mcp_name
    return "none"


# ── 关键词快速预判映射 ──
# 文本包含任一关键词集合 → 直接返回对应 MCP 名，跳过 LLM 调用
_KEYWORD_MAP = [
    ({"天气", "气温", "下雨", "温度", "几度", "穿什么", "今天天气", "明天天气", "今天冷", "今天热"}, "amap-maps"),
    ({"地图", "导航", "附近", "我在哪", "路线", "怎么走", "到哪"}, "amap-maps"),
    ({"搜一下", "查一下", "查查", "谷歌", "购物", "买东西"}, "baize-skills"),
    ({"提醒", "定时", "闹钟", "备忘", "日程", "待办", "记一下", "提醒我"}, "magic-reminder"),
    ({"笔记", "备忘录", "记下来", "记一下"}, "magic-notes"),
    ({"音量", "说慢", "说快", "语速", "大声", "小声"}, "magic-system"),
    ({"状态", "运行", "负载", "设备"}, "magic-system"),
    ({"新闻", "头条", "热点"}, "magic-info"),
    ({"时间", "几点", "日期", "星期"}, "magic-info"),
    ({"翻译", "翻成", "英语说", "怎么说"}, "magic-info"),
    ({"计算", "算一下", "换算", "等于多少", "等于几", "加", "减", "乘", "除"}, "magic-info"),
    ({"放歌", "放一首", "放个", "播放", "听歌", "放周杰伦", "放毛不易", "音乐", "歌单",
      "停止播放", "每日推荐", "随机", "来一首", "播一首", "点一首", "放首", "放点",
      "整首", "整点", "循环", "单曲", "来首", "点歌", "唱首歌", "放音乐"}, "magic-music"),
    ({"空调", "电视", "制冷", "制热", "风扇", "开灯", "关灯", "关闭空调", "关闭电视"}, "ac-control"),
    ({"文件", "读文件", "写文件", "笔记"}, "filesystem"),
    ({"外卖", "点餐", "购物", "商品", "查一下", "充电桩", "特斯拉", "出门"}, "magic-life"),
    ({"做菜", "菜谱", "食谱", "做什么菜", "食材", "吃什么", "吃饭", "怎么做", "做法",
      "怎么煮", "怎么炒", "今天吃啥", "今晚吃啥", "中午吃啥", "推荐个菜", "推荐一道菜",
      "凉菜", "热菜", "汤", "主食", "下饭", "买菜", "番茄炒蛋", "可乐鸡翅"}, "magic-recipe"),
    ({"学习", "进化", "自进化", "优化", "自我优化", "自学习", "学习进度", "进化状态"}, "magic-evolution"),
    ({"淘宝", "京东", "比价", "商品", "价格对比", "买东西", "购物", "买"}, "magic-taobao"),
    ({"浏览器", "打开网页", "打开网站", "访问", "浏览", "爬取", "截图", "页面", "网页", "百度"}, "magic-browser"),
    ({"微信", "支付宝", "今日头条", "美团", "拼多多", "大众点评", "猫眼", "大麦", "咸鱼",
      "外卖", "酒店", "机票", "火车票", "高铁", "电影票", "餐厅", "日料", "火锅",
      "美食", "门票", "演出", "演唱会"}, "magic-apps"),
    ({"飞书", "飞书文档", "飞书消息", "飞书日历", "日历"}, "magic-feishu"),
    ({"抖音", "douyin", "抖音搜索", "抖音视频", "抖音热搜", "热门视频", "热搜"}, "magic-douyin"),
    ({"晚安", "睡觉", "好梦", "休息吧", "睡吧", "睡", "goodnight"}, "magic-scenes"),
    ({"早上好", "早安", "起床", "good morning", "上午好"}, "magic-scenes"),
    ({"电影", "看电影", "视频", "追剧", "观影", "movie"}, "magic-scenes"),
    ({"看看屏幕", "屏幕上有什么", "截图分析", "帮我看看屏幕", "截屏", "识别图片",
      "图上有什么", "看看这张图", "看看这张", "看看这个图", "屏幕上显示什么", "屏幕上有啥"}, "mimo-vision"),
]


def get_all_domain_keywords() -> set[str]:
    """返回所有领域关键词的并集，用于闲聊短句过滤。"""
    all_kw: set[str] = set()
    for kw_set, _ in _KEYWORD_MAP:
        all_kw |= kw_set
    return all_kw


def classify_by_keyword(text: str) -> str | None:
    """关键词预判：如果文本匹配任一领域关键词集合，直接返回 MCP 名。

    Args:
        text: 用户输入文本

    Returns:
        MCP 名称，无匹配返回 None
    """
    for keywords, mcp_name in _KEYWORD_MAP:
        if any(kw in text for kw in keywords):
            return mcp_name
    return None