# Changelog

本项目版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。每个版本的下载见
[GitHub Releases](https://github.com/SxLiuYu/charlie-voice-assistant/releases)。

## [3.2.0] - 2026-08-13

开箱即用版本的稳定化迭代：修复用户可感知的缺陷、移除死代码、同步文档、清理技术债。

### 修复
- 电视/空调控制不再硬编码内网 IP `192.168.1.7`；未配置 `ESP32_IP` 时给出明确提示而非静默失败
- 系统音量调节在控制不可用时返回清晰反馈，不再假装成功
- “停止 / 暂停 / 闭嘴”仅做应答，不再误操作系统静音
- ESP32 烧录在 PyInstaller 窗口模式下改为进程内调用 `esptool.main()`，修复 frozen 环境无法烧录的问题
- frozen 环境下 esptool 依赖探测误报“未安装”

### 变更
- ESP32 配网全面切换为设备内置 AP 热点门户（`http://192.168.4.1`），移除脆弱的 NVS 字符串 patch 方案
  - 删除 `app/nvs_patch.py` 及其测试，从 spec 中移除引用
- 打包清单移除未使用的 u2 技能目录，便携包体积更小
- 百度 OAuth token 临时文件纳入 `.gitignore`（含 access_token，绝不入库）
- 新增环境变量 `MQTT_ENABLE_OTA`、`INTERNAL_API_TOKEN`，并登记到 `env_catalog`

### 文档
- 重写 `docs/ESP32.md`、`firmware/README.md`：AP 热点配网原理与步骤
- 更新根 `README.md`、`charlie/README.md`、`docs/DEPLOYMENT.md`、`docs/DEMO_MODE.md`、`docs/WINDOWS_BUILD.md`
  - 主路径改为 Windows 便携版 `charlie.exe` + 免费智谱 GLM
  - 移除 `nvs_patch`、`charlie-mac.zip`、`patch NVS`、`brew`/`sudo esptool` 等过时表述

### 清理
- 删除过时文件：根 `DEPLOYMENT.md`（Finna/deepseek 旧架构）、两个已合并的 `.patch`、
  旧打包脚手架 `assistant-kid/`、社交媒体草稿 `charlie/charlie_post.json`
- 修复 `.gitignore` 中损坏的字面换行
- `app/cert.py` 的 `datetime.utcnow()` 迁移为 `datetime.now(datetime.UTC)`

## [3.1.0] - 2026-08-13

首个开箱即用版本：双击 exe 即可在原生桌面窗口运行，免费 GLM 大脑 + 百度语音，无需安装 Python。

### 新增
- Windows 便携版 `Charlie-Portable.zip`：解压双击 `charlie.exe` 即运行，内置 ESP32 固件与 esptool
- 跨平台原生窗口（pywebview / WebView2）
- ESP32 AP 热点配网：烧录干净固件 + 手机连 `lc-s3-wifi-1.54tft-XXXX` 配网，支持任意长度 WiFi 密码
- 应用内烧录向导，进程内调用 esptool，免装 Python 环境
- 配置热重载：向导保存 Key 后立即生效，无需重启；保存时实时验证 GLM/百度 Key 有效性

### 修复
- 流式对话“大脑启动失败”
- 启动时显示“⏰ undefined”
- “语音服务繁忙”误导提示（未配置时准确引导）
- 移除天气回复中的 Open-Meteo 归属文本

### 资产
- `charlie-esp32-flash-16MB.bin`：ESP32 16MB 全量固件镜像（xiaozhi v2.1.0，LC-S3 1.54寸 TFT），已擦除 NVS，不含任何 WiFi/服务器信息

## [1.0.0]

早期版本（已被后续版本取代，无对应 tag）。
