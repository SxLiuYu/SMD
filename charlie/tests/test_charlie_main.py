"""
T9 — charlie_main 首次启动检测测试

Seam: charlie_main._ensure_first_run 公共接口
"""
import os
from unittest.mock import patch, MagicMock

import charlie_main


class TestEnsureFirstRun:
    def test_creates_env_from_example_when_missing(self, tmp_path):
        """缺 .env 时从 .env.example 复制"""
        example = tmp_path / ".env.example"
        example.write_text("ARK_KEY=\nBAIDU_API_KEY=\n")
        assert not (tmp_path / ".env").exists()
        with patch("webbrowser.open") as mock_open:
            result = charlie_main._ensure_first_run(str(tmp_path))
        assert result is True
        assert (tmp_path / ".env").exists()
        assert (tmp_path / ".env").read_text() == "ARK_KEY=\nBAIDU_API_KEY=\n"
        mock_open.assert_called_once()

    def test_creates_empty_env_when_no_example(self, tmp_path):
        """无 .env.example 时创建空白 .env"""
        with patch("webbrowser.open") as mock_open:
            result = charlie_main._ensure_first_run(str(tmp_path))
        assert result is True
        assert (tmp_path / ".env").exists()
        mock_open.assert_called_once()

    def test_skips_when_env_exists(self, tmp_path):
        """已存在 .env 时返回 False，不开浏览器"""
        (tmp_path / ".env").write_text("ARK_KEY=test")
        with patch("webbrowser.open") as mock_open:
            result = charlie_main._ensure_first_run(str(tmp_path))
        assert result is False
        mock_open.assert_not_called()

    def test_opens_welcome_url(self, tmp_path):
        """开浏览器到 /welcome 页面"""
        with patch("webbrowser.open") as mock_open:
            charlie_main._ensure_first_run(str(tmp_path))
        url = mock_open.call_args[0][0]
        assert "/welcome" in url
        assert "localhost" in url
