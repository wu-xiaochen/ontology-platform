"""
自我评估器单元测试

验证 SelfEvaluator 的核心功能：
1. 学习质量评估（真实分数计算）
2. 规则有效性评估
3. 系统健康状态
4. 空输入边界条件
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault("SKIP_LLM", "true")

from src.evolution.self_evaluator import SelfEvaluator, EvaluationResult


class TestSelfEvaluator:
    """自我评估器测试套件"""

    def setup_method(self):
        """初始化"""
        from src.utils.config import ConfigManager
        ConfigManager._instance = None
        self.evaluator = SelfEvaluator()

    def teardown_method(self):
        from src.utils.config import ConfigManager
        ConfigManager._instance = None

    def test_empty_patterns_returns_zero_score(self):
        """空模式列表应返回 0 分"""
        result = self.evaluator.evaluate_learning_quality([], None)
        assert result.score == 0.0
        assert result.passed is False

    def test_patterns_with_confidence(self):
        """有置信度的模式应计算真实分数"""
        # 创建带有 confidence 属性的简单对象
        class MockPattern:
            def __init__(self, confidence, domain="test", logic_type="rule"):
                self.confidence = confidence
                self.domain = domain
                self.logic_type = logic_type
                self.usage_count = 1

        patterns = [
            MockPattern(0.9),
            MockPattern(0.8),
            MockPattern(0.7),
        ]
        result = self.evaluator.evaluate_learning_quality(patterns, None)
        # 分数应 > 0
        assert result.score > 0.0
        assert "learning_quality" in result.metric_name

    def test_patterns_as_dicts(self):
        """字典格式的模式也应正确评估"""
        patterns = [
            {"confidence": 0.9, "name": "test_pattern"},
            {"confidence": 0.7, "name": "test_pattern_2"},
        ]
        result = self.evaluator.evaluate_learning_quality(patterns, None)
        assert result.score > 0.0

    def test_patterns_as_strings(self):
        """字符串格式的模式应使用默认置信度"""
        patterns = ["pattern1", "pattern2", "pattern3"]
        result = self.evaluator.evaluate_learning_quality(patterns, None)
        assert result.score > 0.0

    def test_rule_effectiveness_no_cases(self):
        """无测试用例应返回 0 分"""
        result = self.evaluator.evaluate_rule_effectiveness("rule_1", [])
        assert result.score == 0.0
        assert result.passed is False

    def test_rule_effectiveness_with_passed_field(self):
        """包含 passed 字段的测试用例"""
        cases = [
            {"passed": True},
            {"passed": True},
            {"passed": False},
        ]
        result = self.evaluator.evaluate_rule_effectiveness("rule_1", cases)
        # 2/3 = 0.6667
        assert abs(result.score - 2/3) < 0.01

    def test_rule_effectiveness_with_output_comparison(self):
        """包含 expected/actual output 的测试用例"""
        cases = [
            {"expected_output": "A", "actual_output": "A"},
            {"expected_output": "B", "actual_output": "C"},
        ]
        result = self.evaluator.evaluate_rule_effectiveness("rule_2", cases)
        # 1/2 = 0.5
        assert abs(result.score - 0.5) < 0.01

    def test_system_health_default(self):
        """默认健康状态（无评估历史）"""
        health = self.evaluator.get_system_health()
        assert "status" in health
        assert "overall_score" in health
        assert health["evaluation_count"] == 0

    def test_system_health_after_evaluations(self):
        """评估后健康状态应反映真实数据"""
        # 执行一些评估
        self.evaluator.evaluate_learning_quality(
            [{"confidence": 0.9}], None
        )
        self.evaluator.evaluate_rule_effectiveness(
            "r1", [{"passed": True}]
        )
        health = self.evaluator.get_system_health()
        assert health["evaluation_count"] == 2
        assert health["overall_score"] > 0.0

    def test_inject_metrics(self):
        """注入的指标应出现在健康报告中"""
        self.evaluator.inject_metrics({"total_facts": 100})
        health = self.evaluator.get_system_health()
        assert health["total_facts"] == 100

    def test_evaluation_history_trimmed(self):
        """评估历史应不超过 1000 条"""
        for i in range(1100):
            self.evaluator.evaluate_rule_effectiveness(
                f"rule_{i}", [{"passed": True}]
            )
        assert len(self.evaluator.evaluation_history) <= 1000
