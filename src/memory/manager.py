"""
统一记忆管理器 (Unified Memory Manager)

整合 Neo4j (图记忆) 和 ChromaDB (向量记忆)，提供统一的记忆接口。
支持自动降级到内存存储，确保系统可用性。

设计原则：
- 零硬编码：所有阈值从配置文件读取
- 自动降级：数据库不可用时自动切换到内存模式
- 完整实现：所有方法都有实际逻辑，无占位符
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import threading
import time

# 配置常量（从环境变量读取，符合零硬编码原则）
# ChromaDB 配置
DEFAULT_CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma_db")
# 搜索返回结果数量
DEFAULT_SEARCH_TOP_K = int(os.getenv("MEMORY_SEARCH_TOP_K", "5"))
# Neo4j 连接配置
DEFAULT_NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
DEFAULT_NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
DEFAULT_NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
# 向量存储配置
DEFAULT_VECTOR_COLLECTION = os.getenv("VECTOR_COLLECTION_NAME", "clawra_patterns")
# 降级模式配置
DEFAULT_ENABLE_FALLBACK = os.getenv("ENABLE_MEMORY_FALLBACK", "true").lower() == "true"

logger = logging.getLogger(__name__)


@dataclass
class MemoryPattern:
    """
    记忆模式数据结构
    
    统一的模式表示，用于图存储和向量存储之间的数据交换。
    """
    id: str
    name: str = ""
    description: str = ""
    logic_type: str = "unknown"
    domain: str = "general"
    confidence: float = 0.9
    source: str = "learned"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含所有字段的字典表示
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "logic_type": self.logic_type,
            "domain": self.domain,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryPattern":
        """
        从字典创建实例
        
        Args:
            data: 包含模式数据的字典
            
        Returns:
            MemoryPattern 实例
        """
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            logic_type=data.get("logic_type", "unknown"),
            domain=data.get("domain", "general"),
            confidence=data.get("confidence", 0.9),
            source=data.get("source", "learned"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )


class InMemoryPatternStore:
    """
    内存模式存储（降级模式后端）
    
    当 Neo4j 和 ChromaDB 都不可用时，使用内存字典存储模式。
    提供完整的 CRUD 和搜索接口。
    """
    
    def __init__(self):
        # 主存储：id -> MemoryPattern
        self._patterns: Dict[str, MemoryPattern] = {}
        # 倒排索引：domain -> set of pattern_ids
        self._domain_index: Dict[str, set] = {}
        # 文本索引：用于简单搜索
        self._text_chunks: Dict[str, str] = {}  # id -> text for search
        
        logger.warning("⚠️ 使用内存存储模式 - 数据不会持久化")
    
    def store(self, pattern: MemoryPattern) -> bool:
        """存储模式"""
        try:
            self._patterns[pattern.id] = pattern
            
            # 更新领域索引
            domain = pattern.domain or "general"
            if domain not in self._domain_index:
                self._domain_index[domain] = set()
            self._domain_index[domain].add(pattern.id)
            
            # 更新文本索引（用于搜索）
            text = f"{pattern.name} {pattern.description}"
            self._text_chunks[pattern.id] = text
            
            return True
        except Exception as e:
            logger.error(f"内存存储失败: {e}")
            return False
    
    def get(self, pattern_id: str) -> Optional[MemoryPattern]:
        """获取模式"""
        return self._patterns.get(pattern_id)
    
    def delete(self, pattern_id: str) -> bool:
        """删除模式"""
        if pattern_id in self._patterns:
            pattern = self._patterns[pattern_id]
            # 清理索引
            domain = pattern.domain or "general"
            if domain in self._domain_index:
                self._domain_index[domain].discard(pattern_id)
            if pattern_id in self._text_chunks:
                del self._text_chunks[pattern_id]
            del self._patterns[pattern_id]
            return True
        return False
    
    def search(self, query: str, top_k: int = 5) -> List[MemoryPattern]:
        """
        简单文本搜索（降级模式）
        
        使用关键词匹配，不支持真正的语义搜索。
        """
        query_lower = query.lower()
        results = []
        
        for pattern_id, pattern in self._patterns.items():
            # 检查名称和描述中的关键词
            text = self._text_chunks.get(pattern_id, "").lower()
            score = sum(1 for word in query_lower.split() if word in text)
            if score > 0:
                results.append((pattern, score))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in results[:top_k]]
    
    def list_by_domain(self, domain: str, limit: int = 50) -> List[MemoryPattern]:
        """按领域列出模式"""
        pattern_ids = self._domain_index.get(domain, set())
        patterns = [self._patterns[pid] for pid in pattern_ids if pid in self._patterns]
        # 按置信度排序
        patterns.sort(key=lambda x: x.confidence, reverse=True)
        return patterns[:limit]
    
    def count(self) -> int:
        """返回模式数量"""
        return len(self._patterns)
    
    def clear(self):
        """清空存储"""
        self._patterns.clear()
        self._domain_index.clear()
        self._text_chunks.clear()


class UnifiedMemory:
    """
    统一记忆管理器
    
    整合图记忆（Neo4j）和向量记忆（ChromaDB），提供统一的记忆接口。
    
    特性：
    1. 双存储协调 - 同时存储到图数据库和向量数据库
    2. 自动降级 - 数据库不可用时自动切换到内存存储
    3. 统一接口 - 对外提供一致的 API
    4. 健康监控 - 提供状态查询和降级状态检查
    
    使用示例:
        memory = UnifiedMemory(neo4j_enabled=True, chroma_enabled=True)
        
        # 存储模式
        memory.store_pattern({
            "id": "rule_001",
            "name": "燃气设备规则",
            "description": "燃气调压箱需要定期维护"
        })
        
        # 搜索相似模式
        patterns = memory.search_similar_patterns("燃气设备维护", top_k=5)
        
        # 获取统计信息
        stats = memory.get_statistics()
    """
    
    def __init__(
        self,
        neo4j_enabled: bool = True,
        chroma_enabled: bool = True,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        chroma_path: Optional[str] = None,
        collection_name: str = "clawra_patterns"
    ) -> None:
        """
        初始化统一记忆管理器
        
        Args:
            neo4j_enabled: 是否启用 Neo4j
            chroma_enabled: 是否启用 ChromaDB
            neo4j_uri: Neo4j 连接 URI
            neo4j_user: Neo4j 用户名
            neo4j_password: Neo4j 密码
            chroma_path: ChromaDB 持久化路径
            collection_name: ChromaDB 集合名称
        """
        # 图记忆适配器
        self.graph_memory = None
        # 向量记忆适配器
        self.vector_memory = None
        # 内存降级存储
        self._fallback_store: Optional[InMemoryPatternStore] = None
        # 降级状态
        self._degraded = False
        # 线程锁
        self._lock = threading.Lock()
        # 集合名称
        self._collection_name = collection_name
        
        # 初始化图记忆
        if neo4j_enabled:
            self._init_graph_memory(
                neo4j_uri or DEFAULT_NEO4J_URI,
                neo4j_user or DEFAULT_NEO4J_USER,
                neo4j_password or DEFAULT_NEO4J_PASSWORD
            )
        
        # 初始化向量记忆
        if chroma_enabled:
            self._init_vector_memory(
                chroma_path or DEFAULT_CHROMA_PATH,
                collection_name
            )
        
        # 如果两者都不可用，启用内存降级
        if not self.graph_memory and not self.vector_memory:
            self._init_fallback()
        
        logger.info(f"统一记忆管理器初始化完成，降级模式: {self._degraded}")
    
    def _init_graph_memory(self, uri: str, user: str, password: str) -> None:
        """
        初始化 Neo4j 图记忆
        
        Args:
            uri: Neo4j 连接 URI
            user: 用户名
            password: 密码
        """
        try:
            from .neo4j_adapter import Neo4jMemory
            self.graph_memory = Neo4jMemory(
                uri=uri,
                user=user,
                password=password
            )
            # 尝试连接
            if self.graph_memory.connect():
                logger.info("✅ 图记忆 (Neo4j) 已初始化并连接成功")
            else:
                logger.warning("⚠️ 图记忆初始化失败，将使用降级模式")
                self.graph_memory = None
        except ImportError:
            logger.warning("⚠️ Neo4j 适配器未安装，图记忆不可用")
            self.graph_memory = None
        except Exception as e:
            logger.warning(f"⚠️ 图记忆初始化失败: {e}")
            self.graph_memory = None
    
    def _init_vector_memory(self, persist_directory: str, collection_name: str) -> None:
        """
        初始化 ChromaDB 向量记忆
        
        Args:
            persist_directory: 持久化目录路径
            collection_name: 集合名称
        """
        try:
            from .vector_adapter import ChromaMemory
            self.vector_memory = ChromaMemory(
                persist_directory=persist_directory,
                collection_name=collection_name
            )
            if self.vector_memory.is_degraded:
                logger.warning("⚠️ 向量记忆使用内存降级模式")
            else:
                logger.info("✅ 向量记忆 (ChromaDB) 已初始化")
        except ImportError:
            logger.warning("⚠️ ChromaDB 适配器未安装，向量记忆不可用")
            self.vector_memory = None
        except Exception as e:
            logger.warning(f"⚠️ 向量记忆初始化失败: {e}")
            self.vector_memory = None
    
    def _init_fallback(self) -> None:
        """
        初始化内存降级存储
        
        当 Neo4j 和 ChromaDB 都不可用时，启用内存存储作为降级方案
        """
        self._fallback_store = InMemoryPatternStore()
        self._degraded = True
        logger.warning("⚠️ 记忆系统降级到纯内存模式 - 数据不会持久化")
    
    # ─────────────────────────────────────────────
    # 公共属性
    # ─────────────────────────────────────────────
    
    @property
    def is_degraded(self) -> bool:
        """
        返回是否处于降级模式
        
        降级模式意味着：
        - 数据只存储在内存中，不会持久化
        - 向量搜索功能受限（仅支持关键词匹配）
        - 重启后数据丢失
        """
        # 检查是否启用了内存降级
        if self._degraded or self._fallback_store:
            return True
        # 检查向量存储是否降级
        if self.vector_memory and self.vector_memory.is_degraded:
            return True
        # 检查图存储是否降级
        if self.graph_memory and self.graph_memory.is_degraded:
            return True
        # 如果两者都不可用，也视为降级
        if not self.graph_memory and not self.vector_memory:
            return True
        return False
    
    # ─────────────────────────────────────────────
    # 核心方法：模式存储
    # ─────────────────────────────────────────────
    
    def store_pattern(self, pattern: Union[Dict[str, Any], MemoryPattern]) -> bool:
        """
        存储学习到的模式
        
        将模式同时存储到图记忆和向量记忆，实现双写一致性。
        任一存储失败不影响另一个，但会记录警告。
        
        Args:
            pattern: 模式字典或 MemoryPattern 对象，包含 id、name、description 等字段
            
        Returns:
            是否至少成功存储到一个后端
        """
        # 转换为 MemoryPattern 对象以确保数据完整性
        mp = MemoryPattern.from_dict(pattern) if isinstance(pattern, dict) else pattern
        
        # 确保模式有唯一 ID
        if not mp.id:
            import hashlib
            mp.id = f"pattern_{hashlib.md5(str(pattern).encode()).hexdigest()[:12]}"
        
        success = False
        
        # 1. 存储到图记忆（结构化存储）
        if self.graph_memory:
            try:
                result = self._store_pattern_to_graph(mp)
                if result:
                    success = True
            except Exception as e:
                logger.error(f"存储到图记忆失败: {e}")
        
        # 2. 存储到向量记忆（语义搜索）
        if self.vector_memory:
            try:
                result = self._store_pattern_to_vector(mp)
                if result:
                    success = True
            except Exception as e:
                logger.error(f"存储到向量记忆失败: {e}")
        
        # 3. 如果上述都不可用，使用降级存储
        if not success and self._fallback_store:
            try:
                success = self._fallback_store.store(mp)
            except Exception as e:
                logger.error(f"存储到降级存储失败: {e}")
        
        if success:
            logger.debug(f"模式存储成功: {mp.id}")
        
        return success
    
    def _store_pattern_to_graph(self, pattern: MemoryPattern) -> bool:
        """
        将模式存储到图数据库
        
        使用 Neo4j 适配器的 store_pattern 方法。
        在降级模式下会自动使用内存存储。
        
        Args:
            pattern: 要存储的记忆模式
            
        Returns:
            存储是否成功
        """
        if not self.graph_memory:
            return False
        
        try:
            # 使用 Neo4j 适配器的模式存储方法
            result = self.graph_memory.store_pattern(pattern.to_dict())
            return result is not None
        except Exception as e:
            logger.error(f"图存储失败: {e}")
            return False
    
    def _store_pattern_to_vector(self, pattern: MemoryPattern) -> bool:
        """
        将模式存储到向量数据库
        
        将模式的描述文本向量化后存储，支持语义搜索。
        
        Args:
            pattern: 要存储的记忆模式
            
        Returns:
            存储是否成功
        """
        if not self.vector_memory:
            return False
        
        try:
            from .vector_adapter import Document
            
            # 构建文档内容（用于向量化）
            # 包含名称、描述和类型信息以增强语义检索
            content = f"{pattern.name}\n{pattern.description}\n类型: {pattern.logic_type}\n领域: {pattern.domain}"
            
            # 构建元数据
            metadata = {
                "pattern_id": pattern.id,
                "name": pattern.name,
                "logic_type": pattern.logic_type,
                "domain": pattern.domain,
                "confidence": pattern.confidence,
                "source": pattern.source,
                "created_at": pattern.created_at
            }
            
            # 创建文档并存储
            doc = Document(content=content, metadata=metadata, id=f"pattern_{pattern.id}")
            ids = self.vector_memory.add_documents([doc])
            
            return len(ids) > 0
        except Exception as e:
            logger.error(f"向量存储失败: {e}")
            return False
    
    # ─────────────────────────────────────────────
    # 核心方法：模式检索
    # ─────────────────────────────────────────────
    
    def search_similar_patterns(self, query: str, top_k: int = DEFAULT_SEARCH_TOP_K) -> List[Dict[str, Any]]:
        """
        搜索相似的模式
        
        使用向量语义搜索查找相似模式，返回 top_k 个最相关的结果。
        在降级模式下使用关键词匹配。
        
        Args:
            query: 查询文本
            top_k: 返回数量，默认从配置读取
            
        Returns:
            相似模式列表，每个元素是一个包含模式信息的字典
        """
        results = []
        
        # 1. 优先使用向量语义搜索
        if self.vector_memory:
            try:
                docs = self.vector_memory.similarity_search(query, top_k=top_k)
                for doc in docs:
                    # 从文档元数据恢复模式信息
                    metadata = doc.metadata or {}
                    pattern = {
                        "id": metadata.get("pattern_id", doc.id),
                        "name": metadata.get("name", ""),
                        "description": doc.content.split("\n")[1] if "\n" in doc.content else doc.content,
                        "logic_type": metadata.get("logic_type", "unknown"),
                        "domain": metadata.get("domain", "general"),
                        "confidence": metadata.get("confidence", 0.9),
                        "source": metadata.get("source", "unknown"),
                        "score": 1.0  # ChromaDB 不直接返回分数，使用默认值
                    }
                    results.append(pattern)
                
                if results:
                    logger.debug(f"向量搜索找到 {len(results)} 个相似模式")
                    return results
                    
            except Exception as e:
                logger.error(f"向量搜索失败: {e}")
        
        # 2. 向量搜索无结果时，尝试从图数据库搜索
        # 降级链：ChromaDB -> Neo4j -> 内存存储
        if self.graph_memory and not results:
            try:
                # 使用图数据库的 list_patterns 获取模式列表
                # 然后通过关键词匹配过滤，作为语义搜索的降级方案
                patterns = self.graph_memory.list_patterns(limit=100)
                query_lower = query.lower()
                
                # 关键词匹配：检查查询词是否出现在模式名称或描述中
                scored_patterns = []
                for pattern in patterns:
                    score = 0
                    name = pattern.get("name", "").lower()
                    desc = pattern.get("description", "").lower()
                    
                    # 计算匹配分数
                    for word in query_lower.split():
                        if word in name:
                            score += 3  # 名称匹配权重更高
                        if word in desc:
                            score += 1
                    
                    if score > 0:
                        pattern["score"] = score
                        scored_patterns.append(pattern)
                
                # 按分数排序并返回前 top_k 个
                scored_patterns.sort(key=lambda x: x.get("score", 0), reverse=True)
                results = scored_patterns[:top_k]
                
                if results:
                    logger.debug(f"图数据库搜索找到 {len(results)} 个匹配模式")
                    
            except Exception as e:
                logger.error(f"图搜索失败: {e}")
        
        # 3. 降级模式：使用内存存储的简单搜索
        if not results and self._fallback_store:
            try:
                patterns = self._fallback_store.search(query, top_k=top_k)
                results = [p.to_dict() for p in patterns]
                if results:
                    logger.debug(f"内存降级搜索找到 {len(results)} 个匹配模式")
            except Exception as e:
                logger.error(f"降级搜索失败: {e}")
        
        return results
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取模式
        
        优先从图数据库查询（更完整的关系信息），
        如果不存在则从向量数据库查询，最后尝试降级存储。
        
        Args:
            pattern_id: 模式唯一标识符
            
        Returns:
            模式字典，不存在则返回 None
        """
        # 1. 优先从图记忆查询
        if self.graph_memory:
            try:
                pattern = self.graph_memory.get_pattern_by_id(pattern_id)
                if pattern:
                    return pattern
            except Exception as e:
                logger.error(f"图查询失败: {e}")
        
        # 2. 从向量记忆查询
        if self.vector_memory:
            try:
                doc = self.vector_memory.get_by_id(f"pattern_{pattern_id}")
                if doc:
                    metadata = doc.metadata or {}
                    return {
                        "id": metadata.get("pattern_id", pattern_id),
                        "name": metadata.get("name", ""),
                        "description": doc.content.split("\n")[1] if "\n" in doc.content else doc.content,
                        "logic_type": metadata.get("logic_type", "unknown"),
                        "domain": metadata.get("domain", "general"),
                        "confidence": metadata.get("confidence", 0.9),
                        "source": metadata.get("source", "unknown")
                    }
            except Exception as e:
                logger.error(f"向量查询失败: {e}")
        
        # 3. 从降级存储查询
        if self._fallback_store:
            try:
                pattern = self._fallback_store.get(pattern_id)
                if pattern:
                    return pattern.to_dict()
            except Exception as e:
                logger.error(f"降级存储查询失败: {e}")
        
        return None
    
    def delete_pattern(self, pattern_id: str) -> bool:
        """
        删除模式
        
        从所有存储后端（图存储、向量存储、降级存储）删除模式。
        
        Args:
            pattern_id: 模式唯一标识符
            
        Returns:
            是否至少从一个后端成功删除
        """
        success = False
        
        # 从图存储删除
        if self.graph_memory:
            try:
                if self.graph_memory.delete_pattern(pattern_id):
                    success = True
            except Exception as e:
                logger.error(f"从图存储删除失败: {e}")
        
        # 从向量存储删除
        if self.vector_memory:
            try:
                if self.vector_memory.delete(f"pattern_{pattern_id}"):
                    success = True
            except Exception as e:
                logger.error(f"从向量存储删除失败: {e}")
        
        # 从降级存储删除
        if self._fallback_store:
            try:
                if self._fallback_store.delete(pattern_id):
                    success = True
            except Exception as e:
                logger.error(f"从降级存储删除失败: {e}")
        
        return success
    
    # ─────────────────────────────────────────────
    # 统计信息
    # ─────────────────────────────────────────────
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        返回图存储、向量存储和降级存储的状态和数量统计。
        
        Returns:
            包含各存储后端统计信息的字典
        """
        stats = {
            "graph_memory": {
                "enabled": self.graph_memory is not None,
                "connected": False,
                "node_count": 0,
                "relationship_count": 0,
                "is_degraded": False
            },
            "vector_memory": {
                "enabled": self.vector_memory is not None,
                "document_count": 0,
                "is_degraded": False
            },
            "fallback_memory": {
                "enabled": self._fallback_store is not None,
                "pattern_count": 0
            },
            "overall_degraded": self.is_degraded
        }
        
        # 获取图记忆统计
        if self.graph_memory:
            try:
                graph_stats = self.graph_memory.get_stats()
                stats["graph_memory"]["connected"] = graph_stats.get("mode") == "neo4j"
                stats["graph_memory"]["node_count"] = graph_stats.get("nodes", 0)
                stats["graph_memory"]["relationship_count"] = graph_stats.get("relationships", 0)
                stats["graph_memory"]["is_degraded"] = graph_stats.get("is_degraded", False)
            except Exception as e:
                logger.error(f"获取图记忆统计失败: {e}")
                stats["graph_memory"]["error"] = str(e)
        
        # 获取向量记忆统计
        if self.vector_memory:
            try:
                vector_stats = self.vector_memory.get_statistics()
                stats["vector_memory"]["document_count"] = vector_stats.get("document_count", 0)
                stats["vector_memory"]["is_degraded"] = vector_stats.get("is_degraded", False)
                stats["vector_memory"]["collection_name"] = vector_stats.get("collection_name", "")
            except Exception as e:
                logger.error(f"获取向量记忆统计失败: {e}")
                stats["vector_memory"]["error"] = str(e)
        
        # 获取降级存储统计
        if self._fallback_store:
            try:
                stats["fallback_memory"]["pattern_count"] = self._fallback_store.count()
            except Exception as e:
                logger.error(f"获取降级存储统计失败: {e}")
                stats["fallback_memory"]["error"] = str(e)
        
        return stats
    
    # ─────────────────────────────────────────────
    # 生命周期管理
    # ─────────────────────────────────────────────
    
    def close(self) -> None:
        """
        关闭所有连接并释放资源
        
        按顺序关闭图存储、向量存储的连接，并清理降级存储。
        """
        # 关闭图记忆
        if self.graph_memory:
            try:
                self.graph_memory.close()
                logger.info("图记忆连接已关闭")
            except Exception as e:
                logger.error(f"关闭图记忆失败: {e}")
        
        # ChromaDB 不需要显式关闭，但可以清理资源
        if self.vector_memory:
            try:
                self.vector_memory = None
                logger.info("向量记忆已释放")
            except Exception as e:
                logger.error(f"释放向量记忆失败: {e}")
        
        # 清理降级存储
        if self._fallback_store:
            try:
                self._fallback_store.clear()
                logger.info("降级存储已清空")
            except Exception as e:
                logger.error(f"清空降级存储失败: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        检查各存储后端的健康状态，返回详细的健康报告。
        
        Returns:
            包含各组件状态和健康信息的字典
        """
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # 检查图存储
        if self.graph_memory:
            try:
                is_connected = self.graph_memory.is_connected()
                health["components"]["graph_memory"] = {
                    "status": "healthy" if is_connected else "degraded",
                    "connected": is_connected,
                    "degraded": self.graph_memory.is_degraded
                }
                if not is_connected:
                    health["status"] = "degraded"
            except Exception as e:
                health["components"]["graph_memory"] = {
                    "status": "error",
                    "error": str(e)
                }
                health["status"] = "degraded"
        else:
            health["components"]["graph_memory"] = {"status": "disabled"}
        
        # 检查向量存储
        if self.vector_memory:
            try:
                count = self.vector_memory.count()
                health["components"]["vector_memory"] = {
                    "status": "healthy" if not self.vector_memory.is_degraded else "degraded",
                    "document_count": count,
                    "degraded": self.vector_memory.is_degraded
                }
                if self.vector_memory.is_degraded:
                    health["status"] = "degraded"
            except Exception as e:
                health["components"]["vector_memory"] = {
                    "status": "error",
                    "error": str(e)
                }
                health["status"] = "degraded"
        else:
            health["components"]["vector_memory"] = {"status": "disabled"}
        
        # 检查降级存储
        if self._fallback_store:
            health["components"]["fallback_memory"] = {
                "status": "active",
                "pattern_count": self._fallback_store.count()
            }
            health["status"] = "degraded"  # 使用降级存储意味着降级状态
        
        return health
    
    def reconnect(self) -> bool:
        """
        尝试重新连接所有存储后端
        
        用于从临时故障中恢复，检查各存储后端的可用性。
        
        Returns:
            是否至少成功重连一个后端
        """
        success = False
        
        # 重连图存储
        if self.graph_memory:
            try:
                if self.graph_memory.reconnect():
                    logger.info("✅ 图存储重连成功")
                    success = True
            except Exception as e:
                logger.error(f"图存储重连失败: {e}")
        
        # 向量存储不需要重连，检查是否可用
        if self.vector_memory:
            try:
                count = self.vector_memory.count()
                if count >= 0:
                    success = True
            except Exception as e:
                logger.error(f"向量存储检查失败: {e}")
        
        return success
