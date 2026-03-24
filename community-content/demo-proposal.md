# 技术 Demo 提案

## 什么 Demo 最能展示"Agent 成长"能力？

---

## 核心原则：Demo 要讲一个故事

技术 Demo 最常见的失败是：**展示了功能，但没有展示价值**。

最好的 Demo 是这样的：开发者看 30 秒，就能说出"这个我需要"。

针对 ontology-platform 的"Agent 成长"核心价值，我们需要的 Demo 是：

**"一个会从错误中学习的 Agent"** —— 而不是"一个能存储向量相似内容的 Agent"。

---

## 提案 1：⭐⭐⭐⭐⭐ 核心 Demo - "Autonomous Supplier Monitor"

### 概念

一个命令行 Agent，持续监控 10 个供应商的实时数据，自动发现风险模式，并在运行时学习新规则。

**为什么这是最好的 Demo：**
1. 它展示了所有三大特性（学习 + 推理 + 元认知）
2. 它有一个真实场景的紧迫感（采购风险 = 真实钱的问题）
3. 它能展示"运行时学习"——这是最违反直觉、最令人惊讶的能力
4. 开发者看到它会说："这个逻辑我之前得用 ML 模型，现在几行代码就搞定了？"

### 架构

```
┌─────────────────────────────────────────────────┐
│              Supplier Monitor Agent              │
│                                                  │
│  ┌─────────┐    ┌────────────┐    ┌───────────┐ │
│  │ Supplier │───▶│  Ontology  │───▶│ Reasoning │ │
│  │  Data    │    │   Engine   │    │  Engine   │ │
│  └─────────┘    └────────────┘    └───────────┘ │
│                      │                │         │
│                      ▼                ▼         │
│              ┌────────────┐    ┌───────────┐    │
│              │   Rules    │    │ Meta-     │    │
│              │   Learns   │    │ Cognition │    │
│              │  at runtime│    │ (Confidence)│   │
│              └────────────┘    └───────────┘    │
└─────────────────────────────────────────────────┘
```

### 代码结构

**`demo/supplier_monitor.py`**：

