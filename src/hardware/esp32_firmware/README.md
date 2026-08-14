# Charlie ESP32 固件

LC-S3 1.54 寸 TFT WiFi 开发板固件，xiaozhi 协议，MQTT + UDP 音频传输。

## 目录结构

```
esp32_firmware/
├── README.md                    # 本文件
└── custom/                      # 自用定制版
    ├── README.md                # 硬编码 WiFi + MQTT 推送说明
    ├── build.sh                 # 构建脚本
    ├── sdkconfig.lc-s3          # 板型配置
    └── lc-s3-wifi-1.54tft/     # 板型文件
```

## 固件信息

| 属性 | 值 |
|------|-----|
| 板子 | lc-s3-wifi-1.54tft |
| 芯片 | ESP32-S3 |
| 屏幕 | ST7789 240x240 SPI |
| 音频 | ES8311 codec (I2C) + I2S |
| 协议 | MQTT + UDP（xiaozhi 协议） |
| 固件源码 | `/Users/sxliuyu/repos/xz/` |

## 构建与烧录

```bash
cd custom
bash build.sh sync     # 同步配置到 xz 仓库
bash build.sh build    # 编译固件
bash build.sh flash    # 烧录到开发板
bash build.sh all      # 一键完成
```

## 相关文档

- 配网原理：`../../docs/ESP32.md`
- 固件分发：`../../firmware/README.md`
- MQTT 服务端：`../app/mqtt_server.py`
- WebSocket 端点：`../app/xiaozhi_ws.py`