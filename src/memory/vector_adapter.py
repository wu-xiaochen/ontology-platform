import logging
import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Any

try:
    import chromadb
except ImportError:
    chromadb = None

logger = logging.getLogger(__name__)

class Document(ABC):
    """基本文档结构"""
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}

class VectorStore(ABC):
    """
    向量存储抽象基类 (Vector Store Interface)
    """
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        pass
        
    @abstractmethod
    def similarity_search(self, query: str, top_k: int = 3) -> List[Document]:
        pass

class ChromaVectorStore(VectorStore):
    """
    工业级向量数据库 (ChromaDB Integration)
    
    使用 ChromaDB 作为本地向量存储层，提供精确的 Embedding 检索，
    结合 Neo4j 的图遍历，实现真正的企业级 Hybrid GraphRAG。
    """
    def __init__(self, persist_directory: str = "data/chroma_db", collection_name: str = "clawra_knowledge"):
        if chromadb is None:
            raise ImportError("chromadb is not installed. Please install it via `pip install chromadb`")
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            return
            
        ids = [f"doc_{hashlib.md5(doc.content.encode()).hexdigest()}" for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [doc.metadata if doc.metadata else {"source": "unknown"} for doc in documents]
        
        self.collection.add(
            documents=contents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"💾 ChromaVectorStore: Added {len(documents)} dense vectors.")

    def similarity_search(self, query: str, top_k: int = 3) -> List[Document]:
        if not self.collection.count():
            return []

        # Chroma query syntax returns dict of lists
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        docs = []
        if results and results.get("documents") and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                content = results["documents"][0][i]
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                docs.append(Document(content=content, metadata=metadata))
                
        logger.info(f"🔍 ChromaVectorStore: Retrieved {len(docs)} semantic matches for query: '{query}'")
        return docs
