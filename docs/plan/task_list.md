# Clawra 开发计划表

## 已完成任务 (Done)

| 任务 | 描述 | 完成时间 |
|------|------|---------|
| 核心推理引擎 | 前向链/后向链推理，置信度传播 | v1.0 |
| 记忆系统 | SemanticMemory(Neo4j) + EpisodicMemory(SQLite) + VectorStore(ChromaDB) | v2.0 |
| Agent 框架 | Orchestrator + MetacognitiveAgent + AuditorAgent | v2.5 |
| 演化层 | UnifiedLogicLayer + MetaLearner + RuleDiscoveryEngine | v3.0 |
| 规则引擎 | SafeMathSandbox + OntologyRule + RuleEngine | v3.0 |
| API 层 | FastAPI RESTful + GraphQL + Swagger | v3.3 |
| 安全模块 | API Key 认证 + 速率限制 + IP 阻止 + 安全头 | v3.4 |
| 性能优化 | LRU 缓存 + 连接池 + 批处理 + 查询优化 | v3.4 |
| 缓存策略 | 两级缓存 + Redis 分布式缓存 + 缓存预热 | v3.5 |
| 错误处理 | 自定义异常体系 + 全局异常处理器 + 错误恢复 | v3.5 |
| ConfigManager 扩展 | 新增 ReasoningConfig/MemoryConfig/EvolutionConfig/PerformanceConfig | v3.6 |
| 零硬编码修复 | 所有模块从 ConfigManager 读取配置 | v3.6 |
| 逐行中文注释 | 7 个核心文件补充行级注释 | v3.6 |
| 裸 except 修复 | memory/base.py 裸 except 改为具体异常类型 | v3.6 |
| API 配置统一 | api/main.py 统一使用 ConfigManager | v3.6 |
| 测试补充 | test_clawra.py + test_errors.py | v3.6 |
| **Phase 1: 核心架构** | KnowledgeGraph 嵌入式引擎 + 三级索引 + 社区检测 | **Done** |
| **Phase 2: 记忆与检索** | UnifiedMemory + GraphRAG检索(Local/Global/Smart Search) | **Done** |
| **Phase 3: Agent编排** | Orchestrator + ToolRegistry(单例+热插拔) + 工作流管理 | **Done** |
| **Phase 4: 企业级特性** | RBAC权限管理 + 审计日志 + 数据血缘 + 配置管理 | **Done** |
| **E2E测试补全** | 7个关键E2E测试文件 + 性能/安全/检索/配置全覆盖 | **Done** |

### Phase 1-4 完成摘要

**Phase 1 - 核心架构 (已完成)**
- 嵌入式知识图谱引擎，支持三元组增删改查
- 三级索引(SPO/PO/OS)实现高效检索
- LRU淘汰机制 + 分页加载 + 内存监控
- 社区检测(Louvain算法) + 批量操作原子性

**Phase 2 - 记忆与检索 (已完成)**
- UnifiedMemory统一记忆管理器
- Neo4j/ChromaDB集成，支持自动降级到内存存储
- GraphRAG检索引擎：Local Search + Global Search + Smart Search
- 置信度加权排序 + RRF融合排序

**Phase 3 - Agent编排 (已完成)**
- Orchestrator工作流编排器
- ToolRegistry工具注册中心（单例模式）
- 工具热插拔：注册/卸载/启用/禁用
- OpenAI格式工具定义生成

**Phase 4 - 企业级特性 (已完成)**
- RBAC权限管理：角色创建/权限分配/继承/循环检测
- 审计日志系统：SQLite存储 + 异步写入
- 数据血缘追踪：来源记录/派生关系/完整链路追溯
- ConfigManager配置管理：环境变量覆盖 + 配置验证

## 进行中任务 (Doing)

| 任务 | 描述 | 进度 |
|------|------|------|
| - | - | - |

## 已完成任务 (本次迭代)

| 任务 | 描述 | 完成时间 |
|------|------|---------|
| 并发缺陷修复 (Fake Async) | Orchestrator 切换 AsyncOpenAI 与异步时间锁，解决请求死锁阻塞 | 2026-04-08 |
| MathSandbox 安全防线 | 编写硬阻断控制防大指数、大乘法漏洞，防止恶意规则 CPU/内存 OOM | 2026-04-08 |
| 异步 GC 钩挂 | Neo4j 的记忆修剪实现纯异步后台运行，打通 0 额外 Latency | 2026-04-08 |
| GraphRAG 拓扑防爆 | 提取图关系强行施加 Top-15 截断，防止超级节点引发 Token 爆炸 | 2026-04-08 |
| Pydantic V2 重构 | 全局移除废弃的 V1 Config，全面应用 ConfigDict 高效执行 | 2026-04-08 |
| Web 与 E2E 演示套件开发 | 全面淘汰旧 Demo，推出基于 Streamlit与终端双向的综合能力应用 | 2026-04-08 |
| 全量测试修复 | 修复所有测试导入问题，330个测试全部通过 | 2026-04-08 |
| 模块导入修复 | 统一所有内部模块使用相对导入，解决循环导入问题 | 2026-04-08 |
| 测试导入统一 | 所有测试文件统一使用 `src.xxx` 格式导入 | 2026-04-08 |
| 性能测试调优 | 调整性能测试超时阈值以适应 CI 环境 | 2026-04-08 |
| 文档更新 | 更新架构文档，添加新模块说明 | 2026-04-08 |
| **Iteration 5: Mem0 硬化** | 解决豆包 Embedding 兼容性与 404 热降级 | v5.0 |
| **Iteration 6: 技能蒸馏** | 建立推理轨迹到 Python 技能的自主进化闭环 | v6.0 |
| **[D] 自主进化验证** | 完成安全审计与动态工具注入的全量测试 | Done |

## 待办任务 (Todo)

| 任务 | 描述 | 优先级 |
|------|------|--------|
| RLHF 集成 | 基于人类反馈的强化学习微调 | P1 |
| 多模态支持 | 图像/表格/PDF 知识抽取 | P2 |
| 分布式推理 | 多节点推理引擎集群 | P2 |
| 实时可视化增强 | 实现 Streaming 推理轨迹与图谱拓扑实时联动 | P2 |
| 知识蒸馏 (跨模型) | 从大参数模型到轻量级本地模型的跨模型推理蒸馏 | P3 |
