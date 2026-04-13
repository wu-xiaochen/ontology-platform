"""
demo_pattern_versioning.py - Pattern 版本控制演示

展示 UnifiedLogicLayer 的 Pattern 版本管理能力：
1. 手动添加 LogicPattern
2. 获取 pattern 的版本号
3. 获取 pattern 的完整历史版本
4. 对比两个版本的差异
5. 回滚到指定版本
6. 合并相似 Pattern
7. 检测冗余规则

运行方式:
    cd /Users/xiaochenwu/Desktop/ontology-platform
    python examples/demo_pattern_versioning.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 60)
    print("Pattern 版本控制演示")
    print("=" * 60)

    # ── Step 1: 初始化 ────────────────────────────────────────────
    print("\n[Step 1] 初始化 Clawra...")
    from src.clawra import Clawra
    from src.evolution.unified_logic import LogicPattern, LogicType

    clawra = Clawra()
    logic_layer = clawra.logic_layer
    print("  ✓ Clawra 初始化完成")

    # ── Step 2: 添加初始 Pattern ─────────────────────────────────
    print("\n[Step 2] 添加初始 Pattern (v1)...")
    pattern_v1 = LogicPattern(
        id="gas_pressure_rule_v1",
        logic_type=LogicType.RULE,
        name="燃气压力上限规则",
        description="调压箱出口压力不得超过 0.4MPa",
        conditions=[
            {"subject": "?X", "predicate": "type", "object": "调压箱"},
            {"subject": "?X", "predicate": "出口压力", "object": "?P"}
        ],
        actions=[
            {"type": "constrain", "subject": "?P", "predicate": "<=", "object": "0.4MPa"}
        ],
        confidence=0.85,
        source="manual",
        domain="gas_safety",
        version=1
    )
    success = logic_layer.add_pattern(pattern_v1)
    print(f"  ✓ 添加 Pattern v1: {'成功' if success else '失败'}")
    print(f"    ID: {pattern_v1.id}, 版本: {pattern_v1.version}")

    # ── Step 3: 更新 Pattern（自动创建 v2）────────────────────────
    print("\n[Step 3] 更新 Pattern 创建 v2...")
    # 修改后重新添加（版本会自动递增）
    pattern_v2 = LogicPattern(
        id="gas_pressure_rule_v1",  # 相同 ID，触发版本更新
        logic_type=LogicType.RULE,
        name="燃气压力上限规则",
        description="调压箱出口压力不得超过 0.35MPa（已修订，更严格）",
        conditions=[
            {"subject": "?X", "predicate": "type", "object": "调压箱"},
            {"subject": "?X", "predicate": "出口压力", "object": "?P"}
        ],
        actions=[
            {"type": "constrain", "subject": "?P", "predicate": "<=", "object": "0.35MPa"}
        ],
        confidence=0.90,
        source="manual",
        domain="gas_safety",
        version=2
    )
    success = logic_layer.add_pattern(pattern_v2)
    print(f"  ✓ 更新 Pattern: {'成功' if success else '失败'}")
    print(f"    当前版本: {logic_layer.get_pattern_version('gas_pressure_rule_v1')}")

    # ── Step 4: 添加更多 Pattern ─────────────────────────────────
    print("\n[Step 4] 添加更多 Pattern...")
    patterns_to_add = [
        LogicPattern(
            id="maintenance_rule_001",
            logic_type=LogicType.RULE,
            name="调压箱维护规则",
            description="调压箱应每半年进行一次维护检查",
            conditions=[
                {"subject": "?X", "predicate": "type", "object": "调压箱"}
            ],
            actions=[
                {"type": "require", "subject": "?X", "predicate": "维护周期", "object": "6个月"}
            ],
            confidence=0.88,
            source="learned",
            domain="gas_equipment"
        ),
        LogicPattern(
            id="maintenance_rule_002",
            logic_type=LogicType.RULE,
            name="调压器维护规则",
            description="调压器应每半年进行一次维护检查",
            conditions=[
                {"subject": "?X", "predicate": "type", "object": "调压器"}
            ],
            actions=[
                {"type": "require", "subject": "?X", "predicate": "维护周期", "object": "6个月"}
            ],
            confidence=0.88,
            source="learned",
            domain="gas_equipment"
        ),
        LogicPattern(
            id="safety_valve_rule",
            logic_type=LogicType.RULE,
            name="安全阀校验规则",
            description="安全阀应每年校验一次，确保灵敏可靠",
            conditions=[
                {"subject": "?X", "predicate": "type", "object": "安全阀"}
            ],
            actions=[
                {"type": "require", "subject": "?X", "predicate": "校验周期", "object": "12个月"}
            ],
            confidence=0.92,
            source="learned",
            domain="gas_safety"
        ),
    ]

    for p in patterns_to_add:
        logic_layer.add_pattern(p)
    print(f"  ✓ 添加了 {len(patterns_to_add)} 个 Pattern")

    # ── Step 5: 获取 Pattern 版本历史 ─────────────────────────────
    print("\n[Step 5] 获取 Pattern 版本历史...")
    history = logic_layer.get_pattern_history("gas_pressure_rule_v1")
    print(f"  ✓ gas_pressure_rule_v1 共有 {len(history)} 个历史版本:")
    for v in history:
        print(f"    v{v.version}: {v.description[:50]}... (置信度: {v.confidence:.2f})")

    # ── Step 6: 对比两个版本 ──────────────────────────────────────
    print("\n[Step 6] 对比 v1 和 v2 的差异...")
    diff = logic_layer.compare_versions("gas_pressure_rule_v1", 1, 2)
    print(f"  ✓ 版本对比结果:")
    print(f"    版本差异: v1 -> v2")
    for key, changes in diff.items():
        if changes and key != "version":
            print(f"    - {key}: {changes}")

    # ── Step 7: 回滚到 v1 ─────────────────────────────────────────
    print("\n[Step 7] 回滚到 v1...")
    rollback_ok = logic_layer.rollback_pattern("gas_pressure_rule_v1", target_version=1)
    print(f"  ✓ 回滚: {'成功' if rollback_ok else '失败'}")
    current_version = logic_layer.get_pattern_version("gas_pressure_rule_v1")
    print(f"    当前版本: {current_version}")
    current_pattern = logic_layer.patterns.get("gas_pressure_rule_v1")
    if current_pattern:
        print(f"    当前描述: {current_pattern.description}")

    # ── Step 8: 检测冗余 Pattern ─────────────────────────────────
    print("\n[Step 8] 检测冗余 Pattern...")
    redundant = logic_layer.find_redundant_patterns()
    print(f"  ✓ 发现 {len(redundant)} 对冗余 Pattern:")
    for pair in redundant[:5]:
        print(f"    - {pair[0]} <-> {pair[1]}")

    # ── Step 9: 合并相似 Pattern ──────────────────────────────────
    print("\n[Step 9] 合并相似 Pattern (dry-run)...")
    merge_candidates = logic_layer.merge_similar_patterns(
        threshold=0.8,
        dry_run=True
    )
    print(f"  ✓ 建议合并 {len(merge_candidates)} 对 Pattern:")
    for candidate in merge_candidates[:5]:
        print(f"    - Pattern A: {candidate.get('pattern_a_id')}")
        print(f"      Pattern B: {candidate.get('pattern_b_id')}")
        print(f"      相似度: {candidate.get('similarity', 0):.3f}")

    # ── Step 10: 查看所有 Pattern ─────────────────────────────────
    print("\n[Step 10] 查看所有 Pattern...")
    all_patterns = logic_layer.patterns
    print(f"  ✓ 共有 {len(all_patterns)} 个 Pattern:")
    for pid, p in list(all_patterns.items())[:10]:
        print(f"    [{p.logic_type.value}] {p.name} (v{p.version}, 置信度: {p.confidence:.2f})")

    # ── Step 11: 统计信息 ─────────────────────────────────────────
    print("\n[Step 11] 获取统计信息...")
    stats = logic_layer.get_statistics()
    print(f"  ✓ Pattern 统计:")
    for key, val in stats.items():
        if val:
            print(f"    - {key}: {val}")

    print("\n" + "=" * 60)
    print("✅ demo_pattern_versioning.py 完成！")
    print("=" * 60)
    print("\n下一步推荐:")
    print("  → python examples/demo_leiden_community.py  查看 Leiden 社区检测")
    print("  → python examples/demo_evolution_loop.py      查看进化闭环")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
