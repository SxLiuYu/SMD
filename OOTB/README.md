# Charlie 语音助手 — 开箱即用版 (OOTB)

面向最终用户的分发版本，无需任何配置即可运行（Demo 模式），填入 Key 即可解锁全部功能。

## 获取方式

| 平台 | 下载 |
|------|------|
| Windows | [Charlie-Portable.zip](https://github.com/SxLiuYu/charlie-voice-assistant/releases) |
| macOS | [charlie-mac-arm64.zip](https://github.com/SxLiuYu/charlie-voice-assistant/releases) |
| Linux | `pip install -r requirements-core.txt` |

解压后双击运行，无需安装 Python。

---

## 版本信息

| 属性 | 值 |
|------|-----|
| 版本 | v3.2.0 |
| Python | 3.12+ |
| 框架 | FastAPI |
| ESP32 固件 | xiaozhi v2.1.0（AP 热点配网，无硬编码） |

---

## 快速开始

### Demo 模式（零配置，立即体验）

```bash
cd OOTB
python3 charlie/voice_server.py
# 浏览器打开 http://localhost:8000
```

### 完整模式（填入 API Key）

```bash
cp charlie/.env.example charlie/.env
# 编辑 .env，填入所需 Key（至少填 BAIDU_APP_ID 等）
python3 charlie/voice_server.py
```

---

## 功能一览

| 功能 | Demo | 完整 |
|------|:----:|:----:|
| 语音对话（ASR→LLM→TTS） | ✅ 降级 | ✅ 完整 |
| ESP32 语音终端 | ✅ | ✅ |
| 空调红外控制 | ❌ | ✅ |
| 场景协议（早安/晚安） | ✅ | ✅ |
| 飞书推送 | ❌ | ✅ |
| MCP 技能扩展（19个） | ❌ | ✅ |
| HTTPS 手机访问 | ❌ | ✅ |

---

## ESP32 开发板

**板型**: LC-S3 1.54 寸 TFT WiFi（~¥30）

**固件**: xiaozhi v2.1.0，16MB flash，NVS 已擦除

**配网步骤**:
1. 烧录 `firmware/` 目录中的 `charlie-esp32-flash-16MB.bin`（GitHub Release 下载）
2. 手机连接 `lc-s3-wifi-1.54tft-XXXX` 热点
3. 浏览器访问 `http://192.168.4.1` 填写 WiFi 和 OTA 地址

详见 [docs/ESP32.md](../docs/ESP32.md)

---

## 项目结构

```
OOTB/
├── README.md              # 本文件
├── charlie/               # 核心源码
│   ├── voice_server.py    # FastAPI 主服务
│   ├── voice_agent.py     # 大脑引擎
│   ├── .env.example       # 环境变量模板
│   ├── app/               # 子模块（MQTT/ASR/TTS/LLM）
│   ├── agent/             # 意图/历史/偏好
│   ├── web/               # 前端页面
│   └── tests/             # pytest 测试
├── firmware/              # ESP32 固件说明
├── docs/                  # 用户文档
├── scripts/               # 工具脚本
└── skills/                # MCP 技能生态
```

---

## 许可证

MIT — [SxLiuYu/charlie-voice-assistant](https://github.com/SxLiuYu/charlie-voice-assistant)
