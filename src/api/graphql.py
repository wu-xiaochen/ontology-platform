"""
GraphQL API Schema and Resolvers
基于ontology-clawra v3.3的GraphQL支持

提供GraphQL查询和变更接口，支持：
- 实体查询
- 关系查询
- 推理执行
- 本体Schema查询
- 置信度计算
"""

import logging
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import strawberry
from strawberry import field
from strawberry.types import Info

logger = logging.getLogger(__name__)


# ==================== GraphQL Types ====================

@strawberry.type(description="RDF三元组")
class RDFTripleType:
    subject: str
    predicate: str
    object: str
    confidence: float
    source: str
    
    @classmethod
    def from_dict(cls, data: Dict) -> "RDFTripleType":
        return cls(
            subject=data.get("subject", ""),
            predicate=data.get("predicate", ""),
            object=data.get("object", ""),
            confidence=data.get("confidence", 1.0),
            source=data.get("source", "unknown")
        )


@strawberry.type(description="本体类定义")
class OntologyClassType:
    uri: str
    label: str
    description: str
    super_classes: List[str]
    confidence: str
    
    @classmethod
    def from_dict(cls, data: Dict) -> "OntologyClassType":
        return cls(
            uri=data.get("uri", ""),
            label=data.get("label", ""),
            description=data.get("description", ""),
            super_classes=data.get("super_classes", []),
            confidence=data.get("confidence", "UNKNOWN")
        )


@strawberry.type(description="本体属性定义")
class OntologyPropertyType:
    uri: str
    label: str
    property_type: str
    domain: List[str]
    range: List[str]
    confidence: str
    
    @classmethod
    def from_dict(cls, data: Dict) -> "OntologyPropertyType":
        return cls(
            uri=data.get("uri", ""),
            label=data.get("label", ""),
            property_type=data.get("property_type", "object"),
            domain=data.get("domain", []),
            range=data.get("range", []),
            confidence=data.get("confidence", "UNKNOWN")
        )


@strawberry.type(description="图节点")
class GraphNodeType:
    id: str
    labels: List[str]
    properties: str  # JSON string
    confidence: float


@strawberry.type(description="图关系")
class GraphRelationshipType:
    id: str
    type: str
    start_node: str
    end_node: str
    properties: str  # JSON string
    confidence: float


@strawberry.type(description="推理结论")
class InferenceConclusionType:
    rule: str
    rule_id: str
    subject: str
    predicate: str
    object: str
    confidence: float
    method: str


@strawberry.type(description="置信度结果")
class ConfidenceResultType:
    value: float
    method: str
    evidence_count: int
    details: str  # JSON string


@strawberry.type(description="推理链路径")
class InferencePathType:
    nodes: List[GraphNodeType]
    relationships: List[GraphRelationshipType]
    confidence: float
    rule_ids: List[str]
    depth: int


@strawberry.type(description="统计信息")
class StatsType:
    total_triples: int
    unique_subjects: int
    unique_predicates: int
    unique_objects: int
    nodes_count: int
    relationships_count: int


@strawberry.type(description="API状态")
class HealthStatusType:
    status: str
    rdf_adapter: bool
    neo4j_client: bool
    reasoner: bool
    neo4j_connected: bool


# ==================== Context ====================

@strawberry.type
class QueryContext:
    """GraphQL查询上下文"""
    rdf_adapter: Any = None
    neo4j_client: Any = None
    reasoner: Any = None
    confidence_calculator: Any = None


# ==================== Queries ====================

