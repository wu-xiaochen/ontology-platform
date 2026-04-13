# Ontology 模块 (Ontology Module)

本目录包含本体论核心实现，提供 RDF 数据处理、Neo4j 图数据库集成和自动学习功能。

## 📁 文件结构

```
src/ontology/
├── neo4j_client.py   # Neo4j 图数据库客户端
├── rdf_adapter.py    # RDF 数据适配层
├── auto_learn.py     # 主动学习引擎
├── reasoner.py       # 轻量推理器
└── __init__.py
```

## 🚀 核心组件

### neo4j_client.py - Neo4j 图数据库集成

**功能**:
- 实体和关系的 CRUD 操作
- 图查询和遍历
- 推理链追溯
- 置信度传播

**核心类**:
- `Neo4jClient`: 主客户端，管理连接和查询
- `GraphNode`: 图节点数据模型
- `GraphRelationship`: 图关系数据模型
- `NodeLabel`: 节点标签枚举
- `RelationshipType`: 关系类型枚举

**使用示例**:
```python
from src.ontology.neo4j_client import Neo4jClient

client = Neo4jClient(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# 创建实体
node = client.create_node(
    labels=["Entity"],
    properties={"name": "Knowledge Graph", "type": "Concept"}
)

# 查询实体
results = client.query(
    "MATCH (n:Entity {name: $name}) RETURN n",
    {"name": "Knowledge Graph"}
)
```

### rdf_adapter.py - RDF 数据适配层

**功能**:
- RDF/XML、Turtle、N-Triples 格式解析
- 本体加载和序列化
- OWL/RDFS 支持
- 三元组存储和查询

**核心类**:
- `RDFAdapter`: RDF 数据处理主类
- 支持 rdflib 集成

**使用示例**:
```python
from src.ontology.rdf_adapter import RDFAdapter

adapter = RDFAdapter()

# 加载 RDF 文件
adapter.load("ontology.ttl")

# 查询三元组
triples = adapter.query(
    """
    SELECT ?s ?p ?o WHERE {
        ?s ?p ?o .
    }
    LIMIT 100
    """
)
```

### auto_learn.py - 主动学习引擎

**功能**:
- 低置信度样本识别
- 主动学习循环
- 置信度分级
- 人类反馈集成

**核心组件**:
- `auto_learn_engine`: 主动学习控制器
- `ConfidenceLevel`: 置信度等级枚举

**使用示例**:
```python
from src.ontology.auto_learn import auto_learn_engine, ConfidenceLevel

# 获取需要人工审核的低置信度样本
low_confidence = auto_learn_engine.get_low_confidence_samples(
    threshold=ConfidenceLevel.LOW
)

# 提交人类反馈
auto_learn_engine.submit_feedback(
    sample_id="sample_123",
    is_correct=True,
    correction="正确标注"
)
```

### reasoner.py - 轻量推理器

**功能**:
- 基础规则推理
- 本体一致性检查
- 分类推理

## 🔧 安装依赖

```bash
# Neo4j 驱动
pip install neo4j

# RDF 处理
pip install rdflib

# 其他依赖
pip install -r requirements.txt
```

## 📊 数据模型

### 节点标签 (NodeLabel)
- `Entity`: 实体节点
- `Concept`: 概念节点
- `Rule`: 规则节点
- `Individual`: 个体节点
- `Class`: 类节点
- `Property`: 属性节点

### 关系类型 (RelationshipType)
- `HAS_PROPERTY`: 拥有属性
- `INSTANCE_OF`: 实例关系
- `SUB_CLASS_OF`: 子类关系
- `SUB_PROPERTY_OF`: 子属性关系
- `EQUIVALENT_TO`: 等价关系
- `RELATED_TO`: 相关关系
- `CAUSED_BY`: 因果关系
- `DEPENDS_ON`: 依赖关系
- `INFERRED_FROM`: 推理来源

## 📚 相关文档

- [项目主 README](../../README.md)
- [API 模块](../api/README.md)
- [Reasoner 模块](../reasoner.py)
