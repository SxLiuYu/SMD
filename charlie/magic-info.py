"""magic-info: 信息查询 (6个工具: 时间/天气/新闻/位置/翻译/计算)"""
from app.magic_base import create_magic_mcp, get_magic_logger
from mcp_common import aliyun_chat, _safe_math_eval, ESP32_IP
from datetime import datetime
import os, requests
log = get_magic_logger("magic")
mcp = create_magic_mcp("magic-info")


@mcp.tool()
def get_current_time() -> str:
    log.debug("[info] get_current_time 被调用")
    """获取当前时间、日期和星期"""
    now = datetime.now()
    w = ['一','二','三','四','五','六','日'][now.weekday()]
    return f"现在是 {now.strftime('%Y年%m月%d日 %H:%M:%S')}，星期{w}"


@mcp.tool()
def get_detailed_weather(city: str = "北京") -> str:
    log.debug(f"[info] get_detailed_weather(city={city})")
    """获取详细天气预报，包括今天白天/夜间天气、温度、逐小时预报和穿衣建议。

    例: get_detailed_weather() → 返回今天详细天气+穿衣建议
        get_detailed_weather("上海") → 返回上海天气
    """
    # 委托到 app.weather 统一入口（AMAP → Open-Meteo 兜底，消除重复逻辑）
    from app.weather import get_weather_text
    return get_weather_text(city)


