"""
SQLite Graph Adapter - 物理级本地图存储引擎

实现基于 SQLite 的三元组存储 (Triplestore)，提供 ACID 持久化能力。
作为 Neo4j 不可用时的“真实本地替代方案”，拒绝 Mock。

设计特性：
1. 物理持久化：数据存储在本地 .db 文件中
2. 时序追踪：支持版本号和时间戳，记录知识演化
3. 高性能索引：针对 S-P-O 结构优化查询速度
"""

import sqlite3
import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class SQLiteNode:
    id: str
    name: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class SQLiteRelationship:
    id: str
    start_node: str
    end_node: str
    rel_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    task_id: Optional[str] = None
    version: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class SQLiteGraph:
    """
    基于 SQLite 的高性能本地图存储引擎 (Production-Grade)
    """
    
    def __init__(self, db_path: str = "data/knowledge_graph.db"):
        self.db_path = db_path
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        logger.info(f"✅ SQLite Graph Storage initialized at {self.db_path}")

    def _init_db(self):
        """初始化数据库表结构与索引"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 实体表 (Nodes)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    label TEXT,
                    properties TEXT,
                    version INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. 关系表 (Edges/Relationships)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    start_node TEXT NOT NULL,
                    end_node TEXT NOT NULL,
                    rel_type TEXT NOT NULL,
                    properties TEXT,
                    confidence REAL DEFAULT 1.0,
                    task_id TEXT,
                    version INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (start_node) REFERENCES nodes(id),
                    FOREIGN KEY (end_node) REFERENCES nodes(id)
                )
            ''')
            
            # 3. 创建索引优化 Graph Traversal (S-P-O 模式)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_start ON relationships(start_node)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_end ON relationships(end_node)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_type ON relationships(rel_type)')
            
            conn.commit()

    def add_node(self, name: str, label: str = "Entity", properties: Optional[Dict] = None) -> str:
        """持久化一个节点"""
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        props_json = json.dumps(properties or {}, ensure_ascii=False)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 检查是否已存在同名节点 (Upsert 逻辑)
            cursor.execute("SELECT id, version FROM nodes WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                existing_id, version = row
                cursor.execute("""
                    UPDATE nodes SET properties = ?, version = ?, timestamp = ?, label = ?
                    WHERE id = ?
                """, (props_json, version + 1, datetime.now().isoformat(), label, existing_id))
                return existing_id
            else:
                cursor.execute("""
                    INSERT INTO nodes (id, name, label, properties)
                    VALUES (?, ?, ?, ?)
                """, (node_id, name, label, props_json))
                conn.commit()
                return node_id

    def add_relationship(self, start_name: str, rel_type: str, end_name: str, 
                         properties: Optional[Dict] = None, 
                         confidence: float = 1.0, 
                         task_id: Optional[str] = None) -> str:
        """持久化一条关系"""
        # 确保起始和终点节点存在
        start_id = self.add_node(start_name)
        end_id = self.add_node(end_name)
        
        rel_id = f"rel_{uuid.uuid4().hex[:8]}"
        props_json = json.dumps(properties or {}, ensure_ascii=False)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO relationships (id, start_node, end_node, rel_type, properties, confidence, task_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (rel_id, start_id, end_id, rel_type, props_json, confidence, task_id))
            conn.commit()
            return rel_id

    def find_neighbors(self, entity_name: str, depth: int = 1) -> Dict[str, Any]:
        """BFS 邻居检索 (Local Graph Discovery)"""
        results = {"nodes": [], "relationships": []}
        visited_nodes = set()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取起始节点
            cursor.execute("SELECT * FROM nodes WHERE name = ?", (entity_name,))
            start_node = cursor.fetchone()
            if not start_node:
                return results
            
            visited_nodes.add(start_node['id'])
            results["nodes"].append(dict(start_node))
            
            current_level_ids = [start_node['id']]
            
            for _ in range(depth):
                if not current_level_ids:
                    break
                    
                placeholders = ','.join(['?'] * len(current_level_ids))
                # 查找从这些节点出发的所有关系
                cursor.execute(f"""
                    SELECT r.*, n.name as end_node_name, n.label as end_node_label, n.properties as end_node_props
                    FROM relationships r
                    JOIN nodes n ON r.end_node = n.id
                    WHERE r.start_node IN ({placeholders})
                """, current_level_ids)
                
                rows = cursor.fetchall()
                next_level_ids = []
                
                for row in rows:
                    if row['id'] not in [r['id'] for r in results["relationships"]]:
                        results["relationships"].append(dict(row))
                    
                    if row['end_node'] not in visited_nodes:
                        visited_nodes.add(row['end_node'])
                        results["nodes"].append({
                            "id": row['end_node'],
                            "name": row['end_node_name'],
                            "label": row['end_node_label'],
                            "properties": row['end_node_props']
                        })
                        next_level_ids.append(row['end_node'])
                
                current_level_ids = next_level_ids
                
        return results

    def get_all_relationships(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取所有关系样本，包含节点名称"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, n1.name as start_node_name, n2.name as end_node_name
                FROM relationships r
                JOIN nodes n1 ON r.start_node = n1.id
                JOIN nodes n2 ON r.end_node = n2.id
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, int]:
        """获取存储统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM nodes")
            n_count = cursor.fetchone()[0]
            cursor.execute("SELECT count(*) FROM relationships")
            r_count = cursor.fetchone()[0]
            return {"nodes": n_count, "relationships": r_count}
