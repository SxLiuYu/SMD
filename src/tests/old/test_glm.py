import os, sys
# 用 finna 中转 GLM-5.2
llm_cfg = {
    'model': 'glm-5.2',
    'model_type': 'oai',
    'api_base': 'https://www.finna.com.cn/v1',
    'api_key': 'TEST-API-KEY-PLACEHOLDER',
}

from qwen_agent.llm import get_chat_model
llm = get_chat_model(llm_cfg)
print("=== LLM实例:", type(llm).__name__, "model=", llm.model)

# 测试1: 纯对话
print("\n=== 测试1: 纯对话 ===")
try:
    rsp = llm.chat(messages=[{'role':'user','content':'你好，用一句话介绍你自己'}], stream=False)
    for m in rsp:
        print("回复:", m[0]['content'][:200] if isinstance(m,list) and m else m)
        break
except Exception as e:
    print("纯对话失败:", type(e).__name__, str(e)[:300])
