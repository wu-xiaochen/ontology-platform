"""
Pattern Versioning - 逻辑模式版本控制系统

为 LogicPattern 提供版本历史、分支、A/B 测试、Rollback 和相似度去重能力。

主要功能：
1. PatternVersion: 单个版本记录（content + metadata + confidence + source）
2. PatternHistory: 每个 pattern 的完整版本历史
3. PatternBranching: A/B 测试分支管理
4. PatternRollback: 安全回滚（完整性检查）
5. SimilarityDeduplication: 规则相似度去重（Jaccard + 语义向量）

依赖：
- openai>=1.0（语义相似度，可选，有 fallback）
- numpy（向量计算，可选）
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import hashlib
import copy
import logging

logger = logging.getLogger(__name__)

# 延迟导入可选依赖
_openai_available = False
_numpy_available = False

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    pass

try:
    import numpy as np
    _numpy_available = True
except ImportError:
    pass


class ChangeType(Enum):
    """变更类型"""
    CREATED = "created"
    UPDATED = "updated"
    DEPRECATED = "deprecated"
    MERGED = "merged"
    ROLLED_BACK = "rolled_back"
    BRANCHED = "branched"


@dataclass
class PatternVersion:
    """
    单个版本记录

    记录 pattern 的某一个版本快照，包含内容、元数据、来源和置信度。
    """
    version: str  # 语义版本，如 "1.0.0", "1.1.0"
    content: Dict[str, Any]  # 版本内容（LogicPattern 的核心字段快照）
    metadata: Dict[str, Any]  # 版本元数据（author, timestamp, tags 等）
    source: str = "manual"  # 来源：manual / auto_merge / discovery / meta_learn
    confidence: float = 0.8  # 置信度 0~1
    change_type: ChangeType = ChangeType.CREATED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
            "confidence": self.confidence,
            "change_type": self.change_type.value,
        }


@dataclass
class PatternHistory:
    """
    单个 Pattern 的版本历史

    管理一个 LogicPattern 从创建到当前的所有版本。
    """
    pattern_id: str
    current_version: str = "0.0.0"
    versions: Dict[str, PatternVersion] = field(default_factory=dict)
    _history: List[PatternVersion] = field(default_factory=list)

    def add_version(
        self,
        version: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "manual",
        confidence: float = 0.8,
        change_type: ChangeType = ChangeType.UPDATED,
    ) -> PatternVersion:
        """添加一个新版本"""
        if metadata is None:
            metadata = {}

        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()

        pv = PatternVersion(
            version=version,
            content=content,
            metadata=metadata,
            source=source,
            confidence=confidence,
            change_type=change_type,
        )

        self.versions[version] = pv
        self._history.append(pv)
        self.current_version = version

        return pv

    def get_version(self, version: str) -> Optional[PatternVersion]:
        """获取指定版本"""
        return self.versions.get(version)

    def get_history(self) -> List[PatternVersion]:
        """获取完整版本历史（按时间顺序）"""
        return list(self._history)

    def rollback_candidates(self) -> List[PatternVersion]:
        """获取可回滚的版本列表（排除当前版本）"""
        return [v for v in self._history if v.version != self.current_version]

    def get_latest_stable(self) -> Optional[PatternVersion]:
        """获取最新稳定版本（deprecated 除外）"""
        candidates = [
            v for v in reversed(self._history)
            if v.change_type != ChangeType.DEPRECATED
        ]
        return candidates[0] if candidates else None


@dataclass
class PatternBranching:
    """
    Pattern A/B 测试分支管理器

    支持为一个 base pattern 创建实验分支，对比不同版本的效果。
    """
    base_pattern_id: str
    branches: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # branches[branch_name] = {"pattern_id": "...", "metric": {...}, "active": True}

    def create_branch(
        self,
        branch_name: str,
        pattern_id: str,
        variant_content: Dict[str, Any],
    ) -> str:
        """创建实验分支"""
        self.branches[branch_name] = {
            "pattern_id": pattern_id,
            "variant_content": variant_content,
            "metric": {},
            "active": True,
            "created_at": datetime.now().isoformat(),
        }
        return branch_name

    def record_metric(self, branch_name: str, metric_name: str, value: float):
        """记录分支效果指标"""
        if branch_name in self.branches:
            if "metric" not in self.branches[branch_name]:
                self.branches[branch_name]["metric"] = {}
            self.branches[branch_name]["metric"][metric_name] = value

    def get_best_branch(self, metric_name: str) -> Optional[str]:
        """获取指标最优分支"""
        candidates = [
            (name, data["metric"].get(metric_name, 0))
            for name, data in self.branches.items()
            if data.get("active") and metric_name in data.get("metric", {})
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda x: x[1])[0]

    def merge_branch(self, branch_name: str) -> bool:
        """标记分支已合并"""
        if branch_name in self.branches:
            self.branches[branch_name]["active"] = False
            self.branches[branch_name]["merged_at"] = datetime.now().isoformat()
            return True
        return False


class PatternRollback:
    """
    安全回滚器

    回滚前进行完整性检查，确保不会回滚到损坏或不稳定的版本。
    """

    def __init__(self, pattern_history: PatternHistory):
        self._history = pattern_history

    def validate_version(self, version: str) -> Tuple[bool, str]:
        """
        验证版本是否可回滚

        Returns:
            (is_valid, reason)
        """
        pv = self._history.get_version(version)
        if not pv:
            return False, f"版本 {version} 不存在"

        # 不允许回滚到 deprecated 版本
        if pv.change_type == ChangeType.DEPRECATED:
            return False, f"版本 {version} 已废弃，不能回滚"

        # 不允许回滚到内容为空的版本
        if not pv.content or len(pv.content) == 0:
            return False, f"版本 {version} 内容为空"

        # 检查必需字段（基于 LogicPattern 的核心字段）
        required_fields = ["id", "logic_type", "name"]
        missing = [f for f in required_fields if f not in pv.content]
        if missing:
            return False, f"版本 {version} 缺少必需字段: {missing}"

        return True, "OK"

    def rollback_to(self, version: str) -> Tuple[bool, str, Optional[PatternVersion]]:
        """
        执行回滚

        Returns:
            (success, message, version_data)
        """
        is_valid, reason = self.validate_version(version)
        if not is_valid:
            return False, reason, None

        pv = self._history.get_version(version)

        # 创建新的回滚版本记录
        rollback_content = copy.deepcopy(pv.content)
        rollback_version = f"{version}-rollback-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        self._history.add_version(
            version=rollback_version,
            content=rollback_content,
            metadata={"rolled_back_from": self._history.current_version},
            source="rollback",
            confidence=pv.confidence,
            change_type=ChangeType.ROLLED_BACK,
        )

        return True, f"成功回滚到版本 {version}", pv


class SimilarityDeduplication:
    """
    规则相似度去重器

    使用两种策略结合：
    1. Jaccard 相似度（基于逻辑结构）
    2. 语义向量相似度（基于 OpenAI embedding，可选）
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        use_semantic: bool = True,
        openai_api_key: Optional[str] = None,
    ):
        """
        Args:
            similarity_threshold: 相似度阈值，超过此值则合并（默认 0.85）
            use_semantic: 是否使用语义相似度（需要 OpenAI API）
            openai_api_key: OpenAI API Key（可选，从环境变量 OPENAI_API_KEY 读取）
        """
        self._threshold = similarity_threshold
        self._use_semantic = use_semantic and _openai_available

        if self._use_semantic:
            import os
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self._openai_client = OpenAI(api_key=api_key)
            else:
                self._use_semantic = False
                logger.warning("未提供 OpenAI API Key，语义相似度功能不可用")

    def _compute_jaccard(self, a: Dict[str, Any], b: Dict[str, Any]) -> float:
        """
        计算 Jaccard 相似度（基于逻辑结构）

        比较两个 pattern 的 conditions、actions、logic_type 等核心结构字段。
        排除 id 字段（仅标识符，不反映语义相似性）。
        """
        IGNORED_FIELDS = {"id", "metadata", "version", "source"}

        def extract_keys(d: Dict, prefix: str = "") -> set:
            """扁平化提取所有 key-value 对为可哈希集合（排除 id 等标识符）"""
            result = set()
            for k, v in d.items():
                if k in IGNORED_FIELDS:
                    continue
                key = f"{prefix}{k}"
                if isinstance(v, dict):
                    result.update(extract_keys(v, f"{key}."))
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            result.update(extract_keys(item, f"{key}[]."))
                        else:
                            result.add(f"{key}[]={item}")
                else:
                    result.add(f"{key}={v}")
            return result

        keys_a = extract_keys(a)
        keys_b = extract_keys(b)

        if not keys_a and not keys_b:
            return 1.0

        intersection = keys_a & keys_b
        union = keys_a | keys_b

        return len(intersection) / len(union) if union else 0.0

    def _compute_semantic_similarity(
        self, text_a: str, text_b: str
    ) -> float:
        """
        计算语义相似度（基于 OpenAI embedding）

        Returns:
            余弦相似度 0~1
        """
        if not self._use_semantic or not hasattr(self, "_openai_client"):
            return 0.0

        try:
            emb_a = self._openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text_a
            )
            emb_b = self._openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text_b
            )

            vec_a = emb_a.data[0].embedding
            vec_b = emb_b.data[0].embedding

            if not _numpy_available:
                # 纯 Python 余弦相似度
                dot = sum(x * y for x, y in zip(vec_a, vec_b))
                norm_a = sum(x * x for x in vec_a) ** 0.5
                norm_b = sum(x * x for x in vec_b) ** 0.5
                return dot / (norm_a * norm_b) if (norm_a * norm_b) > 0 else 0.0

            vec_a = np.array(vec_a)
            vec_b = np.array(vec_b)
            return float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)))

        except Exception as e:
            logger.debug(f"语义相似度计算失败: {e}")
            return 0.0

    def compute_similarity(
        self,
        pattern_a: Dict[str, Any],
        pattern_b: Dict[str, Any],
    ) -> float:
        """
        计算两个 pattern 的综合相似度

        策略：Jaccard(权重 0.4) + 语义(权重 0.6)
        如果语义不可用，只用 Jaccard。

        Returns:
            0~1 的相似度分数
        """
        jaccard = self._compute_jaccard(pattern_a, pattern_b)

        if not self._use_semantic:
            return jaccard

        # 提取文本描述用于语义相似度
        text_a = self._pattern_to_text(pattern_a)
        text_b = self._pattern_to_text(pattern_b)
        semantic = self._compute_semantic_similarity(text_a, text_b)

        return jaccard * 0.4 + semantic * 0.6

    def _pattern_to_text(self, pattern: Dict[str, Any]) -> str:
        """将 pattern 转换为文本描述"""
        parts = []
        parts.append(pattern.get("name", ""))
        parts.append(pattern.get("description", ""))

        for cond in pattern.get("conditions", []):
            parts.append(str(cond))

        for action in pattern.get("actions", []):
            parts.append(str(action))

        return " | ".join(parts)

    def deduplicate(
        self,
        patterns: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        对 pattern 列表进行去重

        策略：按相似度聚类，每类只保留置信度最高的 pattern。

        Returns:
            去重后的 pattern 列表
        """
        if len(patterns) <= 1:
            return patterns

        keep = []
        remove_ids = set()

        for i, pa in enumerate(patterns):
            if pa.get("id") in remove_ids:
                continue

            cluster = [pa]

            for j, pb in enumerate(patterns[i + 1:], i + 1):
                if pb.get("id") in remove_ids:
                    continue

                sim = self.compute_similarity(pa, pb)
                if sim >= self._threshold:
                    cluster.append(pb)
                    remove_ids.add(pb.get("id"))

            # 每类只保留置信度最高的
            best = max(cluster, key=lambda p: p.get("confidence", 0.8))
            keep.append(best)

        logger.info(
            f"去重完成: 输入 {len(patterns)} 个 pattern，"
            f"输出 {len(keep)} 个，合并了 {len(patterns) - len(keep)} 对"
        )

        return keep

    def merge_similar_patterns(
        self,
        patterns: List[Dict[str, Any]],
        keep_metadata: bool = True,
    ) -> Tuple[List[Dict[str, Any]], List[Tuple[int, int]]]:
        """
        合并相似 pattern

        Args:
            patterns: pattern 列表
            keep_metadata: 合并时保留被合并 pattern 的元数据

        Returns:
            (merged_patterns, merge_pairs) — 合并后的列表 + 合并对列表
        """
        if len(patterns) <= 1:
            return patterns, []

        merge_pairs = []

        # 构建 id → index 映射
        id_to_pattern = {p.get("id", i): p for i, p in enumerate(patterns)}

        # 按相似度分组
        clusters = []
        assigned = set()

        for i, pa in enumerate(patterns):
            if i in assigned:
                continue

            cluster = [i]
            assigned.add(i)

            for j, pb in enumerate(patterns[i + 1:], i + 1):
                if j in assigned:
                    continue

                sim = self.compute_similarity(pa, pb)
                if sim >= self._threshold:
                    cluster.append(j)
                    assigned.add(j)

            clusters.append(cluster)

        # 每类合并成一个
        merged = []
        for cluster in clusters:
            if len(cluster) == 1:
                merged.append(patterns[cluster[0]])
            else:
                # 选置信度最高的作为基础
                base_idx = max(cluster, key=lambda idx: patterns[idx].get("confidence", 0.8))
                base = copy.deepcopy(patterns[base_idx])

                merge_pairs.append((cluster[0], cluster[-1]))  # 记录合并对

                # 合并元数据
                if keep_metadata:
                    all_metadata = [patterns[idx].get("metadata", {}) for idx in cluster]
                    base["metadata"] = {
                        "merged_from": [patterns[idx].get("id", f"pattern_{idx}") for idx in cluster],
                        "merge_count": len(cluster),
                        "original_metadata": all_metadata,
                    }

                # 合并 conditions（去重）
                all_conditions = []
                seen_cond = set()
                for idx in cluster:
                    for cond in patterns[idx].get("conditions", []):
                        cond_str = str(cond)
                        if cond_str not in seen_cond:
                            seen_cond.add(cond_str)
                            all_conditions.append(cond)
                base["conditions"] = all_conditions

                merged.append(base)

        return merged, merge_pairs


def merge_similar_patterns(
    patterns: List[Dict[str, Any]],
    threshold: float = 0.85,
) -> List[Dict[str, Any]]:
    """
    便捷函数：对 pattern 列表去重合并

    Args:
        patterns: pattern 列表
        threshold: 相似度阈值

    Returns:
        去重后的 pattern 列表
    """
    dedup = SimilarityDeduplication(similarity_threshold=threshold, use_semantic=False)
    merged, _ = dedup.merge_similar_patterns(patterns)
    return merged


def compare_versions(
    history: PatternHistory,
    version_a: str,
    version_b: str,
) -> Dict[str, Any]:
    """
    对比两个版本的差异

    Returns:
        差异报告
    """
    pv_a = history.get_version(version_a)
    pv_b = history.get_version(version_b)

    if not pv_a or not pv_b:
        return {"error": "版本不存在"}

    content_a = pv_a.content
    content_b = pv_b.content

    all_keys = set(content_a.keys()) | set(content_b.keys())
    diff_fields = []

    for key in all_keys:
        val_a = content_a.get(key)
        val_b = content_b.get(key)
        if val_a != val_b:
            diff_fields.append({
                "field": key,
                "from": str(val_a)[:100],
                "to": str(val_b)[:100],
            })

    return {
        "version_a": version_a,
        "version_b": version_b,
        "confidence_change": pv_b.confidence - pv_a.confidence,
        "diff_fields": diff_fields,
        "source_change": f"{pv_a.source} -> {pv_b.source}",
    }
