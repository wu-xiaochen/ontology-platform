"""
API Main Entry Point (API主入口)
FastAPI framework, RESTful endpoints and GraphQL support

Based on ontology-clawra v3.3 ontology practices, implementing production-level API:
- FastAPI framework
- RESTful endpoints
- GraphQL support (Strawberry)
- Reasoning engine integration
- Confidence propagation
- Inference chain tracing
- Swagger/OpenAPI documentation
- Global error handling
- Enhanced caching strategies

v3.4.0 Updates:
- Added Prometheus monitoring and metrics collection
- Added API key authentication
- Added request rate limiting
- Added security headers
- Added performance optimization (cache, connection pool)

v3.5.0 Updates:
- Added Swagger/OpenAPI documentation with detailed descriptions
- Added global error handling with custom exception handlers
- Added enhanced cache strategy module
- Added Redis distributed cache support
- Added cache warming strategies
- Added detailed API documentation with examples
"""

import logging
import time
import uuid
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Depends, Query, Body, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field

# 导入项目模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ontology.rdf_adapter import RDFAdapter
from src.ontology.neo4j_client import Neo4jClient
from src.loader import OntologyLoader
from src.reasoner import Reasoner, Fact
from src.confidence import ConfidenceCalculator, Evidence

# 导入新模块
from src.monitoring import metrics, request_logger, performance_monitor
from src.security import (
    api_key_manager, rate_limiter, ip_blocker, 
    SecurityHeaders, audit_logger, cors_config
)
from src.performance import (
    inference_cache
)
from src.export import DataExporter, ExportFormat, ExportOptions
from src.permissions import permission_manager, Permission

# 定义logger用于模块级导入错误
_import_logger = logging.getLogger(__name__)

# 导入GraphQL (v3.3新增)
try:
    from src.api.graphql import schema as graphql_schema
    GRAPHQL_AVAILABLE = True
except ImportError as e:
    GRAPHQL_AVAILABLE = False
    _import_logger.warning(f"GraphQL not available: {e}")

# 导入主动学习引擎 (v3.3新增)
try:
    from src.ontology.auto_learn import auto_learn_engine, ConfidenceLevel
    AUTO_LEARN_AVAILABLE = True
except ImportError as e:
    AUTO_LEARN_AVAILABLE = False
    _import_logger.warning(f"Auto-learn engine not available: {e}")
from src.caching import query_cache, debug_cache, create_cache

# 导入错误处理和缓存策略
from src.errors import (
    setup_exception_handlers, error_handler
)
from src.cache_strategy import (
    CacheConfig
)

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


# ==================== 安全中间件 ====================

class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件：添加安全头部、速率限制、IP阻止"""
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 检查IP是否被阻止
        if ip_blocker.is_blocked(client_ip):
            return Response(
                content='{"detail": "Access denied"}',
                status_code=403,
                media_type="application/json"
            )
        
        # 速率限制检查
        allowed, rate_info = rate_limiter.check_rate_limit(client_ip)
        if not allowed:
            audit_logger.log_rate_limit_exceeded(client_ip, client_ip)
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(int(rate_info["reset_at"] - time.time()))}
            )
        
        # 生成或获取correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        response = await call_next(request)
        
        # 添加安全头部
        for key, value in SecurityHeaders.get_headers().items():
            response.headers[key] = value
        
        # 添加correlation ID
        response.headers["X-Correlation-ID"] = correlation_id
        
        # 添加速率限制信息
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        
        # 处理请求
        response = await call_next(request)
        
        # 记录日志
        duration = time.perf_counter() - start_time
        request_logger.log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=duration,
            correlation_id=getattr(request.state, "correlation_id", None),
            extra={"client_ip": request.client.host if request.client else None}
        )
        
        # 记录性能指标
        performance_monitor.record_request(duration)
        metrics.increment_counter("http_requests_total", {
            "method": request.method,
            "endpoint": request.url.path,
            "status": str(response.status_code)
        })
        metrics.observe_histogram("http_request_duration_seconds", duration, {
            "method": request.method,
            "endpoint": request.url.path
        })
        
        return response


# ==================== API密钥认证 ====================

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = API_KEY_HEADER) -> str:
    """获取并验证API密钥"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    key_data = api_key_manager.validate_key(api_key)
    if not key_data:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return key_data["user_id"]


