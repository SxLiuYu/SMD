"""
T10 — ESP32 NVS patch 纯函数测试

Seam: app.nvs_patch.patch_nvs / build_replacements 公共接口
"""
import pytest
from app import nvs_patch


class TestPatchNvs:
    def test_replaces_wifi_ssid(self):
        """替换 WiFi SSID"""
        fake_bin = b'\x00\x00***REMOVED***\x00\x00***REMOVED***\x00\x00'
        result = nvs_patch.patch_nvs(fake_bin, {"***REMOVED***": "MyWiFi"})
        assert b"MyWiFi" in result
        assert b"***REMOVED***" not in result

    def test_replaces_multiple_values(self):
        """替换多个值（SSID+密码+IP）"""
        fake_bin = b'***REMOVED***\x00***REMOVED***\x00192.168.1.3\x00'
        result = nvs_patch.patch_nvs(fake_bin, {
            "***REMOVED***": "HomeWiFi",
            "***REMOVED***": "mypass8",  # 7字节 ≤ 旧值8字节
            "192.168.1.3": "10.0.0.5",
        })
        assert b"HomeWiFi" in result
        assert b"mypass8" in result
        assert b"10.0.0.5" in result

    def test_pads_shorter_value(self):
        """新值短于旧值时用 0x00 填充"""
        fake_bin = b'***REMOVED***\x00'  # 10 字节
        result = nvs_patch.patch_nvs(fake_bin, {"***REMOVED***": "WiFi"})
        assert b"WiFi" in result
        assert len(result) == len(fake_bin)  # 长度不变

    def test_rejects_longer_value(self):
        """新值长于旧值时报 ValueError"""
        fake_bin = b'***REMOVED***\x00'
        with pytest.raises(ValueError, match="溢出"):
            nvs_patch.patch_nvs(fake_bin, {"***REMOVED***": "AVeryLongWiFiName123"})

    def test_no_match_returns_unchanged(self):
        """旧值不在 bin 时返回原 bin（warning）"""
        fake_bin = b'\x00\x01\x02\x03'
        result = nvs_patch.patch_nvs(fake_bin, {"NonExistent": "value"})
        assert result == fake_bin

    def test_replaces_multiple_occurrences(self):
        """旧值出现多次时全部替换"""
        fake_bin = b'192.168.1.3\x00192.168.1.3\x00'
        result = nvs_patch.patch_nvs(fake_bin, {"192.168.1.3": "10.0.0.1"})
        assert result.count(b"10.0.0.1") == 2
        assert b"192.168.1.3" not in result


class TestBuildReplacements:
    def test_builds_from_defaults(self):
        """build_replacements 用默认旧值构建映射"""
        r = nvs_patch.build_replacements("MyWiFi", "mypass", "10.0.0.1")
        assert r["***REMOVED***"] == "MyWiFi"
        assert r["***REMOVED***"] == "mypass"
        assert r["192.168.1.3"] == "10.0.0.1"

    def test_custom_old_values(self):
        """build_replacements 支持自定义旧值"""
        custom_old = {"ssid": "OldNet", "password": "OldPass", "server_ip": "1.2.3.4"}
        r = nvs_patch.build_replacements("NewNet", "NewPass", "5.6.7.8", custom_old)
        assert r["OldNet"] == "NewNet"
        assert r["1.2.3.4"] == "5.6.7.8"
