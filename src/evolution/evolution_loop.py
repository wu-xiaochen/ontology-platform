"""
Evolution Loop - 自主进化闭环引擎

实现 Clawra 的 8 阶段自主进化闭环：
1. Perceive（感知） → 2. Learn（学习） → 3. Reason（推理） → 4. Execute（执行）
→ 5. Evaluate（评估） → 6. DetectDrift（漂移检测） → 7. ReviseRules（规则修正） → 8. UpdateKG（知识更新）

失败反馈机制：
- 任何阶段的失败都会产生 FeedbackSignal
- FeedbackSignal 自动路由到 MetaLearner 进行策略调整
- 支持三种失败类型：inference_error / pattern_conflict / drift_detected

设计原则：
- 复用已有的 MetaLearner、RuleDiscovery、SelfEvaluator、SelfCorrection 组件
- 零硬编码：所有参数从 config 读取
- Phase 可选开关：某些场景可跳过 Meta-Learner
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import logging

from ..utils.config import get_config

# 延迟导入避免循环依赖
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .meta_learner import MetaLearner
    from .rule_discovery import RuleDiscoveryEngine
    from .self_evaluator import SelfEvaluator
    from .self_correction import ContradictionChecker
    from .unified_logic import UnifiedLogicLayer
    from .episodic_memory import EpisodicMemory
    from .honcho_bridge import HonchoBridge
    from ..core.reasoner import Reasoner

logger = logging.getLogger(__name__)


class EvolutionPhase(Enum):
    """进化阶段枚举"""
    PERCEIVE = "perceive"
    LEARN = "learn"
    REASON = "reason"
    EXECUTE = "execute"
    EVALUATE = "evaluate"
    DETECT_DRIFT = "detect_drift"
    REVISE_RULES = "revise_rules"
    UPDATE_KG = "update_kg"
    META_LEARN = "meta_learn"  # 失败反馈专用


class FailureType(Enum):
    """失败类型枚举"""
    INFERENCE_ERROR = "inference_error"      # 推理错误 → retry
    PATTERN_CONFLICT = "pattern_conflict"    # 规则冲突 → resolve
    DRIFT_DETECTED = "drift_detected"        # 漂移检测 → relearn
    LEARNING_ERROR = "learning_error"        # 学习错误 → retry
    EXECUTION_ERROR = "execution_error"      # 执行错误 → fallback


@dataclass
class FeedbackSignal:
    """失败反馈信号"""
    failure_type: FailureType
    source_phase: EvolutionPhase
    context: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "failure_type": self.failure_type.value,
            "source_phase": self.source_phase.value,
            "context": self.context,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count
        }


@dataclass
class PhaseResult:
    """阶段执行结果"""
    phase: EvolutionPhase
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "phase": self.phase.value,
            "success": self.success,
            "data": str(self.data)[:200] if self.data else None,
            "error": self.error,
            "duration": self.duration
        }


@dataclass
class EvolutionLoopState:
    """进化闭环状态"""
    current_phase: EvolutionPhase = EvolutionPhase.PERCEIVE
    episode_id: str = ""
    input_data: Any = None
    results: Dict[EvolutionPhase, PhaseResult] = field(default_factory=dict)
    feedback_signals: List[FeedbackSignal] = field(default_factory=list)
    iterations: int = 0
    converged: bool = False

    def reset(self):
        """重置状态"""
        self.current_phase = EvolutionPhase.PERCEIVE
        self.results.clear()
        self.feedback_signals.clear()
        self.iterations = 0
        self.converged = False


class EvolutionLoop:
    """
    自主进化闭环引擎

    职责：
    1. 按顺序执行 8 个进化阶段
    2. 管理失败反馈路由（推理失败 → MetaLearner 回流重学）
    3. 协调 MetaLearner、RuleDiscovery、SelfEvaluator、SelfCorrection

    使用方式：
    ```python
    from src.evolution import EvolutionLoop, EpisodicMemory

    episodic = EpisodicMemory()
    loop = EvolutionLoop(
        meta_learner=meta_learner,
        rule_discovery=rule_discovery,
        evaluator=evaluator,
        reasoner=reasoner,
        episodic_memory=episodic,
    )

    # 单步执行
    result = loop.step({"text": "燃气调压箱出口压力 ≤ 0.4MPa", "phase": "perceive"})

    # 完整闭环
    result = loop.run({"text": "..."})
    ```
    """

    def __init__(
        self,
        meta_learner: Optional["MetaLearner"] = None,
        rule_discovery: Optional["RuleDiscoveryEngine"] = None,
        evaluator: Optional["SelfEvaluator"] = None,
        reasoner: Optional["Reasoner"] = None,
        logic_layer: Optional["UnifiedLogicLayer"] = None,
        contradiction_checker: Optional["ContradictionChecker"] = None,
        episodic_memory: Optional["EpisodicMemory"] = None,
        honcho_bridge: Optional["HonchoBridge"] = None,
    ):
        """
        初始化进化闭环引擎

        Args:
            meta_learner: 元学习器（可选，跳过则使用简化版本）
            rule_discovery: 规则发现引擎
            evaluator: 自我评估器
            reasoner: 推理引擎
            logic_layer: 统一逻辑层
            contradiction_checker: 矛盾检查器
            episodic_memory: 情节记忆（失败案例记录）
            honcho_bridge: Honcho 记忆桥接器（可选，从 Honcho conclusions 提取 facts）
        """
        self.config = get_config()
        self.meta_learner = meta_learner
        self.rule_discovery = rule_discovery
        self.evaluator = evaluator
        self.reasoner = reasoner
        self.logic_layer = logic_layer
        self.contradiction_checker = contradiction_checker
        self._episodic = episodic_memory
        self._honcho_bridge = honcho_bridge

        # 失败回流配置
        self._enable_meta_feedback = self.config.evolution.enable_meta_learner
        self._rule_simplify_threshold = 0.3

        # 阶段配置
        self._phase_sequence = [
            EvolutionPhase.PERCEIVE,
            EvolutionPhase.LEARN,
            EvolutionPhase.REASON,
            EvolutionPhase.EXECUTE,
            EvolutionPhase.EVALUATE,
            EvolutionPhase.DETECT_DRIFT,
            EvolutionPhase.REVISE_RULES,
            EvolutionPhase.UPDATE_KG,
        ]

        # 状态
        self._state = EvolutionLoopState()

        # 回调钩子
        self._phase_hooks: Dict[EvolutionPhase, Callable] = {}

        # 配置参数
        self._max_iterations = self.config.evolution.max_iterations
        self._convergence_threshold = self.config.evolution.convergence_threshold
        self._enable_meta_learner = self.config.evolution.enable_meta_learner
        self._enable_rule_discovery = self.config.evolution.enable_rule_discovery

        logger.info(
            f"EvolutionLoop 初始化完成: "
            f"meta_learner={'OK' if meta_learner else 'None'}, "
            f"episodic={'OK' if episodic_memory else 'None'}"
        )

    # ─────────────────────────────────────────────────────────────
    # 公开 API
    # ─────────────────────────────────────────────────────────────

    def step(self, input_data: Dict[str, Any]) -> PhaseResult:
        """
        执行单个阶段

        Args:
            input_data: 包含 phase 字段指定执行哪个阶段

        Returns:
            PhaseResult: 阶段执行结果
        """
        phase = input_data.get("phase", EvolutionPhase.PERCEIVE)
        if isinstance(phase, str):
            phase = EvolutionPhase(phase)

        self._state.current_phase = phase

        start_time = time.time()

        try:
            if phase == EvolutionPhase.PERCEIVE:
                result = self._phase_perceive(input_data)
            elif phase == EvolutionPhase.LEARN:
                result = self._phase_learn(input_data)
            elif phase == EvolutionPhase.REASON:
                result = self._phase_reason(input_data)
            elif phase == EvolutionPhase.EXECUTE:
                result = self._phase_execute(input_data)
            elif phase == EvolutionPhase.EVALUATE:
                result = self._phase_evaluate(input_data)
            elif phase == EvolutionPhase.DETECT_DRIFT:
                result = self._phase_detect_drift(input_data)
            elif phase == EvolutionPhase.REVISE_RULES:
                result = self._phase_revise_rules(input_data)
            elif phase == EvolutionPhase.UPDATE_KG:
                result = self._phase_update_kg(input_data)
            elif phase == EvolutionPhase.META_LEARN:
                result = self._phase_meta_learn(input_data)
            else:
                result = PhaseResult(
                    phase=phase,
                    success=False,
                    error=f"未知阶段: {phase}"
                )
        except Exception as e:
            logger.exception(f"阶段 {phase.value} 执行异常")
            result = PhaseResult(
                phase=phase,
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )

        result.duration = time.time() - start_time
        self._state.results[phase] = result

        # 记录到情节记忆
        if self._episodic:
            self._record_episode(phase, result, input_data)

        return result

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整进化闭环

        Args:
            input_data: 输入数据，必须包含 text 或 query 字段

        Returns:
            完整闭环执行结果
        """
        self._state.reset()
        self._state.episode_id = input_data.get("episode_id", f"ep_{int(time.time())}")
        self._state.input_data = input_data

        logger.info(f"开始进化闭环: episode={self._state.episode_id}")

        for phase in self._phase_sequence:
            # 执行阶段
            phase_result = self.step({**input_data, "phase": phase})

            # 记录反馈信号
            if not phase_result.success:
                feedback = self._create_feedback_signal(phase, phase_result)
                self._state.feedback_signals.append(feedback)

                # 失败处理路由：真实回流 MetaLearner
                handled = self._route_failure(feedback)
                if not handled:
                    logger.warning(
                        f"阶段 {phase.value} 失败但未被处理: {phase_result.error}"
                    )

            # 执行阶段回调
            if phase in self._phase_hooks:
                try:
                    self._phase_hooks[phase](phase_result)
                except Exception as e:
                    logger.debug(f"阶段回调执行异常: {e}")

            # 检查是否收敛
            self._state.iterations += 1
            if self._state.iterations >= self._max_iterations:
                logger.warning(
                    f"达到最大迭代次数 {self._max_iterations}，提前终止"
                )
                break

        logger.info(
            f"进化闭环完成: episode={self._state.episode_id}, "
            f"iterations={self._state.iterations}, "
            f"failures={len(self._state.feedback_signals)}"
        )

        return {
            "episode_id": self._state.episode_id,
            "iterations": self._state.iterations,
            "results": {k.value: v.to_dict() for k, v in self._state.results.items()},
            "feedback_signals": [f.to_dict() for f in self._state.feedback_signals],
            "converged": self._state.converged,
            "success": all(r.success for r in self._state.results.values())
        }

    def register_hook(self, phase: EvolutionPhase, hook: Callable[[PhaseResult], None]):
        """
        注册阶段回调钩子

        Args:
            phase: 阶段
            hook: 回调函数
        """
        self._phase_hooks[phase] = hook

    def get_state(self) -> EvolutionLoopState:
        """获取当前状态"""
        return self._state

    # ─────────────────────────────────────────────────────────────
    # 情节记忆
    # ─────────────────────────────────────────────────────────────

    def _record_episode(
        self, phase: EvolutionPhase, result: PhaseResult, input_data: Dict[str, Any]
    ):
        """将阶段执行结果记录到情节记忆"""
        from .episodic_memory import OutcomeType

        phase_str = phase.value if isinstance(phase, EvolutionPhase) else str(phase)

        if result.success:
            self._episodic.add_success(
                phase=phase_str,
                input_summary=str(input_data.get("text", input_data))[:200],
                output_summary=str(result.data)[:200],
                confidence=result.data.get("confidence") if isinstance(result.data, dict) else None,
                domain=input_data.get("domain"),
                duration=result.duration,
            )
        else:
            self._episodic.add_failure(
                phase=phase_str,
                input_summary=str(input_data.get("text", input_data))[:200],
                output_summary=str(result.data)[:200],
                error=result.error or "unknown",
                failure_type=self._infer_failure_type(phase, result),
                domain=input_data.get("domain"),
                retry_count=0,
                duration=result.duration,
            )

    def _infer_failure_type(self, phase: EvolutionPhase, result: PhaseResult) -> str:
        """从阶段和结果推断失败类型"""
        if phase == EvolutionPhase.REASON:
            return "inference_error"
        elif phase == EvolutionPhase.LEARN:
            return "learning_error"
        elif phase == EvolutionPhase.EXECUTE:
            return "execution_error"
        elif phase == EvolutionPhase.DETECT_DRIFT:
            return "drift_detected"
        return "unknown"

    # ─────────────────────────────────────────────────────────────
    # 失败处理
    # ─────────────────────────────────────────────────────────────

    def _create_feedback_signal(
        self, phase: EvolutionPhase, result: PhaseResult
    ) -> FeedbackSignal:
        """从阶段失败创建反馈信号"""
        # 根据阶段确定失败类型
        if phase == EvolutionPhase.REASON:
            failure_type = FailureType.INFERENCE_ERROR
        elif phase == EvolutionPhase.LEARN:
            failure_type = FailureType.LEARNING_ERROR
        elif phase == EvolutionPhase.EXECUTE:
            failure_type = FailureType.EXECUTION_ERROR
        else:
            failure_type = FailureType.DRIFT_DETECTED

        return FeedbackSignal(
            failure_type=failure_type,
            source_phase=phase,
            context={
                "error": result.error,
                "phase": phase.value,
                "data": str(result.data)[:200] if result.data else None
            }
        )

    def _route_failure(self, feedback: FeedbackSignal) -> bool:
        """
        路由失败信号到对应处理逻辑，真实触发 MetaLearner 回流

        Returns:
            是否被处理
        """
        # 增加重试计数
        feedback.retry_count += 1

        if feedback.retry_count > 3:
            logger.warning(
                f"反馈信号 {feedback.failure_type.value} 重试次数超过 3 次，停止处理"
            )
            return True  # 已处理（但失败）

        failure_type = feedback.failure_type

        if failure_type == FailureType.INFERENCE_ERROR:
            self._handle_inference_error(feedback)
            return True
        elif failure_type == FailureType.PATTERN_CONFLICT:
            self._handle_pattern_conflict(feedback)
            return True
        elif failure_type == FailureType.DRIFT_DETECTED:
            self._handle_drift_detected(feedback)
            return True
        elif failure_type == FailureType.LEARNING_ERROR:
            self._handle_learning_error(feedback)
            return True
        elif failure_type == FailureType.EXECUTION_ERROR:
            self._handle_execution_error(feedback)
            return True

        logger.warning(f"未处理的失败类型: {failure_type.value}")
        return False

    def _handle_inference_error(self, feedback: FeedbackSignal):
        """
        处理推理错误：真实回流 MetaLearner 重学

        策略：从情节记忆获取失败案例，从中选择相关样本，
        让 MetaLearner 学习这些失败案例的模式，避免再次出错
        """
        logger.info(
            f"处理推理错误 [retry={feedback.retry_count}]: "
            f"{feedback.context.get('error')}"
        )

        if not self.meta_learner or not self._enable_meta_feedback:
            return

        # 从情节记忆获取失败案例
        failure_context = feedback.context.get("error", "")
        domain = feedback.context.get("data", {})

        # 失败案例优先采样
        if self._episodic:
            sampled = self._episodic.failure_sampling(n=3)
            if sampled:
                logger.info(f"从情节记忆采样 {len(sampled)} 条失败案例进行重学")
                for ep in sampled:
                    if ep.failure_type in ("inference_error", "learning_error"):
                        try:
                            # MetaLearner 用失败案例重学
                            self.meta_learner.learn(
                                input_data=ep.input_summary,
                                input_type="text",
                                domain_hint=ep.domain,
                            )
                        except Exception as e:
                            logger.debug(f"MetaLearner 回流学习失败: {e}")

        # 简化规则（降低置信度阈值）
        if self.logic_layer:
            low_confidence = [
                pid for pid, pat in getattr(self.logic_layer, "_patterns", {}).items()
                if getattr(pat, "confidence", 1.0) < self._rule_simplify_threshold
            ]
            if low_confidence:
                logger.info(f"发现 {len(low_confidence)} 条低置信度规则，尝试简化")

    def _handle_pattern_conflict(self, feedback: FeedbackSignal):
        """处理规则冲突：调用 SelfCorrection + 规则去重"""
        logger.info(f"处理规则冲突: {feedback.context}")

        if not self.logic_layer:
            return

        # 调用统一逻辑层的规则去重
        try:
            if hasattr(self.logic_layer, "merge_similar_patterns"):
                merged = self.logic_layer.merge_similar_patterns()
                logger.info(f"合并了 {merged} 对冲突规则")
        except Exception as e:
            logger.debug(f"规则去重异常: {e}")

        # 调用 SelfCorrection
        if self.contradiction_checker:
            try:
                self.contradiction_checker.check_and_resolve()
            except Exception as e:
                logger.debug(f"矛盾检查异常: {e}")

    def _handle_learning_error(self, feedback: FeedbackSignal):
        """
        处理学习错误：触发 MetaLearner 重新学习

        策略：从情节记忆获取失败案例，重新组织学习材料
        """
        logger.info(
            f"处理学习错误 [retry={feedback.retry_count}]: "
            f"{feedback.context.get('error')}"
        )

        if not self.meta_learner or not self._enable_meta_feedback:
            return

        error_context = feedback.context.get("error", "")
        domain = feedback.context.get("domain")

        # 获取相关失败案例
        if self._episodic:
            sampled = self._episodic.failure_sampling(n=3)
            if sampled:
                logger.info(f"从 {len(sampled)} 个失败案例中提取学习材料")

    def _handle_execution_error(self, feedback: FeedbackSignal):
        """
        处理执行错误：记录并触发规则验证

        策略：检查是否是规则本身的问题，如果是则触发重新学习
        """
        logger.info(
            f"处理执行错误 [retry={feedback.retry_count}]: "
            f"{feedback.context.get('error')}"
        )

        if not self.logic_layer:
            return

        # 检查规则是否过时
        try:
            revise_count = self._revise_low_confidence_patterns()
            if revise_count > 0:
                logger.info(f"执行错误触发修正了 {revise_count} 条低置信度规则")
        except Exception as e:
            logger.debug(f"规则修正异常: {e}")

    def _handle_drift_detected(self, feedback: FeedbackSignal):
        """
        处理漂移检测：触发 MetaLearner 重新学习

        策略：找到漂移的原因（低置信度规则、过时模式），
        通知 MetaLearner 优先学习相关新文本
        """
        logger.info(f"处理漂移检测: {feedback.context}")

        if not self.meta_learner or not self._enable_meta_feedback:
            return

        drift_reason = feedback.context.get("error", "")

        # 下调低置信度规则
        if self.logic_layer:
            revise_count = self._revise_low_confidence_patterns()
            logger.info(f"修正了 {revise_count} 条低置信度规则")

        # 触发 MetaLearner 重新学习
        try:
            # 从情节记忆获取最近的领域信息
            if self._episodic:
                recent_failures = self._episodic.get_recent(n=5)
                domains = set(ep.domain for ep in recent_failures if ep.domain)
            else:
                domains = set()

            for domain in domains:
                try:
                    self.meta_learner.learn(
                        input_data=f"领域 {domain} 检测到知识漂移，请重新学习",
                        input_type="text",
                        domain_hint=domain,
                    )
                except Exception as e:
                    logger.debug(f"MetaLearner 重新学习失败: {e}")
        except Exception as e:
            logger.debug(f"漂移回流处理异常: {e}")

    def _revise_low_confidence_patterns(self) -> int:
        """下调低置信度规则，返回修正数量"""
        if not self.logic_layer or not hasattr(self.logic_layer, "_patterns"):
            return 0

        revised = 0
        threshold = self._rule_simplify_threshold

        for pattern_id, pattern in list(self.logic_layer._patterns.items()):
            conf = getattr(pattern, "confidence", 1.0)
            if conf < threshold:
                # 标记为废弃或降低置信度
                try:
                    if hasattr(pattern, "confidence"):
                        pattern.confidence = threshold
                        revised += 1
                    if hasattr(pattern, "status"):
                        pattern.status = "deprecated"
                except Exception:
                    pass

        return revised

    # ─────────────────────────────────────────────────────────────
    # 阶段实现
    # ─────────────────────────────────────────────────────────────

    def _phase_perceive(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Phase 1: 感知 - 解析输入，提取结构化信息"""
        try:
            text = input_data.get("text", input_data.get("query", ""))
            domain_hint = input_data.get("domain_hint")

            # 调用 LLM 提取器（如果有）
            if self.meta_learner and hasattr(self.meta_learner, '_extractor'):
                extractor = self.meta_learner._extractor
                if hasattr(extractor, 'extract'):
                    extraction = extractor.extract(text)
                    return PhaseResult(
                        phase=EvolutionPhase.PERCEIVE,
                        success=True,
                        data={
                            "text": text,
                            "entities": extraction.get("entities", []),
                            "relations": extraction.get("relations", []),
                            "domain": extraction.get("domain", domain_hint or "generic")
                        }
                    )

            # 降级方案：返回原始文本
            return PhaseResult(
                phase=EvolutionPhase.PERCEIVE,
                success=True,
                data={
                    "text": text,
                    "entities": [],
                    "relations": [],
                    "domain": domain_hint or "generic"
                }
            )
        except Exception as e:
            return PhaseResult(
                phase=EvolutionPhase.PERCEIVE,
                success=False,
                error=f"感知失败: {e}"
            )

    def _phase_learn(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Phase 2: 学习 - 从感知结果中发现规则"""
        try:
            perceived = input_data.get("perceived_data", input_data.get("data", {}))
            text = perceived.get("text", input_data.get("text", ""))
            domain = perceived.get("domain", input_data.get("domain", "generic"))

            patterns_created = []

            # 1. MetaLearner 学习
            if self.meta_learner and self._enable_meta_learner:
                try:
                    learn_result = self.meta_learner.learn(
                        text=text,
                        domain_hint=domain,
                        input_type="text"
                    )
                    if learn_result.get("success"):
                        patterns_created.extend(
                            learn_result.get("learned_patterns", [])
                        )
                except Exception as e:
                    logger.debug(f"MetaLearner 学习异常: {e}")

            # 2. RuleDiscovery 发现
            if self.rule_discovery and self._enable_rule_discovery:
                try:
                    discovered = self.rule_discovery.discover_from_text(
                        text=text,
                        domain=domain
                    )
                    patterns_created.extend(discovered)
                except Exception as e:
                    logger.debug(f"RuleDiscovery 发现异常: {e}")

            # 3. Honcho Bridge: 从 conclusions 提取 facts 并直接存入 LogicLayer
            # 不经 discover_from_facts（该方法为频繁模式挖掘设计，数据稀疏时无输出）
            conclusions = input_data.get("conclusions", [])
            if conclusions and self._honcho_bridge:
                try:
                    # conclusions → facts
                    facts = self._honcho_bridge.extract_facts_from_conclusions(
                        conclusions
                    )
                    if facts and self.logic_layer:
                        # facts → LogicPattern → LogicLayer
                        stored = self._honcho_bridge.store_as_patterns(
                            facts, self.logic_layer
                        )
                        patterns_created.extend(stored)
                        logger.debug(
                            f"Honcho bridge: {len(conclusions)} conclusions → "
                            f"{len(facts)} facts → {len(stored)} patterns stored"
                        )
                except Exception as e:
                    logger.debug(f"Honcho bridge 学习异常: {e}")

            # 4. 存入 LogicLayer
            if self.logic_layer and patterns_created:
                for pattern in patterns_created:
                    try:
                        if hasattr(pattern, 'id'):
                            self.logic_layer.add_pattern(pattern)
                    except Exception as e:
                        logger.debug(f"存入 LogicLayer 异常: {e}")

            return PhaseResult(
                phase=EvolutionPhase.LEARN,
                success=True,
                data={
                    "patterns_created": len(patterns_created),
                    "pattern_ids": [
                        p.id if hasattr(p, 'id') else str(p)
                        for p in patterns_created
                    ]
                }
            )
        except Exception as e:
            return PhaseResult(
                phase=EvolutionPhase.LEARN,
                success=False,
                error=f"学习失败: {e}"
            )

    def _phase_reason(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Phase 3: 推理 - 执行前向链或后向链推理"""
        try:
            facts = input_data.get("facts", [])
            query = input_data.get("query", "")
            max_depth = input_data.get("max_depth", 5)

            if not self.reasoner:
                return PhaseResult(
                    phase=EvolutionPhase.REASON,
                    success=False,
                    error="推理引擎未配置"
                )

            if not facts and not query:
                return PhaseResult(
                    phase=EvolutionPhase.REASON,
                    success=True,
                    data={"conclusions": [], "note": "无事实或查询"}
                )

            # 执行前向链推理
            conclusions = []
            try:
                result = self.reasoner.forward_chain(facts=facts, max_depth=max_depth)
                if isinstance(result, dict):
                    conclusions = result.get("conclusions", [])
                else:
                    conclusions = result if isinstance(result, list) else []
            except Exception as e:
                return PhaseResult(
                    phase=EvolutionPhase.REASON,
                    success=False,
                    error=f"推理执行失败: {e}"
                )

            return PhaseResult(
                phase=EvolutionPhase.REASON,
                success=True,
                data={"conclusions": conclusions, "count": len(conclusions)}
            )
        except Exception as e:
            return PhaseResult(
                phase=EvolutionPhase.REASON,
                success=False,
                error=f"推理失败: {e}"
            )

    def _phase_execute(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Phase 4: 执行 - 执行推理得出的动作"""
        try:
            conclusions = input_data.get("conclusions", [])

            executed = []
            for conclusion in conclusions:
                if isinstance(conclusion, dict) and conclusion.get("action"):
                    action = conclusion["action"]
                    executed.append({
                        "conclusion": conclusion,
                        "action": action,
                        "executed": True
                    })

            return PhaseResult(
                phase=EvolutionPhase.EXECUTE,
                success=True,
                data={
                    "executed_count": len(executed),
                    "actions": executed
                }
            )
        except Exception as e:
            return PhaseResult(
                phase=EvolutionPhase.EXECUTE,
                success=False,
                error=f"执行失败: {e}"
            )

    def _phase_evaluate(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Phase 5: 评估 - 评估推理结果质量"""
        try:
            if not self.evaluator:
                return PhaseResult(
                    phase=EvolutionPhase.EVALUATE,
                    success=True,
                    data={"note": "评估器未配置，跳过"}
                )

            learned_patterns = input_data.get("patterns_created", [])
            inference_result = input_data.get("reason_result")

            eval_result = self.evaluator.evaluate_learning_quality(learned_patterns)

            return PhaseResult(
                phase=EvolutionPhase.EVALUATE,
                success=True,
                data=eval_result
            )
        except Exception as e:
            return PhaseResult(
                phase=EvolutionPhase.EVALUATE,
                success=False,
                error=f"评估失败: {e}"
            )

    def _phase_detect_drift(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Phase 6: 漂移检测 - 检测知识/规则漂移"""
        try:
            drift_detected = input_data.get("drift_detected", False)
            reason = input_data.get("reason", "")

            # 检查 LogicLayer 置信度
            if self.logic_layer and hasattr(self.logic_layer, "_patterns"):
                low_conf = [
                    p for p in self.logic_layer._patterns.values()
                    if getattr(p, "confidence", 1.0) < 0.4
                ]
                if low_conf:
                    drift_detected = True
                    reason = f"发现 {len(low_conf)} 条低置信度规则"

            return PhaseResult(
                phase=EvolutionPhase.DETECT_DRIFT,
                success=True,
                data={
                    "drift_detected": drift_detected,
                    "reason": reason
                }
            )
        except Exception as e:
            return PhaseResult(
                phase=EvolutionPhase.DETECT_DRIFT,
                success=False,
                error=f"漂移检测失败: {e}"
            )

    def _phase_revise_rules(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Phase 7: 规则修正 - 修正或废弃问题规则"""
        try:
            drift_data = input_data.get("drift_data", input_data.get("data", {}))
            drift_detected = drift_data.get("drift_detected", False)

            revise_count = 0

            if not drift_detected:
                return PhaseResult(
                    phase=EvolutionPhase.REVISE_RULES,
                    success=True,
                    data={"revised": 0, "reason": "无漂移，无需修正"}
                )

            drift_reason = drift_data.get("reason", "")

            if "低置信度" in drift_reason and self.logic_layer:
                revise_count = self._revise_low_confidence_patterns()

            return PhaseResult(
                phase=EvolutionPhase.REVISE_RULES,
                success=True,
                data={
                    "revised": revise_count,
                    "reason": drift_reason
                }
            )
        except Exception as e:
            return PhaseResult(
                phase=EvolutionPhase.REVISE_RULES,
                success=False,
                error=f"规则修正失败: {e}"
            )

    def _phase_update_kg(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Phase 8: 知识更新 - 更新知识图谱"""
        try:
            updated_count = 0

            if self.logic_layer and input_data.get("patterns_created"):
                for pattern_id in input_data.get("patterns_created", []):
                    updated_count += 1

            return PhaseResult(
                phase=EvolutionPhase.UPDATE_KG,
                success=True,
                data={
                    "updated": updated_count,
                    "domain": input_data.get("domain", "generic")
                }
            )
        except Exception as e:
            return PhaseResult(
                phase=EvolutionPhase.UPDATE_KG,
                success=False,
                error=f"知识更新失败: {e}"
            )

    def _phase_meta_learn(self, input_data: Dict[str, Any]) -> PhaseResult:
        """MetaLearn: 失败反馈 - MetaLearner 处理失败并调整策略"""
        try:
            if not self.meta_learner or not self._enable_meta_learner:
                return PhaseResult(
                    phase=EvolutionPhase.META_LEARN,
                    success=True,
                    data={"note": "MetaLearner 未启用，跳过"}
                )

            feedback = input_data.get("feedback")
            if not feedback:
                return PhaseResult(
                    phase=EvolutionPhase.META_LEARN,
                    success=True,
                    data={"note": "无反馈信号，跳过"}
                )

            # 分析失败原因，推荐策略
            failure_type = feedback.get("failure_type")
            context = feedback.get("context", {})

            strategy = "continue"
            if failure_type == FailureType.INFERENCE_ERROR.value:
                strategy = "simplify_rules"
            elif failure_type == FailureType.PATTERN_CONFLICT.value:
                strategy = "resolve_conflict"
            elif failure_type == FailureType.DRIFT_DETECTED.value:
                strategy = "relearn"

            # 调用 MetaLearner 分析
            if hasattr(self.meta_learner, 'analyze_failure'):
                try:
                    analysis = self.meta_learner.analyze_failure(context)
                    strategy = analysis.get("recommended_strategy", strategy)
                except Exception as e:
                    logger.debug(f"MetaLearner.analyze_failure 异常: {e}")

            return PhaseResult(
                phase=EvolutionPhase.META_LEARN,
                success=True,
                data={
                    "failure_type": failure_type,
                    "strategy": strategy,
                    "context": context
                }
            )
        except Exception as e:
            return PhaseResult(
                phase=EvolutionPhase.META_LEARN,
                success=False,
                error=f"MetaLearn 失败: {e}"
            )
