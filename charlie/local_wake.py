"""local_wake: 本地唤醒词检测 — 不依赖浏览器前台

架构:
1. sounddevice 持续捕获麦克风音频 (16kHz mono, 16bit)
2. Vosk 连续识别, 检测 "charlie" 等唤醒词
3. 检测到唤醒词后, 播放提示音, VAD 录制命令音频直到静音
4. 命令音频 → voice_loop() (ASR→brain→TTS) → 扬声器播放

集成点:
- _start_wake_listener() 在 voice_server.py 启动时调用
- wake_callback 接收 WAV bytes, 触发 voice_loop → 播放 TTS
- /api/wake/toggle 端点控制启用/禁用
"""
import os
import io
import json
import time
import wave
import queue
import threading
import logging
import numpy as np

log = logging.getLogger("magic")

# 音频参数
RATE = 16000  # 采样率
CHUNK = 4000  # 每次读取帧数 (250ms @ 16kHz)
CHANNELS = 1

# VAD 参数
VAD_SILENCE_FRAMES = 20      # 连续静音帧数 (250ms/帧, 即 5 秒)
VAD_MAX_RECORD_FRAMES = 60   # 最大录制帧数 (15 秒)
VAD_MIN_SPEECH_FRAMES = 3    # 最少说话帧数 (0.75 秒)
VAD_SPEECH_THRESHOLD = 0.5   # Silero VAD 语音概率阈值
VAD_CHUNK = 512              # Silero VAD 要求的帧大小 (16kHz)

# Silero VAD 模型 (懒加载)
_silero_model = None

def _load_silero_vad():
    global _silero_model
    if _silero_model is not None:
        return _silero_model
    try:
        from silero_vad import load_silero_vad
        _silero_model = load_silero_vad()
        log.info("[wake] Silero VAD 已加载")
        return _silero_model
    except Exception as e:
        log.warning(f"[wake] Silero VAD 加载失败, 降级到能量阈值: {e}")
        return None

def _is_speech(audio_chunk: np.ndarray) -> float:
    """用 Silero VAD 检测是否有语音, 返回语音概率 0~1"""
    model = _load_silero_vad()
    if model is None:
        # 降级: 能量阈值
        energy = np.abs(audio_chunk).mean()
        return 1.0 if energy > 300 else 0.0
    try:
        import torch
        if len(audio_chunk) < VAD_CHUNK:
            audio_chunk = np.pad(audio_chunk, (0, VAD_CHUNK - len(audio_chunk)))
        t = torch.from_numpy(audio_chunk[:VAD_CHUNK].astype(np.float32) / 32768.0)
        return model(t, RATE).item()
    except Exception:
        energy = np.abs(audio_chunk).mean()
        return 1.0 if energy > 300 else 0.0

# 唤醒词列表 (全部转小写匹配)
_WAKE_WORDS = [
    "charlie", "charley", "charls", "charles",
    "chali", "charli", "查理", "查里", "charlie"
]

# 状态
_is_running = False
_is_enabled = True  # 可通过 /api/wake/toggle 切换
_wake_callback = None
_vosk_model = None
_detector_thread = None


def _load_vosk_model():
    """加载 Vosk 英文小模型"""
    global _vosk_model
    if _vosk_model is not None:
        return _vosk_model
    try:
        from vosk import Model
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "web", "vosk", "vosk-model-small-en-us-0.15")
        if not os.path.exists(model_path):
            log.warning(f"[wake] Vosk 模型不存在: {model_path}")
            return None
        _vosk_model = Model(model_path)
        log.info("[wake] Vosk 英文唤醒词模型已加载")
        return _vosk_model
    except Exception as e:
        log.warning(f"[wake] Vosk 模型加载失败: {e}")
        return None


def _play_beep():
    """播放短促提示音 (800Hz 正弦波, 100ms)"""
    try:
        import sounddevice as sd
        duration = 0.1
        t = np.linspace(0, duration, int(RATE * duration), False)
        beep = np.sin(2 * np.pi * 800 * t) * 0.3
        sd.play(beep, RATE)
        sd.wait()
    except Exception:
        pass  # 提示音失败不影响核心功能


def _play_audio(audio_bytes: bytes, interruptible: bool = True) -> bool:
    """播放音频到扬声器, 支持中断检测
    interruptible: 是否允许用户通过说话打断播放
    Returns: True=播放完成, False=被中断
    """
    try:
        import sounddevice as sd
        import soundfile as sf
        data, sr = sf.read(io.BytesIO(audio_bytes))
        if data.ndim > 1:
            data = data[:, 0]
        
        if not interruptible:
            sd.play(data, sr)
            sd.wait()
            log.info(f"[wake] 播放完成: {len(audio_bytes)} 字节")
            return True
        
        # 中断检测: 边播放边监听麦克风
        chunk_size = int(sr * 0.2)  # 200ms 检测间隔
        played = 0
        speech_frames = 0
        
        while played < len(data):
            end = min(played + chunk_size, len(data))
            chunk = data[played:end]
            sd.play(chunk, sr, blocking=False)
            
            # 同时捕获麦克风音频 (检测是否有人在说话)
            try:
                mic_data = sd.rec(chunk_size, samplerate=RATE, channels=1, dtype='int16')
                sd.wait()  # 等待捕获完成
                if mic_data.ndim > 1:
                    mic_data = mic_data[:, 0]
                speech_prob = _is_speech(mic_data)
                if speech_prob > VAD_SPEECH_THRESHOLD:
                    speech_frames += 1
                    if speech_frames >= 3:  # 连续 3 帧 (600ms) 有语音
                        sd.stop()  # 停止播放
                        log.info("[wake] TTS 被用户语音打断 (Silero prob={:.2f})".format(speech_prob))
                        _play_beep()  # 确认听见了
                        return False
                else:
                    speech_frames = 0
            except Exception:
                pass
            
            played += chunk_size
            sd.wait()  # 等待播放完成
        
        log.info(f"[wake] 播放完成: {len(audio_bytes)} 字节")
        return True
    except Exception as e:
        log.warning(f"[wake] 音频播放失败: {e}")
        return True  # 播放失败视为完成


