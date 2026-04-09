"""
MetaLearner 单元测试

测试元学习器的所有功能
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.evolution.meta_learner import MetaLearner, LearningEpisode
from src.evolution.unified_logic import UnifiedLogicLayer, LogicType
from src.evolution.rule_discovery import RuleDiscoveryEngine


class TestMetaLearner:
    """MetaLearner 测试类。"""
    
    @pytest.fixture
    def meta_learner(self):
        """创建测试实例。"""
        logic_layer = UnifiedLogicLayer()
        discovery_engine = RuleDiscoveryEngine(logic_layer)
        return MetaLearner(logic_layer, discovery_engine)
    
    def test_initialization(self, meta_learner):
        """测试初始化状态。"""
        assert len(meta_learner.episodes) == 0
        assert len(meta_learner.domain_models) == 0
        assert len(meta_learner.domain_keywords) > 0
    
    def test_detect_domain_medical(self, meta_learner):
        """测试医疗领域识别。"""
        text = "患者需要定期服用胰岛素控制血糖，这是医疗诊断治疗方案。"
        scores = meta_learner.detect_domain(text)
        
        assert "medical" in scores
        assert scores["medical"] > 0.3  # 应该识别为医疗领域
    
    def test_detect_domain_legal(self, meta_learner):
        """测试法律领域识别。"""
        text = "合同违约需要支付赔偿金。"
        scores = meta_learner.detect_domain(text)
        
        assert "legal" in scores
        assert scores["legal"] > 0.5
    
    def test_detect_domain_gas(self, meta_learner):
        """测试燃气领域识别。"""
        text = "燃气调压箱进口压力范围0.02-0.4MPa。"
        scores = meta_learner.detect_domain(text)
        
        assert "gas_equipment" in scores
        assert scores["gas_equipment"] > 0.5
    
    def test_detect_domain_generic(self, meta_learner):
        """测试通用领域识别。"""
        text = "这是一段普通文本，没有特定领域关键词。"
        scores = meta_learner.detect_domain(text)
        
        # 没有明显匹配时应该有 generic
        assert "generic" in scores
    
    def test_learn_from_text(self, meta_learner):
        """测试从文本学习。"""
        text = "如果设备是燃气调压箱，那么需要定期维护。"
        
        result = meta_learner.learn(text, input_type="text")
        
        assert result["success"] is True
        assert "episode_id" in result
        assert "domain" in result
        assert "strategy" in result
        assert len(result["learned_patterns"]) > 0
        assert result["learning_time"] >= 0
    
    def test_learn_from_text_with_domain_hint(self, meta_learner):
        """测试带领域提示的学习。"""
        text = "设备需要维护。"
        
        result = meta_learner.learn(text, input_type="text", domain_hint="gas_equipment")
        
        assert result["domain"] == "gas_equipment"
    
    def test_learn_from_structured(self, meta_learner):
        """测试从结构化数据学习。"""
        facts = [
            {"subject": "设备A", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "设备B", "predicate": "is_a", "object": "燃气设备"},
            {"subject": "燃气设备", "predicate": "requires", "object": "维护"}
        ]
        
        result = meta_learner.learn(facts, input_type="structured")
        
        assert result["success"] is True
    
    def test_learn_empty_text(self, meta_learner):
        """测试空文本学习。"""
        result = meta_learner.learn("", input_type="text")
        
        assert result["success"] is False
    
    def test_provide_feedback(self, meta_learner):
        """测试提供反馈。"""
        # 先执行一次学习
        result = meta_learner.learn("测试文本", input_type="text")
        episode_id = result["episode_id"]
        
        # 提供正面反馈
        meta_learner.provide_feedback(episode_id, 0.9, "学习效果很好")
        
        # 验证反馈已记录
        episode = next(e for e in meta_learner.episodes if e.episode_id == episode_id)
        assert episode.feedback_score == 0.9
    
    def test_get_learning_statistics(self, meta_learner):
        """测试获取学习统计。"""
        # 执行几次学习
        meta_learner.learn("文本1", input_type="text")
        meta_learner.learn("文本2", input_type="text")
        
        stats = meta_learner.get_learning_statistics()
        
        assert stats["total_episodes"] == 2
        assert "success_rate" in stats
        assert "avg_learning_time" in stats
        assert "domain_distribution" in stats
    
    def test_export_knowledge(self, meta_learner):
        """测试导出知识。"""
        # 先学习一些知识
        meta_learner.learn("燃气设备需要维护。", input_type="text")
        
        export = meta_learner.export_knowledge()
        
        assert "patterns" in export
        assert "statistics" in export
        assert "export_time" in export
    
    def test_export_knowledge_by_domain(self, meta_learner):
        """测试按领域导出知识。"""
        meta_learner.learn("燃气设备需要维护。", input_type="text", domain_hint="gas_equipment")
        
        export = meta_learner.export_knowledge(domain="gas_equipment")
        
        assert "patterns" in export
    
    def test_import_knowledge(self, meta_learner):
        """测试导入知识。"""
        knowledge_json = '''
        {
            "patterns": [
                {
                    "id": "imported:1",
                    "logic_type": "rule",
                    "name": "导入规则",
                    "description": "测试导入",
                    "conditions": [],
                    "actions": [],
                    "confidence": 0.8,
                    "source": "imported",
                    "domain": "test"
                }
            ],
            "statistics": {},
            "export_time": 1234567890
        }
        '''
        
        result = meta_learner.import_knowledge(knowledge_json)
        
        assert result["success"] is True
        assert result["imported"] == 1
    
    def test_import_knowledge_invalid_json(self, meta_learner):
        """测试导入无效 JSON。"""
        result = meta_learner.import_knowledge("invalid json")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_strategy_effectiveness_tracking(self, meta_learner):
        """测试策略效果追踪。"""
        # 执行多次学习
        for i in range(5):
            meta_learner.learn(f"文本{i}", input_type="text")
        
        stats = meta_learner.get_learning_statistics()
        
        # 验证策略统计已更新
        assert "strategy_effectiveness" in stats
        for strategy, effectiveness in stats["strategy_effectiveness"].items():
            assert "attempts" in effectiveness
            assert "successes" in effectiveness
            assert "avg_learning_time" in effectiveness


class TestLearningEpisode:
    """LearningEpisode 测试类。"""
    
    def test_episode_creation(self):
        """测试学习过程记录创建。"""
        episode = LearningEpisode(
            episode_id="ep_123",
            timestamp=1234567890.0,
            domain="gas_equipment",
            input_type="text",
            input_data="测试文本",
            learned_patterns=["pattern:1", "pattern:2"],
            learning_time=0.5,
            success=True
        )
        
        assert episode.episode_id == "ep_123"
        assert episode.domain == "gas_equipment"
        assert len(episode.learned_patterns) == 2
        assert episode.success is True


class TestDomainAdaptation:
    """领域自适应测试类。"""
    
    @pytest.fixture
    def meta_learner(self):
        logic_layer = UnifiedLogicLayer()
        discovery_engine = RuleDiscoveryEngine(logic_layer)
        return MetaLearner(logic_layer, discovery_engine)
    
    def test_adapt_to_new_domain(self, meta_learner):
        """测试适应新领域。"""
        # 学习新领域知识
        meta_learner.learn(
            "新能源电池需要定期检测电压。",
            input_type="text",
            domain_hint="new_energy"
        )
        
        # 验证领域模型已创建
        assert "new_energy" in meta_learner.domain_models
    
    def test_domain_isolation(self, meta_learner):
        """测试领域隔离。"""
        # 学习不同领域的知识
        meta_learner.learn("燃气设备需要维护。", input_type="text", domain_hint="gas")
        meta_learner.learn("医疗设备需要消毒。", input_type="text", domain_hint="medical")
        
        # 验证领域隔离
        gas_patterns = meta_learner.logic_layer.get_patterns_by_domain("gas")
        medical_patterns = meta_learner.logic_layer.get_patterns_by_domain("medical")
        
        # 确保模式不混淆
        for p in gas_patterns:
            assert p.domain == "gas"
        for p in medical_patterns:
            assert p.domain == "medical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
