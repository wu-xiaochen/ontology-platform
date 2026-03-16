# 推理引擎设计文档

## 1. 概述

本文档描述基于本体论（Ontology）的推理引擎架构设计。该引擎负责从本体知识库中推导出新的知识断言，支持规则推理、置信度计算和链式推导。

### 1.1 核心设计目标

- **可扩展性**: 支持自定义推理规则（SWRL、RDF Schema、OWL 2 RL）
- **高效性**: 使用索引和缓存优化查询性能
- **可解释性**: 记录推理路径，支持结果回溯
- **置信度**: 为推理结果计算置信度评分

---

## 2. 推理流程

### 2.1 整体流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                         推理引擎流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ 输入查询 │───▶│ 知识加载 │───▶│ 规则匹配 │───▶│ 推理执行 │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                              │                  │
│                                              ▼                  │
│                                        ┌──────────┐             │
│                                        │置信度计算│             │
│                                        └──────────┘             │
│                                              │                  │
│                                              ▼                  │
│                                        ┌──────────┐             │
│                                        │ 结果输出 │             │
│                                        └──────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 详细流程步骤

#### Step 1: 输入解析
- 解析用户查询，提取实体、关系、约束条件
- 将查询转换为内部推理目标（Target）

```python
# 伪代码：输入解析
def parse_query(query: str) -> ReasoningTarget:
    # 1. NER 提取实体
    entities = ner.extract(query)
    
    # 2. 关系抽取
    relations = relation_extractor.extract(query)
    
    # 3. 构建推理目标
    target = ReasoningTarget(
        focus_entities=entities,
        query_relations=relations,
        constraints=extract_constraints(query)
    )
    
    return target
```

#### Step 2: 知识加载
- 从本体库中加载相关知识子图
- 使用索引加速检索

```python
# 伪代码：知识加载
def load_knowledge(target: ReasoningTarget) -> KnowledgeGraph:
    # 1. 定位焦点实体
    focus_entities = target.focus_entities
    
    # 2. 加载 2-hop 邻居子图（可配置）
    subgraph = ontology.load_subgraph(
        entities=focus_entities,
        depth=2,
        include_inferred=True
    )
    
    # 3. 过滤不相关三元组
    filtered = filter_by_relevance(subgraph, target)
    
    return KnowledgeGraph(triples=filtered)
```

#### Step 3: 规则匹配
- 匹配适用于当前上下文的推理规则
- 支持前向链和后向链两种模式

```python
# 伪代码：规则匹配
def match_rules(kg: KnowledgeGraph, target: ReasoningTarget) -> List[MatchedRule]:
    matched = []
    
    for rule in rule_registry.get_all_rules():
        # 规则前置条件匹配
        if rule.matches_precondition(kg, target):
            # 计算规则适用性得分
            applicability = rule.compute_applicability(kg)
            
            matched.append(MatchedRule(
                rule=rule,
                applicability=applicability,
                bindings=rule.unify(kg)
            ))
    
    # 按适用性排序，优先匹配高置信度规则
    return sorted(matched, key=lambda x: x.applicability, reverse=True)
```

#### Step 4: 推理执行
- 执行匹配的规则，产生新断言
- 支持链式推理（多步推导）

```python
# 伪代码：推理执行
def execute_reasoning(kg: KnowledgeGraph, matched_rules: List[MatchedRule]) -> List[Inference]:
    inferences = []
    working_memory = kg.clone()  # 工作内存，支持增量推理
    
    for matched in matched_rules:
        # 执行规则前向推导
        new_triples = matched.rule.apply(working_memory, matched.bindings)
        
        for triple in new_triples:
            # 检测循环依赖
            if not has_cycle(working_memory, triple):
                # 记录推理路径
                inference = Inference(
                    triple=triple,
                    derivation=[matched.rule],
                    source=matched.bindings
                )
                inferences.append(inference)
                working_memory.add(triple)
    
    return inferences
```

#### Step 5: 置信度计算
- 为每个推理结果计算置信度评分

```python
# 伪代码：置信度计算
def compute_confidence(inference: Inference, kg: KnowledgeGraph) -> float:
    # 1. 规则置信度（基于历史准确率）
    rule_confidence = inference.rule.accuracy  # 0.0 - 1.0
    
    # 2. 证据置信度（来源三元组的平均置信度）
    evidence_confidences = []
    for source in inference.source:
        triple_confidence = kg.get_triple_confidence(source)
        evidence_confidences.append(triple_confidence)
    
    evidence_confidence = mean(evidence_confidences) if evidence_confidences else 0.5
    
    # 3. 推导链长度惩罚（链越长，置信度越低）
    chain_penalty = pow(0.9, len(inference.derivation))
    
    # 4. 综合置信度
    final_confidence = (
        rule_confidence * 0.4 +
        evidence_confidence * 0.4 +
        chain_penalty * 0.2
    )
    
    return min(1.0, max(0.0, final_confidence))
```

