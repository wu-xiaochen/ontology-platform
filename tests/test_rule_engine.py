"""Tests for Enhanced Rule Engine"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import tempfile
from pathlib import Path
from src.core.ontology.rule_engine import SafeMathSandbox, OntologyRule, RuleEngine


class TestSafeMathSandbox:
    """Test safe math sandbox"""
    
    def test_basic_arithmetic(self):
        """Test basic arithmetic operations"""
        assert SafeMathSandbox.evaluate("1 + 2", {}) == 3
        assert SafeMathSandbox.evaluate("10 - 3", {}) == 7
        assert SafeMathSandbox.evaluate("4 * 5", {}) == 20
        assert SafeMathSandbox.evaluate("15 / 3", {}) == 5.0
    
    def test_power_operation(self):
        """Test power operation"""
        assert SafeMathSandbox.evaluate("2 ** 3", {}) == 8
        assert SafeMathSandbox.evaluate("10 ** 2", {}) == 100
    
    def test_comparison_operations(self):
        """Test comparison operations"""
        assert SafeMathSandbox.evaluate("5 > 3", {}) == True
        assert SafeMathSandbox.evaluate("5 < 3", {}) == False
        assert SafeMathSandbox.evaluate("5 >= 5", {}) == True
        assert SafeMathSandbox.evaluate("5 <= 4", {}) == False
        assert SafeMathSandbox.evaluate("5 == 5", {}) == True
        assert SafeMathSandbox.evaluate("5 != 4", {}) == True
    
    def test_logical_operations(self):
        """Test logical operations"""
        assert SafeMathSandbox.evaluate("True and False", {}) == False
        assert SafeMathSandbox.evaluate("True or False", {}) == True
        assert SafeMathSandbox.evaluate("not False", {}) == True
    
    def test_variable_substitution(self):
        """Test variable substitution"""
        context = {"x": 10, "y": 20}
        assert SafeMathSandbox.evaluate("x + y", context) == 30
        assert SafeMathSandbox.evaluate("x * 2", context) == 20
    
    def test_allowed_functions(self):
        """Test allowed functions"""
        assert SafeMathSandbox.evaluate("abs(-5)", {}) == 5
        assert SafeMathSandbox.evaluate("min(1, 2, 3)", {}) == 1
        assert SafeMathSandbox.evaluate("max(1, 2, 3)", {}) == 3
        assert SafeMathSandbox.evaluate("round(3.7)", {}) == 4
    
    def test_complex_expression(self):
        """Test complex expressions"""
        context = {"supply_capacity": 100, "flow_requirement": 50}
        result = SafeMathSandbox.evaluate("supply_capacity >= flow_requirement * 1.5", context)
        assert result == True
        
        context2 = {"supply_capacity": 60, "flow_requirement": 50}
        result2 = SafeMathSandbox.evaluate("supply_capacity >= flow_requirement * 1.5", context2)
        assert result2 == False
    
    def test_unsupported_operation(self):
        """Test that unsupported operations raise error"""
        with pytest.raises((TypeError, ValueError)):
            # Lambda functions should not be allowed
            SafeMathSandbox.evaluate("lambda x: x + 1", {})
    
    def test_undefined_variable(self):
        """Test undefined variable error"""
        with pytest.raises(ValueError):
            SafeMathSandbox.evaluate("undefined_var + 1", {})


class TestOntologyRule:
    """Test ontology rule dataclass"""
    
    def test_rule_creation(self):
        """Test rule creation"""
        rule = OntologyRule(
            id="test_rule",
            target_object_class="TestClass",
            expression="value > 0",
            description="Test rule description"
        )
        
        assert rule.id == "test_rule"
        assert rule.version == "1.0.0"
        assert rule.metadata == {}
    
    def test_rule_serialization(self):
        """Test rule serialization"""
        rule = OntologyRule(
            id="serialize_test",
            target_object_class="TestClass",
            expression="x < y",
            description="Serialization test",
            version="2.0.0"
        )
        
        rule_dict = rule.to_dict()
        assert rule_dict["id"] == "serialize_test"
        assert rule_dict["version"] == "2.0.0"
        
        # Deserialize
        restored = OntologyRule.from_dict(rule_dict)
        assert restored.id == rule.id
        assert restored.expression == rule.expression


class TestRuleEngine:
    """Test enhanced rule engine"""
    
    def test_default_rules_loaded(self):
        """Test that default rules are loaded"""
        engine = RuleEngine()
        assert len(engine.rules) >= 4
        assert "rule:gas_regulator_safety_margin" in engine.rules
    
    def test_register_new_rule(self):
        """Test registering new rule"""
        engine = RuleEngine()
        initial_count = len(engine.rules)
        
        rule = OntologyRule(
            id="custom_rule",
            target_object_class="CustomObject",
            expression="value >= 0",
            description="Custom validation rule"
        )
        
        result = engine.register_rule(rule)
        assert result["status"] == "success"
        assert len(engine.rules) == initial_count + 1
    
    def test_conflict_detection(self):
        """Test rule conflict detection"""
        engine = RuleEngine()
        
        # Add first rule
        rule1 = OntologyRule(
            id="conflict_rule_1",
            target_object_class="TestObject",
            expression="price > 100",
            description="Rule 1"
        )
        engine.register_rule(rule1)
        
        # Add potentially conflicting rule
        rule2 = OntologyRule(
            id="conflict_rule_2",
            target_object_class="TestObject",
            expression="price < 50",
            description="Rule 2"
        )
        
        result = engine.register_rule(rule2)
        # Should detect potential conflict
        assert len(result.get("warnings", [])) > 0
    
    def test_rule_evaluation_pass(self):
        """Test rule evaluation that passes"""
        engine = RuleEngine()
        
        context = {
            "supply_capacity": 100,
            "flow_requirement": 50
        }
        
        result = engine.evaluate_rule("rule:gas_regulator_safety_margin", context)
        assert result["status"] == "PASS"
    
    def test_rule_evaluation_fail(self):
        """Test rule evaluation that fails"""
        engine = RuleEngine()
        
        context = {
            "supply_capacity": 60,
            "flow_requirement": 50
        }
        
        result = engine.evaluate_rule("rule:gas_regulator_safety_margin", context)
        assert result["status"] == "FAIL"
    
    def test_rule_evaluation_not_found(self):
        """Test evaluation with non-existent rule"""
        engine = RuleEngine()
        result = engine.evaluate_rule("non_existent_rule", {})
        assert result["status"] == "ERROR"
    
    def test_get_rules_for_object(self):
        """Test getting rules for specific object class"""
        engine = RuleEngine()
        
        rules = engine.get_rules_for_object("GasRegulator")
        assert len(rules) >= 2  # At least safety_margin and pressure_range
    
    def test_evaluate_action_preconditions(self):
        """Test evaluating action preconditions"""
        engine = RuleEngine()
        
        context = {
            "supply_capacity": 100,
            "flow_requirement": 50,
            "outlet_pressure": 0.1
        }
        
        results = engine.evaluate_action_preconditions(
            "test_action",
            "GasRegulator",
            context
        )
        
        assert len(results) >= 2
        # All should pass with these values
        for result in results:
            assert result["status"] == "PASS"
    
    def test_audit_trail(self):
        """Test rule change audit trail"""
        engine = RuleEngine()
        
        # Add a rule
        rule = OntologyRule(
            id="audit_test_rule",
            target_object_class="TestClass",
            expression="x > 0",
            description="Audit test"
        )
        engine.register_rule(rule)
        
        # Update the rule
        updated_rule = OntologyRule(
            id="audit_test_rule",
            target_object_class="TestClass",
            expression="x > 10",
            description="Updated audit test",
            version="2.0.0"
        )
        engine.register_rule(updated_rule)
        
        # Check audit trail
        assert len(engine.rule_history) >= 2
        assert engine.rule_history[-1]["action"] == "UPDATE"


class TestRuleEngineFileIO:
    """Test rule engine file I/O"""
    
    def test_save_and_load_yaml(self):
        """Test saving and loading rules from YAML"""
        engine = RuleEngine()
        
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            filepath = Path(f.name)
        
        try:
            # Save rules
            engine.save_rules_to_file(filepath)
            
            # Load into new engine
            new_engine = RuleEngine(rules_path=filepath)
            
            # Should have same rules
            assert len(new_engine.rules) == len(engine.rules)
        finally:
            if filepath.exists():
                filepath.unlink()
    
    def test_save_and_load_json(self):
        """Test saving and loading rules from JSON"""
        engine = RuleEngine()
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = Path(f.name)
        
        try:
            # Save rules
            engine.save_rules_to_file(filepath)
            
            # Load into new engine
            new_engine = RuleEngine(rules_path=filepath)
            
            # Should have same rules
            assert len(new_engine.rules) == len(engine.rules)
        finally:
            if filepath.exists():
                filepath.unlink()
    
    def test_load_nonexistent_file(self):
        """Test loading from non-existent file"""
        with pytest.raises(FileNotFoundError):
            RuleEngine(rules_path=Path("/nonexistent/path.yaml"))
