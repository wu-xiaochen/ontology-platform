"""
Example: CaseBasedReasoner - 案例推理演示

运行方式:
    cd /Users/xiaochenwu/Desktop/ontology-platform
    python examples/demo_case_based_reasoner.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evolution.case_based_reasoner import (
    CaseBasedReasoner,
    CaseOutcome,
)


def demo_basic_cbr():
    """基础 CBR 流程"""
    print("=" * 60)
    print("1. 基础 CBR 流程")
    print("=" * 60)

    cbr = CaseBasedReasoner(min_similarity=0.2)

    # ─── Retain：存入经验 ───────────────────────────────
    print("\n[Retain] 存入三个经验案例...")

    cbr.retain(
        situation={"domain": "燃气", "pressure": "high", "device": "调压器"},
        solution={"action": "降低压力", "value": "0.3MPa", "duration": "10min"},
        outcome=CaseOutcome.SUCCESS,
        outcome_text="压力恢复正常范围",
        domain="燃气",
    )

    cbr.retain(
        situation={"domain": "燃气", "pressure": "normal", "temp": "high"},
        solution={"action": "降低温度", "value": "20°C", "duration": "15min"},
        outcome=CaseOutcome.SUCCESS,
        outcome_text="温度恢复到正常",
        domain="燃气",
    )

    cbr.retain(
        situation={"domain": "电力", "voltage": "over", "device": "变压器"},
        solution={"action": "降低电压", "value": "220V", "duration": "5min"},
        outcome=CaseOutcome.SUCCESS,
        outcome_text="电压稳定",
        domain="电力",
    )

    print(f"  案例库容量: {cbr.case_base.size()} 条")

    # ─── Retrieve + Reuse：新问题 ───────────────────────
    print("\n[Retrieve + Reuse] 遇到新情境：")
    print("  情境：domain=燃气, pressure=very_high, device=调压器")

    result = cbr.reason(
        situation={"domain": "燃气", "pressure": "very_high", "device": "调压器"},
        domain="燃气",
    )

    print(f"\n  推理结果：")
    print(f"    策略: {result.strategy_used}")
    print(f"    置信度: {result.confidence:.2f}")
    print(f"    适配步骤: {' → '.join(result.adaptation_steps)}")
    print(f"    参考案例: {result.fallback_cases}")
    print(f"    解决方案: {result.adapted_solution}")


def demo_meta_strategy():
    """元策略演示"""
    print("\n" + "=" * 60)
    print("2. 元策略：无案例时的应对")
    print("=" * 60)

    cbr = CaseBasedReasoner(min_similarity=0.2)

    print("\n[MetaStrategy] 案例库为空，遇到全新情境")
    print("  情境：domain=未知, type=complex, a=1, b=2, c=3")

    result = cbr.reason(
        situation={"domain": "未知领域", "type": "complex", "a": 1, "b": 2, "c": 3},
    )

    print(f"\n  触发元策略: {result.strategy_used}")
    print(f"  适配方案: {result.adapted_solution}")
    print(f"  置信度: {result.confidence:.2f}（低置信度表示不确定性）")


def demo_partial_match():
    """部分匹配+适配"""
    print("\n" + "=" * 60)
    print("3. 部分匹配 + 适配")
    print("=" * 60)

    cbr = CaseBasedReasoner(min_similarity=0.1)

    cbr.retain(
        situation={"field": "pressure", "range": "0-100", "unit": "MPa"},
        solution={"set_range": "0-100", "set_unit": "MPa"},
        outcome=CaseOutcome.SUCCESS,
        outcome_text="压力设置成功",
        domain="测量",
    )

    print("\n[Partial Match] 存：pressure 0-100MPa")
    print("  推理：pressure 0-150MPa（新单位）")

    result = cbr.reason(
        situation={"field": "pressure", "range": "0-150", "unit": "MPa"},
    )

    print(f"\n  策略: {result.strategy_used}")
    print(f"  置信度: {result.confidence:.2f}")
    print(f"  适配: {result.adaptation_steps}")


def demo_numerical_similarity():
    """数值相似度"""
    print("\n" + "=" * 60)
    print("4. 数值情境的相似度匹配")
    print("=" * 60)

    cbr = CaseBasedReasoner(min_similarity=0.1)

    cbr.retain(
        situation={"temp": 25, "humidity": 60, "pressure": 101.3},
        solution={"action": "标准工况运行"},
        outcome=CaseOutcome.SUCCESS,
        outcome_text="正常",
        domain="环境",
    )

    test_cases = [
        {"temp": 25, "humidity": 60, "pressure": 101.3},   # 完全相同
        {"temp": 30, "humidity": 65, "pressure": 101.5},  # 略微不同
        {"temp": 50, "humidity": 80, "pressure": 102.0}, # 明显不同
    ]

    for i, s in enumerate(test_cases, 1):
        result = cbr.reason(s)
        print(f"\n  情境 {i}: temp={s['temp']}, humidity={s['humidity']}, pressure={s['pressure']}")
        print(f"    → 策略={result.strategy_used}, 置信度={result.confidence:.2f}")


if __name__ == "__main__":
    print("CaseBasedReasoner 示例")
    print("基于「人类逻辑起源」——遇到新事物 → 检索相似案例 → 类比适配\n")

    demo_basic_cbr()
    demo_meta_strategy()
    demo_partial_match()
    demo_numerical_similarity()

    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)
