"""Charlie - 应用模块包"""
import importlib.util as _iu
import os as _os


def load_magic_module(name: str, filename: str = None):
    """加载 magic-*.py 模块（统一路径策略，#3 修复的跨文件版本）

    Args:
        name: 逻辑模块名（如 "magic_scenes"）
        filename: 文件名（如 "magic-scenes.py"）；默认 name + ".py"
    """
    fname = filename or (name.replace("_", "-") + ".py")
    # 尝试两种路径：PROJECT_DIR（voice_agent 传 cwd）和上级 charlie/ 目录
    candidates = [
        _os.path.join(_os.getcwd(), fname),
        _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), fname),
    ]
    for path in candidates:
        if not _os.path.exists(path):
            continue
        _spec = _iu.spec_from_file_location(name, path)
        if _spec and _spec.loader:
            _mod = _iu.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            return _mod
    return None

