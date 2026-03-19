# Changelog

All notable changes to ontology-platform will be documented in this file.

## [1.1.0] - 2026-03-19

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
