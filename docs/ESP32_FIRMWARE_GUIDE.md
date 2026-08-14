# ESP32 固件开发指南

> 更新时间: 2026-08-13
> 目标: LC-S3 WiFi 1.54TFT 开发板固件编译、烧录、验证

---

## 1. 硬件规格

| 参数 | 值 |
|------|-----|
| 芯片 | ESP32-S3 |
| 开发板 | LC-S3 WiFi 1.54" TFT |
| USB 芯片 | CH343 (串口: `/dev/tty.usbmodem101`) |
| 显示屏 | ST7789, 240x240 彩色 TFT |
| Flash | 16MB |
| Flash 模式 | DIO |
| Flash 频率 | 80MHz |
| 源码仓库 | `/Users/sxliuyu/repos/xz` (xiaozhi-esp32) |

### 引脚分配

```
显示 SPI:    SDA=GPIO3, SCL=GPIO4, DC=GPIO5, CS=GPIO6, RES=GPIO7
背光:        GPIO2 (active-high)
I2S 音频:    MCLK=14, WS=11, BCLK=13, DIN=12, DOUT=10
I2C:         SDA=9, SCL=8
按键:        BOOT=GPIO0, VOL_UP=42, VOL_DOWN=41
LED:         GPIO1
红外发射:    GPIO39, 38KHz
```

---

## 2. 已知工作固件备份

### 2.1 June 13 备份 (工作版本)

**位置**: `/Users/sxliuyu/esp32/firmware/backup/watch_20260613_115741/flash_16MB.bin`

**特点**:
- 固件版本: xiaozhi v2.1.0
- 有 PowerManager (电池监控)
- ES8311 音频编解码器软失败处理
- 背光亮度 70%
- **所有功能正常工作**

### 2.2 还原命令

```bash
python3 -m esptool --chip esp32s3 --port /dev/tty.usbmodem101 \
  --before default_reset --after hard_reset \
  write-flash --flash-mode dio --flash-size 16MB --flash-freq 80m \
  0x0 /Users/sxliuyu/esp32/firmware/backup/watch_20260613_115741/flash_16MB.bin
```

---

## 3. 编译环境

### 3.1 ESP-IDF 版本

- v5.5.2: `/Users/sxliuyu/esp-idf-v5.5.2` **(推荐)**

### 3.2 构建命令

```bash
# 设置环境变量
export IDF_PATH=/Users/sxliuyu/esp-idf-v5.5.2
export IDF_SKIP_CHECK_SUBMODULES=1

# 进入项目目录
cd /Users/sxliuyu/repos/xz

# 构建
/Users/sxliuyu/.espressif/python_env/idf5.5_py3.14_env/bin/python \
  /Users/sxliuyu/esp-idf-v5.5.2/tools/idf.py build

# 烧录
/Users/sxliuyu/.espressif/python_env/idf5.5_py3.14_env/bin/python \
  /Users/sxliuyu/esp-idf-v5.5.2/tools/idf.py -p /dev/tty.usbmodem101 flash

# 一步完成 (构建 + 烧录)
/Users/sxliuyu/.espressif/python_env/idf5.5_py3.14_env/bin/python \
  /Users/sxliuyu/esp-idf-v5.5.2/tools/idf.py -p /dev/tty.usbmodem101 build flash
```

### 3.3 sdkconfig 关键配置

```bash
# 切换到 LC-S3 板型
python3 -c "
import re
with open('sdkconfig', 'r') as f:
    content = f.read()
content = re.sub(r'CONFIG_BOARD_TYPE_BREAD_COMPACT_WIFI=y', '# CONFIG_BOARD_TYPE_BREAD_COMPACT_WIFI is not set', content)
if 'CONFIG_BOARD_TYPE_LC_S3_WIFI_1_54TFT=y' not in content:
    content = content.replace('# CONFIG_BOARD_TYPE_XINGZHI_ABS_2_0 is not set', 'CONFIG_BOARD_TYPE_LC_S3_WIFI_1_54TFT=y\n# CONFIG_BOARD_TYPE_XINGZHI_ABS_2_0 is not set')
with open('sdkconfig', 'w') as f:
    f.write(content)
"

# 设置 OTA URL (本地 Charlie 服务器)
sed -i '' 's|CONFIG_OTA_URL="https://api.tenclass.net/xiaozhi/ota/"|CONFIG_OTA_URL="http://192.168.1.12:8000/xiaozhi/ota"|' sdkconfig
```

---

## 4. 验证清单

烧录后使用以下命令验证:

```bash
python3 << 'EOF'
import serial, time, subprocess

subprocess.run(['python3', '-m', 'esptool', '--chip', 'esp32s3', 
                '--port', '/dev/tty.usbmodem101', 
                '--before', 'default_reset', '--after', 'hard_reset', 'read_mac'], 
               capture_output=True)

ser = serial.Serial('/dev/tty.usbmodem101', 115200, timeout=1)
time.sleep(0.3)

output = b''
start = time.time()
while time.time() - start < 8:
    if ser.in_waiting:
        data = ser.read(ser.in_waiting)
        output += data
ser.close()

text = output.decode('utf-8', errors='replace')

checks = {
    "Board SKU": "SKU=lc-s3-wifi-1.54tft" in text,
    "Display on": "Turning display on" in text,
    "LVGL init": "LVGL" in text,
    "Backlight": "brightness" in text.lower(),
    "WiFi connected": "Connected to WiFi" in text,
    "MQTT connected": "MQTT" in text and "Connected" in text,
}

for name, passed in checks.items():
    print(f"  {'✅' if passed else '❌'} {name}")
EOF
```

