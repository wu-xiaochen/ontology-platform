# Clawra 架构详解

> 从源码结构到模块协作，全面解析 Clawra 的工程架构。
> 面向人群：想深入理解 Clawra 如何工程落地的开发者。

---

## 1. 分层架构总览

Clawra 采用**六层架构**，从底层到顶层依次是：

```
┌─────────────────────────────────────────────────────┐
│               5. 应用层 (clawra.py / SDK)            │
│         Clawra 主类 / ClawraSDK / API 接口            │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               4. 编排层 (agents/)                     │
│            Orchestrator 认知编排器                      │
│         Learn / Reason / Retrieve / Execute           │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               3. 进化层 (evolution/)        ⭐       │
│    EvolutionLoop / MetaLearner / RuleDiscovery       │
│    UnifiedLogic / SelfEvaluator / SelfCorrection     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               2. 认知层 (core/)                      │
│         Reasoner / RuleEngine / KnowledgeGraph        │
│         Retriever (GraphRAG) / PermissionManager     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               1. 记忆层 (memory/)                    │
│        Neo4jAdapter / ChromaAdapter / EpisodicMemory │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               0. 适配层 (llm/)                       │
│         LLMProvider 抽象 / API / MiniMax / 缓存策略  │
└─────────────────────────────────────────────────────┘
```

**数据流**：用户输入 → 感知提取 → 学习存入KG → 推理得出结论 → 评估反馈 → 进化更新

---

## 2. 核心模块详解

### 2.1 应用层：`clawra.py` + `sdk/`

```
src/
├── clawra.py              # Clawra 主类（高层 API）
└── sdk/
    ├── __init__.py        # ClawraSDK 导出
    ├── adapters/          # 外部框架适配器（LangChain 等）
    └── ...
```

**Clawra 主类**是用户入口，提供 `learn()` / `reason()` / `retrieve()` / `evolve()` 四个核心方法：

```python
from src.clawra import Clawra

agent = Clawra(enable_memory=False)

# 学习：文本 → 知识图谱
agent.learn("燃气调压箱出口压力必须 ≤ 0.4MPa")

# 推理：事实 → 新结论
agent.add_fact("调压箱A", "出口压力", "0.35MPa")
conclusions = agent.reason(max_depth=3)

# 检索：语义 + 图结构混合
results = agent.retrieve_knowledge("燃气安全规范", top_k=5)

# 进化：运行完整闭环
agent.evolve()
```

**ClawraSDK** 封装 Clawra 主类，提供更友好的接口。

---

### 2.2 编排层：`agents/orchestrator.py`

`Orchestrator` 是认知编排器，负责将用户的复杂请求拆解为多个子任务，按顺序或并行执行。

```
Orchestrator.orchestrate()
  ├── Perceive（感知）
  ├── Learn（学习）
  ├── Reason（推理）
  └── Retrieve（检索）
```

核心流程：接收 `ActionRequest` → 解析 `thought` → 选择 `tool` → 执行 → 返回 `ActionResult`

---

### 2.3 进化层：`evolution/` ⭐ 核心差异化

```
evolution/
├── evolution_loop.py     # 8阶段进化闭环（821行）⭐
├── meta_learner.py       # 元学习器（669行）
├── rule_discovery.py      # 规则发现（406行）
├── unified_logic.py       # 统一逻辑层（968行）⭐ 含Pattern版本控制
├── skill_distiller.py     # 技能蒸馏（433行）
├── skill_executor.py      # 技能执行器（新增）
├── self_evaluator.py      # 自我评估
├── self_correction.py     # 自我纠错
└── behavior_learner.py    # 行为学习
```

#### EvolutionLoop 8阶段闭环

```
Perceive → Learn → Reason → Execute → Evaluate → DetectDrift → ReviseRules → UpdateKG
    ↑                                                                              │
    └────────────── 失败反馈路由（推理错误 / 规则冲突 / 漂移检测） ─────────────────┘
```

| 阶段 | 职责 | 核心组件 |
|-----|------|---------|
| Perceive | 解析输入，提取结构化信息 | LLM Extractor |
| Learn | 从文本中发现规则 | MetaLearner + RuleDiscovery |
| Reason | 执行前向链/后向链推理 | Reasoner |
| Execute | 执行推理得出的动作 | SkillExecutor |
| Evaluate | 评估推理结果质量 | SelfEvaluator |
| DetectDrift | 检测知识/规则漂移 | LogicLayer 置信度检查 |
| ReviseRules | 修正或废弃问题规则 | SelfCorrection |
| UpdateKG | 将新知识写入知识图谱 | KnowledgeGraph |

#### MetaLearner 元学习器

MetaLearner 学习"如何学习"，是 Clawra 区别于传统规则引擎的核心。

```python
# 从文本中学习模式
result = meta_learner.learn(
    text="燃气调压箱的出口压力必须在 0.002~0.4MPa 之间",
    domain_hint="gas_equipment"
)
# 返回：LogicPattern（含条件、动作、置信度）
```

#### UnifiedLogicLayer 统一逻辑层

统一表达三层规则：
- **LogicPattern**：条件→动作规则（IF-THEN）
- **BehaviorPattern**：行为序列模式
- **PolicyRule**：业务策略规则

