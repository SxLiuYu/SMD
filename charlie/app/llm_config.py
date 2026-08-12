"""LLM 配置解析 — ARK vs Ollama adapter（深 module）

从 voice_agent._build_brain 抽出。负责：
- 探测 ARK_KEY 是否配置
- 探测 Ollama 服务是否在线
- 返回 llm_cfg dict（ARK 或 Ollama）
"""
import os
import logging

log = logging.getLogger("magic")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:2b")
OLLAMA_OPENAI_BASE = OLLAMA_HOST + "/v1"

ARK_BASE = os.getenv("ARK_BASE", "https://ark.cn-beijing.volces.com/api/plan/v3")
ARK_KEY = os.getenv("ARK_KEY", "")
ARK_MODEL = os.getenv("ARK_MODEL", "ark-code-latest")


def is_ark_configured() -> bool:
    """ARK_KEY 是否已配置 — 委托到 env_catalog（#5 修复：单一来源）"""
    from app.env_catalog import is_configured
    return is_configured("ARK_KEY")


def demo_mode_active() -> bool:
    """当前是否处于 Demo 模式 — 委托到 env_catalog"""
    from app.env_catalog import demo_mode_active as _env_demo
    return _env_demo()


def ollama_online() -> bool:
    """探测 Ollama 服务是否在线 + 模型存在"""
    try:
        import requests as _req
        r = _req.get(OLLAMA_HOST + "/api/tags", timeout=1.5)
        if r.status_code != 200:
            return False
        models = {m.get("name", "") for m in r.json().get("models", [])}
        if OLLAMA_MODEL in models or any(m.startswith(OLLAMA_MODEL.split(":")[0]) for m in models):
            return True
        log.warning(f"[ollama] 服务在线但模型 {OLLAMA_MODEL} 未拉取")
        return False
    except Exception as e:
        log.warning(f"[ollama] 探测失败（{e}）")
        return False


def resolve() -> dict:
    """返回 llm_cfg dict（ARK 或 Ollama）

    - ARK_KEY 已配 → ARK 配置
    - ARK_KEY 空 → Demo 模式：Ollama 在线用 Ollama，离线 raise RuntimeError
    """
    if demo_mode_active():
        if not ollama_online():
            raise RuntimeError(f"Demo 模式: Ollama 服务或模型 {OLLAMA_MODEL} 不可用")
        log.warning(f"[llm] ━━━ Demo 模式 ━━━ 使用 Ollama {OLLAMA_MODEL}")
        return {
            'model': OLLAMA_MODEL, 'model_type': 'oai',
            'api_base': OLLAMA_OPENAI_BASE, 'api_key': 'ollama',
            'generate_cfg': {'use_raw_api': True, 'extra_body': {'extra_body': {'enable_thinking': False}}, 'max_tokens': 512},
        }
    return {
        'model': ARK_MODEL, 'model_type': 'oai',
        'api_base': ARK_BASE, 'api_key': ARK_KEY,
        'generate_cfg': {'use_raw_api': True, 'extra_body': {'extra_body': {'enable_thinking': False}}, 'max_tokens': 512},
    }
