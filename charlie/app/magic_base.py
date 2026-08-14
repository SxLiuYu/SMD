"""magic-* MCP 模块公共基类 — 消除 22 个模块的重复代码

提供:
- create_magic_mcp(name) — 统一 FastMCP 工厂 + 日志
- get_data_dir() — 统一数据目录
- load_json(path) / save_json(path, data) — 原子 JSON 文件 I/O（含锁）
- ProjectDirContext — 上下文管理器（os.chdir 模式）
"""
import os
import json
import threading
import logging
from contextlib import contextmanager
from mcp.server.fastmcp import FastMCP


# ---------------------------------------------------------------------------
# 统一数据目录
# ---------------------------------------------------------------------------

def get_data_dir(caller_file: str | None = None) -> str:
    """返回 magic 模块统一的数据目录。

    caller_file: 调用者的 __file__（用于在未设置 ASSISTANT_KID_DATA_DIR 时
    回退到调用者所在目录而非 app/ 目录）。默认用本模块所在目录。
    """
    base = caller_file or __file__
    return os.environ.get("ASSISTANT_KID_DATA_DIR", os.path.dirname(os.path.abspath(base)))


# ---------------------------------------------------------------------------
# 统一日志
# ---------------------------------------------------------------------------

def get_magic_logger(name: str) -> logging.Logger:
    """返回 magic-* 模块的统一 logger"""
    return logging.getLogger("magic")


# ---------------------------------------------------------------------------
# 统一 FastMCP 工厂
# ---------------------------------------------------------------------------

def create_magic_mcp(name: str) -> FastMCP:
    """创建统一配置的 FastMCP 实例"""
    return FastMCP(name)


# ---------------------------------------------------------------------------
# 项目目录上下文管理器（替代 os.chdir 模式）
# ---------------------------------------------------------------------------

@contextmanager
def project_dir():
    """临时切换到项目目录，完成后恢复。

    替代 magic-* 模块中重复的 os.chdir(os.path.dirname(os.path.abspath(__file__))) 模式。
    """
    old = os.getcwd()
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        yield
    finally:
        os.chdir(old)


# ---------------------------------------------------------------------------
# 原子 JSON 文件读写（含锁）
# ---------------------------------------------------------------------------

_json_locks: dict[str, threading.Lock] = {}
_json_locks_lock = threading.Lock()


def _get_json_lock(path: str) -> threading.Lock:
    """获取或创建文件级锁"""
    with _json_locks_lock:
        if path not in _json_locks:
            _json_locks[path] = threading.Lock()
        return _json_locks[path]


def load_json(path: str, default=None) -> dict:
    """原子读取 JSON 文件，文件不存在时返回 default"""
    if default is None:
        default = {}
    lock = _get_json_lock(path)
    with lock:
        try:
            if not os.path.exists(path):
                return default
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            return default
        except (json.JSONDecodeError, OSError):
            return default


def save_json(path: str, data: dict | list) -> None:
    """原子写入 JSON 文件（先写临时文件再 rename）"""
    lock = _get_json_lock(path)
    with lock:
        tmp = path + ".tmp"
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except OSError:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise


def load_json_list(path: str, default=None) -> list:
    """原子读取 JSON 文件，返回列表，文件不存在时返回 default"""
    if default is None:
        default = []
    lock = _get_json_lock(path)
    with lock:
        try:
            if not os.path.exists(path):
                return default
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            return default
        except (json.JSONDecodeError, OSError):
            return default