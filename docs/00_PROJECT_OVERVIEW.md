# Clawra 项目总览

> 快速了解 Clawra 是什么、解决什么问题、核心优势、以及如何参与贡献。

---

## 1. Clawra 是什么

**Clawra**（Cognitive Learning Agent With Self-Evolving Architecture）是一款具备**自主进化能力**的神经符号认知引擎。它让 AI 真正能够从数据中学习规则、从错误中自我纠错、在持续运行中不断变强——而不是依赖人工编写 thousands of if-else 规则。

> "传统 Agent 是程序员写好的剧本，Clawra 是能自己编写剧本的 AI"

---

## 2. 解决什么问题

### 2.1 传统 Agent 的困境

| 问题 | 传统方案 | Clawra 方案 |
|-----|---------|-------------|
| 规则需要人工编写 | 提示词工程师手写 thousands of rules | **自主从文本/数据中发现规则** |
| 领域适应困难 | 每个领域重新训练 | **自动识别领域 + 动态加载逻辑** |
| 知识检索不精准 | 纯向量 RAG（chunk-level） | **GraphRAG 混合检索**（实体关系图谱） |
| LLM 幻觉无法防护 | 无解 | **符号逻辑双重验证** |
| 计算安全无保护 | 无解 | **SafeMath 沙盒隔离** |
| 自我进化能力 | 静态，一次训练终身使用 | **持续学习迭代** |

### 2.2 核心痛点

- **规则维护成本高**：每新增一个业务场景就需要专家编写大量规则
- **知识遗忘**：上下文窗口有限，长期记忆缺失
- **推理不可解释**：只返回结果，不告诉为什么
- **无法自我纠错**：错误发生只能人工介入

---

## 3. 核心能力

### 3.1 四大核心能力

| 能力 | 说明 | 技术实现 |
|-----|------|---------|
| 🧠 **自主规则学习** | 从文本自动提取规则，无需人工编写 | MetaLearner + LLM 知识抽取 |
| 🔄 **领域自适应** | 自动识别领域，动态加载相关逻辑 | 领域检测 + 模式索引 |
| 📊 **规则发现** | 从数据中归纳规则，支持关联挖掘 | RuleDiscovery Engine |
| 🎯 **统一逻辑表达** | 规则/行为/策略统一表达 | UnifiedLogic Layer |

### 3.2 其他关键特性

- **GraphRAG 混合检索**：向量 + 图谱双重召回
- **SafeMath 沙盒**：AST 级数学执行，阻断 DoS/OOM
- **神经符号融合**：LLM 语义 + 符号逻辑双重保障
- **异步 ReAct**：纯异步非阻塞调用
- **多 LLM 支持**：OpenAI / Volcano Engine / 本地模型

---

## 4. 技术架构

### 4.1 架构概览图

```
┌───────────────────────────────────────────────────────┐
│                    应用层 (Application)                │
│  Streamlit Demo  │  FastAPI  │  CLI  │  SDK          │
├───────────────────────────────────────────────────────┤
│                  编排层 (Orchestration)               │
│  CognitiveOrchestrator  │  Metacognition  │  Auditor  │
├───────────────────────────────────────────────────────┤
│               进化层 (Evolution Layer) ⭐              │
│  MetaLearner  │  UnifiedLogic  │  RuleDiscovery       │
│  SelfEvaluator  │  SelfCorrection  │  SkillDistiller   │
├───────────────────────────────────────────────────────┤
│                  认知层 (Cognition Layer)             │
│  Reasoner  │  RuleEngine  │  Ontology Manager       │
├───────────────────────────────────────────────────────┤
│                  记忆层 (Memory Layer)                 │
│  Neo4j  │  ChromaDB  │  Episodic Memory (SQLite)    │
├───────────────────────────────────────────────────────┤
│                  感知层 (Perception Layer)             │
│  Extractor  │  GlossaryEngine  │  ChunkingEngine     │
└───────────────────────────────────────────────────────┘
```

### 4.2 自主进化闭环

```
  ┌─────────────────────────────────────────────────────┐
  │                   进化闭环 (Evolution Loop)         │
  │                                                     │
  │   ┌──────────┐    ┌──────────┐    ┌──────────┐   │
  │   │   感知   │───▶│  学习    │───▶│  推理    │   │
  │   └──────────┘    └──────────┘    └──────────┘   │
  │        ▲                              │           │
  │        │         ┌──────────┐        │           │
  │        └─────────│  评估    │◀───────┘           │
  │                  └──────────┘                     │
  │                      │ ▲                          │
  │                      ▼ │                          │
  │                  ┌──────────┐                    │
  │                  │  纠错    │                    │
  │                  └──────────┘                    │
  └─────────────────────────────────────────────────────┘
```

---

## 5. 适用场景

### 5.1 最佳适用场景

| 场景 | 说明 | 典型客户 |
|-----|------|---------|
| 🏭 **工业知识管理** | 燃气/电力/制造设备知识图谱 + 安全规则 | 能源企业、工业集团 |
| 💼 **企业采购风控** | 供应商评估规则 + 合同合规检查 | 新奥集团等采购平台 |
| 🏥 **医疗辅助决策** | 疾病症状关联 + 治疗方案规则 | 医疗机构 |
| ⚖️ **法律合同分析** | 合同条款提取 + 风险点识别 | 律所、企业法务 |

