#!/usr/bin/env python3
"""
Clawra LangChain Adapter - Demo

展示如何将 Clawra 作为 LangChain Agent 的工具集。

运行:
    cd /Users/xiaochenwu/Desktop/ontology-platform
    python examples/demo_langchain_adapter.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sdk.adapters.langchain import get_clawra_tools, get_clawra_tools_dict


def demo_tools_list():
    """展示所有 Clawra Tools"""
    print("=" * 60)
    print("🧠 Clawra LangChain Adapter - 工具列表")
    print("=" * 60)

    tools = get_clawra_tools()
    print(f"\n共 {len(tools)} 个工具:\n")

    for i, tool in enumerate(tools, 1):
        print(f"{i}. 【{tool.name}】")
        print(f"   描述: {tool.description}")
        print()


def demo_individual_tool(name: str = "clawra_stats"):
    """演示单个工具"""
    print("=" * 60)
    print(f"🔧 演示工具: {name}")
    print("=" * 60)

    tools_dict = get_clawra_tools_dict()
    tool = tools_dict[name]

    # 同步执行（LangChain tools 需要传入空字典或空字符串）
    print(f"\n执行 {tool.name}...\n")
    try:
        result = tool.run({})  # 无参数工具用空字典
    except TypeError:
        result = tool._run()  # fallback 直接调用

    print(f"结果:\n{result}")


def demo_learn_and_reason():
    """演示: 学习 + 推理的组合使用"""
    print("=" * 60)
    print("🔄 演示: Learn → Reasoning 组合")
    print("=" * 60)

    tools_dict = get_clawra_tools_dict()

    # Step 1: 学习知识
    print("\n[Step 1] 使用 clawra_learn 学习领域知识...")
    learn_tool = tools_dict["clawra_learn"]
    learn_result = learn_tool.run({
        "text": "燃气调压箱的出口压力不得超过 0.4MPa，超过 0.35MPa 时应触发紧急截断。"
        "调压箱是城市燃气输配系统的核心设备。"
    })
    print(f"学习结果:\n{learn_result}")

    # Step 2: 推理
    print("\n[Step 2] 使用 clawra_reasoning 推理...")
    reason_tool = tools_dict["clawra_reasoning"]
    reason_result = reason_tool.run({
        "query": "调压箱的最大安全压力是多少？"
    })
    print(f"推理结果:\n{reason_result}")


def demo_usage_in_langchain_agent():
    """展示在 LangChain Agent 中使用的代码模板"""
    print("=" * 60)
    print("📦 LangChain Agent 集成示例代码")
    print("=" * 60)

    code = '''
# ============================================================
# Clawra + LangChain Agent 集成示例
# ============================================================

from langchain.agents import AgentType, initialize_agent
from langchain.chat_models import ChatOpenAI  # 或其他 LLM
from clawra.sdk.adapters.langchain import get_clawra_tools

# 1. 初始化 LLM
llm = ChatOpenAI(temperature=0, model="gpt-4")

# 2. 获取 Clawra 工具
clawra_tools = get_clawra_tools()

# 3. 初始化 Agent
agent = initialize_agent(
    tools=clawra_tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# 4. 运行
result = agent.run(
    """
    首先用 Clawra 学习天然气管道的安全规范：
    - 最大允许压力 0.4MPa
    - 超过 0.35MPa 触发警报
    - 每季度检修一次

    然后回答：如果管道当前压力是 0.5MPa，安全吗？
    """
)

print(result)
# ============================================================
'''
    print(code)


if __name__ == "__main__":
    print("\n🧠 Clawra LangChain Adapter Demo\n")

    # 1. 列出所有工具
    demo_tools_list()

    # 2. 演示单个工具
    demo_individual_tool("clawra_stats")

    # 3. 演示 learn + reason 组合
    demo_learn_and_reason()

    # 4. 展示 LangChain Agent 集成代码
    demo_usage_in_langchain_agent()

    print("\n✅ Demo 完成!")
    print("""
下一步:
1. 安装 langchain: pip install langchain
2. 设置 OPENAI_API_KEY
3. 运行上面的示例代码
""")
