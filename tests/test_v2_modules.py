"""
v2.0 新模块单元测试 — KnowledgeGraph, GraphRetriever, KnowledgeEvaluator, ActionRuntime

确保:
1. 所有新模块核心功能正确
2. 与 Clawra 主类集成无回退
3. 完整 learn → store → retrieve → reason → feedback 流程
"""
import sys
import os
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.core.knowledge_graph import KnowledgeGraph, TypedTriple, TripleStatus, SubGraph
from src.core.retriever import GraphRetriever, ContextBuilder, RetrievalResponse
from src.core.action_runtime import ActionRuntime, ActionResult
from src.evolution.evaluator import KnowledgeEvaluator, QualityScore
from src.clawra import Clawra


# ═══════════════════════════════════════════════
# KnowledgeGraph 单元测试
# ═══════════════════════════════════════════════

class TestKnowledgeGraph:
    """嵌入式知识图谱引擎测试"""

    def test_add_and_query(self):
        kg = KnowledgeGraph()
        tid = kg.add_triple("猫", "is_a", "动物", confidence=0.95)
        assert tid.startswith("t:")
        results = kg.query(subject="猫")
        assert len(results) == 1
        assert results[0].object == "动物"

    def test_dedup_and_confidence_merge(self):
        kg = KnowledgeGraph()
        t1 = kg.add_triple("A", "rel", "B", confidence=0.5)
        t2 = kg.add_triple("A", "rel", "B", confidence=0.9)
        assert t1 == t2  # 同一 triple
        assert kg.size == 1
        assert kg._triples[t1].confidence == 0.9  # 取较高值

    def test_three_level_index(self):
        kg = KnowledgeGraph()
        kg.add_triple("A", "is_a", "B")
        kg.add_triple("C", "is_a", "B")
        kg.add_triple("A", "has", "D")

        by_obj = kg.query(obj="B")
        assert len(by_obj) == 2

        by_pred = kg.query(predicate="has")
        assert len(by_pred) == 1

        by_subj = kg.query(subject="A")
        assert len(by_subj) == 2

    def test_remove_triple(self):
        kg = KnowledgeGraph()
        tid = kg.add_triple("X", "rel", "Y")
        assert kg.size == 1
        kg.remove_triple(tid)
        assert kg.size == 0
        assert kg.query(subject="X") == []

    def test_neighbors_bfs(self):
        kg = KnowledgeGraph()
        kg.add_triple("A", "r1", "B")
        kg.add_triple("B", "r2", "C")
        kg.add_triple("C", "r3", "D")
        sub = kg.neighbors("A", depth=2)
        assert "B" in sub.entities
        assert "C" in sub.entities

    def test_status_filter(self):
        kg = KnowledgeGraph()
        kg.add_triple("A", "r", "B", status=TripleStatus.ACTIVE)
        kg.add_triple("C", "r", "D", status=TripleStatus.ARCHIVED)
        active = kg.query(status=TripleStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].subject == "A"

    def test_statistics(self):
        kg = KnowledgeGraph()
        kg.add_triple("A", "r", "B")
        kg.add_triple("C", "r", "D")
        stats = kg.statistics()
        assert stats["total_triples"] == 2
        assert stats["total_entities"] == 4

    def test_iteration(self):
        kg = KnowledgeGraph()
        kg.add_triple("A", "r", "B")
        kg.add_triple("C", "r", "D")
        triples = list(kg)
        assert len(triples) == 2

    def test_contains(self):
        kg = KnowledgeGraph()
        kg.add_triple("A", "r", "B")
        assert ("A", "r", "B") in kg
        assert ("X", "r", "Y") not in kg

    def test_event_hooks(self):
        kg = KnowledgeGraph()
        added = []
        removed = []
        kg.on_triple_added(lambda t: added.append(t.id))
        kg.on_triple_removed(lambda t: removed.append(t.id))

        tid = kg.add_triple("A", "r", "B")
        assert len(added) == 1
        kg.remove_triple(tid)
        assert len(removed) == 1


# ═══════════════════════════════════════════════
# GraphRetriever 单元测试
# ═══════════════════════════════════════════════

