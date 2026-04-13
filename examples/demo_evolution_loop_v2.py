"""
Example: EvolutionLoop v4.1 - 真实闭环演示

运行方式:
    cd /Users/xiaochenwu/Desktop/ontology-platform
    python examples/demo_evolution_loop_v2.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evolution.evolution_loop import EvolutionLoop, EvolutionPhase
from src.evolution.episodic_memory import EpisodicMemory
from src.evolution.meta_learner import MetaLearner


def demo_episodic_memory():
    """情节记忆演示"""
    print("=" * 60)
    print("1. 情节记忆 - 记录每次执行经验")
    print("=" * 60)

    episodic = EpisodicMemory()

    # 记录多次成功
    episodic.add_success(
        phase="reason",
        input_summary="燃气压力过高",
        output_summary="执行降压操作",
        confidence=0.9,
        domain="燃气",
    )
    episodic.add_success(
        phase="reason",
        input_summary="温度超过阈值",
        output_summary="执行降温操作",
        confidence=0.85,
        domain="热力",
    )

    # 记录失败
    episodic.add_failure(
        phase="reason",
        input_summary="未知错误",
        output_summary="",
        error="推理引擎崩溃",
        failure_type="inference_error",
        domain="未知",
    )

    print(f"\n  情节记忆: {len(episodic)} 条记录")

    stats = episodic.get_stats()
    print(f"  成功率: {stats['success_rate']:.1%}")
    print(f"  失败案例采样（2条）:")
    for ep in episodic.failure_sampling(n=2):
        print(f"    - {ep.phase}: {ep.input_summary} → {ep.error}")


def demo_failure_routing():
    """失败路由 + MetaLearner 回流"""
    print("\n" + "=" * 60)
    print("2. 失败路由 → MetaLearner 真实回流")
    print("=" * 60)

    episodic = EpisodicMemory()
    from src.evolution.unified_logic import UnifiedLogicLayer
    from src.evolution.rule_discovery import RuleDiscoveryEngine
    unified = UnifiedLogicLayer()
    discovery = RuleDiscoveryEngine(unified)
    meta_learner = MetaLearner(unified_logic_layer=unified, rule_discovery_engine=discovery)

    loop = EvolutionLoop(
        meta_learner=meta_learner,
        episodic_memory=episodic,
    )

    # 模拟推理失败
    result = loop.step({
        "text": "燃气调压箱出口压力 ≤ 0.4MPa",
        "phase": EvolutionPhase.REASON,
        "query": "test",
        "facts": [],
    })

    print(f"\n  阶段执行: {result.phase.value}, 成功={result.success}")
    if result.error:
        print(f"  错误: {result.error}")

    # 情节记忆应该有记录
    print(f"\n  情节记忆统计:")
    stats = episodic.get_stats()
    print(f"    总记录: {stats['total']}")
    print(f"    成功率: {stats['success_rate']:.1%}")

    # MetaLearner 回流
    print(f"\n  MetaLearner 分析失败案例:")
    failures = episodic.get_failures()
    for ep in failures[:2]:
        print(f"    - [{ep.phase}] {ep.input_summary[:50]}")
        print(f"      失败类型: {ep.failure_type}, 领域: {ep.domain}")


def demo_drift_handling():
    """漂移检测处理"""
    print("\n" + "=" * 60)
    print("3. 漂移检测 → 知识更新")
    print("=" * 60)

    episodic = EpisodicMemory()
    from src.evolution.unified_logic import UnifiedLogicLayer
    from src.evolution.rule_discovery import RuleDiscoveryEngine
    unified = UnifiedLogicLayer()
    discovery = RuleDiscoveryEngine(unified)
    meta_learner = MetaLearner(unified_logic_layer=unified, rule_discovery_engine=discovery)

    loop = EvolutionLoop(
        meta_learner=meta_learner,
        episodic_memory=episodic,
    )

    # 注入低置信度知识（模拟漂移）
    from src.evolution.unified_logic import LogicPattern

    logic_layer = UnifiedLogicLayer()
    # 模拟一个低置信度规则
    pattern = LogicPattern(
        id="p_old_1",
        name="旧规则",
        description="低置信度旧规则",
        logic_type="forward_chain",
        conditions=[{"type": "field_match", "field": "x", "op": ">", "value": 100}],
        actions=[{"type": "set_value", "field": "y", "value": 0}],
        confidence=0.2,  # 低置信度
    )
    logic_layer.add_pattern(pattern)

    loop.logic_layer = logic_layer

    # 执行漂移检测
    result = loop.step({
        "text": "检测知识漂移",
        "phase": EvolutionPhase.DETECT_DRIFT,
        "drift_detected": False,  # 会被低置信度规则触发
    })

    print(f"\n  漂移检测: {result.success}")
    print(f"  检测结果: {result.data}")


def demo_full_loop():
    """完整进化闭环"""
    print("\n" + "=" * 60)
    print("4. 完整进化闭环")
    print("=" * 60)

    episodic = EpisodicMemory()
    from src.evolution.unified_logic import UnifiedLogicLayer
    from src.evolution.rule_discovery import RuleDiscoveryEngine
    unified = UnifiedLogicLayer()
    discovery = RuleDiscoveryEngine(unified)
    meta_learner = MetaLearner(unified_logic_layer=unified, rule_discovery_engine=discovery)

    loop = EvolutionLoop(
        meta_learner=meta_learner,
        episodic_memory=episodic,
    )

    result = loop.run({
        "text": "燃气调压箱出口压力 ≤ 0.4MPa",
        "domain_hint": "燃气",
    })

    print(f"\n  闭环结果:")
    print(f"    成功: {result['success']}")
    print(f"    迭代次数: {result['iterations']}")
    print(f"    反馈信号: {len(result['feedback_signals'])} 个")

    for phase_name, phase_result in result['results'].items():
        status = "✓" if phase_result['success'] else "✗"
        print(f"    {status} {phase_name}: {phase_result.get('error', 'OK')}")

    print(f"\n  情节记忆最终统计:")
    stats = episodic.get_stats()
    print(f"    总记录: {stats['total']}, 成功率: {stats['success_rate']:.1%}")


if __name__ == "__main__":
    print("EvolutionLoop v4.1 真实闭环演示")
    print("新特性：情节记忆 + 失败回流 + 漂移检测\n")

    demo_episodic_memory()
    demo_failure_routing()
    demo_drift_handling()
    demo_full_loop()

    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)
