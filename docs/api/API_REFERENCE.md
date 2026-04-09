# Clawra API 参考文档

## 概述

本文档提供 Clawra 框架的完整 API 参考，包括进化层、推理层、记忆层和感知层的所有公共接口。

---

## 进化层 API (Evolution Layer)

### UnifiedLogicLayer

统一逻辑表达层，管理所有逻辑模式（规则、行为、策略、约束）。

#### 初始化

```python
from evolution.unified_logic import UnifiedLogicLayer

logic_layer = UnifiedLogicLayer()
```

#### 方法

##### `add_pattern(pattern: LogicPattern) -> bool`

添加新的逻辑模式。

**参数:**
- `pattern`: LogicPattern 对象

**返回:**
- `bool`: 是否添加成功

**示例:**
```python
from evolution.unified_logic import LogicPattern, LogicType

pattern = LogicPattern(
    id="rule:equipment_maintenance",
    logic_type=LogicType.RULE,
    name="设备维护规则",
    description="燃气设备需要定期维护",
    conditions=[
        {"subject": "?X", "predicate": "is_a", "object": "燃气设备"}
    ],
    actions=[
        {"type": "infer", "subject": "?X", "predicate": "requires", "object": "定期维护"}
    ],
    domain="gas_equipment"
)

logic_layer.add_pattern(pattern)
```

##### `extract_logic_from_text(text: str, domain_hint: str = None) -> List[LogicPattern]`

从文本中提取逻辑模式。

**参数:**
- `text`: 输入文本
- `domain_hint`: 领域提示（可选）

**返回:**
- `List[LogicPattern]`: 提取的逻辑模式列表

**示例:**
```python
text = "如果设备是燃气调压箱，那么需要定期维护。"
patterns = logic_layer.extract_logic_from_text(text, domain_hint="gas_equipment")
```

##### `get_patterns_by_domain(domain: str) -> List[LogicPattern]`

获取特定领域的所有逻辑模式。

##### `get_patterns_by_type(logic_type: LogicType) -> List[LogicPattern]`

获取特定类型的逻辑模式。

##### `execute_pattern(pattern: LogicPattern, context: Dict) -> Dict`

执行逻辑模式。

**返回:**
```python
{
    "success": bool,
    "results": List[Dict],
    "explanation": str
}
```

##### `get_statistics() -> Dict`

获取统计信息。

**返回:**
```python
{
    "total_patterns": int,
    "by_type": Dict[str, int],
    "by_domain": Dict[str, int],
    "total_executions": int,
    "avg_confidence": float
}
```

---

### MetaLearner

元学习器，实现"学习如何学习"的能力。

#### 初始化

```python
from evolution.meta_learner import MetaLearner
from evolution.rule_discovery import RuleDiscoveryEngine

discovery_engine = RuleDiscoveryEngine(logic_layer)
meta_learner = MetaLearner(logic_layer, discovery_engine)
```

#### 方法

##### `learn(input_data: Any, input_type: str = "text", domain_hint: str = None) -> Dict`

执行学习过程。

**参数:**
- `input_data`: 输入数据（文本、结构化数据或交互历史）
- `input_type`: 输入类型 ("text", "structured", "interaction")
- `domain_hint`: 领域提示

**返回:**
```python
{
    "episode_id": str,
    "domain": str,
    "strategy": str,
    "learned_patterns": List[str],
    "learning_time": float,
    "success": bool
}
```

**示例:**
```python
# 从文本学习
result = meta_learner.learn(
    "燃气设备需要定期维护。维护周期是6个月。",
    input_type="text"
)

# 从结构化数据学习
facts = [
    {"subject": "设备A", "predicate": "is_a", "object": "燃气设备"},
    {"subject": "设备A", "predicate": "requires", "object": "维护"}
]
result = meta_learner.learn(facts, input_type="structured")
```

##### `detect_domain(text: str) -> Dict[str, float]`

检测文本所属领域。

**返回:**
```python
{
    "medical": 0.85,
    "legal": 0.10,
    "gas_equipment": 0.05
}
```

##### `provide_feedback(episode_id: str, feedback_score: float, feedback_text: str = None)`

提供学习反馈。

**参数:**
- `episode_id`: 学习过程 ID
- `feedback_score`: 反馈分数 (0-1)
- `feedback_text`: 反馈文本（可选）

##### `get_learning_statistics() -> Dict`

获取学习统计。

##### `export_knowledge(domain: str = None) -> str`

导出知识为 JSON。

##### `import_knowledge(knowledge_json: str) -> Dict`

导入外部知识。

---

### RuleDiscoveryEngine

规则发现引擎，从数据中自动发现规则。

#### 方法

