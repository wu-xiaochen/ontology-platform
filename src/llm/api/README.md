# API 模块 (API Module)

本目录包含 ontology-platform 的 API 层实现，基于 FastAPI 框架提供 RESTful 和 GraphQL 接口。

## 📁 文件结构

```
src/api/
├── main.py          # FastAPI 主入口，RESTful 端点定义
├── graphql.py       # Strawberry GraphQL 模式定义
└── __init__.py
```

## 🚀 核心功能

### main.py - RESTful API 主入口

**框架**: FastAPI

**主要特性**:
- RESTful 端点（CRUD 操作）
- GraphQL 支持（通过 Strawberry）
- 推理引擎集成
- 置信度传播
- 推理链追溯
- Swagger/OpenAPI 文档
- 全局错误处理
- 缓存策略优化

**版本更新历史**:
- **v3.4.0**: Prometheus 监控、API Key 认证、速率限制、安全头、性能优化
- **v3.5.0**: 详细 Swagger 文档、全局异常处理、Redis 分布式缓存、缓存预热

**主要依赖模块**:
```python
from src.ontology.rdf_adapter import RDFAdapter        # RDF 适配层
from src.ontology.neo4j_client import Neo4jClient      # Neo4j 图数据库
from src.loader import OntologyLoader                  # 本体加载器
from src.reasoner import Reasoner                      # 推理引擎
from src.confidence import ConfidenceCalculator        # 置信度计算
from src.monitoring import metrics                     # 监控指标
from src.security import api_key_manager               # 安全认证
from src.performance import inference_cache            # 性能优化
from src.export import DataExporter                    # 数据导出
```

### graphql.py - GraphQL 接口

**框架**: Strawberry

**功能**:
- 图查询接口
- 本体探索
- 推理结果查询

## 🔧 使用示例

### 启动 API 服务

```bash
# 使用 uvicorn 启动
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 访问 Swagger 文档
http://localhost:8000/docs
```

### API 端点示例

```bash
# 获取本体信息
curl http://localhost:8000/api/ontology

# 查询实体
curl http://localhost:8000/api/entities?q=knowledge

# 推理查询
curl -X POST http://localhost:8000/api/reason \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是知识图谱？"}'
```

## 🔐 安全特性

- **API Key 认证**: 所有端点需要有效的 API Key
- **速率限制**: 防止滥用
- **CORS 配置**: 跨域请求控制
- **审计日志**: 所有操作记录

## 📊 监控

- **Prometheus 指标**: `/metrics` 端点
- **性能监控**: 请求延迟、吞吐量
- **错误追踪**: 异常统计

## 📚 相关文档

- [项目主 README](../../README.md)
- [Ontology 模块](../ontology/README.md)
- [Reasoner 模块](../reasoner.py)
