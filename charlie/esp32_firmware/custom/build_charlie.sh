#!/bin/bash
# ============================================================
# Charlie ESP32 固件构建脚本
# 基于 June 13 备份固件 + Charlie 适配 + MQTT 主动推送
# ============================================================
set -e

ESP_IDF_PATH="/Users/sxliuyu/esp-idf-v5.5.2"
XZ_REPO="/Users/sxliuyu/repos/xz"
PORT="${1:-/dev/tty.usbmodem101}"

echo "=== Charlie ESP32 固件构建 ==="
echo "ESP-IDF: $ESP_IDF_PATH"
echo "源码: $XZ_REPO"
echo "端口: $PORT"
echo ""

# 1. 检查 sdkconfig 配置
cd "$XZ_REPO"
echo "【1/4】检查 sdkconfig 配置..."
BOARD_TYPE=$(grep "BOARD_TYPE.*=y" sdkconfig | grep -v "not set" | head -1)
echo "  板型: $BOARD_TYPE"
OTA_URL=$(grep "OTA_URL" sdkconfig | grep -v "not set")
echo "  OTA: $OTA_URL"

# 2. 构建
echo ""
echo "【2/4】构建固件..."
export IDF_PATH="$ESP_IDF_PATH"
export IDF_SKIP_CHECK_SUBMODULES=1
/Users/sxliuyu/.espressif/python_env/idf5.5_py3.14_env/bin/python \
  "$ESP_IDF_PATH/tools/idf.py" build

# 3. 烧录
echo ""
echo "【3/4】烧录固件 (端口: $PORT)..."
echo "请确保设备已连接并处于下载模式"
echo "如果设备无响应，请按板子上的 RST 按钮"
/Users/sxliuyu/.espressif/python_env/idf5.5_py3.14_env/bin/python \
  "$ESP_IDF_PATH/tools/idf.py" -p "$PORT" flash

# 4. 验证
echo ""
echo "【4/4】验证固件..."
sleep 3
python3 << 'PYEOF'
import serial, time, subprocess, sys
port = sys.argv[1] if len(sys.argv) > 1 else "/dev/tty.usbmodem101"

subprocess.run(['python3', '-m', 'esptool', '--chip', 'esp32s3', 
                '--port', port, 
                '--before', 'default_reset', '--after', 'hard_reset', 'read_mac'], 
               capture_output=True)

ser = serial.Serial(port, 115200, timeout=1)
time.sleep(0.5)

output = b''
start = time.time()
while time.time() - start < 20:
    if ser.in_waiting:
        data = ser.read(ser.in_waiting)
        output += data
ser.close()

text = output.decode('utf-8', errors='replace')

checks = {
    "LC-S3 Board": "SKU=lc-s3-wifi-1.54tft" in text,
    "Display on": "Turning display on" in text,
    "Backlight": "brightness" in text.lower(),
    "WiFi connected": "Connected to WiFi" in text,
    "MQTT connected": "MQTT" in text and "Connected" in text,
    "Charlie OTA": "192.168.1.12" in text,
    "MQTT Subscribe": "Subscribing to topic" in text,
}

print("=== 验证结果 ===")
all_pass = True
for name, passed in checks.items():
    status = '✅' if passed else '❌'
    print(f"  {status} {name}")
    if not passed:
        all_pass = False

if all_pass:
    print("\n🎉 所有检查通过！")
else:
    print("\n⚠️ 部分检查未通过")
PYEOF "$PORT"

echo ""
echo "=== 构建完成 ==="