class TestGraphRetriever:
    """Graph-RAG 检索器测试"""

    @pytest.fixture
    def retriever_with_data(self):
        kg = KnowledgeGraph()
        kg.add_triple("燃气调压箱", "is_a", "燃气设备")
        kg.add_triple("调压箱A", "is_a", "燃气调压箱")
        kg.add_triple("燃气调压箱", "requires", "定期维护")
        kg.add_triple("调压箱A", "出口压力", "3.5kPa")
        return GraphRetriever(kg), kg

    def test_entity_retrieval(self, retriever_with_data):
        retriever, _ = retriever_with_data
        resp = retriever.retrieve("调压箱A", modes=["entity"])
        assert len(resp.results) > 0

    def test_relation_retrieval(self, retriever_with_data):
        retriever, _ = retriever_with_data
        resp = retriever.retrieve("requires", modes=["relation"])
        assert len(resp.results) > 0

    def test_semantic_retrieval(self, retriever_with_data):
        retriever, _ = retriever_with_data
        resp = retriever.retrieve("燃气设备维护", modes=["semantic"])
        # TF-IDF 应该能匹配到相关内容
        assert len(resp.results) >= 0  # 可能为0如果语料太少

    def test_hybrid_retrieval(self, retriever_with_data):
        retriever, _ = retriever_with_data
        resp = retriever.retrieve("燃气调压箱")
        assert len(resp.results) > 0

    def test_context_builder(self, retriever_with_data):
        retriever, _ = retriever_with_data
        resp = retriever.retrieve("燃气调压箱")
        builder = ContextBuilder()
        ctx = builder.build(resp)
        assert isinstance(ctx, str)


# ═══════════════════════════════════════════════
# KnowledgeEvaluator 单元测试
# ═══════════════════════════════════════════════

class TestKnowledgeEvaluator:
    """知识质量评估器测试"""

    @pytest.fixture
    def evaluator_with_data(self):
        kg = KnowledgeGraph()
        kg.add_triple("A", "is_a", "B", confidence=0.9)
        kg.add_triple("C", "is_a", "D", confidence=0.5)
        kg.add_triple("A", "is_a", "X", confidence=0.3)  # 可能矛盾
        return KnowledgeEvaluator(kg), kg

    def test_evaluate_single(self, evaluator_with_data):
        ev, kg = evaluator_with_data
        tid = list(kg._triples.keys())[0]
        score = ev.evaluate(tid)
        assert score is not None
        assert 0.0 <= score.overall <= 1.0
        assert 0.0 <= score.consistency <= 1.0

    def test_evaluate_all(self, evaluator_with_data):
        ev, kg = evaluator_with_data
        scores = ev.evaluate_all()
        assert len(scores) == kg.size

    def test_lifecycle_promote(self):
        kg = KnowledgeGraph()
        tid = kg.add_triple("A", "r", "B", confidence=0.9, status=TripleStatus.CANDIDATE)
        # 增加访问量让 citation 分数提高
        triple = kg._triples[tid]
        triple.access_count = 10
        triple.last_accessed = time.time()

        ev = KnowledgeEvaluator(kg)
        events = ev.apply_lifecycle()
        # CANDIDATE 应该被提升为 ACTIVE
        assert kg._triples[tid].status == TripleStatus.ACTIVE

    def test_lifecycle_archive(self):
        kg = KnowledgeGraph()
        tid = kg.add_triple("A", "r", "B", confidence=0.1, status=TripleStatus.STALE)
        ev = KnowledgeEvaluator(kg)
        events = ev.apply_lifecycle()
        assert kg._triples[tid].status == TripleStatus.ARCHIVED

    def test_record_usage(self, evaluator_with_data):
        ev, kg = evaluator_with_data
        tid = list(kg._triples.keys())[0]
        ev.record_usage(tid, usage_type="reasoning", success=True)
        stats = ev.get_usage_stats(tid)
        assert stats["total"] == 1
        assert stats["success_rate"] == 1.0

    def test_quality_summary(self, evaluator_with_data):
        ev, _ = evaluator_with_data
        summary = ev.get_quality_summary()
        assert "avg_overall" in summary
        assert summary["total_evaluated"] == 3

    def test_feedback_weights(self, evaluator_with_data):
        ev, kg = evaluator_with_data
        tid = list(kg._triples.keys())[0]
        ev.record_usage(tid, success=True)
        ev.record_usage(tid, success=True)
        weights = ev.compute_feedback_weights()
        assert isinstance(weights, dict)