#### Step 6: 结果输出
- 返回推理结果，按置信度排序
- 附带推理路径用于可解释性

```python
# 伪代码：结果输出
def output_results(inferences: List[Inference]) -> ReasoningResult:
    results = []
    
    for inf in inferences:
        confidence = compute_confidence(inf, working_memory)
        
        results.append(InferenceResult(
            triple=inf.triple,
            confidence=confidence,
            derivation_path=inf.derivation,
            explanation=generate_explanation(inf)
        ))
    
    # 按置信度降序排序
    results.sort(key=lambda x: x.confidence, reverse=True)
    
    # 过滤低置信度结果（阈值可配置）
    filtered = [r for r in results if r.confidence >= CONFIDENCE_THRESHOLD]
    
    return ReasoningResult(results=filtered)
```

---

## 3. 规则匹配机制

### 3.1 规则表示

支持多种规则格式：

```yaml
# 示例：OWL 2 RL 规则
rule_id: "owl_transitive_property"
description: "传递属性推导"
pattern:
  - "?x prop ?y"
  - "?y prop ?z"
conclusion:
  - "?x prop ?z"
confidence_weight: 0.9

# 示例：自定义业务规则
rule_id: "senior_engineer_promotion"
description: "高级工程师晋升规则"
preconditions:
  - entity.type == "Engineer"
  - entity.years_experience >= 5
  - entity.rating >= 4.0
conclusion:
  - entity.eligible_for_promotion == true
confidence_weight: 0.85
```

### 3.2 匹配算法

```python
# 伪代码：规则匹配器
class RuleMatcher:
    def __init__(self, ontology: Ontology):
        self.ontology = ontology
        self.rule_index = self._build_index()
    
    def _build_index(self) -> Dict:
        """按实体类型和关系建立规则索引"""
        index = defaultdict(list)
        for rule in self.rules:
            key = (rule.get_entity_type(), rule.get_relation())
            index[key].append(rule)
        return index
    
    def match(self, kg: KnowledgeGraph, target: ReasoningTarget) -> List[Match]:
        matches = []
        
        # 1. 快速索引查找
        candidate_rules = self._get_candidate_rules(target)
        
        # 2. 精确模式匹配
        for rule in candidate_rules:
            match_result = self._pattern_match(rule, kg)
            if match_result.is_match:
                matches.append(match_result)
        
        # 3. 语义扩展匹配（可选）
        if not matches:
            matches = self._semantic_expansion_match(target, kg)
        
        return matches
    
    def _pattern_match(self, rule: Rule, kg: KnowledgeGraph) -> MatchResult:
        """模式匹配：检查规则前件是否在知识图中"""
        # 构建查询模式
        patterns = rule.get_precondition_patterns()
        
        # 遍历匹配
        for pattern in patterns:
            results = kg.query(pattern)
            if not results:
                return MatchResult(is_match=False)
        
        return MatchResult(
            is_match=True,
            bindings=self._unify_bindings(results)
        )
```

---

## 4. 置信度计算

### 4.1 置信度模型

置信度计算采用多因子加权模型：

| 因子 | 权重 | 说明 |
|------|------|------|
| 规则置信度 | 0.4 | 规则本身的历史准确率 |
| 证据置信度 | 0.4 | 推理依据的来源置信度 |
| 链长惩罚 | 0.2 | 推导链越长，置信度越低 |

### 4.2 详细计算逻辑

```python
# 伪代码：置信度计算器
class ConfidenceCalculator:
    def __init__(self, config: ConfidenceConfig):
        self.rule_weight = config.rule_weight        # 0.4
        self.evidence_weight = config.evidence_weight  # 0.4
        self.chain_penalty_factor = config.chain_penalty_factor  # 0.9
    
    def calculate(self, inference: Inference, kg: KnowledgeGraph) -> float:
        # Factor 1: 规则置信度
        rule_conf = self._calculate_rule_confidence(inference.rule)
        
        # Factor 2: 证据置信度
        evidence_conf = self._calculate_evidence_confidence(inference.sources, kg)
        
        # Factor 3: 链长惩罚
        chain_penalty = self._calculate_chain_penalty(inference.derivation)
        
        # 综合计算
        confidence = (
            rule_conf * self.rule_weight +
            evidence_conf * self.evidence_weight +
            chain_penalty * self.chain_penalty_factor
        )
        
        return self._normalize(confidence)
    
    def _calculate_rule_confidence(self, rule: Rule) -> float:
        """基于规则历史表现计算置信度"""
        # 规则准确率 = 成功推导次数 / 总触发次数
        return rule.success_count / max(1, rule.trigger_count)
    
    def _calculate_evidence_confidence(self, sources: List[Triple], kg: KnowledgeGraph) -> float:
        """计算推理证据的平均置信度"""
        if not sources:
            return 0.5  # 无证据时默认中等置信度
        
        confidences = [kg.get_triple_confidence(s) for s in sources]
        
        # 使用几何平均（更保守）
        return geometric_mean(confidences) if confidences else 0.5
    
    def _calculate_chain_penalty(self, derivation: List[Rule]) -> float:
        """推导链越长，置信度越低"""
        length = len(derivation)
        return pow(self.chain_penalty_factor, length)
    
    def _normalize(self, confidence: float) -> float:
        """归一化到 [0, 1] 区间"""
        return max(0.0, min(1.0, confidence))
```

