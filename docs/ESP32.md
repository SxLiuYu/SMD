# ESP32 手表终端配置指南

Charlie 支持 ESP32 LC-S3 1.54 寸 TFT WiFi 手表（xiaozhi v2.1.0 协议），流式语音对话。

## 硬件

- 板子：lc-s3-wifi-1.54tft（LC-S3 1.54 寸 TFT WiFi）
- 固件：xiaozhi v2.1.0，16MB 全量 flash
- 屏幕：ST7789 240x240 SPI
- 音频：上行 16kHz Opus → ASR；下行 TTS → 24kHz Opus
- VAD：Silero 神经网络（0.48s 尾静音）

## 烧录（网页向导）

1. 手表插 USB 连 Mac
2. 打开 `http://localhost:8000/esp32-setup`
3. 点击「检测串口」→ 选择 `/dev/cu.usbmodem*`
4. 输入 WiFi SSID / 密码 / Charlie 运行的 Mac IP
5. 点击「开始烧录」（需 30-60 秒）
6. 烧录完成 → 向导自动测 OTA 连通性

向导自动：
- 读取固件 bin（`firmware/flash_16MB_local.bin`，16MB）
- 用 `app/nvs_patch.py` patch NVS 里的 WiFi/服务器地址
- 调 esptool 烧录到 0x0
- curl OTA 端点测连通

## 手动烧录（向导失败时）

```bash
# 1. patch 固件 NVS（Python）
python3 -c "
from app.nvs_patch import patch_nvs, build_replacements
with open('firmware/flash_16MB_local.bin','rb') as f: bin=f.read()
patched = patch_nvs(bin, build_replacements('你的WiFi','你的密码','你的Mac-IP'))
with open('/tmp/patched.bin','wb') as f: f.write(patched)
print('patched')
"

# 2. esptool 烧录
sudo python3 -m esptool --chip esp32s3 -p /dev/cu.usbmodem101 -b 115200 \
  --before=default_reset --after=hard_reset write_flash \
  --flash_mode dio --flash_freq 80m --flash_size 16MB \
  0x0 /tmp/patched.bin
```

## IP 别名（固件 OTA 地址与 Mac 实际 IP 不一致时）

固件 NVS 里服务器地址 patch 后会改为你输入的 IP，无需别名。但如果固件仍指向旧地址（如 `192.168.1.3`），而 Mac 实际 IP 不同，需加别名：

```bash
sudo ifconfig en1 alias 192.168.1.3 255.255.255.0
sudo route add -host 192.168.1.3 -interface lo0
```

或运行 `scripts/esp32-alias.sh`（如有）。

## 性能

- 说完→首句：~1.16s
- 端到端：~2.23s（优化前 3.1s）
- ASR：SenseVoice 本地 26ms（需模型文件）/ 百度 327ms 降级
- TTS：百度 119ms / Finna 降级
