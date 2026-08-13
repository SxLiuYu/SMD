#!/bin/bash
# Charlie 自用定制版 ESP32 固件构建脚本
# 固件源码在 /Users/sxliuyu/repos/xz/（xiaozhi-esp32）
# 板型: lc-s3-wifi-1.54tft
#
# 用法:
#   bash build.sh sync       # 同步板型配置到 xz 仓库
#   bash build.sh build      # 构建固件
#   bash build.sh flash      # 烧录到开发板
#   bash build.sh all        # 同步 + 构建 + 烧录
#
# 环境变量:
#   PORT     串口设备（默认 /dev/cu.usbmodem*）
#   IDF_PATH ESP-IDF 路径（默认 ~/esp/esp-idf）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
XZ_REPO="/Users/sxliuyu/repos/xz"
BOARD="lc-s3-wifi-1.54tft"
PORT="${PORT:-$(ls /dev/cu.usbmodem* 2>/dev/null | head -1)}"
IDF_PATH="${IDF_PATH:-$HOME/esp/esp-idf}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ─── 同步板型配置 ───
sync_config() {
    log_info "同步板型配置到 xz 仓库..."

    # 复制板型文件
    cp "$SCRIPT_DIR/lc-s3-wifi-1.54tft/config.h" \
       "$XZ_REPO/main/boards/lc-s3-wifi-1.54tft/config.h"

    cp "$SCRIPT_DIR/lc-s3-wifi-1.54tft/lc-s3-wifi-1.54tft.cc" \
       "$XZ_REPO/main/boards/lc-s3-wifi-1.54tft/lc-s3-wifi-1.54tft.cc"

    cp "$SCRIPT_DIR/lc-s3-wifi-1.54tft/power_manager.h" \
       "$XZ_REPO/main/boards/lc-s3-wifi-1.54tft/power_manager.h"

    # 复制 sdkconfig
    cp "$SCRIPT_DIR/sdkconfig.lc-s3" "$XZ_REPO/sdkconfig"

    log_info "同步完成"
    log_info "  板型文件: $XZ_REPO/main/boards/$BOARD/"
    log_info "  sdkconfig: $XZ_REPO/sdkconfig"
    log_info ""
    log_warn "请确认 sdkconfig 中的 OTA_URL 和 WiFi 配置正确"
    log_info "  OTA_URL: $(grep OTA_URL "$XZ_REPO/sdkconfig" | head -1)"
}

# ─── 构建固件 ───
build_firmware() {
    log_info "开始构建固件 (板型: $BOARD)..."

    if [ ! -d "$IDF_PATH" ]; then
        log_error "ESP-IDF 未找到: $IDF_PATH"
        log_info "请设置 IDF_PATH 环境变量，或安装 ESP-IDF"
        exit 1
    fi

    cd "$XZ_REPO"

    # 激活 ESP-IDF
    source "$IDF_PATH/export.sh" 2>/dev/null || {
        log_error "无法激活 ESP-IDF 环境"
        exit 1
    }

    # 确认板型
    local board_type=$(grep "CONFIG_BOARD_TYPE_LC_S3_WIFI_1_54TFT" sdkconfig)
    if [ -z "$board_type" ]; then
        log_error "sdkconfig 未配置 LC-S3 板型，请先运行 sync"
        exit 1
    fi

    # 构建
    idf.py build

    if [ $? -eq 0 ]; then
        log_info "构建成功！"
        log_info "固件位置: $XZ_REPO/build/xiaozhi.bin"
    else
        log_error "构建失败"
        exit 1
    fi
}

# ─── 烧录固件 ───
flash_firmware() {
    if [ -z "$PORT" ]; then
        log_error "未检测到串口设备，请设置 PORT 环境变量"
        log_info "  macOS: ls /dev/cu.usbmodem*"
        log_info "  Linux: ls /dev/ttyUSB*"
        log_info "  Windows: 设备管理器查看 COM 端口"
        exit 1
    fi

    log_info "烧录到 $PORT ..."

    cd "$XZ_REPO"
    source "$IDF_PATH/export.sh" 2>/dev/null

    idf.py -p "$PORT" flash

    if [ $? -eq 0 ]; then
        log_info "烧录成功！"
        log_info "设备将自动重启，屏幕应显示初始化界面"
    else
        log_error "烧录失败"
        log_info "常见问题:"
        log_info "  1. 按住 BOOT 按钮再上电，进入下载模式"
        log_info "  2. 检查 USB 数据线（不是充电线）"
        log_info "  3. 安装 CP210x/CH340 驱动"
        exit 1
    fi
}

# ─── 主入口 ───
case "${1:-}" in
    sync)
        sync_config
        ;;
    build)
        build_firmware
        ;;
    flash)
        flash_firmware
        ;;
    all)
        sync_config
        build_firmware
        flash_firmware
        ;;
    *)
        echo "用法: bash build.sh {sync|build|flash|all}"
        echo ""
        echo "  sync   - 同步板型配置和 sdkconfig 到 xz 仓库"
        echo "  build  - 编译固件"
        echo "  flash  - 烧录到开发板"
        echo "  all    - 同步 + 编译 + 烧录"
        echo ""
        echo "环境变量:"
        echo "  PORT      串口设备 (默认自动检测 /dev/cu.usbmodem*)"
        echo "  IDF_PATH  ESP-IDF 路径 (默认 ~/esp/esp-idf)"
        exit 1
        ;;
esac