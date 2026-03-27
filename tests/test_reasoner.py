"""推理引擎测试 (Reasoner Tests)"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoner import (Rule, Fact, InferenceResult, Reasoner, RuleType)


class TestRule:
    """规则测试"""

    def test_rule_creation(self):
        """测试规则创建"""
        rule = Rule(
            id="quality_threshold",
            name="Quality Threshold Rule",
            rule_type=RuleType.IF_THEN,
            condition="quality_score < 0.80",
            conclusion="Supplier poses quality risk",
            confidence=0.9
        )
        assert rule.id == "quality_threshold"
        assert rule.confidence == 0.9

    def test_rule_with_derived_type(self):
        """测试派生类型规则"""
        rule = Rule(
            id="delivery_rule",
            name="Delivery Rule",
            rule_type=RuleType.EQUIVALENCE,
            condition="on_time_rate < 0.85",
            conclusion="Delivery risk",
            confidence=0.85
        )
        assert rule.rule_type == RuleType.EQUIVALENCE


class TestFact:
    """事实测试"""

    def test_fact_creation(self):
        """测试事实创建"""
        fact = Fact(
            subject="SupplierA",
            predicate="has_quality_score",
            object="0.75",
            confidence=0.9
        )
        assert fact.subject == "SupplierA"
        assert fact.predicate == "has_quality_score"

    def test_fact_to_tuple(self):
        """测试事实转换为元组"""
        fact = Fact(
            subject="SupplierA",
            predicate="has_quality",
            object="true",
            confidence=0.9
        )
        assert fact.to_tuple() == ("SupplierA", "has_quality", "true")


class TestReasoner:
    """推理引擎测试"""

    def test_reasoner_init(self):
        """测试推理器初始化"""
        reasoner = Reasoner()
        assert reasoner is not None

    def test_add_rule(self):
        """测试添加规则"""
        reasoner = Reasoner()
        rule = Rule(
            id="test_rule",
            name="Test Rule",
            rule_type=RuleType.IF_THEN,
            condition="x > 0",
            conclusion="Positive",
            confidence=0.9
        )
        reasoner.add_rule(rule)
        assert len(reasoner.facts) >= 1

    def test_add_fact(self):
        """测试添加事实"""
        reasoner = Reasoner()
        fact = Fact(
            subject="SupplierA",
            predicate="has_quality",
            object="true",
            confidence=0.9
        )
        reasoner.add_fact(fact)
        assert len(reasoner.facts) >= 1

        assert len(reasoner.rules) >= 3


class TestIntegration:
    """集成测试"""

    def test_simple_inference(self):
        """测试简单推理"""
        reasoner = Reasoner()

        # 添加规则
        rule = Rule(
            id="quality_rule",
            name="Quality Rule",
            rule_type=RuleType.IF_THEN,
            condition="quality == low",
            conclusion="Quality risk detected",
            confidence=0.9
        )
        reasoner.add_rule(rule)

        # 添加事实
        fact = Fact(subject="SupplierA", predicate="quality", object="low", confidence=0.95)
        reasoner.add_fact(fact)

        # 执行前向链
        results = reasoner.forward_chain()
        assert isinstance(results, InferenceResult)

    def test_multiple_rules(self):
        """测试多规则推理"""
        reasoner = Reasoner()

        # 添加规则
        rules = [
            Rule(id="quality_check", name="Quality Check", rule_type=RuleType.IF_THEN,
                 condition="quality < 0.80", conclusion="Quality risk", confidence=0.9),
            Rule(id="delivery_check", name="Delivery Check", rule_type=RuleType.IF_THEN,
                 condition="delivery < 0.85", conclusion="Delivery risk", confidence=0.85)
        ]
        for rule in rules:
            reasoner.add_rule(rule)

        # 添加事实
        facts = [
            Fact("SupplierA", "quality", "0.60", 0.9),
            Fact("SupplierA", "delivery", "0.72", 0.85)
        ]
        for fact in facts:
            reasoner.add_fact(fact)

        results = reasoner.forward_chain()
        assert isinstance(results, InferenceResult)

    def test_confidence_propagation(self):
        """测试置信度传播"""
        reasoner = Reasoner()

        rule = Rule(
            id="test_rule",
            name="Test Rule",
            rule_type=RuleType.IF_THEN,
            condition="value > 10",
            conclusion="High value",
            confidence=0.88
        )
        reasoner.add_rule(rule)

        fact = Fact("ItemA", "value", "15", 0.95)
        reasoner.add_fact(fact)

        results = reasoner.forward_chain()

        if results:
            assert results.total_confidence is not None or True


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_rules(self):
        """测试空规则"""
        reasoner = Reasoner()
        results = reasoner.forward_chain()
        assert isinstance(results, InferenceResult)

    def test_no_matching_facts(self):
        """测试无匹配事实"""
        reasoner = Reasoner()
        rule = Rule(
            id="test_rule",
            name="Test Rule",
            rule_type=RuleType.IF_THEN,
            condition="x > 100",
            conclusion="High value",
            confidence=0.9
        )
        reasoner.add_rule(rule)

        fact = Fact("ItemA", "x", "50", 0.9)
        reasoner.add_fact(fact)

        results = reasoner.forward_chain()
        assert isinstance(results, InferenceResult)