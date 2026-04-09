# Changelog

All notable changes to clawra will be documented in this file.

## [1.2.0] - 2026-03-24

### Added
- **RDF适配器 (rdf_adapter.py)** - 1087行:
  - OWL/RDF标准支持：RDFTriple, RDFTerm, OntologySchema数据模型
  - JSONL到RDF转换：load_jsonl(), 自动类提取
  - RDF序列化：Turtle, JSON-LD格式输出
  - 本体Schema定义：OntologyClassDef, OntologyPropertyDef
  - 置信度传播：source tracking, confidence scoring

- **Neo4j客户端 (neo4j_client.py)** - 936行:
  - Neo4j Python驱动集成（可选无驱动模式）
  - 实体CRUD：create_entity, get_entity, update_entity, delete_entity
  - 关系CRUD：create_relationship, get_relationships, delete_relationship
  - 图查询API：find_neighbors, find_paths, find_shortest_path
  - 推理链追溯：InferencePath, trace_inference
  - 置信度传播算法

- **API服务化 (main.py)** - 1695行:
  - FastAPI框架：完整RESTful端点设计
  - GraphQL支持：Strawberry集成（可选）
  - Swagger/OpenAPI文档
  - API密钥认证、Rate Limiting、IP Blocking
  - Prometheus监控、请求日志、性能优化
  - 全局错误处理、缓存策略

### Added
- **聚量采购（Volume Pooling）领域本体**：新增采购供应链本体第七章
  - 三级聚量分类：全国聚量 / 区域聚量 / 预测性聚量
  - 物料离散率公式：标准化分 = 物料种类数 ÷ 交易总次数
  - 聚量规则表：金额、买家数、频次、标准化分阈值
  - 真实案例数据：IC卡、锂电池、干电池、阻火器、智能水表
  - 聚量节省估算公式、决策流程、关联本体图
- **ontology-clawra v3.6.1**：追加聚量采购领域知识

## [1.0.0] - 2026-03-19

### Changed
- **愿景升级**：从"知识图谱平台"重新定位为"Agent成长框架"
- **架构重构**：新增三大核心模块（Memory-System / Reasoning-Engine / Meta-Cognition）
- **README重写**：全新愿景陈述
- **架构文档**：新增 docs/architecture.md
- **PRD升级**：v2 → v3.0，全新愿景版
- **License**：MIT → Partial Open Source License（部分开源）

### Added
- **三大核心能力**：
  - 学习特性：本体自学习/自更新/自构建
  - 推理能力：逻辑推理 + 因果推理
  - 元认知：置信度自知 + 知识边界识别
- **差异化定位**：明确与Mem0/RAG/知识图谱的区别
- **部分开源协议**：商业应用需授权

### Fixed
- 项目定位不清晰问题
- 缺少愿景驱动问题

## [0.9.0] - 2026-03-16

### Added
- ontology-clawra v3.3
- 供应链领域本体库
- PRD v2

## [0.8.0] - 2026-03-14

### Added
- 初始项目结构
- 领域本体库

---

*format: [version] - [date]*
