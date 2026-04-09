"""
知识蒸馏器单元测试

验证 KnowledgeDistiller 的核心功能：
1. 正则降级提取（LLM 不可用时）
2. 空输入边界条件
3. Schema 更新建议
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 强制离线模式，测试正则降级路径
os.environ["SKIP_LLM"] = "true"

from src.core.reasoner import Reasoner, Fact
from src.evolution.distillation import KnowledgeDistiller


class TestKnowledgeDistiller:
    """知识蒸馏器测试套件"""

    def setup_method(self):
        """初始化测试环境"""
        from src.utils.config import ConfigManager
        ConfigManager._instance = None
        self.reasoner = Reasoner()
        self.distiller = KnowledgeDistiller(self.reasoner)

    def teardown_method(self):
        """清理"""
        from src.utils.config import ConfigManager
        ConfigManager._instance = None

    def test_empty_text_returns_empty(self):
        """空文本应返回空列表"""
        result = self.distiller.extract_triples("")
        assert result == []

    def test_whitespace_text_returns_empty(self):
        """纯空白文本应返回空列表"""
        result = self.distiller.extract_triples("   \n\t  ")
        assert result == []

    def test_regex_extract_is_relation(self):
        """正则应提取 '是' 关系"""
        text = "燃气调压箱是一种压力调节设备"
        facts = self.distiller.extract_triples(text)
        assert len(facts) >= 1
        # 验证提取的事实包含 "是" 谓词
        is_facts = [f for f in facts if f.predicate == "是"]
        assert len(is_facts) >= 1

    def test_regex_extract_belongs_relation(self):
        """正则应提取 '属于' 关系"""
        text = "调压器属于燃气设备。"
        facts = self.distiller.extract_triples(text)
        belongs_facts = [f for f in facts if f.predicate == "属于"]
        assert len(belongs_facts) >= 1

    def test_regex_extract_contains_relation(self):
        """正则应提取 '包含' 关系"""
        text = "调压箱包含减压阀和安全阀。"
        facts = self.distiller.extract_triples(text)
        contains_facts = [f for f in facts if f.predicate == "包含"]
        assert len(contains_facts) >= 1

    def test_regex_extract_confidence(self):
        """正则提取的置信度应低于 LLM 提取"""
        text = "燃气调压箱是一种压力调节设备"
        facts = self.distiller.extract_triples(text)
        if facts:
            # 正则提取置信度应在 0.4-0.5 范围
            assert all(f.confidence <= 0.6 for f in facts)

    def test_suggest_schema_for_new_predicates(self):
        """新谓词应生成 Schema 更新建议"""
        # 确保 Reasoner 中没有 "new_pred" 谓词的事实
        new_facts = [
            Fact("A", "new_relation", "B", confidence=0.7, source="test"),
        ]
        suggestions = self.distiller.suggest_schema_updates(new_facts)
        # 应有 1 个建议
        assert len(suggestions) >= 1
        assert suggestions[0]["type"] == "new_property"
        assert suggestions[0]["predicate"] == "new_relation"

    def test_no_suggestion_for_existing_predicates(self):
        """已知谓词不应生成 Schema 更新建议"""
        # 先添加事实到 Reasoner
        self.reasoner.add_fact(Fact("X", "known_pred", "Y", confidence=0.9, source="test"))
        # 重新创建 distiller 以刷新已知谓词集合
        distiller = KnowledgeDistiller(self.reasoner)
        
        facts = [
            Fact("A", "known_pred", "B", confidence=0.7, source="test"),
        ]
        suggestions = distiller.suggest_schema_updates(facts)
        assert len(suggestions) == 0

    def test_multiple_sentences_extract(self):
        """多句文本应提取多个三元组"""
        text = "调压器属于燃气设备。减压阀是调压器的核心部件。"
        facts = self.distiller.extract_triples(text)
        # 应提取至少 2 个三元组
        assert len(facts) >= 2
