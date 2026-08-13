"""xiaozhi MQTT 协议端 — 替代 WebSocket 的常驻连接方案

ESP32 通过 OTA 切换到 MqttProtocol 后:
1. ESP32 常驻连接 MQTT broker
2. 用户唤醒 → ESP32 发 hello 到 publish_topic
3. 服务器回复 hello(含 UDP server/port/AES key/nonce)
4. ESP32 建 UDP → 加密 Opus 双向传输
5. 对话结束 → goodbye → ESP32 回唤醒词模式（MQTT 仍保持）

主动推送: 服务器随时可通过 subscribe_topic 推 JSON 消息
"""
import os, json, asyncio, socket, struct, secrets, logging, threading, time
from typing import Optional, Callable

log = logging.getLogger("magic")

# 常量
OPUS_FRAME_DURATION_MS = 60
UDP_AUDIO_HEADER_SIZE = 16
DOWNLINK_SAMPLE_RATE = 16000
UPLINK_SAMPLE_RATE = 16000

# 端点检测参数（复用 xiaozhi_ws.py 的阈值）
MIN_SPEECH_FRAMES = 12        # 最少语音帧数 (~0.7s)
MAX_UTTERANCE_FRAMES = 600    # 最大语音时长 (~36s)
SILENCE_FRAMES_VAD = 8        # VAD确认静音帧数 (~0.48s)
NOISE_DROP_FRAMES = 200       # 无语音超时丢弃 (~12s)

# 活跃的 UDP 会话: {device_id: {"sock": socket, "aes_key": bytes, "aes_nonce": bytes, "addr": (ip,port)}}
_sessions: dict[str, dict] = {}
_sessions_lock = threading.Lock()


def _generate_aes_key_nonce() -> tuple[bytes, bytes]:
    """生成 16 字节 AES key 和 16 字节 nonce"""
    return secrets.token_bytes(16), secrets.token_bytes(16)


def _hex_encode(data: bytes) -> str:
    return data.hex()


def _aes_ctr_crypt(key: bytes, nonce: bytes, data: bytes) -> bytes:
    """AES-CTR 加密/解密（对称操作）"""
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()
    except ImportError:
        # 降级 pyaes（纯 Python）
        try:
            import pyaes
            aes = pyaes.AESModeOfOperationCTR(key, iv=nonce)
            return aes.encrypt(data) if isinstance(data, bytes) else aes.encrypt(data.encode())
        except ImportError:
            log.error("[mqtt-server] 需要 cryptography 或 pyaes")
            raise


def _build_audio_packet(aes_nonce: bytes, payload: bytes, timestamp: int, sequence: int) -> bytes:
    """构造加密 UDP 音频包

    格式: |type 1|flags 1|payload_len 2(big)|ssrc 4|timestamp 4(big)|sequence 4(big)|encrypted_payload|
    nonce = base_nonce，bytes[2:4]=payload_len, bytes[8:12]=timestamp, bytes[12:16]=sequence
    """
    payload_len = len(payload)
    # 构造 per-packet nonce
    nonce = bytearray(aes_nonce)
    struct.pack_into("!H", nonce, 2, payload_len)       # payload_len big-endian
    struct.pack_into("!I", nonce, 8, timestamp)         # timestamp big-endian
    struct.pack_into("!I", nonce, 12, sequence)          # sequence big-endian

    # 加密 payload
    encrypted = _aes_ctr_crypt(aes_nonce[:16], bytes(nonce), payload)

    # 构造完整包
    header = bytearray(UDP_AUDIO_HEADER_SIZE)
    header[0] = 0x01  # type = audio
    header[1] = 0x00  # flags
    struct.pack_into("!H", header, 2, payload_len)
    struct.pack_into("!I", header, 4, 0)  # ssrc
    struct.pack_into("!I", header, 8, timestamp)
    struct.pack_into("!I", header, 12, sequence)

    return bytes(header) + encrypted


