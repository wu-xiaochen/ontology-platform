"""
Tests for case_based_reasoner module
"""
import pytest
from src.evolution.case_based_reasoner import (
    CaseBasedReasoner,
    Case,
    CaseBase,
    CaseOutcome,
    MetaStrategy,
    AdaptationResult,
)


class TestCase:
    """Case 数据结构测试"""

    def test_similarity_same(self):
        """完全相同情境"""
        c1 = Case(
            case_id="c1",
            situation={"domain": "燃气", "pressure": "high"},
            solution={"action": "降压"},
            outcome=CaseOutcome.SUCCESS,
            outcome_text="成功",
        )
        sim = c1.similarity_with({"domain": "燃气", "pressure": "high"})
        assert sim == 1.0

    def test_similarity_partial(self):
        """部分相同情境"""
        c1 = Case(
            case_id="c1",
            situation={"domain": "燃气", "pressure": "high", "temp": "normal"},
            solution={"action": "降压"},
            outcome=CaseOutcome.SUCCESS,
            outcome_text="成功",
        )
        sim = c1.similarity_with({"domain": "燃气", "pressure": "high", "temp": "low"})
        assert 0 < sim < 1.0

    def test_similarity_different(self):
        """完全不同情境"""
        c1 = Case(
            case_id="c1",
            situation={"domain": "燃气", "pressure": "high"},
            solution={"action": "降压"},
            outcome=CaseOutcome.SUCCESS,
            outcome_text="成功",
        )
        sim = c1.similarity_with({"domain": "电力", "voltage": "high"})
        assert sim == 0.0

    def test_to_dict(self):
        """序列化"""
        c = Case(
            case_id="c1",
            situation={"domain": "燃气"},
            solution={"action": "降压"},
            outcome=CaseOutcome.SUCCESS,
            outcome_text="成功",
        )
        d = c.to_dict()
        assert d["case_id"] == "c1"
        assert d["outcome"] == "success"


class TestCaseBase:
    """CaseBase 测试"""

    def test_add_and_get(self):
        """添加和获取"""
        cb = CaseBase()
        c = Case(
            case_id="c1",
            situation={"domain": "燃气"},
            solution={"action": "a"},
            outcome=CaseOutcome.SUCCESS,
            outcome_text="ok",
        )
        cb.add(c)
        assert cb.get("c1").case_id == "c1"
        assert cb.size() == 1

    def test_get_by_domain(self):
        """按领域查询"""
        cb = CaseBase()
        cb.add(Case("c1", {"domain": "燃气"}, {"action": "a"}, CaseOutcome.SUCCESS, "ok", domain="燃气"))
        cb.add(Case("c2", {"domain": "电力"}, {"action": "b"}, CaseOutcome.SUCCESS, "ok", domain="电力"))
        cb.add(Case("c3", {"domain": "燃气"}, {"action": "c"}, CaseOutcome.SUCCESS, "ok", domain="燃气"))

        gas_cases = cb.get_by_domain("燃气")
        assert len(gas_cases) == 2

    def test_remove(self):
        """移除"""
        cb = CaseBase()
        cb.add(Case("c1", {"domain": "燃气"}, {"action": "a"}, CaseOutcome.SUCCESS, "ok"))
        assert cb.size() == 1
        cb.remove("c1")
        assert cb.size() == 0

    def test_size(self):
        """容量"""
        cb = CaseBase()
        assert cb.size() == 0


