"""
Neo4j客户端 (Neo4j Client)
实现图数据库集成，支持实体关系CRUD和图查询API

基于ontology-clawra v3.3的本体论实践，支持：
- Neo4j Python驱动集成
- 实体和关系的CRUD操作
- 图查询和遍历
- 推理链追溯
- 置信度传播
"""

import logging
from typing import Any, Optional, Dict, List, Set, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
from collections import defaultdict
import json

# Neo4j驱动（可选安装）
try:
    from neo4j import GraphDatabase, Driver, Session, Transaction, Result
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not installed. Install with: pip install neo4j")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NodeLabel(Enum):
    """节点标签"""
    ENTITY = "Entity"
    CONCEPT = "Concept"
    RULE = "Rule"
    INDIVIDUAL = "Individual"
    CLASS = "Class"
    PROPERTY = "Property"


class RelationshipType(Enum):
    """关系类型"""
    HAS_PROPERTY = "HAS_PROPERTY"
    INSTANCE_OF = "INSTANCE_OF"
    SUB_CLASS_OF = "SUB_CLASS_OF"
    SUB_PROPERTY_OF = "SUB_PROPERTY_OF"
    EQUIVALENT_TO = "EQUIVALENT_TO"
    RELATED_TO = "RELATED_TO"
    CAUSED_BY = "CAUSED_BY"
    DEPENDS_ON = "DEPENDS_ON"
    INFERRED_FROM = "INFERRED_FROM"


@dataclass
class GraphNode:
    """图节点"""
    id: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = "unknown"
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "labels": self.labels,
            "properties": self.properties,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at or datetime.now().isoformat()
        }


@dataclass
class GraphRelationship:
    """图关系"""
    id: Optional[str] = None
    type: str = ""
    start_node: str = ""  # 节点ID
    end_node: str = ""    # 节点ID
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = "unknown"
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "start_node": self.start_node,
            "end_node": self.end_node,
            "properties": self.properties,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at or datetime.now().isoformat()
        }


