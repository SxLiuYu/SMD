import os
os.environ['DASHSCOPE_API_KEY'] = "TEST-DASHSCOPE-KEY-PLACEHOLDER"
from qwen_agent.agents import Assistant

# Qwen-Audio: 音频理解模型（能"听"音频内容）
llm_cfg = {'model_type': 'qwenaudio_dashscope', 'model': 'qwen-audio-turbo-latest'}
bot = Assistant(llm=llm_cfg, system_message='你听音频并回答问题，用中文。')

audio_url = 'https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3'
messages = [{'role':'user','content':[{'audio':audio_url},{'text':'这段音频在说什么？用一句话总结'}]}]
print("=== 测试 Qwen-Audio 音频理解 ===")
print("音频:", audio_url)
try:
    final=None
    for rsp in bot.run(messages):
        final=rsp
    if final and isinstance(final,list):
        for m in final:
            if m.get('role')=='assistant' and m.get('content'):
                print("Qwen-Audio:", m['content'][:300])
except Exception as e:
    print("失败:", type(e).__name__, str(e)[:300])
