# Clawra: 自主进化本体认知引擎 (Autonomous Agent Framework)

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](blob/main/LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Active-green.svg)](https://neo4j.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Embedded-purple.svg)](https://www.trychroma.com/)

**Clawra** 是一款具备**自主进化能力**的神经符号认知代理框架。它突破了传统 Agent 需要人工编写规则的限制，通过**零硬编码**的元学习架构，实现真正的自主学习、自我进化、持续成长。

## 🎯 核心突破

- **零硬编码**: 所有规则、行为、策略均通过自主学习获得，无需人工编写
- **领域自适应**: 自动识别领域，动态加载相关逻辑，适配任何行业
- **自我进化**: 从数据、文本、交互中持续学习，不断提升能力
- **神经符号融合**: 结合大模型语义理解与符号逻辑严谨性

---

## 🏗️ 系统架构

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

## ✨ 核心特性

| 特性 | 说明 | 状态 |
|-----|------|------|
| 🧠 **自主规则学习** | 从文本自动提取规则，无需硬编码 | ✅ 已实现 |
| 🔄 **领域自适应** | 自动识别领域，动态加载逻辑 | ✅ 已实现 |
| 📊 **规则发现** | 从数据中归纳规则，支持关联挖掘 | ✅ 已实现 |
| 🎯 **统一逻辑表达** | 规则/行为/策略统一表达，灵活扩展 | ✅ 已实现 |
| 🔍 **GraphRAG** | 向量+图谱混合检索，增强上下文 | ✅ 已实现 |
| 🛡️ **规则引擎** | AST级数学沙盒，完全阻断 DoS 及 OOM 内存高阶攻击 | ✅ 已实现 |
| 🤖 **认知编排** | 纯异步非阻塞 ReAct 调用，保证并发毫秒级高可用 | ✅ 已实现 |

---

## 🚀 快速开始

### 1. 环境准备

**系统要求:**
- Python 3.10+
- Neo4j 5.x (可选，用于图谱存储)
- 8GB+ RAM

**安装步骤:**
```bash
git clone https://github.com/wu-xiaochen/ontology-platform.git
cd ontology-platform
pip install -r requirements.txt
```

### 2. 配置文件

在项目根目录创建 `.env` 文件：

```env
# LLM API 配置 (支持 OpenAI 格式)
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 或火山引擎 Ark
# OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
# OPENAI_MODEL=doubao-seed-2-0-pro-260215

# Neo4j 配置 (可选)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 3. 启动演示

我们为您提供了两种验证框架能力的演示级 Demo：

**方式一：高端前端 Web 演示 (推荐)**
包括自主提取、DoS注入测试、LLM 幻觉拦截等交互式展示。
```bash
PYTHONPATH=. streamlit run examples/web_capability_demo.py --server.port 8501
```

**方式二：终端控制台 E2E 演示**
```bash
PYTHONPATH=. python examples/demo_clawra_e2e.py
```

### 4. 编程使用

```python
from evolution.unified_logic import UnifiedLogicLayer
from evolution.meta_learner import MetaLearner

# 初始化系统
logic_layer = UnifiedLogicLayer()
meta_learner = MetaLearner(logic_layer, None)

# 自主学习
result = meta_learner.learn(
    "如果设备是燃气调压箱，那么需要定期维护",
    input_type="text"
)

print(f"发现 {len(result['learned_patterns'])} 个模式")
```

---

## 📁 项目结构

```
ontology-platform/
├── src/                          # 源代码
│   ├── agents/                   # 认知编排层
│   │   ├── base.py              # Agent 基类
│   │   ├── orchestrator.py      # 认知编排器
│   │   ├── metacognition.py     # 元认知模块
│   │   └── auditor.py           # 审计引擎
│   ├── core/                     # 核心逻辑层
│   │   ├── reasoner.py          # 推理引擎
│   │   ├── rule_engine.py       # 规则引擎
│   │   ├── ontology/            # 本体管理
│   │   └── permissions.py       # 权限管理
│   ├── evolution/                # 自主进化层 ⭐
│   │   ├── unified_logic.py     # 统一逻辑表达
│   │   ├── meta_learner.py      # 元学习器
│   │   ├── rule_discovery.py    # 规则发现引擎
│   │   ├── behavior_learner.py  # 行为学习器
│   │   └── self_evaluator.py    # 自我评估器
│   ├── memory/                   # 记忆存储层
│   │   ├── neo4j_adapter.py     # Neo4j 适配器
│   │   ├── vector_adapter.py    # ChromaDB 适配器
│   │   └── base.py              # 记忆基类
│   ├── perception/               # 感知提取层
│   │   ├── extractor.py         # 知识提取器
│   │   └── glossary_engine.py   # 术语引擎
│   └── llm/                      # LLM 接口层
│       ├── api.py               # API 封装
│       └── caching.py           # 缓存策略
├── examples/                     # 示例代码
│   ├── autonomous_evolution_demo.py  # 自主进化演示 ⭐
│   ├── clawra_final_demo.py          # 完整功能演示
│   └── archive/                 # 归档旧版本
├── tests/                        # 测试代码
├── docs/                         # 文档
│   ├── api/                     # API 文档
│   ├── architecture/            # 架构文档
│   ├── guides/                  # 使用指南
│   └── development/             # 开发规范
├── data/                         # 数据文件
└── scripts/                      # 工具脚本
```

---

## 📚 文档导航

| 文档 | 说明 | 路径 |
|-----|------|------|
| [API 参考](docs/api/API_REFERENCE.md) | 完整 API 文档 | `docs/api/` |
| [架构设计](docs/architecture/architecture.md) | 系统架构详解 | `docs/architecture/` |
| [开发规范](docs/development/CONTRIBUTING.md) | 代码规范与贡献指南 | `docs/development/` |
| [概念说明](docs/architecture/CONCEPT_CLARIFICATION.md) | 核心概念解释 | `docs/architecture/` |
| [OWL 语义](docs/architecture/OWL_SEMANTICS.md) | 本体语义规范 | `docs/architecture/` |
| [Agent 指南](docs/guides/AGENT_GUIDE.md) | Agent 开发指南 | `docs/guides/` |

## 🔧 开发规范

### 代码规范
1. **类型注解**: 所有函数必须使用类型注解
2. **文档字符串**: 使用 Google 风格 docstring
3. **异步优先**: IO 操作必须使用 async/await
4. **错误处理**: 使用自定义异常体系

### 架构原则
1. **零硬编码**: 所有规则必须通过自主学习获得
2. **领域隔离**: 不同领域的逻辑必须隔离
3. **可审计**: 所有决策必须可追溯
4. **可测试**: 核心功能必须有单元测试

### 提交规范
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

---

## 🗺️ 路线图 (Roadmap)

### 已完成功能 ✅
- [x] 自主进化架构（零硬编码规则学习）
- [x] 领域自适应机制
- [x] 统一逻辑表达层
- [x] 规则发现引擎
- [x] 元学习器
- [x] GraphRAG 混合检索
- [x] 神经符号推理引擎
- [x] 多 LLM 支持 (OpenAI/VolcEngine)

### 进行中 🚧
- [ ] 多模态知识抽取（图文）
- [ ] 分布式知识图谱
- [ ] 联邦式本体协作

### 规划中 📋
- [ ] 强化学习优化策略
- [ ] 自动超参数调优
- [ ] 可视化规则编辑器

---

## 许可证
本项目采用 Apache 2.0 许可证。
