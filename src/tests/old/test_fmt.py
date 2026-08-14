import os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from qwen_agent.llm import get_chat_model

llm_cfg = {
    'model': 'glm-5.2',
    'model_type': 'oai',
    'api_base': 'https://www.finna.com.cn/v1',
    'api_key': 'TEST-API-KEY-PLACEHOLDER',
}
llm = get_chat_model(llm_cfg)

# 直接测 OpenAI 原生 tool_calls（看finna GLM-5.2是否支持结构化工具调用）
import openai
client = openai.OpenAI(base_url='https://www.finna.com.cn/v1', api_key='TEST-API-KEY-PLACEHOLDER')
tools_api = [{
    "type":"function",
    "function":{
        "name":"search_charging_stations",
        "description":"搜索附近的充电桩",
        "parameters":{"type":"object","properties":{"city":{"type":"string","description":"城市"},"count":{"type":"integer","description":"数量"}},"required":[]}
    }
}]
print("=== 测试 finna GLM-5.2 原生 OpenAI tool_calls ===")
try:
    r = client.chat.completions.create(
        model='glm-5.2',
        messages=[{'role':'user','content':'帮我搜下北京附近的充电桩'}],
        tools=tools_api,
        stream=False,
    )
    msg = r.choices[0].message
    print("content:", repr(msg.content)[:200])
    print("tool_calls:", json.dumps([tc.model_dump() for tc in (msg.tool_calls or [])], ensure_ascii=False, indent=2)[:600])
except Exception as e:
    print("原生tool调用失败:", type(e).__name__, str(e)[:300])