@strawberry.type(description="Root Query")
class Query:
    
    @strawberry.field(description="查询三元组")
    def triples(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
        min_confidence: float = 0.0,
        info: Info = None
    ) -> List[RDFTripleType]:
        adapter = getattr(info.context, "rdf_adapter", None)
        if not adapter:
            return []
        
        results = adapter.query(subject, predicate, obj, min_confidence)
        return [RDFTripleType.from_dict(t.to_dict()) for t in results]
    
    @strawberry.field(description="查询本体类")
    def classes(
        self,
        info: Info = None
    ) -> List[OntologyClassType]:
        adapter = getattr(info.context, "rdf_adapter", None)
        if not adapter:
            return []
        
        schema = adapter.export_schema()
        return [OntologyClassType.from_dict(c) for c in schema.get("classes", [])]
    
    @strawberry.field(description="查询本体属性")
    def properties(
        self,
        info: Info = None
    ) -> List[OntologyPropertyType]:
        adapter = getattr(info.context, "rdf_adapter", None)
        if not adapter:
            return []
        
        schema = adapter.export_schema()
        return [OntologyPropertyType.from_dict(p) for p in schema.get("properties", [])]
    
    @strawberry.field(description="获取图节点")
    def node(
        self,
        name: str,
        info: Info = None
    ) -> Optional[GraphNodeType]:
        client = getattr(info.context, "neo4j_client", None)
        if not client or not client.is_connected():
            return None
        
        node = client.get_entity(name)
        if not node:
            return None
        
        return GraphNodeType(
            id=node.id or "",
            labels=node.labels,
            properties=json.dumps(node.properties),
            confidence=node.confidence
        )
    
    @strawberry.field(description="获取节点的邻居")
    def neighbors(
        self,
        name: str,
        depth: int = 1,
        info: Info = None
    ) -> List[GraphNodeType]:
        client = getattr(info.context, "neo4j_client", None)
        if not client or not client.is_connected():
            return []
        
        results = client.find_neighbors(name, depth)
        return [
            GraphNodeType(
                id=n.id or "",
                labels=n.labels,
                properties=json.dumps(n.properties),
                confidence=n.confidence
            )
            for n in results
        ]
    
    @strawberry.field(description="获取统计信息")
    def stats(
        self,
        info: Info = None
    ) -> Optional[StatsType]:
        adapter = getattr(info.context, "rdf_adapter", None)
        client = getattr(info.context, "neo4j_client", None)
        
        if not adapter:
            return None
        
        rdf_stats = adapter.get_stats()
        neo4j_stats = client.get_stats() if client and client.is_connected() else {}
        
        return StatsType(
            total_triples=rdf_stats.get("total_triples", 0),
            unique_subjects=rdf_stats.get("unique_subjects", 0),
            unique_predicates=rdf_stats.get("unique_predicates", 0),
            unique_objects=rdf_stats.get("unique_objects", 0),
            nodes_count=neo4j_stats.get("nodes", 0),
            relationships_count=neo4j_stats.get("relationships", 0)
        )
    
    @strawberry.field(description="健康检查")
    def health(
        self,
        info: Info = None
    ) -> HealthStatusType:
        adapter = getattr(info.context, "rdf_adapter", None)
        client = getattr(info.context, "neo4j_client", None)
        reasoner = getattr(info.context, "reasoner", None)
        
        return HealthStatusType(
            status="healthy" if adapter else "initializing",
            rdf_adapter=adapter is not None,
            neo4j_client=client is not None,
            reasoner=reasoner is not None,
            neo4j_connected=client.is_connected() if client else False
        )
    
    @strawberry.field(description="置信度传播")
    def confidence_propagation(
        self,
        start_entity: str,
        max_depth: int = 3,
        method: str = "multiplicative",
        info: Info = None
    ) -> str:
        adapter = getattr(info.context, "rdf_adapter", None)
        if not adapter:
            return "{}"
        
        result = adapter.propagate_confidence(start_entity, max_depth, method)
        return json.dumps(result)
    
    @strawberry.field(description="推理链追溯")
    def trace_inference(
        self,
        start_entity: str,
        end_entity: str,
        max_depth: int = 5,
        info: Info = None
    ) -> List[InferencePathType]:
        adapter = getattr(info.context, "rdf_adapter", None)
        if not adapter:
            return []
        
        paths = adapter.trace_inference(start_entity, end_entity, max_depth)
        
        result = []
        for path in paths:
            nodes = [
                GraphNodeType(
                    id=n.get("id", ""),
                    labels=n.get("labels", []),
                    properties=json.dumps(n.get("properties", {})),
                    confidence=n.get("confidence", 1.0)
                )
                for n in path.get("nodes", [])
            ]
            rels = [
                GraphRelationshipType(
                    id=r.get("id", ""),
                    type=r.get("type", ""),
                    start_node=r.get("start_node", ""),
                    end_node=r.get("end_node", ""),
                    properties=json.dumps(r.get("properties", {})),
                    confidence=r.get("confidence", 1.0)
                )
                for r in path.get("relationships", [])
            ]
            result.append(InferencePathType(
                nodes=nodes,
                relationships=rels,
                confidence=path.get("confidence", 1.0),
                rule_ids=path.get("rule_ids", []),
                depth=path.get("depth", 0)
            ))
        
        return result


