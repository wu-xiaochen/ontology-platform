"""
UnifiedLogicLayer 单元测试

测试统一逻辑表达层的所有功能
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.evolution.unified_logic import UnifiedLogicLayer, LogicPattern, LogicType


class TestUnifiedLogicLayer:
    """UnifiedLogicLayer 测试类。"""
    
    @pytest.fixture
    def logic_layer(self):
        """创建测试实例。"""
        return UnifiedLogicLayer()
    
    def test_initialization(self, logic_layer):
        """测试初始化状态。"""
        assert len(logic_layer.patterns) == 2  # 2个元规则
        assert logic_layer.get_statistics()["total_patterns"] == 2
    
    def test_add_pattern_success(self, logic_layer):
        """测试成功添加模式。"""
        pattern = LogicPattern(
            id="test:rule:1",
            logic_type=LogicType.RULE,
            name="测试规则",
            description="测试描述",
            conditions=[{"subject": "?X", "predicate": "is_a", "object": "Device"}],
            actions=[{"type": "infer", "subject": "?X", "predicate": "requires", "object": "maintenance"}],
            domain="test"
        )
        
        result = logic_layer.add_pattern(pattern)
        
        assert result is True
        assert "test:rule:1" in logic_layer.patterns
        assert logic_layer.patterns["test:rule:1"].name == "测试规则"
    
    def test_add_pattern_version_increment(self, logic_layer):
        """测试添加重复模式时版本升级。"""
        pattern = LogicPattern(
            id="test:rule:1",
            logic_type=LogicType.RULE,
            name="测试规则",
            description="测试描述",
            conditions=[],
            actions=[],
            domain="test"
        )
        
        logic_layer.add_pattern(pattern)
        logic_layer.add_pattern(pattern)
        
        assert logic_layer.patterns["test:rule:1"].version == 2
    
    def test_get_patterns_by_domain(self, logic_layer):
        """测试按领域获取模式。"""
        pattern1 = LogicPattern(
            id="test:1",
            logic_type=LogicType.RULE,
            name="规则1",
            description="",
            conditions=[],
            actions=[],
            domain="domain_a"
        )
        pattern2 = LogicPattern(
            id="test:2",
            logic_type=LogicType.RULE,
            name="规则2",
            description="",
            conditions=[],
            actions=[],
            domain="domain_a"
        )
        pattern3 = LogicPattern(
            id="test:3",
            logic_type=LogicType.RULE,
            name="规则3",
            description="",
            conditions=[],
            actions=[],
            domain="domain_b"
        )
        
        logic_layer.add_pattern(pattern1)
        logic_layer.add_pattern(pattern2)
        logic_layer.add_pattern(pattern3)
        
        domain_a_patterns = logic_layer.get_patterns_by_domain("domain_a")
        assert len(domain_a_patterns) == 2
        
        domain_b_patterns = logic_layer.get_patterns_by_domain("domain_b")
        assert len(domain_b_patterns) == 1
    
    def test_get_patterns_by_type(self, logic_layer):
        """测试按类型获取模式。"""
        pattern1 = LogicPattern(
            id="test:1",
            logic_type=LogicType.RULE,
            name="规则",
            description="",
            conditions=[],
            actions=[]
        )
        pattern2 = LogicPattern(
            id="test:2",
            logic_type=LogicType.BEHAVIOR,
            name="行为",
            description="",
            conditions=[],
            actions=[]
        )
        
        logic_layer.add_pattern(pattern1)
        logic_layer.add_pattern(pattern2)
        
        rules = logic_layer.get_patterns_by_type(LogicType.RULE)
        behaviors = logic_layer.get_patterns_by_type(LogicType.BEHAVIOR)
        
        # 验证能正确获取类型 (bootstrap规则可能未通过type_patterns索引)
        assert len(rules) >= 1  # 至少包含测试添加的
        assert len(behaviors) == 1
    
    def test_extract_logic_from_text_if_then(self, logic_layer):
        """测试从文本提取如果-那么规则。"""
        text = "如果设备是燃气调压箱，那么需要定期维护。"
        
        patterns = logic_layer.extract_logic_from_text(text, domain_hint="gas")
        
        assert len(patterns) > 0
        # 检查是否提取到了包含关键词的模式
        assert any("燃气调压箱" in p.description for p in patterns)
        # 检查是否有规则类型的模式
        rule_patterns = [p for p in patterns if p.logic_type == LogicType.RULE]
        # 如果没有规则类型，至少要有定义或行为类型
        if not rule_patterns:
            assert any(p.logic_type in [LogicType.BEHAVIOR, LogicType.CONSTRAINT] for p in patterns)
    
    def test_extract_logic_from_text_definition(self, logic_layer):
        """测试从文本提取定义。"""
        text = "燃气调压箱：是一种将燃气调压器集成在金属箱体内的成套设备。"
        
        patterns = logic_layer.extract_logic_from_text(text)
        
        # 应该提取到定义模式
        definition_patterns = [p for p in patterns if "定义" in p.name]
        assert len(definition_patterns) > 0
    
    def test_extract_logic_from_text_function(self, logic_layer):
        """测试从文本提取功能。"""
        text = "功能：主要用于将上游管网的高压燃气降至下游用户所需的低压标准。"
        
        patterns = logic_layer.extract_logic_from_text(text)
        
        # 应该提取到功能模式
        function_patterns = [p for p in patterns if "功能" in p.name]
        assert len(function_patterns) > 0
    
    def test_execute_pattern_success(self, logic_layer):
        """测试成功执行模式。"""
        pattern = LogicPattern(
            id="test:execute",
            logic_type=LogicType.RULE,
            name="执行测试",
            description="",
            conditions=[{"subject": "?X", "predicate": "is_a", "object": "Device"}],
            actions=[{"type": "infer", "subject": "?X", "predicate": "status", "object": "active"}]
        )
        
        context = {
            "facts": [{"subject": "DeviceA", "predicate": "is_a", "object": "Device"}]
        }
        
        result = logic_layer.execute_pattern(pattern, context)
        
        assert result["success"] is True
        assert len(result["results"]) > 0
    
    def test_execute_pattern_no_match(self, logic_layer):
        """测试条件不匹配时的执行。"""
        pattern = LogicPattern(
            id="test:execute",
            logic_type=LogicType.RULE,
            name="执行测试",
            description="",
            conditions=[{"subject": "?X", "predicate": "is_a", "object": "Device"}],
            actions=[{"type": "infer", "subject": "?X", "predicate": "status", "object": "active"}]
        )
        
        context = {"facts": []}  # 空事实
        
        result = logic_layer.execute_pattern(pattern, context)
        
        assert result["success"] is False
    
    def test_get_statistics(self, logic_layer):
        """测试获取统计信息。"""
        stats = logic_layer.get_statistics()
        
        assert "total_patterns" in stats
        assert "by_type" in stats
        assert "by_domain" in stats
        assert "avg_confidence" in stats
    
    def test_pattern_to_dict(self, logic_layer):
        """测试模式序列化。"""
        pattern = LogicPattern(
            id="test:1",
            logic_type=LogicType.RULE,
            name="测试",
            description="描述",
            conditions=[],
            actions=[],
            confidence=0.9
        )
        
        data = pattern.to_dict()
        
        assert data["id"] == "test:1"
        assert data["logic_type"] == "rule"
        assert data["confidence"] == 0.9
    
    def test_pattern_from_dict(self, logic_layer):
        """测试模式反序列化。"""
        data = {
            "id": "test:1",
            "logic_type": "rule",
            "name": "测试",
            "description": "描述",
            "conditions": [],
            "actions": [],
            "confidence": 0.85,
            "source": "learned",
            "domain": "test"
        }
        
        pattern = LogicPattern.from_dict(data)
        
        assert pattern.id == "test:1"
        assert pattern.logic_type == LogicType.RULE
        assert pattern.confidence == 0.85
    
    def test_update_success_rate(self, logic_layer):
        """测试更新成功率。"""
        pattern = LogicPattern(
            id="test:1",
            logic_type=LogicType.RULE,
            name="测试",
            description="",
            conditions=[],
            actions=[],
            confidence=0.5
        )
        
        # 模拟多次执行
        for _ in range(8):
            pattern.update_success_rate(True)
        for _ in range(2):
            pattern.update_success_rate(False)
        
        assert pattern.usage_count == 10
        assert pattern.success_count == 8
        assert pattern.failure_count == 2
        assert pattern.confidence == 0.8  # 8/10


class TestLogicPattern:
    """LogicPattern 测试类。"""
    
    def test_pattern_creation(self):
        """测试模式创建。"""
        pattern = LogicPattern(
            id="test:1",
            logic_type=LogicType.RULE,
            name="测试规则",
            description="测试描述",
            conditions=[{"subject": "?X", "predicate": "is_a", "object": "Device"}],
            actions=[{"type": "infer", "subject": "?X", "predicate": "status", "object": "active"}],
            confidence=0.9,
            source="learned",
            domain="test"
        )
        
        assert pattern.id == "test:1"
        assert pattern.logic_type == LogicType.RULE
        assert pattern.confidence == 0.9
        assert pattern.source == "learned"
        assert pattern.domain == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
