"""
嵌入式知识图谱引擎 (Embedded Knowledge Graph Engine)

轻量级、零外部依赖的高性能图存储，基于 NetworkX DiGraph 构建。

设计参考:
- LightRAG 的实体级+关系级双层检索
- Palantir Ontology 的 Semantic Layer
- GraphRAG 的社区检测与多层次检索

特性:
- 三级索引加速查询 (SPO/PO/OS) 实现 O(1) 查询
- 社区检测支持 (Louvain/Girvan-Newman/Label Propagation)
- 自动去重 + 置信度合并
- BFS 图遍历 + 子图提取
- JSONL 持久化 (人类可读, 增量写入)
- 知识生命周期管理 (CANDIDATE → ACTIVE → STALE → ARCHIVED)
- LRU 内存管理 + 分页加载 + 异步并发

性能目标: 10万三元组 < 50MB 内存, 查询 < 1ms
"""

import asyncio
import copy
import json
import logging
import os
import sys
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Iterator, Union

# 导入 NetworkX 用于图操作和社区检测
import networkx as nx
from networkx.algorithms.community import (
    louvain_communities,
    girvan_newman,
    label_propagation_communities,
)

# 导入 Leiden 算法（可选）
try:
    import leidenalg as la
    import igraph as ig
    LEIDEN_AVAILABLE = True
except ImportError:
    LEIDEN_AVAILABLE = False
    la = None
    ig = None

# 导入配置管理
from ..utils.config import get_config

# 导入血缘追踪模块
from .lineage import (
    lineage_tracker,
    DataSource,
    LineageType,
    record_inference_lineage,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

class TripleStatus(Enum):
    """知识生命周期状态"""
    CANDIDATE = "candidate"   # 新学到，待评估
    ACTIVE = "active"         # 已验证，活跃使用
    STALE = "stale"           # 长期未引用，待清理
    ARCHIVED = "archived"     # 已归档，不参与检索


@dataclass
class TypedTriple:
    """类型化三元组 — 知识图谱的原子单元"""
    id: str
    subject: str
    predicate: str
    object: str
    confidence: float = 0.9
    source: str = "learned"
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 生命周期
    status: TripleStatus = TripleStatus.ACTIVE
    # 使用统计
    access_count: int = 0
    last_accessed: float = 0.0
    # 血缘追踪信息
    lineage_source: str = ""  # 数据来源类型：manual/llm_extracted/inference/learned/import
    lineage_source_id: str = ""  # 来源标识（原始文本ID、推理规则ID等）
    lineage_description: str = ""  # 来源描述
    parent_ids: List[str] = field(default_factory=list)  # 父三元组ID列表（用于推理生成）

    def to_tuple(self) -> Tuple[str, str, str]:
        return (self.subject, self.predicate, self.object)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        # 确保列表类型的字段正确序列化
        if self.parent_ids is None:
            d["parent_ids"] = []
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TypedTriple':
        status = data.get("status", "active")
        if isinstance(status, str):
            status = TripleStatus(status)
        data["status"] = status
        # 确保 parent_ids 字段存在
        if "parent_ids" not in data:
            data["parent_ids"] = []
        return cls(**data)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, TypedTriple):
            return self.id == other.id
        return NotImplemented


@dataclass
class SubGraph:
    """子图结果"""
    triples: List[TypedTriple]
    entities: Set[str]
    predicates: Set[str]

    @property
    def size(self) -> int:
        return len(self.triples)