class TestCaseBasedReasoner:
    """CaseBasedReasoner 测试"""

    def test_reason_with_matching_case(self):
        """有匹配案例时推理"""
        cbr = CaseBasedReasoner(min_similarity=0.3)
        cbr.retain(
            situation={"domain": "燃气", "pressure": "high"},
            solution={"action": "降低压力到0.3MPa"},
            outcome=CaseOutcome.SUCCESS,
            outcome_text="压力恢复正常",
            domain="燃气",
        )

        result = cbr.reason(
            situation={"domain": "燃气", "pressure": "very_high"},
            domain="燃气",
        )

        assert result.strategy_used in ("direct", "partial", "meta_hybrid")
        assert result.confidence > 0

    def test_reason_with_no_case_meta_strategy(self):
        """无案例时触发 MetaStrategy"""
        cbr = CaseBasedReasoner(min_similarity=0.3)
        result = cbr.reason(
            situation={"domain": "未知领域", "type": "complex"},
        )
        assert result.strategy_used.startswith("meta_")
        assert "type" in result.adapted_solution

    def test_reason_partial_match(self):
        """部分匹配时做适配"""
        cbr = CaseBasedReasoner(min_similarity=0.3)
        cbr.retain(
            situation={"domain": "燃气", "pressure": "high", "temp": "normal"},
            solution={"action": "降压", "value": "0.3MPa"},
            outcome=CaseOutcome.SUCCESS,
            outcome_text="成功",
        )

        # 温度不同，相似度降低
        result = cbr.reason(
            situation={"domain": "燃气", "pressure": "very_high", "temp": "high"},
        )
        assert "adapted_solution" in result.adapted_solution or "type" in result.adapted_solution

    def test_retain_and_reason(self):
        """存入后再推理"""
        cbr = CaseBasedReasoner(min_similarity=0.3)
        case_id = cbr.retain(
            situation={"field": "A", "value": 10},
            solution={"result": 20},
            outcome=CaseOutcome.SUCCESS,
            outcome_text="ok",
            domain="test",
        )
        assert case_id.startswith("case_")

        result = cbr.reason({"field": "A", "value": 15})
        assert len(result.adaptation_steps) > 0

    def test_evict_low_value(self):
        """容量满时淘汰低价值案例"""
        cbr = CaseBasedReasoner(min_similarity=0.3, max_cases=3)

        for i in range(5):
            cbr.retain(
                situation={"field": f"f{i}"},
                solution={"result": i},
                outcome=CaseOutcome.SUCCESS if i % 2 == 0 else CaseOutcome.FAILURE,
                outcome_text="",
            )

        # 容量限制，应该淘汰了一些
        assert cbr.case_base.size() <= 3

    def test_decompose_strategy(self):
        """DECOMPOSE 元策略"""
        cbr = CaseBasedReasoner(min_similarity=0.1)

        result = cbr.reason(
            situation={
                "context": {"sub_a": 1, "sub_b": 2},
                "extra": {"x": 10},
                "other": 5,
            },
        )

        if result.strategy_used == "meta_decompose":
            sub = result.adapted_solution.get("sub_problems", [])
            assert len(sub) > 0

    def test_meta_strategy_selection(self):
        """元策略选择逻辑"""
        cbr = CaseBasedReasoner(min_similarity=0.3)

        # 无案例、无 epic → DEFER
        result = cbr.reason({"domain": "unknown", "x": 1})
        assert result.strategy_used.startswith("meta_")

    def test_partial_adapt_solution(self):
        """部分适配解决方案"""
        cbr = CaseBasedReasoner(min_similarity=0.3)

        cbr.retain(
            situation={"pressure": 10, "temp": 25},
            solution={"set_pressure": 10, "set_temp": 25},
            outcome=CaseOutcome.SUCCESS,
            outcome_text="ok",
        )

        result = cbr.reason({"pressure": 20, "temp": 30})
        assert result.strategy_used in ("direct", "partial", "meta_hybrid")

    def test_learn_from_episodic(self):
        """从情节记忆导入成功案例"""
        from src.evolution.episodic_memory import EpisodicMemory, OutcomeType

        episodic = EpisodicMemory()
        episodic.add_success(
            phase="reason",
            input_summary="输入A",
            output_summary="输出B",
            domain="燃气",
        )
        episodic.add_failure(
            phase="reason",
            input_summary="输入C",
            output_summary="输出D",
            error="err",
            failure_type="inference_error",
            domain="电力",
        )

        cbr = CaseBasedReasoner(min_similarity=0.3)
        imported = cbr.learn_from_episodic(episodic)

        # 只导入成功的
        assert imported == 1
        gas_cases = cbr.case_base.get_by_domain("燃气")
        assert len(gas_cases) == 1
