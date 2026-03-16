#!/usr/bin/env python3
"""
Ontology Platform API Server
提供 RESTful API 服务，支持推理和本体查询
"""

import os
import sys
from typing import Any, Dict, List, Optional

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 导入本体模块
from src.loader import OntologyLoader
from src.reasoner import Reasoner
from src.confidence import ConfidenceCalculator

# ============== 配置 ==============
APP_DIR = "/Users/xiaochenwu/.openclaw/workspace/ontology-platform"
ONTOLOGY_PATH = os.path.join(APP_DIR, "ontology.json")

# ============== FastAPI 应用 ==============
app = FastAPI(
    title="Ontology Platform API",
    description="本体推理与查询平台",
    version="1.0.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== 全局状态 ==============
ontology_loader: Optional[OntologyLoader] = None
reasoner: Optional[Reasoner] = None


def initialize_ontology():
    """初始化本体加载器"""
    global ontology_loader, reasoner
    
    try:
        if os.path.exists(ONTOLOGY_PATH):
            ontology_loader = OntologyLoader().load(ONTOLOGY_PATH)
            reasoner = Reasoner(ontology_loader)
            print(f"✓ 本体加载成功: {ONTOLOGY_PATH}")
        else:
            # 创建一个空的本体加载器
            ontology_loader = OntologyLoader()
            reasoner = Reasoner(ontology_loader)
            print(f"⚠ 本体文件不存在，使用空本体: {ONTOLOGY_PATH}")
    except Exception as e:
        print(f"✗ 本体加载失败: {e}")
        ontology_loader = OntologyLoader()
        reasoner = Reasoner(ontology_loader)


# 启动时初始化
@app.on_event("startup")
async def startup_event():
    initialize_ontology()


# ============== 请求/响应模型 ==============

class ReasonRequest(BaseModel):
    """推理请求"""
    query: str = Field(..., description="推理查询语句")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")
    options: Optional[Dict[str, Any]] = Field(default=None, description="推理选项")


class ReasonResponse(BaseModel):
    """推理响应"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    inference_chain: Optional[List[Dict[str, Any]]] = None


class OntologyQueryRequest(BaseModel):
    """本体查询请求"""
    subject: Optional[str] = Field(None, description="主语")
    predicate: Optional[str] = Field(None, description="谓词")
    object: Optional[str] = Field(None, description="对象")
    query_type: str = Field("triple", description="查询类型: triple/class/property/individual")


class OntologyQueryResponse(BaseModel):
    """本体查询响应"""
    success: bool
    result: Optional[Any] = None
    count: Optional[int] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    ontology_loaded: bool
    version: str


# ============== API 路由 ==============

@app.get("/", response_model=HealthResponse)
async def root():
    """健康检查"""
    return HealthResponse(
        status="running",
        ontology_loaded=ontology_loader is not None,
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """健康检查"""
    return HealthResponse(
        status="running",
        ontology_loaded=ontology_loader is not None,
        version="1.0.0"
    )


# ============== 推理接口 ==============

@app.post("/api/v1/reason", response_model=ReasonResponse)
async def reason(request: ReasonRequest):
    """
    推理接口
    
    接收自然语言查询或结构化查询，返回推理结果
    
    示例请求:
    ```json
    {
        "query": "找出所有Person的子类",
        "context": {"source": "user_query"},
        "options": {"depth": 3}
    }
    ```
    """
    try:
        if not reasoner:
            raise HTTPException(status_code=503, detail="推理引擎未初始化")
        
        query = request.query.strip()
        options = request.options or {}
        
        # 解析查询意图
        result = {}
        inference_chain = []
        
        # 简单的查询解析
        if "子类" in query or "subclass" in query.lower():
            # 提取类名
            import re
            match = re.search(r'[A-Z][a-zA-Z]+', query)
            class_name = match.group(0) if match else "Thing"
            
            # 执行推理
            inferred = reasoner.infer(class_name)
            result = {
                "type": "subclasses",
                "class": class_name,
                "classes": inferred.classes if hasattr(inferred, 'classes') else [],
                "properties": inferred.properties if hasattr(inferred, 'properties') else []
            }
            
        elif "属性" in query or "property" in query.lower():
            # 查询属性
            import re
            match = re.search(r'[A-Z][a-zA-Z]+', query)
            class_name = match.group(0) if match else "Thing"
            
            result = {
                "type": "properties",
                "class": class_name,
                "properties": reasoner.get_properties(class_name) if hasattr(reasoner, 'get_properties') else []
            }
            
        elif "实例" in query or "instance" in query.lower():
            # 查询实例
            result = {
                "type": "instances",
                "instances": []
            }
            
        else:
            # 默认：执行通用推理
            result = {
                "type": "general",
                "query": query,
                "message": "请指定查询类型（子类/属性/实例）"
            }
        
        # 计算置信度
        confidence = None
        if inference_chain:
            confidence = reasoner.propagate_confidence(inference_chain) if hasattr(reasoner, 'propagate_confidence') else 0.5
        
        return ReasonResponse(
            success=True,
            result=result,
            confidence=confidence,
            inference_chain=inference_chain if inference_chain else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ReasonResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/v1/reason/classes", response_model=ReasonResponse)
async def list_classes():
    """列出所有类"""
    try:
        if not ontology_loader:
            raise HTTPException(status_code=503, detail="本体未加载")
        
        classes = []
        if hasattr(ontology_loader, 'classes'):
            for uri, cls in ontology_loader.classes.items():
                classes.append({
                    "uri": cls.uri,
                    "label": cls.label,
                    "super_classes": cls.super_classes
                })
        
        return ReasonResponse(
            success=True,
            result={"classes": classes, "count": len(classes)}
        )
    except Exception as e:
        return ReasonResponse(success=False, error=str(e))


# ============== 本体查询接口 ==============

@app.post("/api/v1/ontology", response_model=OntologyQueryResponse)
async def ontology_query(request: OntologyQueryRequest):
    """
    本体查询接口
    
    支持多种查询类型:
    - triple: 三元组查询 (subject, predicate, object)
    - class: 类查询
    - property: 属性查询
    - individual: 实例查询
    
    示例请求:
    ```json
    {
        "subject": "Person",
        "predicate": "type",
        "object": "Class",
        "query_type": "class"
    }
    ```
    """
    try:
        if not ontology_loader:
            raise HTTPException(status_code=503, detail="本体未加载")
        
        query_type = request.query_type
        result = None
        count = 0
        
        if query_type == "triple":
            # 三元组查询
            triples = []
            if hasattr(ontology_loader, 'triples'):
                for s, p, o in ontology_loader.triples:
                    if (not request.subject or s == request.subject) and \
                       (not request.predicate or p == request.predicate) and \
                       (not request.object or o == request.object):
                        triples.append({"subject": s, "predicate": p, "object": o})
            result = {"triples": triples}
            count = len(triples)
            
        elif query_type == "class":
            # 类查询
            classes = []
            if hasattr(ontology_loader, 'classes'):
                for uri, cls in ontology_loader.classes.items():
                    if not request.subject or cls.label == request.subject or cls.uri == request.subject:
                        classes.append({
                            "uri": cls.uri,
                            "label": cls.label,
                            "super_classes": cls.super_classes,
                            "properties": list(cls.properties.keys()) if cls.properties else []
                        })
            result = {"classes": classes}
            count = len(classes)
            
        elif query_type == "property":
            # 属性查询
            properties = []
            if hasattr(ontology_loader, 'properties'):
                for uri, prop in ontology_loader.properties.items():
                    if not request.subject or prop.label == request.subject or prop.uri == request.subject:
                        properties.append({
                            "uri": prop.uri,
                            "label": prop.label,
                            "domain": prop.domain,
                            "range": prop.range,
                            "property_type": prop.property_type
                        })
            result = {"properties": properties}
            count = len(properties)
            
        elif query_type == "individual":
            # 实例查询
            individuals = []
            if hasattr(ontology_loader, 'individuals'):
                for uri, ind in ontology_loader.individuals.items():
                    if not request.subject or ind.label == request.subject or ind.uri == request.subject:
                        individuals.append({
                            "uri": ind.uri,
                            "label": ind.label,
                            "types": ind.types,
                            "assertions": ind.assertions
                        })
            result = {"individuals": individuals}
            count = len(individuals)
            
        else:
            raise HTTPException(status_code=400, detail=f"不支持的查询类型: {query_type}")
        
        return OntologyQueryResponse(
            success=True,
            result=result,
            count=count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return OntologyQueryResponse(success=False, error=str(e))


@app.get("/api/v1/ontology/classes", response_model=OntologyQueryResponse)
async def get_classes():
    """获取所有类"""
    try:
        if not ontology_loader:
            raise HTTPException(status_code=503, detail="本体未加载")
        
        classes = []
        if hasattr(ontology_loader, 'classes'):
            for uri, cls in ontology_loader.classes.items():
                classes.append({
                    "uri": cls.uri,
                    "label": cls.label,
                    "super_classes": cls.super_classes
                })
        
        return OntologyQueryResponse(
            success=True,
            result={"classes": classes},
            count=len(classes)
        )
    except Exception as e:
        return OntologyQueryResponse(success=False, error=str(e))


@app.get("/api/v1/ontology/properties", response_model=OntologyQueryResponse)
async def get_properties():
    """获取所有属性"""
    try:
        if not ontology_loader:
            raise HTTPException(status_code=503, detail="本体未加载")
        
        properties = []
        if hasattr(ontology_loader, 'properties'):
            for uri, prop in ontology_loader.properties.items():
                properties.append({
                    "uri": prop.uri,
                    "label": prop.label,
                    "domain": prop.domain,
                    "range": prop.range
                })
        
        return OntologyQueryResponse(
            success=True,
            result={"properties": properties},
            count=len(properties)
        )
    except Exception as e:
        return OntologyQueryResponse(success=False, error=str(e))


@app.get("/api/v1/ontology/individuals", response_model=OntologyQueryResponse)
async def get_individuals():
    """获取所有实例"""
    try:
        if not ontology_loader:
            raise HTTPException(status_code=503, detail="本体未加载")
        
        individuals = []
        if hasattr(ontology_loader, 'individuals'):
            for uri, ind in ontology_loader.individuals.items():
                individuals.append({
                    "uri": ind.uri,
                    "label": ind.label,
                    "types": ind.types
                })
        
        return OntologyQueryResponse(
            success=True,
            result={"individuals": individuals},
            count=len(individuals)
        )
    except Exception as e:
        return OntologyQueryResponse(success=False, error=str(e))


# ============== 主程序入口 ==============

if __name__ == "__main__":
    print("=" * 50)
    print("Ontology Platform API Server")
    print("=" * 50)
    print("启动服务...")
    print(f"本体路径: {ONTOLOGY_PATH}")
    print("")
    print("API 端点:")
    print("  - GET  /                      健康检查")
    print("  - GET  /health                健康检查")
    print("  - POST /api/v1/reason         推理接口")
    print("  - GET  /api/v1/reason/classes 列出所有类")
    print("  - POST /api/v1/ontology       本体查询接口")
    print("  - GET  /api/v1/ontology/classes   获取所有类")
    print("  - GET  /api/v1/ontology/properties 获取所有属性")
    print("  - GET  /api/v1/ontology/individuals 获取所有实例")
    print("")
    print("运行服务: http://localhost:8000")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