### 4.3 置信度等级

| 置信度区间 | 等级 | 含义 |
|------------|------|------|
| 0.9 - 1.0 | A | 高确信，可直接使用 |
| 0.7 - 0.9 | B | 较高确信，建议复核 |
| 0.5 - 0.7 | C | 中等确信，需人工确认 |
| 0.3 - 0.5 | D | 低确信，仅供参考 |
| 0.0 - 0.3 | E | 极低确信，不推荐使用 |

---

## 5. 数据结构

### 5.1 核心类定义

```python
@dataclass
class ReasoningTarget:
    """推理目标"""
    focus_entities: List[Entity]           # 焦点实体
    query_relations: List[Relation]       # 查询关系
    constraints: Dict                      # 约束条件
    mode: ReasoningMode                    # FORWARD / BACKWARD

@dataclass
class KnowledgeGraph:
    """知识图谱"""
    triples: List[Triple]
    entity_index: Dict[Entity, List[Triple]]
    relation_index: Dict[Relation, List[Triple]]
    
    def query(self, pattern: TriplePattern) -> List[Binding]:
        """模式查询"""
        ...

@dataclass
class Triple:
    """三元组"""
    subject: Entity
    predicate: Relation
    object: Entity
    confidence: float                       # 原始置信度
    source: str                             # 来源标识
    timestamp: datetime

@dataclass
class Rule:
    """推理规则"""
    id: str
    name: str
    description: str
    preconditions: List[Pattern]            # 前置条件
    conclusion: Pattern                      # 结论模式
    confidence_weight: float                # 置信度权重
    trigger_count: int                      # 触发次数
    success_count: int                      # 成功次数
    
    @property
    def accuracy(self) -> float:
        return self.success_count / max(1, self.trigger_count)

@dataclass
class MatchedRule:
    """匹配后的规则"""
    rule: Rule
    applicability: float                    # 适用性评分
    bindings: List[Binding]                 # 变量绑定

@dataclass
class Inference:
    """推理结果"""
    triple: Triple
    derivation: List[Rule]                  # 推导链
    sources: List[Triple]                   # 源三元组

@dataclass
class InferenceResult:
    """最终推理结果"""
    triple: Triple
    confidence: float
    confidence_level: str                   # A/B/C/D/E
    derivation_path: List[Rule]
    explanation: str                       # 自然语言解释
```

---

## 6. 配置参数

```yaml
# 推理引擎配置
reasoner:
  # 推理模式
  mode: "HYBRID"  # FORWARD / BACKWARD / HYBRID
  
  # 知识加载
  knowledge:
    max_depth: 3                 # 最大跳数
    min_confidence: 0.3          # 最小置信度阈值
    
  # 规则匹配
  rules:
    max_candidates: 100          # 最大候选规则数
    timeout_ms: 5000             # 匹配超时
    
  # 推理执行
  reasoning:
    max_chain_length: 5          # 最大推导链长度
    allow_recursive: false       # 是否允许递归推理
    
  # 置信度
  confidence:
    rule_weight: 0.4
    evidence_weight: 0.4
    chain_penalty_factor: 0.9
    threshold: 0.5              # 输出阈值
    
  # 性能
  performance:
    cache_enabled: true
    cache_ttl_seconds: 3600
    parallel_workers: 4
```

---

## 7. 总结

本设计文档定义了基于本体论的推理引擎核心架构：

1. **推理流程**: 解析 → 加载 → 匹配 → 执行 → 置信度计算 → 输出
2. **规则匹配**: 支持多种规则格式，采用索引加速和模式匹配
3. **置信度计算**: 多因子加权模型，综合规则、证据、链长因素

该设计支持扩展，可根据实际业务需求添加自定义规则和置信度策略。
