# Charlie ESP32 固件

## 最终版本（当前使用）

**文件**: `flash_16MB_local.bin` (16MB 全量flash镜像)

| 属性 | 值 |
|------|-----|
| 固件版本 | xiaozhi v2.1.0 |
| 编译时间 | 2026-01-30 |
| ESP-IDF | v5.5.1 |
| 板子 | lc-s3-wifi-1.54tft (LC-S3 1.54寸 TFT WiFi) |
| Flash大小 | 16MB |
| OTA URL | `http://192.168.1.3:8000/xiaozhi/ota` |
| WS URL | `ws://192.168.1.3:8000/ws/xiaozhi` |
| WiFi | ***REMOVED*** / ***REMOVED*** (硬编码在NVS) |
| 屏幕 | ST7789 240x240 SPI, 1.54寸 TFT (亮✅) |

> ⚠️ **此版本是最终版本，不要再重新编译烧录。** xz项目用xingzhi-cube板子编译的固件屏幕不亮（显示引脚不同）。这个版本是从ESP32原厂固件patch而来，直接修改OTA/WS地址指向Charlie本地服务。

## 烧录命令

```bash
# 前置：安装esptool
# pip install esptool

# 烧录（全量16MB，会覆盖所有分区）
python3 -m esptool --chip esp32s3 \
  -p /dev/cu.usbmodem101 \
  -b 115200 \
  --before=default_reset \
  --after=hard_reset \
  write_flash \
  --flash_mode dio \
  --flash_freq 80m \
  --flash_size 16MB \
  0x0 firmware/flash_16MB_local.bin
```

## Mac端配套设置（每次重启后执行）

固件里OTA地址是 `192.168.1.3`，但Mac的实际IP是 `192.168.1.12`。需要给Mac加IP别名：

```bash
#!/bin/bash
# esp32-alias.sh — 给Mac加192.168.1.3别名
# 用法: sudo bash scripts/esp32-alias.sh

IFACE=$(route get default 2>/dev/null | grep interface | head -1 | awk '{print $2}')
if [ -z "$IFACE" ]; then
  IFACE="en1"
fi

# 删除旧别名（如果存在）
sudo ifconfig $IFACE delete 192.168.1.3 2>/dev/null

# 添加IP别名
sudo ifconfig $IFACE alias 192.168.1.3 255.255.255.0

# 修复路由（让192.168.1.3指向本地）
sudo route delete 192.168.1.3 2>/dev/null
sudo route add -host 192.168.1.3 -interface lo0

# 验证
curl -s --connect-timeout 3 http://192.168.1.3:8000/health && echo "✅ 192.168.1.3 可达" || echo "❌ 不可达"
```

## 分区布局

| 分区 | 偏移 | 大小 | 说明 |
|------|------|------|------|
| nvs | 0x9000 | 16KB | WiFi配置、设备参数 |
| otadata | 0xD000 | 8KB | OTA状态 |
| phy_init | 0xF000 | 4KB | 射频校准 |
| ota_0 | 0x20000 | 4032KB | 固件镜像（有效） |
| ota_1 | 0x410000 | 4032KB | 备用分区（空） |
| assets | 0x800000 | 8MB | 字体/表情/语音模型 |

## 历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-01-30 | v2.1.0 | 原厂固件，从tenclass.net OTA获取 |
| 2026-06-13 | - | 从ESP32完整备份flash到 `flash_16MB.bin` |
| 2026-06-13 | - | patch OTA/WS地址为 `192.168.1.3`（`flash_16MB_local.bin`） |
| 2026-08-11 | - | 尝试用xz项目编译xingzhi-cube固件 → **屏幕不亮**（引脚不匹配） |
| 2026-08-11 | - | 恢复 `flash_16MB_local.bin` → **屏幕亮，最终版本** |

## 注意事项

1. **不要用xz项目重新编译** — xingzhi-cube-1.54tft-wifi板子的显示引脚与lc-s3不同
2. **不要擦除flash** — `erase_flash` 会清掉NVS里的WiFi配置和phy_init
3. **OTA自动升级已禁用** — OTA地址指向本地Charlie服务，不会从tenclass.net升级
4. **IP别名必须设置** — 没有别名ESP32连不上Charlie服务
5. **Mac静态IP** — 已设为 `192.168.1.12`（固定不变），ESP32通过 `192.168.1.3` 别名访问
