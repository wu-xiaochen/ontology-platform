"""
行为学习器单元测试

验证 BehaviorLearner 的核心功能：
1. 交互记录和 FIFO 淘汰
2. 从历史中学习行为模式（频率/成功率过滤）
3. 按上下文查询模式
4. 空历史边界条件
"""
import os
import sys
import pytest

# 确保测试能找到 src 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 设置环境变量，确保测试环境独立于用户配置
os.environ.setdefault("SKIP_LLM", "true")

from src.evolution.behavior_learner import BehaviorLearner, BehaviorPattern


class TestBehaviorLearner:
    """行为学习器测试套件"""

    def setup_method(self):
        """每个测试方法执行前重置状态"""
        # 设置低阈值以便测试中容易触发模式发现
        os.environ["BEHAVIOR_MIN_FREQUENCY"] = "2"
        os.environ["BEHAVIOR_MIN_SUCCESS_RATE"] = "0.3"
        os.environ["BEHAVIOR_MAX_HISTORY_SIZE"] = "100"
        # 强制重建 ConfigManager 单例以应用测试配置
        import src.utils.config as config_module
        config_module.ConfigManager._instance = None
        config_module.config = config_module.ConfigManager()
        self.learner = BehaviorLearner()

    def teardown_method(self):
        """清理测试配置"""
        for key in ["BEHAVIOR_MIN_FREQUENCY", "BEHAVIOR_MIN_SUCCESS_RATE", "BEHAVIOR_MAX_HISTORY_SIZE"]:
            os.environ.pop(key, None)
        import src.utils.config as config_module
        config_module.ConfigManager._instance = None
        config_module.config = config_module.ConfigManager()

    def test_empty_history_returns_no_patterns(self):
        """空交互历史应返回空列表"""
        patterns = self.learner.learn_from_history()
        assert patterns == []

    def test_record_interaction_stores_data(self):
        """记录交互后历史列表应增长"""
        self.learner.record_interaction(
            context={"type": "query"},
            action="search",
            outcome="found results",
            success=True
        )
        assert len(self.learner.interaction_history) == 1

    def test_learn_discovers_frequent_patterns(self):
        """高频行为应被发现为模式"""
        # 记录 3 次相同的 (query, search) 行为
        for _ in range(3):
            self.learner.record_interaction(
                context={"type": "query"},
                action="search",
                outcome="found",
                success=True
            )
        
        patterns = self.learner.learn_from_history()
        # 应发现 1 个模式
        assert len(patterns) == 1
        assert patterns[0].context_type == "query"
        assert patterns[0].action == "search"
        assert patterns[0].frequency == 3
        assert patterns[0].success_rate == 1.0

    def test_low_frequency_filtered_out(self):
        """低频行为应被过滤（min_frequency=2）"""
        # 只记录 1 次 —— 低于最小频率阈值
        self.learner.record_interaction(
            context={"type": "rare"},
            action="rare_action",
            outcome="done",
            success=True
        )
        patterns = self.learner.learn_from_history()
        assert len(patterns) == 0

    def test_low_success_rate_filtered_out(self):
        """低成功率行为应被过滤（min_success_rate=0.3）"""
        # 记录 5 次，全部失败 → 成功率 0.0 < 0.3
        for _ in range(5):
            self.learner.record_interaction(
                context={"type": "test"},
                action="fail_action",
                outcome="failed",
                success=False
            )
        patterns = self.learner.learn_from_history()
        assert len(patterns) == 0

    def test_mixed_success_rate(self):
        """混合成功率应正确计算"""
        # 3 成功 + 1 失败 → 成功率 0.75
        for i in range(4):
            self.learner.record_interaction(
                context={"type": "mixed"},
                action="mixed_action",
                outcome="ok" if i < 3 else "fail",
                success=(i < 3)
            )
        patterns = self.learner.learn_from_history()
        assert len(patterns) == 1
        assert abs(patterns[0].success_rate - 0.75) < 0.01

    def test_get_patterns_by_context(self):
        """按上下文类型查询应返回正确模式"""
        # 创建两种不同上下文的行为
        for _ in range(3):
            self.learner.record_interaction(
                context={"type": "alpha"},
                action="a1",
                outcome="ok",
                success=True
            )
        for _ in range(3):
            self.learner.record_interaction(
                context={"type": "beta"},
                action="b1",
                outcome="ok",
                success=True
            )
        self.learner.learn_from_history()
        
        alpha_patterns = self.learner.get_patterns_by_context("alpha")
        assert len(alpha_patterns) == 1
        assert alpha_patterns[0].context_type == "alpha"

    def test_fifo_eviction(self):
        """超过最大容量时应 FIFO 淘汰旧记录"""
        # max_history_size=100，写入 120 条
        for i in range(120):
            self.learner.record_interaction(
                context={"type": "test"},
                action=f"action_{i}",
                outcome="ok",
                success=True
            )
        # 淘汰机制：每次超出上限时批量淘汰 10%，所以最终长度应 < 写入总数
        assert len(self.learner.interaction_history) < 120

    def test_clear_resets_state(self):
        """clear 应清空所有状态"""
        self.learner.record_interaction(
            context={"type": "test"},
            action="act",
            outcome="ok",
            success=True
        )
        self.learner.clear()
        assert len(self.learner.interaction_history) == 0
        assert len(self.learner.behaviors) == 0

    def test_pattern_deduplication(self):
        """重复学习不应创建重复模式"""
        for _ in range(3):
            self.learner.record_interaction(
                context={"type": "dup"},
                action="act",
                outcome="ok",
                success=True
            )
        
        # 第一次学习
        patterns1 = self.learner.learn_from_history()
        assert len(patterns1) == 1
        
        # 再添加记录并第二次学习
        for _ in range(2):
            self.learner.record_interaction(
                context={"type": "dup"},
                action="act",
                outcome="ok",
                success=True
            )
        patterns2 = self.learner.learn_from_history()
        # 应更新已有模式而非创建新的
        assert len(patterns2) == 0
        # 总模式数仍然是 1
        assert len(self.learner.behaviors) == 1
