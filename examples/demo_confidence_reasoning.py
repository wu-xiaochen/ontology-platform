"""
Confidence-Reasoning Demo
展示如何使用置信度系统进行可信推理

功能：
- 多证据源的置信度计算
- 推理链置信度传播
- 事实验证和不确定性标注

运行方式：
    cd ontology-platform
    PYTHONPATH=src python examples/demo_confidence_reasoning.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from confidence import ConfidenceCalculator, ConfidenceResult, Evidence


def demo_basic_confidence():
    """基础置信度计算演示"""
    print("\n" + "="*60)
    print("📊 基础置信度计算")
    print("="*60)
    
    calc = ConfidenceCalculator(default_reliability=0.7)
    
    # 单证据源
    evidence_single = [
        Evidence(
            source="ERP系统",
            reliability=0.95,
            content="供应商A的准时交付率为92%"
        )
    ]
    result = calc.calculate(evidence_single, method="weighted")
    print(f"\n单证据源置信度: {result.value:.2%}")
    print(f"  来源: ERP系统 (可靠性: 0.95)")
    print(f"  计算方法: weighted")
    
    # 多证据源
    evidence_multi = [
        Evidence(source="ERP系统", reliability=0.95, content="准时率92%"),
        Evidence(source="历史合同", reliability=0.85, content="过去12个月平均91%"),
        Evidence(source="行业报告", reliability=0.80, content="同类供应商平均88%")
    ]
    result = calc.calculate(evidence_multi, method="weighted")
    print(f"\n多证据源置信度: {result.value:.2%}")
    print(f"  来源: ERP系统 + 历史合同 + 行业报告")
    print(f"  证据数量: {result.evidence_count}")
    
    return result


def demo_evidence_analysis():
    """证据分析演示"""
    print("\n" + "="*60)
    print("🔍 证据分析")
    print("="*60)
    
    calc = ConfidenceCalculator()
    
    # 高质量证据
    evidence_good = [
        Evidence(source="ERP系统", reliability=0.95, content="数据1"),
        Evidence(source="质检报告", reliability=0.92, content="数据2"),
    ]
    result_good = calc.calculate(evidence_good)
    print(f"\n高质量证据 (2个): {result_good.value:.2%}")
    
    # 低质量证据
    evidence_poor = [
        Evidence(source="口头反馈", reliability=0.30, content="数据1"),
    ]
    result_poor = calc.calculate(evidence_poor)
    print(f"低质量证据 (1个): {result_poor.value:.2%}")
    
    # 矛盾证据
    evidence_conflict = [
        Evidence(source="ERP", reliability=0.95, content="准时率92%"),
        Evidence(source="投诉记录", reliability=0.85, content="经常延迟"),
    ]
    result_conflict = calc.calculate(evidence_conflict)
    print(f"矛盾证据: {result_conflict.value:.2%}")
    print(f"  → 系统检测到冲突，置信度降低")
    
    return result_conflict


def demo_business_scenario():
    """商业场景演示"""
    print("\n" + "="*60)
    print("💼 供应商评估场景")
    print("="*60)
    
    calc = ConfidenceCalculator()
    
    # 供应商A评估 - 高置信度
    evidence_a = [
        Evidence(source="ERP系统", reliability=0.95, content="准时交付率92%"),
        Evidence(source="质检报告", reliability=0.90, content="合格率98%"),
        Evidence(source="财务系统", reliability=0.92, content="付款及时"),
    ]
    result_a = calc.calculate(evidence_a)
    
    print(f"\n供应商A:")
    print(f"  置信度: {result_a.value:.2%}")
    print(f"  证据数: {result_a.evidence_count}")
    print(f"  → 决策: 可信任，建议合作")
    
    # 供应商B评估 - 低置信度
    evidence_b = [
        Evidence(source="口头推荐", reliability=0.40, content="听说不错"),
    ]
    result_b = calc.calculate(evidence_b)
    
    print(f"\n供应商B:")
    print(f"  置信度: {result_b.value:.2%}")
    print(f"  证据数: {result_b.evidence_count}")
    print(f"  → 决策: 需要更多数据，建议深入调查")


def demo_auto_learning():
    """自动学习演示 - 基于反馈更新置信度"""
    print("\n" + "="*60)
    print("🧠 自动学习演示")
    print("="*60)
    
    calc = ConfidenceCalculator()
    
    # 初始评估
    evidence = [
        Evidence(source="ERP", reliability=0.90, content="历史数据")
    ]
    initial = calc.calculate(evidence)
    print(f"\n初始评估: {initial.value:.2%}")
    
    # 用户确认结果正确 -> 提高置信度
    calc.set_source_weight("ERP", 0.95)  # 提高到95%
    updated = calc.calculate(evidence)
    print(f"用户确认后: {updated.value:.2%}")
    print(f"  → 系统学习: ERP系统可靠性提升")
    
    # 用户纠正结果错误 -> 降低置信度
    calc.set_source_weight("ERP", 0.80)  # 降低到80%
    corrected = calc.calculate(evidence)
    print(f"纠正后: {corrected.value:.2%}")
    print(f"  → 系统学习: ERP系统可靠性需要修正")


def main():
    """主函数"""
    print("\n" + "🌟"*30)
    print("Confidence-Based Reasoning Demo")
    print("置信度推理系统演示")
    print("🌟"*30)
    
    # 1. 基础置信度计算
    demo_basic_confidence()
    
    # 2. 证据分析
    demo_evidence_analysis()
    
    # 3. 商业场景
    demo_business_scenario()
    
    # 4. 自动学习
    demo_auto_learning()
    
    print("\n" + "="*60)
    print("✅ 演示完成")
    print("="*60)
    print("""
核心价值:
1. 知道"自己不知道" - 置信度让AI有自知之明
2. 多证据源融合 - 综合多方信息得出更可靠结论
3. 自动学习 - 从反馈中持续提升准确性
4. 可解释 - 每项结论都有置信度标注
    """)


if __name__ == "__main__":
    main()