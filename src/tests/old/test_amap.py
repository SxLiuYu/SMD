import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from qwen_agent.agents import Assistant

llm_cfg = {
    'model':'glm-5.2','model_type':'oai',
    'api_base':'https://www.finna.com.cn/v1','api_key':'TEST-API-KEY-PLACEHOLDER',
    'generate_cfg': {'use_raw_api': True},
}
# 真实高德地图MCP（用你的key）
tools = [{"mcpServers": {
    "amap-maps": {
        "command": "npx",
        "args": ["-y", "@amap/amap-maps-mcp-server"],
        "env": {"AMAP_MAPS_API_KEY": "your-amap-key-here"}
    }
}}]
bot = Assistant(llm=llm_cfg, name='Charlie',
    system_message='你是Charlie，用高德地图MCP工具回答地图天气出行问题，简洁中文。',
    function_list=tools)
print("="*50)
for q in ["北京现在天气怎么样？", "望京附近有什么咖啡店？"]:
    print(f"\n>>> {q}")
    final=None
    for rsp in bot.run([{'role':'user','content':q}]):
        final=rsp
    if final and isinstance(final,list):
        for m in reversed(final):
            if m.get('role')=='assistant' and m.get('content'):
                print(f"白泽: {m['content'][:400]}"); break
