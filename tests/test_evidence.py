"""
Auto-Learn Tests
自动学习功能测试
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from confidence import ConfidenceCalculator, Evidence


def test_source_weight_adjustment():
    """测试证据源权重调整"""
    calc = ConfidenceCalculator()
    
    # 初始状态
    evidence = [Evidence(source="ERP", reliability=0.90, content="测试")]
    result1 = calc.calculate(evidence)
    initial_value = result1.value
    
    # 调整权重
    calc.set_source_weight("ERP", 0.50)
    result2 = calc.calculate(evidence)
    
    # 验证权重降低导致置信度降低
    assert result2.value < initial_value, "降低权重应该降低置信度"
    print(f"✓ 权重调整: {initial_value:.2%} → {result2.value:.2%}")


def test_multiple_sources_confidence():
    """测试多证据源置信度计算"""
    calc = ConfidenceCalculator()
    
    evidence = [
        Evidence(source="A", reliability=0.90, content="数据1"),
        Evidence(source="B", reliability=0.80, content="数据2"),
        Evidence(source="C", reliability=0.70, content="数据3"),
    ]
    
    result = calc.calculate(evidence)
    
    # 多证据源应该比单证据源更可靠
    assert result.value > 0.70, "多证据源应该提高置信度"
    assert result.evidence_count == 3, "应该记录3个证据"
    print(f"✓ 多证据源: {result.value:.2%} (3个证据)")


def test_confidence_levels():
    """测试置信度级别判断"""
    calc = ConfidenceCalculator()
    
    # 高置信度场景
    high_evidence = [
        Evidence(source="ERP", reliability=0.95, content="数据"),
    ]
    high_result = calc.calculate(high_evidence)
    assert high_result.value >= 0.80, "高质量单证据应该有高置信度"
    
    # 低置信度场景
    low_evidence = [
        Evidence(source="口头", reliability=0.30, content="听说"),
    ]
    low_result = calc.calculate(low_evidence)
    assert low_result.value < 0.50, "低质量证据应该有低置信度"
    
    print(f"✓ 高置信度: {high_result.value:.2%}")
    print(f"✓ 低置信度: {low_result.value:.2%}")


if __name__ == "__main__":
    print("Running auto-learn tests...")
    test_source_weight_adjustment()
    test_multiple_sources_confidence()
    test_confidence_levels()
    print("\n✅ All tests passed!")