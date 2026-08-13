# Charlie 语音助手 — 便携版使用说明

## 快速开始
1. 解压 `Charlie-Portable.zip` 到任意目录（如 `D:\Charlie`）。
2. 双击 **`charlie.exe`** 启动。
3. 首次启动会自动打开欢迎向导：注册一个**免费**的智谱 GLM Key 填进去即可对话。
   - Key 申请地址：https://open.bigmodel.cn/apikey/platform （注册即送，glm-4.7-flash 永久免费）
   - 填完点保存，**无需重启**，立即生效。
4. 回到主界面即可语音 / 文字对话。

## 目录结构
```
charlie/
├── charlie.exe        ← 双击启动（原生桌面窗口，不弹黑框）
├── _internal/         ← 运行所需文件（勿删）
├── data/              ← 首次运行自动生成：对话历史、提醒、缓存
├── logs/              ← 首次运行自动生成：运行日志（排查问题用）
└── .env               ← 首次运行自动生成：你填的 API Key 配置
```

## 便携特性
- 整个文件夹可随意移动、拷贝到 U 盘，配置和数据都在文件夹内，不写注册表、不写系统目录。
- 迁移到另一台电脑：直接复制整个 `charlie/` 文件夹即可（含已配置的 `.env` 和 `data/`）。

## 语音功能（可选）
语音对话需要百度智能云 ASR/TTS（有免费额度）：
- 申请：https://console.bce.baidu.com/ai/#/ai/speech/overview/index
- 在向导或「高级配置」页填入 `BAIDU_APP_ID` / `BAIDU_API_KEY` / `BAIDU_SECRET_KEY`。
- 不配置也能用文字对话。

## 常见问题
- **提示"还没配置 AI 大脑"**：按提示打开 `/welcome` 填一个免费 GLM Key。
- **窗口打不开**：Windows 10/11 需安装 WebView2（多数系统已自带；若缺失会提示下载）。
- **查问题**：看 `logs/app.log`。
