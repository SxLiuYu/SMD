"""ESP32 固件 NVS 二进制 patch — 替换 WiFi/服务器地址

固件 NVS 里硬编码了 WiFi SSID/密码和服务器 IP。本模块做二进制字符串替换：
在 bin 里搜索旧值，替换为新值。新值长度必须 ≤ 旧值（超出报错），短于则 0x00 填充。

不重新编译固件，仅 patch 同一份 bin（符合 RTK.md 约束）。
"""
import os
import logging

log = logging.getLogger("magic")

# 固件里 baked 的默认值（旧固件刷机前替换值用；新分发版用户自行在引导页填）
# 旧版本的明文凭证已移除，改为从环境变量读取，避免凭证泄漏
DEFAULT_OLD_VALUES = {
    "ssid": os.environ.get("CHARLIE_NVS_OLD_SSID", ""),
    "password": os.environ.get("CHARLIE_NVS_OLD_PASSWORD", ""),
    "server_ip": os.environ.get("CHARLIE_NVS_OLD_SERVER_IP", ""),
}


def patch_nvs(bin_bytes: bytes, replacements: dict[str, str]) -> bytes:
    """二进制替换固件里的字符串值

    Args:
        bin_bytes: 固件 bin 的原始字节
        replacements: {旧值: 新值} 映射，如 {"***REMOVED***": "MyWiFi"}

    Returns:
        patch 后的新 bin 字节。新值长度必须 ≤ 旧值（超出 ValueError）。
        短于旧值时用 0x00 填充保持长度。
    """
    data = bytearray(bin_bytes)
    for old, new in replacements.items():
        old_b = old.encode("utf-8")
        new_b = new.encode("utf-8")
        if len(new_b) > len(old_b):
            raise ValueError(
                f"新值 '{new}' 长度({len(new_b)})超过旧值 '{old}' 长度({len(old_b)})，"
                "NVS 字段溢出。请缩短新值或重新编译固件。"
            )
        idx = data.find(old_b)
        count = 0
        while idx != -1:
            padded = new_b + b'\x00' * (len(old_b) - len(new_b))
            data[idx:idx + len(old_b)] = padded
            count += 1
            idx = data.find(old_b, idx + len(old_b))
        if count > 0:
            log.info(f"[nvs_patch] 替换 '{old}' → '{new}' ({count} 处)")
        else:
            log.warning(f"[nvs_patch] 旧值 '{old}' 未在 bin 中找到")
    return bytes(data)


def build_replacements(ssid: str, password: str, server_ip: str,
                       old_values: dict | None = None) -> dict[str, str]:
    """构建替换映射

    Args:
        ssid: 新 WiFi SSID
        password: 新 WiFi 密码
        server_ip: 新服务器 IP
        old_values: 旧值映射（默认用 DEFAULT_OLD_VALUES）
    """
    old = old_values or DEFAULT_OLD_VALUES
    return {
        old["ssid"]: ssid,
        old["password"]: password,
        old["server_ip"]: server_ip,
    }
