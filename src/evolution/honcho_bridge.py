"""
HonchoBridge - Honcho Memory ↔ Clawra Engine 输入适配器

桥接层：将 Honcho 的自然语言 conclusions 转换为 Clawra Engine 的 facts 三元组格式。

设计原则：
1. 单向流动：Honcho → Bridge → Clawra Engine，不反向修改 Honcho
2. LLM 驱动：用 LLM 提取语义三元组，避免硬编码规则
3. 可插拔：作为 InputAdapter 接入 EvolutionLoop

使用方法：
    from src.evolution.honcho_bridge import HonchoBridge

    bridge = HonchoBridge()
    facts = bridge.extract_facts_from_conclusions([
        "用户不喜欢废话",
        "用户喜欢主动建议",
        "用户做决策时会权衡利弊",
    ])
    # → [{"subject": "用户", "predicate": "沟通偏好", "object": "简洁"}, ...]
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

from ..utils.config import get_config
from .llm_extractor import LLMKnowledgeExtractor, ExtractedRelation

logger = logging.getLogger(__name__)


@dataclass
class HonchoConclusion:
    """Honcho conclusions 的结构化表示"""
    content: str
    source: str = "honcho"  # 来源标记
    timestamp: Optional[float] = None


@dataclass
class CognitiveFact:
    """
    认知事实 - Honcho 到 Clawra 的中间表示

    与 Clawra Engine 的 Dict[str, Any] facts 格式兼容：
    {
        "subject": "用户",
        "predicate": "沟通偏好",
        "object": "简洁"
    }
    """
    subject: str
    predicate: str
    object: str
    confidence: float = 0.8
    source: str = "honcho_bridge"
    raw_conclusion: str = ""  # 保留原始 conclusion 用于审计


class HonchoBridge:
    """
    Honcho Memory → Clawra Engine 桥接器

    核心能力：
    1. 接收 Honcho conclusions（自然语言）
    2. 规则提取 facts（三元组）
    3. facts 直接转换为 LogicPattern，存入 UnifiedLogicLayer
    4. 不经过 discover_from_facts（该方法用于频繁模式挖掘，不适合单条偏好场景）
    """

    # 固定的 subject（因为是关于"用户"的认知）
    DEFAULT_SUBJECT = "用户"

    def __init__(self):
        """
        初始化桥接器，复用已有的 LLMKnowledgeExtractor
        """
        self._extractor = LLMKnowledgeExtractor()

    def extract_facts_from_conclusions(
        self, conclusions: List[str], subject: str = None
    ) -> List[Dict[str, Any]]:
        """
        主入口：将 Honcho conclusions 列表转换为 Clawra facts

        Args:
            conclusions: Honcho conclusions 自然语言列表
            subject: 默认 "用户"，可覆盖

        Returns:
            Clawra Engine 兼容的 facts 列表
            每个 fact 格式: {"subject": str, "predicate": str, "object": str}
        """
        if not conclusions:
            return []

        facts = []

        # 逐条处理，保持与 conclusion 的对应关系
        for conclusion in conclusions:
            extracted = self._extract_single(conclusion, subject)
            facts.extend(extracted)

        logger.info(
            f"HonchoBridge: {len(conclusions)} conclusions → {len(facts)} facts"
        )
        return facts

    def _extract_single(self, conclusion: str, subject: str = None) -> List[Dict[str, Any]]:
        """
        从单条 conclusion 提取三元组

        策略：规则优先，LLM 作为补充。
        由于 LLM 服务不稳定，默认使用增强版规则提取，
        仅在规则失败时尝试 LLM。
        """
        subject = subject or self.DEFAULT_SUBJECT

        # 规则提取（主要路径，完全本地，不依赖 LLM）
        facts = self._rule_based_extract(conclusion, subject)
        if facts:
            return facts

        # 规则失败 → 尝试 LLM（兜底）
        try:
            result = self._extractor.extract(conclusion, domain_hint="user_cognition")
            for relation in result.relations:
                facts.append({
                    "subject": subject,
                    "predicate": self._normalize_predicate(relation.predicate),
                    "object": relation.object,
                })
        except Exception:
            pass

        return facts

    def _normalize_predicate(self, predicate: str) -> str:
        """
        规范化 predicate，避免过于具体的词

        例如："沟通方式" → "沟通偏好"
        """
        normalize_map = {
            "沟通方式": "沟通偏好",
            "表达方式": "表达模式",
            "决策方式": "决策风格",
            "工作方式": "工作习惯",
        }
        return normalize_map.get(predicate, predicate)

    def _rule_based_extract(self, conclusion: str, subject: str) -> List[Dict[str, Any]]:
        """
        增强版规则提取：覆盖常见 conclusion 模式

        不依赖 LLM，完全本地规则匹配。
        覆盖：偏好类、行为类、风格类、期望类、边界类
        """
        import re
        facts = []
        conclusion = conclusion.strip()

        # ── 通用提取器 ──────────────────────────────
        # 模式: "用户(动词)X" → {subject, predicate, object}
        # 例: "用户不喜欢废话" → {不喜欢, 废话}

        # ── 偏好类 (喜欢/讨厌/在意/注重) ───────────
        # "用户在意X" / "用户注重X" / "用户喜欢X" / "用户讨厌X"
        pref_match = re.search(
            r'用户(?:喜欢|讨厌|不喜欢|在意|注重|偏好|崇尚)(.+)',
            conclusion
        )
        if pref_match:
            item = pref_match.group(1).strip().rstrip('。，、')
            # 根据关键词推断 predicate
            if any(k in conclusion for k in ['喜欢', '偏好', '崇尚']):
                pred = self._infer_predicate(item, "正向偏好")
            elif any(k in conclusion for k in ['讨厌', '不喜欢']):
                pred = self._infer_predicate(item, "负向偏好")
            else:
                pred = self._infer_predicate(item, "关注点")
            facts.append({"subject": subject, "predicate": pred, "object": item[:30]})
            return facts  # 匹配到了就返回，不重复匹配

        # ── 行为类 (会/总是/通常/倾向) ───────────────
        action_match = re.search(
            r'用户(?:会|总是|通常|倾向|习惯于)(.+)',
            conclusion
        )
        if action_match:
            item = action_match.group(1).strip().rstrip('。，、')
            pred = self._infer_predicate(item, "行为特征")
            facts.append({"subject": subject, "predicate": pred, "object": item[:30]})
            return facts

        # ── 决策类 (做决策时/决策风格/会先) ──────────
        decide_match = re.search(
            r'用户[做]?决策(?:时|风格|会先|倾向于)(.+)',
            conclusion
        )
        if decide_match:
            item = decide_match.group(1).strip().rstrip('。，、')
            facts.append({
                "subject": subject,
                "predicate": "决策风格",
                "object": item[:30]
            })
            return facts

        # ── 期望类 (希望/想要/期望) ──────────────────
        expect_match = re.search(
            r'用户(?:希望|想要|期望|要求)(.+)',
            conclusion
        )
        if expect_match:
            item = expect_match.group(1).strip().rstrip('。，、')
            facts.append({
                "subject": subject,
                "predicate": "期望行为",
                "object": item[:30]
            })
            return facts

        # ── 边界/红线类 (不能/不要/禁止/不接受) ──────
        boundary_match = re.search(
            r'用户(?:不能|不要|禁止|不接受|拒绝)(.+)',
            conclusion
        )
        if boundary_match:
            item = boundary_match.group(1).strip().rstrip('。，、')
            facts.append({
                "subject": subject,
                "predicate": "交互边界",
                "object": f"不接受{item[:25]}"
            })
            return facts

        # ── 描述类 (是/属于/表现为) ─────────────────
        desc_match = re.search(
            r'用户(?:是|属于|表现为|属于)(.+)',
            conclusion
        )
        if desc_match:
            item = desc_match.group(1).strip().rstrip('。，、')
            pred = self._infer_predicate(item, "风格特征")
            facts.append({"subject": subject, "predicate": pred, "object": item[:30]})

        return facts

    def _infer_predicate(self, object_text: str, fallback: str) -> str:
        """
        根据 object 内容推断合适的 predicate

        规则：
        - 涉及沟通/说话 → 沟通偏好
        - 涉及做事/方法/流程 → 工作习惯
        - 涉及感受/审美/视觉 → 审美偏好
        - 涉及决策/权衡/比较 → 决策风格
        - 涉及主动/被动/控制 → 行为特征
        - 默认 → fallback
        """
        text = object_text.lower()

        if any(k in text for k in ['废话', '简洁', '直接', '简明', '啰嗦', '话多']):
            return "沟通偏好"
        if any(k in text for k in ['对齐', '排版', '格式', '布局', '美观', '视觉']):
            return "审美偏好"
        if any(k in text for k in ['决策', '权衡', '比较', '分析', '信息']):
            return "决策风格"
        if any(k in text for k in ['主动', '被动', '等待', '催促']):
            return "行为特征"
        if any(k in text for k in ['学习', '理解', '接受', '反馈']):
            return "反馈响应"
        if any(k in text for k in ['个性', '灵动', '创意', '死板', '无聊']):
            return "风格偏好"
        return fallback

    def extract_single(self, conclusion: str) -> List[Dict[str, Any]]:
        """
        单条提取（便捷方法）
        """
        return self.extract_facts_from_conclusions([conclusion])

    def facts_to_patterns(
        self, facts: List[Dict[str, Any]]
    ) -> List["LogicPattern"]:
        """
        将 facts 转换为 LogicPattern（不经 discover）

        每个 fact 变成一个 BEHAVIOR 类型的 pattern。
        conditions = [fact]（当 subject=?X 满足时）
        actions = []（无操作，pattern 本身即知识）
        """
        from .unified_logic import LogicPattern, LogicType
        import hashlib

        patterns = []
        for fact in facts:
            # 生成稳定 ID
            fact_str = f"{fact['subject']}:{fact['predicate']}:{fact['object']}"
            pid = f"honcho:{hashlib.md5(fact_str.encode()).hexdigest()[:12]}"

            pattern = LogicPattern(
                id=pid,
                logic_type=LogicType.BEHAVIOR,
                name=f"{fact['subject']}-{fact['predicate']}",
                description=f"用户{fact['predicate']}：{fact['object']}",
                conditions=[fact],  # 当此 fact 成立时
                actions=[],  # 无操作，纯知识
                confidence=0.85,
                source="honcho",
                domain="user_cognition",
            )
            patterns.append(pattern)
        return patterns

    def store_as_patterns(
        self,
        facts: List[Dict[str, Any]],
        logic_layer: "UnifiedLogicLayer",
    ) -> List["LogicPattern"]:
        """
        将 facts 转换为 LogicPattern 并存入 UnifiedLogicLayer

        这是 bridge 的核心输出：把"关于用户的认知"永久存入推理系统。

        Returns:
            成功存入的 patterns 列表
        """
        patterns = self.facts_to_patterns(facts)
        stored = []
        for p in patterns:
            try:
                logic_layer.add_pattern(p)
                stored.append(p)
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"存入 pattern 失败: {e}")
        return stored

    def query_patterns(
        self,
        logic_layer: "UnifiedLogicLayer",
        predicate_filter: str = None,
        domain: str = "user_cognition",
    ) -> List["LogicPattern"]:
        """
        查询 LogicLayer 中的用户认知 patterns

        用于反馈循环：在响应用户前查询相关 patterns，
        将其转化为行为指导。

        Args:
            logic_layer: UnifiedLogicLayer 实例
            predicate_filter: 可选，只返回特定 predicate 的 patterns
            domain: 领域筛选，默认 user_cognition

        Returns:
            匹配的 LogicPattern 列表
        """
        results = []
        for pid, pattern in logic_layer.patterns.items():
            if pattern.domain != domain:
                continue
            if predicate_filter and pattern.name.split("-")[-1] != predicate_filter:
                # 检查 name 格式: "用户-沟通偏好"
                if predicate_filter not in pattern.name:
                    continue
            results.append(pattern)
        return results

    def patterns_to_guidance(
        self,
        patterns: List["LogicPattern"],
    ) -> str:
        """
        将 LogicPatterns 转换为自然语言行为指导

        用于注入到响应上下文中，让 AI Agent 遵循用户偏好。

        Returns:
            自然语言指导字符串，每行一条
        """
        lines = []
        for p in patterns:
            # 从 description 提取: "用户沟通偏好：简洁" → "保持沟通简洁"
            desc = p.description
            if "：" in desc:
                pred, obj = desc.split("：", 1)
                pred = pred.replace("用户", "")
                lines.append(f"- {pred}：{obj}（来源：{p.source}）")
        return "\n".join(lines)


# 便捷函数
def create_bridge() -> HonchoBridge:
    """工厂方法：创建 bridge 实例"""
    return HonchoBridge()


def conclusions_to_facts(
    conclusions: List[str],
    subject: str = "用户"
) -> List[Dict[str, Any]]:
    """
    快捷函数：将 conclusions 直接转换为 facts

    用法：
        facts = conclusions_to_facts([
            "用户不喜欢废话",
            "用户喜欢主动建议",
        ])
    """
    bridge = HonchoBridge()
    return bridge.extract_facts_from_conclusions(conclusions, subject)
