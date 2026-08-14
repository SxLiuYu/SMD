import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
VENV_PY = "/Users/sxliuyu/orca/projects/傻妞/qwen-agent/.venv/bin/python"

from qwen_agent.agents import Assistant

llm_cfg = {
    'model': 'glm-5.2',
    'model_type': 'oai',
    'api_base': 'https://www.finna.com.cn/v1',
    'api_key': 'TEST-API-KEY-PLACEHOLDER',
    'generate_cfg': {'use_raw_api': True},
}

# 原生MCP服务器配置（标准mcpServers格式）
tools = [{
    "mcpServers": {
        "magic-phone": {
            "command": VENV_PY,
            "args": ["mcp_server.py"],
            "cwd": os.getcwd()
        }
    }
}]

bot = Assistant(
    llm=llm_cfg,
    name='Charlie',
    description='全能私人助理',
    system_message='你是Charlie，中国版Jarvis。用户说话你就能调用工具完成任务。回复简洁中文。',
    function_list=tools,
)

print("="*50)
print("测试: 通过MCP协议调用工具")
print("="*50)
queries = [
    "现在几点了？",
    "帮我搜下北京附近的充电桩",
    "我要出门了，帮我把特斯拉空调开起来，设到24度",
]
for q in queries:
    print(f"\n>>> 用户: {q}")
    messages = [{'role':'user','content':q}]
    final = None
    try:
        for rsp in bot.run(messages):
            final = rsp
            # 打印中间工具调用
            if isinstance(rsp, list):
                for m in rsp:
                    if m.get('role') == 'assistant' and m.get('content'):
                        c = str(m['content'])
                        if 'tool_call' in c.lower() or 'function' in c.lower() or len(c) < 200:
                            print(f"   [工具调用] {c[:150]}")
        # 最终回复
        if final and isinstance(final, list):
            for m in final:
                if m.get('role') == 'assistant' and m.get('content'):
                    print(f"   白泽: {m['content'][:300]}")
    except Exception as e:
        print(f"   异常: {type(e).__name__}: {str(e)[:200]}")
