"""
EvolutionLoop 完整测试套件

测试 8 阶段进化闭环、失败反馈路由、PhaseResult 等核心功能
"""
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from src.evolution.evolution_loop import (
    EvolutionLoop,
    EvolutionPhase,
    FailureType,
    FeedbackSignal,
    PhaseResult,
    EvolutionLoopState,
)


class TestEvolutionLoopBasics(unittest.TestCase):
    """基础功能测试"""

    def setUp(self):
        self.loop = EvolutionLoop(
            meta_learner=None,
            rule_discovery=None,
            evaluator=None,
            reasoner=None,
        )

    def test_initialization(self):
        """EvolutionLoop 初始化"""
        self.assertIsNotNone(self.loop)
        self.assertIsNotNone(self.loop._state)
        self.assertEqual(self.loop._state.current_phase, EvolutionPhase.PERCEIVE)

    def test_phase_sequence(self):
        """8 阶段顺序正确"""
        expected = [
            EvolutionPhase.PERCEIVE,
            EvolutionPhase.LEARN,
            EvolutionPhase.REASON,
            EvolutionPhase.EXECUTE,
            EvolutionPhase.EVALUATE,
            EvolutionPhase.DETECT_DRIFT,
            EvolutionPhase.REVISE_RULES,
            EvolutionPhase.UPDATE_KG,
        ]
        self.assertEqual(self.loop._phase_sequence, expected)

    def test_phase_result_dataclass(self):
        """PhaseResult 数据类"""
        result = PhaseResult(
            phase=EvolutionPhase.PERCEIVE,
            success=True,
            data={"entities": ["设备A"]},
            duration=0.123,
        )
        self.assertEqual(result.phase, EvolutionPhase.PERCEIVE)
        self.assertTrue(result.success)
        self.assertEqual(result.data["entities"], ["设备A"])
        self.assertEqual(result.duration, 0.123)

    def test_feedback_signal_dataclass(self):
        """FeedbackSignal 数据类"""
        signal = FeedbackSignal(
            failure_type=FailureType.INFERENCE_ERROR,
            source_phase=EvolutionPhase.REASON,
            context={"error": "timeout"},
            retry_count=1,
        )
        self.assertEqual(signal.failure_type, FailureType.INFERENCE_ERROR)
        self.assertEqual(signal.source_phase, EvolutionPhase.REASON)
        self.assertEqual(signal.retry_count, 1)
        d = signal.to_dict()
        self.assertEqual(d["failure_type"], "inference_error")


class TestEvolutionLoopPhases(unittest.TestCase):
    """各阶段执行测试"""

    def setUp(self):
        # 创建带 mock 组件的 loop
        self.mock_learner = MagicMock()
        self.mock_reasoner = MagicMock()
        self.mock_evaluator = MagicMock()

        self.loop = EvolutionLoop(
            meta_learner=self.mock_learner,
            rule_discovery=MagicMock(),
            evaluator=self.mock_evaluator,
            reasoner=self.mock_reasoner,
            logic_layer=MagicMock(),
        )

    def test_perceive_phase_success(self):
        """感知阶段成功"""
        result = self.loop.step({
            "text": "燃气调压箱出口压力 ≤ 0.4MPa",
            "phase": EvolutionPhase.PERCEIVE,
        })
        self.assertTrue(result.success)
        self.assertEqual(result.phase, EvolutionPhase.PERCEIVE)
        self.assertIn("entities", result.data)
        self.assertIn("text", result.data)

    def test_perceive_phase_empty_text(self):
        """感知阶段空文本"""
        result = self.loop.step({
            "text": "",
            "phase": EvolutionPhase.PERCEIVE,
        })
        self.assertTrue(result.success)  # 降级处理

    def test_reason_phase_no_reasoner(self):
        """推理阶段无 reasoner 时失败"""
        loop = EvolutionLoop(meta_learner=None)
        result = loop.step({
            "phase": EvolutionPhase.REASON,
            "facts": [],
        })
        self.assertFalse(result.success)
        self.assertIn("未配置", result.error)

    def test_reason_phase_with_mock(self):
        """推理阶段正常"""
        self.mock_reasoner.forward_chain.return_value = {
            "conclusions": [{"id": "c1", "content": "压力正常"}]
        }
        result = self.loop.step({
            "phase": EvolutionPhase.REASON,
            "facts": [{"subject": "压力", "predicate": "值为", "object": "0.3MPa"}],
        })
        self.assertTrue(result.success)
        self.assertIn("conclusions", result.data)

    def test_detect_drift_phase_no_drift(self):
        """漂移检测无漂移"""
        result = self.loop.step({
            "phase": EvolutionPhase.DETECT_DRIFT,
            "data": {"drift_detected": False},
        })
        self.assertTrue(result.success)
        self.assertFalse(result.data["drift_detected"])

    def test_detect_drift_phase_with_drift(self):
        """漂移检测有漂移"""
        mock_logic = MagicMock()
        mock_logic._patterns = {
            "p1": MagicMock(confidence=0.2),  # 低置信度
        }
        loop = EvolutionLoop(logic_layer=mock_logic)

        result = loop.step({
            "phase": EvolutionPhase.DETECT_DRIFT,
            "data": {"drift_detected": True, "reason": "低置信度模式"},
        })
        self.assertTrue(result.success)
        self.assertTrue(result.data["drift_detected"])

    def test_revise_rules_no_drift(self):
        """规则修正无漂移时跳过"""
        result = self.loop.step({
            "phase": EvolutionPhase.REVISE_RULES,
            "data": {"drift_detected": False},
        })
        self.assertTrue(result.success)
        self.assertEqual(result.data["revised"], 0)

    def test_update_kg_phase(self):
        """知识更新阶段"""
        result = self.loop.step({
            "phase": EvolutionPhase.UPDATE_KG,
            "patterns_created": ["p1", "p2"],
            "domain": "燃气",
        })
        self.assertTrue(result.success)


