# 产品需求文档 (PRD v2.1)

## 垂直领域可信AI推理引擎平台

**版本**: 2.1 (生产级增强版)  
**状态**: 规划  
**日期**: 2026-03-23  
**基于**: ontology-clawra v3.5

---

## 1. 产品概述

### 1.1 产品定位

企业级垂直领域可信AI推理引擎平台，基于本体论(Ontology)方法解决AI幻觉问题。通过结构化知识表示、规则推理、置信度追踪和自动学习机制，为供应链、医疗、金融、制造等垂直领域提供可解释、可追溯的智能决策支持。

### 1.2 核心价值

| 价值点 | 说明 |
|--------|------|
| **可信推理** | 每条建议都有推理依据，拒绝黑箱 |
| **置信度感知** | CONFIRMED/ASSUMED/SPECULATIVE/UNKNOWN 四级标注 |
| **可追溯** | 完整记录推理过程，支持回溯和审计 |
| **自动学习** | 用户确认后自动抽取到本体，持续进化 |
| **领域适配** | 预置54+领域本体，支持快速定制 |

### 1.3 目标用户

- 企业知识工程师
- 领域专家
- AI产品经理
- 供应链/采购专业人员
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

### 2.3 自动学习模块 (v3.5新增)

#### 2.3.1 自动抽取引擎

| 功能 | 优先级 | 描述 |
|------|--------|------|
| 用户确认触发 | P0 | 用户确认推理后自动抽取 |
| 实体识别 | P0 | 识别可抽取对象（Person/Concept/Law/Rule） |
| 关系识别 | P0 | 识别实体间关系 |
| 去重检查 | P0 | 名称匹配+相似度检查 |
| 增量更新 | P0 | 避免覆盖式写入 |

**自动抽取流程**:
```
用户确认推理结果
        │
        ▼
┌─────────────────────────────┐
│ 1. 识别可抽取内容           │
│    - 新概念 (Concept)       │
│    - 新规律 (Law)           │
│    - 新规则 (Rule)          │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 2. 置信度升级              │
│    ASSUMED → CONFIRMED     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 3. 增量写入本体            │
│    - 更新 graph.jsonl      │
│    - 记录 extraction_log   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 4. 反馈用户                │
│    "已学习到本体：xxx"     │
└─────────────────────────────┘
```

#### 2.3.2 智能触发器

| 触发事件 | 动作 | 描述 |
|----------|------|------|
| `user_confirms_reasoning` | extract_to_ontology | 推理确认后抽取 |
| `entity_mentioned_3_times` | create_index | 高频实体识别 |
| `ontology_lookup_failed` | suggest_supplement | 本体缺失建议 |
| `user_correction` | update_entity | 错误纠正更新 |

**接口设计**:
```yaml
POST /api/v1/auto-learn/trigger
  - body: { event: string, data: object }
  - response: { action: string, result: object }

POST /api/v1/auto-learn/extract
  - body: { source: string, content: object, confidence_upgrade: boolean }
  - response: { extracted: Entity[], updated: Entity[] }
```

#### 2.3.3 置信度追踪

| 功能 | 优先级 | 描述 |
|------|--------|------|
| 置信度历史 | P0 | 记录每次变更 |
| 自动升级 | P0 | ASSUMED → CONFIRMED |
| 趋势可视化 | P1 | 置信度变化图表 |
| 批量调整 | P2 | 批量更新置信度 |

---

### 2.4 知识图谱模块

#### 2.4.1 Neo4j图数据库集成

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

#### 2.4.2 图可视化查询

| 功能 | 优先级 | 描述 |
|------|--------|------|
| Cypher查询 | P0 | 执行Cypher语句 |
| 语义查询 | P1 | 本体语义查询 |
| 路径查找 | P1 | 最短/全部路径 |
| 子图提取 | P2 | 局部图导出 |

#### 2.4.3 实体关系管理

| 功能 | 优先级 | 描述 |
|------|--------|------|
| 实体搜索 | P0 | 多条件搜索 |
| 关系探索 | P0 | 扩展邻居 |
| 批量操作 | P1 | 批量导入/导出 |
| 冲突检测 | P2 | 重复实体识别 |

