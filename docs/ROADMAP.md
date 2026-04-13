# Clawra 项目路线图

> Clawra 的过去、现在与未来

---

## 版本历史

### v1.0 - 核心架构 (2025-12)
- [x] 嵌入式知识图谱引擎（SQLite）
- [x] 三级索引（SPO/PO/OS）
- [x] 前向链/后向链推理
- [x] 置信度传播机制

### v2.0 - 记忆系统 (2026-01)
- [x] Neo4j 适配器
- [x] ChromaDB 向量适配器
- [x] 情节记忆（EpisodicMemory）
- [x] GraphRAG 检索（Local/Global/Smart）

### v3.0 - 进化层 (2026-02)
- [x] UnifiedLogicLayer
- [x] MetaLearner 元学习器
- [x] RuleDiscoveryEngine
- [x] SelfEvaluator 自我评估
- [x] SelfCorrection 自我纠错

### v3.5 - 企业级特性 (2026-03)
- [x] RBAC 权限管理
- [x] 审计日志系统
- [x] 数据血缘追踪
- [x] SafeMath 安全沙盒
- [x] 配置管理（ConfigManager）

### v3.6 - 质量提升 (2026-04)
- [x] 零硬编码修复
- [x] 逐行中文注释
- [x] 全量测试修复（330+ 测试）
- [x] Pydantic V2 重构
- [x] GraphRAG 拓扑防爆

### v4.0 - 智能化增强 (已完成)
- [x] Skill Distiller 技能蒸馏
- [x] UnifiedSkillRegistry 技能库
- [x] BehaviorLearner 行为学习
- [x] Distillation 知识蒸馏
- [x] 本文档体系完善（SDK指南、集成指南、故障排查、测试策略、部署指南、CHANGELOG、ADR）

---

## v4.x - 进化增强路线

### v4.1 - Evolution 全闭环 ⭐ (进行中 2026-04)
- [x] 完整8阶段进化闭环（Perceive → Learn → Reason → Execute → Evaluate → DetectDrift → ReviseRules → UpdateKG）
- [x] 失败反馈路由（推理错误/规则冲突/漂移检测 → MetaLearner）
- [x] Pattern 版本控制 + 历史 + Rollback
- [x] 规则相似度去重（向量化 + merge）
- [ ] 推理失败 → 自动记录 → 回流 MetaLearner 重学（真实集成）
- [ ] 失败案例优先采样学习
- [ ] Evolution Loop 监控 Dashboard

### v4.2 - Skill 可执行性 + Leiden (已完成 2026-04)
- [x] SkillDistiller 可执行性增强（SafeExecutor 沙盒 + execute(params)）
- [x] Leiden 社区检测算法（pip install leidenalg）
- [x] 社区摘要自动生成（LLM + 启发式降级）
- [x] 跨社区推理路径发现

### v4.3 - 测试硬化 (已完成 2026-04)
- [x] 401 passing 测试基线
- [x] EvolutionLoop 20个专项测试
- [x] 性能测试（P50/P95/P99 延迟）
- [ ] 集成测试覆盖率达到 80%

### v4.5 - 贝叶斯置信度校准 (计划 2026-07)
- [ ] 基于历史预测精度的在线校准
- [ ] 置信度校准曲线可视化
- [ ] 校准报告生成
- [ ] 与 SelfEvaluator 集成

---

## v5.0 - 企业级增强路线

### v5.1 - 跨领域迁移 (计划 2026-Q3)
- [ ] 领域相似度计算
- [ ] 跨领域规则迁移
- [ ] 迁移效果评估
- [ ] 迁移案例库

### v5.2 - 主动学习 (计划 2026-Q3)
- [ ] 信息量最大的样本优先学习
- [ ] 不确定性采样策略
- [ ] 主动学习 Dashboard
- [ ] 与 Label Studio 集成

### v5.3 - Action 监控 (计划 2026-Q3)
- [ ] Action 执行指标追踪
- [ ] P95/P99 延迟告警
- [ ] Action 性能优化建议
- [ ] 实时监控面板

### v5.4 - Datalog 推理扩展 (计划 2026-Q4)
- [ ] 支持过滤/聚合/否定
- [ ] Datalog 规则解析器
- [ ] 与现有 Reasoner 集成
- [ ] 性能优化

---

## v6.0 - 多模态与分布式路线

### v6.1 - 多模态支持 (计划 2027-Q1)
- [ ] 图像知识抽取
- [ ] 表格结构化解析
- [ ] PDF 文档解析
- [ ] 多模态本体映射

### v6.2 - 分布式推理 (计划 2027-Q1)
- [ ] 多节点推理引擎集群
- [ ] 图数据分布式存储
- [ ] 负载均衡策略
- [ ] 故障转移机制

### v6.3 - RLHF 集成 (计划 2027-Q2)
- [ ] 人类反馈数据收集
- [ ] RLHF 微调管道
- [ ] 强化学习策略优化
- [ ] 与 Ray 集成

---

## 长期愿景

### 7.0 - 通用认知引擎 (计划 2027+)
- [ ] 跨领域通用推理
- [ ] 自主架构演进
- [ ] 认知架构可视化
- [ ] 自我解释机制

---

## 已废弃/暂停的功能

| 功能 | 原因 | 替代方案 |
|-----|------|---------|
| Redis 缓存层 | 架构过于复杂 | 直接使用 Neo4j 内置缓存 |
| RQL 查询语言 | 使用 Cypher 替代 | Neo4j 原生查询 |
| 自定义 DSL | 学习成本过高 | Pythonic API |

---

## 里程碑发布计划

```
2026-04  v4.1  Evolution 全闭环 ✅ 进行中
2026-05  v4.5  贝叶斯置信度校准
2026-09  v5.0  企业级增强
2027-01  v6.0  多模态 + 分布式
2027+    v7.0  通用认知引擎
```

---

**最后更新**: 2026-04-13
