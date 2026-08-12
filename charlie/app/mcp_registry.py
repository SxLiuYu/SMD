"""MCP server 注册表 — 表 + frozen 探测 + profile 合并（深 module）

从 voice_agent._build_brain 抽出。负责：
- all_mcp dict（19 个 MCP 的 command/args/cwd 配置）
- frozen/cwd 探测
- 按 mcp_set + MCP_PROFILE 解析启用的 MCP 列表
- Demo 模式（无 LLM）不启 MCP
"""
import os
import sys
import logging

log = logging.getLogger("magic")


def _build_all_mcp() -> dict:
    """构建所有 MCP server 的 command/args/cwd 配置"""
    _is_frozen = getattr(sys, 'frozen', False)
    _py = sys.executable
    _mcp_cwd = os.path.dirname(_py) if _is_frozen else os.getcwd()
    # args: frozen 模式用 --mcp，否则用 .py 文件名
    def _args(name):
        return ["--mcp", name] if _is_frozen else [name + ".py"] if not name.endswith(".py") else [name]

    all_mcp = {
        "amap-maps": {"command": _py, "args": _args("magic-info"), "cwd": _mcp_cwd},
        "magic-info": {"command": _py, "args": _args("magic-info"), "cwd": _mcp_cwd},
        "magic-music": {"command": _py, "args": _args("magic-music"), "cwd": _mcp_cwd},
        "magic-reminder": {"command": _py, "args": _args("magic-reminder"), "cwd": _mcp_cwd},
        "magic-notes": {"command": _py, "args": _args("magic-notes"), "cwd": _mcp_cwd},
        "magic-system": {"command": _py, "args": _args("magic-system"), "cwd": _mcp_cwd},
        "magic-life": {"command": _py, "args": _args("magic-life"), "cwd": _mcp_cwd},
        "magic-scenes": {"command": _py, "args": _args("magic-scenes"), "cwd": _mcp_cwd},
        "magic-apps": {"command": _py, "args": _args("magic-apps"), "cwd": _mcp_cwd},
        "magic-feishu": {"command": _py, "args": _args("magic-feishu"), "cwd": _mcp_cwd},
        "magic-douyin": {"command": _py, "args": _args("magic-douyin"), "cwd": _mcp_cwd},
        "magic-taobao": {"command": _py, "args": _args("magic-taobao"), "cwd": _mcp_cwd},
        "magic-evolution": {"command": _py, "args": _args("magic-evolution"), "cwd": _mcp_cwd},
        "magic-summary": {"command": _py, "args": _args("magic-summary"), "cwd": _mcp_cwd},
        "magic-wardrobe": {"command": _py, "args": _args("magic-wardrobe"), "cwd": _mcp_cwd},
        "magic-recipe": {"command": _py, "args": _args("magic-recipe"), "cwd": _mcp_cwd},
        "magic-browser": {"command": _py, "args": _args("magic-browser"), "cwd": _mcp_cwd},
        "magic-jarvis": {"command": _py, "args": _args("magic-jarvis"), "cwd": _mcp_cwd},
        "baize-skills": {"command": _py, "args": _args("baize-skills"), "cwd": _mcp_cwd,
                         "env": {"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY", ""),
                                 "ALIYUN_API_KEY": os.getenv("ALIYUN_API_KEY", "")}},
        "filesystem": {"command": _py, "args": _args("magic-notes"), "cwd": _mcp_cwd},
        "ac-control": {"command": _py, "args": _args("ac-control"), "cwd": _mcp_cwd},
    }
    # 修正 baize-skills 的 args（它不是 magic- 前缀）
    all_mcp["baize-skills"]["args"] = ["--mcp", "baize-skills"] if _is_frozen else ["baize_skills_mcp.py"]
    all_mcp["ac-control"]["args"] = ["--mcp", "ac-control"] if _is_frozen else ["mcp_ir_control.py"]
    return all_mcp


# 模块加载时构建一次（frozen 状态不变）
ALL_MCP = _build_all_mcp()


def resolve(mcp_set: str = "all") -> dict:
    """解析启用的 MCP server 配置

    Args:
        mcp_set: "none" / "all" / 单个 MCP 名

    Returns:
        {name: {command, args, cwd}} 字典（可能为空）
    """
    from app.mcp_gate import resolve_mcp_profile
    from app.llm_config import demo_mode_active, ollama_online

    # Demo 规则模式（无 LLM）不启 MCP
    if demo_mode_active() and not ollama_online():
        log.info("[mcp_registry] Demo 规则模式: 不启 MCP（无 LLM）")
        return {}
    if mcp_set == "none":
        return {}
    elif mcp_set == "all":
        enabled = resolve_mcp_profile()
        return {k: v for k, v in ALL_MCP.items() if k in enabled}
    else:
        return {mcp_set: ALL_MCP[mcp_set]} if mcp_set in ALL_MCP else {}
