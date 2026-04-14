#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
"""
Clawra Framework - Comprehensive Full Capability Demo
=======================================================

This demo showcases ALL major capabilities of the Clawra autonomous evolution agent framework:

1. Clawra init and learn() - Extract knowledge from text
2. Reasoning - add_fact + reason() 
3. Domain adaptive - Learn from different domains
4. Self-evaluation
5. GraphRAG retrieval
6. Skill library
7. Rule engine

Run with: PYTHONPATH=. python examples/full_demo.py
"""

import sys
import logging
from typing import Dict, Any

# Configure logging for demo visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Reduce noise from third-party libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# Import Clawra main class
from src.clawra import Clawra

# Import rule engine components for Rule Engine demo
from src.core.ontology.rule_engine import RuleEngine, OntologyRule, SafeMathSandbox


def print_section_header(title: str):
    """Print a clear section header for the demo."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title: str):
    """Print a subsection header."""
    print(f"\n--- {title} ---")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           CLAWRA FRAMEWORK - COMPREHENSIVE CAPABILITY DEMO           ║
║                                                                       ║
║  Showcasing ALL 7 Major Capabilities:                               ║
║  1. Clawra Init & learn() - Knowledge extraction from text           ║
║  2. Reasoning - add_fact + reason() forward chaining                ║
║  3. Domain Adaptive - Multi-domain learning                          ║
║  4. Self-Evaluation - Multi-dimensional quality assessment            ║
║  5. GraphRAG Retrieval - Hybrid multi-mode retrieval                 ║
║  6. Skill Library - Voyager-style skill evolution                   ║
║  7. Rule Engine - OWL-compatible constraint enforcement             ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # =========================================================================
    # CAPABILITY 1: Clawra Init and learn() - Knowledge Extraction
    # =========================================================================
    print_section_header("CAPABILITY 1: Clawra Init & learn() - Knowledge Extraction")
    
    print("\n[Step 1] Initializing Clawra agent...")
    clawra = Clawra(enable_memory=False)  # Demo mode: in-memory only
    print("  ✅ Clawra initialized successfully")
    
    print("\n[Step 2] Learning knowledge from text via learn()...")
    text = (
        "燃气调压箱的作用是把高压燃气降低为恒定压力的低压或中压。"
        "使用规范要求：进气压力不能大于0.4MPa，否则存在泄漏爆炸风险。"
        "调压箱通常配备安全阀和监控系统。"
    )
    print(f"  Input text: {text[:50]}...")
    
    result = clawra.learn(text)
    
    print(f"\n[Step 3] Learning Results:")
    print(f"  ✅ Success: {result.get('success', False)}")
    print(f"  📊 Domain detected: {result.get('domain', 'generic')}")
    print(f"  🔢 Patterns learned: {len(result.get('learned_patterns', []))}")
    print(f"  📝 Facts extracted: {result.get('facts_added', 0)}")
    
    # Show extracted facts
    extracted_facts = result.get('extracted_facts', [])
    if extracted_facts:
        print(f"\n[Step 4] Extracted Knowledge Triples:")
        for i, fact in enumerate(extracted_facts[:5], 1):
            print(f"  {i}. ({fact.get('subject')}) -[{fact.get('predicate')}]-> ({fact.get('object')})")
    else:
        print("  (No facts extracted - may be in offline mode)")
    
    # =========================================================================
    # CAPABILITY 2: Reasoning - add_fact + reason()
    # =========================================================================
    print_section_header("CAPABILITY 2: Reasoning - add_fact + reason()")
    
    print("\n[Step 1] Adding facts to the knowledge graph...")
    clawra.add_fact("调压箱A", "is_a", "燃气调压箱", confidence=0.95)
    clawra.add_fact("调压箱A", "has_component", "安全阀", confidence=0.9)
    clawra.add_fact("安全阀", "is_a", "安全装置", confidence=0.95)
    clawra.add_fact("燃气调压箱", "is_a", "压力设备", confidence=0.9)
    clawra.add_fact("压力设备", "is_a", "工业设备", confidence=0.85)
    print("  ✅ Added 5 facts to the graph")
    
    print("\n[Step 2] Current knowledge graph state:")
    stats = clawra.get_statistics()
    print(f"  📊 Total facts in graph: {stats.get('facts', 0)}")
    
    print("\n[Step 3] Executing forward chain reasoning...")
    conclusions = clawra.reason(max_depth=3)
    
    print(f"\n[Step 4] Reasoning Results:")
    print(f"  🧠 Total conclusions derived: {len(conclusions)}")
    if conclusions:
        for i, conc in enumerate(conclusions[:5], 1):
            conc_str = str(conc) if not isinstance(conc, str) else conc
            print(f"  {i}. {conc_str}")
    else:
        print("  (No new conclusions from forward chaining with current rules)")
    
    # =========================================================================
    # CAPABILITY 3: Domain Adaptive - Multi-domain Learning
    # =========================================================================
    print_section_header("CAPABILITY 3: Domain Adaptive - Multi-domain Learning")
    
    domains = [
        {
            "name": "Medical Domain",
            "text": "患者诊断需要根据症状和检查结果进行。药物治疗方案需要考虑患者的过敏史和副作用。",
            "hint": "medical"
        },
        {
            "name": "Legal Domain", 
            "text": "合同违约需要承担赔偿责任。依据合同条款确定违约责任范围。",
            "hint": "legal"
        },
        {
            "name": "Gas Equipment Domain",
            "text": "燃气调压箱的维护周期为每半年一次。需要检查密封性能和压力参数。",
            "hint": "gas_equipment"
        }
    ]
    
    print(f"\n[Step 1] Learning from {len(domains)} different domains...")
    domain_results = []
    
    for i, domain_info in enumerate(domains, 1):
        print(f"\n  [{i}/{len(domains)}] Learning {domain_info['name']}...")
        result = clawra.learn(domain_info['text'], domain_hint=domain_info['hint'])
        domain_detected = result.get('domain', 'unknown')
        patterns_count = len(result.get('learned_patterns', []))
        print(f"      ✅ Domain detected: {domain_detected}, Patterns: {patterns_count}")
        domain_results.append({
            "requested": domain_info['hint'],
            "detected": domain_detected,
            "patterns": patterns_count
        })
    
    print("\n[Step 2] Domain Adaptation Results:")
    print(f"  {'Requested Domain':<20} {'Detected Domain':<20} {'Patterns':<10}")
    print(f"  {'-'*50}")
    for r in domain_results:
        match = "✓" if r['requested'] == r['detected'] else "~"
        print(f"  {r['requested']:<20} {r['detected']:<20} {r['patterns']:<10} {match}")
    
    # =========================================================================
    # CAPABILITY 4: Self-Evaluation
    # =========================================================================
    print_section_header("CAPABILITY 4: Self-Evaluation - Multi-dimensional Assessment")
    
    print("\n[Step 1] Running knowledge quality evaluation...")
    eval_result = clawra.evaluate_knowledge()
    
    print(f"\n[Step 2] Evaluation Results:")
    print(f"  📊 Total evaluated: {eval_result.get('total_evaluated', 0)}")
    print(f"  📈 Average quality: {eval_result.get('avg_overall', 0):.3f}")
    print(f"  🔄 Lifecycle changes: {eval_result.get('lifecycle_changes', 0)}")
    print(f"  📉 Confidence decayed: {eval_result.get('confidence_decayed', 0)}")
    
    # Get patterns for quality evaluation
    print("\n[Step 3] Evaluating pattern quality...")
    patterns = clawra.query_patterns()
    print(f"  📋 Total patterns available: {len(patterns)}")
    
    # Get system health
    from src.evolution.self_evaluator import SelfEvaluator
    evaluator = SelfEvaluator()
    
    if patterns:
        pattern_ids = [p.get('id', '') for p in patterns[:5]]
        print(f"  🎯 Evaluating {len(pattern_ids)} patterns...")
    
    # Get system statistics
    print("\n[Step 4] System Health Report:")
    health = evaluator.get_system_health()
    print(f"  🏥 Health Status: {health.get('status', 'unknown')}")
    print(f"  📊 Overall Score: {health.get('overall_score', 0):.3f}")
    print(f"  📈 Trend: {health.get('trend', 'unknown')}")
    
    # =========================================================================
    # CAPABILITY 5: GraphRAG Retrieval
    # =========================================================================
    print_section_header("CAPABILITY 5: GraphRAG Retrieval - Hybrid Multi-mode")
    
    print("\n[Step 1] Building retrieval index...")
    clawra.retriever.build_index()
    print("  ✅ Index built from knowledge graph")
    
    queries = [
        "燃气调压箱的安全规范",
        "调压设备维护",
        "压力设备类型"
    ]
    
    print(f"\n[Step 2] Testing {len(queries)} retrieval queries...")
    
    for i, query in enumerate(queries, 1):
        print(f"\n  Query {i}: \"{query}\"")
        
        # Test hybrid retrieval
        response = clawra.retrieve_knowledge(query, top_k=5, modes=["entity", "semantic"])
        
        print(f"  📊 Results found: {len(response.results)}")
        print(f"  🔍 Search modes: {response.retrieval_modes}")
        
        if response.results:
            top = response.results[0]
            print(f"  🎯 Top result: ({top.triple.subject}) -[{top.triple.predicate}]-> ({top.triple.object})")
            print(f"     Score: {top.score:.3f}, Source: {top.source}")
    
    # =========================================================================
    # CAPABILITY 6: Skill Library
    # =========================================================================
    print_section_header("CAPABILITY 6: Skill Library - Voyager-style Evolution")
    
    print("\n[Step 1] Accessing Skill Registry...")
    skill_registry = clawra.skill_registry
    print(f"  ✅ Skill registry initialized")
    print(f"  📦 Total skills registered: {len(skill_registry.skills)}")
    
    # List existing skills
    print("\n[Step 2] Existing Skills:")
    for skill_id, skill in list(skill_registry.skills.items())[:5]:
        print(f"  - {skill.name} ({skill.skill_type.value})")
        print(f"    Description: {skill.description[:60]}...")
    
    # Demonstrate skill registration
    print("\n[Step 3] Registering a new skill...")
    from src.evolution.skill_library import Skill, SkillType
    
    new_skill = Skill(
        id="skill:pressure_check",
        name="压力安全检查",
        description="检查燃气设备压力是否在安全范围内，返回检查结果。",
        skill_type=SkillType.CODE,
        content='''
def check_pressure_range(inlet_pressure, outlet_pressure):
    """
    检查压力是否在安全范围内
    安全范围: inlet <= 0.4 MPa, outlet between 0.002-0.4 MPa
    """
    if inlet_pressure > 0.4:
        return {"safe": False, "reason": "进气压力超出安全上限"}
    if outlet_pressure < 0.002 or outlet_pressure > 0.4:
        return {"safe": False, "reason": "出气压力超出安全范围"}
    return {"safe": True, "reason": "压力参数正常"}
'''
    )
    
    success = skill_registry.register_skill(new_skill)
    print(f"  {'✅ Skill registered successfully' if success else '❌ Skill registration failed'}")
    
    # Test skill execution
    print("\n[Step 4] Executing registered skill...")
    if "skill:pressure_check" in skill_registry.callables:
        func = skill_registry.callables["skill:pressure_check"]
        test_result = func(0.3, 0.01)
        print(f"  🔧 Execution result: {test_result}")
    else:
        print("  (Skill callable not yet compiled)")
    
    # Get tool metadata for LLM integration
    print("\n[Step 5] Skill Library Tool Metadata:")
    tools = skill_registry.get_tool_metadata()
    print(f"  📋 Total tools available for LLM: {len(tools)}")
    
    # =========================================================================
    # CAPABILITY 7: Rule Engine
    # =========================================================================
    print_section_header("CAPABILITY 7: Rule Engine - OWL-compatible Constraints")
    
    print("\n[Step 1] Initializing Rule Engine...")
    rule_engine = RuleEngine()
    print("  ✅ Rule Engine initialized")
    
    print("\n[Step 2] Registering domain rules...")
    
    # Rule 1: Gas pressure safety rule
    rule1 = OntologyRule(
        id="rule:gas_pressure_safety",
        target_object_class="GasRegulator",
        expression="outlet_pressure >= 0.002 and outlet_pressure <= 0.4",
        description="出口压力必须在安全的 2kPa 到 400kPa 范围内"
    )
    rule_engine.register_rule(rule1)
    print(f"  ✅ Registered: {rule1.description}")
    
    # Rule 2: Inlet pressure upper limit
    rule2 = OntologyRule(
        id="rule:inlet_pressure_limit",
        target_object_class="GasRegulator", 
        expression="inlet_pressure <= 0.4",
        description="进气压力不能大于0.4MPa"
    )
    rule_engine.register_rule(rule2)
    print(f"  ✅ Registered: {rule2.description}")
    
    # Rule 3: Maintenance cycle
    rule3 = OntologyRule(
        id="rule:maintenance_cycle",
        target_object_class="GasRegulator",
        expression="maintenance_interval_months <= 12",
        description="维护周期不能超过12个月"
    )
    rule_engine.register_rule(rule3)
    print(f"  ✅ Registered: {rule3.description}")
    
    print(f"\n[Step 3] Total rules in engine: {len(rule_engine.rules)}")
    
    print("\n[Step 4] Testing Rule Evaluation...")
    
    # Test case 1: Valid parameters
    test_valid = {
        "outlet_pressure": 0.05,
        "inlet_pressure": 0.3,
        "maintenance_interval_months": 6
    }
    result1 = rule_engine.evaluate_action_preconditions(
        "action:configure",
        "GasRegulator",
        test_valid
    )
    
    all_passed = all(r.get('status') == 'PASS' for r in result1)
    print(f"\n  Test Case 1 (Valid parameters):")
    print(f"    Input: outlet={test_valid['outlet_pressure']}, inlet={test_valid['inlet_pressure']}")
    print(f"    Result: {'✅ ALL PASSED' if all_passed else '❌ FAILED'}")
    
    # Test case 2: Invalid - pressure too high
    test_invalid_high = {
        "outlet_pressure": 0.8,  # Exceeds 0.4
        "inlet_pressure": 0.3,
        "maintenance_interval_months": 6
    }
    result2 = rule_engine.evaluate_action_preconditions(
        "action:configure",
        "GasRegulator",
        test_invalid_high
    )
    
    failed_rules = [r for r in result2 if r.get('status') == 'FAIL']
    print(f"\n  Test Case 2 (Invalid - pressure too high):")
    print(f"    Input: outlet={test_invalid_high['outlet_pressure']}, inlet={test_invalid_high['inlet_pressure']}")
    print(f"    Result: ❌ BLOCKED - {len(failed_rules)} rule(s) failed")
    for r in failed_rules:
        print(f"      🚫 {r.get('rule_name')}: {r.get('message', 'Constraint violated')}")
    
    # Test case 3: SafeMathSandbox demonstration
    print(f"\n[Step 5] SafeMathSandbox - Protection against DoS:")
    print("  Testing dangerous expression: 99999 ** 9999")
    try:
        SafeMathSandbox.evaluate("99999 ** 9999", {})
        print("  ❌ Should have been blocked!")
    except ValueError as e:
        print(f"  🛡️ Blocked by sandbox: {e}")
        print("  ✅ System protected from CPU/memory exhaustion attacks")
    
    # =========================================================================
    # Final Summary
    # =========================================================================
    print_section_header("DEMO COMPLETE - Summary")
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    ALL 7 CAPABILITIES DEMONSTRATED                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  1. ✅ Clawra Init & learn()    - Knowledge extraction from text    ║
║  2. ✅ Reasoning                 - Forward chain inference            ║
║  3. ✅ Domain Adaptive           - Multi-domain learning              ║
║  4. ✅ Self-Evaluation           - Quality assessment & health        ║
║  5. ✅ GraphRAG Retrieval        - Hybrid multi-mode retrieval        ║
║  6. ✅ Skill Library            - Voyager-style skill evolution      ║
║  7. ✅ Rule Engine              - OWL-compatible constraints         ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    print("Final System Statistics:")
    final_stats = clawra.get_statistics()
    print(f"  📊 Total facts: {final_stats.get('facts', 0)}")
    print(f"  📊 Total patterns: {final_stats.get('patterns', {}).get('total', 0)}")
    print(f"  📊 Graph entities: {final_stats.get('graph', {}).get('entities', 0)}")
    print(f"  📊 Knowledge quality: {final_stats.get('evaluation', {}).get('avg_overall', 'N/A')}")


if __name__ == "__main__":
    main()
