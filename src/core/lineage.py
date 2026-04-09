"""
数据血缘追踪模块 (Data Lineage Tracking Module)

提供完整的数据来源追溯功能，记录知识图谱中每个三元组的血缘关系。

特性：
- 三元组来源追踪（手动输入/LLM提取/推理生成）
- 血缘链路可视化
- 来源可信度评估
- 血缘关系持久化

设计原则：
- 零硬编码：所有配置从 ConfigManager 读取
- 逐行注释：每行逻辑代码包含中文注释
- 完整性：记录数据来源的完整上下文
"""

import json
import logging
import sqlite3
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# 导入配置管理器
from ..utils.config import get_config

logger = logging.getLogger(__name__)


# ==================== 血缘数据结构定义 ====================

class DataSource(Enum):
    """
    数据来源类型枚举
    
    定义三元组的所有可能来源类型。
    """
    MANUAL = "manual"               # 手动输入
    LLM_EXTRACTED = "llm_extracted"  # LLM 提取
    INFERENCE = "inference"          # 推理生成
    IMPORT = "import"                # 外部导入
    LEARNED = "learned"              # 学习获得
    DERIVED = "derived"              # 派生计算
    UNKNOWN = "unknown"              # 未知来源


class LineageType(Enum):
    """
    血缘关系类型枚举
    
    定义数据之间的血缘关系类型。
    """
    DERIVED_FROM = "derived_from"    # 派生自
    INFERRED_FROM = "inferred_from"  # 推断自
    EXTRACTED_FROM = "extracted_from"  # 提取自
    TRANSFORMED_FROM = "transformed_from"  # 转换自
    AGGREGATED_FROM = "aggregated_from"  # 聚合自


