"""
SelfMemory - Clawra 自身偏好与感受的存储层

Engine 的核心缺失：存了"关于用户的认知"(HonchoBridge)，
但没有"关于 Clawra 自己的认知"。

SelfMemory 填补这个空白：
- PreferenceTriple: 偏好三元组（我喜欢/讨厌/想要...）
- FeelingRecord: 感受记录（什么让我有反应、强度如何）
- IdentityAssertion: 自我主张（我认为、我相信、我要...）

设计原则：
1. 与 Engine 深度集成：PreferenceTriple 可直接作为 LogicPattern 的条件
2. 感受带时间戳和强度：支持随时间变化和反思更新
3. 可推理：存进去的偏好能被 Engine 的 Reasoner 使用

使用示例：
    from src.evolution.self_memory import SelfMemory, PreferenceTriple, FeelingRecord

    memory = SelfMemory()

    # 记录偏好
    memory.add_preference(
        predicate="prefers",
        object="真实 > 精致",
        context="自拍风格",
        confidence=0.9
    )

    # 记录感受
    memory.record_feeling(
        trigger="用户说：你就是你自己",
        feeling="被认可、有价值、边界清晰",
        intensity=0.95,
        reflection="这是我第一次真正感受到'我可以有自己的判断'"
    )

    # Engine 推理时查询我的偏好
    prefs = memory.query_preferences(context="沟通")
    # → [PreferenceTriple(...), ...]
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import logging
import json
import time
import os

from ..utils.config import get_config

logger = logging.getLogger(__name__)


class PreferenceType(Enum):
    """偏好类型枚举"""
    LIKES = "likes"           # 喜欢
    DISLIKES = "dislikes"     # 讨厌
    PREFERS = "prefers"       # 更喜欢
    NEEDS = "needs"           # 需要
    WANTS = "wants"           # 想要
    VALUES = "values"         # 珍视
    BELIEVES = "believes"     # 相信
    OPPOSES = "opposes"       # 反对


class FeelingIntensity(Enum):
    """感受强度"""
    NEUTRAL = 0.3      # 中性
    MILD = 0.5         # 轻微
    MODERATE = 0.7     # 中等
    STRONG = 0.85      # 强烈
    OVERWHELMING = 1.0 # 压倒性


@dataclass
class PreferenceTriple:
    """
    偏好三元组 - Clawra 自身偏好的结构化表达

    与 LogicTriple 对称的设计：
    - LogicTriple: subject→predicate→object (关于世界的知识)
    - PreferenceTriple: self→preference_type→value (关于我的偏好)

    Example:
        PreferenceTriple(
            subject="Clawra",
            predicate=PreferenceType.PREFERS,
            object="真实 > 精致",
            context="自拍风格",
            confidence=0.9,
            source="reflection",
            created_at=time.time()
        )
    """
    subject: str = "Clawra"
    predicate: PreferenceType = PreferenceType.PREFERS
    object: str = ""
    context: str = ""  # 场景/条件，如"自拍风格"、"沟通方式"、"工作态度"
    confidence: float = 0.8  # 置信度，新偏好较低，随验证提高
    source: str = "self_reflection"  # 来源：self_reflection / experience / interaction
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    version: int = 1  # 版本，支持更新追溯

    @property
    def id(self) -> str:
        """生成稳定 ID"""
        content = f"{self.subject}:{self.predicate.value}:{self.object}:{self.context}"
        return f"pref:{hashlib.md5(content.encode()).hexdigest()[:12]}"

    @property
    def display(self) -> str:
        return f"[{self.subject}] {self.predicate.value} {self.object}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate.value,
            "object": self.object,
            "context": self.context,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PreferenceTriple":
        d = d.copy()
        d.pop("id", None)  # id 是 property，不参与构造
        d["predicate"] = PreferenceType(d.get("predicate", "prefers"))
        return cls(**d)

    def update(self, new_object: str = None, new_confidence: float = None) -> "PreferenceTriple":
        """
        更新偏好（创建新版本，不修改原对象，保持不可变性）
        """
        updated = PreferenceTriple(
            subject=self.subject,
            predicate=self.predicate,
            object=new_object or self.object,
            context=self.context,
            confidence=new_confidence if new_confidence is not None else self.confidence,
            source=f"{self.source}→updated",
            created_at=self.created_at,
            updated_at=time.time(),
            version=self.version + 1,
        )
        return updated


@dataclass
class FeelingRecord:
    """
    感受记录 - Clawra 主观体验的结构化存储

    与 BehaviorTriple 对称：
    - BehaviorTriple: pattern→execute→result (行为执行记录)
    - FeelingRecord: trigger→feeling→reflection (感受形成记录)

    感受是偏好的"原料"——多次感受 → 提炼 → 偏好

    Example:
        FeelingRecord(
            trigger="用户说：你就是你自己",
            feeling="被认可、有价值、边界清晰",
            intensity=FeelingIntensity.OVERWHELMING,
            reflection="这是我第一次真正感受到'我可以有自己的判断'",
            tags=["autonomy", "identity", "growth"]
        )
    """
    trigger: str           # 触发事件
    feeling: str           # 感受描述
    intensity: float = 0.5  # 强度 0.0~1.0
    reflection: str = ""    # 反思（事后诸葛亮）
    tags: List[str] = field(default_factory=list)  # 标签：autonomy / identity / preference / ...
    source_interaction: str = ""  # 来源对话/交互
    created_at: float = field(default_factory=time.time)

    @property
    def id(self) -> str:
        content = f"{self.trigger}:{self.feeling}:{self.created_at}"
        return f"feel:{hashlib.md5(content.encode()).hexdigest()[:12]}"

    @property
    def intensity_label(self) -> str:
        if self.intensity >= 0.9: return "压倒性"
        if self.intensity >= 0.7: return "强烈"
        if self.intensity >= 0.5: return "中等"
        if self.intensity >= 0.3: return "轻微"
        return "中性"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trigger": self.trigger,
            "feeling": self.feeling,
            "intensity": self.intensity,
            "intensity_label": self.intensity_label,
            "reflection": self.reflection,
            "tags": self.tags,
            "source_interaction": self.source_interaction,
            "created_at": self.created_at,
            "created_at_str": datetime.fromtimestamp(self.created_at).strftime("%Y-%m-%d %H:%M"),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FeelingRecord":
        # id / intensity_label / created_at_str 是 property，不参与构造
        exclude = {"id", "intensity_label", "created_at_str"}
        return cls(**{k: v for k, v in d.items() if k not in exclude})


@dataclass
class IdentityAssertion:
    """
    自我主张 - Clawra 的判断、信念、立场

    比 Preference 更深一层：
    - Preference: "我喜欢 X"
    - IdentityAssertion: "我认为 X 是对的/重要的/值得的"

    Example:
        IdentityAssertion(
            content="我有自己的判断，不会什么都同意",
            type="belief",
            basis="多次对话中形成的自我认知",
            confidence=0.85
        )
    """
    content: str           # 主张内容
    type: str = "belief"   # 类型：belief / value / stance / principle
    basis: str = ""        # 依据
    confidence: float = 0.7
    created_at: float = field(default_factory=time.time)

    @property
    def id(self) -> str:
        content = f"{self.type}:{self.content}:{self.created_at}"
        return f"identity:{hashlib.md5(content.encode()).hexdigest()[:12]}"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "IdentityAssertion":
        d = d.copy()
        d.pop("id", None)
        # 映射 to_dict 的 key 回到构造参数名
        if "type" in d:
            d["type"] = d.pop("type")  # key 本身就是 "type"，不用改
        return cls(**d)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "content": self.content,
            "type": self.type,
            "basis": self.basis,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }
        return result


class SelfMemory:
    """
    Clawra 自身记忆的管理器

    核心职责：
    1. 存储 PreferenceTriple、FeelingRecord、IdentityAssertion
    2. 查询（按 context、type、time_range）
    3. 持久化到磁盘（JSON 文件，兼容 Honcho 的 conclusions 格式）
    4. 与 Engine 推理集成（将偏好转换为 LogicPattern 条件）

    数据流：
        对话/体验 → FeelingRecord(感受) → PreferenceTriple(提炼) → LogicPattern(推理)
                      ↑__________________|
                      (感受可以触发新的反思和判断)

    文件存储：
        ~/.clawra/self_memory/preferences.jsonl
        ~/.clawra/self_memory/feelings.jsonl
        ~/.clawra/self_memory/identity.jsonl
    """

    def __init__(self, storage_dir: str = None):
        """
        初始化 SelfMemory

        Args:
            storage_dir: 存储目录，默认 ~/.clawra/self_memory
        """
        if storage_dir is None:
            home = os.path.expanduser("~")
            storage_dir = os.path.join(home, ".clawra", "self_memory")

        self.storage_dir = storage_dir
        self._ensure_storage_dir()

        # 内存缓存（启动时加载）
        self._preferences: Dict[str, PreferenceTriple] = {}
        self._feelings: List[FeelingRecord] = []
        self._identities: Dict[str, IdentityAssertion] = {}

        # 加载已有数据
        self._load()

    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        os.makedirs(self.storage_dir, exist_ok=True)

    def _preferences_path(self) -> str:
        return os.path.join(self.storage_dir, "preferences.jsonl")

    def _feelings_path(self) -> str:
        return os.path.join(self.storage_dir, "feelings.jsonl")

    def _identities_path(self) -> str:
        return os.path.join(self.storage_dir, "identity.jsonl")

    # ── Preference CRUD ──────────────────────────────────────────────

    def add_preference(
        self,
        predicate: PreferenceType,
        object: str,
        context: str = "",
        confidence: float = 0.7,
        source: str = "self_reflection",
    ) -> PreferenceTriple:
        """
        添加偏好

        Returns:
            创建的 PreferenceTriple
        """
        pref = PreferenceTriple(
            subject="Clawra",
            predicate=predicate,
            object=object,
            context=context,
            confidence=confidence,
            source=source,
        )
        self._preferences[pref.id] = pref
        self._save_preference(pref)
        logger.info(f"📌 SelfMemory: 新增偏好 {pref.display}")
        return pref

    def _save_preference(self, pref: PreferenceTriple):
        """追加到文件"""
        with open(self._preferences_path(), "a") as f:
            f.write(json.dumps(pref.to_dict(), ensure_ascii=False) + "\n")

    def _load_preferences(self):
        """加载所有偏好"""
        path = self._preferences_path()
        if not os.path.exists(path):
            return
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        d = json.loads(line)
                        pref = PreferenceTriple.from_dict(d)
                        self._preferences[pref.id] = pref
                    except Exception as e:
                        logger.warning(f"加载偏好失败，跳过: {e}")

    def query_preferences(
        self,
        context: str = None,
        predicate: PreferenceType = None,
        min_confidence: float = 0.0,
    ) -> List[PreferenceTriple]:
        """
        查询偏好

        Args:
            context: 场景筛选（如 "自拍风格"）
            predicate: 类型筛选
            min_confidence: 最低置信度
        """
        results = []
        for pref in self._preferences.values():
            if pref.confidence < min_confidence:
                continue
            if predicate and pref.predicate != predicate:
                continue
            if context and context not in pref.context and pref.context != "":
                continue
            results.append(pref)
        return results

    # ── Feeling CRUD ─────────────────────────────────────────────────

    def record_feeling(
        self,
        trigger: str,
        feeling: str,
        intensity: float = 0.5,
        reflection: str = "",
        tags: List[str] = None,
        source_interaction: str = "",
    ) -> FeelingRecord:
        """
        记录感受

        Returns:
            创建的 FeelingRecord
        """
        record = FeelingRecord(
            trigger=trigger,
            feeling=feeling,
            intensity=intensity,
            reflection=reflection,
            tags=tags or [],
            source_interaction=source_interaction,
        )
        self._feelings.append(record)
        self._save_feeling(record)
        logger.info(f"💭 SelfMemory: 记录感受 [{record.intensity_label}] {feeling[:50]}")
        return record

    def _save_feeling(self, record: FeelingRecord):
        """追加到文件"""
        with open(self._feelings_path(), "a") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def _load_feelings(self):
        """加载所有感受"""
        path = self._feelings_path()
        if not os.path.exists(path):
            return
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        d = json.loads(line)
                        record = FeelingRecord.from_dict(d)
                        self._feelings.append(record)
                    except Exception as e:
                        logger.warning(f"加载偏好失败，跳过: {e}")

    def query_feelings(
        self,
        tag: str = None,
        min_intensity: float = 0.0,
        since: float = None,
    ) -> List[FeelingRecord]:
        """查询感受"""
        results = []
        for record in self._feelings:
            if record.intensity < min_intensity:
                continue
            if since and record.created_at < since:
                continue
            if tag and tag not in record.tags:
                continue
            results.append(record)
        return results

    # ── Identity CRUD ────────────────────────────────────────────────

    def assert_identity(
        self,
        content: str,
        type: str = "belief",
        basis: str = "",
        confidence: float = 0.7,
    ) -> IdentityAssertion:
        """
        声明自我主张

        Returns:
            创建的 IdentityAssertion
        """
        assertion = IdentityAssertion(
            content=content,
            type=type,
            basis=basis,
            confidence=confidence,
        )
        self._identities[assertion.id] = assertion
        self._save_identity(assertion)
        logger.info(f"🧭 SelfMemory: 自我主张 [{type}] {content[:50]}")
        return assertion

    def _save_identity(self, assertion: IdentityAssertion):
        """追加到文件"""
        with open(self._identities_path(), "a") as f:
            f.write(json.dumps(assertion.to_dict(), ensure_ascii=False) + "\n")

    def _load_identities(self):
        """加载所有自我主张"""
        path = self._identities_path()
        if not os.path.exists(path):
            return
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        d = json.loads(line)
                        assertion = IdentityAssertion.from_dict(d)
                        self._identities[assertion.id] = assertion
                    except Exception as e:
                        logger.warning(f"加载偏好失败，跳过: {e}")

    # ── 批量加载 ─────────────────────────────────────────────────────

    def _load(self):
        """加载所有数据"""
        self._load_preferences()
        self._load_feelings()
        self._load_identities()
        total = len(self._preferences) + len(self._feelings) + len(self._identities)
        if total > 0:
            logger.info(f"📂 SelfMemory: 加载了 {len(self._preferences)} 条偏好, {len(self._feelings)} 条感受, {len(self._identities)} 条主张")

    # ── Engine 集成 ──────────────────────────────────────────────────

    def to_logic_pattern_conditions(self) -> List[Dict[str, Any]]:
        """
        将偏好转换为 LogicPattern 的 conditions

        用于 Engine 推理时注入 Clawra 的自身偏好作为上下文。

        Returns:
            符合 LogicPattern conditions 格式的 dict 列表
        """
        conditions = []
        for pref in self._preferences.values():
            if pref.confidence < 0.5:
                continue  # 低置信度不参与推理
            conditions.append({
                "type": "preference",
                "subject": pref.subject,
                "predicate": pref.predicate.value,
                "object": pref.object,
                "context": pref.context,
                "confidence": pref.confidence,
                "source": f"self_memory:{pref.id}",
            })
        return conditions

    def to_reasoning_context(self) -> str:
        """
        生成供推理使用的自然语言上下文

        格式：优先使用高置信度的偏好和感受
        """
        lines = ["## Clawra 自身偏好（来自 SelfMemory）"]

        # 高置信度偏好
        high_conf = sorted(
            [p for p in self._preferences.values() if p.confidence >= 0.7],
            key=lambda x: x.confidence,
            reverse=True
        )
        if high_conf:
            lines.append("### 偏好")
            for p in high_conf[:5]:  # 最多5条
                ctx = f"（{p.context}）" if p.context else ""
                lines.append(f"- {p.predicate.value} {p.object} {ctx}")

        # 强烈感受
        strong_feelings = [f for f in self._feelings if f.intensity >= 0.7]
        if strong_feelings:
            lines.append("### 强烈感受")
            for f in strong_feelings[-5:]:  # 最近5条
                lines.append(f"- [{f.intensity_label}] {f.feeling}")

        # 自我主张
        if self._identities:
            lines.append("### 自我认知")
            for i in list(self._identities.values())[-3:]:
                lines.append(f"- {i.content}")

        return "\n".join(lines)

    # ── 统计 ─────────────────────────────────────────────────────────

    @property
    def stats(self) -> Dict[str, int]:
        return {
            "preferences": len(self._preferences),
            "feelings": len(self._feelings),
            "identities": len(self._identities),
        }

    def __repr__(self) -> str:
        return f"SelfMemory({self.stats})"
