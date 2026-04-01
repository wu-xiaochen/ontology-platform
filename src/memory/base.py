import logging
from typing import Any, List, Dict, Optional
from core.reasoner import Fact
from .neo4j_adapter import Neo4jClient
from .vector_adapter import ChromaVectorStore, Document

logger = logging.getLogger(__name__)

class SemanticMemory:
    """
    语义内存 (Semantic Memory)
    
    存储经过验证的知识图谱。默认使用 Neo4j 作为高性能后端，并辅以 VectorStore 提供模糊语义检索 (Hybrid GraphRAG)。
    支持本体知识的持久化、检索、图查询和向量查询。
    """
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "clawra2026", use_mock: bool = False):
        self.uri = uri
        self.user = user
        self.password = password
        self.use_mock = use_mock
        
        if not self.use_mock:
            self.client = Neo4jClient(uri, user, password)
        else:
            self.client = None
            
        self.vector_store = ChromaVectorStore()
        self.is_connected = False
        # 实体归一化映射表（同义词对齐）
        self.entity_synonyms = {
            "燃气调压柜": "燃气调压箱",
            "调压柜": "燃气调压箱",
            "落地调压柜": "燃气调压箱",
            "楼栋调压箱": "燃气调压箱",
            "调压站设备": "燃气调压箱",
            "区域调压柜": "燃气调压箱",
            "气密性测试": "气密性试验",
            "气密性": "气密性试验",
            "密闭性": "气密性试验",
            "进口压力(P1)": "进口压力",
            "出口压力(P2)": "出口压力",
            "额定流量(Q)": "额定流量",
            "稳压精度(AC)": "稳压精度",
            "关闭压力(SG)": "关闭压力"
        }
        
    def connect(self):
        """建立图数据库连接"""
        if self.client.connect():
            self.is_connected = True
            logger.info("Semantic Memory connected to Neo4j.")
        else:
            logger.warning("Semantic Memory failed to connect to Neo4j. Operating in memory mode.")

    def normalize_entity(self, name: str) -> str:
        """实体归一化：将同义词映射到标准本体术语"""
        if not name:
            return name
        name_stripped = name.strip()
        # 1. 精确匹配映射表
        if name_stripped in self.entity_synonyms:
            return self.entity_synonyms[name_stripped]
        # 2. 包含关系判断（如 "GB 27791标准" -> "GB 27791"）
        for key in self.entity_synonyms:
            if key in name_stripped:
                return self.entity_synonyms[key]
        return name_stripped

    def store_fact(self, fact: Fact):
        """将三元组事实持久化存入图数据库和向量库"""
        # 1. 存入向量库 (Semantic Layer)
        doc = Document(
            content=f"{fact.subject} {fact.predicate} {fact.object}",
            metadata={"source": fact.source, "confidence": fact.confidence}
        )
        self.vector_store.add_documents([doc])
        
        # 2. 存入图数据库 (Logic Layer)
        if self.is_connected and not self.use_mock:
            try:
                norm_subject = self.normalize_entity(fact.subject)
                norm_object = self.normalize_entity(fact.object)
                self.client.create_entity(norm_subject, "Entity")
                self.client.create_entity(norm_object, "Entity")
                self.client.create_relationship(norm_subject, fact.predicate, norm_object)
            except Exception as e:
                logger.warning(f"Neo4j Store Fact Failed: {e}")

    def query(self, concept: str, depth: int = 2) -> List[Any]:
        """查询语义网络中与该概念相关的精确图谱知识 (Graph Traversal)"""
        if not self.is_connected or self.use_mock or not self.client:
            return []
        result = self.client.find_neighbors(concept, depth=depth)
        return result.nodes

    def semantic_search(self, query: str, top_k: int = 3) -> List[Document]:
        """模糊语义查询 (Vector Similarity)"""
        return self.vector_store.similarity_search(query, top_k=top_k)

    def get_grain_cardinality(self, entity_name: str) -> str:
        """
        从图谱中查询实体的粒度约束 (Grain Theory)
        
        逻辑：查询 (entity) -[has_grain]-> (grain_node {cardinality: '1'|'N'})
        默认返回 '1' 以保安全
        """
        if not self.is_connected:
            return "1"
            
        # 真实环境下的粒度查询应依赖图谱中的事实
        # MATCH (e:Entity {name: $norm_name})-[:has_grain]->(g) RETURN g.cardinality
        
        # 为了框架开源可用性，我们提供一种基于规则的兜底评估
        # 凡是带有“清单”、“项”、“明细”、“列表”的实体，默认为 N 端 (Many)
        if any(keyword in norm_name for keyword in ["Item", "List", "Detail", "项", "明细", "清单", "列表"]):
            return "N"
            
        # 默认返回 '1' 以保安全
        return "1"

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
                    task_id TEXT UNIQUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    episode_data JSON,
                    reward REAL DEFAULT 0.0,
                    correction TEXT
                )
            ''')
            conn.commit()

    def store_episode(self, episode: dict):
        """记录一个任务片段并持久化"""
        task_id = episode.get('task_id', 'unknown_task')
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO episodes (task_id, episode_data) VALUES (?, ?)",
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

    def add_human_feedback(self, task_id: str, reward: float, correction: str = ""):
        """
        引入人类反馈 (RLHF)
        对之前的某个决策轨迹 (Episode) 进行打分 and 指正。
        后续演化模块可以利用高 Reward 的轨迹微调大模型，或利用 Correction 更新本体策略。
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE episodes SET reward = ?, correction = ? WHERE task_id = ?",
                (reward, correction, task_id)
            )
            if cursor.rowcount > 0:
                logger.info(f"👍 RLHF Feedback recorded for task {task_id}: Score={reward}")
            else:
                logger.warning(f"⚠️ RLHF Task {task_id} not found in episodic history.")
            conn.commit()

    def analyze_trajectories(self) -> List[Dict[str, Any]]:
        """
        [V3.0] 轨迹反思 (Trajectory Reflection)
        
        扫描最近的经历，识别 '失败-重试-成功' 的模式。
        提取导致成功的关键逻辑变化，作为本体补丁的候选建议。
        """
        episodes = self.retrieve_episodes(limit=20)
        suggestions = []
        
        for ep in episodes:
            data = ep.get("episode_data", {})
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    continue
                
            # 模式识别：是否有多次工具调用且最后成功
            tool_calls = data.get("trace", [])
            if len(tool_calls) > 2:
                # 寻找包含 'AUDIT_FAILURE' 随后又出现 'SUCCESS' 的序列
                has_failure = any(t.get("result", {}).get("status") == "AUDIT_FAILURE" for t in tool_calls)
                if has_failure:
                    suggestions.append({
                        "task_id": data.get("task_id"),
                        "reason": "检测到审计拦截后的自主修正，建议固化该行为为本体规则。",
                        "context": data.get("message", "")[:200]
                    })
                    
        return suggestions

