# Dev.to 技术博客 #3

## 让 Agent 在运行中学习：本体论驱动的新范式

**标签**: Agent Architecture, Runtime Learning, Ontology, Python, AI Engineering  
**预计阅读时间**: 9 分钟  
**代码示例**: Python, 完整可运行

---

## 序言：什么是"运行中学习"？

想象这样一个场景：

> 凌晨 2 点，你的采购 Agent 发现供应商 C 的缺陷率突然上升了。它按照现有规则打了"黄色预警"。
>
> 但第二天早上，资深采购员王工看了一眼，说："这个供应商 C，最近换了一个原材料批次，这条预警应该直接标红色。"他手动更新了供应商评级。
>
> 现在问题来了：**你的 Agent 如何"学会"王工的判断？**

传统方案：
- 记录这条反馈 → 等下次模型更新时微调 → 3 个月后生效

本体论方案：
- 王工添加一条规则 → Agent 下一次推理立即使用 → **5 分钟后生效**

这就是"运行中学习"（Runtime Learning）——不是在训练集中学习，而是在知识图谱中学习。

---

## 1. 重新理解"学习"和"推理"

在传统 ML 系统中，"学习"和"推理"是两个严格分离的阶段：

```
学习阶段：训练数据 → 模型权重（离线，耗时）
推理阶段：输入 → 模型 → 输出（在线，毫秒级）
```

这套范式在分类、预测类任务上效果很好。但对于**需要可解释性、持续更新、跨领域知识整合**的场景，它有几个根本问题：

1. **学习成本高**：更新知识需要重新训练
2. **推理不可解释**：模型决策无法追踪到具体规则
3. **知识无法共享**：一个模型学到的，其他模型无法直接使用

本体论驱动的方法，重新定义了学习和推理的关系：

```
知识库（Knowledge Graph） ←→ 推理引擎（Reasoning Engine）
         ↑                       ↓
    学习新规则              应用规则推理
    （在线，秒级）          （在线，毫秒级）
```

学习的结果不是"更新了模型权重"，而是**在知识图谱中添加了一条新的边或规则**。

---

## 2. 运行时学习的实际实现

让我们看一个完整的例子——一个供应链风险评估 Agent，如何在运行中学习新规则。

### 场景设定

一个 Agent 在监控 50 个供应商。第一周，它运行得不错。但到了第二周，它漏报了一个风险——供应商 D 突然被一家大客户拖欠款项，导致资金链紧张，但这个信息没有进入 Agent 的知识库。

我们用三个步骤来修复这个问题：

### 步骤 1：识别知识缺口（Meta-cognition）

```python
from ontology_platform import OntologyEngine

ontology = OntologyEngine(domain="procurement")

# Agent 尝试推理
result = ontology.reason(
    query="供应商 D 的财务风险等级是多少？",
    reasoning_type="causal",
    trace=True
)

# Agent 检测到自己的知识不足
print(f"置信度: {result.confidence}")  # → 0.31

if result.confidence < 0.60:
    print(f"[元认知] 置信度不足，我缺少关键数据")
    print(f"[元认知] 知识空白: {result.meta_cognition['knowledge_gaps']}")
    # → ['供应商_D_财务数据', '供应商_D_客户信用记录']

    print(f"[元认知] 建议: {result.suggestions}")
    # → ['补充供应商 D 的财务报表', '接入企业征信数据源']
```

Agent 主动暴露了自己的知识边界。这不是失败——这是元认知能力的体现。

### 步骤 2：注入新知识（Runtime Learning）

王工来补充数据了。他不需要训练模型，只需要把知识告诉 Agent：

```python
# 王工添加供应商 D 的财务数据
ontology.assert_fact({
    "entity": "Supplier_D",
    "type": "Supplier",
    "properties": {
        "financial_health_score": 0.45,  # 低分表示财务风险
        "payment_history": "delayed",
        "client_concentration": 0.78  # 78% 收入依赖单一客户
    }
})

# 王工添加一条规则：这是他 20 年采购经验总结出来的
ontology.learn(
    from_source="procurement_expert_wang",
    content="当供应商的 financial_health_score < 0.50 且 client_concentration > 0.70 时，
            该供应商的合同应标记为 HIGH_RISK，应立即启动备选供应商评估",
    confidence=0.96,
    source_type="expert_domain_knowledge",
    evidence=["案例1: 供应商 X（2024年违约）", "案例2: 供应商 Y（2025年延期）"]
)

print("新规则已学习并立即生效")
```

