"""
Clawra Benchmark 测试

自动化运行评估基准并断言各指标达标。
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.eval.benchmark import ClawraBenchmark


@pytest.fixture(scope="module")
def benchmark():
    """创建 benchmark 实例"""
    data_dir = os.path.join(os.path.dirname(__file__), '../data/benchmark')
    return ClawraBenchmark(data_dir=data_dir)


class TestLearningEvaluation:
    """知识学习评估测试"""

    def test_learning_rate(self, benchmark):
        """学习率 >= 2.0（平均每段文本提取 >= 2 个模式）"""
        result = benchmark.evaluate_learning()
        assert result.extraction_rate >= 2.0, (
            f"学习率 {result.extraction_rate:.2f} < 2.0, "
            f"共 {result.total_texts} 段文本, 提取 {result.total_extracted} 个模式"
        )

    def test_knowledge_coverage(self, benchmark):
        """覆盖度 >= 60%"""
        result = benchmark.evaluate_learning()
        assert result.coverage >= 0.60, (
            f"覆盖度 {result.coverage:.2%} < 60%, "
            f"标注 {result.total_expected} 个, 匹配 {result.total_matched} 个"
        )

    def test_per_text_extraction(self, benchmark):
        """每段文本至少提取 1 个模式"""
        result = benchmark.evaluate_learning()
        for text_result in result.per_text_results:
            assert text_result["extracted"] >= 1, (
                f"文本 {text_result['id']} 未提取到任何模式"
            )


class TestReasoningEvaluation:
    """推理准确率评估测试"""

    def test_reasoning_accuracy(self, benchmark):
        """推理准确率 >= 85%"""
        result = benchmark.evaluate_reasoning()
        assert result.accuracy >= 0.85, (
            f"推理准确率 {result.accuracy:.2%} < 85%, "
            f"TP={result.true_positives}, FP={result.false_positives}, FN={result.false_negatives}"
        )

    def test_reasoning_recall(self, benchmark):
        """推理召回率 >= 80%"""
        result = benchmark.evaluate_reasoning()
        assert result.recall >= 0.80, (
            f"推理召回率 {result.recall:.2%} < 80%, "
            f"预期 {result.total_expected} 个结论, 命中 {result.true_positives} 个"
        )

    def test_no_missed_transitive(self, benchmark):
        """传递性推理不应遗漏（RC01, RC02 必须命中）"""
        result = benchmark.evaluate_reasoning()
        for case in result.per_case_results:
            if case["id"] in ("RC01", "RC02"):
                assert case["fn"] == 0, (
                    f"基础传递推理 {case['id']} 遗漏: {case['missed']}"
                )


class TestRetrievalEvaluation:
    """知识检索评估测试"""

    def test_retrieval_precision(self, benchmark):
        """检索精度 >= 70%"""
        result = benchmark.evaluate_retrieval()
        assert result.precision >= 0.70, (
            f"检索精度 {result.precision:.2%} < 70%"
        )

    def test_retrieval_recall(self, benchmark):
        """检索召回率 >= 50%"""
        result = benchmark.evaluate_retrieval()
        assert result.recall >= 0.50, (
            f"检索召回率 {result.recall:.2%} < 50%"
        )


class TestConfidenceCalibration:
    """置信度校准评估测试"""

    def test_confidence_calibration(self, benchmark):
        """校准误差 <= 0.15"""
        result = benchmark.evaluate_confidence()
        assert result.calibration_error <= 0.15, (
            f"置信度校准误差 {result.calibration_error:.3f} > 0.15"
        )


class TestFullBenchmark:
    """完整 Benchmark 测试"""

    def test_full_benchmark_runs(self, benchmark):
        """完整 benchmark 应能无错运行"""
        report = benchmark.run_full_benchmark()
        assert report.learning is not None
        assert report.reasoning is not None
        assert report.retrieval is not None
        assert report.confidence is not None
        assert report.duration > 0

    def test_benchmark_summary(self, benchmark):
        """benchmark 摘要应包含所有维度"""
        report = benchmark.run_full_benchmark()
        summary = report.summary()
        assert "learning" in summary
        assert "reasoning" in summary
        assert "retrieval" in summary
        assert "confidence" in summary