def _record_command() -> bytes | None:
    """录制命令音频: Silero VAD 检测语音边界, 静音后停止, 返回 WAV bytes"""
    try:
        import sounddevice as sd
    except Exception:
        return None

    frames = []
    speech_count = 0
    silence_count = 0

    log.info("[wake] 开始录制命令 (Silero VAD 监听...)")

    with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16',
                        blocksize=CHUNK) as stream:
        while True:
            data, _ = stream.read(CHUNK)
            if data.ndim > 1:
                data = data[:, 0]
            data_bytes = data.tobytes()
            frames.append(data_bytes)

            # Silero VAD 语音检测
            speech_prob = _is_speech(data)

            if speech_prob > VAD_SPEECH_THRESHOLD:
                silence_count = 0
                speech_count += 1
            else:
                silence_count += 1

            # 停止条件: 说话后静音超过阈值, 或超时
            if silence_count >= VAD_SILENCE_FRAMES and speech_count >= VAD_MIN_SPEECH_FRAMES:
                break
            if len(frames) >= VAD_MAX_RECORD_FRAMES:
                break

    if speech_count < VAD_MIN_SPEECH_FRAMES:
        log.info("[wake] 未检测到有效语音, 忽略")
        return None

    # 合并为 WAV
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    wav_bytes = wav_buffer.getvalue()
    log.info(f"[wake] 命令录制完成: {len(wav_bytes)} 字节, {speech_count} 语音帧")
    return wav_bytes


def _listen_loop():
    """持续监听唤醒词的主循环"""
    global _is_running

    model = _load_vosk_model()
    if model is None:
        log.warning("[wake] 无 Vosk 模型, 本地唤醒词不可用")
        return

    from vosk import KaldiRecognizer
    import sounddevice as sd

    rec = KaldiRecognizer(model, RATE)
    rec.SetWords(False)  # 不需要词级别时间戳, 提高速度

    log.info(f"[wake] 本地唤醒词监听已启动 (wake_words={_WAKE_WORDS})")

    with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16',
                        blocksize=CHUNK) as stream:
        _is_running = True
        while _is_running:
            try:
                data, _ = stream.read(CHUNK)
                if data.ndim > 1:
                    data = data[:, 0]

                if not _is_enabled:
                    time.sleep(0.5)
                    continue

                # Vosk 连续识别
                if rec.AcceptWaveform(data.tobytes()):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").lower().strip()
                    if text:
                        for ww in _WAKE_WORDS:
                            if ww in text:
                                log.info(f"[wake] 唤醒词: {text}")
                                _play_beep()
                                wav = _record_command()
                                if wav and _wake_callback:
                                    try:
                                        _wake_callback(wav)
                                    except Exception as e:
                                        log.warning(f"[wake] 回调失败: {e}")
                                break
            except Exception as e:
                log.debug(f"[wake] 监听异常: {e}")
                time.sleep(0.1)

    log.info("[wake] 本地唤醒词监听已停止")


def start_wake_detector(callback):
    """启动唤醒词检测器 (后台线程)
    
    callback: 接收 wav_bytes 参数, 异步处理命令
    """
    global _wake_callback, _detector_thread, _is_running
    _wake_callback = callback
    _detector_thread = threading.Thread(target=_listen_loop, daemon=True)
    _detector_thread.start()
    log.info("[wake] 唤醒词检测器启动")


def stop_wake_detector():
    """停止唤醒词检测器"""
    global _is_running
    _is_running = False
    log.info("[wake] 唤醒词检测器已停止")


def toggle_wake(enabled: bool = None) -> bool:
    """启用/禁用唤醒词检测, 返回当前状态"""
    global _is_enabled
    if enabled is not None:
        _is_enabled = enabled
        log.info(f"[wake] 唤醒词检测 {'启用' if enabled else '禁用'}")
    return _is_enabled


def is_listening() -> bool:
    """返回是否正在监听"""
    return _is_running and _is_enabled


def wake_status() -> dict:
    """返回唤醒词检测器状态"""
    return {
        "running": _is_running,
        "enabled": _is_enabled,
        "model_loaded": _vosk_model is not None,
        "silero_vad": _silero_model is not None,
        "wake_words": _WAKE_WORDS,
        "vad_threshold": VAD_SPEECH_THRESHOLD,
    }
