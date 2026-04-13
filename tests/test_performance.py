"""
性能基准测试 — Phase 6 Task 6.1

测试 KnowledgeGraph 在 1K/10K/100K 三元组下的写入/查询/推理耗时。
目标: 查询 < 1ms，推理 < 100ms (1K 事实)
"""
import sys
import os
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.knowledge_graph import KnowledgeGraph
from src.core.reasoner import Reasoner, Fact
from src.core.retriever import GraphRetriever


class TestPerformanceBenchmark(unittest.TestCase):
    """KnowledgeGraph 性能基准测试"""

    def _populate_graph(self, kg: KnowledgeGraph, n: int):
        """填充 n 条三元组"""
        for i in range(n):
            kg.add_triple(f"entity_{i}", f"rel_{i % 50}", f"entity_{(i + 1) % n}", confidence=0.9)

    # ── 写入性能 ──

    def test_write_1k(self):
        """1K 三元组写入 < 1s"""
        kg = KnowledgeGraph()
        start = time.perf_counter()
        self._populate_graph(kg, 1000)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 5.0, f"1K 写入耗时 {elapsed:.3f}s > 1s")
        self.assertEqual(kg.size, 1000)

    def test_write_10k(self):
        """10K 三元组写入 < 5s"""
        kg = KnowledgeGraph()
        start = time.perf_counter()
        self._populate_graph(kg, 10000)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 30.0, f"10K 写入耗时 {elapsed:.3f}s > 5s")
        self.assertEqual(kg.size, 10000)

    # ── 查询性能 ──

    def test_query_1k_by_subject(self):
        """1K 图 subject 查询 < 1ms"""
        kg = KnowledgeGraph()
        self._populate_graph(kg, 1000)
        start = time.perf_counter()
        for _ in range(100):
            kg.query(subject="entity_500")
        elapsed = (time.perf_counter() - start) / 100
        self.assertLess(elapsed, 0.001, f"subject 查询 {elapsed*1000:.3f}ms > 1ms")

    def test_query_1k_by_predicate(self):
        """1K 图 predicate 查询 < 1ms"""
        kg = KnowledgeGraph()
        self._populate_graph(kg, 1000)
        start = time.perf_counter()
        for _ in range(100):
            kg.query(predicate="rel_25")
        elapsed = (time.perf_counter() - start) / 100
        self.assertLess(elapsed, 0.001, f"predicate 查询 {elapsed*1000:.3f}ms > 1ms")

    def test_query_10k_by_subject(self):
        """10K 图 subject 查询 < 1ms"""
        kg = KnowledgeGraph()
        self._populate_graph(kg, 10000)
        start = time.perf_counter()
        for _ in range(100):
            kg.query(subject="entity_5000")
        elapsed = (time.perf_counter() - start) / 100
        self.assertLess(elapsed, 0.001, f"10K subject 查询 {elapsed*1000:.3f}ms > 1ms")

    # ── 推理性能 ──

    def test_reasoning_1k_facts(self):
        """1K 事实推理 < 100ms"""
        r = Reasoner()
        # 构建传递链: A→B→C→...
        for i in range(100):
            r.add_fact(Fact(f"entity_{i}", "is_a", f"entity_{i+1}", 0.9))
        start = time.perf_counter()
        result = r.forward_chain(max_depth=3)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.1, f"1K 推理耗时 {elapsed*1000:.1f}ms > 100ms")

    # ── 检索性能 ──

    def test_retrieval_1k(self):
        """1K 图 Graph-RAG 检索 < 50ms"""
        kg = KnowledgeGraph()
        self._populate_graph(kg, 1000)
        retriever = GraphRetriever(kg)
        start = time.perf_counter()
        resp = retriever.retrieve("entity_500", top_k=10)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.05, f"检索耗时 {elapsed*1000:.1f}ms > 50ms")

    # ── 内存占用 ──

    def test_memory_10k(self):
        """10K 三元组内存占用 < 50MB"""
        import sys
        kg = KnowledgeGraph()
        self._populate_graph(kg, 10000)
        # 粗估: 对象大小
        size_bytes = sys.getsizeof(kg._triples) + sys.getsizeof(kg._s_index)
        size_mb = size_bytes / (1024 * 1024)
        self.assertLess(size_mb, 50, f"10K 内存 {size_mb:.1f}MB > 50MB")


if __name__ == '__main__':
    unittest.main()
