"""静态文件服务工具 — 从 voice_server.py 提取

提供 ETag/HTML/JSON 响应、PWA manifest、应用图标等可复用的 HTTP 工具函数。
"""
import os
import json
import struct
import zlib
import hashlib
import threading
from typing import Callable

from fastapi import Request
from fastapi.responses import Response


# ---------------------------------------------------------------------------
# ETag helpers
# ---------------------------------------------------------------------------

def _weak_etag(token: str) -> str:
    """Build a compact weak ETag from an opaque cache token."""
    return 'W/"' + hashlib.sha256(token.encode("utf-8")).hexdigest()[:16] + '"'


def _etag_headers(etag: str) -> dict:
    return {"ETag": etag, "Cache-Control": "no-cache", "Vary": "Accept-Encoding"}


def _if_none_matches(request: Request, etag: str) -> bool:
    """Match If-None-Match, tolerating comma-separated weak/strong ETags."""
    cached_etags = []
    for value in request.headers.get("if-none-match", "").split(","):
        value = value.strip()
        if not value:
            continue
        cached_etags.append(value)
        if value.startswith("W/"):
            cached_etags.append(value[2:])
        else:
            cached_etags.append("W/" + value)
    return etag in cached_etags


def _not_modified_response(etag: str) -> Response:
    return Response(status_code=304, headers=_etag_headers(etag))


def _file_etag_token(path: str, prefix: str) -> str:
    """Return a stable file token without opening or reading the file."""
    try:
        stat = os.stat(path)
        return f"{prefix}:{stat.st_mtime_ns}:{stat.st_size}:{stat.st_ino}"
    except FileNotFoundError:
        return f"{prefix}:missing"
    except OSError as exc:
        return f"{prefix}:error:{exc.__class__.__name__}"


def _file_not_modified_response(request: Request, path: str, prefix: str) -> Response | None:
    """Return 304 only if both the request ETag and current file metadata still match."""
    etag = _weak_etag(_file_etag_token(path, prefix))
    if not _if_none_matches(request, etag):
        return None
    if _weak_etag(_file_etag_token(path, prefix)) != etag:
        return None
    return _not_modified_response(etag)


# ---------------------------------------------------------------------------
# Cached text file reading
# ---------------------------------------------------------------------------

_open_text_file = open
_text_file_cache: dict[str, tuple[tuple[int, int, int], str]] = {}
_text_file_cache_lock = threading.Lock()


def _read_cached_text(path: str, return_token: bool = False):
    """Read a small static text file, reusing contents while file metadata is unchanged."""
    for _ in range(2):
        stat = os.stat(path)
        token = (stat.st_mtime_ns, stat.st_size, stat.st_ino)
        with _text_file_cache_lock:
            cached = _text_file_cache.get(path)
        if cached is not None and cached[0] == token:
            return (cached[1], token) if return_token else cached[1]

        with _open_text_file(path, encoding="utf-8") as f:
            text = f.read()

        after_stat = os.stat(path)
        after_token = (after_stat.st_mtime_ns, after_stat.st_size, after_stat.st_ino)
        if token == after_token:
            with _text_file_cache_lock:
                cached = _text_file_cache.get(path)
                if cached is None or cached[0] != token:
                    _text_file_cache[path] = (token, text)
            return (text, token) if return_token else text
    return (text, token) if return_token else text


# ---------------------------------------------------------------------------
# HTML / JSON response builders
# ---------------------------------------------------------------------------

def _html_response(request: Request, path: str, prefix: str) -> Response:
    """Return HTML with a file-based weak ETag and no-store validation headers."""
    cached = _file_not_modified_response(request, path, prefix)
    if cached is not None:
        return cached
    text, token = _read_cached_text(path, return_token=True)
    etag = _weak_etag(f"{prefix}:{token[0]}:{token[1]}:{token[2]}")
    if _if_none_matches(request, etag):
        return _not_modified_response(etag)
    body = text.encode("utf-8")
    headers = _etag_headers(etag)
    headers["Content-Length"] = str(len(body))
    if request.method == "HEAD":
        body = b""
    return Response(content=body, media_type="text/html; charset=utf-8", headers=headers)


def _json_response(
    request: Request,
    payload: dict | Callable[[], dict],
    etag_token: str | None = None,
) -> Response:
    """Return compact JSON with a weak ETag for polling-heavy GET endpoints."""
    if etag_token is not None:
        etag = _weak_etag(etag_token)
        if _if_none_matches(request, etag):
            return _not_modified_response(etag)
        resolved_payload = payload() if callable(payload) else payload
        body = json.dumps(resolved_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    else:
        resolved_payload = payload() if callable(payload) else payload
        body = json.dumps(resolved_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        etag = 'W/"' + hashlib.sha256(body).hexdigest()[:16] + '"'
        if _if_none_matches(request, etag):
            return _not_modified_response(etag)
    return Response(content=body, media_type="application/json", headers=_etag_headers(etag))


# ---------------------------------------------------------------------------
# PWA manifest
# ---------------------------------------------------------------------------

_manifest_lock = threading.Lock()
_MANIFEST_BODY: tuple[bytes, str] | None = None


def _build_manifest_payload() -> dict:
    return {
        "name": "Charlie",
        "short_name": "Charlie",
        "description": "中国版贾维斯 - AI语音助理，全屋智能家居控制",
        "start_url": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0f0c29",
        "theme_color": "#e94560",
        "icons": [
            {"src": "/icon.svg", "sizes": "512x512", "type": "image/svg+xml"},
            {"src": "/icon.svg", "sizes": "192x192", "type": "image/svg+xml"}
        ],
        "categories": ["productivity", "lifestyle", "utilities"],
        "lang": "zh-CN",
        "dir": "ltr"
    }


def _manifest_response(request: Request) -> Response:
    """Serve the immutable PWA manifest once, supporting HEAD and conditional GET."""
    global _MANIFEST_BODY
    with _manifest_lock:
        if _MANIFEST_BODY is None:
            body = json.dumps(
                _build_manifest_payload(), ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            etag = 'W/"' + hashlib.sha256(body).hexdigest()[:16] + '"'
            _MANIFEST_BODY = (body, etag)
        body, etag = _MANIFEST_BODY

    if _if_none_matches(request, etag):
        return _not_modified_response(etag)

    headers = _etag_headers(etag)
    headers["Content-Length"] = str(len(body))
    content = b"" if request.method == "HEAD" else body
    return Response(content=content, media_type="application/json", headers=headers)


# ---------------------------------------------------------------------------
# App icon (inline PNG)
# ---------------------------------------------------------------------------

def _build_app_icon_png() -> bytes:
    """Build a small inline PNG icon without adding a binary asset to the repo."""
    size = 64
    bg = (15, 12, 41)
    fg = (233, 69, 96)
    cx = cy = size // 2
    radius = size // 3

    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            color = fg if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2 else bg
            raw.extend(color)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return b"".join((
        b"\x89PNG\r\n\x1a\n",
        chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)),
        chunk(b"IDAT", zlib.compress(bytes(raw), 9)),
        chunk(b"IEND", b""),
    ))


_APP_ICON_PNG = _build_app_icon_png()
_ICON_HEADERS = {"Cache-Control": "public, max-age=86400"}
_APP_ICON_ETAG = 'W/"' + hashlib.sha256(_APP_ICON_PNG).hexdigest()[:16] + '"'