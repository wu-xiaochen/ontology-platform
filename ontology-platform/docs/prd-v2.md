# 产品需求文档 (PRD v2.0)

## 垂直领域可信AI推理引擎平台

**版本**: 2.0 (生产级)  
**状态**: 规划  
**日期**: 2026-03-19  
**基于**: ontology-clawra v3.3

---

## 1. 产品概述

### 1.1 产品定位

企业级垂直领域可信AI推理引擎平台，基于本体论(Ontology)方法解决AI幻觉问题。通过结构化知识表示、规则推理和置信度追踪，为供应链、医疗、金融、制造等垂直领域提供可解释、可追溯的智能决策支持。

### 1.2 核心价值

| 价值点 | 说明 |
|--------|------|
| **可信推理** | 每条建议都有推理依据，拒绝黑箱 |
| **置信度感知** | CONFIRMED/ASSUMED/SPECULATIVE/UNKNOWN 四级标注 |
| **可追溯** | 完整记录推理过程，支持回溯和审计 |
| **领域适配** | 预置54+领域本体，支持快速定制 |

### 1.3 目标用户

- 企业知识工程师
- 领域专家
- AI产品经理
- 运维/风控人员

---

## 2. 功能模块

### 2.1 本体管理模块

#### 2.1.1 OWL/RDF本体导入导出

| 功能 | 优先级 | 描述 |
|------|--------|------|
| OWL/XML导入 | P0 | 解析OWL本体文件 |
| RDF/XML导入 | P0 | 解析RDF格式 |
| Turtle导入 | P1 | 支持Turtle语法 |
| JSON-LD导入 | P1 | 支持JSON-LD格式 |
| 本体导出 | P0 | 支持多格式导出 |
| 批量导入 | P2 | 目录批量处理 |

**接口设计**:
```yaml
POST /api/v1/ontology/import
  - body: { format: "owl|rdf|turtle|jsonld", content: string }
  - response: { success: boolean, classes: number, properties: number }

POST /api/v1/ontology/export
  - query: { format: "owl|rdf|turtle|jsonld" }
  - response: { content: string }
```

#### 2.1.2 本体版本管理

| 功能 | 优先级 | 描述 |
|------|--------|------|
| 版本记录 | P0 | 自动记录每次修改 |
| 版本列表 | P0 | 查看历史版本 |
| 版本对比 | P1 | diff视图 |
| 版本回滚 | P1 | 回退到指定版本 |
| 分支管理 | P2 | 并行开发分支 |

**接口设计**:
```yaml
GET  /api/v1/ontology/versions
POST /api/v1/ontology/versions/{id}/rollback
GET  /api/v1/ontology/versions/{id}/diff/{other_id}
```

#### 2.1.3 本体可视化编辑

| 功能 | 优先级 | 描述 |
|------|--------|------|
| 类层级树 | P0 | 树形展示类继承关系 |
| 属性图谱 | P1 | 可视化属性连接 |
| 实例管理 | P1 | 实例CRUD操作 |
| 导入预览 | P0 | 导入前预览验证 |
| 搜索定位 | P1 | 快速定位实体 |

---

### 2.2 推理引擎服务

#### 2.2.1 RESTful API

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/v1/query` | POST | 本体语义查询 |
| `/api/v1/reason` | POST | 执行推理 |
| `/api/v1/validate` | POST | 断言验证 |
| `/api/v1/explain` | GET | 推理解释 |

**请求示例**:
```json
POST /api/v1/reason
{
  "facts": [
    {"subject": "供应商A", "predicate": "提供", "object": "产品X"}
  ],
  "rules": ["rule_1", "rule_2"],
  "direction": "forward",
  "max_depth": 5
}
```

**响应示例**:
```json
{
  "success": true,
  "conclusions": [
    {
      "subject": "供应商A",
      "predicate": "可信任",
      "object": "true",
      "confidence": 0.85,
      "confidence_level": "ASSUMED"
    }
  ],
  "reasoning_path": [
    {
      "step": 1,
      "rule": "rule_1",
      "premise": "供应商A提供产品X",
      "conclusion": "供应商A有供货能力",
      "confidence": 0.9
    }
  ],
  "total_confidence": 0.85
}
```

#### 2.2.2 GraphQL查询接口

| 类型 | 字段 | 描述 |
|------|------|------|
| Query | `queryOntology` | 本体语义查询 |
| Query | `reason` | 推理执行 |
| Query | `explain` | 推理解释 |
| Mutation | `addFact` | 添加事实 |
| Mutation | `addRule` | 添加规则 |
| Subscription | `reasoningProgress` | 推理进度 |

**Schema示例**:
```graphql
type Query {
  queryOntology(input: QueryInput!): QueryResult!
  reason(input: ReasonInput!): ReasonResult!
  explain(inferenceId: ID!): Explanation!
}

