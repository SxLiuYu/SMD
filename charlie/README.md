# Charlie 语音助手

> 本地运行的私人 AI 语音助手。ASR→大脑→TTS 语音闭环，支持 ESP32 手表终端、浏览器、飞书推送。

## 5 分钟快速上手

### 方式一：桌面应用（推荐，面向普通用户）

1. 下载 `charlie-mac.zip`（macOS，~200MB）
2. 解压到任意目录
3. 双击 `charlie` 启动
4. 浏览器自动打开引导页 → 选「Demo 规则模式」→ 完成
5. 说「几点了」→ Charlie 报时间（零配置可用）

> 解锁完整能力（天气/翻译/记忆/飞书）：引导页选「完整模式」→ 填 ARK_KEY/百度/高德 key → 重启

### 方式二：Python 开发（面向开发者）

```bash
git clone <repo>
cd charlie/charlie
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-core.txt
brew install ffmpeg  # 外部二进制
cp .env.example .env  # 填入你的 key
python3 voice_server.py
# 打开 http://localhost:8000
```

### 方式三：Docker（v1.1，规划中）

```bash
cp .env.example .env  # 填 key
docker compose up -d
```

## Demo 规则模式（零配置可用）

不填任何 key 也能和 Charlie 对话：

- ✅ 「几点了」→ 报时间
- ✅ 「晚安」→ 触发 goodnight 场景
- ✅ 「看看屏幕」→ 截屏分析
- ✅ 智能命令 / 场景 Protocol

无法完成的（需 key）：天气/翻译/记忆/飞书/空调/音乐。引导页选「完整模式」填 key 解锁。

## 密钥获取

| Key | 用途 | 获取地址 |
|---|---|---|
| ARK_KEY | 大脑 LLM（火山引擎） | https://console.volcengine.com/ark |
| BAIDU_APP_ID/API_KEY/SECRET_KEY | ASR + TTS | https://console.bce.baidu.com/ai/#/ai/speech/overview/index |
| AMAP_KEY | 天气 | https://console.amap.com |

可选：FEISHU_APP_ID/SECRET（飞书推送）、TUYA_CLIENT_ID/ACCESS_KEY（空调）、TAVILY_API_KEY（搜索）、ALIYUN_API_KEY（购物分析）

启动后访问 `http://localhost:8000/setup` 用网页填写，按分组展示每个 key 状态。

## ESP32 手表终端

Charlie 支持 ESP32 LC-S3 1.54 寸 TFT WiFi 手表（xiaozhi 协议）：

1. 手表插 USB 连 Mac
2. 打开 `http://localhost:8000/esp32-setup`
3. 检测串口 → 输入 WiFi/服务器 IP → 烧录
4. 手表自动连接 Charlie，语音对话

> 烧录向导自动 patch 固件 NVS 里的 WiFi/服务器地址，不重新编译固件。
> 详见 `docs/ESP32.md`

## HTTPS 手机访问

```bash
python3 https_server.py
# 自动生成自签证书（首次）
# 手机同 WiFi 访问 https://<Mac-IP>:8443，首次需信任证书
```

## 配置项

所有 60 个环境变量在 `.env.example` 里，按分组注释。配置注册表在 `app/env_catalog.py`（单一来源）。

关键配置：
- `MCP_PROFILE=core`（默认 8 个核心 MCP）/ `all`（19 个）/ `custom`（读 MCP_SERVERS）
- `OLLAMA_HOST=http://localhost:11434`（Demo 模式 LLM，可选）
- `ASSISTANT_KID_HTTP_PORT=8000`（HTTP 端口）

## 项目结构

```
charlie/
├── voice_server.py      # FastAPI 主服务 (HTTP/WebSocket/SSE)
├── voice_agent.py       # 大脑引擎 (意图→LLM→MCP→TTS)
├── charlie_main.py      # PyInstaller 入口 (首次启动引导)
├── https_server.py      # HTTPS 副本 (手机访问)
├── app/
│   ├── env_catalog.py   # 60 环境变量注册表
│   ├── config.py        # 端口/LAN IP/CORS
│   ├── preflight.py     # 外部二进制检测
│   ├── mcp_gate.py      # MCP 分层 + key 缺失过滤
│   ├── cert.py          # HTTPS 证书自动生成
│   ├── nvs_patch.py     # ESP32 固件 NVS patch
│   └── ...
├── web/                 # 前端 (voice/setup/welcome/esp32_setup)
├── scripts/             # gen-cert.sh, download-models.sh, check-leaks.sh
├── firmware/            # ESP32 固件 bin (16MB)
├── docs/                # 文档 (SPEC, DEPLOYMENT, ESP32, DEMO_MODE)
└── tests/               # pytest 测试套件
```

## 测试

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/ -q
```

产品化测试（TDD 覆盖）：
- `test_demo_rule_mode.py` — Demo 规则模式（5 测试）
- `test_lan_info.py` — LAN info API + OTA 动态端口（3）
- `test_preflight.py` — 外部二进制检测（4）
- `test_mcp_gate.py` — MCP 分层 + key 过滤（8）
- `test_cert.py` — HTTPS 证书自动生成（4）
- `test_model_download.py` — SenseVoice 模型下载（3）
- `test_setup_api.py` — setup mcp-status API（5）
- `test_welcome.py` — /welcome 引导页（2）
- `test_nvs_patch.py` — ESP32 NVS patch（8）
- `test_esp32_wizard.py` — 烧录向导（5）
- `test_charlie_main.py` — 首次启动检测（4）

## 许可证

MIT 开源，保留作者署名。
