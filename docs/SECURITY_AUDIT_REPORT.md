# Charlie 语音助手安全审计报告

**审计日期**: 2026-07-25  
**审计员**: 安全专家 (Agnes-2.5-Flash)  
**项目路径**: `/Users/sxliuyu/orca/projects/charlie`  
**整体安全评分**: **4.5/10** ⚠️

---

## 执行摘要

Charlie 是一个功能丰富的本地语音助手，集成了 ASR/LLM/TTS 管道、IoT 控制、飞书推送等功能。代码在输入清洗和基础认证方面做了一定工作，但存在**多个高危安全漏洞**，特别是代码执行沙箱的严重缺陷和证书管理不当。

---

## 🔴 关键漏洞 (Critical)

### C1. `exec()` 沙箱可被轻易绕过 - 远程代码执行风险

**文件**: `charlie/magic-info.py:327`

```python
@mcp.tool()
def run_code(code: str) -> str:
    _BLOCKED_MODULES = {'os', 'subprocess', 'shutil', 'socket', ...}
    # ...
    _tree = compile(code, '<code>', 'exec')
    exec(code, {'__builtins__': __builtins__})  # ← 致命缺陷
```

**问题**:
- 虽然定义了 `_BLOCKED_MODULES` 白名单，但**从未实际检查**该限制
- 将 `__builtins__` 传入 `exec()` 的第二个参数意味着所有内置函数（包括 `__import__`, `getattr`, `eval`）都可访问
- 攻击者可以轻松绕过：
  ```python
  __builtins__['__import__']('os').system('whoami')
  # 或
  type(1).__class__.__bases__[0].__subclasses__()  # 遍历所有类
  ```
- 该工具通过 MCP 暴露给 LLM，LLM 可能根据用户指令调用此工具

**影响**: 远程代码执行，完全控制主机

**修复建议**:
```python
# 使用 ast 树遍历验证代码安全性，或
# 使用 RestrictedPython 库，或
# 将 exec 的 globals 设为空字典（移除 __builtins__）
exec(code, {})  # 不提供任何内置函数
```

---

### C2. `.env` 文件可能被意外提交或泄露

**文件**: 根目录 `.env`, `.env.example`

**问题**:
- 存在 `.env.example` 但未在 `.gitignore` 中强制排除 `.env`（需确认）
- 大量敏感密钥存储在明文环境变量中：`ARK_KEY`, `BAIDU_API_KEY`, `FEISHU_APP_SECRET`, `TUYA_ACCESS_KEY` 等
- 日志中可能暴露密钥（需检查日志脱敏逻辑）

**影响**: API 密钥泄露导致第三方服务被盗用

---

## 🟠 高风险发现 (High)

### H1. CORS 配置过于宽松

**文件**: `charlie/voice_server.py:434-539`

```python
class DynamicCORSMiddleware(CORSMiddleware):
    def __init__(self, app, allow_origins=(), **kwargs):
        if callable(allow_origins):
            self._origin_provider = allow_origins
```

**问题**:
- `allow_credentials=True` 配合动态来源列表
- tunnel 来源从文件读取（`tunnel_url.txt`），可能被恶意文件覆盖
- `configured_cors_origins()` 允许用户自定义来源，缺乏验证

**风险**: 跨域请求伪造 (CSRF) 或数据窃取

---

### H2. 自签证书有效期过长

**文件**: `charlie/app/cert.py:34`

```python
.not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))  # 10年!
```

**问题**:
- 10 年有效期违反了安全最佳实践
- 证书和私钥存储在项目目录下（`cert/cert.pem`, `cert/key.pem`）
- 无证书轮换机制

**建议**: 降至 1 年或更短，实现自动轮换

---

### H3. MQTT 凭证安全

**文件**: `charlie/app/mqtt_server.py:148`, `charlie/voice_server.py:2243-2246`

```python
if mqtt_pass:
    ota_response["mqtt"]["password"] = mqtt_pass  # 明文返回密码
```

**问题**:
- MQTT 密码通过 OTA 响应明文返回给 ESP32
- 如果 WebSocket 通信被截获，密码暴露
- ESP32 固件中的密码存储安全性未知

---

### H4. HTTPS 进程间通信禁用证书验证

**文件**: `charlie/voice_server.py:855-862`

```python
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
r = requests.post(
    f"https://{_lan_ip}:{_hport}/api/internal/xiaozhi-push",
    verify=False, timeout=10)
```

**问题**:
- 进程间通信使用 `verify=False` 接受任何证书
- 中间人攻击可在局域网内劫持此通信

---

### H5. WebSocket 认证使用简单字符串比较

**文件**: `charlie/voice_server.py:2272-2278`

```python
if AUTH_TOKEN:
    tk = ws.query_params.get("token", "")
    if tk != AUTH_TOKEN:  # 普通字符串比较，非恒定时间
        await ws.close(code=4001, reason="未授权")
```

**问题**:
- 使用 `!=` 而非 `hmac.compare_digest()` 进行 token 比较
- 可能遭受定时侧信道攻击

**修复**: 使用 `hmac.compare_digest(tk, AUTH_TOKEN)`

---

## 🟡 中风险发现 (Medium)

### M1. 内部 API 端点认证薄弱

**文件**: `charlie/voice_server.py:3784-3795`