### 5.2 非适用场景

- 🚫 实时性要求极高的交易系统（延迟敏感）
- 🚫 完全没有结构化知识的纯对话场景
- 🚫 需要 100% 精确答案的医疗/法律场景（Clawra 是辅助，不是替代）

---

## 6. 项目结构

```
ontology-platform/
├── src/                          # 源代码
│   ├── clawra.py                # 核心入口类
│   ├── evolution/               # ⭐ 进化层（核心差异化）
│   │   ├── evolution_loop.py  # 8阶段进化闭环
│   │   ├── meta_learner.py    # 元学习器
│   │   ├── rule_discovery.py  # 规则发现引擎
│   │   ├── unified_logic.py   # 统一逻辑表达层（含Pattern版本控制）
│   │   ├── self_correction.py  # 自我纠错
│   │   ├── self_evaluator.py  # 自我评估
│   │   ├── skill_distiller.py # 技能蒸馏（含SafeExecutor）
│   │   └── skill_executor.py  # 技能执行器
│   ├── core/                   # 认知层
│   │   ├── reasoner.py        # 推理引擎
│   │   ├── knowledge_graph.py # 知识图谱（含Leiden社区检测）
│   │   ├── retriever.py      # GraphRAG检索
│   │   └── rule_engine.py     # 规则引擎
│   ├── memory/                 # 记忆层
│   │   ├── neo4j_adapter.py   # 图数据库
│   │   └── vector_adapter.py  # 向量数据库
│   ├── agents/                 # 编排层
│   │   └── orchestrator.py   # 认知编排器
│   ├── llm/                    # LLM适配层
│   │   └── ...
│   └── sdk/                   # SDK层
│       └── ...
├── examples/                   # 示例代码
│   ├── demo_clawra_e2e.py   # 端到端演示
│   ├── demo_supplier_monitor.py
│   └── streamlit_app.py      # Web演示
├── tests/                     # 测试套件（401+ 测试）
├── docs/                      # 文档
│   ├── 00_PROJECT_OVERVIEW.md # 本文档
│   ├── ARCHITECTURE.md        # 架构详解
│   ├── PHILOSOPHY.md          # 核心方法论
│   ├── EVOLUTION_LOOP.md      # 进化闭环设计
│   ├── ROADMAP.md             # 项目路线图
│   ├── CONFIGURATION.md       # 配置管理
│   ├── SDK_GUIDE.md           # SDK使用指南
│   ├── INTEGRATION_GUIDE.md   # 集成指南
│   ├── TROUBLESHOOTING.md     # 故障排查
│   ├── TESTING_STRATEGY.md    # 测试策略
│   ├── DEPLOYMENT.md          # 部署指南
│   ├── CHANGELOG.md           # 更新日志
│   └── ADR/                   # 架构决策记录
└── data/                      # 数据存储
    ├── knowledge_graph.db      # SQLite 图引擎
    ├── chroma_db/             # 向量数据库
    └── episodic_memory.db      # 情节记忆
```

---

## 7. 快速导航

| 你想做什么 | 去哪里 |
|-----------|--------|
| 5 分钟体验 Clawra | [QUICKSTART.md](QUICKSTART.md) |
| 了解核心技术理念 | [PHILOSOPHY.md](PHILOSOPHY.md) |
| 查看架构设计 | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 查看进化闭环设计 | [EVOLUTION_LOOP.md](EVOLUTION_LOOP.md) |
| 查阅 API 接口 | [api/API_REFERENCE.md](api/API_REFERENCE.md) |
| 运行示例代码 | [examples/README.md](../examples/README.md) |
| 部署到生产 | [DEPLOYMENT.md](DEPLOYMENT.md) |
| SDK 使用指南 | [SDK_GUIDE.md](SDK_GUIDE.md) |
| 集成指南 | [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) |
| 配置管理 | [CONFIGURATION.md](CONFIGURATION.md) |
| 故障排查 | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| 测试策略 | [TESTING_STRATEGY.md](TESTING_STRATEGY.md) |
| 架构决策记录 | [ADR/](ADR/) |
| 更新日志 | [CHANGELOG.md](CHANGELOG.md) |

---

## 8. 关键指标

| 指标 | 数值 |
|-----|------|
| 测试用例数 | 401+ |
| 核心模块测试覆盖率 | 85%+ |
| 支持领域数 | 5+ (medical, legal, gas_equipment, finance, engineering) |
| 最大推理深度 | 可配置（默认 10 层） |
| GraphRAG 召回模式 | Local / Global / Smart |
| LLM 支持 | OpenAI / MiniMax / 本地模型 |
| 进化阶段数 | 8阶段（闭环） |

---

## 9. 社区与支持

| 渠道 | 链接 |
|-----|------|
| GitHub Issues | https://github.com/wu-xiaochen/ontology-platform/issues |
| GitHub Discussions | https://github.com/wu-xiaochen/ontology-platform/discussions |
| License | MIT |

---

**下一步**：[PHILOSOPHY.md](PHILOSOPHY.md) — 深入了解 Clawra 的核心方法论与设计理念
