"""Charlie - 应用模块包

提供 magic 模块的延迟加载 registry，替代 load_magic_module() 动态导入。
新增 magic 模块时只需在此 registry 添加一行，无需修改 voice_server.py 中各 API 端点。
"""
import importlib.util as _iu
import os as _os
import logging as _logging

_log = _logging.getLogger("magic")

# ── Magic 模块注册表 ──
# 格式: {逻辑名: 文件名}
# 新增 magic 模块时在此添加一行即可
_MAGIC_MODULES = {
    "magic_decisions": "magic-decisions.py",
    "magic_scenes": "magic-scenes.py",
    "magic_memory": "magic-memory.py",
    "magic_evolution": "magic-evolution.py",
}

# 懒加载缓存
_loaded: dict[str, object] = {}


def _resolve_path(filename: str) -> str | None:
    """解析 magic 模块文件路径。"""
    candidates = [
        _os.path.join(_os.getcwd(), filename),
        _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), filename),
    ]
    for path in candidates:
        if _os.path.exists(path):
            return path
    return None


def load_magic_module(name: str, filename: str = None):
    """加载 magic-*.py 模块（统一路径策略，带缓存）。

    Args:
        name: 逻辑模块名（如 "magic_scenes"）
        filename: 文件名（如 "magic-scenes.py"）；默认从 registry 查找
    """
    fname = filename or _MAGIC_MODULES.get(name)
    if not fname:
        fname = name.replace("_", "-") + ".py"

    # 检查缓存
    if name in _loaded:
        return _loaded[name]

    path = _resolve_path(fname)
    if not path:
        _log.warning(f"[app] 找不到模块: {fname}")
        return None

    _spec = _iu.spec_from_file_location(name, path)
    if _spec and _spec.loader:
        _mod = _iu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        _loaded[name] = _mod
        return _mod
    return None


def get_magic_module(name: str):
    """获取已缓存的 magic 模块，未加载时自动加载。

    比 load_magic_module 更简洁，推荐在 API 端点中使用。
    """
    if name in _loaded:
        return _loaded[name]
    return load_magic_module(name)


def preload_magic_modules() -> int:
    """启动时预加载所有注册的 magic 模块。返回成功加载数。"""
    count = 0
    for name in _MAGIC_MODULES:
        if load_magic_module(name) is not None:
            count += 1
    _log.info(f"[app] 预加载 magic 模块: {count}/{len(_MAGIC_MODULES)}")
    return count