```python
@app.post("/api/internal/xiaozhi-push")
async def _internal_xiaozhi_push(payload: dict, request: Request):
    internal_token = os.getenv("INTERNAL_API_TOKEN", "")
    if internal_token:
        auth = request.headers.get("X-Internal-Token", "")
        if auth != internal_token:  # 同样非恒定时间比较
            return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
```

**问题**:
- 未配置 `INTERNAL_API_TOKEN` 时仅依赖本机访问检测
- 内部端点无速率限制

---

### M2. 请求体大小限制绕过风险

**文件**: `charlie/voice_server.py:419-429`

```python
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        cl = request.headers.get("content-length")
        if cl and int(cl) > MAX_REQUEST_BODY:
```

**问题**:
- 仅检查 `Content-Length` 头，攻击者可发送分块编码请求绕过
- 未限制 WebSocket 消息大小（虽有 `MAX_AUDIO_SIZE` 检查但不够）

---

### M3. 默认无认证运行

**文件**: `charlie/app/auth.py:9`

```python
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
```

**问题**:
- 默认 `AUTH_TOKEN` 为空，本地开发时无认证保护
- 公网部署时需显式设置，但 `.env.example` 中提示不足

---

### M4. session_id 默认值为 "default"

**文件**: 多处，如 `charlie/voice_server.py:387`

```python
session_id: str = Field(default="default", ...)
```

**问题**:
- 所有未指定 session_id 的请求共享同一会话历史
- 多用户场景下隐私泄露风险

---

### M5. 日志中可能的信息泄露

**文件**: `charlie/voice_server.py:411`

```python
log.error(f"[500] 未处理异常 {request.method} {request.url.path}: {exc}\n{tb}")
```

**问题**:
- 完整堆栈跟踪记录到日志文件
- 需确认日志文件权限和轮转策略

---

## 🟢 低风险发现 (Low)

### L1. 局域网 IP 探测可能不准确

**文件**: `charlie/voice_server.py:487-496`

```python
def _get_lan_ip() -> str | None:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
```

通过连接外部地址获取本机 IP，在多网卡环境下可能返回错误接口。

### L2. 缺少请求签名验证

所有 API 请求仅依赖 token，无请求签名防重放攻击。

### L3. 临时文件权限

音频临时文件创建未明确设置权限掩码。

---

## 安全测试覆盖评估

### 已有测试 (`tests/test_security_fixes.py`)

✅ **良好实践**:
- 安全数学求值测试 (`_safe_math_eval`)
- 请求体大小限制测试
- 认证代理欺骗防护测试
- 文本清洗正则预编译测试
- 环境变量文档完整性测试

❌ **缺失测试**:
- WebSocket 认证绕过测试
- CORS 边界测试
- MCP 工具权限隔离测试
- 证书有效性测试
- 敏感信息泄露测试

---

## 依赖安全分析

基于 `requirements.txt` 的关键依赖版本:

| 包名 | 版本 | 状态 |
|------|------|------|
| FastAPI | 0.141.1 | ✅ 最新 |
| Uvicorn | 0.52.0 | ✅ 最新 |
| websockets | 17.0 | ✅ 最新 |
| cryptography | 49.0.0 | ✅ 最新 |
| PyJWT | 2.13.0 | ✅ 最新 |
| python-dotenv | 1.2.2 | ✅ 最新 |

建议定期进行依赖漏洞扫描：
```bash
pip-audit -r requirements.txt
# 或
safety check -r requirements.txt
```

---

## "Grilling" 问题清单

架构应回答以下问题：

1. **代码执行边界**: `run_code()` 工具为何通过 MCP 暴露给 LLM？是否有调用频率限制和使用审计？

2. **多租户隔离**: 如果多个用户通过不同 session_id 使用系统，历史对话和偏好设置是否真正隔离？

3. **IoT 命令审计**: Tuya 空调控制、ESP32 红外发射等命令是否有操作日志和回滚机制？

4. **证书生命周期**: 自签证书的私钥如何备份和恢复？10 年有效期是否在合规层面可接受？

5. **第三方 API 配额保护**: 百度 ASR/TTS、飞书 API 等是否有本地限流防止配额耗尽？

6. **语音数据保留**: 对话历史和音频记录的保留策略是什么？用户能否要求删除？

7. **OTA 更新安全**: ESP32 固件更新是否验证签名？传输通道是否加密？

8. **应急响应**: 发现密钥泄露后的轮换流程是什么？是否有密钥过期机制？

---

## 修复优先级建议

| 优先级 | 问题 | 预计工作量 |
|--------|------|-----------|
| P0 | C1: 修复 `exec()` 沙箱 | 2-4 小时 |
| P0 | C2: 确保 .env 不在版本控制中 | 30 分钟 |
| P1 | H1: 收紧 CORS 配置 | 1-2 小时 |
| P1 | H2: 缩短证书有效期 | 30 分钟 |
| P1 | H5: 使用恒定时间比较 | 15 分钟 |
| P2 | M1: 增强内部 API 认证 | 1 小时 |
| P2 | M2: 修复请求体限制绕过 | 2 小时 |
| P2 | 添加缺失的安全测试 | 4-8 小时 |
| P3 | 实现日志脱敏 | 2 小时 |

---

## 结论

Charlie 语音助手在基础安全措施上有一定投入（输入清洗、限流、CORS 动态配置），但存在**严重的代码执行漏洞**（C1）需要立即修复。项目定位为本地局域网使用，降低了部分攻击面，但考虑到其集成 IoT 控制和外部 API，安全加固仍有必要。

**建议优先修复 C1 后评分可提升至 6.5/10。**