注意这里的 `evidence` 字段：这是本体论系统比纯规则引擎更强大的地方——每条规则都可以有**来源追踪**，知道这条规则是谁的经验、基于哪些案例。

### 步骤 3：新推理结果（立即生效）

```python
# 现在 Agent 用新规则重新推理
result = ontology.reason(
    query="供应商 D 的风险等级和合同建议？",
    reasoning_type="causal",
    trace=True
)

print(f"置信度: {result.confidence}")  # → 0.91（从 0.31 提升）
print(f"风险等级: {result.risk_level}")  # → HIGH_RISK
print(f"触发规则: {result.matched_rules}")
# → ['financial_risk_rule', 'client_concentration_rule', 'combined_risk']

print(f"\n推理链:")
for step in result.reasoning_chain:
    print(f"  → {step}")

# 输出:
#  → Supplier_D financial_health_score = 0.45 (< 0.50)
#  → Rule "financial_risk_rule" triggered: score < 0.50 → HIGH_RISK
#  → Supplier_D client_concentration = 0.78 (> 0.70)
#  → Rule "client_concentration_rule" triggered: high concentration → additional risk
#  → Combined assessment: HIGH_RISK (置信度 0.91)
#  → Recommendation: 立即启动备选供应商评估
```

**关键点：整个过程从"发现问题"到"解决问题"不到 5 分钟。Agent 没有重新训练，但它拥有了新的推理能力。**

---

## 3. 规则学习的类型

不是所有知识都需要用同一种方式学习。ontology-platform 支持多种学习模式：

### 3.1 专家知识（Expert Knowledge）

```python
ontology.learn(
    from_source="domain_expert",
    content="规则内容...",
    confidence=0.95,  # 专家知识，高置信度
    source_type="expert_rule"
)
```

### 3.2 从错误中学习（Learning from Errors）

```python
# 当 Agent 的预测与实际不符时
ontology.learn_from_error(
    prediction="Supplier_E is LOW_RISK (conf: 0.72)",
    actual_outcome="Supplier_E defaulted after 30 days",
    lesson="当供应商的合作年限 < 2年 且 financial_health_score < 0.60 时，
           即使置信度 > 0.7 也应标记为 HIGH_RISK",
    source_type="production_error"
)
```

### 3.3 从数据中发现模式（Pattern Discovery）

```python
# 自动分析历史数据，发现新规则
discovered_rules = ontology.discover_patterns(
    from_data="historical_supplier_data.csv",
    target_variable="defaulted",
    min_support=0.15,  # 至少 15% 的样本支持
    min_confidence=0.80,
    max_rules=10
)

for rule in discovered_rules:
    print(f"Discovered: {rule['condition']} → {rule['conclusion']}")
    print(f"  Confidence: {rule['confidence']}, Support: {rule['support']}")
```

### 3.4 从外部知识库同步（External KB Sync）

```python
# 定期从企业知识库同步
ontology.sync_from_kb(
    source="corporate_kb",
    entities=["Supplier_*", "Contract_*"],
    sync_type="incremental",  # 只同步新增/修改的
    schedule="daily"
)
```

---

## 4. 冲突检测：知识的一致性维护

运行时学习最大的风险之一：**新规则与旧规则冲突**。

比如：

- 旧规则："准时率 > 0.90 → 供应商优秀"
- 新规则："准时率 > 0.90 但缺陷率 > 0.05 → 供应商需评估"

这两个规则本身不冲突，但如果数据变了呢？

ontology-platform 内置了**冲突检测机制**：