**Pattern 版本控制**：
```python
# 每次 add_pattern 自动保存历史版本
layer.add_pattern(new_pattern)       # 旧版本自动归档
layer.get_pattern_history("p1")       # 查看所有版本
layer.rollback_pattern("p1", 2)       # 回滚到版本2
layer.compare_versions("p1", 1, 2)    # diff对比
```

**规则相似度去重**：
```python
layer.merge_similar_patterns(threshold=0.85)  # 自动合并高相似度规则
```

---

### 2.4 认知层：`core/`

```
core/
├── knowledge_graph.py   # 知识图谱（Neo4j/SQLite）⭐ 含Leiden社区检测
├── reasoner.py         # 推理引擎（前向链/后向链/Datalog）
├── rule_engine.py      # 规则引擎（OntologyRule）
├── retriever.py        # GraphRAG 检索（Local/Global/Smart）
├── security.py         # SafeMath 安全沙盒
├── permission.py       # RBAC 权限管理
└── runtime.py         # 运行时监控
```

#### KnowledgeGraph 知识图谱

三级索引结构（SPO / PO / OS），支持 Neo4j 和 SQLite 双后端。

**社区检测算法**：
- `louvain`（默认）：模块度优化
- `leiden`（推荐）：保证社区连接性，更精确
- `girvan_newman`：层次化社区
- `label_propagation`：快速大规模

```python
kg.detect_communities(algorithm="leiden")
kg.generate_community_summaries(llm_client)
paths = kg.cross_community_reasoning("实体A", "实体B", max_hops=3)
```

#### Reasoner 推理引擎

三种推理模式：
- **前向链（Forward）**：从已知事实出发，演绎新结论
- **后向链（Backward）**：从目标结论倒推所需前提
- **Datalog**：支持过滤/聚合/否定的声明式查询

#### Retriever GraphRAG

混合检索策略：
- `entity`：基于知识图谱的结构化检索
- `semantic`：ChromaDB 向量相似度检索
- `global`：社区级别全局检索
- `smart`：LLM 判断最佳策略

---

### 2.5 记忆层：`memory/`

```
memory/
├── neo4j_adapter.py     # Neo4j 图数据库适配器
├── vector_adapter.py    # ChromaDB 向量适配器
├── episodic_memory.py   # 情节记忆（成功/失败案例）
├──本体管理/              # Ontology 管理
└── audit.py            # 审计日志
```

**情节记忆**记录每次推理的成功/失败案例，用于：
- 失败案例优先重学
- 推理质量历史追踪
- 置信度动态校准

---

### 2.6 适配层：`llm/`

```
llm/
├── api/
│   ├── main.py          # LLM 调用入口
│   ├── cache.py         # LLM 响应缓存
│   └── router.py       # 多模型路由
└── providers/           # 模型提供商
    ├── openai.py
    ├── minimax.py
    └── ...
```

支持多模型：
- OpenAI GPT 系列
- MiniMax
- 火山引擎
- 本地模型（Ollama）

---

## 3. 数据流全链路

```
用户输入文本
    │
    ▼
┌─────────────────────────────────────────┐
│          Orchestrator.orchestrate()       │
│   1. extract_entities() → 三元组          │
│   2. reasoner.forward_chain() → 结论      │
│   3. retriever.retrieve() → 上下文        │
│   4. orchestrator._route_action() → 执行  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│             Clawra.reason()              │
│   输入：事实列表                          │
│   输出：推理结论（含置信度）               │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│          Clawra.evolve() ⭐             │
│   运行完整8阶段进化闭环                   │
│   推理失败 → MetaLearner 回流重学        │
└─────────────────────────────────────────┘
```

---

## 4. 配置文件架构

所有配置从以下优先级读取（高→低）：

```
环境变量（.env）
  ↓
config.yaml（项目根目录）
  ↓
默认参数（config.py 中的 dataclass 默认值）
```

核心配置类：
- `LLMConfig`：模型选择、超时、缓存策略
- `MemoryConfig`：Neo4j/ChromaDB 连接参数
- `EvolutionConfig`：进化参数（最大迭代次数、置信度阈值）
- `GraphConfig`：社区检测分辨率、最小社区规模

---

## 5. 测试架构

测试金字塔：

```
         ▲ E2E 测试（少量，长期）
        ▲▲▲ 集成测试
       ▲▲▲▲▲▲ 单元测试（大量，快速）
      ▲▲▲▲▲▲▲▲
```

- **单元测试**：每个模块独立测试（mock LLM 调用）
- **集成测试**：模块间协作正确性
- **E2E 测试**：完整闭环验证

运行：
```bash
# 全部测试
python -m pytest tests/ --timeout=60 -q

# 带覆盖率
python -m pytest tests/ --cov=src --timeout=60 -q

# 指定模块
python -m pytest tests/test_evolution_loop.py -v
```

---

## 6. 扩展指南

### 添加新 LLM Provider

1. 在 `llm/providers/` 创建 `your_provider.py`
2. 实现 `LLMProvider` 接口
3. 在 `LLMFactory` 注册
4. 添加环境变量配置

### 添加新推理模式

1. 在 `core/reasoner.py` 添加 `_reason_*` 方法
2. 在 `forward_chain()` 中注册路由
3. 添加对应测试用例

### 添加新进化阶段

1. 在 `evolution_loop.py` 的 `_phase_sequence` 中添加新阶段
2. 实现 `_phase_*` 方法
3. 在 `EvolutionPhase` 枚举中注册
4. 添加单元测试

---

**最后更新**: 2026-04-13
