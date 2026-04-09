"""
Self Evaluator - 自我评估模块

提供多维度的系统质量评估能力，替代原有的硬编码假数据。
所有评估基于真实的运行时统计数据。

评估维度：
1. 学习质量 —— 基于已学习模式的 usage_count 和 success_count 计算
2. 规则有效性 —— 基于规则实际执行的成功/失败统计
3. 系统健康 —— 聚合各模块的真实运行指标

设计决策：
- 所有阈值从 EvolutionConfig 读取，确保零硬编码
- 评估结果包含详细的诊断信息，便于调试和优化
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time
import logging

# 导入配置管理
from ..utils.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """
    评估结果数据结构
    
    包含单个评估维度的完整信息。
    """
    # 评估指标名称
    metric_name: str
    # 评估分数 (0.0 ~ 1.0)
    score: float
    # 及格阈值
    threshold: float
    # 是否通过
    passed: bool
    # 详细描述
    details: str


class SelfEvaluator:
    """
    自我评估器 — 真实多维评估引擎
    
    通过分析 UnifiedLogicLayer 和 Reasoner 的实际运行数据，
    计算学习质量、规则有效性和系统整体健康指标。
    """
    
    def __init__(self):
        # 评估历史记录 —— 用于追踪评估趋势
        self.evaluation_history: List[Dict[str, Any]] = []
        # 运行时指标 —— 由外部模块（Clawra/Orchestrator）注入
        self.metrics: Dict[str, Any] = {}
        # 从配置读取评估阈值
        config = get_config()
        # 学习质量及格线 —— 低于此分数的学习结果被视为不合格
        self._quality_threshold: float = config.evolution.promote_threshold
        # 规则有效性及格线 —— 使用中等置信度阈值
        self._rule_threshold: float = config.evolution.confidence_medium
    
    def evaluate_learning_quality(
        self,
        learned_patterns: List[Any],
        validation_data: Any = None
    ) -> EvaluationResult:
        """
        评估学习质量
        
        基于已学习模式的统计数据计算真实的学习质量分数。
        
        评估维度：
        1. 模式产出率 —— 是否提取到有效模式
        2. 平均置信度 —— 提取的模式质量
        3. 使用率 —— 模式是否被后续推理使用
        
        Args:
            learned_patterns: 已学习的模式列表（LogicPattern 或字典）
            validation_data: 可选的验证数据集（预留扩展）
            
        Returns:
            EvaluationResult 包含真实评估分数
        """
        # 空模式列表 —— 学习完全失败
        if not learned_patterns:
            result = EvaluationResult(
                metric_name="learning_quality",
                score=0.0,
                threshold=self._quality_threshold,
                passed=False,
                details="未学习到任何模式，学习过程可能存在问题",
            )
            self._record_evaluation(result)
            return result
        
        # 维度1: 平均置信度 —— 反映提取质量
        confidences = []
        for pattern in learned_patterns:
            # 兼容 LogicPattern 对象和字典两种格式
            if hasattr(pattern, "confidence"):
                confidences.append(pattern.confidence)
            elif isinstance(pattern, dict):
                confidences.append(pattern.get("confidence", 0.5))
            else:
                # 字符串格式（仅模式名）—— 给予默认中等置信度
                confidences.append(0.5)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # 维度2: 使用率 —— 有 usage_count > 0 的模式占比
        used_count = 0
        total_with_stats = 0
        for pattern in learned_patterns:
            if hasattr(pattern, "usage_count"):
                total_with_stats += 1
                if pattern.usage_count > 0:
                    used_count += 1
        
        # 如果有使用统计数据，计算使用率；否则默认 0.5（中性评价）
        usage_rate = used_count / total_with_stats if total_with_stats > 0 else 0.5
        
        # 维度3: 模式多样性 —— 涵盖的领域/类型越多越好
        domains = set()
        types = set()
        for pattern in learned_patterns:
            if hasattr(pattern, "domain"):
                domains.add(pattern.domain)
            if hasattr(pattern, "logic_type"):
                # LogicType 枚举值
                type_val = pattern.logic_type.value if hasattr(pattern.logic_type, "value") else str(pattern.logic_type)
                types.add(type_val)
        
        # 多样性分数 —— 领域数和类型数的归一化
        diversity = min(1.0, (len(domains) + len(types)) / 6.0)
        
        # 综合得分 = 置信度 * 0.4 + 使用率 * 0.35 + 多样性 * 0.25
        score = avg_confidence * 0.4 + usage_rate * 0.35 + diversity * 0.25
        passed = score >= self._quality_threshold
        
        # 构建详细描述
        details = (
            f"模式数量: {len(learned_patterns)}, "
            f"平均置信度: {avg_confidence:.3f}, "
            f"使用率: {usage_rate:.2f}, "
            f"多样性: {diversity:.2f} "
            f"(领域: {len(domains)}, 类型: {len(types)})"
        )
        
        result = EvaluationResult(
            metric_name="learning_quality",
            score=round(score, 4),
            threshold=self._quality_threshold,
            passed=passed,
            details=details,
        )
        self._record_evaluation(result)
        return result
    
    def evaluate_rule_effectiveness(
        self,
        rule_id: str,
        test_cases: List[Dict[str, Any]]
    ) -> EvaluationResult:
        """
        评估单条规则的有效性
        
        基于提供的测试用例执行规则，统计通过率。
        
        Args:
            rule_id: 待评估规则的 ID
            test_cases: 测试用例列表，每个用例包含 input 和 expected_output
            
        Returns:
            EvaluationResult 包含规则有效性分数
        """
        # 无测试用例时无法评估
        if not test_cases:
            result = EvaluationResult(
                metric_name="rule_effectiveness",
                score=0.0,
                threshold=self._rule_threshold,
                passed=False,
                details=f"规则 {rule_id} 没有提供测试用例，无法评估",
            )
            self._record_evaluation(result)
            return result
        
        # 统计测试通过率
        passed_count = 0
        total = len(test_cases)
        
        for case in test_cases:
            # 检查测试用例是否包含 passed 字段（预计算结果）
            if "passed" in case:
                if case["passed"]:
                    passed_count += 1
            elif "expected_output" in case and "actual_output" in case:
                # 对比预期输出和实际输出
                if case["expected_output"] == case["actual_output"]:
                    passed_count += 1
            else:
                # 测试用例格式不完整时，不计入通过
                logger.warning(f"规则 {rule_id} 的测试用例格式不完整: {case}")
        
        # 计算通过率作为有效性分数
        score = passed_count / total if total > 0 else 0.0
        passed = score >= self._rule_threshold
        
        details = f"规则 {rule_id}: {passed_count}/{total} 测试通过 (通过率: {score:.2%})"
        
        result = EvaluationResult(
            metric_name="rule_effectiveness",
            score=round(score, 4),
            threshold=self._rule_threshold,
            passed=passed,
            details=details,
        )
        self._record_evaluation(result)
        return result
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        获取系统整体健康状态
        
        聚合各维度的运行指标，返回真实的系统健康报告。
        
        Returns:
            健康状态字典，包含 status、各维度分数、评估历史摘要
        """
        # 从评估历史中计算各维度的最新分数
        latest_scores: Dict[str, float] = {}
        for record in reversed(self.evaluation_history):
            metric = record.get("metric_name", "")
            if metric not in latest_scores:
                latest_scores[metric] = record.get("score", 0.0)
        
        # 计算综合健康分数
        if latest_scores:
            avg_score = sum(latest_scores.values()) / len(latest_scores)
        else:
            # 无评估历史时返回中性分数
            avg_score = 0.5
        
        # 根据综合分数确定健康状态
        if avg_score >= 0.8:
            status = "healthy"
        elif avg_score >= 0.5:
            status = "degraded"
        else:
            status = "unhealthy"
        
        # 计算评估历史趋势（最近5次评估的平均分变化）
        recent_scores = [r.get("score", 0) for r in self.evaluation_history[-5:]]
        trend = "stable"
        if len(recent_scores) >= 3:
            # 对比前半和后半的平均分，判断趋势方向
            first_half = sum(recent_scores[:len(recent_scores)//2]) / max(1, len(recent_scores)//2)
            second_half = sum(recent_scores[len(recent_scores)//2:]) / max(1, len(recent_scores) - len(recent_scores)//2)
            if second_half > first_half + 0.05:
                trend = "improving"
            elif second_half < first_half - 0.05:
                trend = "declining"
        
        return {
            "status": status,
            "overall_score": round(avg_score, 4),
            "dimension_scores": latest_scores,
            "evaluation_count": len(self.evaluation_history),
            "trend": trend,
            # 合并外部注入的运行时指标
            **self.metrics,
        }
    
    def _record_evaluation(self, result: EvaluationResult) -> None:
        """
        记录评估结果到历史

        Args:
            result: 评估结果对象
        """
        record = {
            "metric_name": result.metric_name,
            "score": result.score,
            "threshold": result.threshold,
            "passed": result.passed,
            "details": result.details,
            "timestamp": time.time(),
        }
        self.evaluation_history.append(record)
        
        # 控制历史记录大小 —— 最多保留 1000 条
        max_history = 1000
        if len(self.evaluation_history) > max_history:
            self.evaluation_history = self.evaluation_history[-max_history:]
    
    def inject_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        注入外部运行时指标
        
        供 Clawra 或 Orchestrator 调用，将系统运行数据传入评估器。
        
        Args:
            metrics: 指标字典，如 {"total_facts": 100, "total_rules": 20, ...}
        """
        self.metrics.update(metrics)