class MqttXiaozhiServer:
    """xiaozhi MQTT 协议服务端

    负责:
    1. 连接 MQTT broker
    2. 订阅设备 publish_topic
    3. 处理 hello → 回复 hello + UDP 配置
    4. UDP 音频收发
    5. 主动推送 TTS 到设备
    """

    def __init__(self):
        self._client = None
        self._udp_sock: Optional[socket.socket] = None
        self._udp_port = 0
        self._local_seq = 0
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._device_id: str = ""

    @property
    def udp_port(self) -> int:
        return self._udp_port

    def start(self, loop: asyncio.AbstractEventLoop):
        """启动 MQTT 服务端（在 FastAPI lifespan 中调用）"""
        broker = os.getenv("MQTT_BROKER", "")
        if not broker:
            log.info("[mqtt-server] MQTT_BROKER 未配置，跳过启动")
            return False

        self._loop = loop
        self._device_id = os.getenv("MQTT_DEVICE_ID", "esp32-default")
        port = int(os.getenv("MQTT_PORT", "1883"))
        user = os.getenv("MQTT_USER", "")
        password = os.getenv("MQTT_PASSWORD", "")
        subscribe_topic = f"charlie/esp32/{self._device_id}/up"   # ESP32 发 → 服务器收
        publish_topic = f"charlie/esp32/{self._device_id}/down"   # 服务器发 → ESP32 收

        # 1. 启动 UDP 音频服务（固定端口，Docker 可映射）
        udp_port = int(os.getenv("MQTT_UDP_PORT", "8888"))
        self._udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._udp_sock.bind(("0.0.0.0", udp_port))
        self._udp_port = udp_port
        self._running = True

        # UDP 接收线程
        threading.Thread(target=self._udp_recv_loop, daemon=True).start()

        # 2. 连接 MQTT broker
        try:
            import paho.mqtt.client as mqtt
            self._client = mqtt.Client(client_id=f"charlie-server-{os.getpid()}")
            if user:
                self._client.username_pw_set(user, password)
            self._client.on_connect = lambda c, u, f, rc, p=None: self._on_mqtt_connect(
                c, subscribe_topic, rc)
            self._client.on_message = lambda c, u, msg: self._on_mqtt_message(msg)
            self._client.connect(broker, port, 60)
            self._client.loop_start()
            self._publish_topic = publish_topic
            log.info(f"[mqtt-server] 已连接 {broker}:{port}, UDP端口={self._udp_port}")
            return True
        except Exception as e:
            log.warning(f"[mqtt-server] 连接失败: {e}")
            self._running = False
            return False

    def _on_mqtt_connect(self, client, subscribe_topic, rc):
        """MQTT 连接成功 → 订阅设备上行 topic"""
        client.subscribe(subscribe_topic)
        log.info(f"[mqtt-server] 已订阅 {subscribe_topic}")

    def _on_mqtt_message(self, msg):
        """收到 ESP32 的 MQTT 消息（hello/listen/goodbye 等）"""
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)
            mtype = data.get("type", "")
            log.info(f"[mqtt-server] 收到 {mtype}: {payload[:100]}")

            if mtype == "hello":
                self._handle_hello(data)
            elif mtype == "listen":
                self._handle_listen(data)
            elif mtype == "goodbye":
                self._handle_goodbye(data)
            elif mtype == "abort":
                self._handle_abort(data)
        except Exception as e:
            log.warning(f"[mqtt-server] 消息处理失败: {e}")

    def _handle_hello(self, data: dict):
        """处理 hello → 回复 hello + UDP 配置"""
        # 生成 AES key/nonce
        aes_key, aes_nonce = _generate_aes_key_nonce()

        # 记录会话
        with _sessions_lock:
            _sessions[self._device_id] = {
                "aes_key": aes_key,
                "aes_nonce": aes_nonce,
                "addr": None,  # UDP 地址在收到第一个包时填充
                "timestamp": time.time(),
            }

        # 获取 LAN IP
        lan_ip = os.getenv("ESP32_OTA_IP", "")
        if not lan_ip:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                lan_ip = s.getsockname()[0]
                s.close()
            except Exception:
                lan_ip = "127.0.0.1"

        # 回复 hello
        response = {
            "type": "hello",
            "transport": "udp",
            "session_id": secrets.token_hex(8),
            "audio_params": {
                "format": "opus",
                "sample_rate": DOWNLINK_SAMPLE_RATE,
                "channels": 1,
                "frame_duration": OPUS_FRAME_DURATION_MS,
            },
            "udp": {
                "server": lan_ip,
                "port": self._udp_port,
                "key": _hex_encode(aes_key),
                "nonce": _hex_encode(aes_nonce),
            },
        }
        self._publish(json.dumps(response, ensure_ascii=False))
        log.info(f"[mqtt-server] hello 回复: UDP {lan_ip}:{self._udp_port}")

    def _handle_listen(self, data: dict):
        """处理 listen → 开始接收语音"""
        state = data.get("state", "")
        if state == "detect":
            log.info(f"[mqtt-server] 唤醒: {data.get('text', '')}")
        elif state == "start":
            log.info("[mqtt-server] 开始监听")
        elif state == "stop":
            log.info("[mqtt-server] 停止监听，开始 ASR")

    def _handle_goodbye(self, data: dict):
        """处理 goodbye → 清理 UDP 会话"""
        with _sessions_lock:
            _sessions.pop(self._device_id, None)
        log.info(f"[mqtt-server] goodbye: {data.get('session_id', '')}")

    def _handle_abort(self, data: dict):
        """处理 abort → 中断当前播放"""
        log.info("[mqtt-server] 中断播放")

    def _publish(self, text: str):
        """推 JSON 消息到 ESP32 的 subscribe_topic"""
        if self._client:
            self._client.publish(self._publish_topic, text, qos=1)

    def push_tts(self, text: str, opus_packets: list[bytes]):
        """主动推送 TTS 到 ESP32

        1. MQTT 发 JSON 通知 TTS 开始
        2. UDP 发加密 Opus 帧
        3. MQTT 发 JSON 通知 TTS 结束
        """
        with _sessions_lock:
            session = _sessions.get(self._device_id)
        if not session:
            log.warning(f"[mqtt-server] 无活跃会话，无法推送 TTS")
            return False

        # MQTT 通知 TTS 开始
        self._publish(json.dumps({
            "type": "tts", "state": "start",
            "text": text,
            "voice": "zh-CN",
        }))

        # UDP 发送加密 Opus 帧
        aes_key = session["aes_key"]
        aes_nonce = session["aes_nonce"]
        addr = session.get("addr")
        if not addr:
            log.warning("[mqtt-server] 无 UDP 地址，跳过音频")
            return False

        ts = int(time.time() * 1000)
        # 异步发送：在独立线程中逐帧发送，不阻塞调用方
        def _send_audio():
            for i, pkt in enumerate(opus_packets):
                packet = _build_audio_packet(aes_nonce, pkt, ts + i * 60, i)
                try:
                    self._udp_sock.sendto(packet, addr)
                except Exception as e:
                    log.warning(f"[mqtt-server] UDP 发送失败: {e}")
                    break
                # 控制发送速率 (~60ms/帧)
                time.sleep(0.06)
            self._publish(json.dumps({"type": "tts", "state": "stop"}))
            log.info(f"[mqtt-server] TTS 推送完成: {text[:30]} ({len(opus_packets)}帧)")
        threading.Thread(target=_send_audio, daemon=True).start()
        return True

    def push_notification(self, text: str):
        """推送纯文字通知（不播音频，仅显示在 ESP32 屏幕上）"""
        self._publish(json.dumps({
            "type": "notification",
            "text": text,
        }))
        log.info(f"[mqtt-server] 通知推送: {text[:30]}")

    def _udp_recv_loop(self):
        """UDP 接收循环 — 接收 ESP32 发来的加密 Opus 音频，VAD 端点检测后走 ASR→LLM→TTS"""
        log.info(f"[mqtt-server] UDP 接收循环启动 (port={self._udp_port})")
        # 端点检测状态
        buf_frames: list[bytes] = []
        speech_count = 0
        silence_count = 0
        utterance_active = False
        hot_frames = 0
        from collections import deque
        tail = deque(maxlen=12)  # 预语音滚动缓冲

        while self._running:
            try:
                data, addr = self._udp_sock.recvfrom(4096)
                if len(data) < UDP_AUDIO_HEADER_SIZE:
                    continue

                with _sessions_lock:
                    session = _sessions.get(self._device_id)
                    if session and not session.get("addr"):
                        session["addr"] = addr
                        log.info(f"[mqtt-server] ESP32 UDP 地址: {addr}")
                    if not session:
                        continue
                    aes_key = session["aes_key"]
                    aes_nonce = session["aes_nonce"]

                    if data[0] != 0x01:
                        continue
                    payload_len = struct.unpack_from("!H", data, 2)[0]
                    timestamp = struct.unpack_from("!I", data, 8)[0]
                    sequence = struct.unpack_from("!I", data, 12)[0]
                    if len(data) != UDP_AUDIO_HEADER_SIZE + payload_len:
                        continue
                    nonce = bytearray(aes_nonce)
                    struct.pack_into("!H", nonce, 2, payload_len)
                    struct.pack_into("!I", nonce, 8, timestamp)
                    struct.pack_into("!I", nonce, 12, sequence)
                    encrypted = data[UDP_AUDIO_HEADER_SIZE:]
                    opus_frame = _aes_ctr_crypt(aes_key, bytes(nonce), encrypted)

                # ── 端点检测（复用 xiaozhi_ws.py 的逻辑）──
                from app.xiaozhi_codec import opus_decode_to_wav
                pcm = opus_decode_to_wav([opus_frame], UPLINK_SAMPLE_RATE)

                # RMS 能量
                import array
                samples = array.array('h', pcm[:len(pcm) - len(pcm) % 2])
                if samples:
                    rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
                else:
                    rms = 0

                # Silero VAD（复用 xiaozhi_ws 的模型，避免重复加载）
                vad_speech = False
                try:
                    from app.xiaozhi_ws import _is_speech_vad, _load_silero_vad
                    vad_model = _load_silero_vad()
                    if vad_model:
                        vad_speech = _is_speech_vad(vad_model, pcm, rms, 0.5)
                    else:
                        vad_speech = rms > 500
                except Exception:
                    vad_speech = rms > 500

                is_hot = vad_speech or rms > 500

                if not utterance_active:
                    # 未开始说话：滚动缓冲 + 热帧计数
                    tail.append(opus_frame)
                    if is_hot:
                        hot_frames += 1
                        if hot_frames >= 3:
                            # 语音开始
                            buf_frames = list(tail)
                            speech_count = 1
                            silence_count = 0
                            utterance_active = True
                            hot_frames = 0
                            log.info("[mqtt-server] speech start (%d tail frames)", len(buf_frames))
                    else:
                        hot_frames = 0
                    continue

                # 说话中：收集帧直到静音
                buf_frames.append(opus_frame)
                if is_hot:
                    speech_count += 1
                    silence_count = 0
                else:
                    silence_count += 1

                silence_limit = SILENCE_FRAMES_VAD
                capped = len(buf_frames) >= MAX_UTTERANCE_FRAMES
                noise_timeout = len(buf_frames) >= NOISE_DROP_FRAMES and speech_count < MIN_SPEECH_FRAMES

                if ((speech_count >= MIN_SPEECH_FRAMES and silence_count >= silence_limit)
                        or capped or noise_timeout):
                    had_speech = speech_count >= MIN_SPEECH_FRAMES
                    frames = list(buf_frames)
                    buf_frames = []
                    speech_count = 0
                    silence_count = 0
                    utterance_active = False
                    session["hot_frames"] = 0

                    if not had_speech:
                        log.info("[mqtt-server] no clear speech, ignoring")
                        continue

                    log.info("[mqtt-server] endpoint: %d frames", len(frames))
                    # 异步处理语音（不阻塞 UDP 接收）
                    threading.Thread(
                        target=self._process_utterance,
                        args=(frames,),
                        daemon=True
                    ).start()

            except OSError:
                if not self._running:
                    break
            except Exception as e:
                log.debug(f"[mqtt-server] UDP 接收异常: {e}")

    def _process_utterance(self, frames: list[bytes]):
        """处理一段完整语音：Opus→WAV→ASR→LLM→TTS→MQTT/UDP 下行"""
        try:
            from app.xiaozhi_codec import opus_decode_to_wav
            from voice_agent import asr, is_low_intent_asr, is_garbled_asr
            from agent.intent import LOW_INTENT_ASR_REPLY, strip_wake_word

            # 1. 解码 Opus → WAV
            wav = opus_decode_to_wav(frames, UPLINK_SAMPLE_RATE)
            if not wav:
                return

            # 2. ASR
            asr_text = asr(wav, "wav")
            asr_text = (asr_text or "").strip()
            if not asr_text or is_garbled_asr(asr_text):
                self._publish_stt("")
                return

            # 剥离唤醒词
            stripped = strip_wake_word(asr_text)
            if stripped:
                asr_text = stripped
            elif stripped == "":
                self._publish_stt("")
                return

            log.info("[mqtt-server] ASR: %s", asr_text)
            self._publish_stt(asr_text)

            # 3. LLM + TTS
            if is_low_intent_asr(asr_text):
                self._push_text_tts(LOW_INTENT_ASR_REPLY)
                return

            # 调用 brain
            import voice_agent
            reply_text, reply_fmt, audio_bytes = voice_agent.voice_loop(wav, "wav")
            if audio_bytes:
                self._push_audio_tts(asr_text, audio_bytes)

        except Exception as e:
            log.error(f"[mqtt-server] 语音处理失败: {e}")
            try:
                self._push_text_tts("语音处理失败了，请再试一次")
            except Exception:
                pass

    def _publish_stt(self, text: str):
        """推送 STT 结果到 ESP32（显示在屏幕上）"""
        self._publish(json.dumps({"type": "stt", "text": text}, ensure_ascii=False))

    def _push_text_tts(self, text: str):
        """纯文字 TTS（使用默认 TTS 引擎生成音频后推送）"""
        try:
            from voice_agent import tts_to_mp3
            mp3 = tts_to_mp3(text)
            if mp3:
                self._push_audio_tts(text, mp3)
        except Exception as e:
            log.warning(f"[mqtt-server] TTS 失败: {e}")

    def _push_audio_tts(self, text: str, mp3_data: bytes):
        """推送 TTS 音频到 ESP32：MQTT 通知 + UDP Opus 帧"""
        try:
            from app.xiaozhi_codec import mp3_to_opus_packets
            opus_packets = mp3_to_opus_packets(mp3_data)
            if not opus_packets:
                return
            self.push_tts(text, opus_packets)
        except Exception as e:
            log.warning(f"[mqtt-server] 推送 TTS 失败: {e}")

    def is_connected(self) -> bool:
        """MQTT 是否已连接且有活跃会话"""
        with _sessions_lock:
            return self._device_id in _sessions

    def stop(self):
        """停止服务"""
        self._running = False
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
        if self._udp_sock:
            self._udp_sock.close()
        with _sessions_lock:
            _sessions.clear()
        log.info("[mqtt-server] 已停止")


# 全局单例
_server: Optional[MqttXiaozhiServer] = None


def get_server() -> Optional[MqttXiaozhiServer]:
    """获取 MQTT 服务端实例"""
    return _server


def init_server(loop: asyncio.AbstractEventLoop) -> bool:
    """初始化 MQTT 服务端（在 FastAPI lifespan 中调用）"""
    global _server
    if _server and _server.is_connected():
        return True
    _server = MqttXiaozhiServer()
    return _server.start(loop)


def push_tts_to_mqtt(text: str, mp3_data: bytes) -> bool:
    """通过 MQTT+UDP 推送 TTS 到 ESP32（供 _push_tts_to_xiaozhi 调用）

    MP3 → Opus → 加密 UDP → ESP32 播放
    """
    if not _server or not _server.is_connected():
        return False
    try:
        from app.xiaozhi_codec import mp3_to_opus_packets
        import asyncio
        packets = mp3_to_opus_packets(mp3_data)
        if not packets:
            log.warning("[mqtt-push] Opus 编码失败")
            return False
        return _server.push_tts(text, packets)
    except Exception as e:
        log.warning(f"[mqtt-push] 推送失败: {e}")
        return False
