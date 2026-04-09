import unittest
from src.sdk import ClawraSDK
import os

class TestSDKHardening(unittest.TestCase):
    def setUp(self):
        # 使用内存模式或临时目录避免污染
        self.sdk = ClawraSDK(enable_memory=False)

    def test_learn_and_reason_v4(self):
        """测试 v4.0 的 learn 与 reason (真实调用 orchestrate)"""
        self.sdk.learn("燃气调压器是燃气设备。")
        self.sdk.learn("燃气设备是工业资产。")
        
        # 测试理由 (reason internally calls orchestrate)
        result = self.sdk.reason("什么是燃气调压器？")
        
        self.assertIn("trace", result)
        self.assertIn("conclusions", result)
        self.assertTrue(len(result["trace"]) >= 3)
        print(f"Thinking Trace: {result['trace']}")

    def test_export_graph(self):
        """测试 D3 图数据导出"""
        self.sdk.learn("A 是 B")
        data = self.sdk.get_graph_data()
        
        self.assertIn("nodes", data)
        self.assertIn("links", data)
        self.assertTrue(any(node["id"] == "A" for node in data["nodes"]))

    def test_evolve_v4(self):
        """测试进化闭环回调"""
        result = self.sdk.evolve()
        self.assertEqual(result["status"], "success")
        self.assertIn("results", result)
        print(f"Evolve Result: {result}")

if __name__ == "__main__":
    unittest.main()
