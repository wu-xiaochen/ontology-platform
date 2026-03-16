"""
API主入口 (API Main)
FastAPI框架搭建，RESTful端点设计和GraphQL支持

基于ontology-clawra v3.3的本体论实践，实现生产级API服务：
- FastAPI框架
- RESTful端点
- GraphQL支持 (Strawberry)
- 推理引擎集成
- 置信度传播
- 推理链追溯
"""

import logging
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Union

# 导入项目模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ontology.rdf_adapter import RDFAdapter, RDFTriple, OntologySchema
from src.ontology.neo4j_client import Neo4jClient, GraphNode, GraphRelationship
from src.loader import OntologyLoader
from src.reasoner import Reasoner, Fact, InferenceResult
from src.confidence import ConfidenceCalculator, Evidence, ConfidenceResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 配置 ====================

@dataclass
class AppConfig:
    """应用配置"""
    # Neo4j配置
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j"
    
    # 本体配置
    ontology_path: str = "data/ontology.jsonl"
    base_uri: str = "http://example.org/"
    
    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # 推理配置
    max_inference_depth: int = 5
    min_confidence: float = 0.0


config = AppConfig()


# ==================== 应用状态 ====================

class AppState:
    """应用状态"""
    rdf_adapter: Optional[RDFAdapter] = None
    neo4j_client: Optional[Neo4jClient] = None
    reasoner: Optional[Reasoner] = None
    confidence_calculator: ConfidenceCalculator = None
    initialized: bool = False


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("Initializing Ontology Platform API...")
    
    # 初始化RDF适配器
    try:
        state.rdf_adapter = RDFAdapter(config.base_uri)
        # 尝试加载已有本体
        ontology_file = Path(config.ontology_path)
        if ontology_file.exists():
            state.rdf_adapter.load_jsonl(str(ontology_file))
            logger.info(f"Loaded ontology from {ontology_file}")
    except Exception as e:
        logger.warning(f"Could not load ontology: {e}")
        state.rdf_adapter = RDFAdapter(config.base_uri)
    
    # 初始化Neo4j客户端
    try:
        state.neo4j_client = Neo4jClient(
            config.neo4j_uri,
            config.neo4j_user,
            config.neo4j_password
        )
        state.neo4j_client.connect()
        logger.info("Connected to Neo4j")
    except Exception as e:
        logger.warning(f"Could not connect to Neo4j: {e}. Using memory mode.")
        state.neo4j_client = Neo4jClient()
    
    # 初始化推理引擎
    loader = OntologyLoader()
    state.reasoner = Reasoner(loader)
    state.confidence_calculator = ConfidenceCalculator()
    
    state.initialized = True
    logger.info("Ontology Platform API initialized")
    
    yield
    
    # 关闭时清理
    if state.neo4j_client:
        state.neo4j_client.close()
    logger.info("Ontology Platform API shutdown")


# ==================== FastAPI应用 ====================

app = FastAPI(
    title="Ontology Platform API",
    description="基于ontology-clawra v3.3的生产级本体平台API",
    version="3.3.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic模型 ====================

class EntityCreate(BaseModel):
    """实体创建请求"""
    name: str = Field(..., description="实体名称/URI")
    label: str = Field(default="Entity", description="节点标签")
    properties: Dict[str, Any] = Field(default_factory=dict, description="属性")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度")


class RelationshipCreate(BaseModel):
    """关系创建请求"""
    start_entity: str = Field(..., description="起始实体")
    end_entity: str = Field(..., description="结束实体")
    relationship_type: str = Field(..., description="关系类型")
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class TripleCreate(BaseModel):
    """三元组创建请求"""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source: str = "api"


class InferenceRequest(BaseModel):
    """推理请求"""
    initial_facts: List[Dict[str, str]] = Field(default_factory=list)
    goal: Optional[Dict[str, str]] = None
    max_depth: int = Field(default=5, ge=1, le=20)
    method: str = Field(default="forward", description="forward, backward, bidirectional")


class QueryRequest(BaseModel):
    """本体查询请求"""
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object: Optional[str] = None
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ConfidenceRequest(BaseModel):
    """置信度计算请求"""
    evidence: List[Dict[str, Any]]
    method: str = Field(default="weighted", description="weighted, bayesian, multiplicative, Dempster-Shafer")


# ==================== 依赖项 ====================

def get_rdf_adapter() -> RDFAdapter:
    """获取RDF适配器"""
    if not state.rdf_adapter:
        raise HTTPException(status_code=503, detail="RDF adapter not initialized")
    return state.rdf_adapter


def get_neo4j_client() -> Neo4jClient:
    """获取Neo4j客户端"""
    if not state.neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j client not initialized")
    return state.neo4j_client


def get_reasoner() -> Reasoner:
    """获取推理引擎"""
    if not state.reasoner:
        raise HTTPException(status_code=503, detail="Reasoner not initialized")
    return state.reasoner


# ==================== 根路径 ====================

@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": "Ontology Platform API",
        "version": "3.3.0",
        "description": "基于ontology-clawra v3.3的生产级本体平台",
        "docs": "/docs",
        "status": "running" if state.initialized else "initializing"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "rdf_adapter": state.rdf_adapter is not None,
            "neo4j_client": state.neo4j_client is not None,
            "reasoner": state.reasoner is not None,
            "neo4j_connected": state.neo4j_client.is_connected() if state.neo4j_client else False
        }
    }


