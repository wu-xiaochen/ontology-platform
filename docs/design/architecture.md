# Clawra 技术设计方案

## 1. 系统架构概览

Clawra 是一个自主进化 Agent 框架（Neuro-Symbolic Cognitive Engine），采用分层架构设计。

```
┌───────────────────────────────────────────┐
│                 API Layer                 │
│         (FastAPI + GraphQL)               │
├───────────────────────────────────────────┤
│              Agent Layer                  │
│  Orchestrator │ Metacognition │ Auditor   │
├───────────────────────────────────────────┤
│            Core Engine Layer              │
│  Reasoner │ RuleEngine │ Confidence       │
├───────────────────────────────────────────┤
│           Evolution Layer                 │
│  UnifiedLogic │ MetaLearner │ RuleDiscov  │
├───────────────────────────────────────────┤
│            Memory Layer                   │
│  Semantic(Neo4j) │ Episodic(SQLite)       │
│  Vector(ChromaDB) │ Governance            │
├───────────────────────────────────────────┤
│          Infrastructure Layer             │
│  ConfigManager │ Security │ Performance   │
└───────────────────────────────────────────┘
```

## 2. 核心数据结构

### 2.1 Fact（事实/断言）
```python
@dataclass
class Fact:
    subject: str          # 主语实体
    predicate: str        # 谓语关系
    object: str           # 宾语实体
    confidence: float     # 置信度 [0.0, 1.0]
    source: str           # 来源标识
```

### 2.2 Rule（推理规则）
```python
@dataclass
class Rule:
    id: str               # 规则唯一标识
    name: str             # 规则名称
    rule_type: RuleType   # 规则类型 (IF_THEN/TRANSITIVE/SYMMETRIC)
    condition: str        # 条件模式 (支持 ?var 变量)
    conclusion: str       # 结论模式
    confidence: float     # 规则置信度
```

### 2.3 LogicPattern（逻辑模式）
```python
@dataclass
class LogicPattern:
    id: str               # 模式唯一标识
    logic_type: LogicType # 类型 (RULE/BEHAVIOR/POLICY/CONSTRAINT/WORKFLOW)
    conditions: List[Dict] # 前提条件
    actions: List[Dict]    # 动作/结论
    confidence: float      # 置信度
    domain: str            # 所属领域
```

## 3. 接口契约

### 3.1 推理引擎接口
- `forward_chain(initial_facts, max_depth, timeout_seconds) -> InferenceResult`
- `backward_chain(goal, max_depth, timeout_seconds) -> InferenceResult`
- `add_fact(fact) -> None`
- `add_rule(rule) -> None`
- `query(subject, predicate, obj, min_confidence) -> List[Fact]`

### 3.2 学习接口
- `Clawra.learn(text, domain_hint) -> Dict[str, Any]`
- `MetaLearner.learn(input_data, input_type, domain_hint) -> Dict`
- `RuleDiscoveryEngine.discover_from_facts(facts) -> List[Dict]`

### 3.3 记忆接口
- `SemanticMemory.store_fact(fact) -> None`
- `SemanticMemory.query(concept, depth) -> List[Any]`
- `SemanticMemory.semantic_search(query, top_k) -> List[Document]`
- `EpisodicMemory.store_episode(episode) -> None`
- `EpisodicMemory.retrieve_episodes(limit) -> List[dict]`

### 3.4 配置接口
- `ConfigManager` 单例模式，包含以下配置域：
  - `llm`: LLM API 配置
  - `database`: 数据库连接配置
  - `app`: 应用基础配置
  - `reasoning`: 推理引擎配置
  - `memory`: 记忆系统配置
  - `evolution`: 演化模块配置
  - `performance`: 性能优化配置

## 4. 安全机制

### 4.1 SafeMathSandbox (Deep AST Protection)
- 基于 AST 的安全数学表达式求值器
- 仅允许白名单运算符和函数（abs, min, max, round, sum, len）
- 拒绝执行任何未识别的 AST 节点类型
- **[A Audit Update]** 动态校验 AST 深度，限制 `MAX_AST_DEPTH` 以防止大模型生成导致递归栈溢出的 DoS 攻击。

### 4.2 AuditorAgent
- 在 Orchestrator 执行工具调用前进行安全审计
- 检测潜在的逻辑风险和数学冲突
- 具备 BLOCKED/APPROVED 决策能力

### 4.3 零硬编码配置与容灾机制 (Zero-Hardcoding Prompt Policy)
- 严禁代码中内置 LLM Prompt，必须从 `ConfigManager` 或 `config/prompts.yaml` 按变量加载。
- 提取器 `llm_extractor` 落后降级阈值（Fallback Threshold）与补偿 Regex 亦由配置驱动，提升服务透明度。

## 5. 性能与并发优化

- LRU 缓存：推理结果缓存，TTL 可配置
- 连接池：Neo4j 连接复用
- 批处理：AsyncBatchProcessor 支持并发任务
- 索引优化：谓词索引加速规则匹配
- **分布式锁（Distributed Readiness）**：在 SemanticMemory 与 EpisodicMemory 写入核心链路上，采用 `asyncio.Lock` 与写队列管理，防止分布式推理下的并行写脏数据及死锁瓶颈。
