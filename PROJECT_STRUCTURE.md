# Charlie 项目结构

## 双版本架构

```
charlie-voice-assistant/
│
├── OOTB/                          # 开箱即用版（分发）
│   ├── README.md                  # 用户文档
│   ├── charlie/                   # 核心源码（不含 .env 和密钥）
│   │   ├── .env.example           # 环境变量模板（空值，安全）
│   │   ├── voice_server.py        # FastAPI 主服务
│   │   ├── voice_agent.py         # 大脑引擎
│   │   ├── app/                   # 子模块
│   │   ├── agent/                 # 意图/历史/偏好
│   │   ├── web/                   # 前端页面
│   │   └── tests/                 # 测试用例
│   ├── firmware/                  # ESP32 固件说明（公版 bin）
│   ├── docs/                      # 用户文档
│   ├── scripts/                   # 工具脚本
│   └── skills/                    # MCP 技能生态
│
├── CUSTOM/                        # 自用定制版（开发）
│   ├── README.md                  # 开发文档
│   ├── charlie → ../charlie       # 符号链接到主项目（含 .env）
│   └── esp32_firmware/            # LC-S3 固件配置
│       ├── custom/               # 自定义固件构建配置
│       └── ootb/                  # OOTB 固件说明
│
├── charlie/                       # 主项目源码（开发用）
│   ├── .env                       # 个人密钥（不进 git）
│   ├── .env.example               # 公开模板
│   ├── voice_server.py            # FastAPI 主服务（2723 行）
│   ├── voice_agent.py             # 大脑引擎（2589 行）
│   ├── app/                       # 40+ 子模块
│   ├── agent/                     # 6 个 Agent 模块
│   ├── web/                       # 前端 HTML/JS
│   ├── skills/                    # MCP 技能
│   ├── tests/                     # pytest 测试
│   ├── data/                      # 运行时数据（不进 git）
│   ├── logs/                      # 日志（不进 git）
│   └── esp32_firmware/            # 固件文档（同上）
│
├── firmware/                      # ESP32 固件分发说明
├── docs/                          # 项目文档
├── scripts/                       # 工具脚本
├── skills/                        # 公共技能
├── README.md                      # 项目总览
├── CHANGELOG.md                   # 更新日志
├── .gitignore                     # Git 忽略规则
└── .github/workflows/ci.yml       # CI 配置
```

## 关键路径

| 用途 | 路径 |
|------|------|
| 源码（开发） | `charlie/` |
| 源码（分发） | `OOTB/charlie/` |
| 个人配置 | `charlie/.env` |
| 模板配置 | `charlie/.env.example` |
| ESP32 固件源码 | `/Users/sxliuyu/repos/xz/` |
| ESP32 固件配置 | `charlie/esp32_firmware/custom/` |
| 固件构建 | `charlie/esp32_firmware/custom/build.sh` |
| ESP32 文档 | `docs/ESP32.md` |
| 主服务启动 | `python charlie/voice_server.py` |
| 测试 | `python -m pytest charlie/tests/` |

## .gitignore 关键规则

```
charlie/.env                    # 个人密钥
charlie/.baidu_token*.json      # OAuth token
charlie/dist/                   # 构建产物
charlie/build/                  # 构建缓存
*.bin                           # 固件二进制（从 GitHub Release 下载）
firmware/*.bin
```

## 两个版本的区别

| 维度 | OOTB | CUSTOM |
|------|------|--------|
| 内容 | 源码副本（无密钥） | 实际工作目录（含密钥） |
| 用途 | 分发、Git 仓库、用户安装 | 开发、调试、日常使用 |
| ESP32 固件 | xiaozhi v2.1.0 公版（AP配网） | LC-S3 编译版（MQTT 自动推送） |
| 板型 | XINGZHI_CUBE 1.54TFT（公版） | LC-S3 WiFi 1.54TFT（个人） |
| 同步方式 | 手动同步 | 自动（symlink） |

## ESP32 固件版本

### OOTB 固件（公版）
- 来源：xiaozhi v2.1.0 GitHub Release
- 板型：通用（XINGZHI_CUBE 1.54TFT）
- 配网：AP 热点门户（`http://192.168.4.1`）
- NVS：已擦除，无硬编码凭证
- 协议：MQTT + UDP / WebSocket

### CUSTOM 固件（定制版）
- 来源：本地编译 `/Users/sxliuyu/repos/xz/`
- 板型：LC-S3 WiFi 1.54TFT（已修复 board type）
- 配网：硬编码 WiFi + OTA URL
- NVS：预写入 WiFi + 服务器地址
- 协议：MQTT + UDP（xiaozhi 协议）
- 特色：MQTT 自动推送（服务端主动 TTS/通知）

## 修复记录

### 2026-08-13: 屏幕不亮修复
**根因**: sdkconfig 编译了 XINGZHI_CUBE 板型，但板子是 LC-S3。
**修复**:
- `xz/main/Kconfig.projbuild`: 新增 `BOARD_TYPE_LC_S3_WIFI_1_54TFT`
- `xz/main/CMakeLists.txt`: 新增 LC-S3 构建分支
- `xz/sdkconfig`: 切换为 `CONFIG_BOARD_TYPE_LC_S3_WIFI_1_54TFT=y`
