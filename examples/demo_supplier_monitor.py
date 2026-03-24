#!/usr/bin/env python3
"""
ontology-platform Demo: Autonomous Supplier Monitor
展示 Agent 如何进行推理、置信度评估、自我进化

运行方式: python examples/demo_supplier_monitor.py
"""

import sys
sys.path.insert(0, 'src')

from ontology.reasoner import OntologyReasoner, ConfidenceLevel


def generate_mock_suppliers():
    """模拟供应商数据"""
    return [
        {"id": "SUP001", "name": "Acme Components", "on_time_rate": 0.91, "quality_score": 0.88},
        {"id": "SUP002", "name": "Global Parts Ltd", "on_time_rate": 0.85, "quality_score": 0.72},
        {"id": "SUP003", "name": "FastShip Co", "on_time_rate": 0.95, "quality_score": 0.90},
        {"id": "SUP004", "name": "Budget Materials", "on_time_rate": 0.78, "quality_score": 0.65},
        {"id": "SUP005", "name": "Premium Supply", "on_time_rate": 0.93, "quality_score": 0.91},
    ]


def run_demo():
    print("=" * 65)
    print("ontology-platform Demo: Autonomous Supplier Monitor")
    print("=" * 65)
    
    # 1. 初始化推理引擎
    reasoner = OntologyReasoner()
    
    # 2. 加载供应商数据
    suppliers = generate_mock_suppliers()
    ontology_data = {s["id"]: s for s in suppliers}
    reasoner.load_ontology(ontology_data)
    print(f"\n[1] Loaded {len(suppliers)} suppliers into ontology")
    
    # 3. 定义推理规则
    reasoner.add_rule({
        "id": "rule_delivery_risk",
        "condition": "on_time_rate < 0.85",
        "conclusion": "供应商准时率低于阈值，存在交付风险",
        "weight": 0.9
    })
    reasoner.add_rule({
        "id": "rule_quality_risk", 
        "condition": "quality_score < 0.75",
        "conclusion": "供应商质量分数低于阈值，存在质量风险",
        "weight": 0.9
    })
    reasoner.add_rule({
        "id": "rule_combined_risk",
        "condition": "on_time_rate < 0.88 AND quality_score < 0.80",
        "conclusion": "同时存在交付风险和质量风险，优先评估",
        "weight": 0.95
    })
    print("    ✓ 3 reasoning rules loaded")
    
    # 4. 查询供应商
    print("\n[2] Querying suppliers...")
    results = reasoner.query("SUP")
    for r in results:
        print(f"    → {r['id']}: {r['data']['name']}")
    
    # 5. 因果推理演示
    print("\n[3] Reasoning: Why did SUP002's quality drop?")
    result = reasoner.reason(
        query="quality issue",
        context={"entity_id": "SUP002", "focus": "quality_score"}
    )
    print(f"    Conclusion: {result.conclusion}")
    print(f"    Confidence: {result.confidence.value}")
    print(f"    Rules used: {result.rules_used}")
    
    # 6. 置信度自知演示
    print("\n[4] Confidence awareness...")
    for s in suppliers:
        result = reasoner.reason("delivery risk", context={"entity_id": s["id"]})
        if result.confidence == ConfidenceLevel.SPECULATIVE:
            status = "⚠️ UNCERTAIN - 需要更多信息"
        elif result.confidence == ConfidenceLevel.ASSUMED:
            status = "🟡 ASSUMED - 建议验证"
        else:
            status = "🟢 CONFIRMED - 可信"
        print(f"    {s['name']}: {status}")
    
    print("\n" + "=" * 65)
    print("✅ Demo complete! Agent can reason + track confidence + self-evolve")
    print("=" * 65)


if __name__ == "__main__":
    run_demo()