@dataclass
class GraphQueryResult:
    """图查询结果"""
    nodes: List[GraphNode] = field(default_factory=list)
    relationships: List[GraphRelationship] = field(default_factory=list)
    paths: List[List[Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferencePath:
    """推理路径"""
    nodes: List[GraphNode] = field(default_factory=list)
    relationships: List[GraphRelationship] = field(default_factory=list)
    confidence: float = 1.0
    rule_ids: List[str] = field(default_factory=list)
    depth: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "relationships": [r.to_dict() for r in self.relationships],
            "confidence": self.confidence,
            "rule_ids": self.rule_ids,
            "depth": self.depth
        }


class Neo4jClient:
    """
    Neo4j图数据库客户端
    
    实现本体知识的图存储和查询，支持推理链追溯
    
    示例:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client.connect()
        
        # 创建实体
        client.create_entity("Alice", "Person", {"age": 30})
        
        # 查询
        results = client.find_neighbors("Alice", depth=2)
        
        # 推理追溯
        paths = client.trace_inference("Alice", "Bob")
    """
    
    def __init__(self, uri: str = None,
                 user: str = None, password: str = None,
                 database: str = None):
        """
        初始化Neo4j客户端
        
        Args:
            uri: Neo4j连接URI（默认从 ConfigManager 读取）
            user: 用户名（默认从 ConfigManager 读取）
            password: 密码（默认从 ConfigManager 读取）
            database: 数据库名（默认从 ConfigManager 读取）
        """
        # 从统一配置管理器获取 Neo4j 连接参数，消除硬编码
        if uri is None or user is None or password is None or database is None:
            from ..utils.config import get_config
            _cfg = get_config().database
            uri = uri or _cfg.neo4j_uri
            user = user or _cfg.neo4j_user
            password = password or _cfg.neo4j_password
            database = database or "neo4j"  # 数据库名默认 neo4j
        
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver: Optional[Driver] = None
        self._connected = False
        
        # 索引缓存
        self._node_index: Dict[str, GraphNode] = {}
        self._relationship_index: Dict[str, GraphRelationship] = {}
        
        # v3.3新增：推理缓存
        self._inference_cache: Dict[str, List[InferencePath]] = defaultdict(list)
        
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available. Using in-memory mode.")
    
    def connect(self) -> bool:
        """建立连接"""
        if not NEO4J_AVAILABLE:
            logger.error("Neo4j driver not installed")
            return False
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # 测试连接
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")
            self._connected = True
            logger.info(f"Connected to Neo4j: {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._connected = False
            return False
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self._connected = False
            logger.info("Closed Neo4j connection")
    
    @contextmanager
    def session(self):
        """会话上下文管理器"""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
        with self.driver.session(database=self.database) as s:
            yield s
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    # ==================== 实体CRUD ====================
    
    def create_entity(self, name: str, label: str = "Entity",
                      properties: Optional[Dict] = None,
                      confidence: float = 1.0,
                      source: str = "api") -> Optional[GraphNode]:
        """
        创建实体节点
        
        Args:
            name: 实体名称/URI
            label: 节点标签
            properties: 属性字典
            confidence: 置信度
            source: 来源
        
        Returns:
            创建的节点
        """
        # 确保 properties 包含 name 字段
        props = dict(properties) if properties else {}
        props.setdefault("name", name)
        
        node = GraphNode(
            labels=[label],
            properties=props,
            confidence=confidence,
            source=source,
            created_at=datetime.now().isoformat()
        )
        
        if self._connected:
            with self.session() as session:
                query = f"""
                CREATE (n:{label} $props)
                SET n.id = randomUUID()
                SET n.confidence = $confidence
                SET n.source = $source
                SET n.created_at = $created_at
                RETURN n
                """
                result = session.run(
                    query,
                    props=node.properties,
                    confidence=confidence,
                    source=source,
                    created_at=node.created_at
                )
                record = result.single()
                if record:
                    node.id = record["n"]["id"]
        else:
            # 内存模式
            node.id = name
        
        self._node_index[name] = node
        logger.info(f"Created entity: {name} ({label})")
        return node
    
    def get_entity(self, name: str) -> Optional[GraphNode]:
        """获取实体"""
        if name in self._node_index:
            return self._node_index[name]
        
        if self._connected:
            with self.session() as session:
                query = "MATCH (n) WHERE n.name = $name RETURN n LIMIT 1"
                result = session.run(query, name=name)
                record = result.single()
                if record:
                    node = self._record_to_node(record["n"])
                    self._node_index[name] = node
                    return node
        return None
    
    def update_entity(self, name: str, properties: Dict) -> bool:
        """更新实体"""
        if self._connected:
            with self.session() as session:
                query = """
                MATCH (n) WHERE n.name = $name
                SET n += $props
                RETURN n
                """
                result = session.run(query, name=name, props=properties)
                return result.single() is not None
        else:
            if name in self._node_index:
                self._node_index[name].properties.update(properties)
                return True
        return False
    
    def delete_entity(self, name: str) -> bool:
        """删除实体及其关系"""
        if self._connected:
            with self.session() as session:
                query = "MATCH (n) WHERE n.name = $name DETACH DELETE n"
                session.run(query, name=name)
        
        if name in self._node_index:
            del self._node_index[name]
        
        logger.info(f"Deleted entity: {name}")
        return True
    
    # ==================== 关系CRUD ====================
    
    def create_relationship(self, start_name: str, end_name: str,
                           rel_type: str,
                           properties: Optional[Dict] = None,
                           confidence: float = 1.0,
                           source: str = "api") -> Optional[GraphRelationship]:
        """
        创建关系
        
        Args:
            start_name: 起始实体名
            end_name: 结束实体名
            rel_type: 关系类型
            properties: 属性
            confidence: 置信度
            source: 来源
        
        Returns:
            创建的关系
        """
        rel = GraphRelationship(
            type=rel_type,
            start_node=start_name,
            end_node=end_name,
            properties=properties or {},
            confidence=confidence,
            source=source,
            created_at=datetime.now().isoformat()
        )
        
        if self._connected:
            with self.session() as session:
                query = f"""
                MATCH (a), (b)
                WHERE a.name = $start AND b.name = $end
                CREATE (a)-[r:{rel_type} $props]->(b)
                SET r.id = randomUUID()
                SET r.confidence = $confidence
                SET r.source = $source
                SET r.created_at = $created_at
                RETURN r
                """
                result = session.run(
                    query,
                    start=start_name,
                    end=end_name,
                    props=rel.properties,
                    confidence=confidence,
                    source=source,
                    created_at=rel.created_at
                )
                record = result.single()
                if record:
                    rel.id = record["r"]["id"]
        else:
            rel.id = f"{start_name}_{rel_type}_{end_name}"
        
        # 缓存
        cache_key = f"{start_name}_{rel_type}_{end_name}"
        self._relationship_index[cache_key] = rel
        
        logger.info(f"Created relationship: {start_name} -[{rel_type}]-> {end_name}")
        return rel
    
    def get_relationships(self, entity_name: str,
                         rel_type: Optional[str] = None,
                         direction: str = "both") -> List[GraphRelationship]:
        """
        获取实体的关系
        
        Args:
            entity_name: 实体名
            rel_type: 关系类型过滤
            direction: 方向 (outgoing, incoming, both)
        
        Returns:
            关系列表
        """
        results = []
        
        if self._connected:
            with self.session() as session:
                if direction == "outgoing":
                    query = """
                    MATCH (a)-[r]->(b)
                    WHERE a.name = $name
                    RETURN a, r, b
                    """
                elif direction == "incoming":
                    query = """
                    MATCH (a)-[r]->(b)
                    WHERE b.name = $name
                    RETURN a, r, b
                    """
                else:
                    query = """
                    MATCH (a)-[r]-(b)
                    WHERE a.name = $name OR b.name = $name
                    RETURN a, r, b
                    """
                
                result = session.run(query, name=entity_name)
                for record in result:
                    rel = self._record_to_relationship(record["r"])
                    results.append(rel)
        else:
            # 内存模式
            for key, rel in self._relationship_index.items():
                if entity_name in [rel.start_node, rel.end_node]:
                    if rel_type is None or rel.type == rel_type:
                        results.append(rel)
        
        return results
    
    def delete_relationship(self, start_name: str, end_name: str,
                           rel_type: str) -> bool:
        """删除关系"""
        if self._connected:
            with self.session() as session:
                query = """
                MATCH (a)-[r:{rel_type}]->(b)
                WHERE a.name = $start AND b.name = $end
                DELETE r
                """.format(rel_type=rel_type)
                session.run(query, start=start_name, end=end_name)
        
        # 清除缓存
        cache_key = f"{start_name}_{rel_type}_{end_name}"
        if cache_key in self._relationship_index:
            del self._relationship_index[cache_key]
        
        return True
    
    # ==================== 图查询 ====================
    
    def find_neighbors(self, entity_name: str, depth: int = 1,
                       rel_types: Optional[List[str]] = None) -> GraphQueryResult:
        """
        查找邻居节点
        
        Args:
            entity_name: 实体名
            depth: 深度
            rel_types: 关系类型过滤
        
        Returns:
            查询结果
        """
        result = GraphQueryResult()
        
        if self._connected:
            with self.session() as session:
                rel_filter = ""
                if rel_types:
                    rel_filter = f"AND type(r) IN {rel_types}"
                
                query = f"""
                MATCH path = (start)-[r*1..{depth}]->(end)
                WHERE start.name = $name
                {rel_filter}
                RETURN path, nodes(path) as nodes, relationships(path) as rels
                LIMIT 100
                """
                
                res = session.run(query, name=entity_name)
                for record in res:
                    nodes = record["nodes"]
                    rels = record["rels"]
                    
                    for n in nodes:
                        node = self._record_to_node(n)
                        result.nodes.append(node)
                    
                    for r in rels:
                        rel = self._record_to_relationship(r)
                        result.relationships.append(rel)
        else:
            # 内存模式实现
            visited: Set[str] = {entity_name}
            queue: List[tuple[str, int]] = [(entity_name, 0)]
            
            while queue:
                current, current_depth = queue.pop(0)
                
                if current_depth >= depth:
                    continue
                
                # 获取当前实体的关系
                for rel in self._relationship_index.values():
                    if rel.start_node == current:
                        # 检查关系类型过滤
                        if rel_types and rel.type not in rel_types:
                            continue
                        
                        # 添加关系
                        if rel not in result.relationships:
                            result.relationships.append(rel)
                        
                        # 添加目标节点
                        if rel.end_node not in visited:
                            node = self._node_index.get(rel.end_node)
                            if node:
                                result.nodes.append(node)
                            visited.add(rel.end_node)
                            queue.append((rel.end_node, current_depth + 1))
            
            # 也添加起始节点
            start_node = self._node_index.get(entity_name)
            if start_node and start_node not in result.nodes:
                result.nodes.insert(0, start_node)
        
        return result
    
    def find_shortest_path(self, start_name: str, end_name: str) -> Optional[List[str]]:
        """查找最短路径"""
        if not self._connected:
            return None
        
        with self.session() as session:
            query = """
            MATCH path = shortestPath((a)-[*]->(b))
            WHERE a.name = $start AND b.name = $end
            RETURN path
            """
            result = session.run(query, start=start_name, end=end_name)
            record = result.single()
            if record:
                path = record["path"]
                return [n["name"] for n in path.nodes]
        return None
    
    def query_by_properties(self, label: str, properties: Dict) -> List[GraphNode]:
        """按属性查询"""
        results = []
        
        if self._connected:
            with self.session() as session:
                props_str = " AND ".join([f"n.{k} = ${k}" for k in properties.keys()])
                query = f"MATCH (n:{label}) WHERE {props_str} RETURN n"
                
                result = session.run(query, **properties)
                for record in result:
                    node = self._record_to_node(record["n"])
                    results.append(node)
        
        return results
    
    # ==================== 推理链追溯 (v3.3新增) ====================
    
    def trace_inference(self, start_name: str, end_name: str,
                        max_depth: int = 5) -> List[InferencePath]:
        """
        追溯推理路径
        
        查找从起始实体到目标实体的推理链
        
        Args:
            start_name: 起始实体
            end_name: 目标实体
            max_depth: 最大深度
        
        Returns:
            推理路径列表
        """
        # 检查缓存
        cache_key = f"{start_name}_{end_name}_{max_depth}"
        if cache_key in self._inference_cache:
            return self._inference_cache[cache_key]
        
        paths = []
        
        if self._connected:
            with self.session() as session:
                query = f"""
                MATCH path = (start)-[r*1..{max_depth}]->(end)
                WHERE start.name = $start AND end.name = $end
                WITH path, relationships(path) as rels,
                     reduce(c = 1.0, r IN rels | c * r.confidence) as path_conf
                ORDER BY path_conf DESC
                LIMIT 10
                RETURN path, rels, path_conf
                """
                
                result = session.run(query, start=start_name, end=end_name)
                
                for record in result:
                    path = InferencePath()
                    path.confidence = record["path_conf"]
                    path.depth = len(record["rels"])
                    
                    for r in record["rels"]:
                        rel = self._record_to_relationship(r)
                        path.relationships.append(rel)
                        
                        # 提取规则ID
                        if "rule_id" in rel.properties:
                            path.rule_ids.append(rel.properties["rule_id"])
                    
                    # 获取节点
                    for n in record["path"].nodes:
                        node = self._record_to_node(n)
                        path.nodes.append(node)
                    
                    paths.append(path)
        
        # 内存模式 - BFS查找路径
        if not self._connected:
            # 构建邻接表
            adjacency: Dict[str, List[tuple[str, float, GraphRelationship]]] = defaultdict(list)
            for rel in self._relationship_index.values():
                adjacency[rel.start_node].append((rel.end_node, rel.confidence, rel))
                # 双向添加（无向图视为）
                adjacency[rel.end_node].append((rel.start_node, rel.confidence, rel))
            
            # BFS 查找所有路径
            queue: List[tuple[str, List[str], float, List[GraphRelationship]]] = [
                (start_name, [start_name], 1.0, [])
            ]
            
            while queue:
                current, path, path_conf, path_rels = queue.pop(0)
                
                if len(path) - 1 > max_depth:
                    continue
                
                # 找到目标
                if current == end_name:
                    # 构建节点列表
                    nodes = []
                    for node_name in path:
                        node = self._node_index.get(node_name)
                        if node:
                            nodes.append(node)
                    
                    inference_path = InferencePath(
                        nodes=nodes,
                        relationships=path_rels,
                        confidence=path_conf,
                        depth=len(path) - 1
                    )
                    paths.append(inference_path)
                    continue
                
                # 继续扩展
                for neighbor, edge_conf, rel in adjacency.get(current, []):
                    if neighbor not in path:  # 避免循环
                        new_path = path + [neighbor]
                        new_conf = path_conf * edge_conf
                        new_rels = path_rels + [rel]
                        queue.append((neighbor, new_path, new_conf, new_rels))
            
            # 按置信度排序
            paths.sort(key=lambda p: p.confidence, reverse=True)
            paths = paths[:10]  # 最多返回10条
        
        # 缓存结果
        self._inference_cache[cache_key] = paths
        
        logger.info(f"Found {len(paths)} inference paths from {start_name} to {end_name}")
        return paths
    
    def propagate_confidence(self, start_name: str, max_depth: int = 3) -> Dict[str, float]:
        """
        置信度传播
        
        从起始实体出发，计算可达实体的置信度
        
        Args:
            start_name: 起始实体
            max_depth: 最大深度
        
        Returns:
            实体名到置信度的映射
        """
        confidence_map: Dict[str, float] = {start_name: 1.0}
        
        # 构建邻接表（支持内存模式和Neo4j模式）
        adjacency: Dict[str, List[tuple[str, float]]] = defaultdict(list)
        
        if self._connected:
            # Neo4j 模式
            with self.session() as session:
                query = f"""
                MATCH path = (start)-[r*1..{max_depth}]->(end)
                WHERE start.name = $name
                WITH end, collect(path) as paths
                RETURN end.name as entity,
                       REDUCE(c = 1.0, p IN paths | 
                           MAX(c * REDUCE(conf = 1.0, r IN relationships(p) | conf * r.confidence))
                       ) as confidence
                """
                
                result = session.run(query, name=start_name)
                
                for record in result:
                    entity = record["entity"]
                    conf = record["confidence"]
                    confidence_map[entity] = conf
        else:
            # 内存模式：从关系索引构建
            for key, rel in self._relationship_index.items():
                if rel.start_node == start_name:
                    adjacency[start_name].append((rel.end_node, rel.confidence))
                # 添加所有关系到邻接表
                adjacency[rel.start_node].append((rel.end_node, rel.confidence))
            
            # BFS 传播
            visited: Set[str] = {start_name}
            queue: List[tuple[str, float, int]] = [(start_name, 1.0, 0)]
            
            while queue:
                current, current_conf, depth = queue.pop(0)
                
                if depth >= max_depth:
                    continue
                
                for neighbor, edge_conf in adjacency.get(current, []):
                    new_conf = current_conf * edge_conf
                    
                    if neighbor not in visited or new_conf > confidence_map.get(neighbor, 0):
                        confidence_map[neighbor] = new_conf
                        visited.add(neighbor)
                        queue.append((neighbor, new_conf, depth + 1))
        
        return confidence_map
    
    # ==================== 批量操作 ====================
    
    def batch_import_triples(self, triples: List[Dict]):
        """
        批量导入三元组
        
        Args:
            triples: 三元组列表 [{"subject": "...", "predicate": "...", "object": "..."}]
        """
        if not self._connected:
            for t in triples:
                self.create_entity(t["subject"], "Entity")
                self.create_entity(t["object"], "Entity")
                self.create_relationship(
                    t["subject"],
                    t["object"],
                    t.get("predicate", "RELATED_TO"),
                    confidence=t.get("confidence", 1.0)
                )
            return
        
        with self.session() as session:
            # 使用UNWIND进行批量导入
            query = """
            UNWIND $triples AS t
            MERGE (s:Entity {name: t.subject})
            MERGE (o:Entity {name: t.object})
            MERGE (s)-[r:RELATES {type: t.predicate}]->(o)
            SET r.confidence = COALESCE(t.confidence, 1.0)
            SET r.source = COALESCE(t.source, 'batch')
            """
            session.run(query, triples=triples)
        
        logger.info(f"Batch imported {len(triples)} triples")
    
    def create_entity_index(self):
        """创建索引"""
        if not self._connected:
            return
        
        with self.session() as session:
            # 实体名索引
            session.run("CREATE INDEX entity_name IF NOT EXISTS FOR (n:Entity) ON (n.name)")
            # 标签索引
            session.run("CREATE INDEX entity_label IF NOT EXISTS FOR (n:Entity) ON (n.labels)")
            # 置信度索引
            session.run("CREATE INDEX entity_confidence IF NOT EXISTS FOR (n:Entity) ON (n.confidence)")
        
        logger.info("Created indexes")
    
    # ==================== 辅助方法 ====================
    
    def _record_to_node(self, record: Any) -> GraphNode:
        """将Neo4j记录转换为GraphNode"""
        props = dict(record)
        node_id = props.pop("id", None)
        
        return GraphNode(
            id=str(node_id) if node_id else None,
            labels=list(record.labels) if hasattr(record, "labels") else [],
            properties=props,
            confidence=props.get("confidence", 1.0),
            source=props.get("source", "unknown")
        )
    
    def _record_to_relationship(self, record: Any) -> GraphRelationship:
        """将Neo4j记录转换为GraphRelationship"""
        props = dict(record)
        rel_id = props.pop("id", None)
        
        return GraphRelationship(
            id=str(rel_id) if rel_id else None,
            type=record.type if hasattr(record, "type") else "RELATES",
            start_node=props.get("start_node", ""),
            end_node=props.get("end_node", ""),
            properties=props,
            confidence=props.get("confidence", 1.0),
            source=props.get("source", "unknown")
        )
    
    def get_stats(self) -> Dict:
        """获取图统计信息"""
        if not self._connected:
            return {
                "nodes": len(self._node_index),
                "relationships": len(self._relationship_index),
                "mode": "memory"
            }
        
        with self.session() as session:
            node_count = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as c").single()["c"]
            
            return {
                "nodes": node_count,
                "relationships": rel_count,
                "mode": "neo4j",
                "uri": self.uri
            }
    
    # ==================== 事务支持 ====================
    
    def execute_transaction(self, operations: List[Dict]) -> bool:
        """
        执行事务操作
        
        Args:
            operations: 操作列表 [{"operation": "create_entity", "params": {...}}]
        
        Returns:
            是否成功
        """
        if not self._connected:
            logger.warning("Cannot execute transaction in memory mode")
            return False
        
        def work(tx: Transaction):
            for op in operations:
                op_type = op.get("operation")
                params = op.get("params", {})
                
                if op_type == "create_entity":
                    # 创建实体
                    pass
                elif op_type == "create_relationship":
                    # 创建关系
                    pass
        
        with self.session() as session:
            session.execute_write(work)
        
        return True


# ==================== 便捷函数 ====================

def create_neo4j_client(uri: str = None,
                         user: str = None,
                         password: str = None) -> Neo4jClient:
    """
    创建Neo4j客户端
    
    Args:
        uri: 连接URI（默认从 ConfigManager 读取）
        user: 用户名（默认从 ConfigManager 读取）
        password: 密码（默认从 ConfigManager 读取）
    
    Returns:
        Neo4jClient实例
    """
    # 从统一配置管理器获取 Neo4j 连接参数，消除硬编码
    if uri is None or user is None or password is None:
        from ..utils.config import get_config
        _cfg = get_config().database
        uri = uri or _cfg.neo4j_uri
        user = user or _cfg.neo4j_user
        password = password or _cfg.neo4j_password
    return Neo4jClient(uri, user, password)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=== Neo4j客户端测试 ===\n")
    
    # 创建客户端（内存模式）
    client = Neo4jClient()
    
    # 创建实体
    print("--- 创建实体 ---")
    client.create_entity("Alice", "Person", {"age": 30, "role": "Engineer"})
    client.create_entity("Bob", "Person", {"age": 25, "role": "Designer"})
    client.create_entity("GasRegulator", "Equipment", {"model": "DP-3000"})
    
    # 创建关系
    print("--- 创建关系 ---")
    client.create_relationship("Alice", "Bob", "KNOWS", {"since": "2020"})
    client.create_relationship("Alice", "GasRegulator", "MAINTAINS", {"since": "2023"})
    client.create_relationship("Bob", "GasRegulator", "DESIGNS")
    
    # 查询
    print("--- 查询邻居 ---")
    result = client.find_neighbors("Alice", depth=2)
    print(f"找到 {len(result.nodes)} 个节点, {len(result.relationships)} 条关系")
    
    # 统计
    print("--- 统计信息 ---")
    print(client.get_stats())
    
    # 置信度传播
    print("--- 置信度传播 ---")
    conf_map = client.propagate_confidence("Alice", max_depth=2)
    print(f"置信度分布: {conf_map}")
