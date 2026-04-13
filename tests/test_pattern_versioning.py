"""
Tests for pattern_versioning module
"""
import pytest
from src.evolution.pattern_versioning import (
    PatternVersion,
    PatternHistory,
    PatternBranching,
    PatternRollback,
    SimilarityDeduplication,
    merge_similar_patterns,
    compare_versions,
    ChangeType,
)


class TestPatternHistory:
    """PatternHistory 测试"""

    def test_add_version(self):
        """添加版本"""
        history = PatternHistory(pattern_id="p1")
        pv = history.add_version(
            version="1.0.0",
            content={"id": "p1", "name": "test", "logic_type": "rule"},
            source="manual",
            confidence=0.9,
        )
        assert pv.version == "1.0.0"
        assert history.current_version == "1.0.0"
        assert history.get_version("1.0.0") is not None

    def test_add_multiple_versions(self):
        """添加多个版本"""
        history = PatternHistory(pattern_id="p1")
        history.add_version("1.0.0", {"id": "p1", "name": "v1"}, confidence=0.8)
        history.add_version("1.1.0", {"id": "p1", "name": "v2"}, confidence=0.85)
        history.add_version("2.0.0", {"id": "p1", "name": "v3"}, confidence=0.9)

        assert len(history.versions) == 3
        assert history.current_version == "2.0.0"
        assert len(history.get_history()) == 3

    def test_rollback_candidates(self):
        """可回滚版本列表"""
        history = PatternHistory(pattern_id="p1")
        history.add_version("1.0.0", {"id": "p1"}, confidence=0.8)
        history.add_version("1.1.0", {"id": "p1"}, confidence=0.7)

        candidates = history.rollback_candidates()
        assert len(candidates) == 1
        assert candidates[0].version == "1.0.0"

    def test_get_latest_stable(self):
        """获取最新稳定版本"""
        history = PatternHistory(pattern_id="p1")
        history.add_version("1.0.0", {"id": "p1"}, confidence=0.8)
        history.add_version("1.1.0", {"id": "p1"}, confidence=0.6, change_type=ChangeType.DEPRECATED)
        history.add_version("1.2.0", {"id": "p1"}, confidence=0.9)

        stable = history.get_latest_stable()
        assert stable.version == "1.2.0"


class TestPatternBranching:
    """PatternBranching 测试"""

    def test_create_branch(self):
        """创建分支"""
        pb = PatternBranching(base_pattern_id="p1")
        pb.create_branch("exp_a", "p1_exp", {"name": "experiment"})
        assert "exp_a" in pb.branches
        assert pb.branches["exp_a"]["active"] is True

    def test_record_metric(self):
        """记录指标"""
        pb = PatternBranching(base_pattern_id="p1")
        pb.create_branch("exp_a", "p1_exp", {"name": "experiment"})
        pb.record_metric("exp_a", "accuracy", 0.95)
        assert pb.branches["exp_a"]["metric"]["accuracy"] == 0.95

    def test_get_best_branch(self):
        """获取最优分支"""
        pb = PatternBranching(base_pattern_id="p1")
        pb.create_branch("exp_a", "p1_a", {"name": "a"})
        pb.create_branch("exp_b", "p1_b", {"name": "b"})
        pb.record_metric("exp_a", "accuracy", 0.85)
        pb.record_metric("exp_b", "accuracy", 0.92)

        best = pb.get_best_branch("accuracy")
        assert best == "exp_b"


class TestPatternRollback:
    """PatternRollback 测试"""

    def test_validate_version_ok(self):
        """验证有效版本"""
        history = PatternHistory(pattern_id="p1")
        history.add_version("1.0.0", {"id": "p1", "name": "v1", "logic_type": "rule"})
        history.add_version("1.1.0", {"id": "p1", "name": "v2", "logic_type": "rule"})

        rollback = PatternRollback(history)
        valid, reason = rollback.validate_version("1.0.0")
        assert valid is True

    def test_validate_version_missing(self):
        """验证不存在的版本"""
        history = PatternHistory(pattern_id="p1")
        rollback = PatternRollback(history)
        valid, reason = rollback.validate_version("99.0.0")
        assert valid is False
        assert "不存在" in reason

    def test_validate_version_deprecated(self):
        """验证废弃版本不可回滚"""
        history = PatternHistory(pattern_id="p1")
        history.add_version("1.0.0", {"id": "p1", "name": "v1", "logic_type": "rule"})
        history.add_version(
            "1.1.0", {"id": "p1", "name": "v2", "logic_type": "rule"},
            change_type=ChangeType.DEPRECATED
        )

        rollback = PatternRollback(history)
        valid, reason = rollback.validate_version("1.1.0")
        assert valid is False
        assert "废弃" in reason

    def test_rollback_execute(self):
        """执行回滚"""
        history = PatternHistory(pattern_id="p1")
        history.add_version("1.0.0", {"id": "p1", "name": "v1", "logic_type": "rule"}, confidence=0.9)
        history.add_version("1.1.0", {"id": "p1", "name": "v2", "logic_type": "rule"}, confidence=0.6)

        rollback = PatternRollback(history)
        ok, msg, pv = rollback.rollback_to("1.0.0")

        assert ok is True
        assert "成功" in msg
        assert pv.version == "1.0.0"
        assert history.current_version.startswith("1.0.0-rollback-")