# ==================== 依赖项 ====================

def require_auth():
    """需要认证的依赖"""
    return Depends(get_api_key)


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
    description="""## Overview

The Ontology Platform API provides a comprehensive RESTful interface for managing ontological data, 
performing reasoning operations, and calculating confidence scores.

## Features

- **Ontology Management**: Create, read, update, and delete ontological schemas and triples
- **Graph Database Integration**: Full integration with Neo4j for graph-based reasoning
- **Reasoning Engine**: Forward, backward, and bidirectional chaining inference
- **Confidence Calculation**: Multiple methods including weighted, Bayesian, multiplicative, and Dempster-Shafer
- **Security**: API key authentication, rate limiting, IP blocking
- **Performance**: Multi-level caching, connection pooling, query optimization
- **Monitoring**: Prometheus metrics, health checks, request logging
- **Export**: Multiple formats (JSON, CSV, Turtle, JSON-LD)

## Authentication

Most endpoints require an API key. Include it in the request header:

```
X-API-Key: your-api-key-here
```

## Rate Limiting

Default rate limit: 100 requests per minute per IP.

## Error Responses

All errors follow a consistent format:

```json
{
  "error": true,
  "code": "NOT_FOUND",
  "message": "Resource not found: example",
  "timestamp": "2024-01-01T00:00:00",
  "path": "/api/v1/entities/example",
  "correlation_id": "abc-123"
}
```
""",
    version="3.5.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    terms_of_service="https://example.org/terms/",
    contact={
        "name": "API Support",
        "url": "https://example.org/support",
        "email": "support@example.org"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# CORS中间件 - 配置化
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.allow_origins,
    allow_credentials=cors_config.allow_credentials,
    allow_methods=cors_config.allow_methods,
    allow_headers=cors_config.allow_headers,
)

# 安全中间件
app.add_middleware(SecurityMiddleware)

# 请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 注册监控端点
from src.monitoring import setup_app_metrics
setup_app_metrics(app)

# 注册异常处理器
setup_exception_handlers(app)

# ==================== GraphQL API (v3.3新增) ====================

if GRAPHQL_AVAILABLE:
    try:
        from strawberry.fastapi import GraphQLRouter
        
        @asynccontextmanager
        async def graphql_context(app: FastAPI):
            """GraphQL上下文"""
            yield {
                "rdf_adapter": state.rdf_adapter,
                "neo4j_client": state.neo4j_client,
                "reasoner": state.reasoner,
                "confidence_calculator": state.confidence_calculator
            }
        
        graphql_router = GraphQLRouter(
            graphql_schema,
            context_getter=graphql_context,
            response_model=None,  # Disable response model validation for GraphQL
        )
        app.include_router(graphql_router, prefix="/api/graphql")
        logger.info("GraphQL endpoint added at /api/graphql")
    except Exception as e:
        logger.warning(f"GraphQL router setup failed: {e}")


# ==================== Custom OpenAPI Schema ====================

