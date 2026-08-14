import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from qwen_agent.agents import Assistant
llm_cfg = {'model':'glm-5.2','model_type':'oai','api_base':'https://www.finna.com.cn/v1',
    'api_key':'TEST-API-KEY-PLACEHOLDER','generate_cfg':{'use_raw_api':True}}
tools = [{"mcpServers": {
    "filesystem": {"command":"npx","args":["-y","@modelcontextprotocol/server-filesystem","/Users/sxliuyu/orca/projects/傻妞"]},
    "memory": {"command":"npx","args":["-y","@modelcontextprotocol/server-memory"]}
}}]
bot = Assistant(llm=llm_cfg, name='Charlie',
    system_message='你是Charlie。可用memory工具记住/回忆用户信息，可用filesystem工具读写本地文件。简洁中文。',
    function_list=tools)
qs = [
    "记住：我喜欢喝冰美式咖啡，不喜欢太甜的东西，养了一只猫叫橘子",
    "我喜欢喝什么？我有什么宠物？",
    "帮我看下 /Users/sxliuyu/orca/projects/傻妞 这个目录里有哪些子目录和文件",
]
for q in qs:
    print(f"\n>>> {q}")
    final=None
    for rsp in bot.run([{'role':'user','content':q}]):
        final=rsp
    if final and isinstance(final,list):
        for m in reversed(final):
            if m.get('role')=='assistant' and m.get('content'):
                print(f"白泽: {m['content'][:500]}"); break
