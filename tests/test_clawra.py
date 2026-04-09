"""
test_clawra.py - Clawra 主入口类测试

覆盖 src/clawra.py 的核心功能：
- 初始化
- 文本学习
- 事实管理
- 推理执行
- 模式查询
- 统计信息
- 知识导入/导出
- 系统重置
"""
import pytest
import json
import sys
from pathlib import Path

# 确保 src 在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.clawra import Clawra, create_clawra


class TestClawraInitialization:
    """测试 Clawra 初始化"""

    def test_basic_initialization(self):
        """测试基本初始化，不启用记忆系统"""
        clawra = Clawra()
        # 验证核心组件已初始化
        assert clawra.logic_layer is not None
        assert clawra.rule_discovery is not None
        assert clawra.meta_learner is not None
        assert clawra.reasoner is not None
        # 未启用记忆时 memory 应为 None
        assert clawra.memory is None
        # 配置应从 ConfigManager 获取
        assert clawra.config is not None

    def test_create_clawra_convenience(self):
        """测试便捷创建函数"""
        clawra = create_clawra()
        assert isinstance(clawra, Clawra)


class TestClawraLearning:
    """测试 Clawra 学习功能"""

    def setup_method(self):
        """每个测试方法前创建新实例"""
        self.clawra = Clawra()

    def test_learn_from_text(self):
        """测试从文本学习知识"""
        result = self.clawra.learn("燃气调压箱：是一种用于调节燃气压力的设备")
        # 学习结果应包含基本字段
        assert "episode_id" in result
        assert "domain" in result
        assert "strategy" in result
        assert "learned_patterns" in result
        assert "success" in result

    def test_learn_with_domain_hint(self):
        """测试带领域提示的学习"""
        result = self.clawra.learn(
            "进口压力范围: 0.1-0.4 MPa",
            domain_hint="gas_equipment"
        )
        assert result["domain"] == "gas_equipment"

    def test_learn_empty_text(self):
        """测试空文本学习应返回失败"""
        result = self.clawra.learn("")
        assert result["success"] is False

    def test_learn_batch(self):
        """测试批量学习"""
        texts = [
            "设备A：是一种燃气调压设备",
            "设备B：用于压力调节"
        ]
        results = self.clawra.learn_batch(texts)
        assert len(results) == 2
        for r in results:
            assert "episode_id" in r


class TestClawraFacts:
    """测试 Clawra 事实管理"""

    def setup_method(self):
        self.clawra = Clawra()

    def test_add_fact(self):
        """测试添加事实"""
        self.clawra.add_fact("设备A", "is_a", "燃气调压箱")
        # 验证事实已添加到推理引擎
        facts = self.clawra.reasoner.facts
        added = any(
            f.subject == "设备A" and f.predicate == "is_a" and f.object == "燃气调压箱"
            for f in facts
        )
        assert added

    def test_add_fact_with_confidence(self):
        """测试带置信度的事实添加"""
        self.clawra.add_fact("设备B", "requires", "维护", confidence=0.85)
        facts = self.clawra.reasoner.query(subject="设备B")
        assert len(facts) > 0
        assert facts[0].confidence == 0.85


class TestClawraReasoning:
    """测试 Clawra 推理功能"""

    def setup_method(self):
        self.clawra = Clawra()

    def test_reason_empty(self):
        """测试无事实时的推理"""
        conclusions = self.clawra.reason()
        # 仅有内置规则，无匹配事实时应无结论
        assert isinstance(conclusions, list)

    def test_reason_with_facts(self):
        """测试有事实时的推理"""
        # 添加传递链事实
        self.clawra.add_fact("A", "is_a", "B")
        self.clawra.add_fact("B", "is_a", "C")
        conclusions = self.clawra.reason(max_depth=5)
        assert isinstance(conclusions, list)


class TestClawraQueryPatterns:
    """测试 Clawra 模式查询"""

    def setup_method(self):
        self.clawra = Clawra()
        # 先学习一些知识
        self.clawra.learn("燃气调压箱：是一种用于调节压力的设备", domain_hint="gas_equipment")

    def test_query_all_patterns(self):
        """测试查询所有模式"""
        patterns = self.clawra.query_patterns()
        assert isinstance(patterns, list)
        # 至少应有引导逻辑 + 学习到的模式
        assert len(patterns) >= 2

    def test_query_by_domain(self):
        """测试按领域查询"""
        patterns = self.clawra.query_patterns(domain="gas_equipment")
        for p in patterns:
            assert p["domain"] == "gas_equipment"

    def test_query_by_keyword(self):
        """测试按关键词查询"""
        patterns = self.clawra.query_patterns(keyword="传递")
        for p in patterns:
            assert "传递" in p["description"].lower() or "传递" in p["name"]


class TestClawraStatistics:
    """测试 Clawra 统计信息"""

    def test_get_statistics(self):
        """测试获取统计信息"""
        clawra = Clawra()
        stats = clawra.get_statistics()
        assert "learning" in stats
        assert "patterns" in stats
        assert "memory" in stats
        assert "facts" in stats


class TestClawraKnowledgeExportImport:
    """测试知识导入导出"""

    def test_export_knowledge(self):
        """测试知识导出"""
        clawra = Clawra()
        clawra.learn("测试实体：是一种测试对象")
        exported = clawra.export_knowledge()
        # 导出结果应为有效 JSON
        data = json.loads(exported)
        assert "patterns" in data
        assert "statistics" in data

    def test_import_knowledge(self):
        """测试知识导入"""
        clawra = Clawra()
        knowledge = json.dumps({
            "patterns": [],
            "statistics": {}
        })
        result = clawra.import_knowledge(knowledge)
        assert result["success"] is True


class TestClawraReset:
    """测试系统重置"""

    def test_reset(self):
        """测试重置后组件被重建"""
        clawra = Clawra()
        clawra.add_fact("X", "is_a", "Y")
        # 重置前有事实
        assert len(clawra.reasoner.facts) > 0
        clawra.reset()
        # 重置后事实被清空（仅剩内置规则相关的空事实库）
        old_facts_exist = any(
            f.subject == "X" for f in clawra.reasoner.facts
        )
        assert not old_facts_exist

    def test_close(self):
        """测试关闭系统"""
        clawra = Clawra()
        # close 不应抛出异常
        clawra.close()
