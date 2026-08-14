# Charlie 项目 SMD 综合评估报告

> **评估日期**: 2026-08-14
> **评估框架**: SMD v3 (Smart Development System)
> **评估方式**: 三角色并行评估 (审查员 + 架构师 + 安全专家)
> **项目版本**: v3.2.0 (`custom` 分支)

---

## 📊 综合评分

| 维度 | 评分 | 评估者 | 权重 |
|------|------|--------|------|
| **代码质量** | 6.5 / 10 | 审查员 (code-review) | 35% |
| **架构设计** | 7.0 / 10 | 架构师 (codebase-design) | 35% |
| **安全性** | 4.5 / 10 | 安全专家 (grilling) | 30% |
| **综合评分** | **6.0 / 10** | — | 100% |

> 综合得分 = 6.5 × 0.35 + 7.0 × 0.35 + 4.5 × 0.30 = **6.0**

---

## 一、项目概览

| 指标 | 数值 |
|------|------|
| 语言 | Python 3.12+ |
| 核心框架 | FastAPI + Qwen-Agent + MCP |
| 源码行数 | ~12,000 行 Python |
| Python 模块 | 38 个 |
| 测试文件 | 22 个 |
| 测试函数 | 507 个 |
| 测试代码行数 | ~9,200 行 |
| 代码/测试比 | ~1:0.77 |
| Git 提交数 | 54 |
| 分支 | `custom` (当前), `main` |

---

## 二、各维度详细评估

### 2.1 代码质量: 6.5/10 (审查员)

#### ✅ 优势

| 领域 | 评价 |
|------|------|
| 安全基础 | `auth.py` 正确防止 X-Forwarded-For 欺骗；编译正则进行输入清洗；安全数学求值 |
| 并发安全 | `reminders.py` 使用 fcntl.flock 文件锁；`_locked_history_file` 避免锁内 I/O |
| 韧性设计 | 指数退避重试 + 抖动；大脑熔断器；TTS 熔断 |
| 测试基础设施 | 25+ 测试文件；`ASSISTANT_KID_DATA_DIR` 隔离；autouse 清理 fixtures |
| 热重载 | `_reload_runtime_env()` 允许不停机配置变更 |
| 日志 | JSON 格式化选项；RotatingFileHandler；结构化前缀 |

#### ❌ 关键问题

1. **上帝文件**: `voice_server.py` 3,829 行，承载路由/调度/认证/缓存/静态文件/ESP32 烧录等
2. **重复逻辑**: `app/weather.py` 和 `magic-info.py` 含几乎相同的城市映射和地理编码
3. **命名不一致**: `voice_server.py` 导入别名 `_b64`, `_json`, `_j`, `_t` 缺乏一致性
4. **全局状态**: `_brains`, `_intent_cache`, `_brain_failures` 等大量模块级可变状态
5. **动态导入反模式**: `load_magic_module()` 绕过静态分析，IDE 无法导航
6. **测试同步异味**: `test_voice_agent.py` 的 `_sync_agent_state()` 手动同步 40+ 属性
7. **宽泛异常捕获**: 多处 `except Exception` 吞没 `KeyboardInterrupt` 和编程错误
8. **硬编码魔法数字**: `_MAX_BRAIN_FAILURES = 5`, `if len(text) <= 6` 等
9. **死代码**: `voice_server.py:2630` 不可达的 `return _manifest_response(request)`
10. **日志不一致**: 不同模块使用不同 logger 命名约定

#### 测试覆盖缺口

| 缺失测试 | 影响 |
|----------|------|
| MCP 注册表解析逻辑 | 核心功能无测试 |
| 意图分类器边界情况 | 关键词匹配未覆盖 |
| 限流器行为 | 安全关键路径无测试 |
| WebSocket xiaozhi 协议 | 协议层无测试 |
| `app/mqtt_server.py` | 695 行无测试 |
| `app/feishu_bot.py` | 243 行无测试 |
| `app/background_task.py` | 后台任务无测试 |

---

### 2.2 架构设计: 7.0/10 (架构师)

#### 深层模块 (优秀)

| 模块 | 行数 | 杠杆率 | 评价 |
|------|------|--------|------|
| `agent/intent.py` | 78 | ⭐⭐⭐⭐ | 小接口大实现，3 函数处理 ASR 后处理全部逻辑 |
| `app/mcp_registry.py` | 83 | ⭐⭐⭐⭐⭐ | 重构成功案例，一行 resolve() 控制 20+ 技能 |
| `app/mcp_gate.py` | 107 | ⭐⭐⭐⭐⭐ | 核心/可选分层 + key 依赖过滤，清晰的边界 |
| `mcp_common.py` | 66 | ⭐⭐⭐⭐ | 20 个 skill 共享工具，消除重复 |
| `agent/cache.py` | 30 | ⭐⭐⭐ | LRU+TTL 缓存抽象简洁 |

