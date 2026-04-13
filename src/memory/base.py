import logging
import threading
from typing import Any, List, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class LockProvider:
    """Abstract interface for distributed-ready locking"""
    @contextmanager
    def get_lock(self):
        yield

class ThreadLockProvider(LockProvider):
    """Local threading based lock"""
    def __init__(self):
        self._lock = threading.Lock()
    
    @contextmanager
    def get_lock(self):
        with self._lock:
            yield

class SemanticMemory:
    """
    语义内存 (Semantic Memory)
    
    存储经过验证的知识图谱。默认使用 Neo4j 作为高性能后端，同时使用 SQLiteGraph 提供可靠的本地持久化。
    实现 Hybrid GraphRAG (Neo4j/SQLite + ChromaDB)。
    """
    def __init__(self, uri: str = None, user: str = None, password: str = None, use_mock: bool = False, lock_provider: LockProvider = None):
        self._lock_provider = lock_provider or ThreadLockProvider()
        # 延迟导入避免循环导入问题
        from .neo4j_adapter import Neo4jClient
        from .vector_adapter import ChromaVectorStore
        from .sqlite_graph_adapter import SQLiteGraph
        from ..utils.config import get_config
        
        # 从 ConfigManager 读取数据库配置，避免硬编码
        _cfg = get_config().database
        self.uri = uri or _cfg.neo4j_uri
        self.user = user or _cfg.neo4j_user
        self.password = password or _cfg.neo4j_password
        self.use_mock = use_mock
        
        # 1. 初始化 Neo4j Client (Remote/Server Mode)
        if not self.use_mock:
            self.client = Neo4jClient(uri=uri, user=user, password=password)
        else:
            self.client = None
            
        # 2. 初始化 SQLite Graph (Local Persistence Mode - Zero Mock)
        self.local_graph = SQLiteGraph()
            
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
        if self.client and self.client.connect():
            self.is_connected = True
            logger.info("Semantic Memory connected to Neo4j (Global Mode).")
        else:
            logger.info("Neo4j not available. Using SQLite persistent local graph (Individual Mode).")

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

    def get_total_facts_count(self) -> int:
        """获取总事实（关系）数量 - 优先 Neo4j，兜底 SQLite"""
        if self.is_connected and self.client:
            try:
                query = "MATCH (n)-[r]->(m) RETURN count(r) as c"
                with self.client.session() as session:
                    result = session.run(query)
                    record = result.single()
                    return record["c"] if record else 0
            except Exception as e:
                logger.warning(f"Failed to get facts count from Neo4j: {e}")
        
        # 兜底：从本地 SQLite 数据库获取 (Real Persistence)
        stats = self.local_graph.get_stats()
        return stats.get("relationships", 0)

    def get_sample_triples(self, limit: int = 50) -> List[Any]:
        """获取图谱样本并转换为 Fact 对象"""
        # 延迟导入避免循环导入
        from ..core.reasoner import Fact
        
        # 1. 优先从 Neo4j 获取
        if self.is_connected and self.client:
            triples = self.client.get_sample_triples(limit)
            return [Fact(t["subject"], t["predicate"], t["object"], source="neo4j_sample") for t in triples]
        
        # 2. 兜底从 SQLite 获取 (Real Persistence Mode)
        triples = self.local_graph.get_all_relationships(limit=limit)
        return [Fact(t["start_node_name"], t["rel_type"], t["end_node_name"], source="sqlite_sample") for t in triples]

    def store_fact(self, fact: Any, task_id: Optional[str] = None):
        """将三元组事实持久化存入图数据库(Neo4j + SQLite)和向量库"""
        # 延迟导入避免循环导入
        from .vector_adapter import Document
        
        with self._lock_provider.get_lock():
            # 1. 存入向量库 (Semantic Layer - Persistent ChromaDB)
            doc = Document(
                content=f"{fact.subject} {fact.predicate} {fact.object}",
                metadata={"source": fact.source, "confidence": fact.confidence}
            )
            self.vector_store.add_documents([doc])
            
            # 2. 存入本地物理图谱 (Logic Layer - Persistent SQLite)
            norm_subject = self.normalize_entity(fact.subject)
            norm_object = self.normalize_entity(fact.object)
            self.local_graph.add_relationship(
                norm_subject, fact.predicate, norm_object, 
                confidence=fact.confidence,
                task_id=task_id
            )
            
            # 3. 存入远程图数据库 (Global Logic Layer - Neo4j)
            if self.is_connected and self.client:
                try:
                    self.client.create_entity(norm_subject, "Entity")
                    self.client.create_entity(norm_object, "Entity")
                    self.client.create_relationship(norm_subject, fact.predicate, norm_object)
                except Exception as e:
                    logger.warning(f"Neo4j Store Fact Failed: {e}")

    def query(self, concept: str, depth: int = 1) -> List[Any]:
        """查询语义网络中与该概念相关的精确图谱知识 - 优先 Neo4j，兜底 SQLite"""
        # 延迟引入 Fact 类型
        from ..core.reasoner import Fact
        facts = []
        
        # 1. 优先从 Neo4j 获取 (Global Mode)
        if self.is_connected and self.client:
            try:
                result = self.client.find_neighbors(concept, depth=depth)
                for rel in result.relationships:
                    facts.append(Fact(
                        subject=rel.start_node,
                        predicate=rel.type,
                        object=rel.end_node,
                        confidence=rel.confidence,
                        source="neo4j_rag"
                    ))
            except Exception as e:
                logger.warning(f"Neo4j 检索失败，尝试 SQLite 兜底: {e}")
            
        # 2. 兜底：从物理 SQLite 检索邻居 (Local Mode/Fallback)
        if not facts:
            try:
                # 实体名称转换，确保与存储的归一化名称一致
                norm_concept = self.normalize_entity(concept)
                results = self.local_graph.find_neighbors(norm_concept, depth=depth)
                for rel in results["relationships"]:
                    facts.append(Fact(
                        subject=rel.get("start_node_name", concept),
                        predicate=rel["rel_type"],
                        object=rel["end_node_name"],
                        confidence=rel.get("confidence", 1.0),
                        source="sqlite_rag"
                    ))
            except Exception as e:
                logger.error(f"本地 SQLite 检索异常: {e}")
                
        return facts

    def semantic_search(self, query: str, top_k: int = 3) -> List[Any]:
        """模糊语义查询 (Vector Similarity)"""
        return self.vector_store.similarity_search(query, top_k=top_k)

    def get_grain_cardinality(self, entity_name: str) -> str:
        """从图谱中查询实体的粒度约束 (Grain Theory)"""
        # 逻辑：查询 (entity) -[has_grain]-> (grain_node {cardinality: '1'|'N'})
        # 为保持稳定，暂保留原有逻辑，后续可扩展为 SQLite 的特定谓词查询
        norm_name = self.normalize_entity(entity_name)
        n_keywords = ["Item", "List", "Detail", "Line", "Entry", "Record",
                      "Order", "Transaction", "Log", "Event",
                      "项", "明细", "清单", "列表", "订单", "交易", "日志", "记录"]
        if any(keyword in norm_name for keyword in n_keywords):
            return "N"
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
    def __init__(self, db_path: str = "data/episodic_memory.db", lock_provider: LockProvider = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_provider = lock_provider or ThreadLockProvider()
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
        with self._lock_provider.get_lock():
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
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
        with self._lock_provider.get_lock():
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE episodes SET reward = ?, correction = ? WHERE task_id = ?",
                    (reward, correction, task_id)
                )
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"👍 RLHF Feedback recorded for task {task_id}: Score={reward}")
                else:
                    logger.warning(f"⚠️ RLHF Task {task_id} not found in episodic history.")

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
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    # 解析 episode 数据失败时记录警告并跳过
                    logger.warning(f"解析 episode 数据失败: {e}")
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

    def export_rlhf_dataset(self, filepath: str) -> int:
        """
        导出人类反馈 (RLHF) 高分样本为 LLM SFT（如 DPO/PPO）标准的 JSONL 格式。
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT task_id, episode_data, reward, correction FROM episodes WHERE reward > 0 OR correction != ''")
            rows = cursor.fetchall()
            
        count = 0
        with open(filepath, 'w', encoding='utf-8') as f:
            for task_id, data_str, reward, correction in rows:
                try:
                    data = json.loads(data_str)
                    messages = [{"role": "system", "content": "You are Clawra, an autonomous cognitive engine."}]
                    messages.append({"role": "user", "content": data.get("message", "Task execution")})
                    if correction:
                        messages.append({"role": "assistant", "content": f"Correction received: {correction}"})
                    else:
                        messages.append({"role": "assistant", "content": json.dumps(data.get("trace", []), ensure_ascii=False)})
                    f.write(json.dumps({"messages": messages, "reward": reward}, ensure_ascii=False) + "\\n")
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to export RLHF episode {task_id}: {e}")
                    
        logger.info(f"💾 Exported {count} RLHF episodes to {filepath}")
        return count

