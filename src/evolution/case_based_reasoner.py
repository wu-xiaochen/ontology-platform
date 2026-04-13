"""
CaseBasedReasoner - 案例推理引擎

基于「人类逻辑起源」的认知模型：
遇到新事物 → 检索过去相似案例 → 类比适配 → 执行 → 存为新案例

核心四阶段（CBR cycle）：
1. Retrieve（检索）→ 找相似案例
2. Reuse（复用）→ 适配案例解决方案
3. Revise（修正）→ 评估并调整适配结果
4. Retain（存储）→ 成功的案例存入经验库

当规则库为空且案例库也为空时，启动 MetaStrategy（元策略层），
这是人类"没处理过也不放弃"的机制：
- Trial（试探）: 小范围试错
- Decompose（分解）: 拆成小块逐个击破
- Consult（请教）: 标记为待外部补充
- Defer（搁置）: 承认暂时无法处理但保持记录

依赖：
- src/evolution/unified_logic.py 的 LogicLayer（规则库，用于 Retrieve 时的混合检索）
- src/evolution/episodic_memory.py 的 EpisodicMemory（失败案例，用于修正学习）
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import time
import logging

from ..utils.config import get_config

logger = logging.getLogger(__name__)


class CaseOutcome(Enum):
    """案例结果"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"  # 部分成功
    UNKNOWN = "unknown"


class MetaStrategy(Enum):
    """
    元策略：当无案例可参考时的应对策略

    这是人类"真没处理过也不躺平"的机制。
    """
    TRIAL = "trial"          # 小范围试探性执行
    DECOMPOSE = "decompose"  # 拆解为子问题
    CONSULT = "consult"      # 标记需要外部补充
    DEFER = "defer"          # 暂时搁置，等待更多信息
    ADAPT_BEST = "adapt_best"  # 从最近似案例做大幅适配


@dataclass
class Case:
    """
    单个案例：situation + solution = outcome

    代表一个具体经历过的场景及其处理结果。
    """
    case_id: str
    situation: Dict[str, Any]   # 场景上下文（扁平化 key-value）
    solution: Any               # 执行的解决方案
    outcome: CaseOutcome
    outcome_text: str           # 人类可读的结果描述
    timestamp: float = field(default_factory=time.time)
    domain: Optional[str] = None
    confidence: float = 0.8    # 案例可信度（基于结果稳定性）
    adaptation_steps: List[str] = field(default_factory=list)  # 复用时的适配步骤
    retrieval_count: int = 0    # 被检索次数（用于评估重要性）

    def similarity_with(self, other: Dict[str, Any]) -> float:
        """
        计算当前案例与另一个情境的相似度（改进版 Jaccard + 数值兼容）

        - 分类字段：精确匹配
        - 数值字段：key 相同即算匹配，value 接近给部分分数
        - 排除 case_id、timestamp 等标识字段
        """
        IGNORED = {"case_id", "timestamp", "confidence", "retrieval_count"}

        def extract_keys(d: Dict, prefix: str = "") -> set:
            result = set()
            for k, v in d.items():
                if k in IGNORED:
                    continue
                key = f"{prefix}{k}"
                if isinstance(v, dict):
                    result.update(extract_keys(v, f"{key}."))
                elif isinstance(v, list):
                    if not v:  # 空列表忽略
                        continue
                    for item in v:
                        if isinstance(item, dict):
                            result.update(extract_keys(item, key + "[]."))
                        else:
                            result.add(f"{key}[]={item}")
                elif isinstance(v, (int, float)):
                    # 数值字段：只按 key 算匹配，value 差异单独处理
                    result.add(f"{key}=_NUMERIC_")
                else:
                    result.add(f"{key}={v}")
            return result

        def numeric_similarity(d1: Dict, d2: Dict) -> float:
            """计算数值字段的部分相似度（0~1）

            - key 完全匹配 + value 相等 → 1.0
            - key 完全匹配 + value 不同 → 0.5
            - key 只在一侧存在 → 0.25
            """
            num_keys = set()
            for d in [d1, d2]:
                for k, v in d.items():
                    if k in IGNORED:
                        continue
                    if isinstance(v, (int, float)):
                        num_keys.add(k)

            if not num_keys:
                return 0.0

            matches = 0
            for k in num_keys:
                v1 = d1.get(k)
                v2 = d2.get(k)
                if v1 is not None and v2 is not None:
                    # key 匹配
                    if v1 == v2:
                        matches += 1.0  # 完全匹配
                    else:
                        matches += 0.5  # key 匹配但值不同
                elif k in d1 and k in d2:
                    matches += 0.25  # key 在两侧但值类型不同

            return matches / len(num_keys)

        keys_self = extract_keys(self.situation)
        keys_other = extract_keys(other)

        # 标准 Jaccard（分类字段）
        num_self = {k for k in keys_self if "_NUMERIC_" in k}
        num_other = {k for k in keys_other if "_NUMERIC_" in k}
        cat_self = keys_self - num_self
        cat_other = keys_other - num_other

        if cat_self or cat_other:
            cat_intersection = cat_self & cat_other
            cat_union = cat_self | cat_other
            jaccard = len(cat_intersection) / len(cat_union)
        else:
            jaccard = 0.0

        # 数值字段相似度
        num_sim = numeric_similarity(self.situation, other)

        # 综合评分
        cat_count = len(cat_self | cat_other)
        num_count = len(num_self | num_other)

        if cat_count > 0 and num_count > 0:
            # 混合：各50%
            return jaccard * 0.5 + num_sim * 0.5
        elif cat_count > 0:
            # 纯分类字段
            return jaccard
        else:
            # 纯数值字段：只靠 num_sim
            return num_sim

    def to_dict(self) -> Dict:
        return {
            "case_id": self.case_id,
            "situation": self.situation,
            "solution": str(self.solution)[:200],
            "outcome": self.outcome.value,
            "outcome_text": self.outcome_text,
            "timestamp": self.timestamp,
            "domain": self.domain,
            "confidence": self.confidence,
            "adaptation_steps": self.adaptation_steps,
            "retrieval_count": self.retrieval_count,
        }