type ReasonResult {
  conclusions: [Conclusion!]!
  reasoningPath: [ReasoningStep!]!
  totalConfidence: Float!
}

type Conclusion {
  subject: String!
  predicate: String!
  object: String!
  confidence: Float!
  confidenceLevel: ConfidenceLevel!
}
```

#### 2.2.3 推理结果可解释性输出

| 功能 | 描述 |
|------|------|
| 推理路径可视化 | 展示推理链各步骤 |
| 证据来源展示 | 每步推理的依据 |
| 置信度分解 | 各因素贡献度 |
| 自然语言解释 | 生成可读解释 |

---

### 2.3 知识图谱模块

#### 2.3.1 Neo4j图数据库集成

| 功能 | 优先级 | 描述 |
|------|--------|------|
| 连接管理 | P0 | Neo4j连接池 |
| 实体CRUD | P0 | 节点增删改查 |
| 关系CRUD | P0 | 边增删改查 |
| 批量导入 | P1 | 批量节点/边导入 |
| 事务支持 | P1 | 原子性操作 |

**接口设计**:
```yaml
POST /api/v1/graph/nodes
  - body: { labels: string[], properties: object }
  - response: { id: string }

POST /api/v1/graph/relations
  - body: { type: string, start: string, end: string, properties: object }
  - response: { id: string }

GET  /api/v1/graph/nodes/{id}
GET  /api/v1/graph/paths?start={id}&end={id}
```

#### 2.3.2 图可视化查询

| 功能 | 优先级 | 描述 |
|------|--------|------|
| Cypher查询 | P0 | 执行Cypher语句 |
| 语义查询 | P1 | 本体语义查询 |
| 路径查找 | P1 | 最短/全部路径 |
| 子图提取 | P2 | 局部图导出 |

#### 2.3.3 实体关系管理

| 功能 | 优先级 | 描述 |
|------|--------|------|
| 实体搜索 | P0 | 多条件搜索 |
| 关系探索 | P0 | 扩展邻居 |
| 批量操作 | P1 | 批量导入/导出 |
| 冲突检测 | P2 | 重复实体识别 |

---

### 2.4 用户交互模块

#### 2.4.1 置信度标注展示

| 功能 | 描述 |
|------|------|
| 颜色编码 | CONFIRMED=绿, ASSUMED=黄, SPECULATIVE=橙, UNKNOWN=灰 |
| 图标标注 | 置信度徽章 |
| 详情面板 | 证据来源、计算方法 |
| 趋势图 | 历史置信度变化 |

#### 2.4.2 假设声明与确认流程

| 功能 | 描述 |
|------|------|
| 假设创建 | 声明新的假设 |
| 验证流程 | 自动/人工验证 |
| 确认操作 | 确认假设为真 |
| 否认操作 | 标记假设为假 |
| 假设历史 | 完整状态变更记录 |

**流程**:
```
创建假设 → 系统验证 → 人工审核 → 确认/否认 → 更新本体
```

#### 2.4.3 推理过程追溯

| 功能 | 描述 |
|------|------|
| 步骤时间线 | 推理过程可视化 |
| 中间结果 | 每步产出查看 |
| 推理回放 | 重现推理过程 |
| 报告导出 | PDF/HTML报告 |

---

## 3. 数据模型

### 3.1 核心实体

```
┌─────────────────┐     ┌─────────────────┐
│    Ontology    │────▶│   OntologyClass │
└─────────────────┘     └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│      Rule      │────▶│    Property     │
└─────────────────┘     └─────────────────┘
        │
        ▼
