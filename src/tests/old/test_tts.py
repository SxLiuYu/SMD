import os, requests, base64, json
URL = "https://www.finna.com.cn/v1/audio/speech"
KEY = os.getenv("TTS_KEY", "")
text = "你好，我是Charlie，你的全能私人助理。"
# 试几个voice
for voice in ["Cherry", "Ethan", "default", "zh-CN-XiaoxiaoNeural", "alloy"]:
    print(f"\n--- voice={voice} ---")
    r = requests.post(URL, headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"},
        json={"model":"qwen3-tts-flash","input":text,"voice":voice}, stream=True, timeout=30)
    audio=b""; n_delta=0; done=False; err=None
    for line in r.iter_lines():
        if not line: continue
        line=line.decode('utf-8','ignore')
        if line.startswith("data:"):
            try:
                d=json.loads(line[5:].strip())
            except: continue
            t=d.get("type","")
            if "delta" in t and d.get("audio"):
                audio+=base64.b64decode(d["audio"]); n_delta+=1
            elif "done" in t: done=True
            elif "error" in t or "Error" in t: err=d
    print(f"  状态={r.status_code} 音频块={n_delta} 音频字节={len(audio)} done={done} err={err}")
    if audio:
        fn=f"/tmp/tts_{voice}.mp3"
        open(fn,"wb").write(audio)
        print(f"  ✅ 保存 {fn} ({len(audio)}字节)")
        break
