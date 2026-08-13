"""
T2 — 消除硬编码 + LAN info API 测试

Seam: HTTP API (FastAPI TestClient)
- /api/lan-info 返回 {http_url, https_url, lan_ip}
- /xiaozhi/ota 返回的 ws_url 端口跟随 ASSISTANT_KID_HTTP_PORT（不再硬编码 :8000）
"""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    os.environ["SKIP_BACKGROUND"] = "1"
    os.environ.setdefault("GLM_KEY", "test")
    os.environ.setdefault("TTS_KEY", "test")
    os.environ.setdefault("ASR_KEY", "test")
    os.environ.setdefault("AMAP_KEY", "test")
    import voice_server
    yield TestClient(voice_server.app)


class TestLanInfoAndOta:
    def test_lan_info_returns_structure(self, client):
        """GET /api/lan-info 返回 {http_url, https_url, lan_ip}"""
        r = client.get("/api/lan-info")
        assert r.status_code == 200
        data = r.json()
        assert "http_url" in data
        assert "https_url" in data
        assert "lan_ip" in data

    def test_lan_info_http_url_contains_port(self, client):
        """http_url 含当前 HTTP 端口"""
        from app.config import http_port
        r = client.get("/api/lan-info")
        data = r.json()
        assert str(http_port()) in data["http_url"]

    def test_ota_ws_url_not_hardcoded_8000(self, client):
        """OTA 返回的 ws_url 端口不硬编码 8000，跟随 http_port()"""
        from app.config import http_port, invalidate_lan_origins_cache
        invalidate_lan_origins_cache()
        r = client.post("/xiaozhi/ota", json={})
        assert r.status_code == 200
        ws_url = r.json()["websocket"]["url"]
        assert str(http_port()) in ws_url, f"ws_url 应含端口 {http_port()}, 实际: {ws_url}"