@dataclass
class AdaptationResult:
    """类比适配结果"""
    adapted_solution: Any
    adaptation_steps: List[str]
    confidence: float  # 适配置信度（基于原始案例质量 × 情境匹配度）
    strategy_used: str  # "reuse" / "partial_adapt" / "meta_strategy"
    fallback_cases: List[str] = field(default_factory=list)  # 引用了哪些案例


class CaseBase:
    """
    案例库管理器

    管理所有经验案例，支持增删改查。
    """

    def __init__(self):
        self._cases: Dict[str, Case] = {}
        self._by_domain: Dict[str, List[str]] = {}  # domain → case_ids
        self._by_outcome: Dict[CaseOutcome, List[str]] = {}  # outcome → case_ids

    def add(self, case: Case):
        """添加案例"""
        self._cases[case.case_id] = case

        if case.domain:
            self._by_domain.setdefault(case.domain, []).append(case.case_id)

        self._by_outcome.setdefault(case.outcome, []).append(case.case_id)

    def get(self, case_id: str) -> Optional[Case]:
        return self._cases.get(case_id)

    def get_by_domain(self, domain: str) -> List[Case]:
        ids = self._by_domain.get(domain, [])
        return [self._cases[c] for c in ids if c in self._cases]

    def get_by_outcome(self, outcome: CaseOutcome) -> List[Case]:
        ids = self._by_outcome.get(outcome, [])
        return [self._cases[c] for c in ids if c in self._cases]

    def get_all(self) -> List[Case]:
        return list(self._cases.values())

    def size(self) -> int:
        return len(self._cases)

    def remove(self, case_id: str) -> bool:
        """移除案例"""
        if case_id not in self._cases:
            return False

        case = self._cases.pop(case_id)

        # 从索引中移除
        for idx_dict in [self._by_domain, self._by_outcome]:
            for key_list in idx_dict.values():
                if case_id in key_list:
                    key_list.remove(case_id)

        return True


