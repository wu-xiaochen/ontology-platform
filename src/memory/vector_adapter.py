"""
向量存储适配器 (Vector Store Adapter)

实现 ChromaDB 集成，提供向量嵌入和语义搜索能力。
支持文档的 CRUD 操作和相似度检索。

设计原则：
- 零硬编码：所有阈值从配置文件读取
- 自动降级：ChromaDB 不可用时降级到内存存储
- 完整实现：提供完整的 CRUD 接口
"""

import logging
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# ChromaDB 可选依赖，如果不可用则降级到内存模式
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 配置常量（从环境变量读取，避免硬编码）
# ─────────────────────────────────────────────

import os

# 默认向量搜索返回数量
DEFAULT_TOP_K = int(os.getenv("MEMORY_SEARCH_TOP_K", "5"))
# 集合名称默认值
DEFAULT_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "clawra_knowledge")
# 持久化路径默认值
DEFAULT_PERSIST_PATH = os.getenv("CHROMA_PATH", "./data/chroma_db")


@dataclass
class Document:
    """
    文档结构定义
    
    Attributes:
        content: 文档文本内容
        metadata: 元数据字典，包含来源、置信度等信息
        id: 文档唯一标识符（可选，自动生成）
    """
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    
    def __post_init__(self):
        # 如果没有提供 ID，则根据内容生成唯一 ID
        if self.id is None and self.content:
            # 使用 MD5 哈希生成 ID，确保相同内容产生相同 ID（去重）
            self.id = f"doc_{hashlib.md5(self.content.encode()).hexdigest()}"


class VectorStore(ABC):
    """
    向量存储抽象基类 (Vector Store Interface)
    
    定义所有向量存储后端必须实现的接口，
    便于未来扩展其他向量数据库（如 Pinecone、Weaviate 等）。
    """
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        批量添加文档
        
        Args:
            documents: 文档列表
            
        Returns:
            成功添加的文档 ID 列表
        """
        pass
    
    @abstractmethod
    def similarity_search(self, query: str, top_k: int = DEFAULT_TOP_K) -> List[Document]:
        """
        语义相似度搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            相似文档列表
        """
        pass
    
    @abstractmethod
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        """
        根据 ID 获取文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            文档对象，不存在则返回 None
        """
        pass
    
    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        获取文档总数
        
        Returns:
            文档数量
        """
        pass