---

## 5. 已知问题与修复

### 5.1 ES8311 I2C 通信失败

**现象**: 启动日志中出现 `I2C_If: Fail to write to dev 30`

**原因**: ES8311 音频编解码器 I2C 地址 0x30 无响应

**解决方案**:
1. June 13 备份固件已包含软失败处理，可正常使用
2. 如需编译新固件，需应用 2026-06-15 的修复提交:
   - `2c4acb1` fix(audio): soft-fail ES8311 probe
   - `b690f45` fix(audio): guard EnableInput/Output when codec missing

### 5.2 sdkconfig 被重置

**现象**: 编译后发现 board type 变回 `BREAD_COMPACT_WIFI`

**原因**: `idf.py set-target` 或 `fullclean` 可能删除 sdkconfig

**解决方案**: 使用上方 3.3 节的 python 脚本恢复配置

### 5.3 重启循环问题

**现象**: 设备反复重启，日志中出现多次 `entry 0x403c8908`

**原因**: 固件编译错误或 sdkconfig 配置不正确

**解决方案**: 恢复 June 13 备份固件

---

## 6. 快速参考

```bash
# 一键构建+烧录
export IDF_PATH=/Users/sxliuyu/esp-idf-v5.5.2 IDF_SKIP_CHECK_SUBMODULES=1
cd /Users/sxliuyu/repos/xz
/Users/sxliuyu/.espressif/python_env/idf5.5_py3.14_env/bin/python \
  /Users/sxliuyu/esp-idf-v5.5.2/tools/idf.py -p /dev/tty.usbmodem101 build flash

# 仅烧录 (不重新构建)
/Users/sxliuyu/.espressif/python_env/idf5.5_py3.14_env/bin/python \
  /Users/sxliuyu/esp-idf-v5.5.2/tools/idf.py -p /dev/tty.usbmodem101 flash

# 串口监控
screen /dev/tty.usbmodem101 115200
```

---

## 7. 故障排除

| 问题 | 解决方案 |
|------|----------|
| esptool 连不上 | 按住 BOOT 键 → 插 USB → 等 1 秒 → 松开 BOOT → 烧录 |
| 屏幕不亮 | 检查背光 GPIO2 是否开启，确认 `Turning display on` 日志 |
| I2C 错误 | 正常现象，ES8311 软失败处理已启用 |
| WiFi 连不上 | 检查 sdkconfig 中 WiFi 密码是否正确 |
| MQTT 连不上 | 检查网络连接，确认 `mqtt.xiaozhi.me` 可访问 |
| 重启循环 | 恢复 June 13 备份固件 |

---

## 8. Charlie 适配（2026-08-14 新增）

### 8.1 修改内容

基于 June 13 备份固件，添加了以下功能：

| 修改 | 文件 | 说明 |
|------|------|------|
| OTA URL | `sdkconfig` | 指向 Charlie 服务器 `192.168.1.12:8000` |
| MQTT 回退 | `mqtt_protocol.cc` | 无 NVS 配置时自动使用 Charlie MQTT |
| 订阅推送 | `mqtt_protocol.cc` | 连接后自动订阅 `subscribe_topic` |
| 通知显示 | `mqtt_protocol.cc` | 接收 `notification` 消息并显示在屏幕 |

### 8.2 MQTT 消息格式

**Charlie 服务器推送通知到 ESP32:**
```json
{
  "type": "notification",
  "text": "您有一条新消息",
  "ttl": 5000
}
```

**ESP32 发布到 Charlie 服务器:**
```
Topic: charlie/esp32/{device_id}/up
```

**Charlie 服务器推送到 ESP32:**
```
Topic: charlie/esp32/{device_id}/down
```

### 8.3 构建命令

```bash
# 使用构建脚本
bash /Users/sxliuyu/orca/projects/charlie/charlie/esp32_firmware/custom/build_charlie.sh

# 或手动构建
export IDF_PATH=/Users/sxliuyu/esp-idf-v5.5.2 IDF_SKIP_CHECK_SUBMODULES=1
cd /Users/sxliuyu/repos/xz
/Users/sxliuyu/.espressif/python_env/idf5.5_py3.14_env/bin/python \
  /Users/sxliuyu/esp-idf-v5.5.2/tools/idf.py -p /dev/tty.usbmodem101 build flash
```

### 8.4 测试推送

```python
# 在 Charlie 服务器上测试推送
import json, asyncio
from app.mqtt_server import get_server

async def test_push():
    server = get_server()
    if server:
        server.push_notification("测试推送消息 - 来自 Charlie!")

asyncio.run(test_push())
```

### 8.5 验证清单

烧录后检查以下日志:
```
✅ MQTT: Connecting to endpoint 192.168.1.12:1883
✅ MQTT: Subscribing to topic: charlie/esp32/...
✅ Ota: HttpClient: Established new connection to 192.168.1.12:8000
✅ Push notification: <消息内容>
```

### 8.6 故障排除

| 问题 | 解决方案 |
|------|----------|
| 设备无响应 | 按板子上的 RST 按钮 |
| MQTT 连不上 | 确认 Charlie 服务器的 MQTT broker 在运行 |
| 推送不显示 | 检查 `subscribe_topic` 是否正确 |
| OTA 报错 | 确认 Charlie 服务器 `/xiaozhi/ota` 端点可访问 |
