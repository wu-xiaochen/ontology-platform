# Clawra Engine

!!! quote "Clawra 是什么？"
    **让 AI 从文本中学习规则，而不是你替它写。**

Clawra 是一个**神经符号融合的自主进化 AI Agent 框架**。它能从自然语言文本中自动提取结构化知识（实体、关系、约束），存入知识图谱供符号逻辑引擎严格推理——从根本上解决 LLM 幻觉和 Prompt 维护地狱的问题。

---

## 为什么选 Clawra？

### 对比 LangChain/LangGraph

| | LangChain | Clawra |
|--|-----------|--------|
| 规则来源 | 手动写 Prompt | **AI 从文本自动学习** |
| 幻觉防护 | Prompt 提醒 | **符号逻辑拦截** |
| 推理方式 | 概率性 LLM | **确定性符号逻辑** |
| 自我进化 | 静态 | **8 阶段进化闭环** |
| 依赖 | 强依赖 LangChain | **零外部依赖** |

### 核心能力

- 🧠 **自主规则学习** — 给文本，AI 自动提取知识存入知识图谱
- 🔗 **神经符号融合** — LLM 负责语义理解，符号逻辑负责精确推理
- 🔄 **8 阶段进化闭环** — AI 从错误中自主学习，持续进化
- 🛡️ **符号逻辑硬拦截** — 关键决策不被幻觉污染
- 📊 **GraphRAG 混合检索** — 向量 + 知识图谱双通道
- 🤖 **MCP Server** — 3 行配置接入 Claude Code

---

## 快速开始

```bash
git clone https://github.com/wu-xiaochen/clawra-engine.git
cd clawra-engine
pip install -e .
python examples/demo_basic.py
```

**无需 API Key** — Demo 使用本地模拟 LLM。

---

## 5 行代码体验

```python
from clawra import Clawra

clawra = Clawra()

# 给文本，AI 自动学习规则
clawra.learn("""
燃气调压箱出口压力不得超过 0.4MPa。
超过 0.35MPa 时触发紧急截断。
""")

# 严格推理，自动拦截违规答案
result = clawra.reason("调压箱最大安全压力是多少？")
# → Clawra 物理拦截 pressure = 0.8MPa 的建议
```

---

## 项目状态

- **版本**: 4.2.0-alpha
- **测试**: 433 个测试全部通过
- **许可**: MIT
- **语言**: Python 3.10+

[:fontawesome-brands-github: GitHub](https://github.com/wu-xiaochen/clawra-engine){ .md-button .md-button--primary }
[:fontawesome-brands-discord: Discord](https://discord.gg/your-server){ .md-button }