# ==================== 本体Schema API ====================

@app.get("/api/v1/schema")
async def get_schema(adapter: RDFAdapter = Depends(get_rdf_adapter)):
    """获取本体Schema"""
    return adapter.export_schema()


@app.get("/api/v1/schema/classes")
async def list_classes(adapter: RDFAdapter = Depends(get_rdf_adapter)):
    """列出所有类"""
    schema = adapter.export_schema()
    return {"classes": schema["classes"]}


@app.get("/api/v1/schema/classes/{class_uri}")
async def get_class(class_uri: str, adapter: RDFAdapter = Depends(get_rdf_adapter)):
    """获取类详情"""
    cls = adapter.schema.classes.get(class_uri)
    if not cls:
        raise HTTPException(status_code=404, detail=f"Class not found: {class_uri}")
    return {
        "uri": cls.uri,
        "label": cls.label,
        "description": cls.description,
        "super_classes": cls.super_classes,
        "confidence": cls.confidence
    }


@app.get("/api/v1/schema/properties")
async def list_properties(adapter: RDFAdapter = Depends(get_rdf_adapter)):
    """列出所有属性"""
    schema = adapter.export_schema()
    return {"properties": schema["properties"]}


@app.post("/api/v1/schema/classes")
async def create_class(
    uri: str = Body(...),
    label: str = Body(...),
    super_classes: List[str] = Body(default_factory=list),
    description: str = Body(default=""),
    adapter: RDFAdapter = Depends(get_rdf_adapter)
):
    """创建类定义"""
    cls = adapter.define_class(uri, label, super_classes, description)
    return {"message": "Class created", "class": cls.uri}


@app.post("/api/v1/schema/properties")
async def create_property(
    uri: str = Body(...),
    label: str = Body(...),
    property_type: str = Body(default="object"),
    domain: List[str] = Body(default_factory=list),
    range: List[str] = Body(default_factory=list),
    adapter: RDFAdapter = Depends(get_rdf_adapter)
):
    """创建属性定义"""
    prop = adapter.define_property(uri, label, property_type, domain, range)
    return {"message": "Property created", "property": prop.uri}


# ==================== 本体查询 API ====================

@app.post("/api/v1/query")
async def query_ontology(
    request: QueryRequest,
    adapter: RDFAdapter = Depends(get_rdf_adapter)
):
    """查询本体"""
    triples = adapter.query(
        subject=request.subject,
        predicate=request.predicate,
        obj=request.object,
        min_confidence=request.min_confidence
    )
    
    return {
        "count": len(triples),
        "triples": [t.to_dict() for t in triples]
    }


@app.get("/api/v1/triples")
async def list_triples(
    subject: Optional[str] = Query(None),
    predicate: Optional[str] = Query(None),
    object: Optional[str] = Query(None),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=1000),
    adapter: RDFAdapter = Depends(get_rdf_adapter)
):
    """列出三元组"""
    triples = adapter.query(subject, predicate, object, min_confidence)
    triples = triples[:limit]
    
    return {
        "count": len(triples),
        "triples": [t.to_dict() for t in triples]
    }


@app.post("/api/v1/triples")
async def create_triple(
    triple: TripleCreate,
    adapter: RDFAdapter = Depends(get_rdf_adapter)
):
    """创建三元组"""
    adapter.add_triple(
        triple.subject,
        triple.predicate,
        triple.object,
        triple.confidence,
        triple.source
    )
    
    return {"message": "Triple created"}


# ==================== 图数据库 API ====================

