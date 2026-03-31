import logging
from typing import Any, List, Optional, Dict
from ..core.reasoner import Fact
from .neo4j_adapter import Neo4jClient

logger = logging.getLogger(__name__)

class SemanticMemory:
    """
    语义内存 (Semantic Memory)
    
    存储经过验证的知识图谱。默认使用 Neo4j 作为高性能后端。
    支持本体知识的持久化、检索和复杂的图查询。
    """
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", password: str = "neo4j"):
        self.client = Neo4jClient(uri=uri, user=user, password=password)
        self.is_connected = False
        
    def connect(self):
        """建立图数据库连接"""
        if self.client.connect():
            self.is_connected = True
            logger.info("Semantic Memory connected to Neo4j.")
        else:
            logger.warning("Semantic Memory failed to connect to Neo4j. Operating in memory mode.")

    def store_fact(self, fact: Fact):
        """将推理事实存入图数据库"""
        self.client.create_entity(fact.subject, "Entity")
        self.client.create_entity(fact.object, "Entity")
        self.client.create_relationship(
            fact.subject, fact.object, fact.predicate, 
            confidence=fact.confidence
        )

    def query(self, concept: str, depth: int = 2) -> List[Any]:
        """查询语义网络中与该概念相关的知识"""
        if not self.is_connected:
            return []
        result = self.client.find_neighbors(concept, depth=depth)
        return result.nodes

class EpisodicMemory:
    """
    情理性内存 (Episodic Memory)
    
    记录 Agent 的具体经历、决策轨迹和推理过程。
    """
    def __init__(self, storage_backend: str = "local"):
        self.storage_backend = storage_backend
        self.episodes = []
        
    def store_episode(self, episode: dict):
        """记录一个任务片段"""
        self.episodes.append(episode)
        logger.info(f"Recorded episode: {episode.get('task_id', 'unknown')}")
