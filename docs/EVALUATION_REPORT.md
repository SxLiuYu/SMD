# Charlie 语音助手 — 全面评估报告

> 评估日期：2026-08-14
> 版本：v3.2.0 (`custom` 分支)
> 源码路径：`charlie/`

---

## 一、项目概览

Charlie 是一个**低成本全屋智能家居语音助手**，用一块 ESP32 开发板（~30元）+ 一台运行 Charlie 的电脑，通过红外、涂鸦 IoT、MCP 工具控制现有家电，实现 **ASR → 大脑 LLM → TTS** 的完整语音闭环。

| 属性 | 值 |
|------|-----|
| 版本 | v3.2.0 |
| 许可证 | MIT |
| 语言 | Python 3.12+ |
| 核心框架 | FastAPI + Qwen-Agent + MCP |
| 源码行数 | ~12,000 行 Python（不含 `dist/`、`.venv`） |
| Python 模块数 | 38 个 |
| 测试函数 | 507 个 |
| 测试代码行数 | ~9,200 行 |
| 分发方式 | Windows 便携版 / Docker / Python 源码 |

---

## 二、架构总览

```
ESP32 开发板 (xiaozhi WS)  ←─WiFi─→  浏览器 (HTTPS/SSE)
              ↓                        ↓
        voice_server.py (FastAPI, port 8000/8443)
              │
              ├── ASR: 百度云端 / 本地 SenseVoice（26ms）
              ├── 大脑: 智谱GLM免费 / 火山ARK / Ollama本地
              ├── TTS: 百度 / Finna降级
              ├── MCP工具: 空调/场景/提醒/飞书/搜索...（19个）
              ├── 决策引擎: 状态感知+时间触发，自主推送
              └── ESP32: 干净固件 + AP热点配网 + OTA + WebSocket
```

### 核心模块

| 模块 | 文件 | 行数 | 职责 |
|------|------|------|------|
| 主服务 | `voice_server.py` | 3,834 | FastAPI HTTP/WS/SSE 路由 + 后台调度 + 生命周期管理 |
| 大脑引擎 | `voice_agent.py` | 1,555 | 意图识别 → FastPath → LLM → MCP → TTS |
| 打包入口 | `charlie_main.py` | 254 | PyInstaller 入口 + MCP 子进程启动 + 原生窗口 |
| LLM 配置 | `app/llm_config.py` | 208 | ARK / GLM / Ollama 三级降级 + 429 轮换 |
| 环境注册表 | `app/env_catalog.py` | 451 | 60 个环境变量单一来源 |
| MCP 注册表 | `app/mcp_registry.py` | 83 | 19 个 MCP 按 Profile + Key 过滤启用 |
| 决策引擎 | `magic-decisions.py` | 794 | 状态感知自主推送，反馈闭环 |
| 场景协议 | `magic-scenes.py` | 569 | 多步操作序列 + 自然语言学习 |
| ESP32 WebSocket | `app/xiaozhi_ws.py` | 972 | Xiaozhi v2.1.0 协议兼容 + Silero VAD 端点检测 |
| MQTT 服务 | `app/mqtt_server.py` | 695 | ESP32 常驻连接 + UDP Opus 加密传输 |
| 飞书机器人 | `app/feishu_bot.py` | 243 | WebSocket 长连接群聊机器人 |

---

## 三、启动 Charlie 后提供的所有功能

### 3.1 HTTP API 端点（共 50+ 个路由）

#### 核心对话 API
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/voice` | POST | 音频进 → ASR → 大脑 → TTS → 音频出（同步） |
| `/api/voice/stream` | POST | 流式语音对话：音频 → ASR → 大脑逐句 → TTS 批量 SSE |
| `/api/chat/stream` | POST | 流式文字对话：文字 → 大脑逐句 → TTS 批量 SSE |
| `/api/chat` | POST | 纯文字对话（同步） |
| `/api/tts` | POST | 文字 → 语音 MP3 |
| `/api/asr` | POST | 音频 → 文字 |

#### 对话 & 历史管理
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/reset` | POST | 清空指定会话的对话历史 |
| `/api/conversation` | GET | 分页获取对话历史 |
| `/api/search` | GET | 搜索对话历史（关键词 + 相关性评分） |
| `/api/sessions` | GET | 列出所有活跃会话 |
| `/api/context` | GET | 对话上下文摘要（含 token 估算） |

