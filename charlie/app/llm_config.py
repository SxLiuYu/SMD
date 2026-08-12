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

# 智谱 GLM 免费大脑（glm-4.7-flash 永久免费，OpenAI 兼容，无需 ARK）
GLM_BASE = os.getenv("GLM_BASE", "https://open.bigmodel.cn/api/paas/v4")
GLM_KEY = os.getenv("GLM_KEY", "")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4.7-flash")

# 429 限流 fallback 链：按顺序尝试，免费模型轮换。
# GLM_MODEL 始终作为首选，其余按 GLM_MODELS 顺序补位。
GLM_MODELS = [m.strip() for m in os.getenv("GLM_MODELS",
    "glm-4.7-flash,glm-4-flash,glm-4.5-flash").split(",") if m.strip()]
if GLM_MODEL and GLM_MODEL not in GLM_MODELS:
    GLM_MODELS.insert(0, GLM_MODEL)
# 当前使用的模型下标（429 时由 rotate_glm_model 推进）
_glm_idx = 0


def current_glm_model() -> str:
    """当前轮到的 GLM 模型名"""
    return GLM_MODELS[_glm_idx] if GLM_MODELS else GLM_MODEL


def rotate_glm_model() -> str:
    """429 限流时轮换到下一个 GLM 模型，返回新模型名。"""
    global _glm_idx
    if len(GLM_MODELS) <= 1:
        return GLM_MODEL
    _glm_idx = (_glm_idx + 1) % len(GLM_MODELS)
    log.warning(f"[llm] GLM 429 限流，轮换到 {GLM_MODELS[_glm_idx]}")
    return GLM_MODELS[_glm_idx]


def is_glm_configured() -> bool:
    """智谱 GLM 免费 Key 是否已配置"""
    from app.env_catalog import is_configured
    return is_configured("GLM_KEY")


def active_chat_endpoint() -> tuple[str, str, str]:
    """当前激活的 OpenAI 兼容对话端点 (api_base, api_key, model)。

    优先级：ARK > 智谱 GLM 免费。意图分类等原生 HTTP 调用走这里。
    都没配时返回空串（调用方应回退到关键词匹配 / Ollama）。
    """
    if is_ark_configured():
        return ARK_BASE, ARK_KEY, ARK_MODEL
    if is_glm_configured():
        return GLM_BASE, GLM_KEY, current_glm_model()
    return "", "", ""


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
    """返回 llm_cfg dict（ARK > 智谱 GLM 免费 > Ollama Demo）

    - ARK_KEY 已配 → ARK 配置
    - GLM_KEY 已配 → 智谱 GLM 免费大脑（glm-4-flash 永久免费，OpenAI 兼容）
    - 都没配 → Demo 模式：Ollama 在线用 Ollama，离线 raise RuntimeError
    """
    if is_ark_configured():
        return {
            'model': ARK_MODEL, 'model_type': 'oai',
            'api_base': ARK_BASE, 'api_key': ARK_KEY,
            'generate_cfg': {'use_raw_api': True, 'extra_body': {'extra_body': {'enable_thinking': False}}, 'max_tokens': 512},
        }
    if is_glm_configured():
        _m = current_glm_model()
        log.info(f"[llm] ━━━ 免费 LLM ━━━ 智谱 {_m}")
        # 智谱非 Qwen 推理服务器，去掉 enable_thinking 以免 400
        return {
            'model': _m, 'model_type': 'oai',
            'api_base': GLM_BASE, 'api_key': GLM_KEY,
            'generate_cfg': {'use_raw_api': True, 'max_tokens': 512},
        }
    # Demo 模式：Ollama 兜底
    if not ollama_online():
        raise RuntimeError(f"Demo 模式: Ollama 服务或模型 {OLLAMA_MODEL} 不可用，可在引导页配置智谱 GLM 免费 Key")
    log.warning(f"[llm] ━━━ Demo 模式 ━━━ 使用 Ollama {OLLAMA_MODEL}")
    return {
        'model': OLLAMA_MODEL, 'model_type': 'oai',
        'api_base': OLLAMA_OPENAI_BASE, 'api_key': 'ollama',
        'generate_cfg': {'use_raw_api': True, 'extra_body': {'extra_body': {'enable_thinking': False}}, 'max_tokens': 512},
    }
