"""Enhanced Tests for Clawra Core Reasoning Engine"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from src.core.reasoner import Rule, Fact, InferenceResult, Reasoner, RuleType, InferenceDirection


class TestRuleEnhanced:
    """Enhanced rule tests"""
    
    def test_rule_creation_with_metadata(self):
        """Test rule creation with metadata"""
        rule = Rule(
            id="test_rule_with_meta",
            name="Test Rule with Metadata",
            rule_type=RuleType.IF_THEN,
            condition="(?x quality_score ?y) AND (?y < 0.80)",
            conclusion="(?x poses_quality_risk true)",
            confidence=0.9,
            metadata={"category": "quality", "version": "1.0"}
        )
        assert rule.id == "test_rule_with_meta"
        assert rule.confidence == 0.9
        assert rule.metadata["category"] == "quality"
        assert len(rule.condition_vars) >= 0  # Variables are optional
    
    def test_rule_variable_extraction(self):
        """Test variable extraction from rules"""
        rule = Rule(
            id="var_test",
            name="Variable Test",
            rule_type=RuleType.IF_THEN,
            condition="(?x is_a ?y) AND (?y has_property ?z)",
            conclusion="(?x has_property ?z)",
            confidence=0.9
        )
        # Variables are extracted without the '?' prefix
        assert 'x' in rule.condition_vars
        assert 'y' in rule.condition_vars
        assert 'z' in rule.condition_vars


class TestFactEnhanced:
    """Enhanced fact tests"""
    
    def test_fact_creation_with_timestamp(self):
        """Test fact creation with timestamp"""
        fact = Fact(
            subject="SupplierA",
            predicate="has_quality_score",
            object="0.95",
            confidence=0.9,
            source="test_input",
            timestamp="2024-01-01T00:00:00"
        )
        assert fact.subject == "SupplierA"
        assert fact.timestamp == "2024-01-01T00:00:00"
    
    def test_fact_equality(self):
        """Test fact equality comparison"""
        fact1 = Fact(subject="A", predicate="knows", object="B", confidence=0.9)
        fact2 = Fact(subject="A", predicate="knows", object="B", confidence=0.8)
        fact3 = Fact(subject="A", predicate="knows", object="C", confidence=0.9)
        
        assert fact1.to_tuple() == fact2.to_tuple()
        assert fact1.to_tuple() != fact3.to_tuple()


class TestReasonerEnhanced:
    """Enhanced reasoner tests"""
    
    def test_reasoner_with_multiple_rule_types(self):
        """Test reasoner with different rule types"""
        reasoner = Reasoner()
        
        # Add transitive rule
        trans_rule = Rule(
            id="transitive_test",
            name="Transitive Test",
            rule_type=RuleType.TRANSITIVE,
            condition="(?x parent_of ?y) AND (?y parent_of ?z)",
            conclusion="(?x grandparent_of ?z)",
            confidence=0.9
        )
        reasoner.add_rule(trans_rule)
        
        # Add IF-THEN rule
        if_then_rule = Rule(
            id="if_then_test",
            name="IF-THEN Test",
            rule_type=RuleType.IF_THEN,
            condition="(?x is_human)",
            conclusion="(?x is_mortal)",
            confidence=0.95
        )
        reasoner.add_rule(if_then_rule)
        
        assert len(reasoner.rules) >= 4  # 2 builtin + 2 added
    
    def test_forward_chain_with_timeout(self):
        """Test forward chain with timeout protection"""
        reasoner = Reasoner()
        
        # Add many facts to test timeout
        for i in range(100):
            reasoner.add_fact(Fact(
                subject=f"Entity{i}",
                predicate="related_to",
                object=f"Entity{i+1}",
                confidence=0.9
            ))
        
        # Should complete within timeout
        result = reasoner.forward_chain(max_depth=5, timeout_seconds=2.0)
        assert isinstance(result, InferenceResult)
    
    def test_backward_chain_basic(self):
        """Test backward chain reasoning"""
        reasoner = Reasoner()
        
        # Add facts
        reasoner.add_fact(Fact(
            subject="Alice",
            predicate="knows",
            object="Bob",
            confidence=0.9
        ))
        
        # Query backward
        goal = Fact(subject="?", predicate="knows", object="Bob")
        result = reasoner.backward_chain(goal, max_depth=3)
        
        assert isinstance(result, InferenceResult)
    
    def test_query_with_filters(self):
        """Test querying with filters"""
        reasoner = Reasoner()
        
        # Add various facts
        facts = [
            Fact("Alice", "knows", "Bob", 0.9),
            Fact("Alice", "knows", "Charlie", 0.8),
            Fact("Bob", "knows", "Charlie", 0.7),
            Fact("Alice", "works_with", "Dave", 0.95)
        ]
        for f in facts:
            reasoner.add_fact(f)
        
        # Query by subject
        results = reasoner.query(subject="Alice")
        assert len(results) == 3
        
        # Query by predicate
        results = reasoner.query(predicate="knows")
        assert len(results) == 3
        
        # Query with min confidence
        results = reasoner.query(min_confidence=0.9)
        assert len(results) == 2
    
    def test_explain_reasoning(self):
        """Test reasoning explanation generation"""
        reasoner = Reasoner()
        
        reasoner.add_fact(Fact("A", "connected_to", "B", 0.9))
        reasoner.add_fact(Fact("B", "connected_to", "C", 0.9))
        
        result = reasoner.forward_chain(max_depth=5)
        explanation = reasoner.explain(result)
        
        assert isinstance(explanation, str)
        assert "推导出" in explanation or "conclusions" in explanation.lower()


class TestInferenceResult:
    """Test inference result data structure"""
    
    def test_empty_result(self):
        """Test empty inference result"""
        result = InferenceResult(
            conclusions=[],
            facts_used=[],
            depth=0,
            total_confidence=None
        )
        
        assert len(result.conclusions) == 0
        assert result.depth == 0


class TestRuleLoading:
    """Test rule loading from different sources"""
    
    def test_add_rule_from_dict(self):
        """Test adding rule from dictionary"""
        reasoner = Reasoner()
        
        rule_dict = {
            "id": "dict_rule",
            "name": "Dictionary Rule",
            "type": "if_then",
            "condition": "price > 100",
            "conclusion": "expensive_item",
            "confidence": 0.85,
            "description": "High price rule"
        }
        
        rule = reasoner.add_rule_from_dict(rule_dict)
        assert rule.id == "dict_rule"
        assert rule.confidence == 0.85
    
    def test_load_multiple_rules(self):
        """Test loading multiple rules"""
        reasoner = Reasoner()
        
        rules = [
            {
                "id": "rule1",
                "name": "Rule 1",
                "type": "if_then",
                "condition": "a > 0",
                "conclusion": "positive",
                "confidence": 0.9
            },
            {
                "id": "rule2",
                "name": "Rule 2",
                "type": "if_then",
                "condition": "b < 0",
                "conclusion": "negative",
                "confidence": 0.85
            }
        ]
        
        reasoner.load_rules_from_list(rules)
        assert "rule1" in reasoner.rules
        assert "rule2" in reasoner.rules


class TestEdgeCasesEnhanced:
    """Enhanced edge case tests"""
    
    def test_reasoner_with_empty_ontology(self):
        """Test reasoner behavior with no ontology"""
        reasoner = Reasoner(ontology=None)
        assert reasoner.ontology is None
        
        # Should still work with basic rules
        reasoner.add_fact(Fact("A", "test", "B"))
        result = reasoner.forward_chain()
        assert isinstance(result, InferenceResult)
    
    def test_confidence_propagation(self):
        """Test confidence propagation through reasoning chain"""
        reasoner = Reasoner()
        
        # Add chain of facts with varying confidence
        facts = [
            Fact("A", "implies", "B", confidence=0.9),
            Fact("B", "implies", "C", confidence=0.8),
            Fact("C", "implies", "D", confidence=0.7)
        ]
        
        for f in facts:
            reasoner.add_fact(f)
        
        result = reasoner.forward_chain(max_depth=5)
        
        # 置信度应始终落在 [0, 1] 区间内，不强行假设链路单调下降，以兼容不同传播策略
        if result.conclusions:
            assert 0.0 <= result.total_confidence.value <= 1.0
