# 🧠 Clawra: 自主进化本体认知引擎

> **元学习 × 知识图谱 × 神经符号融合** — 让 AI 真正自主进化，告别硬编码规则

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/wu-xiaochen/ontology-platform/blob/main/LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Active-green.svg)](https://neo4j.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Embedded-purple.svg)](https://www.trychroma.com/)
[![GitHub Stars](https://img.shields.io/github/stars/wu-xiaochen/ontology-platform?style=social)](https://github.com/wu-xiaochen/ontology-platform/stargazers)

---

## 🎯 这是什么？

**Clawra** 是一款具备**自主进化能力**的神经符号认知代理框架。它突破了传统 Agent 需要人工编写规则的限制，通过**零硬编码**的元学习架构，实现真正的自主学习、自我进化、持续成长。

> "传统 Agent 是程序员写好的剧本，Clawra 是能自己编写剧本的 AI"

---

## ✨ 核心能力一览

| 能力 | 说明 | 状态 |
|------|------|------|
| 🧠 **自主规则学习** | 从文本自动提取规则，无需人工编写 | ✅ 已实现 |
| 🔄 **领域自适应** | 自动识别领域，动态加载逻辑 | ✅ 已实现 |
| 📊 **规则发现** | 从数据中归纳规则，支持关联挖掘 | ✅ 已实现 |
| 🎯 **统一逻辑表达** | 规则/行为/策略统一表达 | ✅ 已实现 |
| 🔍 **GraphRAG** | 向量+图谱混合检索，增强上下文 | ✅ 已实现 |
| 🛡️ **SafeMath 沙盒** | AST 级数学沙盒，阻断 DoS/OOM 攻击 | ✅ 已实现 |
| ⚡ **异步 ReAct** | 纯异步非阻塞调用，并发毫秒级响应 | ✅ 已实现 |
| 🧩 **神经符号融合** | 大模型语义 + 符号逻辑双重保障 | ✅ 已实现 |

---

## 📊 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     Meta Learner (元学习层)                       │
│              学习如何学习 · 领域自适应 · 策略优化                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
│  Unified Logic  │ │ Rule Discovery│ │  Self Evaluator │
│     Layer       │ │    Engine     │ │                 │
│  统一逻辑表达层   │ │   规则发现引擎  │ │   自我评估器     │
├─────────────────┤ ├───────────────┤ ├─────────────────┤
│ • 规则 (Rule)   │ │ • 关联规则挖掘 │ │ • 学习质量评估   │
│ • 行为 (Behavior)│ │ • 归纳学习    │ │ • 规则效果验证   │
│ • 策略 (Policy) │ │ • 冲突检测    │ │ • 反馈优化      │
│ • 约束 (Constraint)│ │ • 规则评估   │ │ • 进化闭环      │
└─────────────────┘ └───────────────┘ └─────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
│    Reasoner     │ │    Memory     │ │  Perception     │
│    推理引擎      │ │    记忆系统    │ │   感知提取层     │
├─────────────────┤ ├───────────────┤ ├─────────────────┤
│ • 前向链推理    │ │ • Neo4j 图谱  │ │ • LLM 知识提取   │
│ • 后向链推理    │ │ • ChromaDB   │ │ • 结构化抽取     │
│ • 混合推理      │ │ • 向量检索    │ │ • 语义分块       │
│ • 置信度传播    │ │ • 时序记忆    │ │ • 实体识别       │
└─────────────────┘ └───────────────┘ └─────────────────┘
```

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/wu-xiaochen/ontology-platform.git
cd ontology-platform
pip install -r requirements.txt
```

### 编写你的第一个自主进化 Agent

```python
from src.clawra import Clawra

# 初始化 — 不需要任何规则配置
agent = Clawra(enable_memory=False)

# 注入领域知识，框架自动学习规则
result = agent.learn(
    "燃气调压箱的出口压力必须 ≤ 0.4MPa，否则有爆炸风险"
)

# 查询学到了什么
print(f"发现 {len(result['learned_patterns'])} 个规则")
print(f"领域: {result['domain']}")
# → 发现 3 个规则, 领域: gas_safety
```

---

## 🎬 核心能力演示

```
==============================================================
🤖 Clawra 自主进化智能体框架 - 核心能力演示
==============================================================

[核心优势 1] 元学习：非结构化知识 → 结构化图谱
▶ 注入: "燃气调压箱的出口压力必须 ≤ 0.4MPa，否则有爆炸风险"
▶ 引擎自动分析文本规律...
  ✓ 判别业务域: [gas_safety]
  ✓ 自动归纳图谱结构:
     => (GasRegulator) -[hasSafetyConstraint]-> (pressure ≤ 0.4MPa)
     => (GasRegulator) -[riskLevel]-> (HIGH)
     => (pressure) -[unit]-> (MPa)

[核心优势 2] SafeMath 沙盒：阻断恶意计算
▶ 测试: 99999 ** 9999 (LLM 幻觉产生的指数攻击)
  🛡️ 沙盒拦截: 表达式复杂度超过限制 (max_ops=1000)
  ✓ 服务底层永远不会因 CPU/内存被打满而锁死

[核心优势 3] 规则引擎：符号逻辑守卫
▶ 注册硬性规则: outlet_pressure ∈ [0.002, 0.4] MPa
▶ LLM 建议: pressure = 0.8 MPa (幻觉!)
  🚫 物理阻断: FAIL — 超出工程安全范围!
  ✓ 大模型幻觉被符号逻辑成功拦截

==============================================================
🎉 演示结束 — Clawra 已具备企业级安全防护能力
==============================================================
```

### Web 界面演示

```bash
PYTHONPATH=. streamlit run examples/web_capability_demo.py --server.port 8501
```

---

## 🆚 对比传统 Agent 框架

| 特性 | 传统 Agent (LangChain等) | **Clawra ( ours)** |
|------|--------------------------|-------------------|
| 规则来源 | 人工编写 hardcode | **自主学习生成** |
| 领域适应 | 提示词工程 | **自动识别+动态加载** |
| 知识检索 | 纯向量检索 (RAG) | **GraphRAG 混合检索** |
| LLM 幻觉防护 | 无 | **符号逻辑双重验证** |
| 计算安全 | 无保护 | **SafeMath 沙盒隔离** |
| 自我进化 | 静态 | **持续学习迭代** |
| 架构复杂度 | 高 (依赖外部组件) | **轻量内置** |

> **核心差异**: 传统 Agent 是"人工规则+概率推理"，Clawra 是"自主学习+符号逻辑双引擎"

---

## 📦 项目结构

```
ontology-platform/
├── src/
│   ├── clawra.py              # 🧠 核心入口
│   ├── agents/                # 认知编排层
│   │   ├── orchestrator.py   # ReAct 编排器
│   │   └── metacognition.py  # 元认知
│   ├── core/
│   │   ├── reasoner.py       # 神经符号推理
│   │   ├── rule_engine.py    # AST 规则引擎
│   │   └── ontology/         # 本体管理
│   ├── evolution/             # ⭐ 自主进化层
│   │   ├── unified_logic.py  # 统一逻辑表达
│   │   ├── meta_learner.py   # 元学习器
│   │   └── rule_discovery.py # 规则发现
│   ├── memory/                # 记忆存储
│   │   ├── neo4j_adapter.py  # 图谱存储
│   │   └── vector_adapter.py # 向量存储
│   └── perception/            # 感知提取
│       └── extractor.py      # LLM 知识抽取
├── examples/                  # 示例代码
│   ├── demo_clawra_e2e.py    # E2E 演示
│   └── web_capability_demo.py # Web 演示
└── tests/                     # 测试套件
```

---

## 🌟 为什么给这个项目 Star？

```
┌─────────────────────────────────────────────────────┐
│  如果你认同以下观点，这个项目值得你的 Star ⭐         │
└─────────────────────────────────────────────────────┘
```

1. **🔓 告别硬编码**: 不想再为每个新领域手写 thousands of if-else 规则
2. **🛡️ 安全第一**: 需要企业级 LLM 应用，同时必须防止幻觉和 DoS 攻击
3. **📈 持续进化**: 希望 AI 能够从生产环境数据中持续学习和改进
4. **🧠 认知架构**: 对"自主学习+符号推理"的神经符号融合感兴趣
5. **⚡ 性能敏感**: 需要异步非阻塞的高并发架构

---

## 🗺️ 路线图

### 已完成 ✅
- [x] 自主进化架构（零硬编码规则学习）
- [x] 领域自适应机制
- [x] 统一逻辑表达层
- [x] 规则发现引擎
- [x] GraphRAG 混合检索
- [x] SafeMath 安全沙盒
- [x] 多 LLM 支持 (OpenAI/VolcEngine)

### 进行中 🚧
- [ ] 多模态知识抽取（图文）
- [ ] 分布式知识图谱
- [ ] 联邦式本体协作

### 规划中 📋
- [ ] 强化学习策略优化
- [ ] 自动超参数调优
- [ ] 可视化规则编辑器

---

## 👥 贡献者

[![GitHub Contributors](https://img.shields.io/github/contributors/wu-xiaochen/ontology-platform)](https://github.com/wu-xiaochen/ontology-platform/graphs/contributors)

欢迎提交 Issue 和 Pull Request！请查阅 [开发规范](docs/development/CONTRIBUTING.md)。

---

## 📖 文档

| 文档 | 路径 |
|------|------|
| API 参考 | [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md) |
| 架构设计 | [docs/architecture/architecture.md](docs/architecture/architecture.md) |
| 开发规范 | [docs/development/CONTRIBUTING.md](docs/development/CONTRIBUTING.md) |
| Agent 指南 | [docs/guides/AGENT_GUIDE.md](docs/guides/AGENT_GUIDE.md) |

---

<p align="center">
  <strong>Apache 2.0 License</strong> · Made with 🧠 by the community
</p>
