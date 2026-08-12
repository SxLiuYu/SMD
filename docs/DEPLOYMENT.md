# 部署指南

## 方式一：桌面应用（v1.0 主打，macOS）

### 构建

```bash
cd charlie/charlie
pip install -r requirements-core.txt -r requirements-dev.txt
bash build.sh  # 跑测试 + PyInstaller 打包 → dist/charlie/
```

产物：`dist/charlie/charlie`（~200MB，含核心 Python + web + ffmpeg binary）

### 分发

1. 压缩 `dist/charlie/` → `charlie-mac.zip`
2. 用户解压
3. 双击 `charlie` → 浏览器自动开 `/welcome` 引导页
4. 选模式（Demo 规则 / Ollama / 填 key）→ 完成 → 主界面
5. macOS 首次打开如提示"无法验证开发者"：系统偏好设置 → 安全性与隐私 → 允许

### 发布前检查

```bash
bash scripts/check-leaks.sh  # 扫描敏感信息
```

## 方式二：Python 开发

```bash
git clone <repo>
cd charlie/charlie
python3 -m venv .venv && source .venv/bin/activate

# 核心依赖（装完即可跑对话）
pip install -r requirements-core.txt

# 可选依赖（本地 ASR/ESP32/音频处理）
pip install -r requirements-optional.txt

# 外部二进制
brew install ffmpeg          # 必需（音频转码）
# brew install ollama        # 可选（Demo 模式 LLM）
# pip install esptool        # 可选（ESP32 烧录）

# 配置
cp .env.example .env
# 编辑 .env 填入 ARK_KEY/百度/高德 key
# 或启动后访问 http://localhost:8000/setup 网页填写

# 启动
python3 voice_server.py
# HTTPS（手机访问）：python3 https_server.py
```

## 方式三：Docker（v1.1，规划中）

```bash
cp .env.example .env  # 填 key
docker compose up -d --build
# Ollama sidecar：docker compose --profile ollama up -d
```

## HTTPS 证书

首次启动 `https_server.py` 时自动生成自签证书（`cert/cert.pem` + `cert/key.pem`，10 年有效，CN=hostname）。

手动生成：`bash scripts/gen-cert.sh`

手机同 WiFi 访问 `https://<Mac-IP>:8443`，首次需信任证书。

## SenseVoice 本地 ASR 模型（可选，26ms ASR）

```bash
bash scripts/download-models.sh  # 下载 237MB 模型到 models/sense-voice/
# 或网页：http://localhost:8000/setup → 点「下载本地 ASR 模型」
```

模型缺失时自动降级百度 ASR（327ms）。

## ESP32 手表

见 `docs/ESP32.md`。

## Troubleshooting

### 启动报"缺少必需密钥"

启动时打印每个 key 的配置状态。缺失只 warning 不阻塞（Demo 规则模式可兜底）。访问 `http://localhost:8000/setup` 填写。

### 麦克风不可用（HTTP 连接）

浏览器要求 HTTPS 才能用麦克风。运行 `python3 https_server.py`，手机/电脑用 `https://<IP>:8443` 访问。

### ffmpeg 未找到

`brew install ffmpeg`（macOS）/ `apt install ffmpeg`（Linux）。启动时 preflight 会检测并提示。

### Ollama Demo 模式不可用

```bash
ollama serve &
ollama pull qwen3.5:2b
```

### ESP32 烧录失败

向导需要 sudo 访问串口。失败时手动运行：
```bash
sudo python3 -m esptool --chip esp32s3 -p /dev/cu.usbmodem101 write_flash 0x0 /tmp/patched.bin
```

## 依赖文件说明

| 文件 | 用途 |
|---|---|
| `requirements.txt` | 全量依赖（core + optional + dev，向后兼容）|
| `requirements-core.txt` | 核心对话必需（装完即可跑）|
| `requirements-optional.txt` | 本地 ASR/ESP32/音频处理（缺失会降级）|
| `requirements-dev.txt` | 测试开发（pytest）|