class InMemoryVectorStore(VectorStore):
    """
    内存向量存储（降级模式）
    
    当 ChromaDB 不可用时，使用内存字典作为后备存储。
    不支持真正的向量搜索，仅支持关键词匹配。
    """
    
    def __init__(self):
        # 内存存储：id -> Document
        self._store: Dict[str, Document] = {}
        # 降级标记
        self._degraded = True
        logger.warning("⚠️ ChromaDB 不可用，降级到内存存储模式。语义搜索功能受限。")
    
    @property
    def is_degraded(self) -> bool:
        """返回是否处于降级模式"""
        return self._degraded
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        将文档添加到内存存储
        
        直接使用字典存储，不支持向量嵌入。
        """
        added_ids = []
        for doc in documents:
            if doc.id is None:
                doc.id = f"doc_{hashlib.md5(doc.content.encode()).hexdigest()}"
            self._store[doc.id] = doc
            added_ids.append(doc.id)
        logger.debug(f"内存存储: 添加 {len(added_ids)} 个文档")
        return added_ids
    
    def similarity_search(self, query: str, top_k: int = DEFAULT_TOP_K) -> List[Document]:
        """
        简化的相似度搜索（降级模式）
        
        使用关键词匹配代替向量相似度，功能受限。
        """
        # 降级模式：使用简单的关键词匹配
        query_lower = query.lower()
        results = []
        
        for doc in self._store.values():
            # 计算关键词重叠度作为相似度代理
            # 这不是真正的语义搜索，仅作为降级方案
            doc_lower = doc.content.lower()
            # 统计查询词在文档中出现的次数
            overlap = sum(1 for word in query_lower.split() if word in doc_lower)
            if overlap > 0:
                results.append((doc, overlap))
        
        # 按重叠度排序，返回 top_k 个结果
        results.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in results[:top_k]]
    
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        """从内存存储获取文档"""
        return self._store.get(doc_id)
    
    def delete(self, doc_id: str) -> bool:
        """从内存存储删除文档"""
        if doc_id in self._store:
            del self._store[doc_id]
            return True
        return False
    
    def count(self) -> int:
        """返回内存存储中的文档数量"""
        return len(self._store)


class ChromaMemory(VectorStore):
    """
    ChromaDB 向量数据库适配器
    
    使用 ChromaDB 作为向量存储后端，支持：
    - 自动向量嵌入（使用默认 embedding 函数）
    - 语义相似度搜索
    - 持久化存储
    - 集合管理
    
    如果 ChromaDB 初始化失败，自动降级到 InMemoryVectorStore。
    """
    
    def __init__(
        self,
        persist_directory: str = DEFAULT_PERSIST_PATH,
        collection_name: str = DEFAULT_COLLECTION_NAME
    ):
        """
        初始化 ChromaDB 向量存储
        
        Args:
            persist_directory: 持久化目录路径
            collection_name: 集合名称
        """
        # 标记是否处于降级模式
        self._degraded = False
        # 降级存储实例
        self._fallback_store: Optional[InMemoryVectorStore] = None
        
        # ChromaDB 组件
        self.client = None
        self.collection = None
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # 尝试初始化 ChromaDB
        if not CHROMADB_AVAILABLE:
            self._init_fallback()
            return
        
        # 尝试多种初始化方式以兼容不同版本的 ChromaDB
        self._init_chroma(persist_directory, collection_name)
    
    def _init_chroma(self, persist_directory: str, collection_name: str):
        """
        初始化 ChromaDB 连接
        
        尝试多种连接方式以适配不同版本的 ChromaDB。
        """
        try:
            # 方式1：使用 tenant/database 参数（新版 ChromaDB）
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                tenant="default_tenant",
                database="default_database"
            )
            logger.debug(f"ChromaDB 初始化方式: PersistentClient with tenant/database")
        except Exception as e:
            logger.warning(f"ChromaDB 初始化失败（tenant/database 方式）: {e}")
            try:
                # 方式2：不使用 tenant/database 参数（旧版 ChromaDB）
                self.client = chromadb.PersistentClient(path=persist_directory)
                logger.debug(f"ChromaDB 初始化方式: PersistentClient without tenant/database")
            except Exception as e2:
                logger.warning(f"ChromaDB 初始化失败（简化方式）: {e2}")
                try:
                    # 方式3：使用内存客户端（最后手段）
                    self.client = chromadb.Client()
                    logger.warning("⚠️ ChromaDB 使用内存模式，数据不会持久化")
                except Exception as e3:
                    logger.error(f"所有 ChromaDB 初始化方式都失败: {e3}")
                    self._init_fallback()
                    return
        
        # 获取或创建集合
        try:
            self.collection = self.client.get_or_create_collection(name=collection_name)
            logger.info(f"✅ ChromaDB 向量存储已初始化: {collection_name}")
        except Exception as e:
            logger.error(f"ChromaDB 集合创建失败: {e}")
            self._init_fallback()
    
    def _init_fallback(self):
        """初始化降级存储"""
        self._fallback_store = InMemoryVectorStore()
        self._degraded = True
        self.client = None
        self.collection = None
    
    @property
    def is_degraded(self) -> bool:
        """返回是否处于降级模式"""
        return self._degraded
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        批量添加文档到向量存储
        
        Args:
            documents: 文档列表
            
        Returns:
            成功添加的文档 ID 列表
        """
        if not documents:
            return []
        
        # 降级模式：委托给内存存储
        if self._degraded and self._fallback_store:
            return self._fallback_store.add_documents(documents)
        
        # 确保 collection 可用
        if not self.collection:
            logger.error("ChromaDB collection 未初始化")
            return []
        
        # 准备数据
        ids = []
        contents = []
        metadatas = []
        
        for doc in documents:
            # 生成或使用现有 ID
            doc_id = doc.id or f"doc_{hashlib.md5(doc.content.encode()).hexdigest()}"
            ids.append(doc_id)
            contents.append(doc.content)
            # 确保元数据不为空，ChromaDB 要求非空元数据
            metadata = doc.metadata if doc.metadata else {"source": "unknown", "timestamp": str(time.time())}
            metadatas.append(metadata)
        
        try:
            # 批量添加到 ChromaDB
            self.collection.add(
                documents=contents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"💾 ChromaDB: 添加 {len(ids)} 个向量文档")
            return ids
        except Exception as e:
            logger.error(f"ChromaDB 添加文档失败: {e}")
            return []
    
    def similarity_search(self, query: str, top_k: int = DEFAULT_TOP_K) -> List[Document]:
        """
        语义相似度搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量（默认从配置读取）
            
        Returns:
            相似文档列表
        """
        # 降级模式：委托给内存存储
        if self._degraded and self._fallback_store:
            return self._fallback_store.similarity_search(query, top_k)
        
        # 确保 collection 可用且非空
        if not self.collection:
            logger.warning("ChromaDB collection 未初始化")
            return []
        
        # 检查集合是否有数据
        try:
            if self.collection.count() == 0:
                logger.debug("ChromaDB 集合为空")
                return []
        except Exception:
            pass
        
        try:
            # ChromaDB 查询接口返回字典格式的结果
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # 解析结果
            docs = []
            if results and results.get("documents") and results["documents"][0]:
                documents = results["documents"][0]
                metadatas = results.get("metadatas", [[]])[0]
                ids = results.get("ids", [[]])[0]
                
                for i in range(len(documents)):
                    doc = Document(
                        content=documents[i],
                        metadata=metadatas[i] if i < len(metadatas) else {},
                        id=ids[i] if i < len(ids) else None
                    )
                    docs.append(doc)
            
            logger.info(f"🔍 ChromaDB: 检索到 {len(docs)} 个语义匹配结果")
            return docs
            
        except Exception as e:
            logger.error(f"ChromaDB 查询失败: {e}")
            return []
    
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        """
        根据 ID 获取文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            文档对象，不存在则返回 None
        """
        # 降级模式：委托给内存存储
        if self._degraded and self._fallback_store:
            return self._fallback_store.get_by_id(doc_id)
        
        if not self.collection:
            return None
        
        try:
            # ChromaDB 的 get 方法支持按 ID 查询
            results = self.collection.get(ids=[doc_id])
            
            if results and results.get("documents") and results["documents"]:
                content = results["documents"][0]
                metadata = results.get("metadatas", [{}])[0]
                return Document(content=content, metadata=metadata, id=doc_id)
            
            return None
            
        except Exception as e:
            logger.debug(f"ChromaDB 按 ID 获取失败: {e}")
            return None
    
    def delete(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            是否删除成功
        """
        # 降级模式：委托给内存存储
        if self._degraded and self._fallback_store:
            return self._fallback_store.delete(doc_id)
        
        if not self.collection:
            return False
        
        try:
            # ChromaDB 的 delete 方法
            self.collection.delete(ids=[doc_id])
            logger.debug(f"ChromaDB: 删除文档 {doc_id}")
            return True
        except Exception as e:
            logger.error(f"ChromaDB 删除文档失败: {e}")
            return False
    
    def delete_many(self, doc_ids: List[str]) -> int:
        """
        批量删除文档
        
        Args:
            doc_ids: 文档 ID 列表
            
        Returns:
            成功删除的数量
        """
        if not doc_ids:
            return 0
        
        # 降级模式：逐个删除
        if self._degraded and self._fallback_store:
            count = 0
            for doc_id in doc_ids:
                if self._fallback_store.delete(doc_id):
                    count += 1
            return count
        
        if not self.collection:
            return 0
        
        try:
            self.collection.delete(ids=doc_ids)
            logger.info(f"ChromaDB: 批量删除 {len(doc_ids)} 个文档")
            return len(doc_ids)
        except Exception as e:
            logger.error(f"ChromaDB 批量删除失败: {e}")
            return 0
    
    def count(self) -> int:
        """
        获取文档总数
        
        Returns:
            文档数量
        """
        # 降级模式：委托给内存存储
        if self._degraded and self._fallback_store:
            return self._fallback_store.count()
        
        if not self.collection:
            return 0
        
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"ChromaDB 获取数量失败: {e}")
            return 0
    
    def clear(self) -> bool:
        """
        清空集合中的所有文档
        
        Returns:
            是否成功
        """
        if self._degraded and self._fallback_store:
            self._fallback_store._store.clear()
            return True
        
        if not self.client or not self.collection:
            return False
        
        try:
            # ChromaDB 没有直接清空的方法，需要删除并重建集合
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            logger.info(f"ChromaDB: 集合 {self.collection_name} 已清空")
            return True
        except Exception as e:
            logger.error(f"ChromaDB 清空集合失败: {e}")
            return False
    
    def update_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        更新文档（先删除后添加）
        
        Args:
            doc_id: 文档 ID
            content: 新内容
            metadata: 新元数据
            
        Returns:
            是否成功
        """
        # 先删除旧文档
        self.delete(doc_id)
        
        # 添加新文档（使用相同 ID）
        doc = Document(content=content, metadata=metadata or {}, id=doc_id)
        ids = self.add_documents([doc])
        return len(ids) > 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "type": "chromadb" if not self._degraded else "memory_fallback",
            "collection_name": self.collection_name if not self._degraded else "memory_store",
            "document_count": self.count(),
            "is_degraded": self._degraded,
            "persist_directory": self.persist_directory if not self._degraded else None
        }


# ─────────────────────────────────────────────
# 别名定义（向后兼容）
# ─────────────────────────────────────────────

# ChromaVectorStore 是 ChromaMemory 的别名，保持向后兼容
ChromaVectorStore = ChromaMemory
