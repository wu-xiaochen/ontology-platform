# Clawra 自主进化闭环设计文档

> 详细说明 Clawra 的自主进化机制：从感知到学习、从推理到评估、从纠错到迭代的完整闭环。

---

## 1. 进化闭环概述

### 1.1 闭环架构图

```
┌────────────────────────────────────────────────────────────────────────┐
│                         CL AWRA 进化闭环 (Evolution Loop)               │
│                                                                        │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │    感知      │────▶│    学习      │────▶│    推理      │         │
│  │  Perception  │     │   Learning   │     │  Reasoning   │         │
│  └──────────────┘     └──────────────┘     └──────────────┘         │
│        │                    │                    │                    │
│        │                    │                    │                    │
│        │              ┌─────┴─────┐              │                    │
│        │              │           │              │                    │
│        │              ▼           ▼              │                    │
│        │     ┌──────────────┐ ┌──────────────┐   │                    │
│        │     │  规则发现    │ │  知识存储    │   │                    │
│        │     │RuleDiscovery │ │ KnowledgeBase│   │                    │
│        │     └──────────────┘ └──────────────┘   │                    │
│        │                                         │                    │
│        │                    ▲                    │                    │
│        │                    │                    │                    │
│        └────────────────────┴────────────────────┘                    │
│                          反馈通道                                      │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                        评估与纠错                                  │ │
│  │   SelfEvaluator ──▶ SelfCorrection ──▶ SkillDistiller ──▶ MetaLearner │
│  └──────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.2 闭环核心原则

1. **持续性**：闭环永不停止，24/7 运行
2. **自反性**：输出影响输入，历史影响未来
3. **收敛性**：通过评估和纠错，系统能力持续提升

---

## 2. 感知层 (Perception)

### 2.1 感知流程

```
原始输入 ──▶ Extractor ──▶ 实体识别 ──▶ 关系抽取 ──▶ 知识三元组
     │
     ▼
GlossaryEngine ──▶ 术语解析 ──▶ 标准概念
     │
     ▼
ChunkingEngine ──▶ 语义分块 ──▶ 向量嵌入
```

### 2.2 感知输出

```python
@dataclass
class PerceptionResult:
    """感知结果数据结构"""
    # 提取的实体
    entities: List[Entity]
    # 抽取的关系
    relations: List[Relation]
    # 识别的领域
    domain: str
    # 置信度
    confidence: float
    # 来源文本
    source_text: str
```

### 2.3 感知策略

| 输入类型 | 感知策略 | 说明 |
|---------|---------|------|
| 文本 | LLM + 正则 | LLM 提取结构化知识，正则补充格式化内容 |
| 结构化数据 | 规则映射 | 映射为三元组格式 |
| 交互记录 | 行为分析 | 从成功/失败案例中提取模式 |

---

## 3. 学习层 (Learning)

### 3.1 学习类型

| 类型 | 输入 | 输出 | 使用场景 |
|-----|------|------|---------|
| **文本学习** | 文本 | LogicPattern | 文档、知识库、规则文档 |
| **结构化学习** | 三元组列表 | Rule | 已有知识图谱、数据库 |
| **交互学习** | 行为历史 | Policy | 用户反馈、测试结果 |
| **迁移学习** | 领域 A 规则 | 领域 B 规则 | 跨领域知识复用 |

### 3.2 学习策略选择

```python
def _select_learning_strategy(self, input_type: str, domain: str) -> str:
    """
    根据输入类型和领域选择最佳学习策略
    
    策略选择优先级:
    1. 如果是文本输入 + LLM 可用 → llm_extraction（最高效）
    2. 如果是文本输入 + LLM 不可用 → pattern_extraction（正则降级）
    3. 如果是结构化数据 → rule_discovery（关联规则挖掘）
    4. 如果是交互历史 → interaction_learning（策略学习）
    """
```

### 3.3 规则发现算法

#### 3.3.1 传递性规则发现

```
发现规则: IF A-[pred1]->B AND B-[pred2]->C THEN A-[pred2]->C

示例:
IF 调压箱A is_a 燃气调压箱
AND 燃气调压箱 is_a 燃气设备
THEN 调压箱A is_a 燃气设备
```

#### 3.3.2 分类规则发现

```
发现规则: IF 所有 X 都是 Y AND Y 有属性 P THEN X 也有属性 P

