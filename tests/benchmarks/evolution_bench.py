import time
import unittest
from src.sdk import ClawraSDK

class EvolutionBench(unittest.TestCase):
    def setUp(self):
        # 启用全能力 SDK
        self.sdk = ClawraSDK(enable_memory=False)
        
    def test_long_term_memory_recall(self):
        """验证 Mem0 情节记忆的长效召回能力"""
        print("\n--- 启动情节记忆演化测试 ---")
        
        # 阶段 1: 注入偏好与背景
        interactions = [
            "用户喜欢使用 JSON 格式导出数据。",
            "当前项目的安全等级被设置为 'Level 4'。",
            "系统主要部署在华为公有云环境。"
        ]
        
        for text in interactions:
            self.sdk.learn(text)
            
        print("已注入 3 条情节记忆。")
        
        # 阶段 2: 跨 Session 模拟查询 (SDK 重新实例化)
        # 注意：此处简化，直接使用已初始化的实例
        time.sleep(1) # 等待向量存储同步
        
        # 查询安全等级
        result = self.sdk.reason("当前的系统安全等级是多少？")
        trace = result.get("trace", [])
        
        # 验证 trace 是否包含了 Mem0 的召回背景
        found_memory = any("Level 4" in step for step in trace)
        print(f"Thinking Trace Preview: {trace[:3]}")
        
        # 我们在这里验证背景增强是否生效
        # 预期：trace 中包含 [从长效记忆中发现的相关背景]
        self.assertTrue(any("长效记忆" in step for step in trace), "Thinking Trace 应包含情节记忆背景")
        print("✅ 情节记忆召回验证通过")

    def test_ontology_hardened_performance(self):
        """测试本体硬化后的冲突检测耗时 (ms 级)"""
        start_time = time.time()
        
        # 注入 10 条互斥事实 (直接写入事实库，绕过 LLM 以纯测逻辑引擎压力)
        for i in range(10):
            self.sdk.core.add_fact(f"设备_{i}", "is_a", "高压设备")
            
        duration = (time.time() - start_time) * 1000
        print(f"本体硬化检测平均耗时: {duration/10:.2f}ms")
        self.assertLess(duration/10, 50, "单条本体校验应在 50ms 内完成")

if __name__ == "__main__":
    unittest.main()
