"""外部二进制依赖检测 — 启动时检测 ffmpeg/ollama/ncm/ego-browser/esptool 是否在 PATH

缺失不阻塞启动，只打印安装指引。结果可写 logs/preflight.log 供排查。
"""
import shutil
import logging

log = logging.getLogger("magic")

# 检测的外部二进制 + 安装指引
_EXTERNAL_BINARIES = {
    "ffmpeg": {
        "install": "brew install ffmpeg (macOS) / apt install ffmpeg (Linux)",
        "purpose": "音频转码（ASR/TTS 必需）",
    },
    "ollama": {
        "install": "brew install ollama (macOS) / curl -fsSL https://ollama.com/install.sh | sh",
        "purpose": "Demo 模式本地 LLM（可选，未配 ARK_KEY 时用）",
    },
    "ncm": {
        "install": "网易云音乐 CLI（ncm-cli 项目）",
        "purpose": "音乐播放（可选）",
    },
    "ego-browser": {
        "install": "ego-browser CLI（见项目文档）",
        "purpose": "浏览器自动化（可选，抖音/淘宝/App 网页版）",
    },
    "esptool": {
        "install": "pip install esptool",
        "purpose": "ESP32 固件烧录（可选，烧录向导用）",
    },
}


def check_binary(name: str) -> bool:
    """检测二进制是否在 PATH"""
    return shutil.which(name) is not None


def run_preflight() -> dict:
    """运行全部检测，返回 {name: {installed, install_guide, purpose}}

    缺失项打 warning 日志，不阻塞启动。
    """
    result = {}
    for name, info in _EXTERNAL_BINARIES.items():
        installed = check_binary(name)
        result[name] = {
            "installed": installed,
            "install_guide": info["install"],
            "purpose": info["purpose"],
        }
        if installed:
            log.info(f"[preflight] ✅ {name} — {info['purpose']}")
        else:
            log.warning(f"[preflight] ❌ {name} 未安装 — {info['install']} ({info['purpose']})")
    return result
