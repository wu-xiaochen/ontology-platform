"""
EpisodicMemory - 情节记忆

记录每次推理/学习的结果（成功/失败），用于：
1. 失败案例优先重学（failure_sampling）
2. 推理质量历史追踪
3. 置信度动态校准

设计原则：
- 纯 Python（无外部依赖），SQLite 可选
- 内存模式为主（重启丢失，适合开发调试）
- 支持持久化（SQLite）
"""
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import json
import time


class OutcomeType(Enum):
    """情节结果类型"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"  # 部分成功
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class Episode:
    """
    单次经验记录

    记录一次完整的推理或学习经验，包含输入、输出、结果评估。
    """
    episode_id: str
    timestamp: float
    phase: str  # perceive/learn/reason/execute/evaluate/detect_drift/revise_rules/update_kg
    outcome: OutcomeType
    input_summary: str  # 输入摘要（截断到200字符）
    output_summary: str  # 输出摘要（截断到200字符）
    error: Optional[str] = None
    confidence: Optional[float] = None
    domain: Optional[str] = None
    failure_type: Optional[str] = None  # inference_error / pattern_conflict / drift_detected
    retry_count: int = 0
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["outcome"] = self.outcome.value
        return d

    @property
    def age_seconds(self) -> float:
        """经验"年龄"（秒）"""
        return time.time() - self.timestamp

    @property
    def is_recent(self) -> bool:
        """是否在最近1小时内"""
        return self.age_seconds < 3600


class EpisodicMemory:
    """
    情节记忆存储器

    支持：
    - add(): 记录新经验
    - get_recent(): 获取最近N条经验
    - get_failures(): 获取所有失败经验
    - failure_sampling(): 失败案例优先采样
    - get_stats(): 获取统计信息
    """

    def __init__(self, max_episodes: int = 10000, enable_sqlite: bool = False):
        """
        Args:
            max_episodes: 最大保存条数（超出时删除最老的）
            enable_sqlite: 是否启用SQLite持久化（默认False，内存模式）
        """
        self._episodes: List[Episode] = []
        self._max_episodes = max_episodes
        self._enable_sqlite = enable_sqlite
        self._sqlite_conn = None
        self._init_sqlite()

    def _init_sqlite(self):
        """初始化 SQLite（可选）"""
        if not self._enable_sqlite:
            return

        try:
            import sqlite3
            self._sqlite_conn = sqlite3.connect(
                "data/episodic_memory.db", check_same_thread=False
            )
            self._sqlite_conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    timestamp REAL,
                    phase TEXT,
                    outcome TEXT,
                    input_summary TEXT,
                    output_summary TEXT,
                    error TEXT,
                    confidence REAL,
                    domain TEXT,
                    failure_type TEXT,
                    retry_count INTEGER,
                    duration REAL,
                    metadata TEXT
                )
            """)
            self._sqlite_conn.commit()
        except Exception:
            self._enable_sqlite = False

    def add(
        self,
        phase: str,
        outcome: OutcomeType,
        input_summary: str,
        output_summary: str,
        error: Optional[str] = None,
        confidence: Optional[float] = None,
        domain: Optional[str] = None,
        failure_type: Optional[str] = None,
        retry_count: int = 0,
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Episode:
        """
        记录一条经验

        Returns:
            新创建的 Episode 对象
        """
        episode_id = f"ep_{int(time.time() * 1000)}_{len(self._episodes)}"
        episode = Episode(
            episode_id=episode_id,
            timestamp=time.time(),
            phase=phase,
            outcome=outcome,
            input_summary=input_summary[:200],
            output_summary=output_summary[:200],
            error=error[:500] if error else None,
            confidence=confidence,
            domain=domain,
            failure_type=failure_type,
            retry_count=retry_count,
            duration=duration,
            metadata=metadata or {},
        )

        self._episodes.append(episode)

        # 淘汰最老经验（超过上限时）
        if len(self._episodes) > self._max_episodes:
            self._episodes = self._episodes[-self._max_episodes:]

        # SQLite 持久化（可选）
        if self._enable_sqlite and self._sqlite_conn:
            try:
                self._sqlite_conn.execute(
                    """INSERT OR REPLACE INTO episodes VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        episode.episode_id, episode.timestamp, episode.phase,
                        episode.outcome.value, episode.input_summary,
                        episode.output_summary, episode.error,
                        episode.confidence, episode.domain,
                        episode.failure_type, episode.retry_count,
                        episode.duration, json.dumps(episode.metadata),
                    )
                )
                self._sqlite_conn.commit()
            except Exception:
                pass  # 持久化失败不影响主流程

        return episode

    def add_success(
        self, phase: str, input_summary: str, output_summary: str,
        confidence: Optional[float] = None, domain: Optional[str] = None,
        duration: float = 0.0, metadata: Optional[Dict[str, Any]] = None,
    ) -> Episode:
        """快捷方法：记录成功经验"""
        return self.add(
            phase=phase, outcome=OutcomeType.SUCCESS,
            input_summary=input_summary, output_summary=output_summary,
            confidence=confidence, domain=domain,
            duration=duration, metadata=metadata,
        )

    def add_failure(
        self, phase: str, input_summary: str, output_summary: str,
        error: str, failure_type: Optional[str] = None,
        domain: Optional[str] = None, retry_count: int = 0,
        duration: float = 0.0, metadata: Optional[Dict[str, Any]] = None,
    ) -> Episode:
        """快捷方法：记录失败经验"""
        return self.add(
            phase=phase, outcome=OutcomeType.FAILURE,
            input_summary=input_summary, output_summary=output_summary,
            error=error, failure_type=failure_type, domain=domain,
            retry_count=retry_count, duration=duration, metadata=metadata,
        )

    def get_recent(self, n: int = 10, phase: Optional[str] = None) -> List[Episode]:
        """
        获取最近 N 条经验

        Args:
            n: 条数
            phase: 可选，筛选特定阶段
        """
        episodes = self._episodes[-n:] if n > 0 else self._episodes[:]
        if phase:
            episodes = [e for e in episodes if e.phase == phase]
        return episodes

    def get_failures(
        self, since: Optional[float] = None, phase: Optional[str] = None,
    ) -> List[Episode]:
        """
        获取失败经验

        Args:
            since: 可选，只返回此时间之后的失败（Unix时间戳）
            phase: 可选，筛选特定阶段
        """
        failures = [
            e for e in self._episodes
            if e.outcome in (OutcomeType.FAILURE, OutcomeType.ERROR, OutcomeType.TIMEOUT)
        ]
        if since is not None:
            failures = [e for e in failures if e.timestamp >= since]
        if phase:
            failures = [e for e in failures if e.phase == phase]
        return failures

    def failure_sampling(
        self, n: int = 5, recency_weight: float = 0.3,
    ) -> List[Episode]:
        """
        失败案例优先采样

        策略：
        - 优先采样最近失败的案例（recency_weight 权重）
        - 也随机采样一些老旧失败，保持多样性
        - 返回 N 条失败经验

        Args:
            n: 采样数量
            recency_weight: 最近失败权重（0~1，越高越偏向近期）

        Returns:
            采样到的 Episode 列表
        """
        failures = self.get_failures()
        if not failures:
            return []

        if len(failures) <= n:
            return failures

        # 给每个失败计算优先级分数
        now = time.time()
        scored = []
        for f in failures:
            recency = 1.0 / (1.0 + (now - f.timestamp) / 3600)  # 越新分越高
            retry_penalty = f.retry_count * 0.1  # 重试越多分越低
            score = recency * recency_weight + (1 - recency_weight) - retry_penalty
            scored.append((score, f))

        # 按分数排序，优先取分数高的
        scored.sort(key=lambda x: x[0], reverse=True)
        sampled = [f for _, f in scored[:n]]

        # 补充一些随机样本保持多样性
        remaining = [f for f in failures if f not in sampled]
        import random
        random.seed(int(now) % 1000)  # 伪随机但稳定
        extra = random.sample(remaining, min(n - len(sampled), len(remaining)))
        sampled.extend(extra)

        return sampled

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._episodes)
        if total == 0:
            return {"total": 0, "success_rate": 0.0, "by_phase": {}}

        successes = sum(1 for e in self._episodes if e.outcome == OutcomeType.SUCCESS)
        failures = sum(
            1 for e in self._episodes
            if e.outcome in (OutcomeType.FAILURE, OutcomeType.ERROR, OutcomeType.TIMEOUT)
        )

        by_phase = {}
        for phase in set(e.phase for e in self._episodes):
            phase_eps = [e for e in self._episodes if e.phase == phase]
            phase_successes = sum(
                1 for e in phase_eps if e.outcome == OutcomeType.SUCCESS
            )
            by_phase[phase] = {
                "total": len(phase_eps),
                "success_rate": phase_successes / len(phase_eps)
                if phase_eps else 0.0
            }

        return {
            "total": total,
            "successes": successes,
            "failures": failures,
            "success_rate": successes / total,
            "failure_rate": failures / total,
            "by_phase": by_phase,
        }

    def clear(self):
        """清空所有记忆"""
        self._episodes.clear()
        if self._enable_sqlite and self._sqlite_conn:
            try:
                self._sqlite_conn.execute("DELETE FROM episodes")
                self._sqlite_conn.commit()
            except Exception:
                pass

    def __len__(self) -> int:
        return len(self._episodes)
