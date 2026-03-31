"""
RDF适配器 (RDF Adapter)
实现JSONL到RDF/OWL的转换，支持本体Schema设计和RDF序列化

基于ontology-clawra v3.3的本体论实践，支持：
- JSONL到RDF的三元组转换
- OWL本体建模
- RDF序列化（Turtle, JSON-LD, RDF/XML）
- 本体Schema验证
"""

import json
import re
import logging
from pathlib import Path
from typing import Any, Optional, Dict, List, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RDFTermType(Enum):
    """RDF术语类型"""
    URI = "uri"
    BLANK = "blank"
    LITERAL = "literal"


@dataclass
class RDFTerm:
    """RDF术语"""
    value: str
    term_type: RDFTermType
    datatype: Optional[str] = None
    language: Optional[str] = None
    
    def to_nt(self) -> str:
        """转换为N-Triples格式"""
        if self.term_type == RDFTermType.URI:
            return f"<{self.value}>"
        elif self.term_type == RDFTermType.BLANK:
            return f"_:{self.value}"
        else:
            if self.datatype:
                return f'"{self.value}"^^<{self.datatype}>'
            elif self.language:
                return f'"{self.value}"@{self.language}'
            else:
                return f'"{self.value}"'
    
    def __str__(self) -> str:
        return self.to_nt()


@dataclass
class RDFTriple:
    """RDF三元组"""
    subject: RDFTerm
    predicate: RDFTerm
    object: RDFTerm
    graph: Optional[str] = None
    confidence: float = 1.0
    source: str = "unknown"
    timestamp: Optional[str] = None
    
    def to_nt(self) -> str:
        """转换为N-Triples格式"""
        return f"{self.subject.to_nt()} {self.predicate.to_nt()} {self.object.to_nt()} ."
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "subject": {"value": self.subject.value, "type": self.subject.term_type.value},
            "predicate": {"value": self.predicate.value, "type": self.predicate.term_type.value},
            "object": {"value": self.object.value, "type": self.object.term_type.value},
            "graph": self.graph,
            "confidence": self.confidence,
            "source": self.source,
            "timestamp": self.timestamp or datetime.now().isoformat()
        }


@dataclass
class OntologySchema:
    """本体Schema定义"""
    uri: str
    label: str
    description: str = ""
    version: str = "1.0"
    classes: Dict[str, 'OntologyClassDef'] = field(default_factory=dict)
    properties: Dict[str, 'OntologyPropertyDef'] = field(default_factory=dict)
    prefixes: Dict[str, str] = field(default_factory=dict)
    rules: List[Dict] = field(default_factory=list)
    
    def add_class(self, cls: 'OntologyClassDef'):
        """添加类定义"""
        self.classes[cls.uri] = cls
    
    def add_property(self, prop: 'OntologyPropertyDef'):
        """添加属性定义"""
        self.properties[prop.uri] = prop


@dataclass
class OntologyClassDef:
    """本体类定义"""
    uri: str
    label: str
    description: str = ""
    super_classes: List[str] = field(default_factory=list)
    equivalent_classes: List[str] = field(default_factory=list)
    disjoint_with: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # v3.3 新增：置信度标注
    confidence: str = "CONFIRMED"  # CONFIRMED, ASSUMED, SPECULATIVE
    source: str = "ontology"
    

@dataclass
class OntologyPropertyDef:
    """本体属性定义"""
    uri: str
    label: str
    property_type: str = "object"  # object, datatype, annotation
    description: str = ""
    domain: List[str] = field(default_factory=list)
    range: List[str] = field(default_factory=list)
    super_properties: List[str] = field(default_factory=list)
    equivalent_properties: List[str] = field(default_factory=list)
    inverse_of: Optional[str] = None
    transitive: bool = False
    symmetric: bool = False
    functional: bool = False
    
    # v3.3 新增
    confidence: str = "CONFIRMED"
    source: str = "ontology"


