"""
Tests for episodic_memory module
"""
import pytest
import time
from src.evolution.episodic_memory import (
    EpisodicMemory,
    Episode,
    OutcomeType,
)


class TestEpisodicMemory:
    """EpisodicMemory 测试"""

    def test_add_success(self):
        """记录成功经验"""
        em = EpisodicMemory()
        ep = em.add_success(
            phase="reason",
            input_summary="输入A",
            output_summary="输出B",
            confidence=0.9,
        )
        assert ep.outcome == OutcomeType.SUCCESS
        assert len(em) == 1

    def test_add_failure(self):
        """记录失败经验"""
        em = EpisodicMemory()
        ep = em.add_failure(
            phase="reason",
            input_summary="输入A",
            output_summary="输出B",
            error="推理失败",
            failure_type="inference_error",
        )
        assert ep.outcome == OutcomeType.FAILURE
        assert ep.failure_type == "inference_error"

    def test_get_recent(self):
        """获取最近经验"""
        em = EpisodicMemory()
        for i in range(5):
            em.add_success(f"phase_{i}", f"input_{i}", f"output_{i}")

        recent = em.get_recent(n=3)
        assert len(recent) == 3

    def test_get_failures(self):
        """获取失败经验"""
        em = EpisodicMemory()
        em.add_success("phase_a", "in_a", "out_a")
        em.add_failure("phase_b", "in_b", "out_b", error="err", failure_type="inference_error")
        em.add_failure("phase_c", "in_c", "out_c", error="err", failure_type="drift_detected")

        failures = em.get_failures()
        assert len(failures) == 2

    def test_failure_sampling(self):
        """失败案例优先采样"""
        em = EpisodicMemory()
        em.add_failure("reason", "in1", "out1", error="e1", failure_type="inference_error")
        em.add_failure("reason", "in2", "out2", error="e2", failure_type="inference_error")
        em.add_failure("reason", "in3", "out3", error="e3", failure_type="inference_error")

        sampled = em.failure_sampling(n=2)
        assert len(sampled) == 2
        assert all(ep.outcome != OutcomeType.SUCCESS for ep in sampled)

    def test_get_stats(self):
        """统计信息"""
        em = EpisodicMemory()
        em.add_success("reason", "in1", "out1")
        em.add_success("reason", "in2", "out2")
        em.add_failure("reason", "in3", "out3", error="e", failure_type="inference_error")

        stats = em.get_stats()
        assert stats["total"] == 3
        assert stats["successes"] == 2
        assert stats["failures"] == 1
        assert abs(stats["success_rate"] - 2/3) < 0.01

    def test_clear(self):
        """清空记忆"""
        em = EpisodicMemory()
        em.add_success("p", "i", "o")
        assert len(em) == 1
        em.clear()
        assert len(em) == 0

    def test_episode_age(self):
        """经验年龄"""
        em = EpisodicMemory()
        ep = em.add_success("p", "i", "o")
        assert ep.age_seconds >= 0
        assert ep.is_recent is True

    def test_input_truncation(self):
        """输入截断到 200 字符"""
        em = EpisodicMemory()
        long_input = "x" * 300
        ep = em.add_success("p", long_input, "o")
        assert len(ep.input_summary) == 200

    def test_failure_type_filter(self):
        """按 failure_type 筛选"""
        em = EpisodicMemory()
        em.add_failure("reason", "i1", "o1", error="e", failure_type="inference_error")
        em.add_failure("reason", "i2", "o2", error="e", failure_type="inference_error")
        em.add_failure("reason", "i3", "o3", error="e", failure_type="drift_detected")

        inference_errors = em.get_failures(phase="reason")
        assert len(inference_errors) == 3