#### 浅层模块 (需改进)

| 模块 | 行数 | 问题 |
|------|------|------|
| `voice_server.py` | 3,829 | 上帝模块，路由/调度/指标混杂 |
| `voice_agent.py` | 1,555 | 意图分类 + 大脑构建 + MCP 解析 + 历史管理 |
| `app/state.py` | 370 | 连接管理 + 指标 + 限流三个不相关概念混在一起 |
| `app/xiaozhi_ws.py` | 972 | 文件体积大，WS 协议与业务逻辑耦合 |

#### 架构异味

1. **上帝模块**: voice_server.py + voice_agent.py 严重膨胀
2. **全局状态过多**: `_brains`, `_intent_cache`, `_session` 等模块级变量
3. **霰弹式手术风险**: 新增技能需修改 `mcp_gate.py`, `system_msg.py`, `_normalize_intent()` 多处
4. **反向依赖**: Agent 层过度依赖 App 层（`voice_agent` → `app.llm_config`, `app.mcp_registry`）
5. **信息泄露**: `ALL_MCP` 配置字典模块级可见，调用方知晓内部实现细节

#### Seam 质量

| Seam | 质量 | 评价 |
|------|------|------|
| `agent/intent.py` ↔ `voice_agent.py` | ⭐⭐⭐ | 清晰的后处理接口 |
| `app/mcp_registry.py` ↔ `voice_agent._build_brain` | ⭐⭐⭐ | 重构后分离良好 |
| `skills/*` ↔ `mcp_common.py` | ⭐⭐⭐ | 共享工具层，低耦合 |
| `voice_server.py` ↔ `voice_agent.py` | ⚠️ | 紧耦合，互相导入 |
| `app/state.py` 全局状态 | ⚠️ | 隐式共享，难测试 |

---

### 2.3 安全性: 4.5/10 (安全专家) ⚠️

#### 🔴 关键漏洞 (P0)

| ID | 漏洞 | 文件:行号 | 影响 |
|----|------|-----------|------|
| **C1** | `exec()` 沙箱可被轻易绕过 | `magic-info.py:327` | 远程代码执行，完全控制主机 |
| **C2** | .env 密钥可能被意外提交 | 根目录 `.env` | API 密钥泄露 |

**C1 详情**: `exec(code, {'__builtins__': __builtins__})` 传入完整 `__builtins__`，`_BLOCKED_MODULES` 定义了但从未检查。攻击者可通过 `__import__('os').system('cmd')` 绕过。

#### 🟠 高风险 (P1)

| ID | 问题 | 文件 |
|----|------|------|
| H1 | CORS 配置过于宽松，`allow_credentials=True` | `voice_server.py:434` |
| H2 | 自签证书有效期 10 年 | `app/cert.py:34` |
| H3 | MQTT 密码明文返回 OTA | `voice_server.py:2246` |
| H4 | 进程间通信 `verify=False` | `voice_server.py:862` |
| H5 | WebSocket token 比较非恒定时间 | `voice_server.py:2276` |

#### 🟡 中风险 (P2)

- M1: 内部 API 端点认证薄弱
- M2: 请求体大小限制可被分块编码绕过
- M3: 默认无认证运行 (`AUTH_TOKEN` 默认为空)
- M4: session_id 默认 "default" 导致多用户历史混用
- M5: 日志可能泄露堆栈信息

#### ✅ 良好安全实践

- 输入清洗 (`_sanitize_text` 去除 XSS)
- 请求体大小限制中间件
- 速率限制 (IP 级 + Session 级)
- HMAC token 比较 (HTTP 端)
- 安全数学求值测试覆盖
- 依赖版本均为最新

---

## 三、SMD 综合建议

### 优先级矩阵

