"""
自我纠错模块单元测试

验证 ContradictionChecker 和 ReflectionLoop 的核心功能：
1. 从 JSON 配置文件加载反义词映射
2. 冲突检测正确识别矛盾事实
3. 无冲突事实正常通过
4. 反思回路的循环检测
5. 失败分析报告
"""
import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault("SKIP_LLM", "true")

from src.core.reasoner import Reasoner, Fact
from src.evolution.self_correction import ContradictionChecker, ReflectionLoop


class TestContradictionChecker:
    """冲突检查器测试套件"""

    def setup_method(self):
        """初始化"""
        import src.utils.config as config_module
        config_module.ConfigManager._instance = None
        config_module.config = config_module.ConfigManager()
        self.reasoner = Reasoner()
        self.checker = ContradictionChecker(self.reasoner)

    def teardown_method(self):
        import src.utils.config as config_module
        config_module.ConfigManager._instance = None
        config_module.config = config_module.ConfigManager()

    def test_no_conflict_passes(self):
        """无冲突的事实应通过检测"""
        fact = Fact("Device1", "status", "normal", confidence=0.9, source="test")
        result = self.checker.check_fact(fact)
        assert result is True

    def test_conflict_with_existing_fact(self):
        """与已有事实冲突应被检测到"""
        # 添加已有事实
        self.reasoner.add_fact(
            Fact("Device1", "status", "safe", confidence=0.9, source="existing")
        )
        # 尝试添加冲突事实 —— "high_risk" 与 "safe" 互斥
        conflicting = Fact("Device1", "status", "high_risk", confidence=0.8, source="new")
        result = self.checker.check_fact(conflicting)
        assert result is False

    def test_no_antonym_allows_write(self):
        """没有反义词定义的概念应放行"""
        self.reasoner.add_fact(
            Fact("Item1", "color", "red", confidence=0.9, source="existing")
        )
        # "blue" 和 "red" 没有反义词关系定义
        new_fact = Fact("Item1", "color", "blue", confidence=0.8, source="new")
        result = self.checker.check_fact(new_fact)
        assert result is True

    def test_custom_antonym_file(self):
        """应能从自定义 JSON 文件加载反义词"""
        # 创建临时反义词文件
        custom_mapping = {"good": ["bad"], "bad": ["good"]}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_mapping, f)
            temp_path = f.name

        try:
            # 设置自定义路径并重建 ConfigManager 单例
            os.environ["ANTONYM_MAPPING_PATH"] = temp_path
            import src.utils.config as config_module
            config_module.ConfigManager._instance = None
            config_module.config = config_module.ConfigManager()
            
            # 使用干净的 Reasoner 创建新 checker
            reasoner = Reasoner()
            checker = ContradictionChecker(reasoner)
            reasoner.add_fact(
                Fact("Quality", "rating", "good", confidence=0.9, source="test")
            )
            # "bad" 与 "good" 互斥（来自自定义映射文件）
            conflict = Fact("Quality", "rating", "bad", confidence=0.8, source="new")
            result = checker.check_fact(conflict)
            assert result is False
        finally:
            os.unlink(temp_path)
            os.environ.pop("ANTONYM_MAPPING_PATH", None)
            import src.utils.config as config_module
            config_module.ConfigManager._instance = None
            config_module.config = config_module.ConfigManager()

    def test_reload_antonyms(self):
        """重新加载反义词不应抛出异常"""
        self.checker.reload_antonyms()
        # 重新加载后仍能正常检测
        fact = Fact("X", "p", "v", confidence=0.9, source="test")
        assert self.checker.check_fact(fact) is True


class TestReflectionLoop:
    """反思回路测试套件"""

    def setup_method(self):
        """初始化"""
        # 设置较小的最大迭代次数便于测试
        os.environ["SELF_CORRECTION_MAX_ITERATIONS"] = "5"
        import src.utils.config as config_module
        config_module.ConfigManager._instance = None
        config_module.config = config_module.ConfigManager()
        self.reasoner = Reasoner()
        self.loop = ReflectionLoop(self.reasoner)

    def teardown_method(self):
        os.environ.pop("SELF_CORRECTION_MAX_ITERATIONS", None)
        import src.utils.config as config_module
        config_module.ConfigManager._instance = None
        config_module.config = config_module.ConfigManager()

    def test_valid_trace_passes(self):
        """合理的推理轨迹应通过"""
        trace = ["Step 1: Identify input", "Step 2: Apply rule", "Step 3: Conclude"]
        result = self.loop.evaluate_thought(trace)
        assert result is True

    def test_empty_trace_passes(self):
        """空轨迹应通过（没有引发违规条件）"""
        result = self.loop.evaluate_thought([])
        assert result is True

    def test_too_long_trace_fails(self):
        """超过最大迭代次数的轨迹应失败"""
        trace = [f"Step {i}" for i in range(10)]  # > max_iterations=5
        result = self.loop.evaluate_thought(trace)
        assert result is False

    def test_duplicate_step_fails(self):
        """包含重复步骤的轨迹应失败（循环推理）"""
        trace = ["Step A", "Step B", "Step A"]
        result = self.loop.evaluate_thought(trace)
        assert result is False

    def test_analyze_failure_empty_trace(self):
        """空轨迹的失败分析"""
        report = self.loop.analyze_failure([], "No output")
        assert report["diagnosis"] == "empty_trace"

    def test_analyze_failure_infinite_loop(self):
        """超长轨迹的失败分析"""
        trace = [f"Step {i}" for i in range(10)]
        report = self.loop.analyze_failure(trace, "timeout")
        assert report["diagnosis"] == "infinite_loop"

    def test_analyze_failure_circular(self):
        """循环推理的失败分析"""
        trace = ["Step A", "Step B", "Step A"]
        report = self.loop.analyze_failure(trace, "contradiction")
        assert report["diagnosis"] == "circular_reasoning"
        assert report["problematic_step"] == 2