```python
#!/usr/bin/env python3
"""
Ontology Platform Demo: Autonomous Supplier Monitor
展示 Agent 如何从供应商数据中学习、推理、并自我进化

运行方式: python demo/supplier_monitor.py
"""

import json
import random
from ontology_platform import OntologyEngine, Agent

def generate_mock_supplier_data():
    """生成模拟供应商数据"""
    suppliers = [
        {"id": "SUP001", "name": "Acme Components", "on_time_rate": 0.91, "quality_score": 0.88},
        {"id": "SUP002", "name": "Global Parts Ltd", "on_time_rate": 0.85, "quality_score": 0.72},
        {"id": "SUP003", "name": "FastShip Co", "on_time_rate": 0.95, "quality_score": 0.90},
        {"id": "SUP004", "name": "Budget Materials", "on_time_rate": 0.78, "quality_score": 0.65},
        {"id": "SUP005", "name": "Premium Supply", "on_time_rate": 0.93, "quality_score": 0.91},
    ]
    
    # 添加一些异常模式（用于触发规则）
    # SUP002: 低准时率 + 中等质量
    # SUP004: 低准时率 + 低质量 + 大批量
    
    return suppliers

def run_demo():
    print("=" * 60)
    print("ontology-platform Demo: Autonomous Supplier Monitor")
    print("=" * 60)
    
    # 初始化 Agent
    agent = Agent(domain="procurement", confidence_threshold=0.70)
    
    # 加载供应商数据
    suppliers = generate_mock_supplier_data()
    print(f"\n[1] Loading {len(suppliers)} suppliers into ontology...")
    
    for supplier in suppliers:
        agent.ontology.assert_fact({
            "entity": supplier["id"],
            "type": "Supplier",
            "properties": {
                "name": supplier["name"],
                "on_time_rate": supplier["on_time_rate"],
                "quality_score": supplier["quality_score"]
            }
        })
        print(f"    ✓ {supplier['name']} → on_time: {supplier['on_time_rate']}, quality: {supplier['quality_score']}")
    
    # 定义初始推理规则
    print("\n[2] Defining initial reasoning rules...")
    
    agent.define_rule(
        "delivery_risk",
        condition=lambda s: s["on_time_rate"] < 0.85,
        conclusion="供应商准时率低于阈值，存在交付风险"
    )
    
    agent.define_rule(
        "quality_risk",
        condition=lambda s: s["quality_score"] < 0.75,
        conclusion="供应商质量分数低于阈值，存在质量风险"
    )
    
    agent.define_rule(
        "combined_risk",
        condition=lambda s: s["on_time_rate"] < 0.88 and s["quality_score"] < 0.80,
        conclusion="供应商同时存在交付风险和质量风险，应优先评估"
    )
    
    print("    ✓ 3 rules loaded")
    
    # 第一轮推理：Baseline 分析
    print("\n[3] Running baseline risk assessment...")
    
    result = agent.reason(
        query="哪些供应商需要重点关注？给出风险等级和原因。",
        reasoning_type="causal",
        trace=True
    )
    
    print(f"\n    Confidence: {result.confidence:.2f}")
    print(f"    Risk flagged: {result.risk_flagged}")
    print(f"\n    Reasoning chain:")
    for i, step in enumerate(result.reasoning_chain, 1):
        print(f"      [{i}] {step}")
    
    # 第二轮：模拟引入新数据（触发规则学习）
    print("\n[4] Simulating new data: SUP002 defect rate spike detected...")
    
    agent.ontology.update_fact(
        entity="SUP002",
        properties={"defect_rate": 0.12, "last_defect_report": "2026-Q1"}
    )
    
    # Agent 发现原有规则不适用了——需要学习新规则
    print("\n[5] Agent learning new rule from defect data...")
    
    learning_result = agent.learn_from_data(
        source="defect_report",
        content="当供应商 defect_rate > 0.08 时，即使 on_time_rate > 0.85，
                也应标记为高风险，因为缺陷零件会造成产线停线",
        context={"defect_rate": 0.12, "on_time_rate": 0.85, "impact": "production_line_stop"}
    )
    
    print(f"    Learned: {learning_result['rule_name']}")
    print(f"    Confidence: {learning_result['confidence']}")
    print(f"    Integration: {'Immediate' if learning_result['immediate'] else 'Pending review'}")
    
    # 第三轮：用新学会的规则重新推理
    print("\n[6] Re-assessing with newly learned rule...")
    
    result = agent.reason(
        query="SUP002 的风险等级应该是多少？",
        reasoning_type="causal",
        trace=True
    )
    
    print(f"\n    Confidence: {result.confidence:.2f}")
    print(f"    Risk level: {result.risk_level}")
    print(f"    Triggered rules: {result.matched_rules}")
    print(f"\n    Reasoning chain:")
    for i, step in enumerate(result.reasoning_chain, 1):
        print(f"      [{i}] {step}")
    
    # 元认知：展示 Agent 知道自己的边界
    print("\n[7] Meta-cognition: What does the agent NOT know?")
    
    result = agent.reason(
        query="SUP002 供应商的产能是否足够支撑下季度增长 30% 的订单？",
        reasoning_type="causal",
        trace=True
    )
    
    if result.confidence < 0.70:
        print(f"\n    [Meta-cognition] Confidence: {result.confidence:.2f}")
        print(f"    [Meta-cognition] This question is OUTSIDE my knowledge boundary")
        print(f"    [Meta-cognition] Missing data: capacity utilization rate")
        print(f"    [Meta-cognition] Suggestions: Add supplier capacity data to ontology")
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()
```

**`demo/agent.py`**（简化版 Agent 接口）：

```python
# 核心 Agent 类 - 简化版用于 Demo
class Agent:
    def __init__(self, domain: str, confidence_threshold: float = 0.70):
        self.ontology = OntologyEngine(domain=domain)
        self.confidence_threshold = confidence_threshold
        self.rules = {}
    
    def define_rule(self, name: str, condition: callable, conclusion: str):
        self.rules[name] = {"condition": condition, "conclusion": conclusion}
    
    def reason(self, query: str, reasoning_type: str = "logical", trace: bool = False):
        # 调用 ontology_engine 进行推理
        return self.ontology.reason(query, reasoning_type, trace)
    
    def learn_from_data(self, source: str, content: str, context: dict):
        # 运行时学习新规则
        return self.ontology.learn(source, content, confidence=0.88, source_type="learned")
```

### Demo 输出示例