class CaseBasedReasoner:
    """
    案例推理引擎

    与 RuleReasoner（规则推理）互补：
    - RuleReasoner：用已有规则做前向/后向链
    - CaseBasedReasoner：当无规则或规则失败时，用历史案例类比推理

    使用方式：
    ```python
    from src.evolution.case_based_reasoner import CaseBasedReasoner, Case, CaseOutcome

    cbr = CaseBasedReasoner()

    # 存入一个案例
    cbr.retain(
        situation={"domain": "燃气", "pressure": "high", "device": "调压器"},
        solution={"action": "降低压力", "value": "0.3MPa"},
        outcome=CaseOutcome.SUCCESS,
        outcome_text="压力恢复正常"
    )

    # 给新情境推理解决方案
    result = cbr.reason(
        situation={"domain": "燃气", "pressure": "very_high", "device": "调压器"},
        domain="燃气"
    )
    print(result.adapted_solution)
    ```
    """

    def __init__(
        self,
        logic_layer=None,
        episodic_memory=None,
        min_similarity: float = 0.3,
        max_cases: int = 10000,
    ):
        """
        Args:
            logic_layer: 规则库（用于 Retrieve 阶段的混合检索）
            episodic_memory: 情节记忆（从失败中学习新案例）
            min_similarity: 最低相似度阈值，低于此值不返回案例
            max_cases: 最大案例库容量
        """
        self.config = get_config()
        self.case_base = CaseBase()
        self.logic_layer = logic_layer
        self._episodic = episodic_memory
        self._min_similarity = min_similarity
        self._max_cases = max_cases
        self._case_counter = 0

    def reason(
        self,
        situation: Dict[str, Any],
        domain: Optional[str] = None,
        top_k: int = 3,
    ) -> AdaptationResult:
        """
        核心推理：给定情境，返回适配后的解决方案

        流程：
        1. Retrieve：从案例库检索相似案例
        2. Reuse：适配最佳匹配案例的解决方案
        3. 如果无案例可用 → 触发 MetaStrategy
        """
        # 1. Retrieve
        candidates = self._retrieve(situation, domain, top_k)

        if not candidates:
            # 无案例 → MetaStrategy
            return self._apply_meta_strategy(situation, domain)

        # 2. Reuse - 适配最佳案例
        best_case, similarity = candidates[0]

        # 根据相似度决定适配策略
        if similarity >= 0.8:
            return self._reuse_case(best_case, situation, "direct")
        elif similarity >= 0.5:
            return self._reuse_case(best_case, situation, "partial")
        else:
            # 相似度低，触发混合策略
            return self._reuse_case(best_case, situation, "meta_hybrid")

    def _retrieve(
        self,
        situation: Dict[str, Any],
        domain: Optional[str],
        top_k: int,
    ) -> List[Tuple[Case, float]]:
        """检索最相似的 K 个案例"""
        pool = self.case_base.get_all()

        if domain:
            # 优先同领域
            domain_cases = self.case_base.get_by_domain(domain)
            pool = domain_cases + [c for c in pool if c not in domain_cases]

        scored = []
        for case in pool:
            sim = case.similarity_with(situation)
            if sim >= self._min_similarity:
                scored.append((case, sim))

        # 按相似度排序
        scored.sort(key=lambda x: x[1], reverse=True)

        # 更新检索计数
        for case, _ in scored[:top_k]:
            case.retrieval_count += 1

        return scored[:top_k]

    def _reuse_case(
        self,
        case: Case,
        situation: Dict[str, Any],
        strategy: str,  # "direct" / "partial" / "meta_hybrid"
    ) -> AdaptationResult:
        """
        复用案例：适配旧案例的解决方案到新情境

        适配策略：
        - direct：完全复用（相似度 >= 0.8）
        - partial：部分复用 + 调整（0.5 <= sim < 0.8）
        - meta_hybrid：仅保留结构，从规则库补充细节
        """
        adaptation_steps = [f"基于案例 {case.case_id}（相似度待计算）进行适配"]

        if strategy == "direct":
            adapted_solution = case.solution
            adaptation_steps.append("相似度高，直接复用解决方案")

        elif strategy == "partial":
            # 部分适配：提取解决方案结构，按需调整
            adapted_solution = self._partial_adapt(case.solution, situation, case.situation)
            adaptation_steps.append("相似度中等，对解决方案进行部分调整")

        else:  # meta_hybrid
            adapted_solution = self._hybrid_adapt(case, situation)
            adaptation_steps.append("相似度低，采用混合适配策略")

        return AdaptationResult(
            adapted_solution=adapted_solution,
            adaptation_steps=adaptation_steps,
            confidence=case.confidence * min(1.0, case.similarity_with(situation) * 1.5),
            strategy_used=strategy,
            fallback_cases=[case.case_id],
        )

    def _partial_adapt(
        self,
        solution: Any,
        target_situation: Dict,
        source_situation: Dict,
    ) -> Any:
        """
        部分适配：将旧解决方案适配到新情境

        策略：
        1. 提取解决方案中的参数结构
        2. 用目标情境的字段替换对应参数
        3. 保持解决方案的行动逻辑不变
        """
        if isinstance(solution, dict):
            adapted = dict(solution)
            for key in solution:
                if key in target_situation and key in source_situation:
                    # 用目标情境的值替换
                    adapted[key] = target_situation[key]
            return adapted
        elif isinstance(solution, list):
            return [self._partial_adapt(item, target_situation, source_situation)
                    for item in solution]
        else:
            return solution

    def _hybrid_adapt(
        self,
        case: Case,
        situation: Dict[str, Any],
    ) -> Any:
        """
        混合适配：综合案例结构 + 规则库 + 元策略

        当案例相似度很低时：
        1. 尝试从 logic_layer 获取相关规则
        2. 规则和案例结构结合
        3. 返回组合方案
        """
        solution_parts = []

        # 提取案例的行动结构
        if isinstance(case.solution, dict):
            solution_parts.append({
                "strategy": "case_based",
                "action": case.solution.get("action", str(case.solution)[:100]),
                "confidence": case.confidence * 0.5,  # 低相似度降权
            })

        # 尝试从规则库补充
        if self.logic_layer and hasattr(self.logic_layer, "query_rules"):
            try:
                rules = self.logic_layer.query_rules(situation)
                if rules:
                    solution_parts.append({
                        "strategy": "rule_based",
                        "rules": rules[:3],
                        "confidence": 0.6,
                    })
            except Exception as e:
                logger.debug(f"规则库查询失败: {e}")

        return {
            "type": "hybrid",
            "components": solution_parts,
            "note": "低相似度案例 + 规则库混合方案",
        }

    def _apply_meta_strategy(
        self,
        situation: Dict[str, Any],
        domain: Optional[str],
    ) -> AdaptationResult:
        """
        元策略：当无任何可参考案例时的应对机制

        这是人类"真没处理过也不躺平"的机制。
        策略选择顺序：
        1. DECOMPOSE：拆解问题 → 逐个尝试有把握的子问题
        2. TRIAL：小范围试探
        3. DEFER：承认暂时无法处理但记录
        """
        strategy = self._choose_meta_strategy(situation, domain)

        if strategy == MetaStrategy.DECOMPOSE:
            return AdaptationResult(
                adapted_solution={
                    "type": "meta_strategy",
                    "strategy": "decompose",
                    "action": "将问题拆解为可处理的子问题",
                    "sub_problems": self._decompose_situation(situation),
                },
                adaptation_steps=[
                    "无可用案例，选择 DECOMPOSE 元策略",
                    "将复杂情境拆解为多个子情境",
                ],
                confidence=0.3,
                strategy_used="meta_decompose",
            )

        elif strategy == MetaStrategy.TRIAL:
            return AdaptationResult(
                adapted_solution={
                    "type": "meta_strategy",
                    "strategy": "trial",
                    "action": "小范围试探性执行",
                    "situation": situation,
                },
                adaptation_steps=[
                    "无可用案例，选择 TRIAL 元策略",
                    "建议小范围、低风险地试探",
                ],
                confidence=0.2,
                strategy_used="meta_trial",
            )

        elif strategy == MetaStrategy.CONSULT:
            return AdaptationResult(
                adapted_solution={
                    "type": "meta_strategy",
                    "strategy": "consult",
                    "action": "需要外部补充处理逻辑",
                    "situation": situation,
                },
                adaptation_steps=["无可用案例，需要外部补充"],
                confidence=0.0,
                strategy_used="meta_consult",
            )

        else:  # DEFER
            return AdaptationResult(
                adapted_solution={
                    "type": "meta_strategy",
                    "strategy": "defer",
                    "action": "暂时无法处理，等待更多信息",
                    "situation": situation,
                },
                adaptation_steps=["无可用案例，暂时搁置"],
                confidence=0.0,
                strategy_used="meta_defer",
            )

    def _choose_meta_strategy(
        self,
        situation: Dict[str, Any],
        domain: Optional[str],
    ) -> MetaStrategy:
        """根据情境特征选择合适的元策略"""
        # 统计字段数量（任意类型）
        field_count = len(situation)

        if field_count >= 3:
            return MetaStrategy.DECOMPOSE
        elif self._episodic and domain and domain in self._episodic.get_domains():
            return MetaStrategy.TRIAL
        else:
            return MetaStrategy.DEFER

    def _decompose_situation(self, situation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将复杂情境拆解为可管理的子情境

        策略：
        - dict 字段：提取为独立子情境
        - list 字段：每个元素提取为独立子情境
        - 顶层字段数量 >= 3：按字段分解（每字段一个子情境）
        """
        sub_problems = []

        # 优先提取嵌套结构
        for key, value in situation.items():
            if isinstance(value, dict):
                sub = {key: value}
                sub_problems.append(sub)
            elif isinstance(value, list) and len(value) > 0:
                for item in value[:3]:  # 最多取3个
                    sub = {key: item}
                    sub_problems.append(sub)

        # 如果嵌套结构不够，按顶层字段分解
        if len(sub_problems) < 2:
            for key, value in list(situation.items())[:5]:
                if not any(key in str(sp) for sp in sub_problems):
                    sub_problems.append({key: value})

        return sub_problems[:5]  # 最多5个子问题

    def retain(
        self,
        situation: Dict[str, Any],
        solution: Any,
        outcome: CaseOutcome,
        outcome_text: str,
        domain: Optional[str] = None,
        confidence: float = 0.8,
    ):
        """
        存储新案例（CBR 的 Retain 阶段）

        Args:
            situation: 场景上下文
            solution: 执行的解决方案
            outcome: 执行结果
            outcome_text: 结果描述
            domain: 领域
            confidence: 案例可信度（基于结果稳定性）
        """
        # 检查容量
        if self.case_base.size() >= self._max_cases:
            self._evict_low_value_case()

        self._case_counter += 1
        case_id = f"case_{int(time.time() * 1000)}_{self._case_counter}"
        case = Case(
            case_id=case_id,
            situation=situation,
            solution=solution,
            outcome=outcome,
            outcome_text=outcome_text,
            domain=domain,
            confidence=confidence,
        )

        self.case_base.add(case)
        logger.info(f"案例存储: {case_id}, outcome={outcome.value}, domain={domain}")

        return case_id

    def _evict_low_value_case(self):
        """淘汰最低价值案例（FIFO + LFU 结合）"""
        cases = self.case_base.get_all()
        if not cases:
            return

        # 评分：访问次数高、置信度高、近期的优先保留
        scored = [
            (c.case_id, c.retrieval_count * 0.3 + c.confidence * 0.5)
            for c in cases
        ]
        worst_id = min(scored, key=lambda x: x[1])[0]
        self.case_base.remove(worst_id)
        logger.info(f"案例库满，淘汰案例: {worst_id}")

    def learn_from_episodic(self, episodic_memory) -> int:
        """
        从情节记忆（EpisodicMemory）批量导入成功案例

        这是 MetaLearner 回流学习的逆向补充：
        不仅从规则失败中学习，也从真实的成功/失败经历中学习。

        Returns:
            导入的案例数量
        """
        from .episodic_memory import OutcomeType

        recent = episodic_memory.get_recent(n=100)
        imported = 0

        for ep in recent:
            # 只导入成功的案例
            if ep.outcome == OutcomeType.SUCCESS and ep.domain:
                self.retain(
                    situation={"text": ep.input_summary, "domain": ep.domain},
                    solution=ep.output_summary,
                    outcome=CaseOutcome.SUCCESS,
                    outcome_text=f"源自阶段 {ep.phase} 的成功经验",
                    domain=ep.domain,
                    confidence=0.7,
                )
                imported += 1

        logger.info(f"从 EpisodicMemory 导入 {imported} 条成功案例")
        return imported
