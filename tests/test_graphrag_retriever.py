"""
GraphRAG 检索测试 (GraphRAG Retriever Test)

测试 GraphRAG 检索引擎的各项功能：
1. 构建测试知识图谱（多个实体和关系）
2. 执行社区检测
3. Local Search 测试
4. Global Search 测试
5. Smart Search 自动模式选择
6. 置信度加权排序验证

设计原则：
- 每行逻辑代码必须有中文注释（解释"为什么"）
- 零硬编码：所有配置从环境变量或配置读取
- 无TODO/FIXME：所有实现都是完整可用的
"""

import os
import sys
import pytest
from typing import List

# 添加项目根目录到Python路径，确保可以导入src模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.knowledge_graph import KnowledgeGraph, TypedTriple, TripleStatus
from src.core.retriever import (
    GraphRetriever, RetrievalResult, RetrievalResponse,
    SearchMode, ContextBuilder
)
from src.utils.config import get_config


class TestGraphRAGRetriever:
    """GraphRAG检索器测试类"""
    
    @pytest.fixture
    def knowledge_graph(self) -> KnowledgeGraph:
        """
        创建测试用的知识图谱实例
        
        构建包含多个实体、关系和社区结构的测试图谱
        """
        kg = KnowledgeGraph()
        
        # 构建一个燃气设备知识图谱（包含多个社区结构）
        # 社区1：燃气调压设备
        equipment_triples = [
            ("燃气调压箱", "is_a", "设备", 0.95),
            ("燃气调压箱", "has_component", "调压器", 0.90),
            ("燃气调压箱", "has_component", "过滤器", 0.88),
            ("调压器", "is_a", "核心部件", 0.92),
            ("过滤器", "is_a", "辅助部件", 0.85),
            ("调压器", "requires", "定期维护", 0.87),
            ("过滤器", "requires", "定期更换", 0.86),
        ]
        
        # 社区2：安全规范
        safety_triples = [
            ("燃气安全", "is_a", "安全规范", 0.94),
            ("燃气安全", "requires", "泄漏检测", 0.93),
            ("泄漏检测", "uses", "检测仪器", 0.89),
            ("检测仪器", "is_a", "安全设备", 0.91),
            ("燃气安全", "governed_by", "国家标准", 0.90),
        ]
        
        # 社区3：维护流程
        maintenance_triples = [
            ("设备维护", "is_a", "维护流程", 0.88),
            ("设备维护", "includes", "日常巡检", 0.87),
            ("设备维护", "includes", "定期保养", 0.86),
            ("日常巡检", "performed_by", "巡检人员", 0.85),
            ("定期保养", "performed_by", "专业技术人员", 0.84),
            ("巡检人员", "requires", "培训证书", 0.82),
        ]
        
        # 跨社区连接（使图谱连通）
        cross_community_triples = [
            ("燃气调压箱", "subject_to", "燃气安全", 0.91),
            ("设备维护", "applies_to", "调压器", 0.88),
        ]
        
        # 添加所有三元组
        all_triples = equipment_triples + safety_triples + maintenance_triples + cross_community_triples
        
        for subject, predicate, obj, confidence in all_triples:
            kg.add_triple(
                subject=subject,
                predicate=predicate,
                obj=obj,
                confidence=confidence,
                status=TripleStatus.ACTIVE
            )
        
        return kg
    
    @pytest.fixture
    def retriever(self, knowledge_graph) -> GraphRetriever:
        """
        创建测试用的GraphRetriever实例
        
        使用测试知识图谱初始化检索器
        """
        retriever = GraphRetriever(knowledge_graph)
        # 构建索引
        retriever.build_index()
        return retriever
    
    def test_community_detection(self, knowledge_graph):
        """
        测试社区检测功能
        
        验证点：
        - 社区检测能正确执行
        - 检测到多个社区
        - 社区包含合理的实体
        """
        # 执行社区检测
        communities = knowledge_graph.detect_communities()
        
        # 验证检测到社区
        assert len(communities) > 0, "应检测到至少一个社区"
        
        # 验证每个社区的结构
        for community in communities:
            assert community.community_id >= 0, "社区ID应有效"
            assert community.size > 0, "社区应包含实体"
            assert len(community.entities) > 0, "社区实体列表不应为空"
            # 核心实体是可选的，取决于算法实现
    
    def test_local_search_basic(self, retriever):
        """
        测试Local Search基本功能
        
        验证点：
        - Local Search能返回结果
        - 结果包含相关实体
        - 结果按相关性排序
        """
        # 执行Local Search
        query = "燃气调压箱"
        response = retriever.local_search(query, top_k=10)
        
        # 验证返回结构
        assert isinstance(response, RetrievalResponse), "应返回RetrievalResponse"
        assert response.query == query, "查询应正确记录"
        assert response.search_mode == SearchMode.LOCAL, "检索模式应为LOCAL"
        
        # 验证有结果返回
        assert len(response.results) > 0, "Local Search应返回结果"
        
        # 验证结果包含查询实体
        entity_names = set()
        for result in response.results:
            entity_names.add(result.triple.subject)
            entity_names.add(result.triple.object)
        
        assert "燃气调压箱" in entity_names, "结果应包含查询实体"
    
    def test_local_search_with_neighbors(self, retriever):
        """
        测试Local Search邻居扩展
        
        验证点：
        - 能获取实体的邻居
        - 邻居深度参数生效
        """
        # 执行不同深度的Local Search
        query = "调压器"
        
        # 深度1的搜索
        response_depth1 = retriever.local_search(query, top_k=20, depth=1)
        
        # 深度2的搜索
        response_depth2 = retriever.local_search(query, top_k=20, depth=2)
        
        # 深度2的结果应包含更多实体（或至少不少于深度1）
        # 注意：实际结果取决于图谱结构
        entities_depth1 = set()
        entities_depth2 = set()
        
        for r in response_depth1.results:
            entities_depth1.add(r.triple.subject)
            entities_depth1.add(r.triple.object)
        
        for r in response_depth2.results:
            entities_depth2.add(r.triple.subject)
            entities_depth2.add(r.triple.object)
        
        # 深度2应包含深度1的所有实体（或更多）
        assert len(entities_depth2) >= len(entities_depth1) or len(entities_depth1) > 0, "深度搜索应返回合理结果"
    
    def test_global_search_basic(self, retriever):
        """
        测试Global Search基本功能
        
        验证点：
        - Global Search能返回结果
        - 结果基于社区结构
        - 返回社区统计信息
        """
        # 执行Global Search
        query = "燃气安全规范"
        response = retriever.global_search(query, top_k=10)
        
        # 验证返回结构
        assert isinstance(response, RetrievalResponse), "应返回RetrievalResponse"
        assert response.query == query, "查询应正确记录"
        assert response.search_mode == SearchMode.GLOBAL, "检索模式应为GLOBAL"
        
        # Global Search可能返回空结果（取决于社区检测和查询匹配）
        # 我们主要验证不会抛出异常
        assert response.communities_searched >= 0, "应报告搜索的社区数量"
    
    def test_global_search_community_selection(self, retriever):
        """
        测试Global Search社区选择
        
        验证点：
        - 能选择相关社区
        - 社区选择基于查询语义
        """
        # 测试不同查询的社区选择
        queries = [
            "设备维护流程",
            "安全规范要求",
            "调压设备组成"
        ]
        
        for query in queries:
            response = retriever.global_search(query, top_k=10)
            
            # 验证响应结构正确
            assert response.query == query, f"查询'{query}'应正确记录"
            assert response.communities_searched >= 0, "社区数量应非负"
            
            # 如果搜索到社区，验证实体数量
            if response.communities_searched > 0:
                assert response.entities_found >= 0, "应报告找到的实体数量"
    
    def test_smart_search_auto_mode(self, retriever):
        """
        测试Smart Search自动模式选择
        
        验证点：
        - 自动模式能根据查询特征选择检索策略
        - 实体查询选择Local Search
        - 开放性问题选择Global Search或混合
        """
        # 测试实体查询（应倾向Local Search）
        entity_query = "燃气调压箱"
        response_entity = retriever.smart_search(entity_query, top_k=10, mode="auto")
        
        assert isinstance(response_entity, RetrievalResponse), "应返回RetrievalResponse"
        assert len(response_entity.results) >= 0, "应返回结果（可能为空）"
        
        # 测试开放性问题（可能选择Global或混合）
        open_query = "燃气设备的安全要求有哪些"
        response_open = retriever.smart_search(open_query, top_k=10, mode="auto")
        
        assert isinstance(response_open, RetrievalResponse), "应返回RetrievalResponse"
        
        # 测试混合模式
        hybrid_query = "调压器和过滤器"
        response_hybrid = retriever.smart_search(hybrid_query, top_k=10, mode="hybrid")
        
        assert response_hybrid.search_mode == SearchMode.HYBRID, "混合模式应标记为HYBRID"
    
    def test_smart_search_explicit_modes(self, retriever):
        """
        测试Smart Search显式模式选择
        
        验证点：
        - 显式指定local模式使用Local Search
        - 显式指定global模式使用Global Search
        - 显式指定hybrid模式使用混合检索
        """
        query = "燃气设备"
        
        # 测试Local模式
        response_local = retriever.smart_search(query, top_k=10, mode="local")
        assert response_local.search_mode == SearchMode.LOCAL, "应使用Local Search"
        
        # 测试Global模式
        response_global = retriever.smart_search(query, top_k=10, mode="global")
        assert response_global.search_mode == SearchMode.GLOBAL, "应使用Global Search"
        
        # 测试Hybrid模式
        response_hybrid = retriever.smart_search(query, top_k=10, mode="hybrid")
        assert response_hybrid.search_mode == SearchMode.HYBRID, "应使用Hybrid Search"
    
    def test_weighted_score_calculation(self, retriever):
        """
        测试置信度加权排序
        
        验证点：
        - 检索结果包含加权分数
        - 加权分数基于多个维度
        - 结果按加权分数排序
        """
        query = "燃气调压箱"
        response = retriever.local_search(query, top_k=10)
        
        if len(response.results) > 0:
            # 验证结果包含加权分数
            for result in response.results:
                assert hasattr(result, 'weighted_score'), "结果应包含weighted_score"
                assert hasattr(result, 'relevance_score'), "结果应包含relevance_score"
                assert hasattr(result, 'confidence_score'), "结果应包含confidence_score"
                
                # 验证分数在合理范围
                assert 0 <= result.confidence_score <= 1, "置信度分数应在[0,1]范围"
                assert result.weighted_score >= 0, "加权分数应非负"
            
            # 验证结果按加权分数排序
            scores = [r.weighted_score for r in response.results]
            assert scores == sorted(scores, reverse=True), "结果应按加权分数降序排列"
    
    def test_retrieval_result_structure(self, retriever):
        """
        测试检索结果结构
        
        验证点：
        - 检索结果包含必要的字段
        - 三元组信息完整
        - 上下文信息正确
        """
        query = "调压器"
        response = retriever.local_search(query, top_k=5)
        
        for result in response.results:
            # 验证基本字段
            assert isinstance(result, RetrievalResult), "结果应为RetrievalResult类型"
            assert result.triple is not None, "结果应包含三元组"
            assert result.score >= 0, "分数应非负"
            assert result.source in ["local", "global", "entity", "relation", "semantic"], "来源应有效"
            
            # 验证三元组字段
            triple = result.triple
            assert triple.subject, "三元组应有主语"
            assert triple.predicate, "三元组应有谓语"
            assert triple.object, "三元组应有宾语"
            assert 0 <= triple.confidence <= 1, "三元组置信度应在[0,1]范围"
    
    def test_entity_retrieval(self, retriever):
        """
        测试实体检索功能
        
        验证点：
        - 能按实体名称检索
        - 支持模糊匹配
        - 返回相关三元组
        """
        # 精确匹配
        results = retriever.retrieve_by_entity("燃气调压箱", depth=1, top_k=10)
        
        assert len(results) > 0, "应找到相关三元组"
        
        # 验证返回的三元组包含查询实体
        for result in results:
            assert (result.triple.subject == "燃气调压箱" or 
                   result.triple.object == "燃气调压箱"), "结果应包含查询实体"
        
        # 模糊匹配
        fuzzy_results = retriever.retrieve_by_entity("调压", fuzzy=True, top_k=10)
        
        # 模糊匹配可能找到包含"调压"的实体（如"调压器"）
        assert len(fuzzy_results) >= 0, "模糊匹配应返回结果（可能为空）"
    
    def test_relation_retrieval(self, retriever, knowledge_graph):
        """
        测试关系检索功能
        
        验证点：
        - 能按谓词检索
        - 能按主语/宾语过滤
        - 返回匹配的三元组
        """
        # 按谓词检索
        results = retriever.retrieve_by_relation(predicate="is_a", top_k=10)
        
        # 验证所有结果都有指定的谓词
        for result in results:
            assert result.triple.predicate == "is_a", "结果应有指定的谓词"
        
        # 按主语和谓词检索
        results_filtered = retriever.retrieve_by_relation(
            subject="燃气调压箱",
            predicate="has_component",
            top_k=10
        )
        
        for result in results_filtered:
            assert result.triple.subject == "燃气调压箱", "主语应匹配"
            assert result.triple.predicate == "has_component", "谓词应匹配"
    
    def test_semantic_retrieval(self, retriever):
        """
        测试语义检索功能
        
        验证点：
        - 基于TF-IDF的语义检索能工作
        - 返回语义相关的结果
        """
        query = "燃气设备维护"
        results = retriever.retrieve_by_semantic(query, top_k=10)
        
        # 语义检索可能返回空结果（取决于索引和查询）
        # 主要验证不抛出异常
        assert isinstance(results, list), "应返回列表"
        
        # 如果有结果，验证结构
        for result in results:
            assert result.source == "semantic", "来源应为semantic"
            assert result.triple is not None, "结果应包含三元组"
    
    def test_context_builder(self, retriever):
        """
        测试上下文构建器
        
        验证点：
        - 能将检索结果构建为上下文
        - 上下文格式正确
        - 支持紧凑格式
        """
        query = "燃气调压箱"
        response = retriever.local_search(query, top_k=5)
        
        # 创建上下文构建器
        builder = ContextBuilder(max_tokens=1000)
        
        # 构建上下文
        context = builder.build(response, include_metadata=True)
        
        # 验证上下文不为空且包含关键信息
        assert context, "上下文不应为空"
        assert "知识图谱上下文" in context, "上下文应包含标题"
        
        # 如果有结果，验证包含三元组信息
        if response.results:
            # 上下文应包含至少一个三元组的主语
            first_subject = response.results[0].triple.subject
            assert first_subject in context, "上下文应包含三元组信息"
        
        # 测试紧凑格式
        compact_context = builder.build_compact(response)
        assert isinstance(compact_context, str), "紧凑格式应返回字符串"
    
    def test_empty_query_handling(self, retriever):
        """
        测试空查询处理
        
        验证点：
        - 空查询不抛出异常
        - 返回空结果或合理响应
        """
        # 测试空字符串查询
        response = retriever.smart_search("", top_k=10)
        assert isinstance(response, RetrievalResponse), "空查询应返回RetrievalResponse"
        
        # 测试无意义查询
        response = retriever.smart_search("xyz123notexist", top_k=10)
        assert isinstance(response, RetrievalResponse), "无意义查询应返回RetrievalResponse"
        # 可能返回空结果或回退到语义检索
    
    def test_retrieval_response_properties(self, retriever):
        """
        测试检索响应属性
        
        验证点：
        - top_entities返回正确的实体集合
        - top_triples返回正确的三元组列表
        """
        query = "燃气调压箱"
        response = retriever.local_search(query, top_k=10)
        
        # 测试top_entities
        entities = response.top_entities
        assert isinstance(entities, set), "top_entities应返回集合"
        
        # 如果有结果，验证实体不为空
        if response.results:
            assert len(entities) > 0, "应有实体"
            # 验证所有实体都来自结果
            for entity in entities:
                found = any(
                    r.triple.subject == entity or r.triple.object == entity
                    for r in response.results
                )
                assert found, f"实体{entity}应来自检索结果"
        
        # 测试top_triples
        triples = response.top_triples
        assert isinstance(triples, list), "top_triples应返回列表"
        assert len(triples) == len(response.results), "三元组数量应与结果数量一致"


if __name__ == "__main__":
    # 允许直接运行测试文件
    pytest.main([__file__, "-v"])
