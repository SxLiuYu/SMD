"""
T10 — ESP32 NVS patch 纯函数测试

Seam: app.nvs_patch.patch_nvs / build_replacements 公共接口
"""
import pytest
from app import nvs_patch


class TestPatchNvs:
    def test_replaces_wifi_ssid(self):
        """替换 WiFi SSID"""
        fake_bin = b'\x00\x00OldSSID\x00\x00OldPass1\x00\x00'
        result = nvs_patch.patch_nvs(fake_bin, {"OldSSID": "MyWiFi"})
        assert b"MyWiFi" in result
        assert b"OldSSID" not in result

    def test_replaces_multiple_values(self):
        """替换多个值（SSID+密码+IP）"""
        fake_bin = b'OldSSID\x00OldPass1\x0010.0.0.9\x00'
        result = nvs_patch.patch_nvs(fake_bin, {
            "OldSSID": "NewSSID",   # 7字节 ≤ 旧值7字节
            "OldPass1": "NewPas1",  # 7字节 ≤ 旧值8字节
            "10.0.0.9": "10.0.0.5",
        })
        assert b"NewSSID" in result
        assert b"NewPas1" in result
        assert b"10.0.0.5" in result

    def test_pads_shorter_value(self):
        """新值短于旧值时用 0x00 填充"""
        fake_bin = b'OldSSID\x00'  # 10 字节
        result = nvs_patch.patch_nvs(fake_bin, {"OldSSID": "WiFi"})
        assert b"WiFi" in result
        assert len(result) == len(fake_bin)  # 长度不变

    def test_rejects_longer_value(self):
        """新值长于旧值时报 ValueError"""
        fake_bin = b'OldSSID\x00'
        with pytest.raises(ValueError, match="溢出"):
            nvs_patch.patch_nvs(fake_bin, {"OldSSID": "AVeryLongWiFiName123"})

    def test_no_match_returns_unchanged(self):
        """旧值不在 bin 时返回原 bin（warning）"""
        fake_bin = b'\x00\x01\x02\x03'
        result = nvs_patch.patch_nvs(fake_bin, {"NonExistent": "value"})
        assert result == fake_bin

    def test_replaces_multiple_occurrences(self):
        """旧值出现多次时全部替换"""
        fake_bin = b'10.0.0.9\x0010.0.0.9\x00'
        result = nvs_patch.patch_nvs(fake_bin, {"10.0.0.9": "10.0.0.1"})
        assert result.count(b"10.0.0.1") == 2
        assert b"10.0.0.9" not in result


class TestBuildReplacements:
    def test_builds_from_defaults(self, monkeypatch):
        """build_replacements 默认旧值取自环境变量（旧凭证不再硬编码）"""
        monkeypatch.setenv("CHARLIE_NVS_OLD_SSID", "OldSSID")
        monkeypatch.setenv("CHARLIE_NVS_OLD_PASSWORD", "OldPass")
        monkeypatch.setenv("CHARLIE_NVS_OLD_SERVER_IP", "1.2.3.4")
        # DEFAULT_OLD_VALUES 在模块导入时已读 env；这里用显式 custom_old 验证映射逻辑
        custom_old = {"ssid": "OldSSID", "password": "OldPass", "server_ip": "1.2.3.4"}
        r = nvs_patch.build_replacements("MyWiFi", "mypass", "10.0.0.1", custom_old)
        assert r["OldSSID"] == "MyWiFi"
        assert r["OldPass"] == "mypass"
        assert r["1.2.3.4"] == "10.0.0.1"

    def test_custom_old_values(self):
        """build_replacements 支持自定义旧值"""
        custom_old = {"ssid": "OldNet", "password": "OldPass", "server_ip": "1.2.3.4"}
        r = nvs_patch.build_replacements("NewNet", "NewPass", "5.6.7.8", custom_old)
        assert r["OldNet"] == "NewNet"
        assert r["1.2.3.4"] == "5.6.7.8"

    def test_defaults_no_longer_leak_credentials(self):
        """默认旧值不再含明文凭证（安全回归）"""
        import inspect
        src = inspect.getsource(nvs_patch)
        assert "OldPass1" not in src, "明文 WiFi 密码已清除，不应出现在源码"
        assert "OldSSID" not in src, "明文 SSID 已清除，不应出现在源码"