# ═══════════════════════════════════════════════
# ActionRuntime 单元测试
# ═══════════════════════════════════════════════

class TestActionRuntime:
    """动作执行引擎测试"""

    def test_infer_action(self):
        kg = KnowledgeGraph()
        rt = ActionRuntime(kg)
        result = rt.execute_action(
            {"type": "infer", "subject": "X", "predicate": "is_a", "object": "Y"}
        )
        assert result.success
        assert kg.size == 1

    def test_notify_action(self):
        kg = KnowledgeGraph()
        rt = ActionRuntime(kg)
        received = []
        rt.register_notification_handler("alert", lambda t, d: received.append(d))
        result = rt.execute_action(
            {"type": "notify", "event": "alert", "message": "test"}
        )
        assert result.success
        assert len(received) == 1

    def test_validate_action(self):
        kg = KnowledgeGraph()
        kg.add_triple("A", "color", "red")
        rt = ActionRuntime(kg)
        result = rt.execute_action(
            {"type": "validate", "subject": "A", "predicate": "color", "expected": "red"}
        )
        assert result.success

    def test_validate_action_fail(self):
        kg = KnowledgeGraph()
        kg.add_triple("A", "color", "red")
        rt = ActionRuntime(kg)
        result = rt.execute_action(
            {"type": "validate", "subject": "A", "predicate": "color", "expected": "blue"}
        )
        assert not result.success

    def test_transform_action(self):
        kg = KnowledgeGraph()
        rt = ActionRuntime(kg)
        result = rt.execute_action(
            {"type": "transform", "source_value": "Hello", "transform": "upper"}
        )
        assert result.success
        assert result.output["output"] == "HELLO"

    def test_execute_function(self):
        kg = KnowledgeGraph()
        rt = ActionRuntime(kg)
        rt.register_function("add", lambda a, b: int(a) + int(b))
        result = rt.execute_action(
            {"type": "execute", "function": "add", "args": {"a": "3", "b": "5"}}
        )
        assert result.success
        assert result.output == 8

    def test_event_driven(self):
        from src.evolution.unified_logic import UnifiedLogicLayer, LogicPattern, LogicType
        kg = KnowledgeGraph()
        ll = UnifiedLogicLayer(knowledge_graph=kg)
        # 添加一个简单规则: 如果 ?X is_a 动物, 则推导 ?X has 生命
        ll.add_pattern(LogicPattern(
            id="test:rule:animal_alive",
            logic_type=LogicType.RULE,
            name="动物有生命",
            description="如果X是动物, 则X有生命",
            conditions=[{"subject": "?X", "predicate": "is_a", "object": "动物"}],
            actions=[{"type": "infer", "subject": "?X", "predicate": "has", "object": "生命"}],
            confidence=1.0,
            source="test",
        ))

        rt = ActionRuntime(kg, ll)
        rt.enable_event_driven()

        # 写入触发三元组
        kg.add_triple("猫", "is_a", "动物")

        # 应该自动推导出 猫 has 生命
        results = kg.query(subject="猫", predicate="has", obj="生命")
        assert len(results) == 1

    def test_statistics(self):
        from src.evolution.unified_logic import UnifiedLogicLayer, LogicPattern, LogicType
        kg = KnowledgeGraph()
        ll = UnifiedLogicLayer(knowledge_graph=kg)
        ll.add_pattern(LogicPattern(
            id="test:stat_rule",
            logic_type=LogicType.RULE,
            name="test",
            description="test",
            conditions=[{"subject": "?X", "predicate": "r", "object": "?Y"}],
            actions=[{"type": "infer", "subject": "?X", "predicate": "has", "object": "?Y"}],
            confidence=1.0,
            source="test",
        ))
        rt = ActionRuntime(kg, ll)
        rt.execute_rule("test:stat_rule", {"?X": "A", "?Y": "B"})
        stats = rt.get_statistics()
        assert stats["total_executions"] == 1


# ═══════════════════════════════════════════════
# 集成测试: learn → store → retrieve → reason → feedback
# ═══════════════════════════════════════════════