---

### 2.5 用户交互模块

#### 2.5.1 置信度标注展示

| 功能 | 描述 |
|------|------|
| 颜色编码 | CONFIRMED=绿, ASSUMED=黄, SPECULATIVE=橙, UNKNOWN=灰 |
| 图标标注 | 置信度徽章 |
| 详情面板 | 证据来源、计算方法 |
| 趋势图 | 历史置信度变化 |

#### 2.5.2 假设声明与确认流程

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

#### 2.5.3 推理过程追溯

| 功能 | 描述 |
|------|------|
| 步骤时间线 | 推理过程可视化 |
| 中间结果 | 每步产出查看 |
| 推理回放 | 重现推理过程 |
| 报告导出 | PDF/HTML报告 |

---

### 2.6 供应链领域场景 (v3.5扩展)

#### 2.6.1 供应商风险评估

| 功能 | 描述 |
|------|------|
| 风险评分 | 综合评分 (0-100) |
| 风险因子 | OTD、不良率、供应集中度等 |
| 应对建议 | 基于风险等级的改善建议 |

**接口**:
```yaml
POST /api/v1/supplier/risk-evaluation
  - body: { supplier_id: string, metrics: object }
  - response: { risk_score: number, risk_level: string, factors: [], suggestions: [] }
```

#### 2.6.2 采购价格分析

| 功能 | 描述 |
|------|------|
| 价格竞争力 | 与市场均价对比 |
| 趋势分析 | 近N个月价格走势 |
| 议价空间 | 基于采购量的建议 |

#### 2.6.3 合同条款审查

| 功能 | 描述 |
|------|------|
| 风险点识别 | 预付款、交付周期、质保期等 |
| 风险等级 | 高/中/低风险标注 |
| 修改建议 | 具体协商建议 |

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

### 3.2 自动学习实体

```
┌─────────────────┐     ┌─────────────────┐
│  ExtractionLog │────▶│     Entity      │
└─────────────────┘     └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ConfidenceTrack │────▶│   EventTrigger  │
└─────────────────┘     └─────────────────┘
```

### 3.3 图谱模型

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

### 3.4 置信度模型

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
| 自动学习延迟 | < 500ms (用户确认后) |
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
│  - reason       │ │  - mutation     │ │  - auto-learn   │
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
│  ┌──────────────┐ ┌──────────────┐                           │
│  │ AutoLearn    │ │ Supplier     │                           │
│  │ Service      │ │ Service      │                           │
│  └──────────────┘ └──────────────┘                           │
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

### 6.3 自动学习

- [ ] 用户确认推理后自动抽取新实体
- [ ] 高频实体（3次）自动识别
- [ ] 置信度自动升级 (ASSUMED → CONFIRMED)
- [ ] 增量更新不覆盖已有数据
- [ ] 推理失败时主动建议补充本体

### 6.4 知识图谱

- [ ] 能连接Neo4j并执行Cypher查询
- [ ] 图可视化能展示实体关系
- [ ] 能存储和追溯推理路径

### 6.5 用户交互

- [ ] 置信度能以颜色/图标方式展示
- [ ] 假设能创建、验证、确认/否认
- [ ] 推理过程能完整追溯

### 6.6 供应链场景

- [ ] 供应商风险评估能返回综合评分
- [ ] 采购价格分析能给出议价建议
- [ ] 合同审查能识别风险点

---

## 7. 术语表

| 术语 | 定义 |
|------|------|
| 本体 (Ontology) | 领域知识的结构化表示 |
| 推理 (Reasoning) | 基于规则导出新知识的过程 |
| 置信度 (Confidence) | 结论可信程度的量化指标 |
| 事实 (Fact) | 领域中的具体断言 |
| 规则 (Rule) | 推理时使用的条件-结论对 |
| 自动学习 (Auto-Learn) | 用户确认后自动抽取到本体的机制 |
| 智能触发 (Smart Trigger) | 特定事件自动触发的动作 |

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 2.0 | 2026-03-19 | 初始生产级版本 |
| 2.1 | 2026-03-23 | 新增自动学习模块、供应链场景 |

---

*文档版本: 2.1*  
*最后更新: 2026-03-23*
