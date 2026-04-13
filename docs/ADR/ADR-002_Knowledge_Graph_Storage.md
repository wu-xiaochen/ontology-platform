# ADR-002: Knowledge Graph Storage Architecture

> 状态: **已通过** | 日期: 2026-04-06

---

## 背景

Clawra 的知识图谱需要持久化存储，需要支持：
- 实体和关系的存储与查询
- 属性的动态扩展
- 高效的图遍历查询
- 事务支持（原子性操作）
- 向量检索（语义相似度）

---

## 决策

### 方案选择

| 方案 | 优点 | 缺点 |
|------|------|------|
| **A. Neo4j + ChromaDB** | Neo4j 图遍历强 + ChromaDB 向量强 | 两套系统，需同步 |
| B. Neo4j (原生向量) | 单一系统 | Neo4j 向量性能一般 |
| C. PostgreSQL + pgvector | 单一系统，成熟 | 图遍历不如 Neo4j |
| D. 纯内存 | 最快 | 数据不持久化 |

**选择：方案 A - Neo4j + ChromaDB 分层存储**

### 核心设计

```
┌─────────────────────────────────────┐
│           Clawra KG Layer           │
│                                     │
│  ┌─────────────┐  ┌──────────────┐ │
│  │  Neo4j      │  │  ChromaDB    │ │
│  │  (结构化)    │  │  (向量)      │ │
│  │  实体/关系  │  │  语义检索    │ │
│  └─────────────┘  └──────────────┘ │
└─────────────────────────────────────┘
```

#### Neo4j Schema

```cypher
// 实体节点
(:Entity {
    id: string,           // 唯一标识
    name: string,         // 显示名称
    type: string,         // 实体类型
    domain: string,       // 领域
    confidence: float,    // 置信度
    properties: map,      // 动态属性
    created_at: datetime,
    updated_at: datetime
})

// 关系
[:RELATES {
    predicate: string,    // 关系类型
    confidence: float,
    source: string,       // 来源
    created_at: datetime
}]

// 模式节点
(:Pattern {
    id: string,
    name: string,
    logic_type: string,
    conditions: list,
    actions: list,
    confidence: float,
    version: string,
    domain: string
})
```

#### ChromaDB Schema

```python
# Collection: entities
{
    "ids": ["entity_001", "entity_002"],
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],  # 768维
    "metadatas": [
        {"name": "调压箱A", "type": "设备", "domain": "燃气"},
        {"name": "调压箱B", "type": "设备", "domain": "燃气"}
    ],
    "documents": [
        "调压箱A是燃气调压设备，用于降低燃气压力",
        "调压箱B是燃气调压设备，用于降低燃气压力"
    ]
}

# Collection: patterns
{
    "ids": ["pattern_001"],
    "embeddings": [[...]],
    "metadatas": [
        {"logic_type": "RULE", "domain": "燃气"}
    ],
    "documents": ["燃气调压箱出口压力 <= 0.4MPa"]
}
```

### 数据同步策略

```python
class KnowledgeGraphSync:
    """Neo4j 与 ChromaDB 同步"""

    def add_entity(self, entity: Entity):
        # 1. 写入 Neo4j
        self.neo4j.create_entity(entity)

        # 2. 写入 ChromaDB（获取嵌入）
        embedding = self.embedding_model.encode(entity.description)
        self.chromadb.add(
            collection="entities",
            ids=[entity.id],
            embeddings=[embedding],
            metadatas=[entity.to_metadata()],
            documents=[entity.description]
        )

    def query_similar(self, text: str, top_k: int = 5):
        # 1. 获取查询向量
        query_embedding = self.embedding_model.encode(text)

        # 2. ChromaDB 语义检索
        results = self.chromadb.query(
            collection="entities",
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # 3. 返回实体 ID，可选：回查 Neo4j 获取完整关系
        return results
```

---

## 后果

### 正面

- ✅ Neo4j 提供强大的图遍历和 Cypher 查询
- ✅ ChromaDB 提供高效的向量检索
- ✅ 两者互补，满足 GraphRAG 需求
- ✅ 可以独立扩展（读写分离）

### 负面

- ❌ 两套系统增加运维复杂度
- ❌ 需要处理数据一致性
- ❌ 增加存储成本

### 风险缓解

- ⚠️ 使用事务保证原子性
- ⚠️ 定期一致性检查脚本
- ⚠️ 监控两套系统的健康状态

---

## 实现清单

- [x] `src/memory/neo4j_client.py` - Neo4j 客户端封装
- [x] `src/memory/chroma_client.py` - ChromaDB 客户端封装
- [x] `src/memory/sync.py` - 同步逻辑
- [x] `src/memory/manager.py` - 统一管理器
- [x] schema 迁移脚本

---

## 相关 ADR

- [ADR-001](./ADR-001_LLM_Provider_Abstraction.md) - LLM Provider 选择影响嵌入模型