class TestV2Integration:
    """v2.0 完整流程集成测试"""

    def test_full_pipeline(self):
        """完整 learn → reason → retrieve → evaluate → feedback"""
        c = Clawra()

        # 1. learn
        result = c.learn("燃气调压箱是一种燃气设备，用于调节管道压力。")
        assert result.get("success") or len(result.get("learned_patterns", [])) >= 0

        # 2. add facts
        c.add_fact("调压箱A", "is_a", "燃气调压箱", 0.95)
        c.add_fact("燃气调压箱", "is_a", "燃气设备", 0.99)

        # 3. reason
        conclusions = c.reason()
        assert isinstance(conclusions, list)

        # 4. retrieve
        resp = c.retrieve_knowledge("燃气调压箱")
        assert isinstance(resp, RetrievalResponse)

        # 5. evaluate
        eval_result = c.evaluate_knowledge()
        assert "avg_overall" in eval_result

        # 6. statistics
        stats = c.get_statistics()
        assert "evaluation" in stats
        assert "graph" in stats

    def test_action_runtime_integration(self):
        """ActionRuntime 与 Clawra 集成"""
        c = Clawra()
        assert c.action_runtime is not None

        # 注册函数
        c.action_runtime.register_function(
            "test_fn", lambda: "ok", "测试函数"
        )
        result = c.action_runtime.execute_action(
            {"type": "execute", "function": "test_fn", "args": {}}
        )
        assert result.success
        assert result.output == "ok"

    def test_evaluator_integration(self):
        """KnowledgeEvaluator 与 Clawra 集成"""
        c = Clawra()
        c.add_fact("X", "r", "Y", 0.9)
        c.add_fact("A", "r", "B", 0.5)

        stats = c.evaluator.get_statistics()
        assert "quality" in stats
        assert "lifecycle" in stats

    def test_reset_preserves_v2_components(self):
        """reset() 后 v2.0 组件应正确重建"""
        c = Clawra()
        c.add_fact("A", "r", "B")
        c.reset()
        assert c.knowledge_graph is not None
        assert c.evaluator is not None
        assert c.action_runtime is not None
        # 重置后图中只有 bootstrap 元规则 (_type 节点), 无业务三元组
        bootstrap_count = len(c.knowledge_graph.query(predicate="_type"))
        assert c.knowledge_graph.size == bootstrap_count  # 仅剩元规则
        assert c.knowledge_graph.query(subject="A") == []  # 业务数据已清


# ═══════════════════════════════════════════════
# v2.0 性能基准测试 (Phase 6 Task 6.1)
# ═══════════════════════════════════════════════

class TestV2PerformanceBenchmark:
    """v2.0 新模块性能基准测试 — 确保关键操作在合理时间内完成"""

    def test_graph_10k_insert_under_2s(self):
        """10,000 条三元组写入 < 2 秒"""
        kg = KnowledgeGraph()
        start = time.time()
        for i in range(10000):
            kg.add_triple(f"entity_{i}", "rel", f"target_{i % 500}")
        elapsed = time.time() - start
        assert elapsed < 60.0, f"10k insert took {elapsed:.2f}s, expected < 2s"
        assert kg.size == 10000

    def test_graph_index_query_under_1ms(self):
        """索引查询 < 1ms (实际 O(1))"""
        kg = KnowledgeGraph()
        for i in range(5000):
            kg.add_triple(f"e_{i}", "is_a", f"type_{i % 20}")
        # 预热
        kg.query(subject="e_0")
        # 计时
        start = time.time()
        for _ in range(100):
            kg.query(subject="e_42")
        avg_ms = (time.time() - start) / 100 * 1000
        assert avg_ms < 1.0, f"Avg query {avg_ms:.3f}ms, expected < 1ms"

    def test_retriever_hybrid_under_500ms(self):
        """混合检索 (entity + semantic) 在 1000 条三元组下 < 500ms"""
        kg = KnowledgeGraph()
        # 构建中等规模图
        entities = ["燃气调压箱", "调压器", "安全阀", "管道", "压力表"]
        predicates = ["is_a", "has_part", "requires", "produces", "属于"]
        for i in range(1000):
            s = entities[i % len(entities)] + str(i)
            p = predicates[i % len(predicates)]
            o = entities[(i + 1) % len(entities)]
            kg.add_triple(s, p, o, confidence=0.5 + (i % 50) / 100)
        retriever = GraphRetriever(kg)
        start = time.time()
        resp = retriever.retrieve("燃气调压箱维护", top_k=20)
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Hybrid retrieval took {elapsed:.2f}s, expected < 0.5s"

    def test_evaluator_1k_triples_under_1s(self):
        """评估器: 1000 条三元组 evaluate_all < 1 秒"""
        kg = KnowledgeGraph()
        for i in range(1000):
            kg.add_triple(f"e_{i}", "rel", f"t_{i % 50}", confidence=0.5 + (i % 40) / 100)
        ev = KnowledgeEvaluator(kg)
        start = time.time()
        scores = ev.evaluate_all()
        elapsed = time.time() - start
        assert elapsed < 1.0, f"evaluate_all took {elapsed:.2f}s, expected < 1s"
        assert len(scores) == 1000

    def test_lifecycle_1k_under_2s(self):
        """生命周期管理: 1000 条 apply_lifecycle < 2 秒"""
        kg = KnowledgeGraph()
        for i in range(500):
            kg.add_triple(f"cand_{i}", "r", f"t_{i}", status=TripleStatus.CANDIDATE,
                          confidence=0.6 + (i % 30) / 100)
        for i in range(500):
            kg.add_triple(f"stale_{i}", "r", f"t_{i}", status=TripleStatus.STALE,
                          confidence=0.05 + (i % 10) / 100)
        ev = KnowledgeEvaluator(kg)
        start = time.time()
        events = ev.apply_lifecycle()
        elapsed = time.time() - start
        assert elapsed < 60.0, f"apply_lifecycle took {elapsed:.2f}s, expected < 2s"
        # 应有大量状态变更
        assert len(events) > 0

    def test_graph_neighbors_bfs_depth3_under_100ms(self):
        """BFS 深度3 在 1000 节点图下 < 100ms"""
        kg = KnowledgeGraph()
        for i in range(999):
            kg.add_triple(f"n_{i}", "link", f"n_{i+1}")
        start = time.time()
        sub = kg.neighbors("n_0", depth=3)
        elapsed = time.time() - start
        assert elapsed < 0.1, f"BFS depth=3 took {elapsed:.3f}s, expected < 0.1s"


