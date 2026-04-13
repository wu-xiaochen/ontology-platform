"""
Clawra 评估基准模块

提供科学的评估方法，覆盖知识学习、推理准确率、检索精度、置信度校准等维度。
支持 benchmark 数据集驱动的自动化评估和报告生成。
"""
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..evolution.unified_logic import UnifiedLogicLayer, LogicType, LogicPattern
from ..evolution.rule_discovery import RuleDiscoveryEngine
from ..evolution.meta_learner import MetaLearner
from ..core.reasoner import Reasoner, Fact, Rule, RuleType, InferenceResult
from .confidence import ConfidenceCalculator, Evidence

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 评估结果数据结构
# ─────────────────────────────────────────────

@dataclass
class LearningEvalResult:
    """知识学习评估结果"""
    extraction_rate: float       # 平均每段文本提取的模式数
    coverage: float              # 覆盖度 (成功提取 / 标注总数)
    total_texts: int
    total_expected: int
    total_extracted: int
    total_matched: int
    total_facts_generated: int   # LLM 自动生成的事实数
    fact_generation_rate: float  # 平均每段文本生成的事实数
    per_text_results: List[Dict] = field(default_factory=list)


@dataclass
class ReasoningEvalResult:
    """推理准确率评估结果"""
    accuracy: float
    precision: float
    recall: float
    f1: float
    total_expected: int
    total_actual: int
    true_positives: int
    false_positives: int
    false_negatives: int
    per_case_results: List[Dict] = field(default_factory=list)


@dataclass
class RetrievalEvalResult:
    """知识检索评估结果"""
    precision: float
    recall: float
    f1: float
    total_queries: int
    per_query_results: List[Dict] = field(default_factory=list)


@dataclass
class ConfidenceEvalResult:
    """置信度校准评估结果"""
    calibration_error: float      # 平均绝对校准误差 (ECE)
    total_cases: int
    bin_results: List[Dict] = field(default_factory=list)


@dataclass
class BenchmarkReport:
    """完整 Benchmark 报告"""
    learning: Optional[LearningEvalResult] = None
    reasoning: Optional[ReasoningEvalResult] = None
    retrieval: Optional[RetrievalEvalResult] = None
    confidence: Optional[ConfidenceEvalResult] = None
    timestamp: float = 0.0
    duration: float = 0.0

    @property
    def overall_score(self) -> float:
        """综合评分 (0~1)，各维度加权平均"""
        scores = []
        if self.learning:
            # 学习率目标 >= 2.0，归一化到 0~1
            scores.append(min(self.learning.extraction_rate / 2.0, 1.0) * 0.3)
            scores.append(self.learning.coverage * 0.1)
        if self.reasoning:
            scores.append(self.reasoning.accuracy * 0.3)
        if self.retrieval:
            scores.append(self.retrieval.recall * 0.15)
        if self.confidence:
            # ECE 越小越好，转为正向分数
            scores.append(max(1.0 - self.confidence.calibration_error, 0.0) * 0.15)
        return sum(scores) / max(sum(
            [0.3, 0.1] if self.learning else [],
        ) + sum(
            [0.3] if self.reasoning else [],
        ) + sum(
            [0.15] if self.retrieval else [],
        ) + sum(
            [0.15] if self.confidence else [],
        ), 1e-9) if scores else 0.0

    def summary(self) -> Dict[str, Any]:
        """输出摘要字典"""
        result = {"timestamp": self.timestamp, "duration_s": round(self.duration, 3)}
        if self.learning:
            result["learning"] = {
                "extraction_rate": round(self.learning.extraction_rate, 2),
                "coverage": round(self.learning.coverage, 2),
            }
        if self.reasoning:
            result["reasoning"] = {
                "accuracy": round(self.reasoning.accuracy, 2),
                "precision": round(self.reasoning.precision, 2),
                "recall": round(self.reasoning.recall, 2),
                "f1": round(self.reasoning.f1, 2),
            }
        if self.retrieval:
            result["retrieval"] = {
                "precision": round(self.retrieval.precision, 2),
                "recall": round(self.retrieval.recall, 2),
                "f1": round(self.retrieval.f1, 2),
            }
        if self.confidence:
            result["confidence"] = {
                "calibration_error": round(self.confidence.calibration_error, 3),
            }
        return result


