import logging
from typing import Any, List
from core.reasoner import Fact
from .neo4j_adapter import Neo4jClient
from .vector_adapter import LightweightVectorStore, Document

logger = logging.getLogger(__name__)

class SemanticMemory:
    """
    语义内存 (Semantic Memory)
    
    存储经过验证的知识图谱。默认使用 Neo4j 作为高性能后端，并辅以 VectorStore 提供模糊语义检索 (Hybrid GraphRAG)。
    支持本体知识的持久化、检索、图查询和向量查询。
    """
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", password: str = "neo4j"):
        self.client = Neo4jClient(uri=uri, user=user, password=password)
        self.vector_store = LightweightVectorStore()
        self.is_connected = False
        
    def connect(self):
        """建立图数据库连接"""
        if self.client.connect():
            self.is_connected = True
            logger.info("Semantic Memory connected to Neo4j.")
        else:
            logger.warning("Semantic Memory failed to connect to Neo4j. Operating in memory mode.")

    def store_fact(self, fact: Fact):
        """将推理事实同步存入图数据库与向量数据库"""
        self.client.create_entity(fact.subject, "Entity")
        self.client.create_entity(fact.object, "Entity")
        self.client.create_relationship(
            fact.subject, fact.object, fact.predicate, 
            confidence=fact.confidence
        )
        # 同步写入向量索引
        vector_doc = Document(
            content=f"{fact.subject} {fact.predicate} {fact.object}",
            metadata={"source": fact.source, "confidence": fact.confidence}
        )
        self.vector_store.add_documents([vector_doc])

    def query(self, concept: str, depth: int = 2) -> List[Any]:
        """查询语义网络中与该概念相关的精确图谱知识 (Graph Traversal)"""
        if not self.is_connected:
            return []
        result = self.client.find_neighbors(concept, depth=depth)
        return result.nodes

    def semantic_search(self, query: str, top_k: int = 3) -> List[Document]:
        """模糊语义查询 (Vector Similarity)"""
        return self.vector_store.similarity_search(query, top_k=top_k)

import json
import sqlite3
from pathlib import Path

class EpisodicMemory:
    """
    情理性内存 (Episodic Memory)
    
    记录 Agent 的具体经历、决策轨迹和推理过程。
    通过 SQLite 实现全生命周期的本地持久化，支持未来的 RLHF 数据积累。
    """
    def __init__(self, db_path: str = "data/episodic_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """初始化 SQLite 数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    episode_data JSON
                )
            ''')
            conn.commit()

    def store_episode(self, episode: dict):
        """记录一个任务片段并持久化"""
        task_id = episode.get('task_id', 'unknown_task')
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO episodes (task_id, episode_data) VALUES (?, ?)",
                (task_id, json.dumps(episode, ensure_ascii=False))
            )
            conn.commit()
            
        logger.info(f"💾 Permanently recorded episode into SQLite: {task_id}")

    def retrieve_episodes(self, limit: int = 10) -> List[dict]:
        """检索最近的经历"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT episode_data FROM episodes ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [json.loads(row[0]) for row in rows]

