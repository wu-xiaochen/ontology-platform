"""
单元测试 - RDF适配器

测试置信度传播和推理链追溯功能
"""

import unittest
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ontology.rdf_adapter import RDFAdapter, RDFTriple, RDFTerm, RDFTermType
from ontology.neo4j_client import Neo4jClient, GraphNode, GraphRelationship


class TestRDFAdapter(unittest.TestCase):
    """RDF适配器测试"""

    def setUp(self):
        """测试前准备"""
        self.adapter = RDFAdapter("http://example.org/test/")

    def test_create_triple(self):
        """测试创建三元组"""
        self.adapter.add_triple(
            "http://example.org/Alice",
            "http://example.org/knows",
            "http://example.org/Bob",
            confidence=0.9,
            source="test"
        )

        self.assertEqual(len(self.adapter.triples), 1)
        triple = self.adapter.triples[0]
        self.assertEqual(triple.confidence, 0.9)
        self.assertEqual(triple.source, "test")

    def test_query_with_confidence(self):
        """测试带置信度过滤的查询"""
        self.adapter.add_triple("A", "knows", "B", confidence=0.9)
        self.adapter.add_triple("A", "knows", "C", confidence=0.5)
        self.adapter.add_triple("A", "likes", "D", confidence=0.8)

        # 查询所有
        results = self.adapter.query(subject="A")
        self.assertEqual(len(results), 3)

        # 高置信度查询
        results = self.adapter.query(subject="A", min_confidence=0.8)
        self.assertEqual(len(results), 2)

    def test_confidence_propagation(self):
        """测试置信度传播"""
        # 构建测试图: A -> B -> C -> D
        # A -> B: 0.9, B -> C: 0.8, C -> D: 0.7
        self.adapter.add_triple("A", "knows", "B", confidence=0.9)
        self.adapter.add_triple("B", "knows", "C", confidence=0.8)
        self.adapter.add_triple("C", "knows", "D", confidence=0.7)

        # 传播置信度
        result = self.adapter.propagate_confidence("A", max_depth=3, method="multiplicative")

        # 验证 - 检查任意一个可用的键
        b_conf = result.get("B") or result.get("B".replace(self.adapter.base_uri, ""))
        c_conf = result.get("C") or result.get("C".replace(self.adapter.base_uri, ""))
        
        self.assertIn("A", result)
        self.assertIsNotNone(b_conf)
        self.assertIsNotNone(c_conf)

        # 乘法传播: A->B 是 0.9, A->B->C 是 0.9 * 0.8 = 0.72
        self.assertAlmostEqual(b_conf, 0.9, places=2)
        self.assertAlmostEqual(c_conf, 0.9 * 0.8, places=2)

    def test_confidence_propagation_methods(self):
        """测试不同置信度传播方法"""
        self.adapter.add_triple("A", "knows", "B", confidence=0.9)
        self.adapter.add_triple("B", "knows", "C", confidence=0.8)

        # min 方法
        result_min = self.adapter.propagate_confidence("A", method="min")
        self.assertEqual(result_min["B"], 0.9)
        self.assertEqual(result_min["C"], 0.8)  # min(0.9, 0.8) = 0.8

        # arithmetic 方法
        result_arith = self.adapter.propagate_confidence("A", method="arithmetic")
        self.assertAlmostEqual(result_arith["B"], (1.0 + 0.9) / 2, places=2)

    def test_trace_inference(self):
        """测试推理链追溯"""
        # 构建测试图: A -> B -> C
        self.adapter.add_triple("A", "knows", "B", confidence=0.9)
        self.adapter.add_triple("B", "knows", "C", confidence=0.8)

        # 追溯路径
        paths = self.adapter.trace_inference("A", "C", max_depth=5)

        # 验证
        self.assertGreater(len(paths), 0)
        path = paths[0]
        self.assertEqual(path["nodes"], ["A", "B", "C"])
        self.assertEqual(path["depth"], 2)

    def test_trace_inference_multiple_paths(self):
        """测试多路径推理链追溯"""
        # 构建菱形图: A -> B -> D, A -> C -> D
        self.adapter.add_triple("A", "r1", "B", confidence=0.9)
        self.adapter.add_triple("B", "r2", "D", confidence=0.8)
        self.adapter.add_triple("A", "r3", "C", confidence=0.85)
        self.adapter.add_triple("C", "r4", "D", confidence=0.75)

        paths = self.adapter.trace_inference("A", "D", max_depth=5)

        # 应该找到两条路径
        self.assertGreaterEqual(len(paths), 2)

    def test_trace_inference_no_path(self):
        """测试不存在路径的情况"""
        self.adapter.add_triple("A", "knows", "B", confidence=0.9)

        paths = self.adapter.trace_inference("A", "Z", max_depth=5)

        self.assertEqual(len(paths), 0)

    def test_reasoning_explanation(self):
        """测试推理解释生成"""
        self.adapter.add_triple("Alice", "knows", "Bob", confidence=0.9)
        self.adapter.add_triple("Bob", "worksWith", "Charlie", confidence=0.8)

        explanation = self.adapter.get_reasoning_explanation("Alice", "Charlie")

        self.assertIn("Alice", explanation)
        self.assertIn("Charlie", explanation)

    def test_compute_inference_confidence(self):
        """测试推理链置信度计算"""
        triples = [
            RDFTriple(
                subject=RDFTerm("A", RDFTermType.URI),
                predicate=RDFTerm("knows", RDFTermType.URI),
                object=RDFTerm("B", RDFTermType.URI),
                confidence=0.9
            ),
            RDFTriple(
                subject=RDFTerm("B", RDFTermType.URI),
                predicate=RDFTerm("knows", RDFTermType.URI),
                object=RDFTerm("C", RDFTermType.URI),
                confidence=0.8
            ),
        ]

        conf = self.adapter.compute_inference_confidence(triples)
        self.assertAlmostEqual(conf, 0.9 * 0.8, places=2)

    def test_confidence_propagation_with_cycle(self):
        """测试带循环的置信度传播"""
        # 构建带循环的图: A -> B -> C -> A
        self.adapter.add_triple("A", "knows", "B", confidence=0.9)
        self.adapter.add_triple("B", "knows", "C", confidence=0.8)
        self.adapter.add_triple("C", "knows", "A", confidence=0.7)

        result = self.adapter.propagate_confidence("A", max_depth=3)

        # A 不应该被重复访问
        self.assertEqual(result["A"], 1.0)

    def test_empty_propagation(self):
        """测试空图的置信度传播"""
        result = self.adapter.propagate_confidence("Unknown")
        self.assertEqual(result, {"Unknown": 1.0})


