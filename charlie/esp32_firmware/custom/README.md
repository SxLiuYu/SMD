# 自用定制版 ESP32 固件

面向个人自用的定制固件，**硬编码 WiFi 和服务器地址**，支持 MQTT 自动推送，屏幕显示时间/对话。

> ⚠️ 此版本仅用于个人自用，**不要提交到公开仓库**（含明文 WiFi 密码和服务器 IP）。

## 与开箱即用版的区别

| 项目 | 开箱即用版 (ootb/) | 自用定制版 (custom/) |
|------|-------------------|---------------------|
| WiFi 配网 | AP 热点门户（手机配网） | 硬编码 SSID / 密码 |
| 服务器地址 | OTA 动态获取 | 硬编码 IP |
| NVS | 已擦除 | 预写入 WiFi + 服务器 |
| 适用场景 | 分发给他人的成品 | 自己家里固定网络 |

## 板型配置

| 属性 | 值 |
|------|-----|
| 板子 | lc-s3-wifi-1.54tft |
| 芯片 | ESP32-S3 |
| 屏幕 | ST7789 240x240 SPI |
| 音频 | ES8311 codec（I2C）+ I2S |
| 协议 | MQTT + UDP（xiaozhi 协议） |

## 引脚映射（LC-S3 WiFi 1.54TFT）

```
屏幕 SPI：
  SDA (MOSI)  → GPIO3
  SCL (SCLK)  → GPIO4
  DC          → GPIO5
  CS          → GPIO6
  RES         → GPIO7
  背光 BL      → GPIO2

音频 ES8311 (I2C)：
  SDA         → GPIO9
  SCL         → GPIO8
  PA 使能     → GPIO21

I2S：
  MCLK        → GPIO14
  WS          → GPIO11
  BCLK        → GPIO13
  DIN         → GPIO12  (ADC 输入)
  DOUT        → GPIO10  (DAC 输出)

其它：
  LED         → GPIO1
  BOOT 按钮   → GPIO0
  音量+       → GPIO42
  音量-       → GPIO41
```

## 目录结构

```
custom/
├── README.md                    # 本文件
├── lc-s3-wifi-1.54tft/         # 板型配置文件（从 xz 仓库复制）
│   ├── config.h                 # 引脚定义
│   ├── config.json              # 构建目标
│   ├── lc-s3-wifi-1.54tft.cc   # 板子初始化（SPI/背光/音频/按钮）
│   └── power_manager.h          # 电源管理（此板未用）
├── sdkconfig.lc-s3             # 修正后的 sdkconfig（BOARD_TYPE=LC_S3）
└── build.sh                    # 构建脚本
```

## 编译与烧录

固件源码在独立仓库 `/Users/sxliuyu/repos/xz/`（xiaozhi-esp32），本目录只存放板型配置和构建脚本。

```bash
# 1. 把板型配置同步到固件仓库
bash build.sh sync

# 2. 构建固件
bash build.sh build

# 3. 烧录到开发板
bash build.sh flash   # 默认 /dev/cu.usbmodem*，可用 PORT=COM3 覆盖
```

## MQTT 自动推送

固件通过 MQTT 常驻连接服务器，服务器可随时主动推送：

- **TTS 播报**：服务器推 `{"type":"tts","state":"start"}` + UDP Opus 音频帧
- **文字通知**：服务器推 `{"type":"notification","text":"..."}` 显示在屏幕
- **STT 显示**：识别结果 `{"type":"stt","text":"..."}` 显示在屏幕

服务端实现见 `charlie/app/mqtt_server.py`：

- 上行 topic：`charlie/esp32/{device_id}/up`
- 下行 topic：`charlie/esp32/{device_id}/down`
- UDP 音频：AES-CTR 加密 Opus 帧

## 历史问题记录

### 屏幕不亮（2026-08-13 修复）

**根因**：`sdkconfig` 编译了错误的板型 `BOARD_TYPE_XINGZHI_CUBE_1_54TFT_WIFI`，
而实际板子是 LC-S3，引脚映射完全不同（SPI 在 GPIO3/4/5/6/7 vs GPIO10/9/8/14/18）。

**修复**：在 `Kconfig.projbuild` 注册 `BOARD_TYPE_LC_S3_WIFI_1_54TFT`，
在 `CMakeLists.txt` 添加对应分支，sdkconfig 切换到正确板型。

### 背光冲突

原实现用 PWM 背光（LEDC）会与 GPIO1 的 SingleLed 抢占 LEDC_CHANNEL_0，
已改为 GPIO push-pull 直接驱动 GPIO2（active-high）。
