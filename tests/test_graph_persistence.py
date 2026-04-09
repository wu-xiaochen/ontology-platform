import unittest
import unittest.mock
import os
import shutil
import sqlite3
from src.memory.sqlite_graph_adapter import SQLiteGraph
from src.memory.base import SemanticMemory
from src.core.reasoner import Fact

class TestGraphPersistence(unittest.TestCase):
    def setUp(self):
        self.test_db_dir = "data/test"
        self.test_db_path = os.path.join(self.test_db_dir, "test_knowledge.db")
        if os.path.exists(self.test_db_dir):
            shutil.rmtree(self.test_db_dir)
        os.makedirs(self.test_db_dir)

    def tearDown(self):
        if os.path.exists(self.test_db_dir):
            shutil.rmtree(self.test_db_dir)

    def test_sqlite_adapter_persistence(self):
        """测试适配层本身的物理持久化"""
        adapter = SQLiteGraph(db_path=self.test_db_path)
        
        # 1. 写入数据
        adapter.add_relationship("Apple", "is_a", "Fruit", confidence=0.9)
        stats = adapter.get_stats()
        self.assertEqual(stats["nodes"], 2)
        self.assertEqual(stats["relationships"], 1)
        
        # 2. 模拟进程重启 (重新实例化)
        adapter2 = SQLiteGraph(db_path=self.test_db_path)
        stats2 = adapter2.get_stats()
        self.assertEqual(stats2["nodes"], 2, "数据未能从磁盘加载")
        
        # 3. 验证内容
        neighbors = adapter2.find_neighbors("Apple", depth=1)
        self.assertEqual(len(neighbors["relationships"]), 1)
        self.assertEqual(neighbors["relationships"][0]["rel_type"], "is_a")
        
        # 4. 验证全量采样 (Sampling)
        samples = adapter2.get_all_relationships(limit=10)
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0]["start_node_name"], "Apple")

    def test_semantic_memory_integration(self):
        """测试 SemanticMemory 顶层集成"""
        # 使用更稳健的 patch 方式
        with unittest.mock.patch("src.memory.sqlite_graph_adapter.SQLiteGraph") as MockGraph:
            instance = MockGraph.return_value
            # 模拟统计信息
            instance.get_stats.return_value = {"relationships": 1}
            # 模拟查询返回实事
            instance.find_neighbors.return_value = {
                "relationships": [{"rel_type": "version", "end_node_name": "v8.0"}]
            }
            
            memory = SemanticMemory(use_mock=True)
            memory.local_graph = instance # 直接注入模拟实例
            
            # 验证统计信息透传
            count = memory.get_total_facts_count()
            self.assertEqual(count, 1)
            
            # 验证查询透传
            results = memory.query("Clawra", depth=1)
            self.assertEqual(results[0].predicate, "version")
            self.assertEqual(results[0].object, "v8.0")

if __name__ == "__main__":
    unittest.main()