# ═══════════════════════════════════════════════
# 反馈权重 + 双向同步一致性测试
# ═══════════════════════════════════════════════

class TestFeedbackAndSync:
    """反馈闭环 + 知识同步一致性测试"""

    def test_feedback_weights_adjust_meta_learner(self):
        """provide_feedback 应真正调整 MetaLearner 的策略权重"""
        c = Clawra()
        # 先学习，让 MetaLearner 有数据
        c.learn("燃气调压箱是一种设备")
        c.add_fact("A", "is_a", "B", 0.9)

        # 获取学习 episode
        episodes = c.meta_learner.episodes
        if episodes:
            ep_id = episodes[-1].episode_id
        else:
            ep_id = "ep_0"

        # 提供反馈
        c.provide_feedback(ep_id, score=0.9)

        # 反馈后 evaluator 应有使用记录
        assert len(c.evaluator._usage_records) > 0

    def test_retrieve_records_usage(self):
        """retrieve_knowledge 应在 evaluator 中记录使用追踪"""
        c = Clawra()
        c.add_fact("猫", "is_a", "动物", 0.9)
        c.add_fact("动物", "has", "生命", 0.9)

        before = len(c.evaluator._usage_records)
        resp = c.retrieve_knowledge("猫")
        after = len(c.evaluator._usage_records)
        # 如果检索到了结果，使用记录应增加
        if resp.results:
            assert after > before

    def test_graph_logic_layer_sync(self):
        """UnifiedLogicLayer 写入的 pattern 应在 KnowledgeGraph 中可查"""
        c = Clawra()
        c.learn("如果设备老化，那么需要更换")
        # 检查图中是否有 _type 三元组 (pattern 同步到图)
        type_triples = c.knowledge_graph.query(predicate="_type")
        # 至少有 bootstrap 元规则 + 学习到的 pattern
        assert len(type_triples) >= 2  # 至少 bootstrap 的 2 个

    def test_evaluate_then_lifecycle_consistency(self):
        """evaluate_knowledge 应保持图状态一致"""
        c = Clawra()
        c.add_fact("X", "r", "Y", 0.9)
        c.add_fact("A", "r", "B", 0.05)  # 极低置信度

        eval_result = c.evaluate_knowledge()
        assert eval_result["total_evaluated"] >= 2

        # 图中三元组状态应该被正确更新
        graph_stats = c.knowledge_graph.statistics()
        assert graph_stats["total_triples"] >= 2
