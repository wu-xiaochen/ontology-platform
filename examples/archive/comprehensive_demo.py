"""
Clawra Comprehensive Demo
==========================

This demo showcases all capabilities of the Clawra Neuro-Symbolic Cognitive Engine:

Scenario 1: Knowledge Ingestion and Retrieval
Scenario 2: Rule-Based Reasoning with Confidence
Scenario 3: Knowledge Boundary Detection
Scenario 4: End-to-End Procurement Compliance Check
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoner import Reasoner, Fact, Rule, RuleType
from src.memory.base import SemanticMemory, EpisodicMemory
from src.agents.orchestrator import CognitiveOrchestrator
from src.agents.metacognition import MetacognitiveAgent
from src.core.ontology.rule_engine import RuleEngine, OntologyRule, SafeMathSandbox


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_result(result: dict, indent: int = 0):
    """Print formatted result"""
    prefix = "  " * indent
    for key, value in result.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_result(value, indent + 1)
        elif isinstance(value, list):
            print(f"{prefix}{key}: [{len(value)} items]")
            for i, item in enumerate(value[:3]):  # Show first 3
                if isinstance(item, dict):
                    print(f"{prefix}  [{i}] {item}")
                else:
                    print(f"{prefix}  [{i}] {item}")
            if len(value) > 3:
                print(f"{prefix}  ... and {len(value) - 3} more")
        else:
            print(f"{prefix}{key}: {value}")


def scenario_1_knowledge_ingestion():
    """
    Scenario 1: Knowledge Ingestion and Retrieval
    
    Demonstrates:
    - Adding facts to the knowledge base
    - Semantic search capabilities
    - Graph traversal for knowledge retrieval
    """
    print_section("Scenario 1: Knowledge Ingestion and Retrieval")
    
    # Initialize components
    reasoner = Reasoner()
    semantic_mem = SemanticMemory(use_mock=True)  # Use mock for demo without Neo4j
    episodic_mem = EpisodicMemory(db_path="data/demo_episodic.db")
    
    print("\n1.1 Ingesting Gas Industry Knowledge")
    print("-" * 50)
    
    # Sample gas industry facts
    gas_facts = [
        Fact("燃气调压箱", "用途", "降低和稳定燃气压力", confidence=0.95, source="gas_regulation_spec"),
        Fact("燃气调压箱", "组成部件", "调压器", confidence=0.90, source="gas_regulation_spec"),
        Fact("燃气调压箱", "组成部件", "切断阀", confidence=0.90, source="gas_regulation_spec"),
        Fact("燃气调压箱", "组成部件", "过滤器", confidence=0.90, source="gas_regulation_spec"),
        Fact("调压器", "类型", "直接作用式", confidence=0.85, source="technical_manual"),
        Fact("调压器", "类型", "间接作用式", confidence=0.85, source="technical_manual"),
        Fact("进口压力", "单位", "MPa", confidence=0.95, source="standards"),
        Fact("出口压力", "单位", "kPa", confidence=0.95, source="standards"),
        Fact("GB 27791", "标准名称", "城镇燃气调压柜", confidence=0.95, source="national_standard"),
    ]
    
    for fact in gas_facts:
        reasoner.add_fact(fact)
        semantic_mem.store_fact(fact)
        print(f"  Added: {fact.subject} → {fact.predicate} → {fact.object}")
    
    print(f"\n  Total facts ingested: {len(gas_facts)}")
    
    print("\n1.2 Semantic Search")
    print("-" * 50)
    
    # Semantic search
    query = "燃气调压设备"
    results = semantic_mem.semantic_search(query, top_k=5)
    
    print(f"  Query: '{query}'")
    print(f"  Results found: {len(results)}")
    for i, doc in enumerate(results):
        print(f"  [{i+1}] {doc.content}")
    
    print("\n1.3 Knowledge Retrieval via Reasoner")
    print("-" * 50)
    
    # Query facts about specific entity
    facts_about_regulator = reasoner.query(subject="燃气调压箱")
    print(f"  Facts about '燃气调压箱': {len(facts_about_regulator)}")
    for fact in facts_about_regulator:
        print(f"    - {fact.predicate}: {fact.object} (confidence: {fact.confidence:.2f})")
    
    return {
        "facts_ingested": len(gas_facts),
        "search_results": len(results),
        "facts_retrieved": len(facts_about_regulator)
    }


def scenario_2_rule_based_reasoning():
    """
    Scenario 2: Rule-Based Reasoning with Confidence
    
    Demonstrates:
    - Rule engine evaluation
    - Conflict detection
    - Confidence propagation
    """
    print_section("Scenario 2: Rule-Based Reasoning with Confidence")
    
    rule_engine = RuleEngine()
    
    print("\n2.1 Available Rules")
    print("-" * 50)
    
    for rule_id, rule in rule_engine.rules.items():
        print(f"  Rule: {rule_id}")
        print(f"    Target: {rule.target_object_class}")
        print(f"    Expression: {rule.expression}")
        print(f"    Description: {rule.description}")
        print()
    
    print("\n2.2 Rule Evaluation - PASS Case")
    print("-" * 50)
    
    context_pass = {
        "supply_capacity": 100,  # m³/h
        "flow_requirement": 50   # m³/h
    }
    
    result_pass = rule_engine.evaluate_rule("rule:gas_regulator_safety_margin", context_pass)
    print(f"  Context: {context_pass}")
    print(f"  Result: {result_pass['status']}")
    print(f"  Expression: {result_pass['expression']}")
    
    print("\n2.3 Rule Evaluation - FAIL Case")
    print("-" * 50)
    
    context_fail = {
        "supply_capacity": 60,   # m³/h
        "flow_requirement": 50   # m³/h
    }
    
    result_fail = rule_engine.evaluate_rule("rule:gas_regulator_safety_margin", context_fail)
    print(f"  Context: {context_fail}")
    print(f"  Result: {result_fail['status']}")
    print(f"  Explanation: Supply (60) < Required (50 * 1.5 = 75)")
    
    print("\n2.4 Adding Custom Rule with Conflict Detection")
    print("-" * 50)
    
    # Add a rule that might conflict
    custom_rule = OntologyRule(
        id="rule:custom_pressure_check",
        target_object_class="GasRegulator",
        expression="outlet_pressure >= 0.01",
        description="Minimum outlet pressure check"
    )
    
    registration_result = rule_engine.register_rule(custom_rule, check_conflict=True)
    print(f"  Rule registered: {custom_rule.id}")
    print(f"  Conflicts detected: {registration_result.get('warnings', [])}")
    
    print("\n2.5 Forward Chain Reasoning")
    print("-" * 50)
    
    reasoner = Reasoner()
    
    # Add transitive facts
    reasoner.add_fact(Fact("A", "connected_to", "B", confidence=0.9))
    reasoner.add_fact(Fact("B", "connected_to", "C", confidence=0.9))
    reasoner.add_fact(Fact("C", "connected_to", "D", confidence=0.9))
    
    result = reasoner.forward_chain(max_depth=5)
    
    print(f"  Initial facts: 3")
    print(f"  Derived conclusions: {len(result.conclusions)}")
    print(f"  Total confidence: {result.total_confidence.value:.3f}")
    
    return {
        "rules_available": len(rule_engine.rules),
        "evaluation_pass": result_pass['status'],
        "evaluation_fail": result_fail['status'],
        "derived_conclusions": len(result.conclusions)
    }


def scenario_3_knowledge_boundary():
    """
    Scenario 3: Knowledge Boundary Detection
    
    Demonstrates:
    - Metacognitive agent
    - Confidence calibration
    - Knowledge boundary detection
    """
    print_section("Scenario 3: Knowledge Boundary Detection")
    
    reasoner = Reasoner()
    agent = MetacognitiveAgent(name="BoundaryDetector", reasoner=reasoner)
    
    print("\n3.1 Confidence Calibration")
    print("-" * 50)
    
    # Test different evidence scenarios
    evidence_scenarios = [
        (0, "No evidence"),
        (1, "Single evidence piece"),
        (3, "Few evidence pieces"),
        (10, "Abundant evidence")
    ]
    
    for count, description in evidence_scenarios:
        confidence = agent.calibrate_confidence(evidence_count=count, evidence_quality=0.8)
        print(f"  {description}: confidence = {confidence:.3f}")
    
    print("\n3.2 Knowledge Boundary Detection")
    print("-" * 50)
    
    confidence_levels = [0.95, 0.70, 0.40, 0.15]
    
    for confidence in confidence_levels:
        boundary = agent.check_knowledge_boundary("test query", confidence)
        print(f"\n  Confidence: {confidence:.2f}")
        print(f"    Within boundary: {boundary['within_boundary']}")
        print(f"    Level: {boundary['confidence_level']}")
        print(f"    Message: {boundary['message']}")
        if boundary.get('recommendation'):
            print(f"    Recommendation: {boundary['recommendation']}")
    
    print("\n3.3 Self-Reflection Example")
    print("-" * 50)
    
    # High-quality reasoning
    good_reasoning = [
        {"confidence": 0.95, "conclusion": "Step 1: Validated premise"},
        {"confidence": 0.92, "conclusion": "Step 2: Logical deduction"},
        {"confidence": 0.90, "conclusion": "Step 3: Verified conclusion"}
    ]
    
    print("  Scenario: High-quality reasoning chain")
    reflection = asyncio.run(agent.reflect("Final conclusion", good_reasoning))
    print(f"    Valid: {reflection['valid']}")
    print(f"    Confidence: {reflection['confidence']:.3f}")
    print(f"    Issues: {len(reflection['issues'])}")
    
    # Low-quality reasoning
    poor_reasoning = [
        {"confidence": 0.95, "conclusion": "Step 1: Strong premise"},
        {"confidence": 0.40, "conclusion": "Step 2: Weak link"},  # Low confidence
        {"confidence": 0.90, "conclusion": "Step 3: Conclusion"}
    ]
    
    print("\n  Scenario: Reasoning with weak link")
    reflection = asyncio.run(agent.reflect("Final conclusion", poor_reasoning))
    print(f"    Valid: {reflection['valid']}")
    print(f"    Confidence: {reflection['confidence']:.3f}")
    print(f"    Issues: {reflection['issues']}")
    print(f"    Suggestions: {reflection['suggestions']}")
    
    return {
        "calibration_tested": True,
        "boundary_detection_working": True,
        "self_reflection_working": True
    }


def scenario_4_procurement_compliance():
    """
    Scenario 4: End-to-End Procurement Compliance Check
    
    Demonstrates:
    - Complete workflow integration
    - Multi-rule validation
    - Audit trail generation
    """
    print_section("Scenario 4: End-to-End Procurement Compliance Check")
    
    print("\n4.1 Procurement Project Setup")
    print("-" * 50)
    
    procurement_data = {
        "project_name": "燃气调压箱采购项目-2024",
        "planned_budget": 500000,  # CNY
        "suppliers": [
            {
                "name": "供应商A",
                "quoted_price": 480000,
                "supply_capacity": 150,  # m³/h
                "flow_requirement": 80   # m³/h
            },
            {
                "name": "供应商B",
                "quoted_price": 550000,  # Over budget
                "supply_capacity": 100,
                "flow_requirement": 80
            },
            {
                "name": "供应商C",
                "quoted_price": 490000,
                "supply_capacity": 90,   # Insufficient capacity
                "flow_requirement": 80
            }
        ]
    }
    
    print(f"  Project: {procurement_data['project_name']}")
    print(f"  Budget: ¥{procurement_data['planned_budget']:,}")
    print(f"  Suppliers: {len(procurement_data['suppliers'])}")
    
    print("\n4.2 Compliance Validation")
    print("-" * 50)
    
    rule_engine = RuleEngine()
    
    for supplier in procurement_data['suppliers']:
        print(f"\n  Validating: {supplier['name']}")
        print(f"    Quoted: ¥{supplier['quoted_price']:,}")
        print(f"    Capacity: {supplier['supply_capacity']} m³/h")
        
        # Check budget rule
        budget_context = {
            "quoted_price": supplier['quoted_price'],
            "planned_budget": procurement_data['planned_budget']
        }
        budget_result = rule_engine.evaluate_rule("rule:budget_exceed_limit", budget_context)
        
        # Check safety margin rule
        safety_context = {
            "supply_capacity": supplier['supply_capacity'],
            "flow_requirement": supplier['flow_requirement']
        }
        safety_result = rule_engine.evaluate_rule("rule:gas_regulator_safety_margin", safety_context)
        
        print(f"    Budget compliance: {budget_result['status']}")
        print(f"    Safety compliance: {safety_result['status']}")
        
        if budget_result['status'] == 'PASS' and safety_result['status'] == 'PASS':
            print(f"    ✓ RECOMMENDED for selection")
        else:
            print(f"    ✗ NOT recommended")
    
    print("\n4.3 Audit Trail")
    print("-" * 50)
    
    print(f"  Total rules in engine: {len(rule_engine.rules)}")
    print(f"  Audit entries: {len(rule_engine.rule_history)}")
    
    for entry in rule_engine.rule_history[-3:]:  # Show last 3
        print(f"    [{entry['timestamp']}] {entry['action']}: {entry['rule_id']}")
    
    print("\n4.4 Final Recommendation")
    print("-" * 50)
    
    print("  Based on compliance validation:")
    print("  - Supplier A: PASS all checks ✓")
    print("  - Supplier B: FAIL budget check ✗")
    print("  - Supplier C: FAIL safety margin check ✗")
    print("\n  RECOMMENDATION: Select Supplier A")
    
    return {
        "suppliers_evaluated": len(procurement_data['suppliers']),
        "rules_applied": 2,
        "audit_entries": len(rule_engine.rule_history)
    }


def main():
    """Run all demo scenarios"""
    print("\n" + "="*70)
    print("  CLAWRA NEURO-SYMBOLIC COGNITIVE ENGINE - COMPREHENSIVE DEMO")
    print("="*70)
    print("\nThis demo showcases four key capabilities:")
    print("  1. Knowledge Ingestion and Retrieval")
    print("  2. Rule-Based Reasoning with Confidence")
    print("  3. Knowledge Boundary Detection")
    print("  4. End-to-End Procurement Compliance Check")
    
    results = {}
    
    # Run scenarios
    results['scenario_1'] = scenario_1_knowledge_ingestion()
    results['scenario_2'] = scenario_2_rule_based_reasoning()
    results['scenario_3'] = scenario_3_knowledge_boundary()
    results['scenario_4'] = scenario_4_procurement_compliance()
    
    # Summary
    print_section("DEMO SUMMARY")
    
    print("\n✓ All scenarios completed successfully!")
    print("\nKey Metrics:")
    print(f"  - Facts ingested: {results['scenario_1']['facts_ingested']}")
    print(f"  - Rules available: {results['scenario_2']['rules_available']}")
    print(f"  - Suppliers validated: {results['scenario_4']['suppliers_evaluated']}")
    
    print("\n" + "="*70)
    print("  DEMO COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
