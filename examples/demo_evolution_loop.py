"""
demo_evolution_loop.py - 进化闭环演示

展示 EvolutionLoop 的 8 阶段自主进化闭环：
1. Perceive（感知）→ 2. Learn（学习）→ 3. Reason（推理）→ 4. Execute（执行）
→ 5. Evaluate（评估）→ 6. DetectDrift（漂移检测）→ 7. ReviseRules（规则修正）→ 8. UpdateKG（知识更新）

运行方式:
    cd /Users/xiaochenwu/Desktop/ontology-platform
    python examples/demo_evolution_loop.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 60)
    print("EvolutionLoop 进化闭环演示")
    print("=" * 60)

    # ── Step 1: 初始化组件 ────────────────────────────────────────
    print("\n[Step 1] 初始化组件...")
    from src.clawra import Clawra
    from src.evolution.evolution_loop import EvolutionLoop, EvolutionPhase

    clawra = Clawra()

    # 从 Clawra 实例获取所需组件
    loop = EvolutionLoop(
        meta_learner=clawra.meta_learner,
        rule_discovery=clawra.rule_discovery,
        evaluator=clawra.self_evaluator,
        reasoner=clawra.reasoner,
        logic_layer=clawra.logic_layer,
        contradiction_checker=clawra.conflict_checker,
    )
    print("  ✓ 组件初始化完成")
    print(f"    - MetaLearner: {'✓' if loop.meta_learner else '✗'}")
    print(f"    - RuleDiscovery: {'✓' if loop.rule_discovery else '✗'}")
    print(f"    - Evaluator: {'✓' if loop.evaluator else '✗'}")

    # ── Step 2: 单步执行各阶段 ─────────────────────────────────────
    print("\n[Step 2] 单步执行各进化阶段...")
    input_text = "燃气调压箱出口压力不得超过 0.4MPa，超过时应立即启动安全阀泄压。"

    phase_sequence = [
        (EvolutionPhase.PERCEIVE, "感知 - 解析输入文本"),
        (EvolutionPhase.LEARN, "学习 - 发现逻辑模式"),
        (EvolutionPhase.REASON, "推理 - 执行前向链推导"),
        (EvolutionPhase.EXECUTE, "执行 - 应用规则动作"),
    ]

    for phase, desc in phase_sequence:
        print(f"\n  --- {desc} ---")
        result = loop.step({
            "text": input_text,
            "phase": phase,
            "domain_hint": "gas_safety"
        })
        status = "✅ 成功" if result.success else f"❌ 失败: {result.error}"
        print(f"    状态: {status}")
        print(f"    耗时: {result.duration:.3f}s")
        if result.data:
            # 打印关键数据
            data_str = str(result.data)
            print(f"    数据: {data_str[:150]}...")

    # ── Step 3: 完整闭环执行 ───────────────────────────────────────
    print("\n[Step 3] 执行完整进化闭环...")
    full_result = loop.run({
        "text": "调压箱需要配备安全阀，安全阀应每年校验一次。",
        "episode_id": "demo_ep_001",
        "domain_hint": "gas_equipment"
    })

    print(f"\n  闭环执行结果:")
    print(f"    episode_id: {full_result.get('episode_id')}")
    print(f"    迭代次数: {full_result.get('iterations')}")
    print(f"    是否收敛: {full_result.get('converged')}")
    print(f"    整体成功: {full_result.get('success')}")
    print(f"    反馈信号数: {len(full_result.get('feedback_signals', []))}")

    # 打印各阶段结果摘要
    print("\n  各阶段执行情况:")
    for phase_name, phase_data in full_result.get("results", {}).items():
        icon = "✅" if phase_data.get("success") else "❌"
        duration = phase_data.get("duration", 0)
        error = phase_data.get("error", "")
        data_preview = str(phase_data.get("data", ""))[:60]
        print(f"    {icon} {phase_name}: {duration:.3f}s | {data_preview} {f'| ERROR: {error}' if error else ''}")

    # ── Step 4: 注册阶段回调钩子 ───────────────────────────────────
    print("\n[Step 4] 注册阶段回调钩子...")
    hook_results = []

    def my_phase_hook(phase_result):
        hook_results.append({
            "phase": phase_result.phase.value,
            "success": phase_result.success
        })
        print(f"    钩子触发: {phase_result.phase.value} -> {'✅' if phase_result.success else '❌'}")

    loop.register_hook(EvolutionPhase.LEARN, my_phase_hook)
    loop.register_hook(EvolutionPhase.EVALUATE, my_phase_hook)
    print("  ✓ 已注册 LEARN 和 EVALUATE 阶段的回调钩子")

    # ── Step 5: 再次执行并触发钩子 ─────────────────────────────────
    print("\n[Step 5] 再次执行并触发回调...")
    result2 = loop.run({
        "text": "高压燃气调压至低压时，需使用两级调压。",
        "episode_id": "demo_ep_002"
    })
    print(f"  ✓ 钩子触发次数: {len(hook_results)}")

    # ── Step 6: 知识评估 ───────────────────────────────────────────
    print("\n[Step 6] 知识质量评估...")
    eval_summary = clawra.evaluate_knowledge()
    print(f"  ✓ 评估完成:")
    print(f"    - 总评估知识数: {eval_summary.get('total_evaluated', 0)}")
    print(f"    - 平均质量分: {eval_summary.get('avg_overall', 0):.2f}")
    print(f"    - 生命周期变更: {eval_summary.get('lifecycle_changes', 0)}")
    print(f"    - 置信度衰减: {eval_summary.get('confidence_decayed', 0)}")

    print("\n" + "=" * 60)
    print("✅ demo_evolution_loop.py 完成！")
    print("=" * 60)
    print("\n下一步推荐:")
    print("  → python examples/demo_graphrag.py          查看 GraphRAG 检索")
    print("  → python examples/demo_pattern_versioning.py 查看 Pattern 版本控制")
    print("  → python examples/demo_leiden_community.py  查看 Leiden 社区检测")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