class TestSimilarityDeduplication:
    """SimilarityDeduplication 测试"""

    def test_jaccard_basic(self):
        """Jaccard 基础相似度"""
        dedup = SimilarityDeduplication(similarity_threshold=0.85, use_semantic=False)

        p1 = {"id": "p1", "name": "燃气调压", "conditions": [{"x": 1}], "actions": [{"y": 2}]}
        p2 = {"id": "p2", "name": "燃气调压", "conditions": [{"x": 1}], "actions": [{"y": 2}]}
        p3 = {"id": "p3", "name": "电力开关", "conditions": [{"z": 3}], "actions": [{"w": 4}]}

        sim_same = dedup.compute_similarity(p1, p2)
        sim_diff = dedup.compute_similarity(p1, p3)

        # id 不同，Jaccard < 1.0；但同一类 > 不同类
        assert sim_same > sim_diff
        assert sim_same >= 0.5  # 有共同字段
        assert sim_diff == 0.0  # 完全不同

    def test_deduplicate(self):
        """去重"""
        patterns = [
            {"id": "p1", "name": "规则A", "confidence": 0.9, "conditions": [{"x": 1}], "logic_type": "rule"},
            {"id": "p2", "name": "规则A", "confidence": 0.85, "conditions": [{"x": 1}], "logic_type": "rule"},
            {"id": "p3", "name": "规则B", "confidence": 0.8, "conditions": [{"z": 3}], "logic_type": "rule"},
        ]

        # Jaccard p1 vs p2 约 0.6，需要较低阈值才能合并
        dedup = SimilarityDeduplication(similarity_threshold=0.5, use_semantic=False)
        result = dedup.deduplicate(patterns)

        # p1/p2 结构相同应合并，p3 独立
        assert len(result) == 2
        ids = [p["id"] for p in result]
        assert "p3" in ids
        assert ("p1" in ids or "p2" in ids)

    def test_merge_similar_patterns(self):
        """合并相似 pattern"""
        patterns = [
            {"id": "p1", "name": "调压", "confidence": 0.9, "conditions": [{"x": 1}], "logic_type": "rule", "metadata": {}},
            {"id": "p2", "name": "调压", "confidence": 0.7, "conditions": [{"x": 1}], "logic_type": "rule", "metadata": {}},
        ]

        dedup = SimilarityDeduplication(similarity_threshold=0.5, use_semantic=False)
        merged, pairs = dedup.merge_similar_patterns(patterns)

        assert len(merged) == 1
        assert merged[0]["id"] == "p1"  # 保留高置信度的


class TestCompareVersions:
    """compare_versions 测试"""

    def test_compare_versions(self):
        """版本对比"""
        history = PatternHistory(pattern_id="p1")
        history.add_version("1.0.0", {"id": "p1", "name": "v1", "logic_type": "rule"}, confidence=0.8)
        history.add_version("2.0.0", {"id": "p1", "name": "v2", "logic_type": "rule"}, confidence=0.85)

        report = compare_versions(history, "1.0.0", "2.0.0")
        assert "confidence_change" in report
        assert abs(report["confidence_change"] - 0.05) < 0.001
        assert len(report["diff_fields"]) >= 1


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_merge_similar_patterns_function(self):
        """便捷合并函数"""
        patterns = [
            {"id": "p1", "name": "A", "confidence": 0.9, "conditions": [{"x": 1}], "logic_type": "rule", "metadata": {}},
            {"id": "p2", "name": "A", "confidence": 0.7, "conditions": [{"x": 1}], "logic_type": "rule", "metadata": {}},
            {"id": "p3", "name": "B", "confidence": 0.8, "conditions": [{"z": 2}], "logic_type": "rule", "metadata": {}},
        ]

        # 使用 0.5 阈值，因为 Jaccard(p1, p2) ≈ 0.6
        result = merge_similar_patterns(patterns, threshold=0.5)
        assert len(result) == 2