```python
ontology.learn(
    from_source="new_buyer",
    content="准时率 > 0.95 的供应商无需质量审核",
    confidence=0.88,
    source_type="new_policy"
)

# 检测是否与现有规则冲突
conflicts = ontology.detect_conflicts(new_rule="delivery_only_quality")

if conflicts:
    print("[元认知] 检测到规则冲突:")
    for conflict in conflicts:
        print(f"  冲突规则: {conflict['existing_rule']}")
        print(f"  冲突原因: {conflict['reason']}")
        print(f"  建议处理: {conflict['resolution_suggestion']}")
        # → 建议: 新规则作为补充条件，而非替代原有质量评估

    # Agent 自动调整置信度
    adjusted_confidence = ontology.adjust_confidence_for_conflict(
        original=0.88,
        conflicts=conflicts
    )
    print(f"[元认知] 规则置信度调整为: {adjusted_confidence}")
```

---

## 5. 知识版本控制：可回滚的学习

企业场景下，有时候新规则会导致意外结果。需要能够回滚：

```python
# 查看知识版本历史
history = ontology.knowledge_history(
    entity="Supplier_D",
    since="2026-01-01"
)

for entry in history:
    print(f"{entry['timestamp']}: {entry['change_type']}")
    print(f"  {entry['content']}")
    print(f"  Added by: {entry['source']}, confidence: {entry['confidence']}")

# 回滚到指定版本
ontology.rollback(rule_id="rule_003", reason="导致误报供应商 E")

# 现在 Supplier_E 的推理回到之前的状态
result = ontology.reason(query="供应商 E 风险？")
print(f"置信度: {result.confidence}")  # → 回到了回滚前的值
```

---

## 6. 多 Agent 共享知识图谱

当多个 Agent 协作时，它们可以共享同一个知识图谱——一个 Agent 学到的东西，立即对其他 Agent 可用：

```python
from ontology_platform import SharedOntology

# 创建一个所有 Agent 共享的本体
shared = SharedOntology(domain="enterprise_procurement")

# 多个专业化 Agent 接入同一个知识图谱
pricing_agent = Agent(role="pricing", ontology=shared)
procurement_agent = Agent(role="procurement", ontology=shared)
quality_agent = Agent(role="quality", ontology=shared)

# quality_agent 发现了一个质量问题
quality_agent.learn(
    from_source="quality_audit",
    content="供应商 F 最近 3 批货都有外观缺陷，建议降级",
    propagate=True,  # 自动传播给所有 Agent
    confidence=0.95
)

# pricing_agent 下一次推理时，自动知道供应商 F 的问题
result = pricing_agent.reason(
    query="是否应该给供应商 F 降价谈判？",
    reasoning_type="logical"
)

print(result.reasoning_chain)
# → [..., "Supplier_F quality_issue detected 2026-03-24", 
#    "Pricing negotiation should include quality improvement clause", ...]
```

---

## 结语

运行中学习，是本体论驱动 Agent 和传统 RAG Agent 的本质区别。

RAG Agent 说：**"我记得类似的情况"**  
本体论 Agent 说：**"我学会了这条规则，它解释了为什么这种情况重要"**

这不是一个技术细节。这是一个架构选择——选择把知识表示为可推理的结构，而不是可检索的碎片。

如果你也在构建企业级 Agent，并且需要：
- 持续学习新规则而不重新训练
- 可追溯的推理过程
- 置信度感知和元认知能力

试试 ontology-platform。

---

## 快速开始

```bash
pip install ontology-platform
```

```python
from ontology_platform import OntologyEngine

ontology = OntologyEngine(domain="test")

ontology.assert_fact({
    "entity": "Test", "type": "Example",
    "properties": {"value": 1}
})

ontology.define_rule(
    "test_rule",
    condition=lambda x: x["value"] < 5,
    conclusion="值小于5，规则触发"
)

result = ontology.reason(
    query="What is the test value?",
    reasoning_type="logical",
    trace=True
)

print(f"Confidence: {result.confidence}")
print(f"Reasoning: {result.reasoning_chain}")
```

**GitHub**: https://github.com/wu-xiaochen/ontology-platform

---

*你在 Agent 中如何处理"运行时学习"？有什么好的实践经验？*