class TestEvolutionLoopFailureRouting(unittest.TestCase):
    """失败反馈路由测试"""

    def setUp(self):
        self.loop = EvolutionLoop(
            meta_learner=MagicMock(),
            rule_discovery=MagicMock(),
        )

    def test_create_feedback_signal_inference_error(self):
        """推理错误反馈"""
        result = PhaseResult(
            phase=EvolutionPhase.REASON,
            success=False,
            error="timeout",
        )
        signal = self.loop._create_feedback_signal(EvolutionPhase.REASON, result)
        self.assertEqual(signal.failure_type, FailureType.INFERENCE_ERROR)
        self.assertEqual(signal.source_phase, EvolutionPhase.REASON)

    def test_create_feedback_signal_learning_error(self):
        """学习错误反馈"""
        result = PhaseResult(
            phase=EvolutionPhase.LEARN,
            success=False,
            error="llm error",
        )
        signal = self.loop._create_feedback_signal(EvolutionPhase.LEARN, result)
        self.assertEqual(signal.failure_type, FailureType.LEARNING_ERROR)

    def test_route_failure_increments_retry(self):
        """失败路由增加重试计数"""
        signal = FeedbackSignal(
            failure_type=FailureType.INFERENCE_ERROR,
            source_phase=EvolutionPhase.REASON,
            context={},
            retry_count=0,
        )
        handled = self.loop._route_failure(signal)
        self.assertTrue(handled)
        self.assertEqual(signal.retry_count, 1)

    def test_route_failure_stops_after_3_retries(self):
        """超过3次重试停止"""
        signal = FeedbackSignal(
            failure_type=FailureType.INFERENCE_ERROR,
            source_phase=EvolutionPhase.REASON,
            context={},
            retry_count=3,
        )
        handled = self.loop._route_failure(signal)
        self.assertTrue(handled)  # 认为已处理（丢弃）


class TestEvolutionLoopState(unittest.TestCase):
    """状态管理测试"""

    def test_state_reset(self):
        """状态重置"""
        loop = EvolutionLoop()
        loop._state.iterations = 10
        loop._state.converged = True

        loop._state.reset()

        self.assertEqual(loop._state.current_phase, EvolutionPhase.PERCEIVE)
        self.assertEqual(loop._state.iterations, 0)
        self.assertFalse(loop._state.converged)
        self.assertEqual(len(loop._state.results), 0)

    def test_register_hook(self):
        """阶段钩子注册"""
        loop = EvolutionLoop()
        called = []

        def my_hook(result):
            called.append(result.phase)

        loop.register_hook(EvolutionPhase.PERCEIVE, my_hook)
        self.assertEqual(loop._phase_hooks[EvolutionPhase.PERCEIVE], my_hook)


class TestEvolutionPhaseEnum(unittest.TestCase):
    """Phase 枚举测试"""

    def test_phase_values(self):
        self.assertEqual(EvolutionPhase.PERCEIVE.value, "perceive")
        self.assertEqual(EvolutionPhase.REASON.value, "reason")
        self.assertEqual(EvolutionPhase.EVALUATE.value, "evaluate")
        self.assertEqual(EvolutionPhase.UPDATE_KG.value, "update_kg")
        self.assertEqual(EvolutionPhase.META_LEARN.value, "meta_learn")

    def test_phase_from_string(self):
        p = EvolutionPhase("perceive")
        self.assertEqual(p, EvolutionPhase.PERCEIVE)


if __name__ == "__main__":
    unittest.main()
