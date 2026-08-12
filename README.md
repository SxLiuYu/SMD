# Charlie 语音助手

> 本地运行的私人 AI 语音助手。ASR → 大脑 LLM → TTS 完整语音闭环，支持 ESP32 手表终端、浏览器、飞书消息推送。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![PyInstaller](https://img.shields.io/badge/Distribution-macOS%20%7C%20Linux%20%7C%20Windows-orange.svg)](docs/WINDOWS_BUILD.md)

---

## ✨ 特性一览

| 能力 | Demo 模式 | 完整模式 |
|------|:---------:|:--------:|
| 时间/日期播报 | ✅ | ✅ |
| 场景 Protocol（早安/晚安等） | ✅ | ✅ |
| 视觉截屏分析 | ✅ | ✅ |
| LLM 对话（天气/翻译/记忆/推荐） | ❌ | ✅ |
| ASR 语音识别（百度 / 本地 SenseVoice） | ✅ 降级 | ✅ 可选本地 |
| TTS 语音合成 | ✅ 降级 | ✅ 完整 |
| MCP 工具（飞书/抖音/淘宝/空调/音乐） | ❌ | ✅ 19 个 |
| ESP32 手表语音终端 | ❌ | ✅ |
| HTTPS 手机访问 | ❌ | ✅ |

**升级路径**：Demo（零配置）→ Ollama 离线 LLM → 填 Key 完整模式，三步渐进解锁。

---

## 🚀 快速上手（5 分钟）

### 方式一：桌面应用（推荐，面向普通用户）

```bash
# 1. 下载 macOS 桌面包（~200MB）
#    见 [release 页面](https://github.com/SxLiuYu/charlie-voice-assistant/releases)
#    或本地：charlie/charlie/dist/charlie

# 2. 解压后双击启动
# 3. 浏览器自动打开 http://localhost:8000/welcome
# 4. 选「Demo 规则模式」→ 说「几点了」✅
```

**解锁完整能力**：引导页选「完整模式」→ 填写 ARK_KEY / 百度 / 高德 key → 重启。

> **首次运行提示**：macOS 可能弹窗"无法验证开发者"，前往 *系统设置 → 隐私与安全性 → 仍要打开*。

### 方式二：Python 开发（面向开发者）

```bash
git clone https://github.com/SxLiuYu/charlie-voice-assistant.git
cd charlie-voice-assistant/charlie

# 1. 虚拟环境 + 安装依赖
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-core.txt
brew install ffmpeg              # 外部二进制，必需

# 2. 配置（可略过，Demo 模式直接可用）
cp .env.example .env
# 编辑 .env 填入你的 API Key，或启动后访问网页填写

# 3. 启动
python3 voice_server.py
# 浏览器打开 http://localhost:8000
```

### 方式三：Docker（v1.1 规划中）

```bash
cp .env.example .env  # 填 key
docker compose up -d
```

---

## 🎙️ 与 Charlie 对话

Charlie 是纯语音交互。麦克风权限需 HTTPS，运行：

```bash
python3 https_server.py   # 自动生成自签证书
# 浏览器访问 https://<Mac-IP>:8443
```

**示例指令**：
- 「几点了」「今天天气怎么样」
- 「晚安」「早安」
- 「帮我记住这句话：XXX」
- 「给张三发消息说会议改到三点」

---

## 📦 Demo 规则模式（零配置）

不填任何 Key 也能对话，3 分钟完成验收：

| 你说 | Charlie 回答 |
|------|-------------|
| 「几点了」 | 实时报时 |
| 「晚安」 | 触发 goodnight 场景（关设备/提醒） |
| 「早安」 | 触发 good_morning 场景 |
| 「看看屏幕」 | 截屏 + AI 分析 |

> 能力受限（天气/翻译/记忆等需 LLM），system_msg 会显示 Demo 横幅提示。

---

## 🔑 密钥获取

| Key | 用途 | 获取地址 |
|-----|------|---------|
| `ARK_KEY` | 大脑 LLM（DeepSeek） | [火山引擎 Ark](https://console.volcengine.com/ark) |
| `BAIDU_APP_ID` + `API_KEY` + `SECRET_KEY` | ASR + TTS | [百度智能云语音](https://console.bce.baidu.com/ai/#/ai/speech) |
| `AMAP_KEY` | 天气 / 地图 | [高德开放平台](https://console.amap.com) |

**可选 Key**（按功能启用）：

| Key | 用途 |
|-----|------|
| `FEISHU_APP_ID` + `SECRET` | 飞书消息推送 |
| `TUYA_CLIENT_ID` + `ACCESS_KEY` | 涂鸦 IoT（空调/灯具） |
| `TAVILY_API_KEY` | Tavily 联网搜索 |
| `ALIYUN_API_KEY` | 阿里云购物分析 |

> 启动后访问 `http://localhost:8000/setup` 网页填写，按分组展示每个 Key 的配置状态。

---

## ⌚ ESP32 手表终端

Charlie 支持 ESP32 LC-S3 1.54 寸 TFT WiFi 手表（xiaozhi 协议），实现独立的语音对话终端。

**支持型号**：`lc-s3-wifi-1.54tft`（LC-S3 1.54 寸圆形 TFT）  
**固件**：xiaozhi v2.1.0，16MB flash，ST7789 240×240 SPI 屏

**烧录（网页向导）**：

```
1. 手表插 USB 连 Mac
2. 浏览器打开 http://localhost:8000/esp32-setup
3. 检测串口 → 输入 WiFi SSID/密码/Charlie IP → 开始烧录
4. 烧录完成后手表自动连接，语音对话
```

> 烧录向导自动 patch 固件 NVS 里的 WiFi/服务器地址，无需重新编译固件。  
> 详细文档：[docs/ESP32.md](docs/ESP32.md)

**性能**：说完 → 首句约 1.16s（ASR+LLM+TTS 全链路）。

---

## 🏗️ 架构概览

```
用户浏览器 / ESP32 手表 (xiaozhi WS)
        ↓
  voice_server.py (FastAPI, port 8000)
    ├── ASR: 百度 / 本地 SenseVoice（26ms vs 327ms）
    ├── 大脑: DeepSeek-v4-flash (火山引擎 Ark) / Ollama 本地
    ├── TTS: qwen3-tts-flash (火山引擎)
    ├── MCP 工具层 (19 个 skill，按 Key 分层启用)
    └── 后台任务: 个性化热点推送（每 1h 飞书）
```

**核心模块**：

| 模块 | 文件 | 职责 |
|------|------|------|
| 主服务 | `voice_server.py` | FastAPI HTTP/WS/SSE 路由 |
| 大脑引擎 | `voice_agent.py` | 意图识别 → LLM → MCP → TTS |
| 环境注册表 | `app/env_catalog.py` | 60 环境变量单一来源 |
| MCP 分层 | `app/mcp_gate.py` | 按 Key 过滤启用的工具 |
| 证书生成 | `app/cert.py` | HTTPS 自签证书自动化 |
| NVS Patch | `app/nvs_patch.py` | ESP32 固件地址动态替换 |
| 预检 | `app/preflight.py` | 外部二进制依赖检测 |

---

## 📁 项目结构

```
charlie-voice-assistant/
├── charlie/                  # 核心源码目录
│   ├── voice_server.py       # FastAPI 主服务入口
│   ├── voice_agent.py        # 大脑引擎
│   ├── charlie_main.py       # PyInstaller 打包入口
│   ├── app/                  # 工具模块
│   │   ├── env_catalog.py    # 60 变量注册表
│   │   ├── mcp_gate.py       # MCP 分层开关
│   │   ├── nvs_patch.py      # ESP32 固件 Patch
│   │   └── cert.py           # HTTPS 证书
│   ├── agent/                # Agent 内部模块
│   │   ├── intent.py         # 意图分类
│   │   ├── preferences.py    # 用户偏好
│   │   └── system_msg.py     # System Prompt 构建
│   ├── web/                  # 前端页面
│   │   ├── voice.html        # 主对话界面
│   │   ├── setup.html        # Key 配置页
│   │   ├── welcome.html      # 首次引导页
│   │   └── esp32_setup.html  # ESP32 烧录向导
│   ├── tests/                # pytest 测试套件（60+ 测试）
│   ├── scripts/              # gen-cert.sh / download-models.sh
│   ├── requirements-core.txt # 核心依赖
│   ├── requirements-optional.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── firmware/                 # ESP32 固件 (16MB bin)
├── Baize/                    # Baize MCP 技能生态
├── skills/                   # 社交媒体发布技能
│   ├── douyin-publishing/
│   ├── xiaohongshu-publishing/
│   └── social-media-publishing/
├── docs/                     # 文档
│   ├── DEPLOYMENT.md         # 部署指南
│   ├── DEMO_MODE.md          # Demo 模式说明
│   ├── ESP32.md              # ESP32 烧录详细文档
│   ├── WINDOWS_BUILD.md      # Windows 打包指南
│   └── SPEC-productize.md    # v1.0 产品化 Spec
└── tests/                    # 测试（复用 charlie/tests/）
```

---

## 🧪 测试

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/ -q
```

**测试覆盖**（60+ 用例）：

| 测试文件 | 覆盖范围 |
|---------|---------|
| `test_demo_rule_mode.py` | Demo 规则模式（时间/晚安/截屏） |
| `test_setup_api.py` | Setup 网页 API |
| `test_welcome.py` | 三步引导页 |
| `test_nvs_patch.py` | ESP32 NVS patch（8 用例） |
| `test_esp32_wizard.py` | 烧录向导 |
| `test_mcp_gate.py` | MCP 分层 + Key 过滤 |
| `test_cert.py` | HTTPS 证书自动化 |
| `test_preflight.py` | 外部二进制检测 |
| `test_voice_server.py` | HTTP 接口（3978 行） |
| `test_voice_agent.py` | 对话引擎（1385 行） |

---

## 📋 配置

所有环境变量在 [`charlie/.env.example`](charlie/.env.example) 里，共 60 项，按分组注释：

| 分组 | 变量数 | 说明 |
|------|:------:|------|
| `core` | 5 | LLM / ASR / TTS / 天气（必需） |
| `llm_fallback` | 2 | Ollama 本地降级 |
| `asr_local` | 3 | SenseVoice 本地模型 |
| `push` | 4 | 飞书 / 微信推送 |
| `iot` | 6 | 涂鸦 IoT（空调/灯具） |
| `ecommerce` | 4 | 淘宝 / 拼多多 |
| `social` | 3 | 抖音 / 小红书 |
| `system` | 30+ | 端口/日志/调试参数 |

> 缺失 Key 时只 warning 不阻塞，Demo 模式可兜底运行。

---

## 🔒 安全

- 所有 API Key 存储在本地 `.env`，不上传云端
- 发布前扫描：`bash charlie/scripts/check-leaks.sh`
- HTTPS 自签证书自动过期保护（cert/ 目录，已加入 .gitignore）
- ESP32 固件已移除 NVS 中硬编码的网络凭证

---

## 📄 许可证

MIT 开源，保留作者署名。  
详见 [charlie/LICENSE](charlie/LICENSE)。

---

## 🔗 相关文档

| 文档 | 内容 |
|------|------|
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | 完整部署指南（3 种方式） |
| [DEMO_MODE.md](docs/DEMO_MODE.md) | Demo 规则模式原理 |
| [ESP32.md](docs/ESP32.md) | ESP32 烧录详细步骤 |
| [WINDOWS_BUILD.md](docs/WINDOWS_BUILD.md) | Windows 打包指南 |
| [SPEC-productize.md](docs/SPEC-productize.md) | v1.0 产品化 Spec |

---

**GitHub**: [SxLiuYu/charlie-voice-assistant](https://github.com/SxLiuYu/charlie-voice-assistant)