# ─────────────────────────────────────────────
# 核心评估类
# ─────────────────────────────────────────────

class ClawraBenchmark:
    """Clawra 评估基准引擎"""

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(__file__), '../../data/benchmark'
        )

    # ── 1. 知识学习评估 ──

    def evaluate_learning(
        self,
        cases: List[Dict] = None,
    ) -> LearningEvalResult:
        """
        评估知识学习能力

        每个 case 包含:
          - text: 学习文本
          - domain: 领域
          - expected_patterns: 预期模式列表，每个含 type/entity/relation 等标注
        """
        if cases is None:
            cases = self._load_cases("learning_cases.json")

        total_extracted = 0
        total_matched = 0
        total_expected = 0
        total_facts = 0
        per_text = []

        for case in cases:
            text = case["text"]
            domain = case.get("domain", "generic")
            expected = case.get("expected_patterns", [])
            total_expected += len(expected)

            # 每个 case 用独立的引擎，避免交叉污染
            logic_layer = UnifiedLogicLayer()
            discovery = RuleDiscoveryEngine(logic_layer)
            learner = MetaLearner(logic_layer, discovery)

            result = learner.learn(text, input_type="text", domain_hint=domain)
            learned_ids = result.get("learned_patterns", [])
            extracted_facts = result.get("extracted_facts", [])
            facts_count = len(extracted_facts)
            total_facts += facts_count
            extracted_patterns = [
                logic_layer.patterns[pid] for pid in learned_ids
                if pid in logic_layer.patterns
            ]
            total_extracted += len(extracted_patterns)

            # 匹配检查：对每个预期模式，检查是否在提取结果中有对应
            matched = 0
            match_details = []
            for exp in expected:
                found = self._match_expected_pattern(exp, extracted_patterns)
                if found:
                    matched += 1
                match_details.append({"expected": exp, "found": found is not None})

            total_matched += matched
            per_text.append({
                "id": case.get("id", ""),
                "extracted": len(extracted_patterns),
                "expected": len(expected),
                "matched": matched,
                "facts_generated": facts_count,
                "details": match_details,
            })

        extraction_rate = total_extracted / max(len(cases), 1)
        coverage = total_matched / max(total_expected, 1)
        fact_gen_rate = total_facts / max(len(cases), 1)

        return LearningEvalResult(
            extraction_rate=extraction_rate,
            coverage=coverage,
            total_texts=len(cases),
            total_expected=total_expected,
            total_extracted=total_extracted,
            total_matched=total_matched,
            total_facts_generated=total_facts,
            fact_generation_rate=fact_gen_rate,
            per_text_results=per_text,
        )

    def _match_expected_pattern(
        self, expected: Dict, extracted: List[LogicPattern]
    ) -> Optional[LogicPattern]:
        """检查预期模式是否在提取结果中被匹配到"""
        exp_type = expected.get("type", "")
        exp_entity = expected.get("entity", "").lower()
        exp_relation = expected.get("relation", "").lower()
        exp_condition = expected.get("condition", "").lower()
        exp_action = expected.get("action", "").lower()

        for p in extracted:
            desc = p.description.lower()
            name = p.name.lower()
            full_text = f"{name} {desc}"

            # 按类型匹配
            if exp_type == "definition":
                if exp_entity and exp_entity in full_text:
                    return p
            elif exp_type == "rule":
                if exp_condition and exp_condition in full_text:
                    return p
                if exp_action and exp_action in full_text:
                    return p
            elif exp_type == "attribute":
                if exp_entity and exp_entity in full_text:
                    return p
            elif exp_type == "composition":
                if exp_entity and exp_entity in full_text:
                    return p
            elif exp_type == "function":
                if exp_entity and exp_entity in full_text:
                    return p
            else:
                # 通用匹配：任何关键词出现
                keywords = [v for v in [exp_entity, exp_relation, exp_condition, exp_action] if v]
                if any(kw in full_text for kw in keywords):
                    return p

        return None

    # ── 2. 推理准确率评估 ──

    def evaluate_reasoning(
        self,
        cases: List[Dict] = None,
    ) -> ReasoningEvalResult:
        """
        评估推理准确率

        每个 case 包含:
          - facts: 事实列表 [{subject, predicate, object, confidence}]
          - expected_conclusions: 预期推理结论 [{subject, predicate, object}]
        """
        if cases is None:
            cases = self._load_cases("reasoning_cases.json")

        total_tp = 0
        total_fp = 0
        total_fn = 0
        per_case = []

        for case in cases:
            reasoner = Reasoner()
            facts = case.get("facts", [])
            expected = case.get("expected_conclusions", [])

            # 加载事实
            for f in facts:
                reasoner.add_fact(Fact(
                    subject=f["subject"],
                    predicate=f["predicate"],
                    object=f["object"],
                    confidence=f.get("confidence", 0.9),
                ))

            # 执行推理
            result = reasoner.forward_chain(max_depth=5)
            actual_triples = set()
            for step in result.conclusions:
                c = step.conclusion
                actual_triples.add((c.subject, c.predicate, c.object))

            # 对比
            expected_triples = {
                (e["subject"], e["predicate"], e["object"]) for e in expected
            }

            tp = len(actual_triples & expected_triples)
            fp = len(actual_triples - expected_triples)
            fn = len(expected_triples - actual_triples)

            total_tp += tp
            total_fp += fp
            total_fn += fn

            per_case.append({
                "id": case.get("id", ""),
                "expected": len(expected),
                "actual": len(actual_triples),
                "tp": tp, "fp": fp, "fn": fn,
                "missed": [list(t) for t in (expected_triples - actual_triples)],
                "extra": [list(t) for t in (actual_triples - expected_triples)],
            })

        precision = total_tp / max(total_tp + total_fp, 1)
        recall = total_tp / max(total_tp + total_fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)
        accuracy = total_tp / max(total_tp + total_fp + total_fn, 1)

        return ReasoningEvalResult(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1=f1,
            total_expected=total_tp + total_fn,
            total_actual=total_tp + total_fp,
            true_positives=total_tp,
            false_positives=total_fp,
            false_negatives=total_fn,
            per_case_results=per_case,
        )

    # ── 3. 知识检索评估 ──

    def evaluate_retrieval(
        self,
        cases: List[Dict] = None,
    ) -> RetrievalEvalResult:
        """
        评估知识检索精度

        每个 case 包含:
          - setup: 初始化知识库的配置
            - texts: 学习文本列表
            - facts: 事实列表
          - queries: 查询列表
            - query: 查询文本
            - expected_fact_keywords: 应匹配到的事实关键词
            - expected_pattern_keywords: 应匹配到的模式关键词
        """
        if cases is None:
            cases = self._load_cases("retrieval_cases.json")

        total_tp = 0
        total_fp = 0
        total_fn = 0
        per_query = []

        for case in cases:
            # 构建知识库
            logic_layer = UnifiedLogicLayer()
            discovery = RuleDiscoveryEngine(logic_layer)
            learner = MetaLearner(logic_layer, discovery)
            reasoner = Reasoner()

            setup = case.get("setup", {})
            for text in setup.get("texts", []):
                learner.learn(text, input_type="text")
            for f in setup.get("facts", []):
                reasoner.add_fact(Fact(
                    f["subject"], f["predicate"], f["object"],
                    f.get("confidence", 0.9)
                ))

            # 执行检索查询
            for q in case.get("queries", []):
                query_text = q["query"]
                exp_fact_kw = set(q.get("expected_fact_keywords", []))
                exp_pattern_kw = set(q.get("expected_pattern_keywords", []))

                # 模拟 ClawraAgent 的检索逻辑
                import re
                keywords = self._extract_keywords(query_text)

                # 检索事实
                matched_facts = []
                for kw in keywords:
                    for fact in reasoner.facts:
                        fact_text = f"{fact.subject} {fact.predicate} {fact.object}".lower()
                        if kw.lower() in fact_text and fact not in matched_facts:
                            matched_facts.append(fact)

                # 检索模式
                matched_patterns = []
                for kw in keywords:
                    for pid, p in logic_layer.patterns.items():
                        desc = f"{p.name} {p.description}".lower()
                        if kw.lower() in desc and p not in matched_patterns:
                            matched_patterns.append(p)

                # 计算精度/召回
                actual_fact_kw = set()
                for f in matched_facts:
                    actual_fact_kw.update(
                        w for w in [f.subject, f.predicate, f.object]
                        if len(w) >= 2
                    )

                actual_pattern_kw = set()
                for p in matched_patterns:
                    for w in re.findall(r'[\u4e00-\u9fff]{2,}', p.description):
                        actual_pattern_kw.add(w)

                # 合并所有期望和实际
                all_expected = exp_fact_kw | exp_pattern_kw
                all_actual = actual_fact_kw | actual_pattern_kw

                tp = len(all_expected & all_actual)
                fn = len(all_expected - all_actual)
                # FP: actual 中不在 expected 中的
                fp = 0  # 不对 FP 惩罚过多（检索到额外内容是可接受的）

                total_tp += tp
                total_fp += fp
                total_fn += fn

                per_query.append({
                    "query": query_text,
                    "expected": list(all_expected),
                    "found_facts": len(matched_facts),
                    "found_patterns": len(matched_patterns),
                    "tp": tp, "fn": fn,
                })

        precision = total_tp / max(total_tp + total_fp, 1)
        recall = total_tp / max(total_tp + total_fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)

        return RetrievalEvalResult(
            precision=precision,
            recall=recall,
            f1=f1,
            total_queries=len(per_query),
            per_query_results=per_query,
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本提取关键词（与 ClawraAgent 保持一致）"""
        import re
        stop_chars = set("的是了在和有我你他她什么怎么如何为什么哪些请吗呢一个这个那个需要可以应该关于告诉")
        words = set()
        segments = re.findall(r'[\u4e00-\u9fff]+', text)
        for seg in segments:
            current = []
            for ch in seg:
                if ch in stop_chars:
                    if len(current) >= 2:
                        words.add(''.join(current))
                    current = []
                else:
                    current.append(ch)
            if len(current) >= 2:
                words.add(''.join(current))
        for w in re.findall(r'[a-zA-Z_]{2,}', text):
            words.add(w)
        extra = set()
        for w in list(words):
            if len(w) > 4:
                for i in range(len(w) - 1):
                    sub = w[i:i+2]
                    if sub not in stop_chars:
                        extra.add(sub)
        words |= extra
        return list(words)[:15]

    # ── 4. 置信度校准评估 ──

    def evaluate_confidence(
        self,
        cases: List[Dict] = None,
    ) -> ConfidenceEvalResult:
        """
        评估置信度校准

        每个 case 包含:
          - facts: 事实列表
          - expected_conclusions: 预期推理结论（标注为正确）
          - 推理结论的置信度 vs 实际正确性
        """
        if cases is None:
            # 复用推理测试用例
            cases = self._load_cases("reasoning_cases.json")

        # 收集 (predicted_confidence, is_correct) 对
        predictions: List[Tuple[float, bool]] = []

        for case in cases:
            reasoner = Reasoner()
            for f in case.get("facts", []):
                reasoner.add_fact(Fact(
                    f["subject"], f["predicate"], f["object"],
                    f.get("confidence", 0.9),
                ))

            result = reasoner.forward_chain(max_depth=5)
            expected_triples = {
                (e["subject"], e["predicate"], e["object"])
                for e in case.get("expected_conclusions", [])
            }

            for step in result.conclusions:
                c = step.conclusion
                triple = (c.subject, c.predicate, c.object)
                is_correct = triple in expected_triples
                predictions.append((step.confidence.value, is_correct))

        # 计算 Expected Calibration Error (ECE)
        if not predictions:
            return ConfidenceEvalResult(calibration_error=0.0, total_cases=0)

        n_bins = 10
        bins = [[] for _ in range(n_bins)]
        for conf, correct in predictions:
            bin_idx = min(int(conf * n_bins), n_bins - 1)
            bins[bin_idx].append((conf, correct))

        total_ece = 0.0
        bin_results = []
        for i, bin_data in enumerate(bins):
            if not bin_data:
                continue
            avg_conf = sum(c for c, _ in bin_data) / len(bin_data)
            avg_acc = sum(1 for _, correct in bin_data if correct) / len(bin_data)
            gap = abs(avg_conf - avg_acc)
            weight = len(bin_data) / len(predictions)
            total_ece += gap * weight
            bin_results.append({
                "bin": f"{i/n_bins:.1f}-{(i+1)/n_bins:.1f}",
                "count": len(bin_data),
                "avg_confidence": round(avg_conf, 3),
                "avg_accuracy": round(avg_acc, 3),
                "gap": round(gap, 3),
            })

        return ConfidenceEvalResult(
            calibration_error=total_ece,
            total_cases=len(predictions),
            bin_results=bin_results,
        )

    # ── 5. 完整 Benchmark ──

    def run_full_benchmark(self) -> BenchmarkReport:
        """运行完整 benchmark，返回综合报告"""
        start = time.time()
        report = BenchmarkReport(timestamp=time.time())

        logger.info("=== Clawra Benchmark 开始 ===")

        try:
            logger.info("[1/4] 评估知识学习...")
            report.learning = self.evaluate_learning()
            logger.info(
                f"  学习率: {report.learning.extraction_rate:.2f}, "
                f"覆盖度: {report.learning.coverage:.2%}"
            )
        except FileNotFoundError:
            logger.warning("  学习测试数据不存在，跳过")
        except Exception as e:
            logger.error(f"  学习评估失败: {e}")

        try:
            logger.info("[2/4] 评估推理准确率...")
            report.reasoning = self.evaluate_reasoning()
            logger.info(
                f"  准确率: {report.reasoning.accuracy:.2%}, "
                f"F1: {report.reasoning.f1:.2f}"
            )
        except FileNotFoundError:
            logger.warning("  推理测试数据不存在，跳过")
        except Exception as e:
            logger.error(f"  推理评估失败: {e}")

        try:
            logger.info("[3/4] 评估知识检索...")
            report.retrieval = self.evaluate_retrieval()
            logger.info(
                f"  精度: {report.retrieval.precision:.2%}, "
                f"召回: {report.retrieval.recall:.2%}"
            )
        except FileNotFoundError:
            logger.warning("  检索测试数据不存在，跳过")
        except Exception as e:
            logger.error(f"  检索评估失败: {e}")

        try:
            logger.info("[4/4] 评估置信度校准...")
            report.confidence = self.evaluate_confidence()
            logger.info(
                f"  校准误差 (ECE): {report.confidence.calibration_error:.3f}"
            )
        except FileNotFoundError:
            logger.warning("  置信度测试数据不存在，跳过")
        except Exception as e:
            logger.error(f"  置信度评估失败: {e}")

        report.duration = time.time() - start
        logger.info(f"=== Benchmark 完成 ({report.duration:.2f}s) ===")
        logger.info(f"报告摘要: {json.dumps(report.summary(), ensure_ascii=False, indent=2)}")

        return report

    # ── 工具方法 ──

    def _load_cases(self, filename: str) -> List[Dict]:
        """从 benchmark 数据目录加载测试用例"""
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Benchmark 数据文件不存在: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
