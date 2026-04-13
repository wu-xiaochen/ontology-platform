# API - 接口层

本目录提供 ontology-platform 的对外 API 接口，包括 RESTful API 和 GraphQL API，支持多种客户端接入方式。

## 📁 文件结构

```
api/
├── __init__.py          # 模块导出
├── main.py              # FastAPI 主应用（RESTful API）
├── graphql.py           # GraphQL 服务端点和解析器
└── api/                 # 子模块（见下）
    └── README.md        # API 设计文档
```

## 🚀 核心功能

### 1. RESTful API (`main.py`)

基于 FastAPI 构建的高性能 RESTful API 服务：

**启动服务**:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**主要端点**:

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/v1/ontology/load` | 加载本体知识 |
| POST | `/api/v1/ontology/reason` | 执行推理 |
| POST | `/api/v1/confidence/calculate` | 计算置信度 |
| GET | `/api/v1/memory/search` | 搜索记忆 |
| POST | `/api/v1/agents/execute` | 执行 Agent 任务 |

**请求示例**:

```bash
# 加载本体知识
curl -X POST http://localhost:8000/api/v1/ontology/load \
  -H "Content-Type: application/json" \
  -d '{"path": "domain_expert/supply_chain"}'

# 执行推理
curl -X POST http://localhost:8000/api/v1/ontology/reason \
  -H "Content-Type: application/json" \
  -d '{
    "query": "供应商 A 的风险等级是什么？",
    "evidence": ["交货延迟 3 次", "质量投诉 2 次"]
  }'
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "result": "高风险",
    "confidence": 0.85,
    "reasoning_chain": [
      "检测到交货延迟模式",
      "质量投诉频率超标",
      "综合评估为高风险"
    ],
    "evidence_used": 2
  },
  "metadata": {
    "timestamp": "2026-04-01T06:00:00Z",
    "version": "1.0.0",
    "processing_time_ms": 125
  }
}
```

### 2. GraphQL API (`graphql.py`)

提供灵活的 GraphQL 查询接口：

**Schema 定义**:
```graphql
type Ontology {
  id: ID!
  name: String!
  concepts: [Concept!]!
  relations: [Relation!]!
}

type Concept {
  id: ID!
  label: String!
  type: String!
  properties: [Property!]!
}

type Query {
  ontology(id: ID!): Ontology
  search(query: String!, limit: Int): [Concept!]!
  reason(query: String!, evidence: [String!]): ReasoningResult!
}

type Mutation {
  loadOntology(path: String!): Boolean!
  addConcept(label: String!, type: String!): Concept!
  addRelation(subject: ID!, predicate: String!, object: ID!): Relation!
}
```

**查询示例**:

```bash
# 查询本体结构
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{
      ontology(id: \"supply-chain\") {
        name
        concepts {
          label
          type
        }
      }
    }"
  }'

# 执行推理查询
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query Reason($query: String!, $evidence: [String!]) {
      reason(query: $query, evidence: $evidence) {
        result
        confidence
        reasoningChain
      }
    }",
    "variables": {
      "query": "供应商 A 是否可靠？",
      "evidence": ["3 年合作历史", "零重大事故"]
    }
  }'
```

## 📖 使用示例

### Python 客户端

```python
import requests

# RESTful API 调用
api_url = "http://localhost:8000/api/v1"

# 1. 加载本体
response = requests.post(
    f"{api_url}/ontology/load",
    json={"path": "domain_expert/hr"}
)
assert response.json()["success"]

# 2. 执行推理
response = requests.post(
    f"{api_url}/ontology/reason",
    json={
        "query": "候选人是否适合技术总监职位？",
        "evidence": [
            "10 年开发经验",
            "管理过 50 人团队",
            "主导过 3 个大型项目"
        ]
    }
)
result = response.json()["data"]
print(f"结果：{result['result']}")
print(f"置信度：{result['confidence']:.2%}")

# 3. GraphQL 查询
graphql_query = """
query {
  search(query: "技术领导力", limit: 5) {
    label
    type
    relevanceScore
  }
}
"""
response = requests.post(
    "http://localhost:8000/graphql",
    json={"query": graphql_query}
)
results = response.json()["data"]["search"]
```

### JavaScript/TypeScript 客户端

```typescript
// RESTful API
async function executeReasoning(query: string, evidence: string[]) {
  const response = await fetch('http://localhost:8000/api/v1/ontology/reason', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, evidence })
  });
  
  const result = await response.json();
  return result.data;
}

// GraphQL API (使用 Apollo Client)
import { ApolloClient, InMemoryCache, gql } from '@apollo/client';

const client = new ApolloClient({
  uri: 'http://localhost:8000/graphql',
  cache: new InMemoryCache()
});

const RESULT = await client.query({
  query: gql`
    query Reason($query: String!, $evidence: [String!]) {
      reason(query: $query, evidence: $evidence) {
        result
        confidence
        reasoningChain
      }
    }
  `,
  variables: {
    query: "供应商风险评估",
    evidence: ["延迟交货", "质量投诉"]
  }
});
```

## 🔧 配置选项

### API 服务配置

```python
# .env 或配置文件中
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True
API_MAX_CONCURRENT_REQUESTS=100
API_TIMEOUT_SECONDS=300
API_RATE_LIMIT=1000  # 每分钟请求数
```

### CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 认证配置（可选）

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/protected-endpoint")
async def protected(endpoint_data: dict, token: str = Depends(security)):
    # 验证 token
    pass
```

## 📊 性能监控

### 指标端点

```bash
# Prometheus 格式指标
curl http://localhost:8000/metrics

# 健康检查详情
curl http://localhost:8000/health
```

**监控指标**:
- `api_requests_total`: 总请求数
- `api_request_duration_seconds`: 请求延迟
- `api_errors_total`: 错误数
- `ontology_query_cache_hit_ratio`: 缓存命中率

### 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ontology_api")
```

## 🧪 测试

### 运行测试

```bash
# 单元测试
pytest tests/api/ -v

# 集成测试
pytest tests/api/integration/ -v

# 负载测试
locust -f tests/api/load_test.py --headless -u 100 -r 10 -t 300s
```

### 手动测试

```bash
# 使用 Swagger UI
open http://localhost:8000/docs

# 使用 GraphQL Playground
open http://localhost:8000/graphql
```

## 📚 相关文档

- [API 设计规范](api/README.md) - 详细设计文档
- [主 README](../../README.md) - 项目总览
- [示例代码](../../examples/) - 完整使用示例

## 🤝 贡献指南

添加新 API 端点时：
1. 遵循 RESTful 设计规范
2. 添加完整的类型注解
3. 编写单元测试（覆盖率 > 80%）
4. 更新 OpenAPI 文档
5. 添加错误处理和重试机制

## ⚠️ 注意事项

- 生产环境需启用 HTTPS
- 敏感操作需要认证授权
- 大文件上传需分片处理
- 长时间运行的任务应使用异步队列
- GraphQL 查询需限制深度和复杂度