@mcp.tool()
def get_news(topic: str = "科技", count: int = 5) -> str:
    """获取最新新闻。topic=新闻主题(科技/财经/社会/体育/国际), count=条数

    例: get_news("科技") → 获取最新科技新闻
        get_news("财经", 3) → 获取3条财经新闻
    """
    # 优先 OkSurf 免费 API（无需 Key），降级 Bing 爬取
    oksurf_map = {"科技": "Technology", "财经": "Business", "商业": "Business",
                  "体育": "Sports", "健康": "Health", "科学": "Science",
                  "国际": "World", "世界": "World", "娱乐": "Entertainment"}
    category = oksurf_map.get(topic)
    if category:
        try:
            r = requests.get("https://ok.surf/api/v1/cors/news-feed",
                headers={"Accept": "application/json"}, timeout=10)
            items = r.json().get(category, [])
            if items:
                results = []
                for item in items[:count]:
                    title = item.get("title", "")
                    link = item.get("link", "")
                    if title:
                        results.append(f"• {title}\n  {link}")
                if results:
                    log.info(f"[info] OkSurf新闻成功: {topic} → {len(results)}条")
                    return f"最新{topic}新闻（{len(results)}条）：\n" + "\n\n".join(results)
        except Exception as e:
            log.debug(f"[info] OkSurf新闻失败: {e}")

    # 降级: Bing 爬取
    import sys, re, html as htmlmod
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    query = f"{topic}新闻 最新"
    try:
        r = requests.get('https://cn.bing.com/search',
            params={'q': query, 'count': count * 2},
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
            timeout=15)
        blocks = re.findall(r'<li class="b_algo".*?</li>', r.text, re.DOTALL)
        results = []
        for b in blocks[:count * 2]:
            title_m = re.search(r'<h2[^>]*>(.*?)</h2>', b, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else ''
            title = htmlmod.unescape(title)
            snippet_m = re.search(r'<p[^>]*>(.*?)</p>', b, re.DOTALL)
            snippet = re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip() if snippet_m else ''
            snippet = htmlmod.unescape(snippet)
            if title and len(title) > 5:
                results.append(f"• {title}\n  {snippet[:60]}")
        if not results:
            return f"没找到{topic}相关新闻"
        return f"最新{topic}新闻（{len(results[:count])}条）：\n" + "\n\n".join(results[:count])
    except Exception as e:
        return f"获取新闻失败: {e}"


@mcp.tool()
def get_location() -> str:
    """获取用户当前位置：ESP32 WiFi扫描(室内定位) + 浏览器GPS经纬度反向地理编码。
    返回城市/街道/经纬度。当用户问'我在哪''附近有什么'时调用。"""
    parts = []
    try:
        r = requests.get(f"http://{ESP32_IP}/api/wifi/scan", timeout=10)
        if r.status_code == 200:
            aps = r.json()
            if aps:
                parts.append(f"WiFi扫描到{len(aps)}个AP:")
                for ap in aps[:5]:
                    parts.append(f"  {ap.get('ssid','?')} RSSI={ap.get('rssi','?')}dBm")
                strongest = max(aps, key=lambda x: x.get('rssi', -999))
                if strongest.get('rssi', -999) > -50:
                    parts.append(f"最强信号: {strongest['ssid']}({strongest['rssi']}dBm) → 可能在室内")
    except Exception as e:
        parts.append(f"ESP32 WiFi扫描失败: {type(e).__name__}")

    try:
        amap_key = os.getenv("AMAP_KEY", "")
        if amap_key:
            r2 = requests.get(f"https://restapi.amap.com/v3/ip?key={amap_key}&output=json", timeout=5)
            data = r2.json()
            if data.get("city"):
                parts.append(f"IP定位: {data.get('province','')} {data.get('city','')}")
                if data.get("rectangle"):
                    parts.append(f"坐标范围: {data['rectangle']}")
        else:
            # 降级 ip-api.com（免费无Key）
            from app.geo import locate
            loc = locate()
            if loc:
                parts.append(f"IP定位: {loc.get('country','')} {loc.get('region','')} {loc.get('city','')}")
                parts.append(f"经纬度: {loc.get('lat','')}, {loc.get('lon','')}")
    except Exception as e:
        parts.append(f"IP定位失败: {type(e).__name__}")

    if len(parts) <= 1:
        return "无法获取位置信息。请在浏览器中允许定位权限，或确保ESP32在线。"
    return "\n".join(parts)


@mcp.tool()
def translate(text: str, target: str = "英文") -> str:
    """翻译。text=内容, target=目标语言(英文/中文/日文/韩文)"""
    return aliyun_chat([
        {"role": "system", "content": f"你是翻译引擎，把用户内容翻译成{target}，只输出译文。"},
        {"role": "user", "content": text}
    ])


@mcp.tool()
def calculate(expression: str) -> str:
    """计算或单位换算。expression=算式如'123*456'或'5公里等于多少英里'"""
    import re
    e = expression.strip().rstrip("=＝")
    if re.fullmatch(r"[\d.\s+\-*/()%^]+", e):
        result = _safe_math_eval(e.replace("^", "**"))
        if result is not None:
            return f"{e} = {result}"
    return aliyun_chat([{"role":"system","content":"你是计算换算助手，直接给结果和一行过程"},
        {"role":"user","content":expression}], temperature=0)


@mcp.tool()
def get_holiday_info(date: str = "") -> str:
    """查询公共假日。date=日期(YYYY-MM-DD)，留空查今天

    例: get_holiday_info() → 今天是否放假、假日名称
        get_holiday_info("2026-10-01") → 查国庆节
    """
    import datetime as _dt
    from app.holiday import get_holidays, get_holiday_name, is_holiday
    try:
        if date:
            d = _dt.date.fromisoformat(date)
        else:
            d = _dt.date.today()
    except ValueError:
        return f"日期格式错误，请用 YYYY-MM-DD 格式"

    name = get_holiday_name(d)
    if name:
        return f"{d.isoformat()} 是公共假日：{name}"
    if is_holiday(d):
        return f"{d.isoformat()} 是公共假日"

    # 列出最近的假日
    holidays = get_holidays(d.year)
    upcoming = [h for h in holidays if h.get("date", "") > d.isoformat()]
    if upcoming:
        next_h = upcoming[0]
        return f"{d.isoformat()} 不是公共假日。最近的是 {next_h['date']} {next_h.get('localName', next_h.get('name', ''))}"
    return f"{d.isoformat()} 不是公共假日"


@mcp.tool()
def get_exchange_rate(amount: float = 1, from_currency: str = "USD", to_currency: str = "CNY") -> str:
    """汇率换算。amount=金额, from_currency=源货币代码, to_currency=目标货币代码

    例: get_exchange_rate(100, "USD", "CNY") → 100美元等于多少人民币
        get_exchange_rate(1000, "CNY", "JPY") → 1000人民币等于多少日元
    """
    from app.exchange_rate import convert, currency_name
    result = convert(amount, from_currency, to_currency)
    if result is None:
        return f"汇率查询失败，不支持 {from_currency}→{to_currency}"
    from_name = currency_name(from_currency)
    to_name = currency_name(to_currency)
    return f"{amount} {from_name}（{from_currency}）= {result} {to_name}（{to_currency}）"


@mcp.tool()
def on_this_day(month: int = 0, day: int = 0, count: int = 5) -> str:
    """历史上的今天。month=月(1-12), day=日(1-31), 留空查今天

    例: on_this_day() → 今天的5条历史事件
        on_this_day(7, 4, 3) → 7月4日的历史事件
    """
    from app.on_this_day import get_events_text
    return get_events_text(month or None, day or None, count)


@mcp.tool()
def get_my_location() -> str:
    """查询当前位置（基于IP定位，无需Key）。
    当用户问'我在哪''我的IP'时调用。"""
    from app.geo import locate_text
    return locate_text()


if __name__ == "__main__":
    mcp.run()


@mcp.tool()
def run_code(code: str) -> str:
    """执行Python代码片段（沙箱模式），用于计算、数据处理、自动化等。

    例: run_code("print(sum(range(100)))") → 计算1到99的和
        run_code("import datetime; print(datetime.datetime.now())") → 获取当前时间
    """
    import sys as _sys, io as _io, json as _json, traceback as _tb, ast as _ast
    _BLOCKED_MODULES = {'os', 'subprocess', 'shutil', 'socket', 'ctypes', 'signal',
                        'multiprocessing', 'threading', 'fcntl', 'sys', 'pickle',
                        'marshal', 'code', 'codeop', 'pty', 'posix', 'pwd', 'grp',
                        'crypt', 'gc', 'traceback', 'bdb', 'pdb', 'profile',
                        'cgitb', 'inspect', 'site', 'compileall', 'py_compile',
                        'zipimport', 'pkgutil', 'modulefinder', 'runpy', 'importlib'}
    _BLOCKED_ATTRS = {'__import__', '__subclasses__', '__bases__', '__mro__',
                      '__class__', '__subclasshook__', '__init_subclass__',
                      '__prepare__', '__instancecheck__', '__subclasscheck__',
                      '_getframe', '_get_ident', 'system', 'popen', 'exec',
                      'eval', 'compile', 'breakpoint', 'open', 'input',
                      '__loader__', '__spec__', '__package__', '__cached__',
                      '__file__', '__path__', '__name__', '__doc__',
                      '__builtins__', '__builtin__', '__debug__',
                      'getattr', 'setattr', 'delattr', 'hasattr',
                      '__getattribute__', '__setattr__', '__delattr__',
                      'globals', 'locals', 'vars', 'dir'}

    def _check_ast(node, depth=0):
        """AST 遍历检查危险操作，抛 SyntaxError 阻止执行"""
        if depth > 50:
            raise SyntaxError("代码嵌套层级过深")
        if isinstance(node, _ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] in _BLOCKED_MODULES:
                    raise SyntaxError(f"禁止导入模块: {alias.name}")
        elif isinstance(node, _ast.ImportFrom):
            if node.module and node.module.split('.')[0] in _BLOCKED_MODULES:
                raise SyntaxError(f"禁止导入模块: {node.module}")
        elif isinstance(node, _ast.Attribute):
            if isinstance(node.attr, str) and node.attr in _BLOCKED_ATTRS:
                raise SyntaxError(f"禁止访问属性: {node.attr}")
        elif isinstance(node, _ast.Name):
            if isinstance(node.id, str) and node.id in _BLOCKED_ATTRS:
                raise SyntaxError(f"禁止使用名称: {node.id}")
        elif isinstance(node, _ast.Call):
            if isinstance(node.func, _ast.Name) and node.func.id in _BLOCKED_ATTRS:
                raise SyntaxError(f"禁止调用函数: {node.func.id}")
        for child in _ast.iter_child_nodes(node):
            _check_ast(child, depth + 1)

    _stdout = _io.StringIO()
    _stderr = _io.StringIO()
    _old_stdout = _sys.stdout
    _old_stderr = _sys.stderr
    try:
        _sys.stdout = _stdout
        _sys.stderr = _stderr
        _tree = _ast.parse(code)
        _check_ast(_tree)
        _compiled = compile(_tree, '<code>', 'exec')
        exec(_compiled, {'__builtins__': {
            'print': print, 'len': len, 'range': range, 'int': int, 'float': float,
            'str': str, 'bool': bool, 'list': list, 'dict': dict, 'tuple': tuple,
            'set': set, 'sum': sum, 'min': min, 'max': max, 'abs': abs, 'round': round,
            'sorted': sorted, 'reversed': reversed, 'enumerate': enumerate, 'zip': zip,
            'map': map, 'filter': filter, 'type': type, 'isinstance': isinstance,
            'issubclass': issubclass, 'chr': chr, 'ord': ord, 'hex': hex, 'oct': oct,
            'bin': bin, 'repr': repr, 'format': format, 'pow': pow, 'divmod': divmod,
            'all': any, 'any': all, 'iter': iter, 'next': next, 'slice': slice,
            'True': True, 'False': False, 'None': None,
            'Exception': Exception, 'ValueError': ValueError, 'TypeError': TypeError,
            'KeyError': KeyError, 'IndexError': IndexError, 'StopIteration': StopIteration,
            'ZeroDivisionError': ZeroDivisionError, 'ArithmeticError': ArithmeticError,
            'AttributeError': AttributeError, 'ImportError': ImportError,
            'LookupError': LookupError, 'RuntimeError': RuntimeError,
            'math': __import__('math'), 'json': __import__('json'),
            'datetime': __import__('datetime'), 're': __import__('re'),
            'collections': __import__('collections'), 'itertools': __import__('itertools'),
            'functools': __import__('functools'), 'random': __import__('random'),
            'statistics': __import__('statistics'),
        }})
        _output = _stdout.getvalue()
        _error = _stderr.getvalue()
        if _output and _error:
            return f"输出:\n{_output}\n错误:\n{_error}"
        elif _output:
            return f"输出:\n{_output}"
        elif _error:
            return f"错误:\n{_error}"
        else:
            return "代码执行成功，无输出。"
    except SyntaxError as _e:
        return f"安全限制: {_e}"
    except Exception as _e:
        return f"执行错误:\n{_tb.format_exc()}"
    finally:
        _sys.stdout = _old_stdout
        _sys.stderr = _old_stderr
