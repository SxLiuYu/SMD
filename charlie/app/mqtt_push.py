"""MQTT 信令通道 — 主动摇醒 ESP32 建立 WebSocket

ESP32 固件订阅 charlie/esp32/{device_id}/wake，
收到后主动建 WS → 服务器 flush pending TTS → ESP32 播放。

MQTT broker 可用：
- 本地 mosquitto (apt install mosquitto)
- 公网 EMQX (broker.emqx.io:1883)
- 自建 docker (emqx/emqx)

配置：
  MQTT_BROKER=127.0.0.1       # broker 地址
  MQTT_PORT=1883              # broker 端口
  MQTT_USER=                  # 用户名（可选）
  MQTT_PASSWORD=              # 密码（可选）
  MQTT_DEVICE_ID=esp32-default # ESP32 设备 ID（固件 hello 里上报的 chip_id）
"""
import os, json, logging, threading

log = logging.getLogger("magic")

_client = None
_initialized = False
_init_lock = threading.Lock()

MQTT_BROKER = os.getenv("MQTT_BROKER", "")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_DEVICE_ID = os.getenv("MQTT_DEVICE_ID", "esp32-default")

WAKE_TOPIC_TEMPLATE = "charlie/esp32/{device_id}/wake"


def _init_client():
    """惰性初始化 MQTT 客户端（只在第一次调用时连接）"""
    global _client, _initialized
    if _initialized:
        return _client
    with _init_lock:
        if _initialized:
            return _client
        if not MQTT_BROKER:
            log.debug("[mqtt] MQTT_BROKER 未配置，跳过初始化")
            _initialized = True
            return None
        try:
            import paho.mqtt.client as mqtt
            _client = mqtt.Client(client_id=f"charlie-server-{os.getpid()}")
            if MQTT_USER:
                _client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
            _client.connect(MQTT_BROKER, MQTT_PORT, 60)
            _client.loop_start()  # 后台线程处理心跳
            _initialized = True
            log.info(f"[mqtt] 已连接 {MQTT_BROKER}:{MQTT_PORT} (device={MQTT_DEVICE_ID})")
            return _client
        except ImportError:
            log.warning("[mqtt] paho-mqtt 未安装，运行 pip install paho-mqtt")
            _initialized = True
            return None
        except Exception as e:
            log.warning(f"[mqtt] 连接失败: {e}")
            _initialized = True
            return None


def publish_wake(device_id: str = "", reason: str = "reminder") -> bool:
    """发 MQTT wake 消息摇醒 ESP32 建连

    Args:
        device_id: ESP32 设备 ID（留空用默认 MQTT_DEVICE_ID）
        reason: 唤醒原因（reminder/greeting/decision）
    Returns:
        True=已发送, False=未配置/失败
    """
    client = _init_client()
    if client is None:
        return False
    did = device_id or MQTT_DEVICE_ID
    topic = WAKE_TOPIC_TEMPLATE.format(device_id=did)
    payload = json.dumps({"type": "wake", "reason": reason}, ensure_ascii=False)
    try:
        result = client.publish(topic, payload, qos=1)
        log.info(f"[mqtt] wake → {topic} (reason={reason}, mid={result.mid})")
        return True
    except Exception as e:
        log.warning(f"[mqtt] publish 失败: {e}")
        return False


def is_available() -> bool:
    """MQTT 是否可用（已配置且连接成功）"""
    return _init_client() is not None