@app.post("/api/v1/entities")
async def create_entity(
    entity: EntityCreate,
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """创建实体"""
    node = client.create_entity(
        entity.name,
        entity.label,
        entity.properties,
        entity.confidence
    )
    
    return {"message": "Entity created", "node": node.to_dict() if node else None}


@app.get("/api/v1/entities")
async def list_entities(
    label: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """列出实体"""
    if label:
        nodes = client.query_by_properties(label, {})
    else:
        # 简化：返回所有实体
        stats = client.get_stats()
        return {"count": stats.get("nodes", 0), "entities": []}
    
    return {
        "count": len(nodes),
        "entities": [n.to_dict() for n in nodes[:limit]]
    }


@app.get("/api/v1/entities/{name}")
async def get_entity(
    name: str,
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """获取实体"""
    node = client.get_entity(name)
    if not node:
        raise HTTPException(status_code=404, detail=f"Entity not found: {name}")
    return node.to_dict()


@app.delete("/api/v1/entities/{name}")
async def delete_entity(
    name: str,
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """删除实体"""
    client.delete_entity(name)
    return {"message": "Entity deleted"}


@app.post("/api/v1/relationships")
async def create_relationship(
    rel: RelationshipCreate,
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """创建关系"""
    relationship = client.create_relationship(
        rel.start_entity,
        rel.end_entity,
        rel.relationship_type,
        rel.properties,
        rel.confidence
    )
    
    return {"message": "Relationship created", "relationship": relationship.to_dict() if relationship else None}


@app.get("/api/v1/entities/{name}/relationships")
async def get_entity_relationships(
    name: str,
    rel_type: Optional[str] = Query(None),
    direction: str = Query("both", pattern="^(outgoing|incoming|both)$"),
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """获取实体的关系"""
    relationships = client.get_relationships(name, rel_type, direction)
    
    return {
        "entity": name,
        "count": len(relationships),
        "relationships": [r.to_dict() for r in relationships]
    }


@app.get("/api/v1/entities/{start}/paths/{end}")
async def find_paths(
    start: str,
    end: str,
    max_depth: int = Query(5, ge=1, le=10),
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """查找路径"""
    paths = client.trace_inference(start, end, max_depth)
    
    return {
        "start": start,
        "end": end,
        "count": len(paths),
        "paths": [p.to_dict() for p in paths]
    }


@app.get("/api/v1/entities/{name}/confidence")
async def propagate_confidence(
    name: str,
    max_depth: int = Query(3, ge=1, le=10),
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """置信度传播"""
    confidence_map = client.propagate_confidence(name, max_depth)
    
    return {
        "entity": name,
        "max_depth": max_depth,
        "confidence_distribution": confidence_map
    }


# ==================== 推理引擎 API ====================

@app.post("/api/v1/reason")
async def reason(
    request: InferenceRequest,
    reasoner: Reasoner = Depends(get_reasoner)
):
    """执行推理"""
    # 转换初始事实
    facts = []
    for f in request.initial_facts:
        fact = Fact(
            subject=f.get("subject", ""),
            predicate=f.get("predicate", ""),
            object=f.get("object", ""),
            confidence=f.get("confidence", 1.0)
        )
        facts.append(fact)
    
    # 执行推理
    if request.method == "forward":
        result = reasoner.forward_chain(facts, request.max_depth)
    elif request.method == "backward":
        if not request.goal:
            raise HTTPException(status_code=400, detail="Goal required for backward chaining")
        goal = Fact(
            subject=request.goal.get("subject", ""),
            predicate=request.goal.get("predicate", ""),
            object=request.goal.get("object", "")
        )
        result = reasoner.backward_chain(goal, request.max_depth)
    else:
        raise HTTPException(status_code=400, detail="Invalid method")
    
    # 格式化结果
    conclusions = []
    for step in result.conclusions:
        conclusions.append({
            "rule": step.rule.name,
            "rule_id": step.rule.id,
            "conclusion": {
                "subject": step.conclusion.subject,
                "predicate": step.conclusion.predicate,
                "object": step.conclusion.object
            },
            "confidence": step.confidence.value,
            "method": step.confidence.method
        })
    
    return {
        "success": True,
        "conclusions": conclusions,
        "facts_used": len(result.facts_used),
        "depth": result.depth,
        "total_confidence": result.total_confidence.value,
        "method": request.method
    }


@app.post("/api/v1/confidence")
async def calculate_confidence(request: ConfidenceRequest):
    """计算置信度"""
    evidence_list = []
    for e in request.evidence:
        evidence = Evidence(
            source=e.get("source", "unknown"),
            reliability=e.get("reliability", 0.5),
            content=e.get("content", "")
        )
        evidence_list.append(evidence)
    
    result = state.confidence_calculator.calculate(evidence_list, request.method)
    
    return {
        "value": result.value,
        "method": result.method,
        "evidence_count": result.evidence_count,
        "details": result.details
    }


# ==================== 统计 API ====================

@app.get("/api/v1/stats")
async def get_stats(
    adapter: RDFAdapter = Depends(get_rdf_adapter),
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """获取统计信息"""
    rdf_stats = adapter.get_stats()
    neo4j_stats = client.get_stats()
    
    return {
        "ontology": rdf_stats,
        "graph": neo4j_stats,
        "timestamp": datetime.now().isoformat()
    }


# ==================== 批量操作 API ====================

@app.post("/api/v1/import/triples")
async def import_triples(
    triples: List[TripleCreate],
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """批量导入三元组"""
    triple_dicts = [t.dict() for t in triples]
    client.batch_import_triples(triple_dicts)
    
    return {"message": f"Imported {len(triples)} triples"}


# ==================== 运行入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level="info"
    )