示例:
IF 所有燃气设备都需要维护
AND 维护有周期属性
THEN 自动发现: 维护周期规则
```

#### 3.3.3 继承规则发现

```
发现规则: IF X is_a Y AND Y has_property P THEN X has_property P

示例:
IF 调压箱 is_a 燃气设备
AND 燃气设备 有属性 压力范围
THEN 调压箱 有属性 压力范围
```

---

## 4. 推理层 (Reasoning)

### 4.1 推理类型

| 类型 | 说明 | 应用场景 |
|-----|------|---------|
| **前向链** | 从已知事实出发，应用规则直到目标 | 知识扩展、问答 |
| **后向链** | 从目标出发，反向寻找支撑事实 | 诊断、调试 |
| **混合推理** | 结合前向和后向 | 复杂推理场景 |

### 4.2 推理引擎架构

```
┌─────────────────────────────────────────────────┐
│                   推理请求输入                     │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              前提验证 (Premise Validation)        │
│  • 检查事实是否存在                               │
│  • 检查置信度是否满足阈值                          │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              规则匹配 (Rule Matching)              │
│  • 找出所有满足前提的规则                          │
│  • 按置信度排序                                   │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              冲突检测 (Contradiction Check)       │
│  • 检查新结论是否与已有知识冲突                     │
│  • SelfCorrection 介入                           │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              置信度传播 (Confidence Propagation)   │
│  • 计算结论置信度                                  │
│  • rule_confidence × premise_confidence           │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│                   推理结果输出                     │
│  • 结论列表                                       │
│  • 推理链（可解释性）                              │
│  • 置信度                                         │
└─────────────────────────────────────────────────┘
```

---

## 5. 评估层 (Evaluation)

### 5.1 评估维度

| 维度 | 指标 | 评估方法 |
|-----|------|---------|
| **学习质量** | 模式产出率、平均置信度、使用率 | SelfEvaluator.evaluate_learning_quality |
| **规则有效性** | Precision、Recall、F1 | SelfEvaluator.evaluate_rule_quality |
| **推理准确性** | 推理正确率、漏检率 | SelfEvaluator.evaluate_reasoning_accuracy |
| **系统健康** | 模块可用性、响应时间、错误率 | SelfEvaluator.evaluate_system_health |

### 5.2 评估触发时机

```python
# 评估触发时机
EVALUATION_TRIGGERS = {
    "after_learning": True,      # 学习完成后评估
    "after_reasoning": True,    # 推理完成后评估
    "periodic": "0 2 * * *",    # 每日凌晨2点定时评估
    "manual": True,             # 手动触发
}
```

---

## 6. 纠错层 (Correction)

### 6.1 纠错类型

| 类型 | 说明 | 触发条件 |
|-----|------|---------|
| **事实冲突** | 新事实与已有事实矛盾 | ContradictionChecker |
| **规则冲突** | 新规则与已有规则矛盾 | SelfCorrection.detect_rule_conflicts |
| **推理失败** | 推理结果被验证为错误 | SelfEvaluator 报告 |
| **置信度漂移** | 置信度与实际不符 | 多次预测 vs 实际结果对比 |

### 6.2 纠错流程

```
推理失败/冲突 ──▶ 记录失败案例 ──▶ 分析失败原因
                        │
                        ▼
              ┌─────────────────────┐
              │     纠错策略选择     │
              └─────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   置信度调整      规则修改        规则废弃
   (下调)          (补充条件)      (标记失效)
        │               │               │
        └───────────────┴───────────────┘
                        │
                        ▼
                 MetaLearner 回流
                        │
                        ▼
                 重新学习类似场景
```

---

## 7. 技能蒸馏 (Skill Distillation)

### 7.1 技能蒸馏流程

```
情节记忆 ──▶ 成功案例筛选 ──▶ 模式提取
   │              │                │
   │              ▼                ▼
   │      成功率统计 ───▶ 高价值案例
   │              │
   │              ▼
   └──────▶ LLM 分析 ──▶ 技能模板生成
                             │
                             ▼
                      Skill Library 存储
