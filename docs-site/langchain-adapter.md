# LangChain 适配器

## 5 个工具

Clawra LangChain 适配器提供 5 个完整的 LangChain Tools：

| 工具 | 功能 |
|------|------|
| `clawra_learn` | 从文本学习知识 |
| `clawra_reasoning` | 严格逻辑推理 |
| `clawra_retrieve` | GraphRAG 混合检索 |
| `clawra_evolve` | 触发 8 阶段进化 |
| `clawra_stats` | 获取系统状态 |

## 快速使用

```python
from langchain.agents import AgentType, initialize_agent
from langchain.chat_models import ChatOpenAI
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
result = agent.run("""
    用 Clawra 学习天然气管道安全规范：
    - 最大允许压力 0.4MPa
    - 超过 0.35MPa 触发警报

    然后回答：如果压力是 0.5MPa，安全吗？
""")
```

## 单独使用某个工具

```python
from clawra.sdk.adapters.langchain import get_clawra_tools_dict

tools = get_clawra_tools_dict()

# 学习
tools['clawra_learn'].run({
    "text": "猫是哺乳动物",
    "domain": "biology"
})

# 推理
result = tools['clawra_reasoning'].run({
    "query": "猫有什么特征？"
})

# 统计
stats = tools['clawra_stats'].run({})
```

## Pydantic Schema

每个工具都有完整的 Pydantic 输入验证：

```python
from clawra.sdk.adapters.langchain import ClawraLearnInput

# 输入自动验证
input_data = ClawraLearnInput(
    text="猫是哺乳动物",
    domain="biology"  # 可选
)
```