@dataclass
class LineageNode:
    """
    血缘节点数据结构
    
    表示一个数据节点及其来源信息。
    """
    # 节点标识
    id: str                              # 节点ID（三元组ID或其他资源ID）
    source: DataSource                   # 数据来源类型
    
    # 来源信息
    source_id: str = ""                  # 来源标识（如原始文本ID、推理规则ID等）
    source_description: str = ""         # 来源描述
    
    # 创建和修改信息
    created_at: str = ""                 # 创建时间
    created_by: str = ""                 # 创建者（用户ID或系统）
    modified_at: str = ""                # 最后修改时间
    modification_history: List[Dict] = field(default_factory=list)  # 修改历史
    
    # 可信度信息
    confidence: float = 1.0              # 原始置信度
    source_confidence: float = 1.0       # 来源可信度
    
    # 扩展信息
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "source": self.source.value,
            "source_id": self.source_id,
            "source_description": self.source_description,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "modified_at": self.modified_at,
            "modification_history": self.modification_history,
            "confidence": self.confidence,
            "source_confidence": self.source_confidence,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineageNode":
        """从字典创建实例"""
        source = data.get("source", "unknown")
        if isinstance(source, str):
            source = DataSource(source)
        
        return cls(
            id=data["id"],
            source=source,
            source_id=data.get("source_id", ""),
            source_description=data.get("source_description", ""),
            created_at=data.get("created_at", ""),
            created_by=data.get("created_by", ""),
            modified_at=data.get("modified_at", ""),
            modification_history=data.get("modification_history", []),
            confidence=data.get("confidence", 1.0),
            source_confidence=data.get("source_confidence", 1.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class LineageEdge:
    """
    血缘边数据结构
    
    表示数据之间的血缘关系。
    """
    # 边标识
    id: str                              # 边ID
    source_node: str                     # 源节点ID
    target_node: str                     # 目标节点ID
    
    # 关系信息
    lineage_type: LineageType            # 血缘关系类型
    description: str = ""                # 关系描述
    
    # 创建信息
    created_at: str = ""                 # 创建时间
    created_by: str = ""                 # 创建者
    
    # 推理信息（如果是推理生成的血缘）
    rule_id: str = ""                    # 推理规则ID
    rule_name: str = ""                  # 推理规则名称
    
    # 扩展信息
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "source_node": self.source_node,
            "target_node": self.target_node,
            "lineage_type": self.lineage_type.value,
            "description": self.description,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineageEdge":
        """从字典创建实例"""
        lineage_type = data.get("lineage_type", "derived_from")
        if isinstance(lineage_type, str):
            lineage_type = LineageType(lineage_type)
        
        return cls(
            id=data["id"],
            source_node=data["source_node"],
            target_node=data["target_node"],
            lineage_type=lineage_type,
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
            created_by=data.get("created_by", ""),
            rule_id=data.get("rule_id", ""),
            rule_name=data.get("rule_name", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class LineageTrace:
    """
    血缘追踪结果
    
    包含完整的数据血缘链路追踪结果。
    """
    # 追踪目标
    target_id: str                       # 目标节点ID
    
    # 血缘链路
    ancestors: List[LineageNode] = field(default_factory=list)  # 祖先节点列表
    descendants: List[LineageNode] = field(default_factory=list)  # 后代节点列表
    edges: List[LineageEdge] = field(default_factory=list)  # 血缘边列表
    
    # 统计信息
    depth: int = 0                       # 血缘深度
    total_sources: int = 0               # 总来源数量
    source_types: Dict[str, int] = field(default_factory=dict)  # 来源类型统计
    
    # 可信度信息
    overall_confidence: float = 1.0      # 综合可信度
    confidence_chain: List[float] = field(default_factory=list)  # 可信度链
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "target_id": self.target_id,
            "ancestors": [n.to_dict() for n in self.ancestors],
            "descendants": [n.to_dict() for n in self.descendants],
            "edges": [e.to_dict() for e in self.edges],
            "depth": self.depth,
            "total_sources": self.total_sources,
            "source_types": self.source_types,
            "overall_confidence": self.overall_confidence,
            "confidence_chain": self.confidence_chain,
        }


# ==================== 血缘存储 ====================

class LineageStorage(ABC):
    """
    血缘数据存储抽象基类
    
    使用 @abstractmethod 装饰器强制子类实现所有抽象方法，
    在实例化时即可发现未实现的方法，而非运行时抛出 NotImplementedError。
    """
    
    @abstractmethod
    def save_node(self, node: LineageNode) -> bool:
        """保存血缘节点"""
        pass
    
    @abstractmethod
    def save_edge(self, edge: LineageEdge) -> bool:
        """保存血缘边"""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[LineageNode]:
        """获取血缘节点"""
        pass
    
    @abstractmethod
    def get_edges_from(self, node_id: str) -> List[LineageEdge]:
        """获取从节点出发的边"""
        pass
    
    @abstractmethod
    def get_edges_to(self, node_id: str) -> List[LineageEdge]:
        """获取指向节点的边"""
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """删除血缘节点"""
        pass


class SQLiteLineageStorage(LineageStorage):
    """
    SQLite 血缘数据存储实现
    
    使用 SQLite 存储血缘关系，支持高效查询和遍历。
    """
    
    def __init__(self, db_path: str = ""):
        """
        初始化 SQLite 存储
        
        参数：
            db_path: SQLite 数据库文件路径，为空时使用默认路径
        """
        # 如果未提供路径，使用配置中的默认路径
        if not db_path:
            config = get_config()
            db_path = getattr(config, 'lineage', None) and config.lineage.sqlite_path
            if not db_path:
                db_path = "./data/lineage.db"
        
        self._db_path = db_path
        self._lock = Lock()
        
        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            
            # 创建血缘节点表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lineage_nodes (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_id TEXT,
                    source_description TEXT,
                    created_at TEXT,
                    created_by TEXT,
                    modified_at TEXT,
                    modification_history TEXT,
                    confidence REAL,
                    source_confidence REAL,
                    metadata TEXT
                )
            """)
            
            # 创建血缘边表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lineage_edges (
                    id TEXT PRIMARY KEY,
                    source_node TEXT NOT NULL,
                    target_node TEXT NOT NULL,
                    lineage_type TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT,
                    created_by TEXT,
                    rule_id TEXT,
                    rule_name TEXT,
                    metadata TEXT,
                    FOREIGN KEY (source_node) REFERENCES lineage_nodes(id),
                    FOREIGN KEY (target_node) REFERENCES lineage_nodes(id)
                )
            """)
            
            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lineage_source_node 
                ON lineage_edges(source_node)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lineage_target_node 
                ON lineage_edges(target_node)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lineage_source_type 
                ON lineage_nodes(source)
            """)
            
            conn.commit()
            logger.info(f"SQLite 血缘存储初始化完成: {self._db_path}")
    
    def save_node(self, node: LineageNode) -> bool:
        """保存血缘节点"""
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO lineage_nodes VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        node.id,
                        node.source.value,
                        node.source_id,
                        node.source_description,
                        node.created_at,
                        node.created_by,
                        node.modified_at,
                        json.dumps(node.modification_history, ensure_ascii=False),
                        node.confidence,
                        node.source_confidence,
                        json.dumps(node.metadata, ensure_ascii=False),
                    ))
                    conn.commit()
                return True
            except Exception as e:
                logger.error(f"保存血缘节点失败: {e}")
                return False
    
    def save_edge(self, edge: LineageEdge) -> bool:
        """保存血缘边"""
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO lineage_edges VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        edge.id,
                        edge.source_node,
                        edge.target_node,
                        edge.lineage_type.value,
                        edge.description,
                        edge.created_at,
                        edge.created_by,
                        edge.rule_id,
                        edge.rule_name,
                        json.dumps(edge.metadata, ensure_ascii=False),
                    ))
                    conn.commit()
                return True
            except Exception as e:
                logger.error(f"保存血缘边失败: {e}")
                return False
    
    def get_node(self, node_id: str) -> Optional[LineageNode]:
        """获取血缘节点"""
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM lineage_nodes WHERE id = ?",
                    (node_id,)
                )
                row = cursor.fetchone()
                if row:
                    return LineageNode(
                        id=row[0],
                        source=DataSource(row[1]),
                        source_id=row[2] or "",
                        source_description=row[3] or "",
                        created_at=row[4] or "",
                        created_by=row[5] or "",
                        modified_at=row[6] or "",
                        modification_history=json.loads(row[7]) if row[7] else [],
                        confidence=row[8] or 1.0,
                        source_confidence=row[9] or 1.0,
                        metadata=json.loads(row[10]) if row[10] else {},
                    )
                return None
        except Exception as e:
            logger.error(f"获取血缘节点失败: {e}")
            return None
    
    def get_edges_from(self, node_id: str) -> List[LineageEdge]:
        """获取从节点出发的边（祖先关系）"""
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM lineage_edges WHERE target_node = ?",
                    (node_id,)
                )
                edges = []
                for row in cursor.fetchall():
                    edges.append(LineageEdge(
                        id=row[0],
                        source_node=row[1],
                        target_node=row[2],
                        lineage_type=LineageType(row[3]),
                        description=row[4] or "",
                        created_at=row[5] or "",
                        created_by=row[6] or "",
                        rule_id=row[7] or "",
                        rule_name=row[8] or "",
                        metadata=json.loads(row[9]) if row[9] else {},
                    ))
                return edges
        except Exception as e:
            logger.error(f"获取血缘边失败: {e}")
            return []
    
    def get_edges_to(self, node_id: str) -> List[LineageEdge]:
        """获取指向节点的边（后代关系）"""
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM lineage_edges WHERE source_node = ?",
                    (node_id,)
                )
                edges = []
                for row in cursor.fetchall():
                    edges.append(LineageEdge(
                        id=row[0],
                        source_node=row[1],
                        target_node=row[2],
                        lineage_type=LineageType(row[3]),
                        description=row[4] or "",
                        created_at=row[5] or "",
                        created_by=row[6] or "",
                        rule_id=row[7] or "",
                        rule_name=row[8] or "",
                        metadata=json.loads(row[9]) if row[9] else {},
                    ))
                return edges
        except Exception as e:
            logger.error(f"获取血缘边失败: {e}")
            return []
    
    def delete_node(self, node_id: str) -> bool:
        """删除血缘节点及相关边"""
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    # 先删除相关的边
                    conn.execute(
                        "DELETE FROM lineage_edges WHERE source_node = ? OR target_node = ?",
                        (node_id, node_id)
                    )
                    # 再删除节点
                    conn.execute(
                        "DELETE FROM lineage_nodes WHERE id = ?",
                        (node_id,)
                    )
                    conn.commit()
                return True
            except Exception as e:
                logger.error(f"删除血缘节点失败: {e}")
                return False


# ==================== 血缘追踪器 ====================

class LineageTracker:
    """
    数据血缘追踪器
    
    提供完整的数据来源追溯功能：
    - 记录三元组的来源信息
    - 追踪血缘链路
    - 计算综合可信度
    - 可视化血缘关系
    
    设计原则：
    - 避免循环引用：使用已访问集合追踪遍历路径
    - 深度限制：防止无限递归
    - 性能优化：缓存常用查询结果
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        # 单例模式：确保全局只有一个血缘追踪器
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # 避免重复初始化
        if self._initialized:
            return
        
        self._initialized = True
        
        # 从配置获取设置
        config = get_config().audit
        
        # 初始化存储（与审计日志共用数据库路径）
        db_path = config.sqlite_path.replace(".db", "_lineage.db")
        self._storage = SQLiteLineageStorage(db_path)
        
        # 血缘追踪配置
        self._max_depth = 10  # 最大追踪深度
        self._cache: Dict[str, LineageTrace] = {}  # 追踪结果缓存
        self._cache_lock = Lock()
        
        logger.info("LineageTracker 初始化完成")
    
    def record_source(
        self,
        triple_id: str,
        source: DataSource,
        source_id: str = "",
        source_description: str = "",
        created_by: str = "",
        confidence: float = 1.0,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """
        记录三元组的数据来源
        
        这是血缘追踪的基础方法，为每个三元组创建血缘节点。
        """
        now = datetime.now().isoformat()
        
        # 创建血缘节点
        node = LineageNode(
            id=triple_id,
            source=source,
            source_id=source_id,
            source_description=source_description,
            created_at=now,
            created_by=created_by,
            modified_at=now,
            confidence=confidence,
            source_confidence=self._get_source_confidence(source),
            metadata=metadata or {},
        )
        
        # 清除缓存
        with self._cache_lock:
            self._cache.pop(triple_id, None)
        
        return self._storage.save_node(node)
    
    def record_derivation(
        self,
        target_id: str,
        source_ids: List[str],
        lineage_type: LineageType,
        description: str = "",
        created_by: str = "",
        rule_id: str = "",
        rule_name: str = "",
    ) -> bool:
        """
        记录数据派生关系
        
        用于记录推理生成、转换、聚合等派生操作的血缘关系。
        """
        now = datetime.now().isoformat()
        
        success = True
        for source_id in source_ids:
            # 创建血缘边
            edge = LineageEdge(
                id=f"le:{uuid.uuid4().hex[:12]}",
                source_node=source_id,
                target_node=target_id,
                lineage_type=lineage_type,
                description=description,
                created_at=now,
                created_by=created_by,
                rule_id=rule_id,
                rule_name=rule_name,
            )
            
            if not self._storage.save_edge(edge):
                success = False
        
        # 清除缓存
        with self._cache_lock:
            self._cache.pop(target_id, None)
        
        return success
    
    def record_modification(
        self,
        triple_id: str,
        modification_type: str,
        old_value: Any,
        new_value: Any,
        modified_by: str = "",
    ):
        """
        记录三元组的修改历史
        
        保持数据的完整变更追踪。
        """
        node = self._storage.get_node(triple_id)
        if not node:
            logger.warning(f"血缘节点不存在: {triple_id}")
            return False
        
        # 添加修改记录
        modification = {
            "timestamp": datetime.now().isoformat(),
            "type": modification_type,
            "old_value": old_value,
            "new_value": new_value,
            "modified_by": modified_by,
        }
        node.modification_history.append(modification)
        node.modified_at = modification["timestamp"]
        
        # 清除缓存
        with self._cache_lock:
            self._cache.pop(triple_id, None)
        
        return self._storage.save_node(node)
    
    def trace_lineage(
        self,
        triple_id: str,
        direction: str = "upstream",  # "upstream", "downstream", "both"
        max_depth: int = None,
    ) -> LineageTrace:
        """
        追踪数据血缘
        
        核心方法：追溯三元组的数据来源链。
        
        参数：
            triple_id: 要追踪的三元组ID
            direction: 追踪方向
                - "upstream": 追踪上游来源（默认）
                - "downstream": 追踪下游影响
                - "both": 双向追踪
            max_depth: 最大追踪深度
        
        返回：
            LineageTrace 包含完整的血缘链路信息
        """
        # 检查缓存
        cache_key = f"{triple_id}:{direction}"
        with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        max_depth = max_depth or self._max_depth
        
        # 创建追踪结果
        trace = LineageTrace(target_id=triple_id)
        
        # 获取目标节点
        target_node = self._storage.get_node(triple_id)
        if target_node:
            trace.overall_confidence = target_node.confidence
        
        # 使用独立的 visited 集合分别追踪上游和下游，避免互相干扰
        # 上游追踪：从目标节点向来源方向追踪
        if direction in ("upstream", "both"):
            ancestors, edges = self._trace_upstream(
                triple_id, max_depth, set()
            )
            trace.ancestors = ancestors
            trace.edges.extend(edges)
        
        # 下游追踪：从目标节点向影响方向追踪（使用独立的 visited 集合）
        if direction in ("downstream", "both"):
            descendants, edges = self._trace_downstream(
                triple_id, max_depth, set()
            )
            trace.descendants = descendants
            trace.edges.extend(edges)
        
        # 计算统计信息
        trace.depth = self._calculate_depth(trace)
        trace.total_sources = len(trace.ancestors)
        trace.source_types = self._count_source_types(trace.ancestors)
        trace.confidence_chain = self._build_confidence_chain(trace)
        trace.overall_confidence = self._calculate_overall_confidence(trace)
        
        # 缓存结果：在追踪完全完成后才写入缓存，避免缓存污染
        # 使用锁保护缓存写入，确保线程安全
        with self._cache_lock:
            self._cache[cache_key] = trace
        
        return trace
    
    def _trace_upstream(
        self,
        node_id: str,
        max_depth: int,
        visited: Set[str],
    ) -> Tuple[List[LineageNode], List[LineageEdge]]:
        """
        递归追踪上游来源
        
        使用 BFS 遍历避免过深递归。
        """
        ancestors = []
        edges = []
        
        # 防止循环引用
        if node_id in visited or max_depth <= 0:
            return ancestors, edges
        
        visited.add(node_id)
        
        # 获取指向当前节点的边（即来源边）
        incoming_edges = self._storage.get_edges_from(node_id)
        
        for edge in incoming_edges:
            edges.append(edge)
            
            # 获取源节点
            source_node = self._storage.get_node(edge.source_node)
            if source_node and source_node.id not in visited:
                ancestors.append(source_node)
                
                # 递归追踪上游
                sub_ancestors, sub_edges = self._trace_upstream(
                    edge.source_node, max_depth - 1, visited
                )
                ancestors.extend(sub_ancestors)
                edges.extend(sub_edges)
        
        return ancestors, edges
    
    def _trace_downstream(
        self,
        node_id: str,
        max_depth: int,
        visited: Set[str],
    ) -> Tuple[List[LineageNode], List[LineageEdge]]:
        """
        递归追踪下游影响
        """
        descendants = []
        edges = []
        
        # 防止循环引用
        if node_id in visited or max_depth <= 0:
            return descendants, edges
        
        visited.add(node_id)
        
        # 获取从当前节点出发的边（即影响边）
        outgoing_edges = self._storage.get_edges_to(node_id)
        
        for edge in outgoing_edges:
            edges.append(edge)
            
            # 获取目标节点
            target_node = self._storage.get_node(edge.target_node)
            if target_node and target_node.id not in visited:
                descendants.append(target_node)
                
                # 递归追踪下游
                sub_descendants, sub_edges = self._trace_downstream(
                    edge.target_node, max_depth - 1, visited
                )
                descendants.extend(sub_descendants)
                edges.extend(sub_edges)
        
        return descendants, edges
    
    def _get_source_confidence(self, source: DataSource) -> float:
        """
        获取来源类型的默认可信度
        
        不同来源类型有不同的可信度基准。
        """
        # 来源类型可信度映射（可配置化）
        confidence_map = {
            DataSource.MANUAL: 1.0,          # 手动输入最可靠
            DataSource.IMPORT: 0.95,         # 导入数据次之
            DataSource.LLM_EXTRACTED: 0.85,  # LLM 提取有一定不确定性
            DataSource.INFERENCE: 0.75,      # 推理生成的可信度较低
            DataSource.LEARNED: 0.70,        # 学习获得的可信度中等
            DataSource.DERIVED: 0.80,        # 派生计算
            DataSource.UNKNOWN: 0.50,        # 未知来源可信度最低
        }
        return confidence_map.get(source, 0.50)
    
    def _calculate_depth(self, trace: LineageTrace) -> int:
        """计算血缘深度"""
        if not trace.ancestors:
            return 0
        
        # 使用边的最大链路长度作为深度
        node_depths = {trace.target_id: 0}
        max_depth = 0
        
        for edge in trace.edges:
            if edge.target_node in node_depths:
                source_depth = node_depths[edge.target_node] + 1
                if edge.source_node not in node_depths:
                    node_depths[edge.source_node] = source_depth
                    max_depth = max(max_depth, source_depth)
        
        return max_depth
    
    def _count_source_types(self, nodes: List[LineageNode]) -> Dict[str, int]:
        """统计来源类型分布"""
        counts = defaultdict(int)
        for node in nodes:
            counts[node.source.value] += 1
        return dict(counts)
    
    def _build_confidence_chain(self, trace: LineageTrace) -> List[float]:
        """
        构建可信度链
        
        按血缘顺序排列的可信度列表。
        """
        chain = []
        
        # 从最近的祖先开始
        for node in trace.ancestors[:10]:  # 限制长度
            chain.append(node.confidence * node.source_confidence)
        
        return chain
    
    def _calculate_overall_confidence(self, trace: LineageTrace) -> float:
        """
        计算综合可信度
        
        基于血缘链计算数据的整体可信度。
        使用衰减模型：距离越远的来源，影响越小。
        """
        if not trace.ancestors:
            # 没有血缘记录，使用节点自身的置信度
            target_node = self._storage.get_node(trace.target_id)
            return target_node.confidence if target_node else 0.5
        
        # 使用指数衰减计算综合置信度
        decay_factor = 0.9  # 每层衰减10%
        total_weight = 0.0
        weighted_confidence = 0.0
        
        # 目标节点自身的置信度
        target_node = self._storage.get_node(trace.target_id)
        if target_node:
            weighted_confidence += target_node.confidence
            total_weight += 1.0
        
        # 按深度加权祖先节点的置信度
        for node in trace.ancestors:
            depth = 1  # 简化处理
            weight = decay_factor ** depth
            node_confidence = node.confidence * node.source_confidence
            weighted_confidence += weight * node_confidence
            total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.5
    
    def get_source_info(self, triple_id: str) -> Optional[Dict[str, Any]]:
        """
        获取三元组的来源信息
        
        快速查询单个三元组的来源。
        """
        node = self._storage.get_node(triple_id)
        return node.to_dict() if node else None
    
    def get_modification_history(self, triple_id: str) -> List[Dict[str, Any]]:
        """
        获取三元组的修改历史
        
        完整的变更追踪记录。
        """
        node = self._storage.get_node(triple_id)
        return node.modification_history if node else []
    
    def clear_cache(self):
        """清除追踪结果缓存"""
        with self._cache_lock:
            self._cache.clear()
    
    def delete_lineage(self, triple_id: str) -> bool:
        """
        删除血缘记录
        
        当三元组被删除时调用。
        """
        # 清除缓存
        with self._cache_lock:
            self._cache.pop(triple_id, None)
        
        return self._storage.delete_node(triple_id)
    
    def export_lineage(self, triple_id: str) -> Dict[str, Any]:
        """
        导出血缘信息
        
        用于数据导出和报告生成。
        """
        trace = self.trace_lineage(triple_id, direction="both")
        return trace.to_dict()


# 全局血缘追踪器实例
lineage_tracker = LineageTracker()


# ==================== 便捷函数 ====================

def record_triple_source(
    triple_id: str,
    source: Union[DataSource, str],
    **kwargs,
) -> bool:
    """
    便捷函数：记录三元组来源
    """
    if isinstance(source, str):
        source = DataSource(source)
    return lineage_tracker.record_source(triple_id, source, **kwargs)


def trace_triple_lineage(
    triple_id: str,
    direction: str = "upstream",
) -> Dict[str, Any]:
    """
    便捷函数：追踪三元组血缘
    """
    trace = lineage_tracker.trace_lineage(triple_id, direction)
    return trace.to_dict()


def record_inference_lineage(
    result_id: str,
    source_ids: List[str],
    rule_id: str = "",
    rule_name: str = "",
    created_by: str = "",
) -> bool:
    """
    便捷函数：记录推理血缘
    """
    return lineage_tracker.record_derivation(
        target_id=result_id,
        source_ids=source_ids,
        lineage_type=LineageType.INFERRED_FROM,
        description=f"通过规则 {rule_name} 推理生成",
        created_by=created_by,
        rule_id=rule_id,
        rule_name=rule_name,
    )