| 优先级 | 类别 | 改进项 | 工作量 | 影响 |
|--------|------|--------|--------|------|
| **P0** | 🔴 安全 | 修复 `exec()` 沙箱 (C1) | 2-4h | 消除 RCE |
| **P0** | 🔴 安全 | 确保 .env 安全 (C2) | 30min | 防止密钥泄露 |
| **P0** | 🏗️ 架构 | 拆分 `voice_server.py` | 高 | 降低维护成本 60%+ |
| **P0** | 🏗️ 架构 | 拆分 `voice_agent.py` | 中 | 提升可测试性 |
| **P1** | 📝 代码 | 消除 weather 重复逻辑 | 低 | 修复 Divergent Change |
| **P1** | 📝 代码 | 移除 `_sync_agent_state()` | 中 | 减少测试脆弱性 |
| **P1** | 🏗️ 架构 | 状态对象化 (BrainManager 等) | 中 | 提升可测试性 |
| **P1** | 🔒 安全 | 收紧 CORS + 缩短证书有效期 | 2h | 降低攻击面 |
| **P1** | 🔒 安全 | WebSocket 使用恒定时间比较 | 15min | 防定时攻击 |
| **P2** | 📝 代码 | 替换动态 `load_magic_module()` | 中 | 启用静态分析 |
| **P2** | 📝 代码 | 宽泛 `except` → 具体异常 | 中 | 更快捕获编程错误 |
| **P2** | 🏗️ 架构 | 意图规则外化为配置表 | 低 | 消除霰弹手术 |
| **P2** | 🔒 安全 | 增强内部 API 认证 | 1h | 防内部攻击 |
| **P3** | 📝 代码 | 添加类型注解 | 中 | IDE 支持 |
| **P3** | 📝 代码 | 补充测试覆盖 (MQTT/feishu/限流) | 中 | 补测试缺口 |
| **P3** | 🔒 安全 | 实现日志脱敏 | 2h | 防信息泄露 |

---

## 四、修复路线图

### 阶段 1: 紧急修复 (本周)

```
🔴 C1: 修复 exec() 沙箱
    └── 使用 ast 树遍历验证 / RestrictedPython / 改用空 globals
🔴 C2: 审计 .gitignore + 密钥安全性
🏗️ 提取 weather 重复逻辑到 app.weather
🔒 H5: WebSocket 使用 hmac.compare_digest
```

### 阶段 2: 架构重构 (2-4 周)

```
🏗️ 拆分 voice_server.py → app/routes/*.py + app/schedulers/*.py
🏗️ 拆分 voice_agent.py → agent/pipeline.py + agent/intent_classifier.py
🏗️ 状态对象化 → BrainManager, IntentCache 类
📝 移除 _sync_agent_state() 修复模块边界
```

### 阶段 3: 安全加固 (1-2 周)

```
🔒 收紧 CORS 配置
🔒 证书有效期降至 1 年 + 自动轮换
🔒 增强内部 API 认证
🔒 修复请求体大小限制绕过
🔒 添加安全测试 (WS 绕过 / CORS 边界 / MCP 权限)
```

### 阶段 4: 持续改进 (持续)

```
📝 类型注解 + 死代码清理
📝 补充测试覆盖
🏗️ 意图规则外化配置
🔒 日志脱敏 + 依赖扫描自动化
```

---

## 五、Grilling 问题（架构应回答）

1. **代码执行边界**: `run_code()` 工具为何通过 MCP 暴露给 LLM？是否有调用频率限制和审计？
2. **多租户隔离**: 不同 session_id 的对话历史和偏好是否真正隔离？
3. **IoT 命令审计**: 空调控制、红外发射是否有操作日志和回滚？
4. **证书生命周期**: 自签证书私钥如何备份恢复？10 年有效期合规吗？
5. **第三方 API 配额**: 百度 ASR/TTS、飞书 API 是否有本地限流？
6. **语音数据保留**: 对话历史和音频记录的保留策略？用户能否删除？
7. **OTA 更新安全**: ESP32 固件更新是否验证签名？传输通道是否加密？
8. **应急响应**: 密钥泄露后的轮换流程？是否有过期机制？

---

## 六、结论

Charlie 是一个**功能丰富、设计用心**的语音助手项目，在工程直觉和防御性编程方面展现了扎实的基础。核心架构（MCP 分层、意图路由、三级 LLM 降级）设计合理，测试基础设施完善（507 个测试函数，代码/测试比 0.77）。

然而，项目面临三个主要挑战：

1. **安全性** (4.5/10): `exec()` 沙箱漏洞是最大风险，需立即修复
2. **可维护性**: 上帝模块随着功能增长持续膨胀，需结构化拆分
3. **技术债务**: 全局状态、动态导入、重复逻辑等需要系统性清理

**修复 C1 后安全评分可提升至 6.5/10，综合评分可达 6.7/10。**

---

*报告由 SMD v3 框架生成*
*三角色并行评估: 审查员 + 架构师 + 安全专家*
*完整子报告: `docs/architecture-analysis-2026-08-14.md`, `SECURITY_AUDIT_REPORT.md`*