##### `discover_from_facts(facts: List[Dict]) -> List[Dict]`

从事实中归纳规则。

**返回的规则格式:**
```python
{
    "id": str,
    "type": str,  # "transitive", "classification", "inheritance"
    "name": str,
    "description": str,
    "conditions": List[Dict],
    "actions": List[Dict],
    "confidence": float,
    "support": int
}
```

##### `discover_from_interactions(interaction_history: List[Dict]) -> List[Dict]`

从交互历史中发现策略规则。

##### `evaluate_rule_quality(rule: Dict, test_cases: List[Dict]) -> Dict`

评估规则质量。

**返回:**
```python
{
    "precision": float,
    "recall": float,
    "f1": float,
    "applicable_cases": int
}
```

---

## 推理层 API (Core Layer)

### Reasoner

推理引擎，支持前向链和后向链推理。

#### 初始化

```python
from core.reasoner import Reasoner

reasoner = Reasoner()
```

#### 方法

##### `add_fact(fact: Fact) -> bool`

添加事实。

```python
from core.reasoner import Fact

fact = Fact(
    subject="燃气调压箱",
    predicate="is_a",
    object="燃气设备",
    confidence=0.95
)
reasoner.add_fact(fact)
```

##### `forward_chain(initial_facts: List[Fact] = None, max_depth: int = 10) -> InferenceResult`

前向链推理。

**返回:**
```python
InferenceResult(
    conclusions=List[InferenceStep],
    facts_used=List[Fact],
    depth=int,
    total_confidence=ConfidenceResult
)
```

##### `backward_chain(goal: Fact, max_depth: int = 10) -> Optional[List[Fact]]`

后向链推理。

##### `add_rule(rule: Rule) -> bool`

添加规则。

---

### RuleEngine

规则引擎，执行确定性规则。

#### 方法

##### `evaluate_condition(condition: str, context: Dict) -> bool`

评估条件。

##### `execute_action(action: str, context: Dict) -> Any`

执行动作。

---

## 记忆层 API (Memory Layer)

### Neo4jAdapter

Neo4j 图数据库适配器。

#### 方法

##### `add_triple(subject: str, predicate: str, object: str, properties: Dict = None)`

添加三元组。

##### `query_triples(pattern: Dict) -> List[Dict]`

查询三元组。

##### `get_neighbors(entity: str, direction: str = "both") -> List[Dict]`

获取邻居节点。

### VectorAdapter

ChromaDB 向量数据库适配器。

#### 方法

##### `add_document(text: str, metadata: Dict = None) -> str`

添加文档。

##### `search(query: str, top_k: int = 5) -> List[Dict]`

语义搜索。

---

## 感知层 API (Perception Layer)

### Extractor

知识提取器。

#### 方法

##### `extract_from_text(text: str, schema: Dict = None) -> Dict`

从文本提取结构化知识。

**返回:**
```python
{
    "entities": List[Dict],
    "relations": List[Dict],
    "facts": List[Dict]
}
```

##### `extract_from_document(file_path: str) -> Dict`

从文档提取知识。

---

## Agent 层 API (Agents Layer)

### CognitiveOrchestrator

认知编排器。

#### 方法

##### `run(task: str, context: Dict = None) -> Dict`

执行任务。

**返回:**
```python
{
    "result": Any,
    "trace": List[Dict],
    "confidence": float,
    "execution_time": float
}
```

### MetacognitiveAgent

元认知 Agent。

#### 方法

##### `reflect(action: str, context: Dict) -> Dict`

执行元认知反思。

##### `calibrate_confidence(prediction: Any, evidence: List) -> float`

校准置信度。

---

## 错误处理

所有 API 可能抛出以下异常：

- `ValueError`: 参数错误
- `RuntimeError`: 运行时错误
- `ConnectionError`: 数据库连接错误
- `TimeoutError`: 超时错误

**示例:**
```python
try:
    result = meta_learner.learn(text)
except ValueError as e:
    print(f"参数错误: {e}")
except RuntimeError as e:
    print(f"运行时错误: {e}")
```

---

## 类型定义

### LogicType

```python
class LogicType(Enum):
    RULE = "rule"
    BEHAVIOR = "behavior"
    POLICY = "policy"
    CONSTRAINT = "constraint"
    WORKFLOW = "workflow"
```

### LogicPattern

```python
@dataclass
class LogicPattern:
    id: str
    logic_type: LogicType
    name: str
    description: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    confidence: float = 0.8
    source: str = "learned"
    domain: str = "generic"
    version: int = 1
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
```

---

## 版本信息

- **当前版本**: 2.0.0
- **API 版本**: v2
- **最后更新**: 2026-04-02
