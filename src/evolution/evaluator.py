"""
Knowledge Evaluator — 知识质量评估器 + 生命周期管理 + 反馈回路

v2.0 核心模块，实现:
1. 知识质量多维评估 (一致性、冗余度、置信度衰减、引用频率)
2. 知识生命周期状态机 CANDIDATE → ACTIVE → STALE → ARCHIVED
3. 学习效果反馈回路 — 追踪知识使用，反向调整策略权重

参考: CORAL 自进化 + SEAgent 反馈闭环
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.knowledge_graph import KnowledgeGraph, TripleStatus, TypedTriple
from ..utils.config import get_config

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class QualityScore:
    """单条知识的质量评分"""
    triple_id: str
    consistency: float = 1.0      # 一致性 (0-1)
    redundancy: float = 0.0       # 冗余度 (0=无冗余, 1=完全冗余)
    freshness: float = 1.0        # 新鲜度 (0=陈旧, 1=最新)
    citation_score: float = 0.0   # 引用频率归一化 (0-1)
    overall: float = 0.0          # 综合得分 (0-1)

    def compute_overall(
        self,
        w_consistency: float = None,
        w_redundancy: float = None,
        w_freshness: float = None,
        w_citation: float = None,
    ) -> float:
        """加权综合评分 — 权重从 ConfigManager 读取，不硬编码"""
        cfg = get_config().evolution
        w_con = w_consistency if w_consistency is not None else cfg.quality_w_consistency
        w_red = w_redundancy if w_redundancy is not None else cfg.quality_w_redundancy
        w_fre = w_freshness if w_freshness is not None else cfg.quality_w_freshness
        w_cit = w_citation if w_citation is not None else cfg.quality_w_citation
        self.overall = (
            w_con * self.consistency
            + w_red * (1.0 - self.redundancy)
            + w_fre * self.freshness
            + w_cit * self.citation_score
        )
        return self.overall


@dataclass
class LifecycleEvent:
    """生命周期变更事件"""
    triple_id: str
    old_status: TripleStatus
    new_status: TripleStatus
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class UsageRecord:
    """知识使用追踪记录"""
    triple_id: str
    usage_type: str          # "reasoning" | "retrieval" | "pattern_match"
    success: bool = True
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────
# KnowledgeEvaluator — 核心评估引擎
# ─────────────────────────────────────────────

class KnowledgeEvaluator:
    """
    知识质量评估器 — 反馈闭环的核心

    职责:
    1. 多维质量评估 (一致性/冗余度/新鲜度/引用频率)
    2. 知识生命周期自动管理
    3. 使用追踪 + 反向调整策略权重
    """

    # 参数全部从 ConfigManager 读取，符合零硬编码规则

    def __init__(
        self,
        graph: KnowledgeGraph,
        decay_interval: float = None,
        decay_factor: float = None,
    ):
        # 绑定知识图谱 — 评估对象是图中的所有三元组
        self._graph = graph
        # 从 ConfigManager 读取配置，构造参数可覆盖 (方便测试)
        cfg = get_config().evolution
        # 衰减周期: 每隔多少秒执行一次衰减 (86400 = 1天)
        self._decay_interval = decay_interval if decay_interval is not None else cfg.decay_interval
        # 衰减因子: 每个周期置信度乘以此值 (0.95 = 每天降 5%)
        self._decay_factor = decay_factor if decay_factor is not None else cfg.decay_factor

        # 使用追踪: 记录知识被检索/推理/反馈使用的每一次事件
        self._usage_records: List[UsageRecord] = []
        # 按三元组 ID 索引的使用记录 (快速查找某条知识的使用情况)
        self._usage_by_triple: Dict[str, List[UsageRecord]] = defaultdict(list)

        # 生命周期事件日志 — 记录每次状态转换 (CANDIDATE→ACTIVE 等)
        self._lifecycle_events: List[LifecycleEvent] = []

        # 质量评分缓存: triple_id → QualityScore (每次 evaluate_all 刷新)
        self._quality_cache: Dict[str, QualityScore] = {}

    # ─────────────────────────────────────────
    # 1. 质量评估
    # ─────────────────────────────────────────

    def evaluate(self, triple_id: str) -> Optional[QualityScore]:
        """评估单条知识的质量"""
        triple = self._graph._triples.get(triple_id)
        if triple is None:
            return None

        score = QualityScore(triple_id=triple_id)

        # 一致性: 检测是否与同 subject+predicate 的其他三元组矛盾
        score.consistency = self._check_consistency(triple)

        # 冗余度: 检测同 predicate+object 的重复程度
        score.redundancy = self._check_redundancy(triple)

        # 新鲜度: 基于最后访问时间的衰减
        score.freshness = self._compute_freshness(triple)

        # 引用频率: 归一化访问次数
        score.citation_score = self._compute_citation(triple)

        score.compute_overall()
        self._quality_cache[triple_id] = score
        return score

    def evaluate_all(self) -> Dict[str, QualityScore]:
        """批量评估所有知识"""
        self._quality_cache.clear()
        for tid in list(self._graph._triples.keys()):
            self.evaluate(tid)
        return dict(self._quality_cache)

    def _check_consistency(self, triple: TypedTriple) -> float:
        """
        一致性检测 — 检查是否存在矛盾知识
    
        策略: 同一 (subject, predicate) 如果有多个不同 object,
        且 predicate 不是“包含”类多值关系, 可能存在矛盾。
        例: “张三 身高 170cm” vs “张三 身高 180cm” → 矛盾
        """
        # 多值关系白名单: 这些谓词允许同一主语有多个宾语
        multi_value_predicates = {
            "has_part", "components", "function", "属性",
            "_condition_of", "_action_of", "_type_of",
        }
        if triple.predicate in multi_value_predicates:
            return 1.0  # 多值关系不算矛盾

        # 查询同一 (subject, predicate) 的所有三元组
        same_sp = self._graph.query(
            subject=triple.subject, predicate=triple.predicate
        )
        if len(same_sp) <= 1:
            return 1.0  # 唯一值, 无矛盾

        # 多个不同 object → 可能矛盾, 每多一个冲突降分 0.2
        n_conflicts = len(same_sp) - 1
        return max(0.0, 1.0 - 0.2 * n_conflicts)

    def _check_redundancy(self, triple: TypedTriple) -> float:
        """
        冗余度检测 — 同 (predicate, object) 的条数

        完全冗余 = 1.0, 无冗余 = 0.0
        """
        same_po = self._graph.query(
            predicate=triple.predicate, obj=triple.object
        )
        n = len(same_po)
        if n <= 1:
            return 0.0
        cfg = get_config().evolution
        return min(1.0, (n - 1) / cfg.redundancy_max_duplicates)

    def _compute_freshness(self, triple: TypedTriple) -> float:
        """
        新鲜度 — 基于最后访问时间的指数衰减

        freshness = decay_factor ^ (elapsed / decay_interval)
        """
        now = time.time()
        last = triple.last_accessed if triple.last_accessed > 0 else triple.timestamp
        elapsed = now - last
        if elapsed <= 0:
            return 1.0
        periods = elapsed / self._decay_interval
        return max(0.0, self._decay_factor ** periods)

    def _compute_citation(self, triple: TypedTriple) -> float:
        """
        引用频率归一化 — access_count 相对于图中最大值的比例

        用对数缩放避免极端值。
        """
        if self._graph.size == 0:
            return 0.0

        max_access = max(
            (t.access_count for t in self._graph), default=1
        )
        if max_access == 0:
            return 0.0

        import math
        return math.log1p(triple.access_count) / math.log1p(max_access)

    # ─────────────────────────────────────────
    # 2. 生命周期管理
    # ─────────────────────────────────────────

    def apply_lifecycle(self) -> List[LifecycleEvent]:
        """
        执行一轮生命周期状态转换

        状态机:
        CANDIDATE → ACTIVE   (overall >= PROMOTE_THRESHOLD)
        ACTIVE    → STALE    (overall < STALE_THRESHOLD)
        STALE     → ARCHIVED (confidence < ARCHIVE_CONFIDENCE)
        STALE     → ACTIVE   (被再次引用, overall >= PROMOTE_THRESHOLD)

        Returns:
            本轮产生的变更事件列表
        """
        events: List[LifecycleEvent] = []
        cfg = get_config().evolution

        # 先刷新评估分数
        scores = self.evaluate_all()

        for tid, qs in scores.items():
            triple = self._graph._triples.get(tid)
            if triple is None:
                continue

            old_status = triple.status
            new_status = old_status

            if old_status == TripleStatus.CANDIDATE:
                if qs.overall >= cfg.promote_threshold:
                    new_status = TripleStatus.ACTIVE
                    reason = f"promote: overall={qs.overall:.2f} >= {cfg.promote_threshold}"
                else:
                    reason = ""

            elif old_status == TripleStatus.ACTIVE:
                if qs.overall < cfg.stale_threshold:
                    new_status = TripleStatus.STALE
                    reason = f"demote: overall={qs.overall:.2f} < {cfg.stale_threshold}"
                else:
                    reason = ""

            elif old_status == TripleStatus.STALE:
                if triple.confidence < cfg.archive_confidence:
                    new_status = TripleStatus.ARCHIVED
                    reason = f"archive: confidence={triple.confidence:.2f} < {cfg.archive_confidence}"
                elif qs.overall >= cfg.promote_threshold:
                    new_status = TripleStatus.ACTIVE
                    reason = f"revive: overall={qs.overall:.2f} >= {cfg.promote_threshold}"
                else:
                    reason = ""

            else:
                reason = ""

            if new_status != old_status:
                self._graph.update_status(tid, new_status)
                event = LifecycleEvent(
                    triple_id=tid,
                    old_status=old_status,
                    new_status=new_status,
                    reason=reason,
                )
                events.append(event)
                self._lifecycle_events.append(event)
                logger.info(
                    f"生命周期变更: {tid} {old_status.value} → {new_status.value} ({reason})"
                )

        return events

    def apply_confidence_decay(self) -> int:
        """
        对长期未引用的知识执行置信度衰减

        公式: new_confidence = old * decay_factor ^ (elapsed / interval)
        下限 0.01, 避免完全消失

        Returns:
            受影响的三元组数量
        """
        now = time.time()
        affected = 0

        for triple in self._graph:
            # ARCHIVED 状态不再衰减 (已归档)
            if triple.status == TripleStatus.ARCHIVED:
                continue

            # 计算自上次访问以来的时间间隔
            last = triple.last_accessed if triple.last_accessed > 0 else triple.timestamp
            elapsed = now - last
            if elapsed < self._decay_interval:
                continue  # 未到衰减周期, 跳过

            # 指数衰减: 经过 N 个周期后置信度降为 original * factor^N
            periods = elapsed / self._decay_interval
            new_conf = triple.confidence * (self._decay_factor ** periods)
            new_conf = max(0.01, new_conf)  # 下限保护

            if abs(new_conf - triple.confidence) > 0.001:
                self._graph.update_confidence(triple.id, round(new_conf, 4))
                affected += 1

        if affected > 0:
            logger.info(f"置信度衰减: 影响 {affected} 条三元组")
        return affected

    # ─────────────────────────────────────────
    # 3. 使用追踪 + 反馈回路
    # ─────────────────────────────────────────

    def record_usage(
        self,
        triple_id: str,
        usage_type: str = "retrieval",
        success: bool = True,
        context: Optional[Dict] = None,
    ):
        """
        记录知识被使用的事件

        Args:
            triple_id: 被使用的三元组 ID
            usage_type: "reasoning" / "retrieval" / "pattern_match"
            success: 使用是否成功 (例如推理结论被用户接受)
            context: 额外上下文
        """
        record = UsageRecord(
            triple_id=triple_id,
            usage_type=usage_type,
            success=success,
            context=context or {},
        )
        self._usage_records.append(record)
        self._usage_by_triple[triple_id].append(record)

        # 同步更新图中的 access_count
        triple = self._graph._triples.get(triple_id)
        if triple is not None:
            triple.access_count += 1
            triple.last_accessed = time.time()

    def get_usage_stats(self, triple_id: str) -> Dict[str, Any]:
        """获取某条知识的使用统计"""
        records = self._usage_by_triple.get(triple_id, [])
        if not records:
            return {"total": 0, "success_rate": 0.0, "by_type": {}}

        total = len(records)
        successes = sum(1 for r in records if r.success)
        by_type: Dict[str, int] = defaultdict(int)
        for r in records:
            by_type[r.usage_type] += 1

        return {
            "total": total,
            "success_rate": successes / total if total > 0 else 0.0,
            "by_type": dict(by_type),
        }

    def compute_feedback_weights(self) -> Dict[str, float]:
        """
        根据使用追踪计算反馈权重

        用于反向调整 MetaLearner 的策略权重:
        - 高使用率 + 高成功率 → 正向反馈 (权重 > 1.0)
        - 低使用率 + 低成功率 → 负向反馈 (权重 < 1.0)

        Returns:
            {source_type: adjustment_weight} e.g. {"learned": 1.15, "discovered": 0.85}
        """
        source_stats: Dict[str, Dict] = defaultdict(
            lambda: {"total": 0, "success": 0, "usage": 0}
        )

        for record in self._usage_records:
            triple = self._graph._triples.get(record.triple_id)
            if triple is None:
                continue
            primary_source = triple.source.split(",")[0]
            source_stats[primary_source]["total"] += 1
            source_stats[primary_source]["usage"] += 1
            if record.success:
                source_stats[primary_source]["success"] += 1

        weights: Dict[str, float] = {}
        for source, stats in source_stats.items():
            if stats["total"] == 0:
                weights[source] = 1.0
                continue
            success_rate = stats["success"] / stats["total"]
            # 线性映射: 0.0 → 0.7,  0.5 → 1.0,  1.0 → 1.3
            weights[source] = 0.7 + 0.6 * success_rate

        return weights

    # ─────────────────────────────────────────
    # 统计和报告
    # ─────────────────────────────────────────

    def get_quality_summary(self) -> Dict[str, Any]:
        """获取知识质量总览"""
        if not self._quality_cache:
            self.evaluate_all()

        scores = list(self._quality_cache.values())
        if not scores:
            return {
                "total_evaluated": 0,
                "avg_overall": 0.0,
                "avg_consistency": 0.0,
                "avg_freshness": 0.0,
                "avg_citation": 0.0,
                "low_quality_count": 0,
            }

        n = len(scores)
        return {
            "total_evaluated": n,
            "avg_overall": sum(s.overall for s in scores) / n,
            "avg_consistency": sum(s.consistency for s in scores) / n,
            "avg_freshness": sum(s.freshness for s in scores) / n,
            "avg_citation": sum(s.citation_score for s in scores) / n,
            "low_quality_count": sum(1 for s in scores if s.overall < get_config().evolution.stale_threshold),
        }

    def get_lifecycle_summary(self) -> Dict[str, Any]:
        """获取生命周期管理总览"""
        return {
            "total_events": len(self._lifecycle_events),
            "recent_events": [
                {
                    "triple_id": e.triple_id,
                    "change": f"{e.old_status.value} → {e.new_status.value}",
                    "reason": e.reason,
                }
                for e in self._lifecycle_events[-10:]
            ],
            "usage_records": len(self._usage_records),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """综合统计"""
        return {
            "quality": self.get_quality_summary(),
            "lifecycle": self.get_lifecycle_summary(),
            "feedback_weights": self.compute_feedback_weights(),
        }