┌─────────────────┐     ┌─────────────────┐
│      Fact      │────▶│  Individual     │
└─────────────────┘     └─────────────────┘
```

### 3.2 图谱模型

```
┌──────────┐    HAS_PROPERTY    ┌──────────┐
│ Entity A │───────────────────▶│ Entity B │
└──────────┘                    └──────────┘
      │                              │
      │ INSTANCE_OF                  │ INSTANCE_OF
      ▼                              ▼
┌──────────┐                    ┌──────────┐
│  Class   │◀───SUB_CLASS_OF───│  Class   │
└──────────┘                    └──────────┘
```

### 3.3 置信度模型

| 级别 | 值域 | 说明 |
|------|------|------|
| CONFIRMED | 0.8-1.0 | 经证实的事实 |
| ASSUMED | 0.5-0.8 | 合理推断 |
| SPECULATIVE | 0.2-0.5 | 猜测假设 |
| UNKNOWN | 0.0-0.2 | 未知/无据 |

---

## 4. 非功能需求

### 4.1 性能

| 指标 | 目标 |
|------|------|
| API响应时间 | < 200ms (P99) |
| 推理吞吐量 | > 1000 facts/s |
| 图查询响应 | < 500ms (P99) |
| 并发支持 | > 100 users |

### 4.2 可用性

| 指标 | 目标 |
|------|------|
| 服务可用性 | 99.9% |
| 故障恢复 | < 5 min |
| 数据备份 | 每日增量，每周全量 |

### 4.3 安全

| 需求 | 描述 |
|------|------|
| 认证 | OAuth2 / JWT |
| 权限 | RBAC细粒度控制 |
| 审计 | 所有操作日志 |
| 加密 | 传输TLS + 存储AES256 |

---

## 5. 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│  [Web UI] [REST Client] [GraphQL Client]                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│  [Authentication] [Rate Limiting] [Load Balancing]           │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  REST API       │ │  GraphQL API    │ │  Admin API      │
│  - query        │ │  - query        │ │  - ontology     │
│  - reason       │ │  - mutation     │ │  - config       │
│  - explain      │ │  - subscription │ │  - monitoring   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │
│  │ Reasoner     │ │ Ontology     │ │ Graph        │          │
│  │ Service      │ │ Service      │ │ Service      │          │
│  └──────────────┘ └──────────────┘ └──────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Neo4j      │    │  PostgreSQL  │    │   Redis     │
│  (Graph DB)  │    │ (Metadata)   │    │ (Cache)     │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 6. 验收标准

### 6.1 本体管理

- [ ] 能导入标准OWL文件并正确解析类、属性、实例
- [ ] 能导出为OWL/RDF/Turtle格式
- [ ] 版本历史能正确记录每次修改
- [ ] 可视化界面能展示类层级树

### 6.2 推理引擎

- [ ] 前向链推理能正确推导出新结论
- [ ] 后向链推理能从目标反向推导
- [ ] REST API响应时间 < 200ms
- [ ] GraphQL查询能返回完整推理结果

### 6.3 知识图谱

- [ ] 能连接Neo4j并执行Cypher查询
- [ ] 图可视化能展示实体关系
- [ ] 能存储和追溯推理路径

### 6.4 用户交互

- [ ] 置信度能以颜色/图标方式展示
- [ ] 假设能创建、验证、确认/否认
- [ ] 推理过程能完整追溯

---

## 7. 术语表

| 术语 | 定义 |
|------|------|
| 本体 (Ontology) | 领域知识的结构化表示 |
| 推理 (Reasoning) | 基于规则导出新知识的过程 |
| 置信度 (Confidence) | 结论可信程度的量化指标 |
| 事实 (Fact) | 领域中的具体断言 |
| 规则 (Rule) | 推理时使用的条件-结论对 |

---

*文档版本: 2.0*  
*最后更新: 2026-03-19*