class RDFAdapter:
    """
    RDF适配器
    
    实现JSONL到RDF的转换，支持OWL本体建模
    
    示例:
        adapter = RDFAdapter()
        adapter.load_jsonl("knowledge.jsonl")
        adapter.convert_to_rdf()
        adapter.save_turtle("knowledge.ttl")
    """
    
    # 标准RDF/OWL前缀
    DEFAULT_PREFIXES = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "ex": "http://example.org/",
    }
    
    def __init__(self, base_uri: str = "http://example.org/"):
        """
        初始化RDF适配器
        
        Args:
            base_uri: 基础URI
        """
        self.base_uri = base_uri
        self.prefixes = dict(self.DEFAULT_PREFIXES)
        self.triples: List[RDFTriple] = []
        self.schema = OntologySchema(
            uri=base_uri,
            label="Base Ontology"
        )
        
        # 本体统计
        self.stats = {
            "entities": 0,
            "relations": 0,
            "concepts": 0,
            "rules": 0
        }
    
    def add_prefix(self, prefix: str, namespace: str):
        """添加前缀"""
        self.prefixes[prefix] = namespace
    
    def _create_uri(self, local_name: str) -> str:
        """创建完整URI"""
        if local_name.startswith("http"):
            return local_name
        return f"{self.base_uri}{local_name}"
    
    def _create_term(self, value: str, term_type: RDFTermType = RDFTermType.URI,
                     datatype: Optional[str] = None) -> RDFTerm:
        """创建RDF术语"""
        if term_type == RDFTermType.URI:
            # 展开前缀
            for prefix, namespace in self.prefixes.items():
                if value.startswith(prefix + ":"):
                    value = value.replace(prefix + ":", namespace)
                    break
            # 如果没有http://前缀，添加base_uri
            if not value.startswith("http"):
                value = self._create_uri(value)
        elif term_type == RDFTermType.LITERAL:
            # 检测数据类型
            if datatype is None:
                datatype = self._infer_datatype(value)
        
        return RDFTerm(value=value, term_type=term_type, datatype=datatype)
    
    def _infer_datatype(self, value: str) -> Optional[str]:
        """推断字面量的数据类型"""
        # 整数
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            return "http://www.w3.org/2001/XMLSchema#integer"
        # 浮点数
        try:
            float(value)
            return "http://www.w3.org/2001/XMLSchema#decimal"
        except ValueError:
            pass
        # 布尔值
        if value.lower() in ["true", "false"]:
            return "http://www.w3.org/2001/XMLSchema#boolean"
        # 日期时间
        if re.match(r'\d{4}-\d{2}-\d{2}', value):
            return "http://www.w3.org/2001/XMLSchema#date"
        return None
    
    def add_triple(self, subject: str, predicate: str, obj: str,
                   confidence: float = 1.0, source: str = "jsonl"):
        """添加RDF三元组"""
        # 确定术语类型
        subj_type = RDFTermType.URI if not obj.startswith("_:") else RDFTermType.BLANK
        pred_type = RDFTermType.URI
        obj_type = RDFTermType.LITERAL if self._is_literal(obj) else RDFTermType.URI
        
        subj = self._create_term(subject, subj_type)
        pred = self._create_term(predicate, pred_type)
        obj = self._create_term(obj, obj_type)
        
        triple = RDFTriple(
            subject=subj,
            predicate=pred,
            object=obj,
            confidence=confidence,
            source=source,
            timestamp=datetime.now().isoformat()
        )
        self.triples.append(triple)
        
        # 更新统计
        if predicate in ["rdf:type", "a", "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"]:
            self.stats["entities"] += 1
        self.stats["relations"] += 1
    
    def _is_literal(self, value: str) -> bool:
        """判断是否为字面量"""
        # 简单判断：包含空格、引号或特定格式的为字面量
        if value.startswith('"') and value.endswith('"'):
            return True
        if " " in value and not value.startswith("http"):
            return True
        # 检查是否是带语言标签的字符串
        if re.match(r'".*"@[\w-]+', value):
            return True
        # 检查是否是带数据类型的字符串
        if re.match(r'".*"\^\^', value):
            return True
        return False
    
    # ==================== JSONL 转换 ====================
    
    def load_jsonl(self, file_path: str) -> 'RDFAdapter':
        """
        加载JSONL文件并转换为RDF
        
        JSONL格式示例:
        {"subject": "Person", "predicate": "type", "object": "Class", "confidence": 0.9}
        {"subject": "Alice", "predicate": "knows", "object": "Bob", "confidence": 0.85}
        
        Args:
            file_path: JSONL文件路径
        
        Returns:
            self
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    self._process_jsonl_entry(data, line_num)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON解析错误 (行{line_num}): {e}")
        
        logger.info(f"加载了 {len(self.triples)} 个三元组")
        return self
    
    def _process_jsonl_entry(self, data: Dict, line_num: int):
        """处理JSONL条目"""
        subject = data.get("subject")
        predicate = data.get("predicate") or data.get("predicate")  # 支持predicate或p
        obj = data.get("object") or data.get("object")  # 支持object或o
        
        if not all([subject, predicate, obj]):
            logger.warning(f"行{line_num}: 缺少必需字段")
            return
        
        confidence = data.get("confidence", 1.0)
        source = data.get("source", "jsonl")
        
        self.add_triple(subject, predicate, obj, confidence, source)
        
        # v3.3新增：自动提取类定义
        if predicate in ["type", "a", "rdf:type", "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"]:
            self._extract_class_from_instance(subject, obj, data)
        
        # 自动提取概念
        if data.get("concept"):
            self._extract_concept(subject, data["concept"])
    
    def _extract_class_from_instance(self, instance_uri: str, class_uri: str, data: Dict):
        """从实例提取类定义"""
        class_label = class_uri.split("#")[-1] if "#" in class_uri else class_uri
        
        if class_uri not in self.schema.classes:
            self.schema.add_class(OntologyClassDef(
                uri=class_uri,
                label=class_label,
                confidence=data.get("confidence", "CONFIRMED"),
                source="jsonl_extraction"
            ))
            self.stats["concepts"] += 1
    
    def _extract_concept(self, uri: str, concept_data: Dict):
        """提取概念"""
        # 实现概念提取逻辑
        pass
    
    # ==================== RDF序列化 ====================
    
    def to_turtle(self) -> str:
        """
        序列化为Turtle格式
        
        Returns:
            Turtle格式字符串
        """
        lines = []
        
        # 写入前缀声明
        for prefix, namespace in sorted(self.prefixes.items()):
            lines.append(f"@prefix {prefix}: <{namespace}> .")
        
        lines.append("")
        
        # 写入三元组
        for triple in self.triples:
            lines.append(triple.to_nt())
        
        return "\n".join(lines)
    
    def to_jsonld(self) -> str:
        """
        序列化为JSON-LD格式
        
        Returns:
            JSON-LD格式字符串
        """
        graph = []
        
        for triple in self.triples:
            graph.append({
                "@id": triple.subject.value,
                triple.predicate.value: {
                    "@id": triple.object.value
                } if triple.object.term_type == RDFTermType.URI else triple.object.value
            })
        
        return json.dumps({
            "@context": self.prefixes,
            "@graph": graph
        }, indent=2, ensure_ascii=False)
    
    def to_ntriples(self) -> str:
        """序列化为N-Triples格式"""
        return "\n".join(triple.to_nt() for triple in self.triples)
    
    def save_turtle(self, file_path: str):
        """保存为Turtle文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_turtle())
        logger.info(f"保存Turtle文件: {file_path}")
    
    def save_jsonld(self, file_path: str):
        """保存为JSON-LD文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_jsonld())
        logger.info(f"保存JSON-LD文件: {file_path}")
    
    # ==================== OWL本体建模 ====================
    
    def define_class(self, uri: str, label: str, 
                     super_classes: Optional[List[str]] = None,
                     description: str = "") -> OntologyClassDef:
        """
        定义一个OWL类
        
        Args:
            uri: 类URI
            label: 类标签
            super_classes: 父类列表
            description: 描述
        
        Returns:
            类定义
        """
        cls = OntologyClassDef(
            uri=self._create_uri(uri),
            label=label,
            super_classes=[self._create_uri(sc) for sc in (super_classes or [])],
            description=description
        )
        self.schema.add_class(cls)
        
        # 添加rdfs:subClassOf三元组
        for super_cls in cls.super_classes:
            self.add_triple(
                cls.uri, "rdfs:subClassOf", super_cls,
                confidence=1.0, source="schema"
            )
        
        # 添加rdf:type三元组
        self.add_triple(
            cls.uri, "rdf:type", "owl:Class",
            confidence=1.0, source="schema"
        )
        
        return cls
    
    def define_property(self, uri: str, label: str,
                        property_type: str = "object",
                        domain: Optional[List[str]] = None,
                        range: Optional[List[str]] = None,
                        super_property: Optional[str] = None,
                        description: str = "") -> OntologyPropertyDef:
        """
        定义一个OWL属性
        
        Args:
            uri: 属性URI
            label: 属性标签
            property_type: 属性类型 (object, datatype, annotation)
            domain: 定义域
            range: 值域
            super_property: 父属性
            description: 描述
        
        Returns:
            属性定义
        """
        prop = OntologyPropertyDef(
            uri=self._create_uri(uri),
            label=label,
            property_type=property_type,
            domain=[self._create_uri(d) for d in (domain or [])],
            range=[self._create_uri(r) for r in (range or [])],
            super_properties=[self._create_uri(super_property)] if super_property else [],
            description=description
        )
        self.schema.add_property(prop)
        
        # 添加rdf:type三元组
        if property_type == "object":
            self.add_triple(prop.uri, "rdf:type", "owl:ObjectProperty", 1.0, "schema")
        elif property_type == "datatype":
            self.add_triple(prop.uri, "rdf:type", "owl:DatatypeProperty", 1.0, "schema")
        
        # 添加rdfs:subPropertyOf三元组
        for super_prop in prop.super_properties:
            self.add_triple(prop.uri, "rdfs:subPropertyOf", super_prop, 1.0, "schema")
        
        # 添加rdfs:domain三元组
        for d in prop.domain:
            self.add_triple(prop.uri, "rdfs:domain", d, 1.0, "schema")
        
        # 添加rdfs:range三元组
        for r in prop.range:
            self.add_triple(prop.uri, "rdfs:range", r, 1.0, "schema")
        
        return prop
    
    def define_individual(self, uri: str, label: str,
                          classes: Optional[List[str]] = None,
                          properties: Optional[Dict[str, str]] = None):
        """
        定义一个OWL个体（实例）
        
        Args:
            uri: 个体URI
            label: 个体标签
            classes: 所属类
            properties: 属性值
        """
        # 添加rdf:type三元组
        for cls in (classes or []):
            self.add_triple(
                uri, "rdf:type", self._create_uri(cls),
                confidence=1.0, source="schema"
            )
        
        # 添加属性值
        for prop, value in (properties or {}).items():
            self.add_triple(
                uri, prop, value,
                confidence=1.0, source="schema"
            )
    
    # ==================== 本体查询 ====================
    
    def query(self, subject: Optional[str] = None,
              predicate: Optional[str] = None,
              obj: Optional[str] = None,
              min_confidence: float = 0.0) -> List[RDFTriple]:
        """
        查询三元组
        
        Args:
            subject: 主体模式
            predicate: 谓词模式
            obj: 客体模式
            min_confidence: 最小置信度
        
        Returns:
            匹配的三元组列表
        """
        results = []
        for triple in self.triples:
            if subject and not self._match_pattern(subject, triple.subject.value):
                continue
            if predicate and not self._match_pattern(predicate, triple.predicate.value):
                continue
            if obj and not self._match_pattern(obj, triple.object.value):
                continue
            if triple.confidence < min_confidence:
                continue
            results.append(triple)
        return results
    
    def _match_pattern(self, pattern: str, value: str) -> bool:
        """匹配模式（支持*通配符）"""
        if pattern == "*":
            return True
        if "*" in pattern:
            regex = pattern.replace("*", ".*")
            return bool(re.match(regex, value))
        return pattern in value
    
    def get_stats(self) -> Dict:
        """获取本体统计信息"""
        return {
            **self.stats,
            "total_triples": len(self.triples),
            "unique_subjects": len(set(t.subject.value for t in self.triples)),
            "unique_predicates": len(set(t.predicate.value for t in self.triples)),
            "unique_objects": len(set(t.object.value for t in self.triples))
        }
    
    # ==================== Schema导出 ====================
    
    def export_schema(self) -> Dict:
        """导出本体Schema"""
        return {
            "uri": self.schema.uri,
            "label": self.schema.label,
            "version": self.schema.version,
            "classes": [
                {
                    "uri": c.uri,
                    "label": c.label,
                    "description": c.description,
                    "super_classes": c.super_classes,
                    "confidence": c.confidence
                }
                for c in self.schema.classes.values()
            ],
            "properties": [
                {
                    "uri": p.uri,
                    "label": p.label,
                    "property_type": p.property_type,
                    "domain": p.domain,
                    "range": p.range,
                    "confidence": p.confidence
                }
                for p in self.schema.properties.values()
            ],
            "prefixes": self.prefixes
        }

    # ==================== 置信度传播 (v3.3新增) ====================

    def propagate_confidence(
        self,
        start_entity: str,
        max_depth: int = 3,
        method: str = "multiplicative"
    ) -> Dict[str, float]:
        """
        置信度传播算法

        从起始实体出发，计算可达实体的置信度。
        内存模式实现，不依赖Neo4j。

        Args:
            start_entity: 起始实体名称
            max_depth: 最大传播深度
            method: 传播方法 (min, arithmetic, geometric, multiplicative)

        Returns:
            实体名到置信度的映射
        """
        # 构建邻接表 - 支持完整URI和短名称
        adjacency: Dict[str, List[tuple[str, float]]] = defaultdict(list)
        
        for triple in self.triples:
            if triple.subject.term_type == RDFTermType.URI:
                subj = triple.subject.value
                obj = triple.object.value
                # 存储 (目标, 置信度)
                adjacency[subj].append((obj, triple.confidence))
                # 同时添加短名称映射（去掉base_uri前缀）
                subj_short = subj.replace(self.base_uri, "")
                obj_short = obj.replace(self.base_uri, "")
                adjacency[subj_short].append((obj_short, triple.confidence))
                adjacency[subj].append((obj_short, triple.confidence))
                adjacency[subj_short].append((obj, triple.confidence))

        # BFS 传播
        confidence_map: Dict[str, float] = {start_entity: 1.0}
        visited: Set[str] = {start_entity}
        queue: List[tuple[str, float, int]] = [(start_entity, 1.0, 0)]  # (entity, confidence, depth)

        while queue:
            current, current_conf, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue

            for neighbor, edge_conf in adjacency.get(current, []):
                # 计算传播后的置信度
                if method == "min":
                    new_conf = min(current_conf, edge_conf)
                elif method == "arithmetic":
                    new_conf = (current_conf + edge_conf) / 2
                elif method == "geometric":
                    new_conf = (current_conf * edge_conf) ** 0.5
                elif method == "multiplicative":
                    new_conf = current_conf * edge_conf
                else:
                    new_conf = current_conf * edge_conf

                # 更新置信度（取最大值）
                if neighbor not in visited or new_conf > confidence_map.get(neighbor, 0):
                    confidence_map[neighbor] = new_conf
                    visited.add(neighbor)
                    queue.append((neighbor, new_conf, depth + 1))

        return confidence_map

    def trace_inference(
        self,
        start_entity: str,
        end_entity: str,
        max_depth: int = 5
    ) -> List[Dict]:
        """
        推理链追溯

        查找从起始实体到目标实体的推理路径。

        Args:
            start_entity: 起始实体
            end_entity: 目标实体
            max_depth: 最大深度

        Returns:
            推理路径列表，每条路径包含节点、关系和置信度
        """
        # 构建图 - 支持完整URI和短名称
        graph: Dict[str, List[tuple[str, float, RDFTriple]]] = defaultdict(list)
        
        for triple in self.triples:
            if triple.subject.term_type == RDFTermType.URI:
                subj = triple.subject.value
                obj = triple.object.value
                graph[subj].append((obj, triple.confidence, triple))
                # 添加短名称映射
                subj_short = subj.replace(self.base_uri, "")
                obj_short = obj.replace(self.base_uri, "")
                graph[subj_short].append((obj_short, triple.confidence, triple))
                graph[subj].append((obj_short, triple.confidence, triple))
                graph[subj_short].append((obj, triple.confidence, triple))

        # BFS 查找所有路径
        paths: List[Dict] = []
        queue: List[tuple[str, List[str], float, List[RDFTriple]]] = [
            (start_entity, [start_entity], 1.0, [])
        ]

        while queue:
            current, path, path_conf, path_triples = queue.pop(0)

            if len(path) - 1 > max_depth:
                continue

            # 找到目标
            if current == end_entity:
                paths.append({
                    "nodes": path,
                    "relationships": [t.to_dict() for t in path_triples],
                    "confidence": path_conf,
                    "depth": len(path) - 1
                })
                continue

            # 继续扩展
            for neighbor, edge_conf, triple in graph.get(current, []):
                if neighbor not in path:  # 避免循环
                    new_path = path + [neighbor]
                    new_conf = path_conf * edge_conf
                    new_triples = path_triples + [triple]
                    queue.append((neighbor, new_path, new_conf, new_triples))

        # 按置信度排序
        paths.sort(key=lambda p: p["confidence"], reverse=True)

        return paths[:10]  # 返回最多10条路径

    def compute_inference_confidence(
        self,
        reasoning_chain: List[RDFTriple]
    ) -> float:
        """
        计算推理链的整体置信度

        Args:
            reasoning_chain: 推理链中的三元组列表

        Returns:
            整体置信度
        """
        if not reasoning_chain:
            return 0.0

        # 使用乘法传播
        product = 1.0
        for triple in reasoning_chain:
            product *= triple.confidence

        return product

    def get_reasoning_explanation(
        self,
        start_entity: str,
        end_entity: str
    ) -> str:
        """
        获取推理过程的可读解释

        Args:
            start_entity: 起始实体
            end_entity: 目标实体

        Returns:
            可读的推理解释
        """
        paths = self.trace_inference(start_entity, end_entity)

        if not paths:
            return f"未找到从 {start_entity} 到 {end_entity} 的推理路径"

        lines = []
        lines.append(f"从 {start_entity} 到 {end_entity} 的推理路径:")
        lines.append("")

        for i, path in enumerate(paths[:3], 1):
            lines.append(f"路径 {i} (置信度: {path['confidence']:.3f}, 深度: {path['depth']}):")
            
            for j, node in enumerate(path["nodes"]):
                lines.append(f"  {j+1}. {node}")
                
                if j < len(path["relationships"]):
                    rel = path["relationships"][j]
                    pred = rel.get("predicate", {}).get("value", "unknown")
                    conf = rel.get("confidence", 1.0)
                    lines.append(f"     --[{pred}]--> (置信度: {conf})")

            lines.append("")

        return "\n".join(lines)


# ==================== 便捷函数 ====================

def create_rdf_from_jsonl(jsonl_path: str, base_uri: str = "http://example.org/") -> RDFAdapter:
    """
    从JSONL文件创建RDF适配器
    
    Args:
        jsonl_path: JSONL文件路径
        base_uri: 基础URI
    
    Returns:
        RDFAdapter实例
    """
    adapter = RDFAdapter(base_uri)
    adapter.load_jsonl(jsonl_path)
    return adapter


def create_sample_ontology() -> RDFAdapter:
    """
    创建示例本体（用于测试）
    
    Returns:
        RDFAdapter实例
    """
    adapter = RDFAdapter("http://example.org/gas/")
    
    # 定义类
    adapter.define_class(
        "Equipment", "燃气设备",
        super_classes=["owl:Thing"]
    )
    adapter.define_class(
        "PressureRegulator", "调压设备",
        super_classes=["Equipment"]
    )
    adapter.define_class(
        "GasAlarm", "燃气报警器",
        super_classes=["Equipment"]
    )
    adapter.define_class(
        "Supplier", "供应商",
        super_classes=["owl:Thing"]
    )
    
    # 定义属性
    adapter.define_property(
        "hasModel", "型号",
        property_type="datatype",
        domain=["Equipment"],
        range=["xsd:string"]
    )
    adapter.define_property(
        "hasSupplier", "供应商",
        property_type="object",
        domain=["Equipment"],
        range=["Supplier"]
    )
    adapter.define_property(
        "installedAt", "安装位置",
        property_type="datatype",
        domain=["Equipment"],
        range=["xsd:string"]
    )
    adapter.define_property(
        "meetsStandard", "符合标准",
        property_type="object",
        domain=["Equipment"],
        range=["Standard"]
    )
    
    # 添加实例
    adapter.define_individual(
        "DP-3000", "DP-3000调压箱",
        classes=["PressureRegulator"],
        properties={
            "hasModel": "DP-3000",
            "hasSupplier": "SupplierA"
        }
    )
    
    return adapter


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=== RDF适配器测试 ===\n")
    
    # 创建示例本体
    adapter = create_sample_ontology()
    
    print(f"三元组数量: {len(adapter.triples)}")
    print(f"统计信息: {adapter.get_stats()}")
    
    print("\n--- Schema定义 ---")
    schema = adapter.export_schema()
    print(f"类数量: {len(schema['classes'])}")
    print(f"属性数量: {len(schema['properties'])}")
    
    print("\n--- Turtle输出 (前10行) ---")
    turtle_lines = adapter.to_turtle().split("\n")[:10]
    for line in turtle_lines:
        print(line)
    
    print("\n--- 查询测试 ---")
    results = adapter.query(predicate="*subClassOf*")
    print(f"找到 {len(results)} 条subClassOf关系")
    
    print("\n--- 导出Schema ---")
    print(json.dumps(adapter.export_schema(), indent=2, ensure_ascii=False)[:500])


# ==================== SPARQL Endpoint (v3.3新增) ====================

    def sparql_query(self, query: str) -> List[Dict]:
        """
        执行SPARQL查询（简化版实现）
        
        支持基本的SELECT查询
        
        Args:
            query: SPARQL查询字符串
        
        Returns:
            查询结果列表
        """
        # 简化实现：转换为Triple模式匹配
        query = query.strip()
        
        # 提取SELECT变量
        var_match = re.search(r'SELECT\s+(\?[\w]+|\*)\s+WHERE', query, re.IGNORECASE)
        if not var_match:
            return []
        
        # 提取WHERE模式
        where_match = re.search(r'WHERE\s*\{(.+?)\}', query, re.DOTALL | re.IGNORECASE)
        if not where_match:
            return []
        
        where_clause = where_match.group(1)
        
        # 解析三元组模式
        triple_patterns = []
        for line in where_clause.split('\n'):
            line = line.strip().strip('.')
            if not line:
                continue
            
            parts = line.split()
            if len(parts) >= 3:
                subj = self._resolve_sparql_var(parts[0])
                pred = self._resolve_sparql_var(parts[1])
                obj = self._resolve_sparql_var(parts[2]) if len(parts) > 2 else None
                
                triple_patterns.append({
                    "subject": subj,
                    "predicate": pred,
                    "object": obj
                })
        
        # 执行查询
        results = []
        for triple in self.triples:
            matched = True
            
            for pattern in triple_patterns:
                if pattern["subject"] and "*" not in pattern["subject"]:
                    if pattern["subject"] != triple.subject.value:
                        matched = False
                        break
                if pattern["predicate"] and "*" not in pattern["predicate"]:
                    if pattern["predicate"] != triple.predicate.value:
                        matched = False
                        break
                if pattern["object"] and "*" not in pattern["object"]:
                    if pattern["object"] != triple.object.value:
                        matched = False
                        break
            
            if matched:
                results.append(triple.to_dict())
        
        return results
    
    def _resolve_sparql_var(self, var: str) -> Optional[str]:
        """解析SPARQL变量"""
        var = var.strip()
        if var.startswith("?") or var.startswith("$"):
            return None  # 变量需要绑定
        if var.startswith("<") and var.endswith(">"):
            return var[1:-1]  # URI
        if ":" in var:
            for prefix, namespace in self.prefixes.items():
                if var.startswith(prefix + ":"):
                    return var.replace(prefix + ":", namespace)
        return var
    
    # ==================== RDF序列化增强 (v3.3新增) ====================
    
    def to_rdfxml(self) -> str:
        """序列化为RDF/XML格式"""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"')
        lines.append('         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">')
        
        # 分组主体
        subjects: Dict[str, List[RDFTriple]] = defaultdict(list)
        for triple in self.triples:
            subjects[triple.subject.value].append(triple)
        
        for subj, triples in subjects.items():
            lines.append(f'  <rdf:Description rdf:about="{subj}">')
            
            for triple in triples:
                pred = triple.predicate.value
                obj = triple.object.value
                
                if triple.object.term_type == RDFTermType.URI:
                    lines.append(f'    <{self._get_local_name(pred)} rdf:resource="{obj}"/>')
                else:
                    datatype = triple.object.datatype or ""
                    if datatype:
                        lines.append(f'    <{self._get_local_name(pred)} rdf:datatype="{datatype}">{obj}</{self._get_local_name(pred)}>')
                    else:
                        lines.append(f'    <{self._get_local_name(pred)}>{obj}</{self._get_local_name(pred)}>')
            
            lines.append('  </rdf:Description>')
        
        lines.append('</rdf:RDF>')
        return '\n'.join(lines)
    
    def _get_local_name(self, uri: str) -> str:
        """获取URI的局部名"""
        for prefix, namespace in self.prefixes.items():
            if uri.startswith(namespace):
                return prefix + ":" + uri[len(namespace):]
        
        if "#" in uri:
            return uri.split("#")[-1]
        return uri.split("/")[-1]
    
    def to_jsonld(self, context: Optional[Dict] = None) -> Dict:
        """序列化为JSON-LD格式"""
        default_context = {
            "@context": {
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "owl": "http://www.w3.org/2002/07/owl#",
                **self.prefixes
            }
        }
        
        graph = []
        for triple in self.triples:
            graph.append({
                "@subject": triple.subject.value,
                "@predicate": triple.predicate.value,
                "@object": {
                    "@value": triple.object.value,
                    "@type": triple.object.datatype if triple.object.datatype else None
                } if triple.object.term_type == RDFTermType.LITERAL else triple.object.value
            })
        
        result = default_context.copy()
        result["@graph"] = graph
        
        return result