#### 提醒 & 待办
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/reminders` | GET | 待办列表（含 ETag 条件请求） |
| `/api/reminders` | POST | 添加提醒（支持 daily/weekly/weekdays 重复） |
| `/api/reminders/{rid}` | DELETE | 删除/完成提醒 |

#### 配置 & 引导
| 端点 | 方法 | 功能 |
|------|------|------|
| `/setup` | GET | 配置页面（HTML） |
| `/welcome` | GET | 首次启动引导页（HTML） |
| `/api/setup` | GET | 读取当前 .env 配置 |
| `/api/setup` | POST | 保存配置到 .env + 热重载 |
| `/api/setup/verify` | POST | 实时校验 GLM/百度 Key 有效性 |
| `/api/setup/mcp-status` | GET | MCP 分组状态 |
| `/api/setup/download-model` | POST | SenseVoice 模型下载 |
| `/api/welcome/status` | GET | 欢迎页配置状态 |

#### ESP32 烧录 & 配网
| 端点 | 方法 | 功能 |
|------|------|------|
| `/esp32-setup` | GET | 烧录向导页面 |
| `/api/esp32/detect-port` | GET | 跨平台检测 ESP32 串口 |
| `/api/esp32/flash` | POST | 触发 ESP32 烧录（esptool 进程内调用） |
| `/api/esp32/flash-status` | GET | 查询烧录进度 |
| `/api/esp32/config-info` | GET | 返回 AP 配网信息（OTA 地址、IP 等） |
| `/xiaozhi/ota` | GET/POST | ESP32 OTA 配置端点 |
| `/ws/xiaozhi` | WebSocket | Xiaozhi 兼容 WebSocket（v2.1.0） |

#### 设备 & 监控
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/devices` | GET | 设备面板（WebSocket + MQTT 客户端 + 连接统计） |
| `/api/metrics` | GET | 请求指标（p50/p95/错误率/缓存命中） |
| `/health` | GET | 健康检查（版本/uptime/大脑就绪/WS 连接数） |
| `/api/logs` | GET | 日志查看器（支持关键词过滤） |
| `/api/tunnel` | GET | 隧道 URL 状态 |
| `/api/lan-info` | GET | 局域网信息 |

#### 场景协议 & 决策引擎
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/protocols` | GET | 场景协议列表（内置 + 自定义） |
| `/api/protocols/learn` | POST | 用自然语言学习新场景 |
| `/api/decisions` | GET | 决策引擎状态（规则/历史/用户状态） |
| `/api/decisions/config` | GET | 决策配置 |
| `/api/behaviors` | GET | 行为 API |
| `/api/habits` | GET | 习惯 API |
| `/api/memory` | GET | 情景记忆 |
| `/api/evolution` | GET | 进化系统状态 |
| `/api/evolution/learn` | POST | 触发进化学习 |

#### 偏好 & 用户
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/preferences` | GET | 获取所有用户偏好 |
| `/api/preferences` | POST | 设置用户偏好 |
| `/api/preferences/{key}` | DELETE | 删除用户偏好 |
| `/api/user/switch` | POST | 切换当前用户 |
| `/api/user/current` | GET | 获取当前用户 |

