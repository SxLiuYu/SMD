"""
T4 — setup 路由 + mcp-status API 测试

Seam: HTTP API (GET /api/setup/mcp-status, GET /api/setup)
"""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import voice_server


@pytest.fixture(scope="module")
def client():
    os.environ["SKIP_BACKGROUND"] = "1"
    os.environ.setdefault("GLM_KEY", "test")
    os.environ.setdefault("TTS_KEY", "test")
    os.environ.setdefault("ASR_KEY", "test")
    os.environ.setdefault("AMAP_KEY", "test")
    yield TestClient(voice_server.app)


class TestSetupMcpStatus:
    def test_mcp_status_returns_groups(self, client):
        """GET /api/setup/mcp-status 返回分组结构"""
        r = client.get("/api/setup/mcp-status")
        assert r.status_code == 200
        data = r.json()
        assert "groups" in data
        assert isinstance(data["groups"], list)
        assert len(data["groups"]) > 0

    def test_mcp_status_group_has_entries(self, client):
        """每个分组含 entries 列表"""
        data = client.get("/api/setup/mcp-status").json()
        for g in data["groups"]:
            assert "key" in g
            assert "label" in g
            assert "entries" in g
            assert isinstance(g["entries"], list)

    def test_mcp_status_entry_fields(self, client):
        """每个 entry 含 name/configured/required/demo_supported/description"""
        data = client.get("/api/setup/mcp-status").json()
        for g in data["groups"]:
            for e in g["entries"]:
                assert "name" in e
                assert "configured" in e
                assert "required" in e
                assert "description" in e

    def test_mcp_status_has_demo_mode(self, client):
        """返回含 demo_mode 字段"""
        data = client.get("/api/setup/mcp-status").json()
        assert "demo_mode" in data
        assert "llm_available" in data


class TestSetupGet:
    def test_get_setup_returns_env_values(self, client):
        """GET /api/setup 返回当前 .env 值 + demo_mode 标记"""
        r = client.get("/api/setup")
        assert r.status_code == 200
        data = r.json()
        assert "__demo_mode" in data
        assert "__llm_available" in data
        assert "__missing_required" in data
