import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class Document(ABC):
    """基本文档结构"""
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}

class VectorStore(ABC):
    """
    向量存储抽象基类 (Vector Store Interface)
    
    定义了向量数据库（如 Chroma, Milvus, Qdrant）的标准接口。
    用于在 Clawra 中补充纯知识图谱 (Neo4j) 对模糊自然语言语义泛化能力的不足，实现 Hybrid GraphRAG。
    """
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """将文本文档向量化并存入库中"""
        pass
        
    @abstractmethod
    def similarity_search(self, query: str, top_k: int = 3) -> List[Document]:
        """根据查询的语义相似度返回最相关的 K 个文档"""
        pass

class LightweightVectorStore(VectorStore):
    """
    轻量级/桩实现向量存储 (Lightweight Mock Vector Store)
    
    不引入额外重型依赖（如 PyTorch/Numpy），使用基础的词频匹配（TF-IDF 的极简版）
    模拟向量搜索。在真实的企业级落地中，请替换为使用本地 `SentenceTransformer` 
    或 `text-embedding-3-small` 接口的真实实现类。
    """
    def __init__(self):
        self.collection: List[Document] = []
        
    def add_documents(self, documents: List[Document]) -> None:
        """将文档加入集合"""
        self.collection.extend(documents)
        logger.info(f"💾 VectorStore: Added {len(documents)} documents.")

    def _calculate_overlap(self, query: str, content: str) -> float:
        """极简的单词重合度打分器 (Placeholder for actual Cosine Similarity)"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        if not query_words:
            return 0.0
        overlap = len(query_words.intersection(content_words))
        return overlap / len(query_words)
        
    def similarity_search(self, query: str, top_k: int = 3) -> List[Document]:
        """模拟相似度召回"""
        if not self.collection:
            return []
            
        scored_docs = []
        for doc in self.collection:
            score = self._calculate_overlap(query, doc.content)
            scored_docs.append((score, doc))
            
        # 按分数降序排序
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # 返回前 K 个且得分 > 0 的文档
        results = [doc_tuple[1] for doc_tuple in scored_docs[:top_k] if doc_tuple[0] > 0]
        logger.info(f"🔍 VectorStore: Retrieved {len(results)} matches for query: '{query}'")
        return results