#### 配置 & 控制
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/brain/restart` | POST | 手动重启大脑 |
| `/api/wake/toggle` | POST | 开关唤醒词检测 |
| `/api/wake/status` | GET | 唤醒词检测状态 |
| `/api/tts/voices` | GET | 列出可用 TTS 音色（6 种） |
| `/api/tts/voice` | POST | 切换 TTS 音色 |
| `/api/mcp/servers` | GET | 列出所有 MCP 服务器及状态 |
| `/api/mcp/toggle` | POST | 启用/禁用 MCP 服务器 |
| `/api/internal/xiaozhi-push` | POST | 内部跨进程 TTS 转发到 ESP32 |
| `/api/notifications` | GET | 通知列表 |
| `/api/events` | GET | SSE 事件流 |
| `/api/export` | GET | 数据导出 |

#### PWA 支持
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 主界面（voice.html） |
| `/manage` | GET | 管理面板 |
| `/test` | GET | 语音测试台 |
| `/manifest.json` | GET | PWA manifest |
| `/service-worker.js` | GET | Service Worker |
| `/favicon.ico` | GET | 应用图标 |

### 3.2 Web 前端页面（6 个页面）

| 页面 | 文件 | 行数 | 功能 |
|------|------|------|------|
| 主界面 | `voice.html` | 728 | 语音对话主界面：Orb 按钮、语音/文字对话、对话历史、状态指示 |
| 配置页 | `setup.html` | 190 | 高级配置：按分组展示 60 个环境变量 |
| 欢迎引导 | `welcome.html` | 213 | 首次启动三步引导：选模式 → 配置 → 完成 |
| 管理面板 | `manage.html` | 393 | 设备管理、对话历史、设置 |
| 测试台 | `voice_test.html` | 299 | 语音对话调试：SSE 事件流 + 延迟指标 |
| ESP32 向导 | `esp32_setup.html` | 180 | 烧录向导：检测串口 → 烧录 → 配网指引 |

### 3.3 MCP 工具生态（19 个工具，按 Profile 分层）

#### 核心工具（8 个，`MCP_PROFILE=core` 时启用）
| 工具 | 文件 | 功能 |
|------|------|------|
| `amap-maps` | `magic-info.py` | 高德地图：时间/天气/翻译/新闻/汇率/体育/农历 |
| `magic-reminder` | `magic-reminder.py` | 提醒/定时器/倒计时 |
| `magic-notes` | `magic-notes.py` | 备忘录/文件读写 |
| `magic-system` | `magic-system.py` | 系统控制：音量/语速/屏幕截图 |
| `magic-life` | `magic-life.py` | 生活服务：外卖/充电桩/环境 |
| `magic-scenes` | `magic-scenes.py` | 场景自动化：晚安/早安/电影/出门 4 个内置场景 |
| `magic-summary` | `magic-summary.py` | 每日/每周摘要 |
| `filesystem` | `magic-notes.py` | 文件系统读写 |

#### 可选工具（11 个，`MCP_PROFILE=all` 时启用）
| 工具 | 文件 | 功能 |
|------|------|------|
| `magic-music` | `magic-music.py` | 音乐播放（ncm-cli） |
| `magic-browser` | `magic-browser.py` | 浏览器控制（ego-lite） |
| `magic-apps` | `magic-apps.py` | App 控制 |
| `magic-feishu` | `magic-feishu.py` | 飞书集成（文档/日历/消息） |
| `magic-douyin` | `magic-douyin.py` | 抖音 |
| `magic-taobao` | `magic-taobao.py` | 淘宝/京东搜索 |
| `magic-evolution` | `magic-evolution.py` | 自进化学习 |
| `magic-wardrobe` | `magic-wardrobe.py` | 穿搭推荐 |
| `magic-recipe` | `magic-recipe.py` | 菜谱推荐 |
| `magic-habits` | `magic-habits.py` | 习惯追踪 |
| `magic-memory` | `magic-memory.py` | 情景记忆 |
| `baize-skills` | `baize_skills_mcp.py` | 互联网搜索（Tavily） |
| `ac-control` | `mcp_ir_control.py` | 涂鸦红外空调控制 |
| `mimo-vision` | `skills/mimo-vision/` | 视觉识别/截屏分析 |

### 3.4 后台调度器（启动时自动运行 8 个）

| 调度器 | 功能 | 触发方式 |
|--------|------|---------|
| 提醒调度器 | 每 30s 检查 `reminders.json`，到期提醒自动 TTS + afplay 播报 | 定时轮询 |
| 主动建议 | 每 15min 根据用户状态/天气/时间/习惯生成主动建议 | 定时轮询 |
| 决策引擎 | 每 60s 融合多信号做推理，自主决定"现在应该做什么" | 定时轮询 |
| 进化引擎 | 每 30min 分析对话历史，自适应学习用户偏好 | 定时轮询 |
| 唤醒监听 | 持续监听 Vosk 离线唤醒词 "Charlie"（含中文谐音） | 后台线程 |
| WebSocket 清理 | 定期清理僵死 WS 连接 | 定时轮询 |
| 飞书机器人 | WebSocket 长连接，群聊中回复 @Charlie 的消息 | 常驻连接 |
| 个性化推送 | 每 1h（可配置）兴趣画像 × 抖音热搜 → LLM 筛选 → 飞书推送 | 定时轮询 |

### 3.5 原生桌面窗口

- **Windows**：pywebview + WebView2，原生桌面窗口（440×760），无浏览器边框
- **macOS/Linux**：pywebview 不可用时自动回退到系统浏览器
- **窗口关闭**：优雅退出，清理 MCP 子进程

---

## 四、LLM 大脑三级降级体系

| 优先级 | 大脑 | 费用 | 特点 |
|--------|------|------|------|
| 1 | 火山引擎 ARK | 按量付费 | 速度最快，限流宽松 |
| 2 | 智谱 GLM (glm-4.7-flash) | **永久免费** | 429 限流时自动轮换到 glm-4-flash / glm-4.5-flash |
| 3 | Ollama 本地 (qwen3.5:2b) | 免费 | 需本地硬件支持，`OLLAMA_ENABLED=1` 启用 |

---

## 五、代码质量评估

### 5.1 架构设计亮点

- **深模块设计**：`voice_server.py` 和 `voice_agent.py` 作为两个核心深模块，接口简洁（~10 个公开函数），内部实现复杂
- **单一来源原则**：`env_catalog.py` 统一管理 60 个环境变量，消除散落在 30+ 文件中的 `os.getenv` 调用
- **MCP 分层**：`mcp_registry.py` + `mcp_gate.py` 按 Profile + Key 自动过滤，用户按需启用
- **配置热重载**：`/welcome` 保存 Key 后 `load_dotenv(override=True)` → `llm_config.reload()` → `asr_tts.reload()` → `voice_agent.reload_brain_config()`，无需重启
- **连接韧性**：429 限流自动轮换模型、大脑熔断（连续 5 次失败自动重建）、TTS 熔断（3 次失败冷却 120s）

### 5.2 测试

| 指标 | 数值 |
|------|------|
| 测试文件 | 22 个 |
| 测试函数 | 507 个 |
| 测试代码行数 | ~9,200 行 |
| 代码/测试比 | ~1:0.77 |

**测试覆盖：** `test_voice_server.py`（3,978 行）、`test_voice_agent.py`（1,385 行）、`test_runtime_resilience.py`（1,413 行）、`test_xiaozhi_ws.py`（460 行）、`test_security_fixes.py`（310 行）等。

### 5.3 文档

- 10 个文档文件（README、CHANGELOG、RELEASE_NOTES、ESP32、部署、Demo 模式、打包等）
- `.env.example` 169 行，60 个环境变量按分组注释
- 双版本架构（OOTB/CUSTOM）有独立说明

---

## 六、功能全景总结

| 能力维度 | 具体功能 |
|----------|---------|
| 🎙️ **语音交互** | 百度云端 ASR + 本地 SenseVoice（26ms）+ 静音检测 + 乱码过滤 + 语气词短路 |
| 🧠 **AI 大脑** | 智谱 GLM 免费 / ARK / Ollama 三级降级，429 模型轮换，流式逐句输出 |
| 🔊 **语音合成** | 百度 TTS + Finna 降级，6 种音色切换，TTS 缓存，Markdown 清洗 |
| 📟 **ESP32 终端** | 烧录向导 + AP 热点配网 + WebSocket/WebRTC Opus 音频 + MQTT 推送 |
| 🏠 **智能家居** | 涂鸦红外空调控制 + 4 个内置场景（晚安/早安/出门/电影）+ 自定义场景 |
| ⏰ **提醒系统** | 文件锁 + 去重 + 投递重试 + 重复规则（daily/weekly/weekdays） |
| 📨 **消息推送** | 飞书群聊机器人（WebSocket 长连接）+ 个性化热点推送 + ntfy 备用通道 |
| 🔌 **MCP 扩展** | 19 个 MCP 工具，按 Profile 分层，运行时动态启用/禁用 |
| 🧬 **自主学习** | 决策引擎（状态感知）+ 进化系统（偏好学习）+ 情景记忆 + 习惯追踪 |
| 🌐 **Web 界面** | 6 个页面（主界面/配置/引导/管理/测试台/ESP32 向导），PWA 支持 |
| 🔒 **安全** | AUTH_TOKEN 鉴权 + HTTPS 自签证书 + 内部 API Token + 限流 |
| 📦 **分发** | Windows 便携版 / Docker / Python 源码，零配置 Demo 模式可用 |