# ==================== Mutations ====================

@strawberry.type(description="Root Mutation")
class Mutation:
    
    @strawberry.mutation(description="创建实体")
    def create_entity(
        self,
        name: str,
        label: str = "Entity",
        properties: str = "{}",  # JSON string
        confidence: float = 1.0,
        info: Info = None
    ) -> Optional[GraphNodeType]:
        client = getattr(info.context, "neo4j_client", None)
        if not client:
            return None
        
        props = json.loads(properties) if properties else {}
        node = client.create_entity(name, label, props, confidence)
        if not node:
            return None
        
        return GraphNodeType(
            id=node.id or "",
            labels=node.labels,
            properties=json.dumps(node.properties),
            confidence=node.confidence
        )
    
    @strawberry.mutation(description="创建关系")
    def create_relationship(
        self,
        start_entity: str,
        end_entity: str,
        relationship_type: str,
        properties: str = "{}",  # JSON string
        confidence: float = 1.0,
        info: Info = None
    ) -> Optional[GraphRelationshipType]:
        client = getattr(info.context, "neo4j_client", None)
        if not client:
            return None
        
        props = json.loads(properties) if properties else {}
        rel = client.create_relationship(
            start_entity, end_entity, relationship_type, props, confidence
        )
        if not rel:
            return None
        
        return GraphRelationshipType(
            id=rel.id or "",
            type=rel.type,
            start_node=rel.start_node,
            end_node=rel.end_node,
            properties=json.dumps(rel.properties),
            confidence=rel.confidence
        )
    
    @strawberry.mutation(description="添加三元组")
    def add_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source: str = "graphql",
        info: Info = None
    ) -> RDFTripleType:
        adapter = getattr(info.context, "rdf_adapter", None)
        if not adapter:
            raise Exception("RDF adapter not initialized")
        
        adapter.add_triple(subject, predicate, obj, confidence, source)
        
        return RDFTripleType(
            subject=subject,
            predicate=predicate,
            object=obj,
            confidence=confidence,
            source=source
        )
    
    @strawberry.mutation(description="创建本体类")
    def create_class(
        self,
        uri: str,
        label: str,
        super_classes: List[str] = strawberry.field(default_factory=list),
        description: str = "",
        info: Info = None
    ) -> OntologyClassType:
        adapter = getattr(info.context, "rdf_adapter", None)
        if not adapter:
            raise Exception("RDF adapter not initialized")
        
        cls = adapter.define_class(uri, label, super_classes, description)
        
        return OntologyClassType(
            uri=cls.uri,
            label=cls.label,
            description=cls.description,
            super_classes=cls.super_classes,
            confidence=cls.confidence
        )
    
    @strawberry.mutation(description="计算置信度")
    def calculate_confidence(
        self,
        evidence: str = "[]",  # JSON string of list
        method: str = "weighted",
        info: Info = None
    ) -> ConfidenceResultType:
        calc = getattr(info.context, "confidence_calculator", None)
        if not calc:
            return ConfidenceResultType(
                value=0.0,
                method=method,
                evidence_count=0,
                details="{}"
            )
        
        import json
        evidence_list_data = json.loads(evidence) if evidence else []
        
        from src.confidence import Evidence
        evidence_list = [
            Evidence(
                source=e.get("source", "unknown"),
                reliability=e.get("reliability", 0.5),
                content=e.get("content", "")
            )
            for e in evidence_list_data
        ]
        
        result = calc.calculate(evidence_list, method)
        
        return ConfidenceResultType(
            value=result.value,
            method=result.method,
            evidence_count=result.evidence_count,
            details=json.dumps(result.details)
        )


# ==================== Schema ====================

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
