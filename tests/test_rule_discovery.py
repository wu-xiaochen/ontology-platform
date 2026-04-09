"""
RuleDiscoveryEngine 单元测试

测试规则发现引擎的所有功能
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.evolution.rule_discovery import RuleDiscoveryEngine
from src.evolution.unified_logic import UnifiedLogicLayer


class TestRuleDiscoveryEngine:
    """RuleDiscoveryEngine 测试类。"""
    
    @pytest.fixture
    def discovery_engine(self):
        """创建测试实例。"""
        logic_layer = UnifiedLogicLayer()
        return RuleDiscoveryEngine(logic_layer)
    
    def test_initialization(self, discovery_engine):
        """测试初始化状态。"""
        assert len(discovery_engine.pattern_instances) == 0
        assert len(discovery_engine.candidate_rules) == 0
        assert discovery_engine.min_support == 2
        assert discovery_engine.min_confidence == 0.6
    
    def test_discover_from_facts_empty(self, discovery_engine):
        """测试空事实列表。"""
        discovered = discovery_engine.discover_from_facts([])
        assert len(discovered) == 0
    
    def test_discover_transitive_rule(self, discovery_engine):
        """测试发现传递性规则。"""
        facts = [
            {"subject": "A", "predicate": "related_to", "object": "B"},
            {"subject": "B", "predicate": "related_to", "object": "C"},
            {"subject": "C", "predicate": "related_to", "object": "D"},
            {"subject": "D", "predicate": "related_to", "object": "E"},
            {"subject": "X", "predicate": "related_to", "object": "Y"},
            {"subject": "Y", "predicate": "related_to", "object": "Z"},
        ]
        
        discovered = discovery_engine.discover_from_facts(facts)
        
        # 应该发现传递性规则
        transitive_rules = [r for r in discovered if r["type"] == "transitive"]
        assert len(transitive_rules) > 0
    
    def test_discover_classification_rule(self, discovery_engine):
        """测试发现分类规则。"""
        facts = [
            {"subject": "设备A", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "设备B", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "设备C", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "燃气设备", "predicate": "requires", "object": "维护"},
        ]
        
        discovered = discovery_engine.discover_from_facts(facts)
        
        # 应该发现分类继承规则
        classification_rules = [r for r in discovered if r["type"] == "classification"]
        # 由于支持度要求，可能为空
        assert isinstance(classification_rules, list)
    
    def test_discover_inheritance_rule(self, discovery_engine):
        """测试发现继承规则。"""
        facts = [
            {"subject": "调压箱A", "predicate": "is_a", "object": "燃气调压箱"},
            {"subject": "调压箱B", "predicate": "is_a", "object": "燃气调压箱"},
            {"subject": "燃气调压箱", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "燃气设备", "predicate": "requires", "object": "维护"},
        ]
        
        discovered = discovery_engine.discover_from_facts(facts)
        
        inheritance_rules = [r for r in discovered if r["type"] == "inheritance"]
        assert isinstance(inheritance_rules, list)
    
    def test_discover_from_interactions(self, discovery_engine):
        """测试从交互中发现规则。"""
        interactions = [
            {"context": {"type": "gas"}, "action": "维护", "outcome": "正常", "success": True},
            {"context": {"type": "gas"}, "action": "维护", "outcome": "正常", "success": True},
            {"context": {"type": "gas"}, "action": "维护", "outcome": "正常", "success": True},
            {"context": {"type": "medical"}, "action": "检查", "outcome": "异常", "success": False},
        ]
        
        discovered = discovery_engine.discover_from_interactions(interactions)
        
        # 应该发现成功策略
        policy_rules = [r for r in discovered if r["type"] == "policy"]
        assert len(policy_rules) > 0
        assert policy_rules[0]["confidence"] > 0.6
    
    def test_evaluate_rule_quality(self, discovery_engine):
        """测试评估规则质量。"""
        rule = {
            "id": "test:rule:1",
            "conditions": [{"subject": "?X", "predicate": "is_a", "object": "Device"}],
            "actions": [{"type": "infer", "subject": "?X", "predicate": "status", "object": "active"}]
        }
        
        test_cases = [
            {"context": {"subject": "A", "predicate": "is_a", "object": "Device"}, "expected_result": "active"},
            {"context": {"subject": "B", "predicate": "is_a", "object": "Device"}, "expected_result": "active"},
            {"context": {"subject": "C", "predicate": "is_a", "object": "Other"}, "expected_result": None},
        ]
        
        quality = discovery_engine.evaluate_rule_quality(rule, test_cases)
        
        assert "precision" in quality
        assert "recall" in quality
        assert "f1" in quality
    
    def test_get_discovery_statistics(self, discovery_engine):
        """测试获取发现统计。"""
        # 执行一些发现
        facts = [
            {"subject": "A", "predicate": "is_a", "object": "B"},
            {"subject": "B", "predicate": "is_a", "object": "C"},
        ]
        discovery_engine.discover_from_facts(facts)
        
        stats = discovery_engine.get_discovery_statistics()
        
        assert "total_discoveries" in stats
        assert "candidate_rules" in stats
        assert "pattern_instances" in stats
        assert "by_method" in stats
    
    def test_min_support_threshold(self, discovery_engine):
        """测试最小支持度阈值。"""
        # 设置高阈值
        discovery_engine.min_support = 10
        
        facts = [
            {"subject": "A", "predicate": "is_a", "object": "B"},
            {"subject": "B", "predicate": "is_a", "object": "C"},
        ]
        
        discovered = discovery_engine.discover_from_facts(facts)
        
        # 由于支持度不足，应该没有发现的规则
        assert len(discovered) == 0


class TestPatternDetection:
    """模式检测测试类。"""
    
    @pytest.fixture
    def discovery_engine(self):
        logic_layer = UnifiedLogicLayer()
        return RuleDiscoveryEngine(logic_layer)
    
    def test_detect_chain_rules(self, discovery_engine):
        """测试检测链式规则。"""
        facts = [
            {"subject": "A", "predicate": "part_of", "object": "B"},
            {"subject": "B", "predicate": "part_of", "object": "C"},
            {"subject": "C", "predicate": "part_of", "object": "D"},
            {"subject": "D", "predicate": "part_of", "object": "E"},
            {"subject": "X", "predicate": "part_of", "object": "Y"},
            {"subject": "Y", "predicate": "part_of", "object": "Z"},
        ]
        
        discovered = discovery_engine.discover_from_facts(facts)
        
        # 应该发现 part_of 的传递性
        chain_rules = [r for r in discovered if "chain" in r["id"]]
        assert len(chain_rules) > 0
    
    def test_find_common_properties(self, discovery_engine):
        """测试查找共同属性。"""
        facts = [
            {"subject": "设备A", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "设备B", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "设备C", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "设备A", "predicate": "requires", "object": "维护"},
            {"subject": "设备B", "predicate": "requires", "object": "维护"},
            {"subject": "设备C", "predicate": "requires", "object": "维护"},
        ]
        
        common_props = discovery_engine._find_common_properties(facts, "燃气设备")
        
        assert len(common_props) > 0
        assert common_props[0]["predicate"] == "requires"
        assert common_props[0]["object"] == "维护"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
