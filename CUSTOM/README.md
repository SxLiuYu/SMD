# Charlie 语音助手 — 自用定制版 (CUSTOM)

个人开发环境，包含所有 API Key、MQTT 配置、Tuya 设备 ID 等敏感信息。**不要提交到公开仓库**。

## 定位

| | OOTB（开箱即用） | CUSTOM（自用定制） |
|---|---|---|
| **用途** | 分发、文档、公共仓库 | 开发、调试、日常使用 |
| **凭证** | 无（.env.example） | 有（.env 含真实 Key） |
| **固件** | 公版 xiaozhi v2.1.0 | LC-S3 编译版（MQTT 自动推送） |
| **来源** | GitHub Releases | 本地编译（xz 仓库） |

## 工作区结构

```
CUSTOM/
├── charlie → ../charlie          # 符号链接，指向主项目源码
└── esp32_firmware                 # LC-S3 定制固件配置
    ├── README.md                  # 固件说明
    ├── custom/
    │   ├── build.sh               # 构建脚本
    │   ├── sdkconfig.lc-s3        # 修正后的 sdkconfig
    │   └── lc-s3-wifi-1.54tft/   # 板型文件
    └── ootb/
        └── README.md              # OOTB 固件说明
```

## 主要配置

```bash
# 激活虚拟环境
source charlie/.venv/bin/activate

# 启动服务
python charlie/voice_server.py

# ESP32 固件编译（需先同步到 xz 仓库）
cd esp32_firmware/custom
bash build.sh all
```

## ESP32 固件（LC-S3）

### 根因修复（2026-08-13）

**问题**: `sdkconfig` 编译了错误的板型 `BOARD_TYPE_XINGZHI_CUBE_1_54TFT_WIFI`，
实际板子是 LC-S3，引脚映射完全不同 → 屏幕不亮。

**修复**:
- `xz/main/Kconfig.projbuild`: 新增 `BOARD_TYPE_LC_S3_WIFI_1_54TFT`
- `xz/main/CMakeLists.txt`: 新增 LC-S3 构建分支
- `xz/sdkconfig`: 切换为 `CONFIG_BOARD_TYPE_LC_S3_WIFI_1_54TFT=y`

### 引脚映射（LC-S3 WiFi 1.54TFT）

```
屏幕 SPI：GPIO3(SDA)/GPIO4(SCL)/GPIO5(DC)/GPIO6(CS)/GPIO7(RES)
背光：GPIO2（GPIO push-pull，active HIGH）
音频 ES8311 (I2C)：GPIO9(SDA)/GPIO8(SCL)，PA=GPIO21
I2S：MCLK=14/WS=11/BCLK=13/DIN=12/DOUT=10
LED：GPIO1，BOOT按钮：GPIO0，音量±：GPIO42/GPIO41
```

### 构建

```bash
cd CUSTOM/esp32_firmware/custom
bash build.sh sync     # 同步配置到 xz 仓库
bash build.sh build    # 编译固件
bash build.sh flash    # 烧录
bash build.sh all      # 一键完成
```

## 源码位置

主项目源码在 `/Users/sxliuyu/orca/projects/charlie/charlie/`，
ESP32 固件源码在 `/Users/sxliuyu/repos/xz/`（xiaozhi-esp32）。

## 安全提醒

- `.env` 已加入 `.gitignore`，不提交
- `.baidu_token.json` 已加入 `.gitignore`，不提交
- ESP32 固件的 OTA URL 指向本地服务器（`192.168.1.12:8000`）
- 如需分享固件，使用 OOTB 版本的公版 bin 文件
