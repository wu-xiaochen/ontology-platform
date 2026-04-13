import unittest
from unittest.mock import MagicMock, patch
import os
import shutil
from src.memory.episodic_enhanced import EpisodicMemoryManager
from src.utils.config import get_config

class TestEpisodicMemory(unittest.TestCase):
    """
    情节记忆增强层单元测试
    
    测试重点：
    1. 初始化过程是否正确读取配置
    2. Fallback 机制在大模型 API 失败时的有效性
    3. 记忆搜索结果的结构化输出
    """

    def setUp(self):
        # 初始化配置管理器
        self.config = get_config()
        # 确保测试数据目录干净
        self.test_data_dir = os.path.join(self.config.app.data_dir, "test_mem0")
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
        os.makedirs(self.test_data_dir, exist_ok=True)

    @patch("src.memory.episodic_enhanced.Memory.from_config")
    def test_initialization_success(self, mock_mem0):
        """测试正常初始化流程"""
        # 模拟 Mem0 返回实例
        mock_instance = MagicMock()
        mock_mem0.return_value = mock_instance
        
        # 执行初始化
        mgr = EpisodicMemoryManager(user_id="test_user")
        
        # 验证是否调用了 from_config 且参数包含 embedder
        self.assertTrue(mock_mem0.called)
        args, kwargs = mock_mem0.call_args
        config_arg = args[0]
        self.assertIn("embedder", config_arg)
        self.assertEqual(config_arg["embedder"]["config"]["model"], self.config.llm.embedding_model)
        self.assertFalse(hasattr(mgr, '_is_fallback'))

    @patch("src.memory.episodic_enhanced.Memory.from_config")
    def test_initialization_fallback(self, mock_mem0):
        """测试初始化失败时的降级逻辑"""
        # 模拟 Mem0 初始化抛出异常（如缺少库或配置错误）
        mock_mem0.side_effect = Exception("Mem0 init failed")
        
        # 执行初始化
        mgr = EpisodicMemoryManager(user_id="test_user")
        
        # 验证是否切换到了 fallback 模式
        self.assertTrue(hasattr(mgr, '_is_fallback'))
        self.assertTrue(mgr._is_fallback)

    def test_structured_context_empty(self):
        """测试无记忆时的上下文输出"""
        mgr = EpisodicMemoryManager(user_id="test_user")
        # 手动模拟没有记忆的情况
        mgr.search_memories = MagicMock(return_value=[])
        
        context = mgr.get_structured_context("test query")
        self.assertEqual(context, "")

    def test_structured_context_with_data(self):
        """测试有记忆时的上下文美化输出"""
        mgr = EpisodicMemoryManager(user_id="test_user")
        # 模拟搜索返回
        mgr.search_memories = MagicMock(return_value=[
            {"text": "用户喜欢燃气设备。"},
            {"text": "上一次讨论了调压箱。"}
        ])
        
        context = mgr.get_structured_context("燃气")
        self.assertIn("[从长效记忆中发现的相关背景]", context)
        self.assertIn("用户喜欢燃气设备", context)
        self.assertIn("上一次讨论了调压箱", context)

    @patch("src.memory.episodic_enhanced.Memory.from_config")
    def test_runtime_404_fallback(self, mock_mem0):
        """测试运行时遇到 404 (模型不存在) 时的热补丁降级"""
        mock_instance = MagicMock()
        mock_mem0.return_value = mock_instance
        
        # 模拟 add 方法抛出 404 错误
        mock_instance.add.side_effect = Exception("404 Not Found: The model does not exist")
        
        mgr = EpisodicMemoryManager(user_id="test_user")
        # 此时尚未 fallback
        self.assertFalse(hasattr(mgr, '_is_fallback'))
        
        # 执行添加动作，触发异常捕获
        mgr.add_interaction("这是一条会触发 404 的消息")
        
        # 验证是否已自动切入 fallback
        self.assertTrue(mgr._is_fallback)
        self.assertTrue(hasattr(mgr, 'memory'))

if __name__ == "__main__":
    unittest.main()