```

### 7.2 技能模板格式

```python
@dataclass
class Skill:
    """可执行技能模板"""
    id: str                           # 技能唯一标识
    name: str                         # 技能名称
    description: str                  # 技能描述
    skill_type: SkillType             # 技能类型
    content: str                      # 技能内容 (Markdown 或 Python)
    trigger_conditions: List[Dict]   # 触发条件
    parameters: List[Parameter]       # 参数定义
    success_rate: float              # 历史成功率
    usage_count: int                 # 使用次数
    version: int                    # 版本号
```

---

## 8. 完整进化闭环示例

### 8.1 场景：燃气设备安全检查

```python
# Step 1: 感知 - 从文本学习新规则
text = "燃气调压箱的出口压力必须 ≤ 0.4MPa，否则有爆炸风险。"
result = meta_learner.learn(text, input_type="text")
# → 提取出规则: pressure ≤ 0.4MPa

# Step 2: 学习结果存入 LogicLayer
# → pattern: LogicPattern(id="learned:gas_safety:pressure")
# → domain: gas_equipment
# → confidence: 0.85

# Step 3: 推理 - 检查新设备
new_fact = Fact(subject="调压箱X", predicate="出口压力", object="0.5MPa")
reasoner.add_fact(new_fact)
result = reasoner.forward_chain()
# → 结论: 调压箱X 存在爆炸风险 (confidence: 0.72)

# Step 4: 评估 - 推理结果评估
eval_result = self_evaluator.evaluate_reasoning_accuracy(...)
# → accuracy: 0.95 (因为规则来自权威文档)

# Step 5: 如果推理被验证错误
# → SelfCorrection 检测冲突
# → 记录失败案例
# → MetaLearner 回流重学
```

---

## 9. 版本管理

### 9.1 Pattern 版本控制

```python
# 每个 LogicPattern 都有版本号
pattern = LogicPattern(
    id="rule:gas_safety:pressure",
    version=1,
    ...
)

# 当规则被更新时
# 1. 创建新版本
new_pattern = pattern.new_version(
    conditions=[...],  # 更严格的条件
    confidence=0.9     # 更新置信度
)

# 2. 保存历史版本
logic_layer.add_pattern(new_pattern)  # version=2
# → 旧版本 (version=1) 自动归档

# 3. 可随时回滚
logic_layer.rollback_pattern("rule:gas_safety:pressure", version=1)
```

### 9.2 版本历史查询

```python
# 查询规则的所有版本
versions = logic_layer.get_pattern_history("rule:gas_safety:pressure")
# → [version=1, version=2, version=3]

# 查看版本差异
diff = logic_layer.compare_versions("rule:gas_safety:pressure", v1=1, v2=2)
# → 显示两个版本的差异
```

---

## 10. 监控与告警

### 10.1 监控指标

```python
EVOLUTION_METRICS = {
    # 学习指标
    "learning.episodes.total": "学习总次数",
    "learning.episodes.success_rate": "学习成功率",
    "learning.patterns.created": "新增模式数",
    "learning.patterns.updated": "更新模式数",
    
    # 推理指标
    "reasoning.inferences.total": "推理总次数",
    "reasoning.inferences.success_rate": "推理成功率",
    "reasoning.latency.p95": "P95 推理延迟",
    
    # 评估指标
    "evaluation.accuracy": "准确率",
    "evaluation.false_positives": "误报数",
    "evaluation.false_negatives": "漏报数",
    
    # 纠错指标
    "correction.conflicts.detected": "检测到的冲突数",
    "correction.patterns.rolled_back": "回滚的规则数",
}
```

### 10.2 告警规则

```python
ALERT_RULES = {
    # 告警规则
    "learning_success_rate_below_0.5": {
        "condition": "learning.episodes.success_rate < 0.5",
        "severity": "warning",
        "action": "触发 MetaLearner 策略调整"
    },
    "reasoning_latency_above_5s": {
        "condition": "reasoning.latency.p95 > 5",
        "severity": "critical",
        "action": "触发性能优化"
    },
    "conflict_rate_above_0.1": {
        "condition": "correction.conflicts.detected / reasoning.total > 0.1",
        "severity": "critical",
        "action": "触发 SelfCorrection 全面检查"
    },
}
```

---

**下一步**：[docs/architecture/architecture.md](architecture/architecture.md) — 查看完整的架构设计
