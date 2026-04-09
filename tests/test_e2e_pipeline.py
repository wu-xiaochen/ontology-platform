"""
端到端流水线测试 (End-to-End Pipeline Test)

测试完整的知识注入→推理→查询流水线
"""

import os
import sys
import pytest

# 添加项目根目录到Python路径，确保可以导入src模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.knowledge_graph import KnowledgeGraph, TypedTriple, TripleStatus
from src.core.reasoner import Reasoner, Fact, Rule, RuleType, InferenceDirection


class TestE2EPipeline:
    """端到端流水线测试类"""

    def test_complete_pipeline(self):
        """测试完整的知识处理流水线"""
        # 步骤1: 创建 KnowledgeGraph 并注入知识
        knowledge_graph = KnowledgeGraph()
        
        # 注入三元组数据
        triples_data = [
            {"subject": "燃气公司", "predicate": "operates", "object": "调压柜A", "confidence": 0.95},
            {"subject": "调压柜A", "predicate": "is_a", "object": "设备", "confidence": 1.0},
            {"subject": "调压柜A", "predicate": "has_pressure", "object": "0.5MPa", "confidence": 0.9},
        ]
        
        for triple in triples_data:
            knowledge_graph.add_triple(
                subject=triple["subject"],
                predicate=triple["predicate"],
                obj=triple["object"],
                confidence=triple["confidence"]
            )
        
        # 步骤2: 创建 Reasoner 并添加规则
        reasoner = Reasoner()
        reasoner._graph = knowledge_graph
        
        # 添加推理规则（使用简单格式）
        rule = Rule(
            id="pipeline:test",
            name="管道测试规则",
            rule_type=RuleType.IF_THEN,
            condition="?x operates ?y",
            conclusion="?x manages 业务",
            confidence=0.85
        )
        reasoner.add_rule(rule)
        
        # 步骤3: 执行推理
        inference_result = reasoner.forward_chain(max_depth=3)
        
        # 验证推理执行成功
        assert inference_result is not None, "推理应返回结果"
        
        # 步骤4: 查询验证
        query_results = knowledge_graph.query(subject="燃气公司")
        
        # 验证查询到注入的事实
        assert len(query_results) > 0, "应查询到与燃气公司相关的事实"
        
        # 验证统计信息正确
        stats = knowledge_graph.statistics()
        assert stats["total_triples"] >= len(triples_data), "总三元组数应不少于注入的数量"
        
        # 验证平均置信度在合理范围
        assert 0.0 <= stats["avg_confidence"] <= 1.0, "平均置信度应在[0,1]范围内"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
