"""
Charlie 语音助手 — PyInstaller 入口点

用法:
    charlie                  # 启动服务 (默认)
    charlie --mcp <name>     # 以 MCP 子进程模式运行 (被主进程启动)

说明:
    PyInstaller 打包后，所有 Python 源码被冻结为单个可执行文件。
    MCP 子进程通过 subprocess 启动同一个可执行文件 + --mcp 参数，
    而非启动 Python 解释器 + .py 文件。
"""
import sys
import os
import shutil
import webbrowser


def _ensure_first_run(base_dir: str) -> bool:
    """首次启动检测：缺 .env 则从 .env.example 复制 + 开浏览器到 /welcome

    返回 True 表示是首次运行（已打开引导页），False 表示已配置。
    """
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        return False
    # 从 .env.example 复制空白模板
    example = os.path.join(base_dir, ".env.example")
    if os.path.exists(example):
        shutil.copy(example, env_path)
    else:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# Charlie 语音助手配置\n# 请访问 http://localhost:8000/setup 填写\n")
    # 开浏览器到 /welcome 引导页
    port = 8000
    try:
        from app.config import http_port
        port = http_port()
    except Exception:
        pass
    webbrowser.open(f"http://localhost:{port}/welcome")
    return True


def _run_preflight():
    """运行外部二进制依赖检测（缺失只 warning）"""
    try:
        from app.preflight import run_preflight
        run_preflight()
    except Exception as e:
        print(f"[preflight] 检测跳过: {e}", file=sys.stderr)


def main():
    # 确保工作目录是可执行文件所在目录
    if getattr(sys, 'frozen', False):
        _base = os.path.dirname(sys.executable)
        os.chdir(_base)
        # 将 bin/ 目录加入 PATH (ffmpeg) — PyInstaller 可能放在 _base/bin 或 _base/_internal/bin
        for _bin_dir in [os.path.join(_base, 'bin'),
                         os.path.join(_base, '_internal', 'bin')]:
            if os.path.isdir(_bin_dir):
                os.environ['PATH'] = _bin_dir + os.pathsep + os.environ.get('PATH', '')
        # 创建运行时必需的空文件
        for f in ['conversation_history.json']:
            p = os.path.join(_base, f)
            if not os.path.exists(p):
                with open(p, 'w') as fh:
                    fh.write('[]')
        # T9: 首次启动检测 + preflight
        _ensure_first_run(_base)
        _run_preflight()

    # MCP 子进程模式: 启动指定的 MCP server
    if len(sys.argv) >= 3 and sys.argv[1] == '--mcp':
        mcp_name = sys.argv[2]
        _run_mcp_server(mcp_name)
        return

    # 主服务模式: 启动 voice_server
    _run_server()

def _run_mcp_server(name: str):
    """启动 MCP 子进程 (magic-* / baize-skills / ...)"""
    import importlib.util, os, sys
    # 逻辑名 → 源码文件名 (带连字符的模块名 Python 无法直接 import)
    mcp_files = {
        "magic-info": "magic-info.py",
        "magic-music": "magic-music.py",
        "magic-reminder": "magic-reminder.py",
        "magic-notes": "magic-notes.py",
        "magic-system": "magic-system.py",
        "magic-life": "magic-life.py",
        "magic-scenes": "magic-scenes.py",
        "magic-evolution": "magic-evolution.py",
        "magic-summary": "magic-summary.py",
        "magic-wardrobe": "magic-wardrobe.py",
        "magic-browser": "magic-browser.py",
        "baize-skills": "baize_skills_mcp.py",
        "filesystem": "magic-notes.py",  # 使用备忘录工具（文件读写）
        "ac-control": "mcp_ir_control.py",
    }
    filename = mcp_files.get(name)
    if not filename:
        print(f"未知 MCP: {name}", file=sys.stderr)
        sys.exit(1)
    # 按文件路径加载 (PyInstaller frozen 模式下 __file__ 在 _MEIPASS)
    if getattr(sys, 'frozen', False):
        _base = os.path.join(os.path.dirname(sys.executable), '_internal')
    else:
        _base = os.getcwd()
    filepath = os.path.join(_base, filename)
    if not os.path.exists(filepath):
        # 尝试直接从源码目录
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if not os.path.exists(filepath):
        print(f"MCP {name} 文件不存在: {filepath}", file=sys.stderr)
        sys.exit(1)
    try:
        mod_name = name.replace('-', '_') + '_mcp'
        spec = importlib.util.spec_from_file_location(mod_name, filepath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.mcp.run()
    except Exception as e:
        print(f"MCP {name} 启动失败: {e}", file=sys.stderr)
        sys.exit(1)

def _run_server():
    """启动 voice_server (FastAPI + Uvicorn)"""
    import uvicorn
    from voice_server import app
    from app.config import http_port
    uvicorn.run(app, host="0.0.0.0", port=http_port(), log_level="info")

if __name__ == "__main__":
    main()