@dataclass
class Community:
    """
    社区结构 — 存储社区检测结果。
    
    类型一致性说明：
    - community_id: int — 社区唯一标识，从 0 开始递增
    - entities: Set[str] — 社区内实体集合，确保唯一性
    - hub_entities: List[str] — 核心实体列表，按连接度排序
    - triple_count: int — 社区内三元组数量（非负整数）
    - avg_confidence: float — 平均置信度 [0.0, 1.0]
    
    使用场景：
    - 由 detect_communities() 方法创建
    - 被 GraphRetriever.global_search() 消费
    """
    community_id: int  # 社区唯一标识
    entities: Set[str]  # 社区内的实体集合
    summary: str = ""  # 社区摘要描述（可由 LLM 生成）
    # 社区统计信息
    triple_count: int = 0  # 社区内三元组数量
    avg_confidence: float = 0.0  # 平均置信度
    # 核心实体（连接度最高的实体）
    hub_entities: List[str] = field(default_factory=list)
    
    @property
    def size(self) -> int:
        """社区内实体数量 — 与 len(entities) 等价"""
        return len(self.entities)
    
    def __repr__(self) -> str:
        """简洁的字符串表示，便于调试"""
        return f"Community(id={self.community_id}, size={self.size}, hub={self.hub_entities[:3]})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典 — 用于序列化和导出。
        
        注意：entities 从 Set 转为 List 以确保 JSON 可序列化
        """
        return {
            "community_id": self.community_id,
            "entities": list(self.entities),  # Set → List 转换
            "summary": self.summary,
            "triple_count": self.triple_count,
            "avg_confidence": self.avg_confidence,
            "hub_entities": self.hub_entities,
            "size": self.size,
        }


# ─────────────────────────────────────────────
# 知识图谱引擎
# ─────────────────────────────────────────────

class KnowledgeGraph:
    """
    轻量级嵌入式知识图谱引擎

    特性:
    - 三级索引 (SPO/PO/OS) 实现 O(1) 查询
    - 社区检测支持 (Louvain/Girvan-Newman/Label Propagation)
    - 自动去重 + 置信度合并
    - BFS 图遍历 + 子图提取
    - JSONL 持久化 (人类可读, 增量写入)
    - 知识生命周期管理 (CANDIDATE → ACTIVE → STALE → ARCHIVED)
    - 使用统计追踪 (access_count, last_accessed)
    - LRU 内存管理 + 分页加载 + 异步并发 + 读写锁

    Usage:
        kg = KnowledgeGraph()
        tid = kg.add_triple("猫", "is_a", "动物", confidence=0.95)
        results = kg.query(subject="猫")
        communities = kg.detect_communities()  # 社区检测
        kg.save("knowledge.jsonl")
    """

    def __init__(self, persist_path: Optional[str] = None):
        # 三元组存储: id → TypedTriple
        self._triples: Dict[str, TypedTriple] = {}

        # ── 三级索引 ──
        # subject → set of triple_ids
        self._s_index: Dict[str, Set[str]] = defaultdict(set)
        # predicate → set of triple_ids
        self._p_index: Dict[str, Set[str]] = defaultdict(set)
        # object → set of triple_ids
        self._o_index: Dict[str, Set[str]] = defaultdict(set)
        # (subject, predicate, object) → triple_id (去重索引)
        self._spo_dedup: Dict[Tuple[str, str, str], str] = {}

        # ── NetworkX 图结构 ──
        # 使用 NetworkX 存储图结构以支持社区检测和高级图算法
        self._nx_graph: nx.DiGraph = nx.DiGraph()
        
        # ── 社区检测结果缓存 ──
        # 社区列表：每个社区是实体集合
        self._communities: List[Community] = []
        # 实体到社区的映射
        self._entity_to_community: Dict[str, int] = {}
        # 社区检测算法版本号（用于判断缓存是否过期）
        self._community_version: int = 0
        # 图变更计数器（用于触发社区重检测）
        self._graph_version: int = 0

        # 持久化路径
        self._persist_path = persist_path

        # 事件钩子 - 使用 Callable 替代 callable 以符合类型规范
        self._on_triple_added_hooks: List[Callable[[TypedTriple], None]] = []
        self._on_triple_removed_hooks: List[Callable[[TypedTriple], None]] = []

        # ── 并发控制 ──
        # 读写锁：支持多读单写模式，保护知识图谱的并发访问安全
        self._lock = threading.RLock()
        # 写锁计数器，用于跟踪当前写操作状态
        self._write_count = 0
        # 读锁计数器，用于跟踪当前读操作数量
        self._read_count = 0

        # ── 内存管理配置 ──
        # 最大三元组数量限制，从环境变量读取，默认 100000
        self._max_triples = int(os.getenv("KG_MAX_TRIPLES", "100000"))
        # 内存告警阈值（MB），从环境变量读取，默认 500MB
        self._memory_warning_threshold_mb = float(os.getenv("KG_MEMORY_WARNING_MB", "500.0"))
        # 归档文件路径，用于存储被淘汰的三元组
        self._archive_path: Optional[str] = None
        if persist_path:
            # 基于持久化路径生成归档文件路径
            base_path = Path(persist_path)
            self._archive_path = str(base_path.parent / f"{base_path.stem}_archive.jsonl")

        # 如果持久化文件存在，自动加载
        if persist_path and Path(persist_path).exists():
            self.load(persist_path)

    # ─────────────────────────────────────────
    # 写入操作
    # ─────────────────────────────────────────

    def add_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 0.9,
        source: str = "learned",
        metadata: Optional[Dict[str, Any]] = None,
        status: TripleStatus = TripleStatus.ACTIVE,
        lineage_source: str = "",
        lineage_source_id: str = "",
        lineage_description: str = "",
        parent_ids: List[str] = None,
        user_id: str = "",
    ) -> str:
        """
        添加三元组，自动去重 + 置信度合并

        如果 (s, p, o) 已存在:
        - 取 max(old_confidence, new_confidence)
        - 合并 metadata
        - 返回已有 triple_id
        
        新增特性：
        - 自动检查内存使用情况
        - 超过阈值时触发 LRU 淘汰

        Returns:
            triple_id
        """
        with self._lock:
            # 递增写操作计数器，用于性能监控和锁竞争分析
            self._write_count += 1
            
            spo = (subject, predicate, obj)

            # 去重检查
            if spo in self._spo_dedup:
                existing_id = self._spo_dedup[spo]
                existing = self._triples[existing_id]
                # 置信度合并: 取较高值
                if confidence > existing.confidence:
                    existing.confidence = confidence
                # source 合并
                if source and source != existing.source:
                    existing.source = f"{existing.source},{source}"
                # metadata 合并
                if metadata:
                    existing.metadata.update(metadata)
                # 更新访问统计
                existing.access_count += 1
                existing.last_accessed = time.time()
                return existing_id

            # 检查是否需要 LRU 淘汰（在添加新三元组前）
            self._check_and_evict()

            # 新建三元组
            triple_id = f"t:{uuid.uuid4().hex[:12]}"
            triple = TypedTriple(
                id=triple_id,
                subject=subject,
                predicate=predicate,
                object=obj,
                confidence=confidence,
                source=source,
                timestamp=time.time(),
                metadata=metadata or {},
                status=status,
                access_count=1,  # 初始化访问计数为 1
                last_accessed=time.time(),  # 初始化最后访问时间为当前时间
                lineage_source=lineage_source or source,  # 血缘来源
                lineage_source_id=lineage_source_id,  # 来源标识
                lineage_description=lineage_description,  # 来源描述
                parent_ids=parent_ids or [],  # 父三元组列表
            )

            # 写入存储
            self._triples[triple_id] = triple

            # 更新索引
            self._s_index[subject].add(triple_id)
            self._p_index[predicate].add(triple_id)
            self._o_index[obj].add(triple_id)
            self._spo_dedup[spo] = triple_id

            # 更新 NetworkX 图结构：添加节点和边
            self._nx_graph.add_node(subject, entity_type="subject")
            self._nx_graph.add_node(obj, entity_type="object")
            self._nx_graph.add_edge(subject, obj, predicate=predicate, confidence=confidence, triple_id=triple_id)
            
            # 标记图已变更，社区缓存需要更新
            self._graph_version += 1
            
            # 记录血缘信息：将三元组来源注册到血缘追踪系统
            self._record_lineage(
                triple_id=triple_id,
                source=source,
                lineage_source=lineage_source,
                lineage_source_id=lineage_source_id,
                lineage_description=lineage_description,
                parent_ids=parent_ids,
                confidence=confidence,
                user_id=user_id,
            )

            # 触发钩子
            for hook in self._on_triple_added_hooks:
                try:
                    hook(triple)
                except Exception as e:
                    logger.warning(f"on_triple_added hook error: {e}")

            return triple_id

    def add_triples(self, triples: List[Dict[str, Any]]) -> List[str]:
        """批量添加三元组"""
        ids = []
        for t in triples:
            tid = self.add_triple(
                subject=t["subject"],
                predicate=t["predicate"],
                obj=t["object"],
                confidence=t.get("confidence", 0.9),
                source=t.get("source", "learned"),
                metadata=t.get("metadata"),
                lineage_source=t.get("lineage_source", ""),
                lineage_source_id=t.get("lineage_source_id", ""),
                lineage_description=t.get("lineage_description", ""),
                parent_ids=t.get("parent_ids"),
                user_id=t.get("user_id", ""),
            )
            ids.append(tid)
        return ids

    def remove_triple(self, triple_id: str) -> bool:
        """
        删除三元组（线程安全）
        
        使用写锁保护，确保删除操作的原子性和一致性。
        
        Args:
            triple_id: 要删除的三元组 ID
            
        Returns:
            是否成功删除
        """
        with self._lock:
            # 递增写操作计数器，用于性能监控和锁竞争分析
            self._write_count += 1
            
            if triple_id not in self._triples:
                return False

            triple = self._triples[triple_id]
            spo = triple.to_tuple()

            # 移除索引
            self._s_index[triple.subject].discard(triple_id)
            self._p_index[triple.predicate].discard(triple_id)
            self._o_index[triple.object].discard(triple_id)

            # 清理空索引
            if not self._s_index[triple.subject]:
                del self._s_index[triple.subject]
            if not self._p_index[triple.predicate]:
                del self._p_index[triple.predicate]
            if not self._o_index[triple.object]:
                del self._o_index[triple.object]

            # 移除去重索引
            self._spo_dedup.pop(spo, None)

            # 移除三元组
            del self._triples[triple_id]
            
            # 从 NetworkX 图中移除边（如果存在其他边则保留节点）
            if self._nx_graph.has_edge(triple.subject, triple.object):
                self._nx_graph.remove_edge(triple.subject, triple.object)
            
            # 标记图已变更
            self._graph_version += 1
            
            # 删除血缘记录
            try:
                lineage_tracker.delete_lineage(triple_id)
            except Exception as e:
                logger.warning(f"删除血缘记录失败: {e}")

            # 触发钩子
            for hook in self._on_triple_removed_hooks:
                try:
                    hook(triple)
                except Exception as e:
                    logger.warning(f"on_triple_removed hook error: {e}")

            return True

    def update_confidence(self, triple_id: str, confidence: float) -> bool:
        """更新三元组置信度"""
        if triple_id not in self._triples:
            return False
        self._triples[triple_id].confidence = confidence
        return True

    def update_status(self, triple_id: str, status: TripleStatus) -> bool:
        """更新三元组生命周期状态"""
        if triple_id not in self._triples:
            return False
        self._triples[triple_id].status = status
        return True
    
    def _record_lineage(
        self,
        triple_id: str,
        source: str,
        lineage_source: str,
        lineage_source_id: str,
        lineage_description: str,
        parent_ids: List[str],
        confidence: float,
        user_id: str,
    ):
        """
        记录三元组的血缘信息
        
        根据来源类型自动选择合适的血缘记录方式。
        这是血缘追踪的核心方法，确保每个三元组都有可追溯的来源记录。
        """
        try:
            # 确定数据来源类型
            # 优先使用显式指定的 lineage_source，否则根据 source 字段推断
            source_type_str = lineage_source or source
            
            # 映射来源字符串到 DataSource 枚举
            source_mapping = {
                "manual": DataSource.MANUAL,
                "input": DataSource.MANUAL,
                "user": DataSource.MANUAL,
                "llm_extracted": DataSource.LLM_EXTRACTED,
                "llm": DataSource.LLM_EXTRACTED,
                "extracted": DataSource.LLM_EXTRACTED,
                "inference": DataSource.INFERENCE,
                "inferred": DataSource.INFERENCE,
                "reasoning": DataSource.INFERENCE,
                "import": DataSource.IMPORT,
                "imported": DataSource.IMPORT,
                "learned": DataSource.LEARNED,
                "learning": DataSource.LEARNED,
                "derived": DataSource.DERIVED,
                "unknown": DataSource.UNKNOWN,
            }
            
            data_source = source_mapping.get(source_type_str.lower(), DataSource.LEARNED)
            
            # 记录基本来源信息
            lineage_tracker.record_source(
                triple_id=triple_id,
                source=data_source,
                source_id=lineage_source_id,
                source_description=lineage_description or f"来源: {source_type_str}",
                created_by=user_id,
                confidence=confidence,
            )
            
            # 如果有父三元组，记录推理血缘关系
            if parent_ids:
                lineage_tracker.record_derivation(
                    target_id=triple_id,
                    source_ids=parent_ids,
                    lineage_type=LineageType.INFERRED_FROM,
                    description=lineage_description or "推理生成",
                    created_by=user_id,
                )
                
        except Exception as e:
            # 血缘记录失败不应影响主流程，仅记录警告
            logger.warning(f"记录血缘信息失败: {e}")
    
    def trace_lineage(
        self,
        triple_id: str,
        direction: str = "upstream",
        max_depth: int = 10,
    ) -> Dict[str, Any]:
        """
        追踪三元组的数据血缘
        
        提供完整的数据来源追溯能力，支持双向追踪。
        
        参数：
            triple_id: 要追踪的三元组ID
            direction: 追踪方向
                - "upstream": 追踪上游来源（默认）
                - "downstream": 追踪下游影响
                - "both": 双向追踪
            max_depth: 最大追踪深度
        
        返回：
            包含完整血缘链路信息的字典
        """
        try:
            trace = lineage_tracker.trace_lineage(
                triple_id=triple_id,
                direction=direction,
                max_depth=max_depth,
            )
            return trace.to_dict()
        except Exception as e:
            logger.error(f"追踪血缘失败: {e}")
            return {
                "target_id": triple_id,
                "error": str(e),
                "ancestors": [],
                "descendants": [],
            }

    def clear(self):
        """清空图"""
        self._triples.clear()
        self._s_index.clear()
        self._p_index.clear()
        self._o_index.clear()
        self._spo_dedup.clear()
        # 清空 NetworkX 图
        self._nx_graph.clear()
        # 清空社区缓存
        self._communities.clear()
        self._entity_to_community.clear()
        self._graph_version += 1

    def export_d3(self) -> Dict[str, Any]:
        """
        导出符合 D3.js / force-graph 渲染要求的数据结构
        
        Returns:
            Dict: {"nodes": [...], "links": [...]}
        """
        nodes = []
        links = []
        
        # 实体去重
        entities = self.entities()
        for ent in entities:
            # 基础节点信息
            nodes.append({
                "id": ent,
                "name": ent,
                "type": "entity",
                "val": self._nx_graph.degree(ent) if ent in self._nx_graph else 1
            })
            
        # 边信息
        for tid, triple in self._triples.items():
            links.append({
                "source": triple.subject,
                "target": triple.object,
                "predicate": triple.predicate,
                "confidence": triple.confidence,
                "id": tid
            })
            
        return {
            "nodes": nodes,
            "links": links
        }

    # ─────────────────────────────────────────
    # 查询操作 (索引加速)
    # ─────────────────────────────────────────

    def query(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
        min_confidence: float = 0.0,
        status: Optional[TripleStatus] = None,
        limit: int = 0,
    ) -> List[TypedTriple]:
        """
        索引加速的三元组查询（线程安全）

        任意组合 subject/predicate/object 条件，
        使用索引交集快速定位匹配结果。
        
        并发安全：
        - 使用读锁保护，支持并发读取
        - 自动更新访问统计（access_count, last_accessed）

        Args:
            subject: 主语过滤 (None=不限)
            predicate: 谓词过滤 (None=不限)
            obj: 宾语过滤 (None=不限)
            min_confidence: 最低置信度
            status: 状态过滤 (None=不限)
            limit: 返回数量限制 (0=不限)

        Returns:
            匹配的三元组列表
        """
        with self._lock:
            # 递增读操作计数器，用于性能监控和锁竞争分析
            self._read_count += 1
            
            # 确定候选集 (使用索引交集)
            candidate_ids = self._resolve_candidates(subject, predicate, obj)

            # 过滤
            results = []
            for tid in candidate_ids:
                t = self._triples.get(tid)
                if t is None:
                    continue
                if t.confidence < min_confidence:
                    continue
                if status is not None and t.status != status:
                    continue
                # 更新访问统计
                t.access_count += 1
                t.last_accessed = time.time()
                results.append(t)
                if limit > 0 and len(results) >= limit:
                    break

            return results

    def _resolve_candidates(
        self,
        subject: Optional[str],
        predicate: Optional[str],
        obj: Optional[str],
    ) -> Set[str]:
        """
        使用索引交集确定候选三元组 ID — 查询优化的核心方法。
        
        性能优化策略：
        1. 索引选择：只使用非 None 的条件构建候选集
        2. 最小集优先：选择最小的索引集作为起点，减少交集运算量
        3. 提前退出：如果任一条件无匹配，立即返回空集
        
        时间复杂度：O(min(|S|, |P|, |O|))，其中 |S|/|P|/|O| 是各索引的大小
        
        Args:
            subject: 主语过滤条件（None 表示不限）
            predicate: 谓词过滤条件（None 表示不限）
            obj: 宾语过滤条件（None 表示不限）
            
        Returns:
            候选三元组 ID 集合
        """
        # 收集所有非 None 的索引集
        index_sets: List[Set[str]] = []
        index_sizes: List[int] = []
        
        if subject is not None:
            s_set = self._s_index.get(subject, set())
            if not s_set:
                # 主语不存在，提前返回空集（优化点）
                return set()
            index_sets.append(s_set)
            index_sizes.append(len(s_set))
        
        if predicate is not None:
            p_set = self._p_index.get(predicate, set())
            if not p_set:
                # 谓词不存在，提前返回空集（优化点）
                return set()
            index_sets.append(p_set)
            index_sizes.append(len(p_set))
        
        if obj is not None:
            o_set = self._o_index.get(obj, set())
            if not o_set:
                # 宾语不存在，提前返回空集（优化点）
                return set()
            index_sets.append(o_set)
            index_sizes.append(len(o_set))

        if not index_sets:
            # 无条件 → 返回所有三元组 ID
            return set(self._triples.keys())

        if len(index_sets) == 1:
            # 只有一个条件，直接返回
            return index_sets[0]

        # 优化：按集合大小排序，从最小的开始交集（减少运算量）
        # 时间复杂度优化：先交集小集合可以更快缩小结果规模
        sorted_indices = sorted(range(len(index_sets)), key=lambda i: index_sizes[i])
        
        # 从最小的集合开始
        result = index_sets[sorted_indices[0]].copy()
        for idx in sorted_indices[1:]:
            result &= index_sets[idx]
            # 提前退出：如果结果已为空，无需继续交集
            if not result:
                break
        
        return result

    def get_triple(self, triple_id: str) -> Optional[TypedTriple]:
        """根据 ID 获取三元组"""
        return self._triples.get(triple_id)

    def has_triple(self, subject: str, predicate: str, obj: str) -> bool:
        """检查三元组是否存在"""
        return (subject, predicate, obj) in self._spo_dedup

    def find_triple_id(self, subject: str, predicate: str, obj: str) -> Optional[str]:
        """查找三元组 ID"""
        return self._spo_dedup.get((subject, predicate, obj))

    # ─────────────────────────────────────────
    # 图遍历
    # ─────────────────────────────────────────

    def neighbors(
        self,
        entity: str,
        depth: int = 1,
        direction: str = "both",
        min_confidence: float = 0.0,
    ) -> SubGraph:
        """
        BFS 图遍历，获取实体的邻居子图

        Args:
            entity: 起始实体
            depth: 遍历深度
            direction: "out" (作为subject) / "in" (作为object) / "both"
            min_confidence: 最低置信度

        Returns:
            SubGraph 包含遍历到的三元组和实体
        """
        visited_entities: Set[str] = set()
        collected_triples: List[TypedTriple] = []
        frontier: Set[str] = {entity}

        for _ in range(depth):
            next_frontier: Set[str] = set()
            for ent in frontier:
                if ent in visited_entities:
                    continue
                visited_entities.add(ent)

                # 出边: entity 作为 subject
                if direction in ("out", "both"):
                    for tid in self._s_index.get(ent, set()):
                        t = self._triples.get(tid)
                        if t and t.confidence >= min_confidence:
                            collected_triples.append(t)
                            next_frontier.add(t.object)

                # 入边: entity 作为 object
                if direction in ("in", "both"):
                    for tid in self._o_index.get(ent, set()):
                        t = self._triples.get(tid)
                        if t and t.confidence >= min_confidence:
                            collected_triples.append(t)
                            next_frontier.add(t.subject)

            frontier = next_frontier - visited_entities

        # 去重
        seen_ids = set()
        unique_triples = []
        for t in collected_triples:
            if t.id not in seen_ids:
                seen_ids.add(t.id)
                unique_triples.append(t)

        all_entities = set()
        all_predicates = set()
        for t in unique_triples:
            all_entities.add(t.subject)
            all_entities.add(t.object)
            all_predicates.add(t.predicate)

        return SubGraph(
            triples=unique_triples,
            entities=all_entities,
            predicates=all_predicates,
        )

    def subgraph(self, entities: Set[str]) -> 'KnowledgeGraph':
        """提取包含指定实体的子图"""
        sub = KnowledgeGraph()
        for entity in entities:
            for tid in self._s_index.get(entity, set()):
                t = self._triples[tid]
                if t.object in entities:
                    sub.add_triple(
                        t.subject, t.predicate, t.object,
                        confidence=t.confidence,
                        source=t.source,
                        metadata=t.metadata.copy(),
                    )
        return sub

    # ─────────────────────────────────────────
    # 实体和谓词查询
    # ─────────────────────────────────────────

    def entities(self) -> Set[str]:
        """获取所有实体"""
        return set(self._s_index.keys()) | set(self._o_index.keys())

    def predicates(self) -> Set[str]:
        """获取所有谓词类型"""
        return set(self._p_index.keys())

    def entity_triples(self, entity: str) -> List[TypedTriple]:
        """
        获取某个实体参与的所有三元组 — 高频查询路径优化。
        
        性能优化：
        - 使用索引直接定位，避免全量扫描
        - 时间复杂度 O(k)，k 为实体参与的三元组数量
        
        Args:
            entity: 实体名称
            
        Returns:
            该实体参与的所有三元组列表（作为主语或宾语）
        """
        # 递增读操作计数器，用于性能监控和锁竞争分析
        self._read_count += 1
        
        # 使用 S 索引和 O 索引的并集，避免遍历所有三元组
        tids = self._s_index.get(entity, set()) | self._o_index.get(entity, set())
        # 防御性检查：过滤可能已删除的三元组 ID
        return [self._triples[tid] for tid in tids if tid in self._triples]

    def predicate_triples(self, predicate: str) -> List[TypedTriple]:
        """
        获取某个谓词的所有三元组 — 高频查询路径优化。
        
        性能优化：
        - 使用 P 索引直接定位，避免全量扫描
        - 时间复杂度 O(k)，k 为该谓词的三元组数量
        
        Args:
            predicate: 谓词名称
            
        Returns:
            该谓词的所有三元组列表
        """
        # 使用 P 索引直接定位
        tids = self._p_index.get(predicate, set())
        # 防御性检查：过滤可能已删除的三元组 ID
        return [self._triples[tid] for tid in tids if tid in self._triples]

    # ─────────────────────────────────────────
    # 图合并
    # ─────────────────────────────────────────

    def merge(self, other: 'KnowledgeGraph') -> int:
        """
        合并另一个图的所有三元组到当前图

        Returns:
            新增的三元组数量
        """
        added = 0
        for t in other._triples.values():
            spo = t.to_tuple()
            if spo not in self._spo_dedup:
                added += 1
            self.add_triple(
                t.subject, t.predicate, t.object,
                confidence=t.confidence,
                source=t.source,
                metadata=t.metadata.copy(),
            )
        return added

    # ─────────────────────────────────────────
    # 持久化 (JSONL)
    # ─────────────────────────────────────────

    def save(self, path: Optional[str] = None):
        """保存图到 JSONL 文件"""
        save_path = path or self._persist_path
        if not save_path:
            raise ValueError("No persist path specified")

        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        with open(p, 'w', encoding='utf-8') as f:
            for triple in self._triples.values():
                f.write(json.dumps(triple.to_dict(), ensure_ascii=False) + '\n')

        logger.info(f"知识图谱已保存: {len(self._triples)} 条三元组 → {save_path}")

    def load(self, path: Optional[str] = None):
        """从 JSONL 文件加载图"""
        load_path = path or self._persist_path
        if not load_path:
            raise ValueError("No persist path specified")

        p = Path(load_path)
        if not p.exists():
            logger.warning(f"文件不存在: {load_path}")
            return

        count = 0
        with open(p, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    triple = TypedTriple.from_dict(data)
                    # 直接插入，跳过钩子
                    self._triples[triple.id] = triple
                    self._s_index[triple.subject].add(triple.id)
                    self._p_index[triple.predicate].add(triple.id)
                    self._o_index[triple.object].add(triple.id)
                    self._spo_dedup[triple.to_tuple()] = triple.id
                    count += 1
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"跳过无效行: {e}")

        logger.info(f"知识图谱已加载: {count} 条三元组 ← {load_path}")

    # ─────────────────────────────────────────
    # 内存管理
    # ─────────────────────────────────────────

    def get_memory_usage(self, detailed: bool = False) -> Dict[str, Any]:
        """
        获取当前知识图谱的内存占用估算
        
        通过 sys.getsizeof 估算各核心数据结构的内存占用，
        包括三元组存储、索引结构和 NetworkX 图。
        当内存超过告警阈值时记录 WARNING 日志。
        
        注意：sys.getsizeof 有局限性，它只计算对象本身的内存占用，
        不包括对象引用的其他复杂对象（如嵌套字典、自定义对象等）的完整内存。
        因此返回的值是估算值，实际内存占用可能更高。
        对于更精确的内存分析，建议使用 memory_profiler 或 pympler 等工具。
        
        Args:
            detailed: 是否使用递归深度估算。默认为 False（快速模式）。
                     当 detailed=True 时，会递归遍历所有嵌套结构，
                     提供更精确的估算但耗时更长，适合调试和内存分析。
                     当 detailed=False 时，使用快速估算，适合生产环境监控。
        
        Returns:
            内存使用统计字典，包含各组件占用和总占用（字节）
        """
        # sys 模块已在文件头部导入，此处直接使用
        
        def _estimate_nested_size(obj: Any, seen: Optional[Set[int]] = None) -> int:
            """
            递归估算嵌套数据结构的内存占用
            
            处理嵌套字典、列表、集合等复杂结构，避免重复计算同一对象。
            使用 seen 集合跟踪已处理对象，防止循环引用导致无限递归。
            
            Args:
                obj: 要估算的对象
                seen: 已处理对象的 id 集合，用于处理循环引用
                
            Returns:
                估算的内存占用（字节）
            """
            if seen is None:
                seen = set()
            
            obj_id = id(obj)
            if obj_id in seen:
                return 0  # 避免重复计算和循环引用
            seen.add(obj_id)
            
            size = sys.getsizeof(obj)
            
            # 递归处理容器类型
            if isinstance(obj, dict):
                for k, v in obj.items():
                    size += _estimate_nested_size(k, seen)
                    size += _estimate_nested_size(v, seen)
            elif isinstance(obj, (list, tuple, set)):
                for item in obj:
                    size += _estimate_nested_size(item, seen)
            
            return size
        
        # 根据 detailed 参数选择估算策略
        if detailed:
            # 详细模式：递归深度估算所有嵌套结构
            # 适用于内存分析和调试场景，精度更高但性能开销大
            triples_size = _estimate_nested_size(self._triples)
            s_index_size = _estimate_nested_size(self._s_index)
            p_index_size = _estimate_nested_size(self._p_index)
            o_index_size = _estimate_nested_size(self._o_index)
            spo_dedup_size = _estimate_nested_size(self._spo_dedup)
            graph_size = _estimate_nested_size(self._nx_graph)
        else:
            # 快速模式：使用 sys.getsizeof 进行浅层估算
            # 适用于生产环境监控，性能开销小
            
            # 计算三元组存储的内存占用（使用递归估算处理嵌套 metadata）
            triples_size = sys.getsizeof(self._triples)
            for triple in self._triples.values():
                triples_size += sys.getsizeof(triple)
                # 使用递归估算处理可能嵌套的 metadata，更准确但仍有局限
                triples_size += _estimate_nested_size(triple.metadata)
            
            # 计算索引结构的内存占用
            s_index_size = sys.getsizeof(self._s_index)
            for key, value_set in self._s_index.items():
                s_index_size += sys.getsizeof(key) + sys.getsizeof(value_set)
                for item in value_set:
                    s_index_size += sys.getsizeof(item)
            
            p_index_size = sys.getsizeof(self._p_index)
            for key, value_set in self._p_index.items():
                p_index_size += sys.getsizeof(key) + sys.getsizeof(value_set)
                for item in value_set:
                    p_index_size += sys.getsizeof(item)
            
            o_index_size = sys.getsizeof(self._o_index)
            for key, value_set in self._o_index.items():
                o_index_size += sys.getsizeof(key) + sys.getsizeof(value_set)
                for item in value_set:
                    o_index_size += sys.getsizeof(item)
            
            # 计算去重索引的内存占用
            spo_dedup_size = sys.getsizeof(self._spo_dedup)
            for key, value in self._spo_dedup.items():
                spo_dedup_size += sys.getsizeof(key) + sys.getsizeof(value)
            
            # NetworkX 图的内存占用（粗略估算）
            graph_size = sys.getsizeof(self._nx_graph)
        
        # 计算总占用（字节）
        total_bytes = triples_size + s_index_size + p_index_size + o_index_size + spo_dedup_size + graph_size
        total_mb = total_bytes / (1024 * 1024)
        
        # 检查是否超过告警阈值
        if total_mb > self._memory_warning_threshold_mb:
            logger.warning(
                f"知识图谱内存使用超过告警阈值: {total_mb:.2f}MB > {self._memory_warning_threshold_mb}MB, "
                f"三元组数量: {len(self._triples)}"
            )
        
        return {
            "total_bytes": total_bytes,
            "total_mb": round(total_mb, 2),
            "triples_bytes": triples_size,
            "s_index_bytes": s_index_size,
            "p_index_bytes": p_index_size,
            "o_index_bytes": o_index_size,
            "spo_dedup_bytes": spo_dedup_size,
            "graph_bytes": graph_size,
            "triple_count": len(self._triples),
            "warning_threshold_mb": self._memory_warning_threshold_mb,
            "is_warning": total_mb > self._memory_warning_threshold_mb,
            "detailed_mode": detailed,  # 记录本次估算使用的模式
            "read_count": self._read_count,  # 包含读操作计数
            "write_count": self._write_count,  # 包含写操作计数
        }

    def _evict_lru_triples(self, target_count: int) -> int:
        """
        LRU 三元组淘汰策略：淘汰最久未访问的三元组
        
        淘汰逻辑：
        1. 按 last_accessed 升序排序（最久未访问在前）
        2. 按 access_count 升序排序（访问次数少的优先淘汰）
        3. 优先淘汰 STALE/ARCHIVED 状态的三元组
        4. 淘汰前将三元组持久化到归档文件
        
        Args:
            target_count: 需要淘汰到的目标数量
            
        Returns:
            实际淘汰的三元组数量
        """
        if len(self._triples) <= target_count:
            return 0
        
        # 计算需要淘汰的数量
        to_evict_count = len(self._triples) - target_count
        
        # 构建排序键：优先淘汰低优先级状态、低访问次数、久未访问的三元组
        def eviction_priority(triple: TypedTriple) -> Tuple[int, int, float]:
            # 状态优先级：ARCHIVED(0) < STALE(1) < CANDIDATE(2) < ACTIVE(3)
            status_priority = {
                TripleStatus.ARCHIVED: 0,
                TripleStatus.STALE: 1,
                TripleStatus.CANDIDATE: 2,
                TripleStatus.ACTIVE: 3,
            }.get(triple.status, 3)
            # 返回 (状态优先级, 访问次数, 最后访问时间) 用于排序
            return (status_priority, triple.access_count, triple.last_accessed)
        
        # 按淘汰优先级排序
        sorted_triples = sorted(self._triples.values(), key=eviction_priority)
        
        # 选择需要淘汰的三元组
        to_evict = sorted_triples[:to_evict_count]
        
        # 持久化到归档文件后再删除
        evicted_count = 0
        if to_evict and self._archive_path:
            try:
                # 确保归档文件目录存在
                archive_dir = Path(self._archive_path).parent
                archive_dir.mkdir(parents=True, exist_ok=True)
                
                # 追加写入归档文件
                with open(self._archive_path, 'a', encoding='utf-8') as f:
                    for triple in to_evict:
                        f.write(json.dumps(triple.to_dict(), ensure_ascii=False) + '\n')
                        evicted_count += 1
                
                logger.info(f"LRU 淘汰: {evicted_count} 个三元组已归档到 {self._archive_path}")
            except Exception as e:
                logger.error(f"归档三元组失败: {e}")
                # 即使归档失败也继续删除，避免内存溢出
        
        # 从内存中删除被淘汰的三元组
        for triple in to_evict:
            self._remove_triple_internal(triple.id)
        
        return evicted_count

    def _remove_triple_internal(self, triple_id: str) -> bool:
        """
        内部删除方法：无锁版本，用于 LRU 淘汰等内部操作
        
        与 remove_triple 的区别：
        - 不触发事件钩子
        - 不获取锁（调用方需确保已持有锁）
        
        Args:
            triple_id: 要删除的三元组 ID
            
        Returns:
            是否成功删除
        """
        if triple_id not in self._triples:
            return False

        triple = self._triples[triple_id]
        spo = triple.to_tuple()

        # 移除索引
        self._s_index[triple.subject].discard(triple_id)
        self._p_index[triple.predicate].discard(triple_id)
        self._o_index[triple.object].discard(triple_id)

        # 清理空索引
        if not self._s_index[triple.subject]:
            del self._s_index[triple.subject]
        if not self._p_index[triple.predicate]:
            del self._p_index[triple.predicate]
        if not self._o_index[triple.object]:
            del self._o_index[triple.object]

        # 移除去重索引
        self._spo_dedup.pop(spo, None)

        # 移除三元组
        del self._triples[triple_id]
        
        # 从 NetworkX 图中移除边
        if self._nx_graph.has_edge(triple.subject, triple.object):
            self._nx_graph.remove_edge(triple.subject, triple.object)
        
        # 标记图已变更
        self._graph_version += 1

        return True

    def _check_and_evict(self) -> None:
        """
        检查是否需要执行 LRU 淘汰
        
        当三元组数量超过 max_triples 的 90% 时触发淘汰，
        淘汰到 75% 的水平，留更多余地避免频繁触发。
        """
        current_count = len(self._triples)
        # 使用 >= 确保在达到阈值时立即触发，避免边界遗漏
        if current_count >= self._max_triples * 0.9:
            target_count = int(self._max_triples * 0.75)
            # 修复空图时 target_count 为 0 的死循环问题：确保至少淘汰 1 个或保留最小数量
            if target_count == 0 and current_count > 0:
                target_count = max(1, int(current_count * 0.5))
            logger.info(f"三元组数量 {current_count} 超过阈值 {self._max_triples}，执行 LRU 淘汰")
            evicted = self._evict_lru_triples(target_count)
            logger.info(f"LRU 淘汰完成，淘汰 {evicted} 个三元组，当前数量: {len(self._triples)}")

    def load_page(self, offset: int, limit: int) -> List[TypedTriple]:
        """
        分页加载三元组：支持大数据集按需加载
        
        适用于大数据集场景，避免一次性全量加载导致内存溢出。
        按照三元组 ID 的字典序进行分页。
        
        Args:
            offset: 起始偏移量（从 0 开始）
            limit: 每页返回的最大数量
            
        Returns:
            该页的三元组列表，如果 offset 超出范围则返回空列表
            
        Raises:
            ValueError: 当 offset 为负数时抛出
        """
        # 添加 offset 负数检查：负数偏移量没有语义意义，应明确拒绝
        if offset < 0:
            raise ValueError("Offset cannot be negative")
        
        # 添加 limit 合法性检查：非正数 limit 无意义
        if limit <= 0:
            return []
        
        with self._lock:
            # 递增读操作计数器，用于性能监控和锁竞争分析
            self._read_count += 1
            
            # 获取所有三元组 ID 并排序
            all_ids = sorted(self._triples.keys())
            
            # 计算分页范围
            start_idx = offset
            end_idx = min(offset + limit, len(all_ids))
            
            # 边界检查：当 start_idx >= len(all_ids) 时表示已超出数据范围，返回空列表
            # 这是正常的分页结束条件，不是错误
            if start_idx >= len(all_ids):
                return []
            
            # 获取该页的三元组
            page_ids = all_ids[start_idx:end_idx]
            results = []
            for tid in page_ids:
                triple = self._triples.get(tid)
                if triple:
                    # 更新访问统计
                    triple.access_count += 1
                    triple.last_accessed = time.time()
                    results.append(triple)
            
            return results

    # ─────────────────────────────────────────
    # 统计信息
    # ─────────────────────────────────────────

    def statistics(self) -> Dict[str, Any]:
        """获取图的统计信息"""
        status_counts = defaultdict(int)
        total_confidence = 0.0
        source_counts = defaultdict(int)

        for t in self._triples.values():
            status_counts[t.status.value] += 1
            total_confidence += t.confidence
            primary_source = t.source.split(",")[0] if t.source else "unknown"
            source_counts[primary_source] += 1

        n = len(self._triples)
        return {
            "total_triples": n,
            "total_entities": len(self.entities()),
            "total_predicates": len(self.predicates()),
            "avg_confidence": total_confidence / n if n > 0 else 0.0,
            "status_distribution": dict(status_counts),
            "source_distribution": dict(source_counts),
            "top_predicates": sorted(
                [(p, len(ids)) for p, ids in self._p_index.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }

    @property
    def size(self) -> int:
        """三元组总数"""
        return len(self._triples)

    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Iterator[TypedTriple]:
        return iter(self._triples.values())

    def __contains__(self, spo: Tuple[str, str, str]) -> bool:
        return spo in self._spo_dedup

    def __repr__(self) -> str:
        return (
            f"KnowledgeGraph(triples={self.size}, "
            f"entities={len(self.entities())}, "
            f"predicates={len(self.predicates())})"
        )

    # ─────────────────────────────────────────
    # 异步并发增强
    # ─────────────────────────────────────────

    async def async_add_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 0.9,
        source: str = "learned",
        metadata: Optional[Dict[str, Any]] = None,
        status: TripleStatus = TripleStatus.ACTIVE,
    ) -> str:
        """
        异步添加三元组
        
        将同步 add_triple 包装为异步方法，
        在事件循环中执行，不阻塞其他 I/O 操作。
        
        Args:
            subject: 主语
            predicate: 谓词
            obj: 宾语
            confidence: 置信度
            source: 来源
            metadata: 元数据
            status: 生命周期状态
            
        Returns:
            新增或已存在的 triple_id
        """
        # 使用 asyncio.to_thread 将同步操作转为异步
        # 获取写锁确保线程安全
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.add_triple(
                subject=subject,
                predicate=predicate,
                obj=obj,
                confidence=confidence,
                source=source,
                metadata=metadata,
                status=status,
            )
        )

    async def async_batch_add(
        self,
        triples: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        异步批量添加三元组
        
        将批量添加操作分解为多个小批次异步执行，
        每批次完成后检查内存使用情况，必要时触发 LRU 淘汰。
        
        Args:
            triples: 三元组字典列表，每个字典包含 subject, predicate, object 等字段
            batch_size: 每批处理的数量，默认 100
            
        Returns:
            包含成功 ID 列表和失败信息的字典：
            {
                "success_ids": List[str],  # 成功添加的三元组 ID
                "failed": List[Dict],      # 失败记录列表，每项包含 index 和 error
                "success_count": int,      # 成功数量
                "fail_count": int,         # 失败数量
            }
        """
        all_ids = []
        failed_records = []
        total = len(triples)
        
        for i in range(0, total, batch_size):
            batch = triples[i:i + batch_size]
            
            # 并发处理当前批次
            tasks = []
            for t in batch:
                task = self.async_add_triple(
                    subject=t["subject"],
                    predicate=t["predicate"],
                    obj=t["object"],
                    confidence=t.get("confidence", 0.9),
                    source=t.get("source", "learned"),
                    metadata=t.get("metadata"),
                )
                tasks.append(task)
            
            # 等待当前批次完成
            batch_ids = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果，收集失败信息而非静默吞掉异常
            for idx, result in enumerate(batch_ids):
                global_idx = i + idx
                if isinstance(result, Exception):
                    # 记录失败信息供调用方处理
                    failed_records.append({
                        "index": global_idx,
                        "triple": triples[global_idx],
                        "error": str(result),
                        "error_type": type(result).__name__,
                    })
                    logger.warning(f"异步添加三元组失败 [索引 {global_idx}]: {result}")
                else:
                    all_ids.append(result)
            
            # 每批次完成后检查内存并触发 LRU 淘汰
            # 使用 run_in_executor 避免阻塞事件循环
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._check_and_evict)
            
            # 记录进度
            processed = min(i + batch_size, total)
            logger.debug(f"异步批量添加进度: {processed}/{total}")
        
        return {
            "success_ids": all_ids,
            "failed": failed_records,
            "success_count": len(all_ids),
            "fail_count": len(failed_records),
        }

    async def async_query(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
        min_confidence: float = 0.0,
        status: Optional[TripleStatus] = None,
        limit: int = 0,
    ) -> List[TypedTriple]:
        """
        异步查询三元组
        
        将同步 query 包装为异步方法，
        适用于需要并发执行多个查询的场景。
        
        Args:
            subject: 主语过滤
            predicate: 谓词过滤
            obj: 宾语过滤
            min_confidence: 最低置信度
            status: 状态过滤
            limit: 返回数量限制
            
        Returns:
            匹配的三元组列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.query(
                subject=subject,
                predicate=predicate,
                obj=obj,
                min_confidence=min_confidence,
                status=status,
                limit=limit,
            )
        )

    def batch_pipeline(
        self,
        operations: List[Dict[str, Any]],
        atomic: bool = True,
    ) -> Dict[str, Any]:
        """
        批量操作流水线：支持批量操作的原子化执行
        
        支持的操作类型：
        - add: 添加三元组
        - remove: 删除三元组
        - update_confidence: 更新置信度
        - update_status: 更新状态
        
        Args:
            operations: 操作列表，每个操作是一个字典，包含 'type' 和对应参数
            atomic: 是否原子化执行，为 True 时任一失败则全部回滚
            
        Returns:
            执行结果字典，包含成功数量、失败数量和详细结果
        """
        with self._lock:
            # 递增写操作计数器，用于性能监控和锁竞争分析
            # batch_pipeline 作为批量写操作，只计数一次，内部调用的 add/remove 不重复计数
            self._write_count += 1
            
            # 记录操作前的状态，用于原子回滚
            backup_triples = None
            backup_s_index = None
            backup_p_index = None
            backup_o_index = None
            backup_spo_dedup = None
            
            if atomic:
                # 设计决策：原子模式使用深拷贝实现回滚能力
                # 选择深拷贝而非操作日志的原因：
                # 1. 知识图谱数据结构复杂（多索引+NetworkX图），操作日志回滚逻辑复杂且易出错
                # 2. 批量操作通常数据量可控（<10000条），深拷贝性能可接受
                # 3. 深拷贝确保完全隔离，避免回滚时因引用共享导致的数据污染
                # 4. 简单性原则：深拷贝实现简单，维护成本低，符合防御式编程
                
                # 阈值警告：当三元组数量超过 10000 时，深拷贝可能耗时较长
                triple_count = len(self._triples)
                DEEP_COPY_WARNING_THRESHOLD = 10000  # 深拷贝警告阈值，从环境变量读取或保持固定值
                if triple_count > DEEP_COPY_WARNING_THRESHOLD:
                    logger.warning(
                        f"原子模式：三元组数量 ({triple_count}) 超过阈值 ({DEEP_COPY_WARNING_THRESHOLD})，"
                        f"深拷贝备份可能耗时较长，考虑关闭 atomic 模式或分批处理"
                    )
                
                # 记录深拷贝开始时间，用于性能监控
                backup_start_time = time.time()
                
                # 创建深拷贝备份（使用 copy.deepcopy 确保完全独立，避免浅拷贝导致的引用问题）
                try:
                    backup_triples = copy.deepcopy(self._triples)
                    backup_s_index = copy.deepcopy(self._s_index)
                    backup_p_index = copy.deepcopy(self._p_index)
                    backup_o_index = copy.deepcopy(self._o_index)
                    backup_spo_dedup = copy.deepcopy(self._spo_dedup)
                    
                    # 记录深拷贝耗时，用于性能分析和阈值调优
                    backup_duration = time.time() - backup_start_time
                    logger.info(f"原子模式备份完成: {triple_count} 条三元组，耗时 {backup_duration:.3f}s")
                    
                    # 如果备份耗时超过 1 秒，记录警告提示潜在性能问题
                    if backup_duration > 1.0:
                        logger.warning(
                            f"原子模式备份耗时较长 ({backup_duration:.3f}s)，"
                            f"建议评估是否需要关闭 atomic 模式或优化数据结构"
                        )
                        
                except Exception as e:
                    # 深拷贝失败时记录错误并禁用原子模式，避免不一致状态
                    logger.error(f"原子模式备份失败，禁用原子模式: {e}")
                    atomic = False
                    backup_triples = None
                    backup_s_index = None
                    backup_p_index = None
                    backup_o_index = None
                    backup_spo_dedup = None
            
            results = []
            success_count = 0
            fail_count = 0
            
            try:
                for idx, op in enumerate(operations):
                    op_type = op.get("type")
                    op_result = {"index": idx, "type": op_type, "success": False}
                    
                    try:
                        if op_type == "add":
                            # 添加操作
                            tid = self.add_triple(
                                subject=op["subject"],
                                predicate=op["predicate"],
                                obj=op["object"],
                                confidence=op.get("confidence", 0.9),
                                source=op.get("source", "learned"),
                                metadata=op.get("metadata"),
                                status=op.get("status", TripleStatus.ACTIVE),
                            )
                            op_result["triple_id"] = tid
                            op_result["success"] = True
                            success_count += 1
                            
                        elif op_type == "remove":
                            # 删除操作
                            success = self.remove_triple(op["triple_id"])
                            op_result["success"] = success
                            if success:
                                success_count += 1
                            else:
                                fail_count += 1
                                
                        elif op_type == "update_confidence":
                            # 更新置信度
                            success = self.update_confidence(
                                op["triple_id"],
                                op["confidence"]
                            )
                            op_result["success"] = success
                            if success:
                                success_count += 1
                            else:
                                fail_count += 1
                                
                        elif op_type == "update_status":
                            # 更新状态
                            status = op["status"]
                            if isinstance(status, str):
                                status = TripleStatus(status)
                            success = self.update_status(op["triple_id"], status)
                            op_result["success"] = success
                            if success:
                                success_count += 1
                            else:
                                fail_count += 1
                        else:
                            op_result["error"] = f"未知操作类型: {op_type}"
                            fail_count += 1
                            
                    except Exception as e:
                        op_result["error"] = str(e)
                        fail_count += 1
                        
                        # 原子模式下，任一失败立即回滚
                        if atomic:
                            raise
                    
                    results.append(op_result)
                
                # 批量操作完成后检查内存
                self._check_and_evict()
                
            except Exception as e:
                # 原子模式：回滚到操作前状态
                if atomic and backup_triples is not None:
                    self._triples = backup_triples
                    self._s_index = backup_s_index
                    self._p_index = backup_p_index
                    self._o_index = backup_o_index
                    self._spo_dedup = backup_spo_dedup
                    # 重建 NetworkX 图
                    self._rebuild_nx_graph()
                    logger.warning(f"批量操作失败已回滚: {e}")
                    return {
                        "success": False,
                        "success_count": 0,
                        "fail_count": len(operations),
                        "error": str(e),
                        "results": results,
                        "rolled_back": True,
                    }
                else:
                    # 非原子模式：继续返回部分结果
                    logger.warning(f"批量操作部分失败: {e}")
            
            return {
                "success": fail_count == 0,
                "success_count": success_count,
                "fail_count": fail_count,
                "total_count": len(operations),
                "results": results,
                "rolled_back": False,
            }

    def _rebuild_nx_graph(self) -> None:
        """
        从当前三元组重建 NetworkX 图
        
        用于批量操作回滚后恢复图结构一致性。
        """
        self._nx_graph.clear()
        for triple in self._triples.values():
            self._nx_graph.add_node(triple.subject, entity_type="subject")
            self._nx_graph.add_node(triple.object, entity_type="object")
            self._nx_graph.add_edge(
                triple.subject,
                triple.object,
                predicate=triple.predicate,
                confidence=triple.confidence,
                triple_id=triple.id,
            )
        # 重置社区缓存
        self._communities.clear()
        self._entity_to_community.clear()
        self._graph_version += 1

    # ─────────────────────────────────────────
    # 事件钩子
    # ─────────────────────────────────────────

    def on_triple_added(self, callback: Callable[[TypedTriple], None]) -> None:
        """
        注册三元组添加钩子
        
        Args:
            callback: 回调函数，接收 TypedTriple 参数，无返回值
        """
        self._on_triple_added_hooks.append(callback)

    def on_triple_removed(self, callback: Callable[[TypedTriple], None]) -> None:
        """
        注册三元组删除钩子
        
        Args:
            callback: 回调函数，接收 TypedTriple 参数，无返回值
        """
        self._on_triple_removed_hooks.append(callback)

    # ─────────────────────────────────────────
    # 兼容层: 支持旧的 Fact 对象
    # ─────────────────────────────────────────

    def add_fact(self, subject: str, predicate: str, obj: str,
                 confidence: float = 0.9, source: str = "manual") -> str:
        """兼容旧接口: 等价于 add_triple"""
        return self.add_triple(subject, predicate, obj,
                               confidence=confidence, source=source)

    def query_facts(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> List[TypedTriple]:
        """兼容旧接口: 等价于 query"""
        return self.query(subject=subject, predicate=predicate,
                          obj=obj, min_confidence=min_confidence)

    @property
    def facts(self) -> List[TypedTriple]:
        """兼容旧接口: 返回所有三元组 (作为列表)"""
        return list(self._triples.values())

    @property
    def fact_count(self) -> int:
        """兼容旧接口: 事实总数"""
        return self.size

    # ─────────────────────────────────────────
    # 社区检测方法
    # ─────────────────────────────────────────

    def detect_communities(
        self,
        algorithm: Optional[str] = None,
        force_refresh: bool = False,
        **kwargs,
    ) -> List[Community]:
        """
        执行社区检测，将知识图谱划分为多个社区

        Args:
            algorithm: 社区检测算法，可选 "louvain", "girvan_newman", "label_propagation"
                       如果未指定，从配置读取
            force_refresh: 是否强制刷新社区缓存
            **kwargs: 算法特定参数
                - louvain: resolution (分辨率参数，默认从配置读取)
                - girvan_newman: max_iter (最大迭代次数，默认从配置读取)

        Returns:
            社区列表，每个社区包含实体集合和统计信息
        """
        # 从配置获取默认算法和参数
        config = get_config().graphrag
        algorithm = algorithm or config.community_algorithm
        
        # 检查是否需要重新计算社区
        if not force_refresh and self._communities:
            if self._community_version == self._graph_version:
                # 社区缓存有效，直接返回
                logger.debug(f"使用缓存的社区检测结果: {len(self._communities)} 个社区")
                return self._communities

        # 检查图是否为空
        if self._nx_graph.number_of_nodes() == 0:
            logger.warning("图为空，无法进行社区检测")
            return []

        # 将有向图转换为无向图用于社区检测
        undirected_graph = self._nx_graph.to_undirected()

        # 根据算法执行社区检测
        if algorithm == "louvain":
            communities = self._detect_louvain(undirected_graph, config, **kwargs)
        elif algorithm == "girvan_newman":
            communities = self._detect_girvan_newman(undirected_graph, config, **kwargs)
        elif algorithm == "label_propagation":
            communities = self._detect_label_propagation(undirected_graph)
        elif algorithm == "leiden":
            communities = self._detect_leiden(undirected_graph, config, **kwargs)
        else:
            # 默认使用 Louvain 算法
            logger.warning(f"未知算法 '{algorithm}'，使用默认 Louvain 算法")
            communities = self._detect_louvain(undirected_graph, config, **kwargs)

        # 更新社区缓存
        self._communities = communities
        self._community_version = self._graph_version
        
        # 更新实体到社区的映射
        self._entity_to_community.clear()
        for community in communities:
            for entity in community.entities:
                self._entity_to_community[entity] = community.community_id

        logger.info(f"社区检测完成: {len(communities)} 个社区, 算法={algorithm}")
        return communities

    def _detect_louvain(
        self,
        graph: nx.Graph,
        config,
        **kwargs,
    ) -> List[Community]:
        """
        使用 Louvain 算法进行社区检测

        Louvain 算法通过最大化模块度来划分社区，
        适合大规模图的快速社区检测。
        """
        # 获取分辨率参数：值越大社区越细粒度
        resolution = kwargs.get("resolution", config.louvain_resolution)
        
        # 执行 Louvain 社区检测
        # 注意：networkx 的 louvain_communities 返回节点集合的列表
        try:
            community_sets = louvain_communities(graph, resolution=resolution)
        except Exception as e:
            logger.error(f"Louvain 社区检测失败: {e}")
            return []

        # 转换为 Community 对象
        return self._build_communities(community_sets)

    def _detect_girvan_newman(
        self,
        graph: nx.Graph,
        config,
        **kwargs,
    ) -> List[Community]:
        """
        使用 Girvan-Newman 算法进行社区检测

        Girvan-Newman 算法通过迭代移除介数最高的边来划分社区，
        适合中小规模图的精确社区检测。时间复杂度较高。
        """
        max_iter = kwargs.get("max_iter", config.girvan_newman_max_iter)
        
        try:
            # 获取社区迭代器
            community_generator = girvan_newman(graph)
            
            # 获取第一次划分的结果（顶层社区）
            # 如果需要更细粒度的划分，可以继续迭代
            community_sets = None
            for i, communities in enumerate(community_generator):
                community_sets = communities
                if i >= max_iter - 1:
                    break
            
            if community_sets is None:
                return []
                
        except Exception as e:
            logger.error(f"Girvan-Newman 社区检测失败: {e}")
            return []

        return self._build_communities(list(community_sets))

    def _detect_label_propagation(self, graph: nx.Graph) -> List[Community]:
        """
        使用标签传播算法进行社区检测

        Label Propagation 是一种快速且可扩展的社区检测算法，
        适合动态变化的图。但结果可能不稳定。
        """
        try:
            # label_propagation_communities 返回节点集合的列表
            community_sets = list(label_propagation_communities(graph))
        except Exception as e:
            logger.error(f"Label Propagation 社区检测失败: {e}")
            return []

        return self._build_communities(community_sets)

    def _detect_leiden(
        self,
        graph: nx.Graph,
        config,
        **kwargs,
    ) -> List[Community]:
        """
        使用 Leiden 算法进行社区检测

        Leiden 算法是 Louvain 的改进版本：
        - 保证社区连接性（不会返回断开的社区）
        - 更快的收敛速度
        - 更精确的模块度优化

        需要安装 leidenalg: pip install leidenalg
        """
        if not LEIDEN_AVAILABLE:
            logger.warning(
                "Leiden 算法未安装（pip install leidenalg），"
                "回退到 Louvain 算法"
            )
            return self._detect_louvain(graph, config, **kwargs)

        resolution = kwargs.get("resolution", config.louvain_resolution)

        try:
            # 将 NetworkX 图转换为 igraph 图
            # igraph 不支持空图
            if graph.number_of_nodes() == 0:
                return []

            # 创建 igraph 图
            ig_graph = ig.Graph.from_networkx(graph)

            # 执行 Leiden 社区检测
            # partition_type: RBERCalendar: 允许空社区, ModularVertexPartition: 标准模块度
            partition = la.find_partition(
                ig_graph,
                la.ModularityVertexPartition,
                resolution=resolution,
            )

            # 转换为节点集合列表
            community_sets = [set(partition[v]['name'] for v in comm) for comm in partition]

        except Exception as e:
            logger.error(f"Leiden 社区检测失败: {e}")
            return self._detect_louvain(graph, config, **kwargs)

        return self._build_communities(community_sets)

    def _build_communities(self, community_sets: List[Set[str]]) -> List[Community]:
        """
        将节点集合列表转换为 Community 对象列表

        同时计算每个社区的统计信息和核心实体。
        """
        config = get_config().graphrag
        min_community_size = config.min_community_size
        
        communities = []
        
        for idx, entities in enumerate(community_sets):
            # 过滤过小的社区
            if len(entities) < min_community_size:
                continue
                
            # 计算社区内三元组
            community_triples = []
            for entity in entities:
                # 获取实体的所有三元组
                tids = self._s_index.get(entity, set()) | self._o_index.get(entity, set())
                for tid in tids:
                    t = self._triples.get(tid)
                    if t and t.subject in entities and t.object in entities:
                        community_triples.append(t)
            
            # 去重
            unique_triples = list({t.id: t for t in community_triples}.values())
            
            # 计算平均置信度
            avg_conf = 0.0
            if unique_triples:
                avg_conf = sum(t.confidence for t in unique_triples) / len(unique_triples)
            
            # 找出核心实体（连接度最高的实体）
            entity_degrees = {}
            for entity in entities:
                degree = self._nx_graph.degree(entity) if entity in self._nx_graph else 0
                entity_degrees[entity] = degree
            # 按度数排序，取前5个作为核心实体
            hub_entities = sorted(entity_degrees.keys(), key=lambda x: entity_degrees[x], reverse=True)[:5]
            
            community = Community(
                community_id=idx,
                entities=set(entities),
                triple_count=len(unique_triples),
                avg_confidence=avg_conf,
                hub_entities=hub_entities,
            )
            communities.append(community)

        return communities

    def get_community(self, entity: str) -> Optional[Community]:
        """
        获取实体所属的社区

        Args:
            entity: 实体名称

        Returns:
            该实体所属的社区，如果不存在则返回 None
        """
        # 确保社区已检测
        if not self._communities:
            self.detect_communities()
        
        community_id = self._entity_to_community.get(entity)
        if community_id is None:
            return None
            
        # 通过 ID 查找社区
        for community in self._communities:
            if community.community_id == community_id:
                return community
        
        return None

    def get_community_entities(self, community_id: int) -> Set[str]:
        """
        获取社区内的所有实体

        Args:
            community_id: 社区 ID

        Returns:
            社区内实体集合
        """
        for community in self._communities:
            if community.community_id == community_id:
                return community.entities
        return set()

    def get_community_triples(self, community_id: int) -> List[TypedTriple]:
        """
        获取社区内的所有三元组 — 优化版本。
        
        性能优化：
        - 使用字典查找替代线性搜索定位社区
        - 使用集合成员检查替代重复遍历
        - 使用字典推导式去重，时间复杂度 O(n)
        
        Args:
            community_id: 社区 ID

        Returns:
            社区内三元组列表（已去重）
        """
        # 优化：使用字典查找替代线性搜索
        community_map = {c.community_id: c for c in self._communities}
        community = community_map.get(community_id)
        
        if community is None:
            return []
        
        # 优化：预先将实体集合转为 frozenset 以加速成员检查
        entity_set = frozenset(community.entities)
        
        # 获取社区内所有三元组
        triples = []
        for entity in community.entities:
            # 使用索引快速获取实体相关三元组
            tids = self._s_index.get(entity, set()) | self._o_index.get(entity, set())
            for tid in tids:
                t = self._triples.get(tid)
                # 检查三元组的两端是否都在社区内
                if t and t.subject in entity_set and t.object in entity_set:
                    triples.append(t)
        
        # 去重：使用 dict 保持顺序的同时去重（Python 3.7+ 保证顺序）
        return list({t.id: t for t in triples}.values())

    def get_community_statistics(self) -> Dict[str, Any]:
        """
        获取社区统计信息

        Returns:
            包含社区数量、平均规模、最大/最小社区等统计信息
        """
        if not self._communities:
            self.detect_communities()
        
        if not self._communities:
            return {"total_communities": 0}
        
        sizes = [c.size for c in self._communities]
        return {
            "total_communities": len(self._communities),
            "total_entities_in_communities": sum(sizes),
            "avg_community_size": sum(sizes) / len(sizes),
            "max_community_size": max(sizes),
            "min_community_size": min(sizes),
            "community_details": [
                {
                    "id": c.community_id,
                    "size": c.size,
                    "triple_count": c.triple_count,
                    "avg_confidence": c.avg_confidence,
                    "hub_entities": c.hub_entities[:3],
                }
                for c in self._communities
            ],
        }

    def generate_community_summaries(
        self,
        llm_client: Optional[Any] = None,
        force_regenerate: bool = False,
    ) -> List[Community]:
        """
        为每个社区生成 LLM 摘要描述

        使用 LLM 分析社区内的实体和关系，生成简洁的社区主题描述。
        摘要存储在 Community.summary 字段中。

        Args:
            llm_client: LLM 客户端（如不提供，使用简单的启发式摘要）
            force_regenerate: 是否强制重新生成

        Returns:
            社区列表（含摘要）
        """
        for community in self._communities:
            # 如果已有摘要且不强制重新生成，跳过
            if community.summary and not force_regenerate:
                continue

            # 如果有 LLM 客户端，生成智能摘要
            if llm_client:
                try:
                    community_text = self._build_community_description(community)
                    prompt = (
                        f"请为以下知识社区生成一句简短的主题描述（不超过50字）：\n"
                        f"社区包含实体：{', '.join(list(community.entities)[:10])}...\n"
                        f"社区内关系：{community_text}\n"
                        f"请直接输出描述，不要有多余文字。"
                    )
                    response = llm_client.chat([
                        {"role": "user", "content": prompt}
                    ])
                    community.summary = response.get("content", "").strip()
                except Exception as e:
                    logger.debug(f"LLM 摘要生成失败: {e}")
                    community.summary = self._build_heuristic_summary(community)
            else:
                # 降级方案：启发式摘要
                community.summary = self._build_heuristic_summary(community)

        return self._communities

    def _build_community_description(self, community: Community) -> str:
        """构建社区内关系的文本描述"""
        triples = self.get_community_triples(community.community_id)
        relations = []
        for t in triples[:20]:  # 最多20个关系
            relations.append(f"{t.subject} -[{t.predicate}]-> {t.object}")
        return "; ".join(relations) if relations else "无关系"

    def _build_heuristic_summary(self, community: Community) -> str:
        """构建启发式摘要（无 LLM 时使用）"""
        entities = list(community.entities)[:5]
        hubs = community.hub_entities[:3]

        # 找出最常见的实体类型/前缀
        prefixes: Dict[str, int] = {}
        for e in community.entities:
            prefix = e.split("：")[0].split("（")[0][:4]
            prefixes[prefix] = prefixes.get(prefix, 0) + 1

        top_prefix = max(prefixes, key=prefixes.get) if prefixes else ""

        summary_parts = []
        if top_prefix:
            summary_parts.append(f"围绕「{top_prefix}」主题的社区")
        if hubs:
            summary_parts.append(f"核心实体：{', '.join(hubs)}")
        summary_parts.append(f"共{community.size}个实体，{community.triple_count}条关系")

        return "，".join(summary_parts)

    def cross_community_reasoning(
        self,
        entity_a: str,
        entity_b: str,
        max_hops: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        查找两个实体之间的跨社区推理路径

        跨社区推理用于发现不同领域/社区之间的隐藏联系。

        Args:
            entity_a: 起始实体
            entity_b: 目标实体
            max_hops: 最大跳数

        Returns:
            跨社区推理路径列表，每条路径包含节点、边和经过的社区
        """
        if entity_a not in self._nx_graph or entity_b not in self._nx_graph:
            return []

        # 确保社区已检测
        if not self._communities:
            self.detect_communities()

        paths: List[Dict[str, Any]] = []

        # BFS 查找所有短路径
        try:
            for path in nx.all_shortest_paths(
                self._nx_graph, entity_a, entity_b, cutoff=max_hops
            ):
                if len(path) < 2:
                    continue

                # 分析路径经过的社区
                community_ids = []
                path_communities = []

                for node in path:
                    comm = self.get_community(node)
                    if comm and comm.community_id not in community_ids:
                        community_ids.append(comm.community_id)
                        path_communities.append({
                            "community_id": comm.community_id,
                            "entities": list(comm.entities)[:5],
                            "summary": comm.summary or f"社区 {comm.community_id}",
                        })

                # 构建路径三元组
                path_triples = []
                for i in range(len(path) - 1):
                    s, o = path[i], path[i + 1]
                    # 查找 s → o 的关系
                    for tid in self._nx_graph.get_edge_data(s, o, {}).values():
                        if isinstance(tid, dict):
                            predicate = tid.get("predicate", "related_to")
                        else:
                            predicate = "related_to"
                        path_triples.append(f"{s} -[{predicate}]-> {o}")

                paths.append({
                    "path": path,
                    "hops": len(path) - 1,
                    "communities_crossed": community_ids,
                    "community_details": path_communities,
                    "triples": path_triples,
                    "cross_domain": len(community_ids) > 1,
                })

        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        # 按跳数排序
        paths.sort(key=lambda p: p["hops"])

        # 只返回跨社区的路径（过滤掉同社区的路径）
        cross_community_paths = [p for p in paths if p["cross_domain"]]

        return cross_community_paths

    @property
    def communities(self) -> List[Community]:
        """获取缓存的社区列表（如果不存在则自动检测）"""
        if not self._communities:
            return self.detect_communities()
        return self._communities

    @property
    def nx_graph(self) -> nx.DiGraph:
        """获取 NetworkX 图对象（只读）"""
        return self._nx_graph
