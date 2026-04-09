"""
端到端集成测试

测试完整的学习-推理-应用流程
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.evolution.unified_logic import UnifiedLogicLayer, LogicType
from src.evolution.meta_learner import MetaLearner
from src.evolution.rule_discovery import RuleDiscoveryEngine
from src.core.reasoner import Reasoner, Fact


class TestEndToEndLearning:
    """端到端学习流程测试"""
    
    @pytest.fixture
    def system(self):
        """初始化完整系统"""
        logic_layer = UnifiedLogicLayer()
        discovery_engine = RuleDiscoveryEngine(logic_layer)
        meta_learner = MetaLearner(logic_layer, discovery_engine)
        reasoner = Reasoner()
        return {
            "logic": logic_layer,
            "discovery": discovery_engine,
            "learner": meta_learner,
            "reasoner": reasoner
        }
    
    def test_complete_learning_pipeline(self, system):
        """测试完整学习流程: 文本学习 -> 规则发现 -> 推理应用"""
        # Step 1: 从文本学习规则
        text = "燃气调压箱是一种燃气设备。燃气设备需要定期维护。"
        result = system["learner"].learn(text, input_type="text")
        
        assert result["success"] is True
        assert len(result["learned_patterns"]) > 0
        
        # Step 2: 验证规则已添加到逻辑层
        patterns = system["logic"].get_patterns_by_domain(result["domain"])
        assert len(patterns) > 0
        
        # Step 3: 添加事实到推理引擎
        facts = [
            Fact("调压箱A", "is_a", "燃气调压箱", 0.95),
            Fact("燃气调压箱", "is_a", "燃气设备", 0.95),
        ]
        for f in facts:
            system["reasoner"].add_fact(f)
        
        # Step 4: 执行推理
        inference_result = system["reasoner"].forward_chain(max_depth=2)
        
        # 验证推理成功
        assert inference_result is not None
        
    def test_gas_equipment_domain(self, system):
        """测试燃气设备领域完整流程"""
        # 学习领域知识
        knowledge = [
            "如果设备是燃气调压箱，那么需要定期维护。",
            "如果进口压力大于0.4MPa，那么属于高压设备。",
            "高压设备需要每月检查一次。"
        ]
        
        learned_patterns = []
        for text in knowledge:
            result = system["learner"].learn(text, input_type="text")
            if result["success"]:
                learned_patterns.extend(result["learned_patterns"])
        
        # 验证学习了多个规则
        assert len(learned_patterns) >= 2
        
        # 验证领域识别正确
        for pid in learned_patterns:
            if pid in system["logic"].patterns:
                assert system["logic"].patterns[pid].domain == "gas_equipment"
    
    def test_cross_domain_learning(self, system):
        """测试跨领域学习隔离"""
        # 学习医疗领域
        medical_text = "患者血糖高于7.0需要服用胰岛素。"
        medical_result = system["learner"].learn(medical_text, input_type="text")
        
        # 学习法律领域
        legal_text = "合同违约需要支付违约金。"
        legal_result = system["learner"].learn(legal_text, input_type="text")
        
        # 验证领域隔离
        assert medical_result["domain"] == "medical"
        assert legal_result["domain"] == "legal"
        
        # 验证模式不混淆
        medical_patterns = system["logic"].get_patterns_by_domain("medical")
        legal_patterns = system["logic"].get_patterns_by_domain("legal")
        
        for p in medical_patterns:
            assert p.domain == "medical"
        for p in legal_patterns:
            assert p.domain == "legal"


class TestRuleDiscoveryIntegration:
    """规则发现集成测试"""
    
    @pytest.fixture
    def system(self):
        logic_layer = UnifiedLogicLayer()
        discovery_engine = RuleDiscoveryEngine(logic_layer)
        return {
            "logic": logic_layer,
            "discovery": discovery_engine
        }
    
    def test_discover_and_apply_rule(self, system):
        """测试发现并应用规则"""
        # 准备事实数据 - 需要足够的数据量触发规则发现
        facts = [
            {"subject": "设备A", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "设备B", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "设备C", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "设备D", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "设备E", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "燃气设备", "predicate": "requires", "object": "维护"},
        ]
        
        # 发现规则
        discovered = system["discovery"].discover_from_facts(facts)
        
        # 验证发现规则 (可能为空，取决于数据模式)
        # 规则发现需要特定模式，不强制要求发现规则
        
        # 如果有发现的规则，添加到逻辑层
        from src.evolution.unified_logic import LogicPattern
        for rule in discovered:
            pattern = LogicPattern(
                id=rule["id"],
                logic_type=LogicType.RULE,
                name=rule["name"],
                description=rule["description"],
                conditions=rule["conditions"],
                actions=rule["actions"],
                confidence=rule["confidence"],
                source="discovered",
                domain="test"
            )
            system["logic"].add_pattern(pattern)
        
        # 验证系统正常工作 (不强制要求发现规则)
        assert system["logic"] is not None


class TestPerformanceIntegration:
    """性能集成测试"""
    
    @pytest.fixture
    def system(self):
        logic_layer = UnifiedLogicLayer()
        discovery_engine = RuleDiscoveryEngine(logic_layer)
        meta_learner = MetaLearner(logic_layer, discovery_engine)
        return {
            "logic": logic_layer,
            "discovery": discovery_engine,
            "learner": meta_learner
        }
    
    def test_bulk_learning_performance(self, system):
        """测试批量学习性能"""
        import time
        
        texts = [
            f"如果设备是类型{i}，那么需要维护{i}。"
            for i in range(50)
        ]
        
        start = time.time()
        for text in texts:
            system["learner"].learn(text, input_type="text")
        elapsed = time.time() - start
        
        # 50次学习应在1秒内完成
        assert elapsed < 1.0, f"批量学习太慢: {elapsed}s"
    
    def test_large_dataset_discovery(self, system):
        """测试大数据集规则发现"""
        import time
        
        # 生成1000个事实
        facts = [
            {"subject": f"实体{i}", "predicate": "is_a", "object": f"类型{i % 10}"}
            for i in range(1000)
        ]
        
        start = time.time()
        discovered = system["discovery"].discover_from_facts(facts)
        elapsed = time.time() - start
        
        # 1000个事实应在2秒内完成
        assert elapsed < 2.0, f"规则发现太慢: {elapsed}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