class TestNeo4jClient(unittest.TestCase):
    """Neo4j客户端测试（内存模式）"""

    def setUp(self):
        """测试前准备"""
        self.client = Neo4jClient()  # 内存模式

    def test_create_entity(self):
        """测试创建实体"""
        node = self.client.create_entity(
            "TestEntity",
            label="Test",
            properties={"key": "value"},
            confidence=0.85
        )

        self.assertIsNotNone(node)
        self.assertEqual(node.properties["name"], "TestEntity")
        self.assertEqual(node.confidence, 0.85)

    def test_get_entity(self):
        """测试获取实体"""
        self.client.create_entity("Alice", "Person", {"age": 30})
        
        node = self.client.get_entity("Alice")
        self.assertIsNotNone(node)
        self.assertEqual(node.properties["name"], "Alice")

    def test_create_relationship(self):
        """测试创建关系"""
        self.client.create_entity("Alice", "Person")
        self.client.create_entity("Bob", "Person")
        
        rel = self.client.create_relationship(
            "Alice", "Bob", "KNOWS",
            confidence=0.9
        )

        self.assertIsNotNone(rel)
        self.assertEqual(rel.type, "KNOWS")
        self.assertEqual(rel.confidence, 0.9)

    def test_get_relationships(self):
        """测试获取关系"""
        self.client.create_entity("Alice", "Person")
        self.client.create_entity("Bob", "Person")
        self.client.create_relationship("Alice", "Bob", "KNOWS")

        rels = self.client.get_relationships("Alice", direction="outgoing")
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0].end_node, "Bob")

    def test_confidence_propagation_neo4j(self):
        """测试Neo4j客户端的置信度传播（内存模式）"""
        self.client.create_entity("A", "Entity")
        self.client.create_entity("B", "Entity")
        self.client.create_entity("C", "Entity")

        self.client.create_relationship("A", "B", "KNOWS", confidence=0.9)
        self.client.create_relationship("B", "C", "KNOWS", confidence=0.8)

        result = self.client.propagate_confidence("A", max_depth=3)

        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertIn("C", result)
        self.assertAlmostEqual(result["B"], 0.9, places=2)

    def test_find_neighbors(self):
        """测试查找邻居"""
        self.client.create_entity("A", "Entity")
        self.client.create_entity("B", "Entity")
        self.client.create_entity("C", "Entity")

        self.client.create_relationship("A", "B", "KNOWS")
        self.client.create_relationship("A", "C", "KNOWS")

        result = self.client.find_neighbors("A", depth=1)

        self.assertGreater(len(result.nodes), 0)

    def test_batch_import(self):
        """测试批量导入"""
        triples = [
            {"subject": "A", "predicate": "knows", "object": "B", "confidence": 0.9},
            {"subject": "B", "predicate": "knows", "object": "C", "confidence": 0.8},
        ]

        self.client.batch_import_triples(triples)

        node_a = self.client.get_entity("A")
        self.assertIsNotNone(node_a)


class TestRDFDataClasses(unittest.TestCase):
    """RDF数据类测试"""

    def test_rdf_term_to_nt(self):
        """测试RDF术语转换为N-Triples"""
        term = RDFTerm("http://example.org/Alice", RDFTermType.URI)
        self.assertEqual(term.to_nt(), "<http://example.org/Alice>")

        term = RDFTerm("Alice", RDFTermType.LITERAL)
        self.assertEqual(term.to_nt(), '"Alice"')

        term = RDFTerm("42", RDFTermType.LITERAL, datatype="http://www.w3.org/2001/XMLSchema#integer")
        self.assertEqual(term.to_nt(), '"42"^^<http://www.w3.org/2001/XMLSchema#integer>')

    def test_rdf_triple_to_dict(self):
        """测试RDF三元组转换为字典"""
        triple = RDFTriple(
            subject=RDFTerm("http://example.org/Alice", RDFTermType.URI),
            predicate=RDFTerm("http://example.org/knows", RDFTermType.URI),
            object=RDFTerm("http://example.org/Bob", RDFTermType.URI),
            confidence=0.85
        )

        d = triple.to_dict()
        self.assertEqual(d["confidence"], 0.85)
        self.assertEqual(d["subject"]["value"], "http://example.org/Alice")


if __name__ == '__main__':
    unittest.main()