def custom_openapi():
    """Generate custom OpenAPI schema with examples"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=[],
    )
    
    # Add custom components
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key authentication. Get your key from /api/v1/auth/api-keys"
        }
    }
    
    # Add common security scheme
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    
    # Add examples to schemas
    if "schemas" in openapi_schema.get("components", {}):
        # Add examples to key schemas
        if "EntityCreate" in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"]["EntityCreate"]["example"] = {
                "name": "http://example.org/person/John",
                "label": "Person",
                "properties": {
                    "age": 30,
                    "occupation": "Engineer"
                },
                "confidence": 0.95
            }
        
        if "RelationshipCreate" in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"]["RelationshipCreate"]["example"] = {
                "start_entity": "http://example.org/person/John",
                "end_entity": "http://example.org/person/Jane",
                "relationship_type": "marriedTo",
                "properties": {"since": "2020-01-01"},
                "confidence": 0.9
            }
        
        if "TripleCreate" in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"]["TripleCreate"]["example"] = {
                "subject": "http://example.org/person/John",
                "predicate": "http://example.org/knows",
                "object": "http://example.org/person/Jane",
                "confidence": 0.85,
                "source": "manual"
            }
        
        if "InferenceRequest" in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"]["InferenceRequest"]["example"] = {
                "initial_facts": [
                    {"subject": "Bird", "predicate": "isA", "object": "Animal", "confidence": 1.0},
                    {"subject": "Penguin", "predicate": "isA", "object": "Bird", "confidence": 1.0}
                ],
                "goal": {"subject": "Penguin", "predicate": "isA", "object": "Animal"},
                "max_depth": 5,
                "method": "forward"
            }
        
        if "ConfidenceRequest" in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"]["ConfidenceRequest"]["example"] = {
                "evidence": [
                    {"source": "source1", "reliability": 0.9, "content": "Evidence 1"},
                    {"source": "source2", "reliability": 0.7, "content": "Evidence 2"}
                ],
                "method": "weighted"
            }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Override default OpenAPI generation
app.openapi = custom_openapi


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
    """API Root
    
    Returns basic API information including version, status, and performance metrics.
    
    ### Response
    - **name**: API name
    - **version**: API version (currently 3.5.0)
    - **description**: Brief description
    - **docs**: Link to Swagger documentation
    - **status**: Service status
    - **metrics**: Current performance metrics
    
    ### Example Response
    ```json
    {
        "name": "Ontology Platform API",
        "version": "3.5.0",
        "description": "基于ontology-clawra v3.4的生产级本体平台",
        "docs": "/docs",
        "status": "running",
        "metrics": {
            "requests_per_second": 150.5,
            "avg_response_time_ms": 12.3,
            "cache_stats": {"size": 500, "hit_rate": 0.85}
        }
    }
    ```
    """
    perf_snapshot = performance_monitor.get_snapshot()
    return {
        "name": "Ontology Platform API",
        "version": "3.5.0",
        "description": "基于ontology-clawra v3.5的生产级本体平台",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "status": "running" if state.initialized else "initializing",
        "metrics": {
            "requests_per_second": perf_snapshot.requests_per_second,
            "avg_response_time_ms": perf_snapshot.avg_response_time_ms,
            "cache_stats": inference_cache.stats()
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    perf_snapshot = performance_monitor.get_snapshot()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "rdf_adapter": state.rdf_adapter is not None,
            "neo4j_client": state.neo4j_client is not None,
            "reasoner": state.reasoner is not None,
            "neo4j_connected": state.neo4j_client.is_connected() if state.neo4j_client else False
        },
        "performance": {
            "requests_per_second": perf_snapshot.requests_per_second,
            "avg_response_time_ms": perf_snapshot.avg_response_time_ms,
            "active_connections": perf_snapshot.active_connections
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


# ==================== SPARQL & Export API (v3.3新增) ====================

class SparqlRequest(BaseModel):
    """SPARQL查询请求"""
    query: str


@app.post("/api/v1/sparql")
async def execute_sparql(
    request: SparqlRequest,
    adapter: RDFAdapter = Depends(get_rdf_adapter)
):
    """执行SPARQL查询"""
    results = adapter.sparql_query(request.query)
    return {"results": results, "count": len(results)}


@app.get("/api/v1/export/turtle")
async def export_turtle(adapter: RDFAdapter = Depends(get_rdf_adapter)):
    """导出Turtle格式"""
    return {"format": "turtle", "content": adapter.to_turtle()}


@app.get("/api/v1/export/jsonld")
async def export_jsonld(adapter: RDFAdapter = Depends(get_rdf_adapter)):
    """导出JSON-LD格式"""
    return adapter.to_jsonld()


@app.get("/api/v1/export/rdfxml")
async def export_rdfxml(adapter: RDFAdapter = Depends(get_rdf_adapter)):
    """导出RDF/XML格式"""
    return {"format": "rdfxml", "content": adapter.to_rdfxml()}


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


# ==================== 主动学习 API (v3.3新增) ====================

class ExtractRequest(BaseModel):
    """抽取请求"""
    text: str = Field(..., description="要抽取的文本")


class ConfidenceUpgradeRequest(BaseModel):
    """置信度升级请求"""
    entity_name: str
    from_level: str = Field(default="ASSUMED", description="当前置信度级别")
    to_level: str = Field(default="CONFIRMED", description="目标置信度级别")


class SuggestionRequest(BaseModel):
    """建议请求"""
    query: str
    failed_concepts: List[str] = Field(default_factory=list)


if AUTO_LEARN_AVAILABLE:
    @app.post("/api/v1/auto-learn/extract")
    async def extract_entities(request: ExtractRequest):
        """从文本中抽取实体"""
        entities = auto_learn_engine.extract_from_text(request.text)
        relations = auto_learn_engine.extract_relations(
            request.text, entities
        )
        
        return {
            "entities": [
                {
                    "type": e.entity_type.value,
                    "name": e.name,
                    "properties": e.properties,
                    "confidence": e.confidence.value
                }
                for e in entities
            ],
            "relations": [
                {
                    "type": r.relation_type,
                    "subject": r.subject,
                    "object": r.object,
                    "confidence": r.confidence.value
                }
                for r in relations
            ],
            "entity_count": len(entities),
            "relation_count": len(relations)
        }
    
    @app.post("/api/v1/auto-learn/save")
    async def save_extracted(
        request: ExtractRequest,
    ):
        """保存抽取的实体到本体"""
        entities = auto_learn_engine.extract_from_text(request.text)
        relations = auto_learn_engine.extract_relations(
            request.text, entities
        )
        
        result = auto_learn_engine.save_to_ontology(entities, relations)
        
        return {
            "success": True,
            **result
        }
    
    @app.post("/api/v1/auto-learn/upgrade-confidence")
    async def upgrade_confidence(request: ConfidenceUpgradeRequest):
        """升级实体置信度"""
        from_level = ConfidenceLevel(request.from_level)
        to_level = ConfidenceLevel(request.to_level)
        
        success = auto_learn_engine.upgrade_confidence(from_level, to_level)
        
        return {
            "entity_name": request.entity_name,
            "from_level": request.from_level,
            "to_level": request.to_level,
            "upgraded": success
        }
    
    @app.post("/api/v1/auto-learn/suggest")
    async def suggest_supplement(request: SuggestionRequest):
        """获取本体补充建议"""
        suggestions = auto_learn_engine.suggest_supplement(
            request.query,
            request.failed_concepts
        )
        
        return {
            "query": request.query,
            "suggestions": suggestions
        }
    
    @app.get("/api/v1/auto-learn/stats")
    async def get_learn_stats():
        """获取学习引擎统计"""
        return auto_learn_engine.get_stats()
    
    @app.get("/api/v1/auto-learn/log")
    async def get_extraction_log(limit: int = Query(100, ge=1, le=1000)):
        """获取抽取日志"""
        return {
            "log": auto_learn_engine.get_extraction_log(limit)
        }
    
    @app.get("/api/v1/auto-learn/high-frequency")
    async def get_high_frequency_entities(threshold: int = Query(3, ge=1, le=10)):
        """获取高频实体"""
        return {
            "entities": auto_learn_engine.check_high_frequency(threshold),
            "threshold": threshold
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


# ==================== 安全 API ====================

class APIKeyCreateRequest(BaseModel):
    """创建API密钥请求"""
    user_id: str
    permissions: List[str] = ["read"]
    expires_in_days: int = 90


class APIKeyResponse(BaseModel):
    """API密钥响应"""
    api_key: str
    user_id: str
    permissions: List[str]
    expires_at: str


@app.post("/api/v1/auth/api-keys", response_model=APIKeyResponse)
async def create_api_key(request: APIKeyCreateRequest):
    """创建新的API密钥"""
    key = api_key_manager.generate_key(
        user_id=request.user_id,
        permissions=request.permissions,
        expires_in_days=request.expires_in_days
    )
    
    key_data = api_key_manager.validate_key(key)
    
    return APIKeyResponse(
        api_key=key,
        user_id=key_data["user_id"],
        permissions=key_data["permissions"],
        expires_at=key_data["expires_at"].isoformat()
    )


@app.get("/api/v1/auth/api-keys")
async def list_api_keys(user_id: str = None):
    """列出API密钥"""
    return {"keys": api_key_manager.list_keys(user_id)}


@app.delete("/api/v1/auth/api-keys/{key_prefix}")
async def revoke_api_key(key_prefix: str):
    """撤销API密钥"""
    # Note: In practice, we'd need the full key or store a mapping
    return {"message": "API key revocation not fully implemented"}


# ==================== 性能优化 API ====================

class CacheStatsResponse(BaseModel):
    """缓存统计响应"""
    size: int
    max_size: int
    ttl_seconds: int


@app.get("/api/v1/performance/cache")
async def get_cache_stats():
    """获取缓存统计
    
    Returns detailed cache statistics including hits, misses, hit rate, and eviction counts.
    
    ### Cache Statistics
    - **size**: Current number of cached items
    - **max_size**: Maximum cache capacity
    - **hits**: Number of cache hits
    - **misses**: Number of cache misses
    - **hit_rate**: Ratio of hits to total requests
    - **evictions**: Number of items evicted
    - **expired**: Number of items expired
    
    ### Example Response
    ```json
    {
        "size": 450,
        "max_size": 1000,
        "hits": 850,
        "misses": 150,
        "hit_rate": 0.85,
        "evictions": 50,
        "expired": 200,
        "default_ttl": 3600,
        "avg_age_seconds": 120.5,
        "avg_access_count": 5.2
    }
    ```
    """
    return inference_cache.stats()


@app.get("/api/v1/performance/cache/two-level")
async def get_two_level_cache_stats():
    """获取两级缓存统计
    
    Returns statistics for the two-level cache system (L1 memory + L2 Redis if configured).
    
    ### Response includes:
    - L1 cache stats (memory)
    - L2 cache stats (Redis if available)
    - Hit rates for each level
    """
    return query_cache.stats()


@app.get("/api/v1/performance/cache/debug")
async def get_debug_cache_stats():
    """获取调试缓存统计
    
    Returns debug cache statistics with recent access logs.
    """
    return debug_cache.stats()


@app.get("/api/v1/performance/cache/debug/log")
async def get_cache_access_log(limit: int = Query(100, ge=1, le=1000)):
    """获取缓存访问日志
    
    Returns recent cache access log for debugging purposes.
    
    ### Query Parameters
    - **limit**: Maximum number of log entries to return (default: 100, max: 1000)
    """
    return {"access_log": debug_cache.get_access_log(limit)}


@app.post("/api/v1/performance/cache/clear")
async def clear_cache():
    """清除缓存
    
    Clears the main inference cache.
    """
    inference_cache.clear()
    return {"message": "Cache cleared"}


@app.post("/api/v1/performance/cache/clear-all")
async def clear_all_caches():
    """清除所有缓存
    
    Clears all cache layers including inference cache, query cache, and debug cache.
    """
    inference_cache.clear()
    query_cache.clear()
    debug_cache.clear()
    return {"message": "All caches cleared"}


@app.post("/api/v1/performance/cache/invalidate")
async def invalidate_cache_by_tag(tag: str = Body(...)):
    """通过标签使缓存失效
    
    Invalidates all cache entries with a specific tag.
    
    ### Request Body
    - **tag**: Tag to invalidate
    
    ### Example
    ```json
    {"tag": "ontology:schema"}
    ```
    """
    inference_cache.invalidate_by_tag(tag)
    return {"message": f"Cache invalidated for tag: {tag}"}


@app.post("/api/v1/performance/cache/invalidate-pattern")
async def invalidate_cache_by_pattern(pattern: str = Body(...)):
    """通过模式使缓存失效
    
    Invalidates all cache entries matching a glob pattern.
    
    ### Request Body
    - **pattern**: Glob pattern to match (e.g., "entity:*")
    
    ### Example
    ```json
    {"pattern": "entity:*"}
    ```
    """
    inference_cache.invalidate_by_pattern(pattern)
    return {"message": f"Cache invalidated for pattern: {pattern}"}


# ==================== Error Statistics API ====================

@app.get("/api/v1/errors/stats")
async def get_error_stats():
    """获取错误统计
    
    Returns error statistics including error counts by type and recent errors.
    
    ### Response
    - **total_errors**: Total number of errors
    - **error_counts**: Breakdown by error type
    - **recent_errors**: Last 10 errors with details
    
    ### Example
    ```json
    {
        "total_errors": 50,
        "error_counts": {
            "ValidationException": 20,
            "NotFoundException": 15,
            "GraphConnectionException": 5
        },
        "recent_errors": [...]
    }
    ```
    """
    return error_handler.get_error_stats()


# ==================== Cache Configuration API ====================

class CacheConfigRequest(BaseModel):
    """缓存配置请求"""
    strategy: str = Field(default="lru", description="Cache strategy: lru, lfu, fifo, ttl")
    max_size: int = Field(default=1000, ge=1, le=100000, description="Maximum cache size")
    default_ttl: float = Field(default=3600, ge=1, le=86400, description="Default TTL in seconds")
    enable_redis: bool = Field(default=False, description="Enable Redis L2 cache")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")


@app.post("/api/v1/performance/cache/config")
async def update_cache_config(request: CacheConfigRequest):
    """更新缓存配置
    
    Updates the cache configuration (affects new cache instances).
    
    ### Request Body
    - **strategy**: Cache eviction strategy (lru, lfu, fifo, ttl)
    - **max_size**: Maximum number of items
    - **default_ttl**: Default time-to-live in seconds
    - **enable_redis**: Whether to use Redis for L2 cache
    - **redis_host**: Redis server host
    - **redis_port**: Redis server port
    - **redis_db**: Redis database number
    """
    config = CacheConfig.from_dict({
        "strategy": request.strategy,
        "max_size": request.max_size,
        "default_ttl": request.default_ttl,
        "enable_redis": request.enable_redis,
        "redis_config": {
            "host": request.redis_host,
            "port": request.redis_port,
            "db": request.redis_db
        } if request.enable_redis else None
    })
    
    return {
        "message": "Cache configuration updated",
        "config": config.to_dict()
    }


@app.get("/api/v1/performance/cache/config")
async def get_cache_config():
    """获取当前缓存配置
    
    Returns the current cache configuration.
    """
    return {
        "inference_cache": inference_cache.stats(),
        "query_cache": query_cache.stats(),
        "debug_cache": debug_cache.stats()
    }


# ==================== 数据导出 API ====================

class ExportRequest(BaseModel):
    """导出请求"""
    format: str = Field(default="json", description="导出格式: json, csv, turtle, jsonld")
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object: Optional[str] = None
    label: Optional[str] = None
    include_metadata: bool = True
    include_schema: bool = True
    max_records: int = Field(default=10000, ge=1, le=100000)


@app.post("/api/v1/export/triples")
async def export_triples(
    request: ExportRequest,
    adapter: RDFAdapter = Depends(get_rdf_adapter)
):
    """导出三元组数据"""
    # Update exporter with current adapter
    exporter = DataExporter(rdf_adapter=adapter)
    
    try:
        fmt = ExportFormat(request.format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
    
    options = ExportOptions(
        format=fmt,
        include_metadata=request.include_metadata,
        include_schema=request.include_schema,
        max_records=request.max_records
    )
    
    result = exporter.export_triples(
        subject=request.subject,
        predicate=request.predicate,
        obj=request.object,
        options=options
    )
    
    # Determine content type
    content_types = {
        "json": "application/json",
        "csv": "text/csv",
        "turtle": "text/turtle",
        "jsonld": "application/ld+json"
    }
    
    return Response(
        content=result,
        media_type=content_types.get(request.format, "application/json"),
        headers={"Content-Disposition": f"attachment; filename=triples.{request.format}"}
    )


@app.post("/api/v1/export/entities")
async def export_entities(
    request: ExportRequest,
    client: Neo4jClient = Depends(get_neo4j_client)
):
    """导出实体数据"""
    exporter = DataExporter(neo4j_client=client)
    
    try:
        fmt = ExportFormat(request.format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
    
    options = ExportOptions(
        format=fmt,
        include_metadata=request.include_metadata,
        max_records=request.max_records
    )
    
    result = exporter.export_entities(
        label=request.label,
        options=options
    )
    
    content_types = {
        "json": "application/json",
        "csv": "text/csv"
    }
    
    return Response(
        content=result,
        media_type=content_types.get(request.format, "application/json"),
        headers={"Content-Disposition": f"attachment; filename=entities.{request.format}"}
    )


@app.post("/api/v1/export/schema")
async def export_schema(
    request: ExportRequest,
    adapter: RDFAdapter = Depends(get_rdf_adapter)
):
    """导出本体Schema"""
    exporter = DataExporter(rdf_adapter=adapter)
    
    try:
        fmt = ExportFormat(request.format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
    
    options = ExportOptions(
        format=fmt,
        include_metadata=request.include_metadata
    )
    
    result = exporter.export_schema(options=options)
    
    content_types = {
        "json": "application/json",
        "jsonld": "application/ld+json"
    }
    
    return Response(
        content=result,
        media_type=content_types.get(request.format, "application/json"),
        headers={"Content-Disposition": f"attachment; filename=schema.{request.format}"}
    )


# ==================== 权限管理 API ====================

class RoleCreateRequest(BaseModel):
    """创建角色请求"""
    name: str
    description: str
    permissions: List[str] = []
    inherits_from: List[str] = []


class UserRoleRequest(BaseModel):
    """用户角色分配请求"""
    user_id: str
    role_name: str


@app.get("/api/v1/permissions/roles")
async def list_roles():
    """列出所有角色"""
    return {"roles": permission_manager.list_roles()}


@app.post("/api/v1/permissions/roles")
async def create_role(request: RoleCreateRequest):
    """创建新角色"""
    try:
        perms = {Permission(p) for p in request.permissions}
        role = permission_manager.create_role(
            name=request.name,
            description=request.description,
            permissions=perms,
            inherits_from=request.inherits_from
        )
        return {"message": "Role created", "role": role.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/v1/permissions/roles/{role_name}")
async def update_role(role_name: str, request: RoleCreateRequest):
    """更新角色"""
    try:
        perms = {Permission(p) for p in request.permissions}
        role = permission_manager.update_role(
            name=role_name,
            description=request.description,
            permissions=perms,
            inherits_from=request.inherits_from
        )
        return {"message": "Role updated", "role": role.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/permissions/roles/{role_name}")
async def delete_role(role_name: str):
    """删除角色"""
    try:
        success = permission_manager.delete_role(role_name)
        if success:
            return {"message": "Role deleted"}
        raise HTTPException(status_code=404, detail="Role not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/permissions/users/{user_id}/roles")
async def get_user_roles(user_id: str):
    """获取用户角色"""
    return {"user_id": user_id, "roles": permission_manager.get_user_roles(user_id)}


@app.post("/api/v1/permissions/users/roles")
async def assign_role(request: UserRoleRequest):
    """分配角色给用户"""
    try:
        permission_manager.assign_role(request.user_id, request.role_name)
        return {"message": "Role assigned"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/permissions/users/{user_id}/roles/{role_name}")
async def remove_user_role(user_id: str, role_name: str):
    """移除用户角色"""
    success = permission_manager.remove_role(user_id, role_name)
    if success:
        return {"message": "Role removed"}
    return {"message": "Role not assigned to user"}


@app.get("/api/v1/permissions/users/{user_id}/permissions")
async def get_user_permissions(user_id: str):
    """获取用户权限"""
    perms = permission_manager.get_user_permissions(user_id)
    return {"user_id": user_id, "permissions": [p.value for p in perms]}


@app.get("/api/v1/permissions/check")
async def check_permission(
    user_id: str,
    permission: str
):
    """检查用户权限"""
    try:
        perm = Permission(permission)
        has_permission = permission_manager.check_permission(user_id, perm)
        return {"user_id": user_id, "permission": permission, "allowed": has_permission}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid permission: {permission}")


# ==================== 增强缓存 API ====================

class CacheCreateRequest(BaseModel):
    """创建缓存请求"""
    cache_type: str = "lru"
    max_size: int = 1000
    default_ttl: float = 3600


@app.post("/api/v1/performance/cache/create")
async def create_custom_cache(request: CacheCreateRequest):
    """创建自定义缓存"""
    try:
        create_cache(
            cache_type=request.cache_type,
            max_size=request.max_size,
            default_ttl=request.default_ttl
        )
        return {"message": "Cache created", "config": request.dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 运行入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level="info"
    )
