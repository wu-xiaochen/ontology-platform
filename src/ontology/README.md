# Ontology Module

本体论核心模块，负责知识图谱的构建、存储和推理。

## 核心组件

### neo4j_client.py
Neo4j 图数据库客户端，提供：
- 节点和关系的 CRUD 操作
- 图查询优化
- 批量数据处理

### rdf_adapter.py
RDF（资源描述框架）适配器：
- RDF 三元组转换
- OWL 本体支持
- 语义网标准兼容

### auto_learn.py
自动学习模块：
- 从文本自动提取实体和关系
- 本体演化
- 知识融合

### reasoner.py
推理引擎：
- 基于规则的推理
- 一致性检查
- 隐含知识发现

## 使用示例

```python
from src.ontology.neo4j_client import Neo4jClient
from src.ontology.reasoner import Reasoner

# 初始化
client = Neo4jClient(url="bolt://localhost:7687")
reasoner = Reasoner(client)

# 添加知识
client.add_node("Person", {"name": "Alice", "age": 30})
client.add_relationship("KNOWS", "Alice", "Bob")

# 推理
inferred = reasoner.infer()
```

## 架构设计

```
ontology/
├── neo4j_client.py    # Neo4j 交互层
├── rdf_adapter.py     # RDF 转换层
├── auto_learn.py      # 自动学习层
└── reasoner.py        # 推理引擎
```

## 性能优化

- 批量操作：支持批量插入/更新
- 查询缓存：常用查询结果缓存
- 索引优化：自动创建和维护索引

## 依赖

- neo4j-driver >= 4.4.0
- rdflib >= 6.0.0
- networkx >= 2.6.0
