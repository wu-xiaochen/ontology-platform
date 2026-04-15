# 知乎/掘金 发布指南

## 知乎文章

**标题：** 我用 LangChain 两年后，决定自己写一个 AI Agent 框架

**正文：**

---

用 LangChain 两年后，我决定自己写一个框架。

不是因为我多厉害。是因为我实在受不了了。

**LangChain 解决的是编排问题，但它把最难的部分留给了开发者：知识。**

每加一条规则，你就在 prompt 里多加一段。6 个月后，你的 prompt 变成了 2000 行。偶尔能跑，但说不清哪个规则和哪个冲突，一调就崩。

我后来想明白了一件事：**prompt engineering 本质上是在用错误的方式解决正确的问题。**

规则是结构化的、确定性的知识。prompt 是非结构化的、概率性的表达。把前者塞进后者，就像把钢管塞进果冻——不是不行，但肯定不对。

所以我写了 Clawra。

**核心理念很简单：让 AI 从文本里自己学规则，而不是你替它写。**

比如，你给它一段工业燃气设备的安全文档：

```python
from clawra import Clawra

clawra = Clawra()
clawra.learn("""
根据 GB 12350-2009，燃气调压箱必须：
- 出口压力不得超过 0.4MPa
- 超过 0.35MPa 时触发紧急截断
- 每 12 个月检修一次
""")

result = clawra.orchestrate("这个调压箱的最大安全压力是多少？")
```

Clawra 会自动：
1. 提取实体：燃气调压箱、0.4MPa、0.35MPa、紧急截断
2. 提取约束：pressure ≤ 0.4MPa、trigger_at ≥ 0.35MPa
3. 注册为**硬性规则**进入符号推理引擎
4. 生成**双向验证链**

当 LLM 建议 pressure = 0.8MPa，Clawra 直接用形式逻辑把它拦下来。不是 prompt 提醒，是数学证明级别的拦截。

**这叫神经符号融合** — LLM 负责语义理解，符号逻辑负责精确推理，各用所长。

它还有一个 8 阶段进化闭环：

```
感知 → 学习 → 推理 → 执行 → 评估 → 漂移检测 → 规则修订 → 知识更新
 ↑__________________________________________________|
                    (从错误中学习)
```

每犯一次错，它就更新自己的规则集。这不是一次性的流水线，是个**活着的系统**。

**10 个可运行的 Demo，433 个测试，MIT 协议：**

```bash
git clone https://github.com/wu-xiaochen/clawra-engine.git
cd clawra-engine
pip install -e .
python examples/demo_basic.py  # 无需 API Key
```

还有 MCP Server，可以直接给 Claude Code 用，3 行配置：

```json
{
    "mcpServers": {
        "clawra": {
            "command": "python",
            "args": ["-m", "clawra.mcp.server"]
        }
    }
}
```

我当然不是说 LangChain 不好。它是很好的工具。**但如果你在生产环境里被 prompt 维护折磨过，你会懂我在说什么。**

GitHub：https://github.com/wu-xiaochen/clawra-engine

---

**标签：** AI / LangChain / 机器学习 / Python / 大模型

---

## 掘金文章

**标题：** 从痛点到架构：为什么我放弃了 LangChain，写了自己的 AI Agent 框架

**正文：**

---

## 背景：LangChain 哪里好，哪里不够好

LangChain 的编排能力是真的强。Chain、Agent、Tool — 这套抽象让复杂的 AI 工作流变得可管理。两年用下来，我对这部分是很认可的。

但有一个问题始终困扰我：**知识管理**。

LangChain 里，知识 = prompt 里的一段文字。

每来一个新领域，你要写新的 prompt。每加一条约束，你要改 prompt。规则多了，prompt 长了，互相冲突了，调试成本指数上升。

这不是工程能力问题。这是**架构问题**。

---

## Clawra 的设计思路

Clawra 的核心设计假设是：**规则应该用结构化的方式存储，用形式化的方式执行。**

不是塞在 prompt 里等 LLM "记住"，而是：
1. 从文本中提取 → 存入知识图谱
2. 用符号逻辑引擎 → 严格推理
3. LLM 负责理解 → 逻辑层负责执行

一个具体例子：

```python
# 传统方式：写 prompt
system_prompt = """
当讨论燃气压力时：
- 禁止推荐超过 0.4MPa 的压力值
- 超过 0.35MPa 必须警告爆炸风险
...
"""

# Clawra 方式：给文本
clawra.learn("燃气调压箱出口压力不得超过 0.4MPa，超压有爆炸风险")

# Clawra 自动：
# - 提取实体：调压箱、出口压力、0.4MPa、爆炸风险
# - 提取约束：pressure ≤ 0.4MPa
# - 注册为硬性规则
# - 生成反向验证链

# LLM 建议 pressure = 0.8MPa → Clawra 直接拦截
```

---

## 技术架构

```
┌──────────────────────────────────────────────┐
│              Meta Learner (元学习层)            │
│     学习如何学习 · 从错误中进化 · 策略自适应       │
└────────────────────┬───────────────────────┘
                      │
       ┌──────────────┼──────────────────┐
       ▼              ▼                  ▼
┌────────────┐  ┌─────────────┐  ┌────────────┐
│  Unified   │  │    Rule    │  │    Self   │
│ Logic Layer│  │  Discovery │  │ Evaluator │
│ (Rule/Behav│  │ (自动提取)   │  │ (质量评估) │
└─────┬──────┘  └──────┬──────┘  └──────┬─────┘
      │                │                 │
      └────────────────┼─────────────────┘
                       │
       ┌────────────────┼────────────────┐
       ▼                ▼                 ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│  Reasoner  │  │   Memory   │  │ Perception │
│ (前向/后向链│  │(Neo4j+向量)│  │ (LLM提取)  │
└────────────┘  └────────────┘  └────────────┘
```

---

## 与 LangChain 对比

| 能力 | LangChain | Clawra |
|------|-----------|--------|
| 规则来源 | Prompt 手写 | **AI 从文本自动学习** |
| 幻觉防护 | Prompt 提醒 | **符号逻辑拦截** |
| 数学安全 | 无 | **AST 沙盒** |
| 知识检索 | 纯向量 RAG | **GraphRAG 混合** |
| 自我进化 | 静态 | **8 阶段闭环** |
| 架构 | 依赖 LangChain | **无外部依赖** |

---

## 快速开始

```bash
git clone https://github.com/wu-xiaochen/clawra-engine.git
cd clawra-engine
pip install -e .
python examples/demo_basic.py  # 无需 API Key
```

**10 个完整 Demo，433 个测试，MIT 许可。**

---

## 适合谁

Clawra 不是银弹。如果你需要快速原型，LangChain 仍然是最好的起点。

但如果你是**生产级 AI 系统**，且满足以下任一条件：
- 规则高频变更（合规、监管、政策）
- 领域专业知识要求高（医疗、法律、工业）
- 安全要求严格（关键决策零幻觉）
- AI 需要持续进化（不只是加 prompt）

那 Clawra 值得一试。

---

GitHub: https://github.com/wu-xiaochen/clawra-engine