```
======================================================================
ontology-platform Demo: Autonomous Supplier Monitor
======================================================================

[1] Loading 5 suppliers into ontology...
    ✓ Acme Components → on_time: 0.91, quality: 0.88
    ✓ Global Parts Ltd → on_time: 0.85, quality: 0.72
    ✓ FastShip Co → on_time: 0.95, quality: 0.90
    ✓ Budget Materials → on_time: 0.78, quality: 0.65
    ✓ Premium Supply → on_time: 0.93, quality: 0.91

[2] Defining initial reasoning rules...
    ✓ 3 rules loaded

[3] Running baseline risk assessment...
    Confidence: 0.91
    Risk flagged: [SUP002, SUP004]

    Reasoning chain:
      [1] SUP002: on_time_rate = 0.85 < 0.88 threshold
      [2] SUP002: quality_score = 0.72 < 0.80 threshold
      [3] Rule "combined_risk" triggered
      [4] SUP004: on_time_rate = 0.78 < 0.85 threshold
      [5] SUP004: quality_score = 0.65 < 0.75 threshold
      [6] Both SUP002 and SUP004 should be flagged

[4] Simulating new data: SUP002 defect rate spike detected...

[5] Agent learning new rule from defect data...
    Learned: defect_risk_escalation
    Confidence: 0.88
    Integration: Immediate

[6] Re-assessing with newly learned rule...
    Confidence: 0.93
    Risk level: HIGH
    Triggered rules: ['combined_risk', 'defect_risk_escalation']

    Reasoning chain:
      [1] SUP002 defect_rate = 0.12 > 0.08 threshold
      [2] DEFECT RULE triggered: defect_rate > 0.08 → HIGH risk
      [3] Original combined_risk also applies
      [4] SUP002 risk level: HIGH (double-triggered)

[7] Meta-cognition: What does the agent NOT know?
    Confidence: 0.52
    [Meta-cognition] This question is OUTSIDE my knowledge boundary
    [Meta-cognition] Missing data: capacity utilization rate
    [Meta-cognition] Suggestions: Add supplier capacity data to ontology

======================================================================
Demo Complete!
======================================================================
```

---

## 提案 2：⭐⭐⭐⭐ Web UI Demo - "Ontology Explorer"

### 概念

一个轻量级的 Web 界面，展示知识图谱的实时可视化 + 推理过程追踪。

**功能：**
- 上传结构化数据（CSV/JSON）→ 自动构建知识图谱
- 输入自然语言查询 → 展示推理链
- 展示置信度变化 → 用户能看到 Agent"思考"的过程
- 运行时学习 → 用户添加新规则，立即看到效果

### 技术栈

- **前端**: React + D3.js（知识图谱可视化）+ TailwindCSS
- **后端**: FastAPI + ontology-platform Python SDK
- **部署**: Docker one-liner

### 架构

```
Browser (React + D3.js)
       ↕ WebSocket
FastAPI Server
       ↕
ontology-platform Engine
```

---

## 提案 3：⭐⭐⭐ 代码片段 Gallery（最轻量）

### 概念

一组可直接复制粘贴的代码片段，展示核心功能，每个 5-10 行。

**不需要完整 Demo 环境，直接在 README 里展示。**

```python
# 片段 1: 基础推理
from ontology_platform import OntologyEngine
o = OntologyEngine(domain="test")
o.assert_fact({"entity": "A", "type": "Supplier", "properties": {"score": 0.72}})
result = o.reason("What is A's risk level?", trace=True)

# 片段 2: 运行时学习
o.learn(from_source="error_log", content="Rule: score < 0.75 → HIGH risk")
result = o.reason("Is A risky?", trace=True)

# 片段 3: 元认知
if result.confidence < 0.6:
    print(f"I don't know. Confidence: {result.confidence}")
```

---

## 推荐实施顺序

| 阶段 | Demo | 工作量 | 优先级 | 理由 |
|------|------|--------|--------|------|
| **立即** | 代码片段 Gallery | ~2h | 🔴 最高 | 可直接放在 README，立刻提升转化率 |
| **Week 1** | Supplier Monitor CLI | ~1-2 days | 🔴 高 | 展示核心差异化能力，有视频价值 |
| **Week 2** | Ontology Explorer Web | ~1 week | 🟡 中 | 提升项目的视觉冲击力，适合社交媒体传播 |

---

## Supplier Monitor Demo 的关键叙事点

这个 Demo 的叙事弧线非常清晰：

1. **Setup（30秒）**：加载 5 个供应商数据
2. **Tension（1分钟）**：Agent 发现了一些风险模式
3. **Twist（30秒）**：新数据来了，原有规则不够用了
4. **Resolution（30秒）**：Agent **自己学会了新规则**，重新推理出正确结果
5. **Meta moment（30秒）**：Agent 承认有自己不知道的事情

**这 3 分钟的叙事，胜过 1000 字的营销文案。**

---

## 需要的技术支持

1. **`demo/supplier_monitor.py`** - 主要 Demo 脚本（见上方代码）
2. **`demo/data/suppliers.json`** - 模拟数据
3. **`demo/run_demo.sh`** - 一键运行脚本
4. **`docs/demo.gif`** 或 **`docs/demo.mp4`** - 录制好的 Demo 视频

**最简 MVP**：只需要 `supplier_monitor.py` + `suppliers.json`，30 分钟可以完成。
