# ontology-platform 产品需求文档 (V2.0 生产级)

**文档版本**: V2.0  
**创建日期**: 2026-03-16  
**最后更新**: 2026-03-16  
**状态**: 规划中  
**基于**: ontology-clawra v3.3

---

## 一、产品概述

### 1.1 产品背景

ontology-platform 是基于 ontology-clawra v3.3 构建的垂直领域可信AI推理引擎平台。产品核心价值在于：

- **消除AI幻觉**: 每步推理有据可查
- **可解释推理**: 透明推理过程，支持追溯
- **领域知识库**: 燃气工程、采购供应链、安全生产、金融风控
- **企业级可靠**: 可审计、可追溯、可扩展
- **主动学习**: 用户确认后自动抽取知识，持续进化

### 1.2 产品定位

| 维度 | 定位 |
|------|------|
| 目标用户 | 企业决策者、领域专家、开发者 |
| 产品形态 | Web平台 + API服务 + CLI工具 |
| 部署方式 | 私有化部署 / SaaS |
| 核心能力 | 本体管理 + 推理引擎 + 知识图谱 + 主动学习 |

### 1.3 核心功能架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Web界面   │  │ REST API │  │GraphQL   │  │ CLI工具  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      推理服务层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 推理引擎  │  │置信度评估│  │可解释输出│  │链式推理 │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │主动学习   │  │智能触发  │  │假设确认  │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
├─────────────────────────────────────────────────────────────┤
│                      本体管理层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │OWL/RDF   │  │版本管理  │  │可视化编辑│  │校验合并 │  │
│  │导入导出  │  │          │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      知识图谱层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Neo4j   │  │ 图查询   │  │可视化    │  │统计分析 │  │
│  │ 图数据库 │  │          │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      数据存储层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 本体文件  │  │图数据库  │  │推理日志  │  │抽取日志  │  │
│  │ (YAML)  │  │ (Neo4j)  │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、用户故事

### 2.1 主要用户角色

| 角色 | 职责 | 痛点 |
|------|------|------|
| **领域专家** | 构建和维护领域本体 | 缺乏可视化编辑工具，本体版本混乱 |
| **业务决策者** | 获取推理结论辅助决策 | 不信任AI结论，无法追溯推理过程 |
| **开发者** | 集成推理能力到业务系统 | API能力不足，缺乏灵活查询接口 |
| **平台管理员** | 管理平台运维和权限 | 缺乏审计和权限控制 |

### 2.2 用户故事地图

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                用户故事地图（User Story Map）                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   阶段 →      【发现/探索】              【评估/试用】              【正式使用】        │
│   角色        ↓                           ↓                        ↓                │
│   ──────────────────────────────────────────────────────────────────────────────    │
│                                                                                      │
│  领域专家   │ ① 了解产品能力            ⑤ 查看Demo演示            ⑨ 创建第一个本体    │
│            │ ② 阅读产品文档            ⑥ 试用在线演示            ⑩ 导入OWL文件       │
│            │ ③ 对比竞品差异            ⑦ 配置示例本体             ⑪ 编辑实体关系       │
│            │ ④ 评估技术适配性          ⑧ 体验API接口             ⑫ 查看版本历史       │
│            │                            ⑨                        ⑬ 导出本体          │
│            │                                                      ⑭ 抽取新实体        │
│            │                                                      ⑮ 升级置信度        │
│   ──────────────────────────────────────────────────────────────────────────────    │
│                                                                                      │
│ 业务决策者 │ ① 了解产品能力            ⑤ 查看Demo演示            ⑨ 执行推理查询       │
│            │ ② 关注ROI和数据安全       ⑥ 试用在线演示            ⑩ 查看置信度        │
│            │ ③ 评估供应商风险          ⑦ 体验推理可解释性        ⑪ 追溯推理过程       │
│            │ ④ 审批采购决策            ⑧                        ⑫ 确认假设          │
│            │                                                      ⑬ 导出推理报告       │
│            │                                                      ⑭ 审阅抽取建议       │
│   ──────────────────────────────────────────────────────────────────────────────    │
│                                                                                      │
│  开发者    │ ① 阅读API文档             ⑤ 申请API Key             ⑨ 集成REST API       │
│            │ ② 查看技术架构            ⑥ 试用GraphQL             ⑩ 集成GraphQL        │
│            │ ③ 评估集成复杂度          ⑦                        ⑪ 批量推理处理       │
│            │ ④                        ⑧                        ⑫ 自定义触发器       │
│            │                                                      ⑬ 集成到业务系统     │
│   ──────────────────────────────────────────────────────────────────────────────    │
│                                                                                      │
│  平台管理员 │ ① 评估安全合规           ⑤ 配置租户               ⑨ 管理用户权限        │
│            │ ② 审查审计日志           ⑥ 设置API配额             ⑩ 查看操作日志        │
│            │ ③ 评估运维成本           ⑦                        ⑪ 备份恢复管理        │
│            │ ④                        ⑧                        ⑫ 监控系统配置        │
│            │                                                      ⑬ 性能调优          │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘

图例说明：
①-④：前期活动（探索/评估阶段）
⑤-⑧：中期活动（试用/验证阶段）  
⑨-⑮：后期活动（正式使用/深化阶段）

用户故事优先级：
┌────────────────────────────────────────────────────────────────────────────────────┐
│  高优先级（必须满足）                                                              │
├────────────────────────────────────────────────────────────────────────────────────┤
│  领域专家：⑨ 创建第一个本体  ⑩ 导入OWL文件  ⑪ 编辑实体关系  ⑫ 导出本体          │
│  业务决策者：⑨ 执行推理查询  ⑩ 查看置信度  ⑪ 追溯推理过程  ⑬ 导出推理报告       │
│  开发者：⑨ 集成REST API  ⑩ 集成GraphQL  ⑪ 批量推理处理                         │
│  平台管理员：⑨ 管理用户权限  ⑩ 查看操作日志  ⑪ 备份恢复管理                      │
├────────────────────────────────────────────────────────────────────────────────────┤
│  中优先级（提升体验）                                                              │
├────────────────────────────────────────────────────────────────────────────────────┤
│  领域专家：⑬ 查看版本历史  ⑭ 抽取新实体  ⑮ 升级置信度                            │
│  业务决策者：⑫ 确认假设  ⑭ 审阅抽取建议                                         │
│  开发者：⑫ 自定义触发器  ⑬ 集成到业务系统                                        │
│  平台管理员：⑫ 监控系统配置  ⑬ 性能调优                                          │
├────────────────────────────────────────────────────────────────────────────────────┤
│  低优先级（增值功能）                                                              │
├────────────────────────────────────────────────────────────────────────────────────┤
│  领域专家：①-⑧ 前期所有活动                                                      │
│  业务决策者：①-⑧ 前期所有活动                                                    │
│  开发者：①-⑧ 前期所有活动                                                        │
│  平台管理员：①-⑧ 前期所有活动                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 用户故事列表

#### 故事1: 领域专家维护本体
> 作为领域专家，我需要导入现有的OWL本体文件，以便利用已有的知识积累。

#### 故事2: 本体版本管理
> 作为领域专家，我需要查看本体版本历史并回滚到旧版本，以便在出错时快速恢复。

#### 故事3: 推理结果可信度
> 作为业务决策者，我需要看到每个推理结论的置信度标注，以便判断结论是否可靠。

#### 故事4: 推理过程追溯
> 作为业务决策者，我需要追溯每步推理的依据，以便向领导解释决策来源。

#### 故事5: 假设确认流程
> 作为系统，我需要在推理依赖关键假设时暂停，向用户确认假设是否成立，再输出最终结论。

#### 故事6: 图谱可视化探索
> 作为领域专家，我需要通过可视化方式探索知识图谱，以便发现实体间隐藏的关系。

#### 故事7: 灵活查询本体
> 作为开发者，我需要通过GraphQL灵活查询本体数据，以便定制化获取所需信息。

#### 故事8: 导出推理报告
> 作为业务决策者，我需要导出推理报告（PDF/Markdown），以便存档和汇报。

#### 故事9: 主动学习抽取
> 作为领域专家，我需要将正确的推理结果一键抽取到本体，以便丰富知识库。（v3.3新增）

#### 故事10: 置信度升级
> 作为领域专家，我需要确认推理结果正确后自动提升置信度，以便提高后续推理准确性。（v3.3新增）

#### 故事11: 推理失败建议
> 作为系统，我需要在本体查无数据时主动提示用户补充，而不是直接返回未知。（v3.3新增）

---

## 三、功能需求

### 3.1 本体管理模块

#### 3.1.1 OWL/RDF本体导入导出

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| ONT-001 | 支持OWL格式本体文件导入 | P0 | 导入标准OWL文件不报错 |
| ONT-002 | 支持RDF/XML格式本体导入 | P0 | 导入RDF文件正确解析 |
| ONT-003 | 支持导出为OWL格式 | P0 | 导出后可重新导入且数据一致 |
| ONT-004 | 支持导出为RDF格式 | P0 | 导出后语义保持一致 |
| ONT-005 | 支持YAML/JSON格式互转 | P0 | 与现有系统兼容 |

#### 3.1.2 本体版本管理

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| ONT-006 | 本体版本自动记录 | P0 | 每次修改自动创建版本 |
| ONT-007 | 版本历史查看 | P0 | 查看所有历史版本列表 |
| ONT-008 | 版本回滚 | P0 | 回滚到指定版本 |
| ONT-009 | 版本对比 | P1 | 显示两个版本的差异 |
| ONT-010 | 版本分支 | P1 | 支持创建分支并行开发 |

#### 3.1.3 本体可视化编辑

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| ONT-011 | 实体关系图可视化 | P0 | Web界面展示本体图谱 |
| ONT-012 | 实体CRUD操作 | P0 | 可视化创建/编辑/删除实体 |
| ONT-013 | 关系连线操作 | P0 | 可视化创建实体间关系 |
| ONT-014 | 本体树形结构展示 | P1 | 层级视图展示分类关系 |
| ONT-015 | 批量导入 | P1 | 支持CSV/Excel批量导入实体 |

#### 3.1.4 本体校验与合并

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| ONT-016 | OWL完整性检查 | P0 | 检查必需属性是否完备 |
| ONT-017 | 一致性验证 | P0 | 检测逻辑矛盾 |
| ONT-018 | 多源本体合并 | P1 | 合并两个本体并处理冲突 |
| ONT-019 | 重复实体检测 | P1 | 识别并标记重复实体 |

#### 3.1.5 本体抽取（v3.3新增）

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| ONT-020 | 交互式抽取 | P0 | 从文本中识别实体并抽取 |
| ONT-021 | 实体去重检查 | P0 | 抽取前检查是否已存在 |
| ONT-022 | 抽取预览确认 | P0 | 抽取前展示给用户确认 |
| ONT-023 | 抽取日志记录 | P0 | 记录所有抽取操作到日志 |
| ONT-024 | 抽取来源追踪 | P1 | 记录每个实体的数据来源 |

### 3.2 推理引擎服务

#### 3.2.1 RESTful API设计

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| REA-001 | 推理查询接口 | P0 | POST /api/v1/reason 返回推理结果 |
| REA-002 | 置信度获取 | P0 | 返回置信度标注 |
| REA-003 | 推理链获取 | P0 | 返回完整推理链路 |
| REA-004 | 本体查询接口 | P0 | GET /api/v1/ontology 查询本体 |
| REA-005 | 批量推理 | P1 | 批量提交多个推理任务 |

#### 3.2.2 GraphQL查询接口

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| REA-006 | GraphQL端点 | P0 | POST /graphql 支持GraphQL查询 |
| REA-007 | 实体查询 | P0 | query { entities {...} } |
| REA-008 | 关系查询 | P0 | query { relations {...} } |
| REA-009 | 推理结果查询 | P0 | query { reasoning {...} } |
| REA-010 | 订阅推理事件 | P1 | 支持实时推理进度推送 |

#### 3.2.3 推理结果可解释性输出

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| REA-011 | 推理依据展示 | P0 | 每步展示匹配规则ID和内容 |
| REA-012 | 置信度标注 | P0 | CONFIRMED/ASSUMED/SPECULATIVE/UNKNOWN |
| REA-013 | 假设声明 | P0 | 明确标注哪些是假设 |
| REA-014 | 推理步骤可视化 | P0 | 图形化展示推理链路 |
| REA-015 | 推理报告生成 | P1 | 生成PDF/Markdown推理报告 |

#### 3.2.4 高级推理能力

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| REA-016 | 链式推理 | P1 | 支持多步推理链 |
| REA-017 | 反向推理 | P1 | 从结论反向推导条件 |
| REA-018 | 推理缓存 | P1 | 相同条件推理结果缓存 |
| REA-019 | 并行推理 | P1 | 多推理任务并行处理 |

#### 3.2.5 主动学习能力（v3.3核心新增）

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| REA-020 | 抽取触发器 | P0 | 用户说"写入本体"时触发抽取 |
| REA-021 | 置信度升级 | P0 | 用户确认推理正确后升级置信度 |
| REA-022 | 高频实体识别 | P1 | 实体出现3次以上自动识别建议 |
| REA-023 | 推理失败建议 | P0 | 本体查无数据时主动提示补充 |
| REA-024 | 用户纠正记录 | P0 | 记录用户纠正用于后续优化 |

#### 3.2.6 智能触发机制（v3.3新增）

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| REA-025 | 自动学习开关 | P0 | 用户可开启/关闭自动学习 |
| REA-026 | 写入确认 | P0 | 每次写入前必须用户确认 |
| REA-027 | 触发条件配置 | P1 | 支持配置自动触发条件 |
| REA-028 | 隐私保护 | P0 | 不自动读取敏感文件 |

### 3.3 知识图谱模块

#### 3.3.1 Neo4j图数据库集成

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| KG-001 | Neo4j连接 | P0 | 成功连接Neo4j并执行查询 |
| KG-002 | 实体同步 | P0 | 本体实体同步到Neo4j |
| KG-003 | 关系同步 | P0 | 本体关系同步到Neo4j |
| KG-004 | 增量更新 | P0 | 实时同步增量变化 |
| KG-005 | 数据备份 | P1 | 图数据库定期备份 |

#### 3.3.2 图可视化查询

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| KG-006 | 图谱可视化 | P0 | Web界面展示知识图谱 |
| KG-007 | 节点搜索 | P0 | 按名称/类型搜索实体 |
| KG-008 | 关系探索 | P0 | 点击节点显示关联关系 |
| KG-009 | 路径查询 | P1 | 查询两实体间最短路径 |
| KG-010 | 子图导出 | P1 | 导出选中子图 |

#### 3.3.3 实体关系管理

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| KG-011 | 实体CRUD | P0 | 通过API管理实体 |
| KG-012 | 关系CRUD | P0 | 通过API管理关系 |
| KG-013 | 批量操作 | P1 | 批量创建/更新/删除 |
| KG-014 | 导入导出 | P1 | CSV/JSON格式导入导出 |

#### 3.3.4 图谱统计分析

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| KG-015 | 实体统计 | P1 | 实体类型分布、数量统计 |
| KG-016 | 关系统计 | P1 | 关系类型分布、密度分析 |
| KG-017 | 图谱健康度 | P1 | 孤立节点、环路检测 |

### 3.4 用户交互

#### 3.4.1 置信度标注展示

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| UI-001 | 置信度标签 | P0 | 清晰展示四种置信度 |
| UI-002 | 置信度筛选 | P0 | 按置信度筛选结论 |
| UI-003 | 置信度颜色 | P0 | 绿/黄/红/灰颜色区分 |
| UI-004 | 置信度说明 | P0 | 悬停显示置信度含义 |

#### 3.4.2 假设声明与确认流程

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| UI-005 | 假设高亮 | P0 | 明确标识假设内容 |
| UI-006 | 确认弹窗 | P0 | 关键假设弹出确认 |
| UI-007 | 假设库 | P1 | 管理常用假设模板 |
| UI-008 | 假设历史 | P1 | 查看历史假设确认记录 |

#### 3.4.3 推理过程追溯

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| UI-009 | 推理链展示 | P0 | 可视化展示推理步骤 |
| UI-010 | 步骤详情 | P0 | 点击查看每步详情 |
| UI-011 | 规则来源 | P0 | 展示匹配的规则ID和内容 |
| UI-012 | 回溯导航 | P0 | 支持跳转到任意步骤 |
| UI-013 | 导出推理链 | P1 | 导出推理链为图片/PDF |

#### 3.4.4 主动学习交互（v3.3新增）

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| UI-014 | 抽取确认 | P0 | 写入本体前展示预览 |
| UI-015 | 抽取成功反馈 | P0 | 写入后反馈用户 |
| UI-016 | 置信度升级确认 | P0 | 升级前确认 |
| UI-017 | 失败建议展示 | P0 | 查无数据时提示补充 |

---

## 四、非功能需求

### 4.1 性能需求

| 指标 | 目标值 | 说明 |
|------|--------|------|
| API响应时间 | < 500ms | 推理API P99响应时间 |
| 图查询响应 | < 500ms | 复杂查询P99响应时间 |
| 并发支持 | ≥ 100用户 | 正常负载 |
| 本体加载 | < 5秒 | 10万实体加载时间 |
| 图谱渲染 | < 2秒 | 千级节点渲染时间 |
| 抽取响应 | < 1秒 | 实体抽取响应时间 |

### 4.2 可用性需求

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 系统可用性 | ≥ 99.5% | 月度可用性 |
| 故障恢复 | < 30分钟 | MTTR |
| 数据备份 | 每日 | 增量备份 |
| 监控告警 | 7x24 | 关键指标监控 |

### 4.3 安全需求

| 指标 | 要求 |
|------|------|
| 认证 | 支持API Key / OAuth2 |
| 权限 | RBAC角色权限控制 |
| 审计 | 记录所有操作日志 |
| 加密 | 敏感数据传输TLS加密 |
| 隐私 | 自动学习默认禁用，用户授权开启 |

### 4.4 可扩展性需求

| 指标 | 要求 |
|------|------|
| 水平扩展 | 支持K8s自动扩缩容 |
| 存储扩展 | 支持分库分表 |
| 插件化 | 支持自定义推理引擎 |
| 触发器扩展 | 支持自定义自动学习触发器 |

---

## 五、技术架构

### 5.1 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | React + Ant Design + D3.js |
| 后端 | Python FastAPI + GraphQL (Strawberry) |
| 图数据库 | Neo4j |
| 本体存储 | RDFLib / OWL-RL |
| 消息队列 | Redis (缓存) |
| 部署 | Docker + K8s |

### 5.2 API设计

#### RESTful API

**本体管理 API**

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/ontologies` | 获取本体列表 | - | `OntologyListResponse` |
| POST | `/api/v1/ontologies` | 创建本体 | `CreateOntologyRequest` | `Ontology` |
| GET | `/api/v1/ontologies/{id}` | 获取本体详情 | - | `Ontology` |
| PUT | `/api/v1/ontologies/{id}` | 更新本体 | `UpdateOntologyRequest` | `Ontology` |
| DELETE | `/api/v1/ontologies/{id}` | 删除本体 | - | `DeleteResponse` |
| POST | `/api/v1/ontologies/import` | 导入本体(OWL/RDF/YAML) | `ImportOntologyRequest` | `Ontology` |
| GET | `/api/v1/ontologies/{id}/export` | 导出本体 | `?format=owl|rdf|yaml|json` | `File` |
| GET | `/api/v1/ontologies/{id}/versions` | 获取版本历史 | - | `VersionListResponse` |
| POST | `/api/v1/ontologies/{id}/rollback` | 回滚到指定版本 | `RollbackRequest` | `Ontology` |

**实体管理 API**

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/entities` | 获取实体列表 | `?type=&limit=&offset=` | `EntityListResponse` |
| POST | `/api/v1/entities` | 创建实体 | `CreateEntityRequest` | `Entity` |
| GET | `/api/v1/entities/{id}` | 获取实体详情 | - | `Entity` |
| PUT | `/api/v1/entities/{id}` | 更新实体 | `UpdateEntityRequest` | `Entity` |
| DELETE | `/api/v1/entities/{id}` | 删除实体 | - | `DeleteResponse` |
| PUT | `/api/v1/entities/{id}/confidence` | 升级置信度 | `ConfidenceUpdateRequest` | `Entity` |
| GET | `/api/v1/entities/{id}/history` | 获取实体变更历史 | - | `EntityHistoryResponse` |

**关系管理 API**

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/relations` | 获取关系列表 | `?sourceId=&targetId=&type=` | `RelationListResponse` |
| POST | `/api/v1/relations` | 创建关系 | `CreateRelationRequest` | `Relation` |
| GET | `/api/v1/relations/{id}` | 获取关系详情 | - | `Relation` |
| DELETE | `/api/v1/relations/{id}` | 删除关系 | - | `DeleteResponse` |

**推理服务 API**

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/v1/reason` | 执行推理 | `ReasonRequest` | `ReasoningResult` |
| GET | `/api/v1/reason/{id}` | 获取推理结果 | - | `ReasoningResult` |
| GET | `/api/v1/reason/{id}/chain` | 获取推理链 | - | `ReasoningChainResponse` |
| POST | `/api/v1/reason/chain` | 链式推理 | `ChainReasonRequest` | `ReasoningResult` |
| GET | `/api/v1/reason/{id}/suggest` | 获取补充建议 | - | `SuggestionResponse` |
| POST | `/api/v1/reason/{id}/confirm` | 确认假设 | `ConfirmHypothesisRequest` | `ReasoningResult` |
| POST | `/api/v1/reason/batch` | 批量推理 | `BatchReasonRequest` | `BatchReasonResponse` |

**知识图谱 API**

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/graph` | 图谱查询 | `?type=&name=&limit=` | `GraphResponse` |
| GET | `/api/v1/graph/stats` | 图谱统计 | - | `GraphStatsResponse` |
| POST | `/api/v1/graph/path` | 路径查询 | `PathQueryRequest` | `PathResponse` |
| POST | `/api/v1/graph/subgraph` | 子图查询 | `SubgraphRequest` | `SubgraphResponse` |

**抽取与主动学习 API (v3.3新增)**

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/v1/extract` | 抽取实体到本体 | `ExtractRequest` | `ExtractionResult` |
| POST | `/api/v1/extract/preview` | 预览抽取结果 | `ExtractRequest` | `ExtractionResult` |
| POST | `/api/v1/extract/confirm` | 确认抽取 | `ConfirmExtractionRequest` | `ConfirmResponse` |
| GET | `/api/v1/extract/logs` | 抽取日志 | `?limit=&offset=` | `ExtractionLogResponse` |

**用户与权限 API**

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/v1/auth/login` | 用户登录 | `LoginRequest` | `TokenResponse` |
| POST | `/api/v1/auth/refresh` | 刷新Token | - | `TokenResponse` |
| GET | `/api/v1/users/me` | 当前用户信息 | - | `User` |
| GET | `/api/v1/users` | 用户列表 | - | `UserListResponse` |

#### API 请求/响应格式

```python
# 通用响应包装
class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[ErrorDetail] = None

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None

# 本体相关
class CreateOntologyRequest(BaseModel):
    name: str
    description: Optional[str] = None
    format: Literal["owl", "rdf", "yaml", "json"]
    content: str

class Ontology(BaseModel):
    id: UUID
    name: str
    version: str
    format: str
    entity_count: int
    relation_count: int
    created_by: str
    created_at: datetime
    updated_at: datetime

# 实体相关
class CreateEntityRequest(BaseModel):
    name: str
    type: str
    properties: Optional[dict] = None
    confidence: Optional[ConfidenceLevel] = ConfidenceLevel.UNKNOWN

class Entity(BaseModel):
    id: UUID
    ontology_id: UUID
    name: str
    type: str
    properties: dict
    confidence: ConfidenceLevel
    source: Optional[str] = None  # v3.3新增
    created_at: datetime
    updated_at: datetime

# 推理相关
class ReasonRequest(BaseModel):
    query: str
    ontology_id: Optional[UUID] = None
    context: Optional[dict] = None
    options: Optional[ReasonOptions] = None

class ReasonOptions(BaseModel):
    include_chain: bool = True
    include_suggestions: bool = True  # v3.3新增
    max_steps: int = 10

class ReasoningResult(BaseModel):
    id: UUID
    query: str
    final_conclusion: str
    confidence: ConfidenceLevel
    steps: List[ReasoningStep]
    suggestions: Optional[List[Suggestion]] = None  # v3.3新增
    execution_time_ms: int
    timestamp: datetime

class ReasoningStep(BaseModel):
    step: int
    input: str
    rule_id: Optional[UUID]
    rule_content: Optional[str]
    conclusion: str
    confidence: ConfidenceLevel
    is_assumption: bool = False  # v3.3新增
    needs_confirmation: bool = False  # v3.3新增
    confirmed_by_user: Optional[bool] = None  # v3.3新增

class Suggestion(BaseModel):  # v3.3新增
    type: str  # "missing_entity", "missing_relation"
    message: str
    related_entities: List[str] = []

# 抽取相关 (v3.3新增)
class ExtractRequest(BaseModel):
    text: str
    ontology_id: UUID
    preview: bool = False

class ExtractionResult(BaseModel):
    entities: List[Entity]
    relations: List[Relation]
    duplicates: List[Entity] = []
    preview: bool

class ConfirmExtractionRequest(BaseModel):
    entity_ids: List[UUID]
    relation_ids: List[UUID]
```

#### HTTP 状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 422 | 业务逻辑错误 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

#### 错误码

| 错误码 | 描述 |
|--------|------|
| ONTOLOGY_NOT_FOUND | 本体不存在 |
| ENTITY_NOT_FOUND | 实体不存在 |
| ONTOLOGY_PARSE_ERROR | 本体解析失败 |
| REASONING_FAILED | 推理失败 |
| EXTRACTION_FAILED | 抽取失败 |
| VALIDATION_ERROR | 校验失败 |
| VERSION_CONFLICT | 版本冲突 |

#### GraphQL Schema (核心)

```graphql
# ============================================
# Scalars
# ============================================

scalar DateTime
scalar JSON

# ============================================
# Enums
# ============================================

enum Confidence {
  CONFIRMED
  ASSUMED
  SPECULATIVE
  UNKNOWN
}

enum OntologyFormat {
  OWL
  RDF
  YAML
  JSON
}

enum ExtractionStatus {
  PENDING
  CONFIRMED
  CANCELLED
}

# ============================================
# Input Types
# ============================================

input EntityInput {
  name: String!
  type: String!
  properties: JSON
  confidence: Confidence
}

input RelationInput {
  sourceId: ID!
  targetId: ID!
  type: String!
  properties: JSON
}

input ReasonInput {
  query: String!
  ontologyId: ID
  context: JSON
  options: ReasonOptionsInput
}

input ReasonOptionsInput {
  includeChain: Boolean = true
  includeSuggestions: Boolean = true
  maxSteps: Int = 10
}

input ExtractInput {
  text: String!
  ontologyId: ID!
  preview: Boolean = false
}

input OntologyInput {
  name: String!
  description: String
  format: OntologyFormat!
  content: String!
}

input EntityFilterInput {
  type: String
  confidence: Confidence
  search: String
  limit: Int = 100
  offset: Int = 0
}

input GraphFilterInput {
  entityTypes: [String!]
  relationTypes: [String!]
  depth: Int = 2
  limit: Int = 100
}

# ============================================
# Types - Core
# ============================================

type Ontology {
  id: ID!
  name: String!
  version: String!
  format: OntologyFormat!
  description: String
  entityCount: Int!
  relationCount: Int!
  createdBy: User!
  createdAt: DateTime!
  updatedAt: DateTime!
  
  # 关联
  entities(filter: EntityFilterInput): [Entity!]!
  relations: [Relation!]!
  versions: [OntologyVersion!]!
}

type OntologyVersion {
  id: ID!
  version: String!
  changelog: String
  createdBy: User!
  createdAt: DateTime!
  diff: JSON
}

type Entity {
  id: ID!
  ontology: Ontology!
  name: String!
  type: String!
  properties: JSON
  confidence: Confidence!
  source: String  # v3.3新增：来源追踪
  createdAt: DateTime!
  updatedAt: DateTime!
  
  # 关联
  outgoingRelations: [Relation!]!
  incomingRelations: [Relation!]!
}

type Relation {
  id: ID!
  ontology: Ontology!
  source: Entity!
  target: Entity!
  type: String!
  properties: JSON
  confidence: Float
  createdAt: DateTime!
}

type User {
  id: ID!
  username: String!
  email: String
  role: UserRole!
  createdAt: DateTime!
}

enum UserRole {
  ADMIN
  EXPERT
  DEVELOPER
  VIEWER
}

# ============================================
# Types - Reasoning (v3.3增强)
# ============================================

type ReasoningResult {
  id: ID!
  query: String!
  finalConclusion: String!
  confidence: Confidence!
  steps: [ReasoningStep!]!
  suggestions: [Suggestion!]  # v3.3新增
  executionTimeMs: Int!
  timestamp: DateTime!
}

type ReasoningStep {
  step: Int!
  input: String!
  rule: Rule
  conclusion: String!
  confidence: Confidence!
  evidence: [String!]!
  isAssumption: Boolean!  # v3.3新增
  needsConfirmation: Boolean!  # v3.3新增
  confirmedByUser: Boolean  # v3.3新增
}

type Rule {
  id: ID!
  name: String!
  condition: String!
  action: String!
  weight: Float!
  source: String
  confidence: Confidence!
}

type Suggestion {  # v3.3新增
  type: String!
  message: String!
  relatedEntities: [String!]!
  suggestedEntity: EntitySuggestion
}

type EntitySuggestion {
  name: String!
  type: String!
  properties: JSON
}

# ============================================
# Types - Extraction (v3.3新增)
# ============================================

type ExtractionResult {
  id: ID!
  entities: [Entity!]!
  relations: [Relation!]!
  duplicates: [Entity!]!
  preview: Boolean!
  status: ExtractionStatus!
  createdAt: DateTime!
}

type ExtractionLog {
  id: ID!
  sourceText: String!
  extractedEntities: [Entity!]!
  extractedRelations: [Relation!]!
  userConfirmed: Boolean
  status: ExtractionStatus!
  createdAt: DateTime!
}

# ============================================
# Types - Graph
# ============================================

type GraphStats {
  totalEntities: Int!
  totalRelations: Int!
  entityTypes: [TypeCount!]!
  relationTypes: [TypeCount!]!
  avgDegree: Float!
}

type TypeCount {
  type: String!
  count: Int!
}

type GraphPath {
  nodes: [Entity!]!
  edges: [Relation!]!
  length: Int!
}

type Subgraph {
  nodes: [Entity!]!
  edges: [Relation!]!
  rootEntity: Entity!
}

# ============================================
# Query
# ============================================

type Query {
  # 本体查询
  ontology(id: ID!): Ontology
  ontologies(limit: Int = 50, offset: Int = 0): [Ontology!]!
  ontologyVersion(id: ID!, version: String!): OntologyVersion
  
  # 实体查询
  entities(filter: EntityFilterInput): [Entity!]!
  entity(id: ID!): Entity
  searchEntities(query: String!, type: String, limit: Int = 20): [Entity!]!
  
  # 关系查询
  relations(sourceId: ID, targetId: ID, type: String): [Relation!]!
  relation(id: ID!): Relation
  
  # 推理查询
  reasoning(id: ID!): ReasoningResult
  reasonings(limit: Int = 50, offset: Int = 0): [ReasoningResult!]!
  
  # 图谱查询
  graph(filter: GraphFilterInput): [Entity!]!
  graphStats: GraphStats!
  shortestPath(sourceId: ID!, targetId: ID!): GraphPath
  subgraph(rootEntityId: ID!, depth: Int = 2): Subgraph
  
  # 抽取查询 (v3.3新增)
  extractionLogs(limit: Int = 50, offset: Int = 0): [ExtractionLog!]!
  
  # 用户查询
  currentUser: User
  users: [User!]!
}

# ============================================
# Mutation
# ============================================

type Mutation {
  # 本体管理
  createOntology(input: OntologyInput!): Ontology!
  updateOntology(id: ID!, input: OntologyInput!): Ontology!
  deleteOntology(id: ID!): Boolean!
  importOntology(file: String!, format: OntologyFormat!): Ontology!
  exportOntology(id: ID!, format: OntologyFormat!): String!
  rollbackOntology(id: ID!, version: String!): Ontology!
  
  # 实体管理
  createEntity(ontologyId: ID!, input: EntityInput!): Entity!
  updateEntity(id: ID!, input: EntityInput!): Entity!
  deleteEntity(id: ID!): Boolean!
  upgradeConfidence(entityId: ID!): Entity!  # v3.3新增
  
  # 关系管理
  createRelation(ontologyId: ID!, input: RelationInput!): Relation!
  deleteRelation(id: ID!): Boolean!
  
  # 推理服务
  reason(input: ReasonInput!): ReasoningResult!
  confirmHypothesis(reasoningId: ID!, stepIndex: Int!, confirmed: Boolean!): ReasoningResult!  # v3.3新增
  
  # 抽取与主动学习 (v3.3新增)
  extract(input: ExtractInput!): ExtractionResult!
  confirmExtraction(extractionId: ID!, entityIds: [ID!]!, relationIds: [ID!]!): Boolean!
  
  # 用户管理
  updateUser(id: ID!, role: UserRole!): User!
}

# ============================================
# Subscription (实时推理)
# ============================================

type Subscription {
  reasoningProgress(reasoningId: ID!): ReasoningStep!
  extractionProgress: ExtractionResult!
}
```

#### GraphQL 查询示例

```graphql
# 查询本体及其实体
query GetOntologyWithEntities {
  ontology(id: "550e8400-e29b-41d4-a716-446655440000") {
    id
    name
    version
    entityCount
    entities(limit: 10) {
      id
      name
      type
      confidence
    }
  }
}

# 推理查询
mutation ExecuteReasoning {
  reason(input: {
    query: "某燃气管道设计压力为0.8MPa，应该使用什么级别的管道？"
    ontologyId: "550e8400-e29b-41d4-a716-446655440000"
    options: {
      includeChain: true
      includeSuggestions: true
      maxSteps: 10
    }
  }) {
    id
    finalConclusion
    confidence
    executionTimeMs
    steps {
      step
      input
      conclusion
      confidence
      rule {
        name
        condition
      }
      isAssumption
      needsConfirmation
    }
    suggestions {
      type
      message
      relatedEntities
    }
  }
}

# 抽取实体 (v3.3新增)
mutation ExtractEntities {
  extract(input: {
    text: "GB/T 8163-2018规定，输送流体用无缝钢管..."
    ontologyId: "550e8400-e29b-41d4-a716-446655440000"
    preview: true
  }) {
    id
    entities {
      name
      type
      properties
    }
    relations {
      source { name }
      target { name }
      type
    }
    duplicates {
      name
      id
    }
    preview
  }
}

# 图谱查询
query GetGraphStats {
  graphStats {
    totalEntities
    totalRelations
    entityTypes {
      type
      count
    }
    avgDegree
  }
}

query SearchSubgraph {
  subgraph(rootEntityId: "550e8400-e29b-41d4-a716-446655440000", depth: 2) {
    nodes {
      id
      name
      type
    }
    edges {
      type
      source { name }
      target { name }
    }
  }
}
```

---

## 六、数据模型

### 6.1 本体模型

```yaml
# 本体
Ontology:
  id: UUID
  name: String
  version: String
  format: Enum[OWL, RDF, YAML, JSON]
  content: Text
  created_by: User
  created_at: DateTime
  updated_at: DateTime

# 实体
Entity:
  id: UUID
  ontology_id: UUID
  name: String
  type: String (Person/Concept/Law/Rule/Task...)
  properties: JSON
  confidence: Enum[CONFIRMED, ASSUMED, SPECULATIVE, UNKNOWN]
  source: String  # v3.3新增：数据来源
  created_at: DateTime
  updated_at: DateTime

# 关系
Relation:
  id: UUID
  ontology_id: UUID
  source_id: UUID (Entity)
  target_id: UUID (Entity)
  type: String (is_a/has_rule/triggers...)
  properties: JSON
  confidence: Float
  created_at: DateTime
```

### 6.2 推理模型

```yaml
# 推理结果
Reasoning:
  id: UUID
  query: String
  context: JSON
  steps: [ReasoningStep]
  conclusion: String
  confidence: Enum[CONFIRMED, ASSUMED, SPECULATIVE, UNKNOWN]
  execution_time: Int (ms)
  created_at: DateTime
  suggestions: [Suggestion]  # v3.3新增

# 推理步骤
ReasoningStep:
  step: Int
  input: String
  rule_id: UUID (可选)
  rule_content: String (可选)
  conclusion: String
  confidence: Enum
  is_assumption: Boolean  # v3.3新增
  needs_confirmation: Boolean  # v3.3新增
  confirmed_by_user: Boolean  # v3.3新增

# 规则
Rule:
  id: UUID
  name: String
  condition: String
  action: String
  weight: Float
  source: String
  confidence: Enum
  enabled: Boolean
```

### 6.3 主动学习模型（v3.3新增）

```yaml
# 抽取日志
ExtractionLog:
  id: UUID
  timestamp: DateTime
  source_text: String
  extracted_entities: [Entity]
  extracted_relations: [Relation]
  user_confirmed: Boolean
  duplicates: [Entity]
  status: Enum[PENDING, CONFIRMED, CANCELLED]

# 置信度追踪
ConfidenceTracker:
  entity_id: UUID
  current_confidence: Enum
  upgrade_history: [UpgradeRecord]
  user_confirmations: Int
  last_confirmed_at: DateTime

# 智能触发配置
AutoLearnTrigger:
  id: UUID
  event: String  # user_says_write_ontology/user_confirms_reasoning
  action: String  # extract_to_ontology/suggest_upgrade_confidence
  enabled: Boolean
  requires_confirmation: Boolean
```

---

## 七、验收标准

### 7.1 本体管理模块

| 验收项 | 验收条件 |
|--------|----------|
| OWL导入 | 导入标准OWL文件，实体和关系正确解析 |
| RDF导入 | 导入RDF/XML文件，数据完整 |
| 版本管理 | 修改本体后自动创建版本，可回滚 |
| 可视化编辑 | Web界面创建实体和关系，数据正确保存 |
| 交互抽取 | 用户说"写入本体"后展示预览，确认后写入 |

### 7.2 推理引擎服务

| 验收项 | 验收条件 |
|--------|----------|
| RESTful API | 所有端点正常响应，状态码正确 |
| GraphQL | 支持查询实体、关系、推理结果 |
| 置信度标注 | 推理结果包含四种置信度标注 |
| 推理链 | 返回完整推理步骤，每步有规则依据 |
| 主动学习 | 支持抽取触发、置信度升级 |
| 失败建议 | 本体查无数据时返回补充建议 |

### 7.3 知识图谱模块

| 验收项 | 验收条件 |
|--------|----------|
| Neo4j集成 | 本体变更实时同步到Neo4j |
| 图可视化 | Web界面展示知识图谱，支持缩放拖拽 |
| 图查询 | 支持按类型/名称搜索，支持路径查询 |

### 7.4 用户交互

| 验收项 | 验收条件 |
|--------|----------|
| 置信度展示 | 四种置信度用不同颜色标注 |
| 假设确认 | 关键假设暂停推理，弹出确认框 |
| 推理追溯 | 可视化展示推理链，支持点击查看详情 |
| 抽取确认 | 写入本体前展示预览，用户确认后执行 |

---

## 八、交付计划

### 8.1 迭代规划

| 迭代 | 时间 | 交付内容 |
|------|------|----------|
| Sprint 1 | 1-2周 | 项目初始化、基础框架搭建 |
| Sprint 2 | 3-4周 | OWL/RDF解析器、基础本体加载 |
| Sprint 3 | 5-6周 | 本体版本管理、RESTful API |
| Sprint 4 | 7-8周 | Neo4j集成、图查询API |
| Sprint 5 | 9-10周 | GraphQL API、推理可解释性 |
| Sprint 6 | 11-12周 | Web界面、测试优化 |
| Sprint 7 | 13-14周 | 主动学习模块开发 |
| Sprint 8 | 15-16周 | Beta测试、Bug修复 |

### 8.2 里程碑

| 里程碑 | 计划日期 | 交付内容 |
|--------|----------|----------|
| M1 - 基础框架 | 第2周 | 项目架构、技术选型 |
| M2 - 本体管理 | 第4周 | OWL/RDF导入导出、版本管理 |
| M3 - 图数据库 | 第6周 | Neo4j集成、图查询 |
| M4 - 推理引擎 | 第8周 | RESTful + GraphQL API |
| M5 - 可解释性 | 第10周 | 推理过程追溯、置信度展示 |
| M6 - Web界面 | 第12周 | 本体编辑、图谱可视化 |
| M7 - 主动学习 | 第14周 | 抽取、升级、失败建议 |
| **V2.0 发布** | **第16周** | **正式版本发布** |

---

## 十一、MVP功能优先级

### 11.1 MVP定义

MVP（Minimum Viable Product）版本聚焦核心价值：**可信AI推理引擎**

### 11.2 MVP功能清单

| 优先级 | 功能模块 | 功能ID | 功能描述 | 用户价值 |
|--------|----------|--------|----------|----------|
| **P0-MVP** | 本体管理 | ONT-001 | OWL格式本体导入 | 利用已有知识积累 |
| **P0-MVP** | 本体管理 | ONT-002 | RDF/XML格式导入 | 扩展导入能力 |
| **P0-MVP** | 本体管理 | ONT-003 | 导出为OWL格式 | 数据可移植性 |
| **P0-MVP** | 本体管理 | ONT-005 | YAML格式互转 | 与现有系统兼容 |
| **P0-MVP** | 本体管理 | ONT-006 | 本体版本自动记录 | 变更可追溯 |
| **P0-MVP** | 本体管理 | ONT-007 | 版本历史查看 | 了解变更过程 |
| **P0-MVP** | 本体管理 | ONT-008 | 版本回滚 | 快速恢复 |
| **P0-MVP** | 本体管理 | ONT-011 | 实体关系图可视化 | 直观理解本体结构 |
| **P0-MVP** | 本体管理 | ONT-012 | 实体CRUD操作 | 维护本体数据 |
| **P0-MVP** | 本体管理 | ONT-013 | 关系连线操作 | 建立实体关联 |
| **P0-MVP** | 推理服务 | REA-001 | 推理查询接口 | 执行核心推理 |
| **P0-MVP** | 推理服务 | REA-002 | 置信度获取 | 判断结论可靠性 |
| **P0-MVP** | 推理服务 | REA-003 | 推理链获取 | 追溯推理过程 |
| **P0-MVP** | 推理服务 | REA-004 | 本体查询接口 | 查询本体数据 |
| **P0-MVP** | 推理服务 | REA-006 | GraphQL端点 | 灵活查询能力 |
| **P0-MVP** | 推理服务 | REA-011 | 推理依据展示 | 理解推理逻辑 |
| **P0-MVP** | 推理服务 | REA-012 | 置信度标注 | 区分结论可靠性 |
| **P0-MVP** | 推理服务 | REA-013 | 假设声明 | 明确推理前提 |
| **P0-MVP** | 推理服务 | REA-014 | 推理步骤可视化 | 直观展示推理链 |
| **P0-MVP** | 图数据库 | KG-001 | Neo4j连接 | 基础图数据能力 |
| **P0-MVP** | 图数据库 | KG-002 | 实体同步 | 本体图谱同步 |
| **P0-MVP** | 图数据库 | KG-003 | 关系同步 | 图关系同步 |
| **P0-MVP** | 图数据库 | KG-006 | 图谱可视化 | Web界面展示 |
| **P0-MVP** | 图数据库 | KG-007 | 节点搜索 | 快速定位实体 |
| **P0-MVP** | 图数据库 | KG-008 | 关系探索 | 发现关联关系 |
| **P0-MVP** | 用户交互 | UI-001 | 置信度标签 | 清晰展示四种置信度 |
| **P0-MVP** | 用户交互 | UI-002 | 置信度筛选 | 按置信度筛选结论 |
| **P0-MVP** | 用户交互 | UI-003 | 置信度颜色 | 颜色区分可靠性 |
| **P0-MVP** | 用户交互 | UI-004 | 置信度说明 | 理解置信度含义 |
| **P0-MVP** | 用户交互 | UI-009 | 推理链展示 | 可视化推理步骤 |
| **P0-MVP** | 用户交互 | UI-010 | 步骤详情 | 查看每步详情 |
| **P0-MVP** | 用户交互 | UI-011 | 规则来源 | 展示规则依据 |

### 11.3 MVP不在范围

| 模块 | 功能ID | 原因 |
|------|--------|------|
| 本体管理 | ONT-009/010/014/015/016-019 | 增强功能，可后续迭代 |
| 推理服务 | REA-005/010/015/016-028 | 非MVP必须，主动学习后续迭代 |
| 图数据库 | KG-005/009/010/011-017 | 可后续迭代 |
| 用户交互 | UI-005-008/012-017 | 假设确认和主动学习交互后续迭代 |

### 11.4 MVP交付检查

```
MVP完成标准检查清单：
☐ OWL/RDF/YAML本体可导入导出
☐ 本体版本自动记录，可查看和回滚
☐ Web界面可视化编辑实体和关系
☐ Neo4j图数据库集成，图谱可视化
☐ RESTful API推理查询
☐ GraphQL灵活查询
☐ 推理结果包含置信度标注（4种）
☐ 推理步骤完整可追溯
☐ 置信度颜色区分展示
☐ 推理链可视化展示
```

---

## 十二、竞品功能对比

### 12.1 竞品概览

| 竞品 | 类型 | 定位 | 核心优势 | 定价 |
|------|------|------|----------|------|
| **Neo4j** | 图数据库 | 图数据存储查询 | 图数据库领导者、生态成熟 | $70K+/年 |
| **Stardog** | 知识图谱平台 | 企业级知识图谱 | 统一数据平台、推理能力 | $50K+/年 |
| **GraphDB** | 图数据库 | RDF图存储 | OWL推理、免费版可用 | €2.5K+/年 |
| **AllegroGraph** | 图数据库 | RDF四层存储 | 大规模推理、时序支持 | $20K+/年 |
| **Palantir Foundry** | 数据平台 | 企业数据操作系统 | 数据整合、决策支持 | $100K+/年 |
| **pool** | 知识图谱 | 开源知识图谱 | 免费开源、社区活跃 | 开源免费 |
| **国产图数据库** | 图数据库 | 本地化市场 | 政策支持、本地化 | 10-50万 |

### 12.2 功能矩阵对比

| 功能维度 | ontology-platform | Neo4j | Stardog | GraphDB | Palantir | pool |
|----------|-------------------|-------|---------|---------|----------|------|
| **本体推理** | | | | | | |
| OWL2 RL推理 | ✅ P0 | ❌ | ✅ | ✅ | △ | ✅ |
| RDF推理 | ✅ P0 | ❌ | ✅ | ✅ | △ | ✅ |
| 规则引擎 | ✅ 自研 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 混合推理 | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ |
| **可解释性** | | | | | | |
| 推理链追溯 | ✅ P0 | ❌ | △ | ❌ | △ | ❌ |
| 置信度标注 | ✅ P0 | ❌ | ❌ | ❌ | △ | ❌ |
| 假设声明 | ✅ P0 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **知识图谱** | | | | | | |
| Neo4j集成 | ✅ P0 | ✅ | ✅ | ❌ | ✅ | ✅ |
| 图可视化 | ✅ P0 | ✅ | ✅ | ✅ | ✅ | ✅ |
| **主动学习** | | | | | | |
| 交互式抽取 | ✅ v3.3 | ❌ | ❌ | ❌ | ❌ | ❌ |
| 置信度升级 | ✅ v3.3 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **开发接口** | | | | | | |
| REST API | ✅ P0 | ✅ | ✅ | ✅ | ✅ | ✅ |
| GraphQL | ✅ P0 | ❌ | ✅ | ❌ | △ | ❌ |
| **部署** | | | | | | |
| 私有化部署 | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| K8s支持 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **定价** | | | | | | |
| 免费版 | 规划中 | ❌ | ❌ | ✅ | ❌ | ✅ |
| 企业版 | 30万起 | $70K+ | $50K+ | €2.5K+ | $100K+ | 免费 |

**图例**: ✅ 支持 | △ 部分支持 | ❌ 不支持 | P0 优先级

### 12.3 核心差异分析

#### 12.3.1 vs Neo4j

| 维度 | ontology-platform | Neo4j |
|------|-------------------|-------|
| **定位差异** | 本体推理引擎 | 图数据库 |
| **核心能力** | OWL推理 + 可解释性 | 图查询性能 |
| **优势** | 消除AI幻觉、推理可追溯 | 生态成熟、性能优秀 |
| **劣势** | 图查询性能 | 无推理能力 |

**结论**: Neo4j是优秀的图存储层，但缺少上层推理能力。ontology-platform可作为Neo4j的上层推理引擎。

#### 12.3.2 vs Stardog

| 维度 | ontology-platform | Stardog |
|------|-------------------|---------|
| **定位差异** | 垂直领域推理 | 企业知识图谱平台 |
| **核心能力** | 可解释AI + 主动学习 | 统一数据视图 |
| **优势** | 推理过程透明、v3.3新特性 | 企业级功能完善 |
| **劣势** | 起步晚、生态待建 | 定价高、学习曲线陡 |

**结论**: Stardog是最接近的竞品，但定价高昂且缺乏主动学习能力。ontology-platform在性价比和AI可解释性上有优势。

#### 12.3.3 vs Palantir Foundry

| 维度 | ontology-platform | Palantir |
|------|-------------------|----------|
| **定位差异** | 推理引擎组件 | 数据操作系统 |
| **核心能力** | 本体推理 + 可解释性 | 数据整合 + 决策 |
| **优势** | 专注推理、部署灵活 | 品牌效应、端到端 |
| **劣势** | 非端到端平台 | 定价极高、封闭 |

**结论**: Palantir定位更高端。ontology-platform定位为推理组件，可与Palantir互补或作为替代方案。

### 12.4 竞争优势总结

| 竞争优势 | 说明 | 竞品对比 |
|----------|------|----------|
| **AI可解释性** | 完整推理链 + 置信度 + 假设声明 | 独有 |
| **主动学习** | v3.3新增的交互式抽取和置信度升级 | 独有 |
| **混合推理** | OWL + 规则引擎 + 图遍历融合 | Stardog部分支持 |
| **性价比** | 企业版30万起，远低于国际大厂 | 显著优势 |
| **本地化** | 中文支持、国产化适配 | 政策优势 |
| **OpenClaw集成** | 与AI Agent深度集成 | 独有生态 |

---

## 十三、风险分析

### 9.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| OWL解析复杂度 | 高 | 调研成熟库(RDFLib)，预留缓冲时间 |
| Neo4j性能 | 中 | 预先性能测试，优化查询 |
| GraphQL复杂性 | 中 | 使用成熟框架(Strawberry) |
| 主动学习误触发 | 中 | 默认禁用，用户授权开启 |

### 9.2 产品风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 用户对可解释性接受度 | 中 | 收集早期用户反馈 |
| 本体构建门槛 | 中 | 提供模板和示例 |
| 自动学习隐私风险 | 高 | 严格权限控制，不读取敏感文件 |

---

## 十四、附录

### 10.1 参考文档

- ontology-clawra SKILL.md (v3.3)
- 技术架构文档 (cto/architecture.md)
- API接口文档

### 10.2 术语表

| 术语 | 定义 |
|------|------|
| OWL | Web Ontology Language，网络本体语言 |
| RDF | Resource Description Framework，资源描述框架 |
| 本体 | 领域概念模型及其关系 |
| 置信度 | 推理结论的可信程度 |
| 推理链 | 从输入到结论的推理步骤序列 |
| 主动学习 | 用户确认后自动抽取知识的能力 |
| 智能触发 | 特定条件下自动执行预定义动作 |

---

### 10.3 v3.3 核心升级说明

本PRD基于ontology-clawra v3.3，主要新增以下能力：

1. **主动学习能力**
   - 用户说"写入本体"触发抽取
   - 抽取前预览确认
   - 置信度升级机制

2. **智能触发机制**
   - 推理失败时主动建议补充
   - 高频实体自动识别
   - 用户纠正自动记录

3. **安全边界**
   - 自动学习默认禁用
   - 写入需用户确认
   - 隐私保护（不读取敏感文件）

---

**文档版本**: V2.0  
**创建日期**: 2026-03-16  
**最后更新**: 2026-03-16 23:50  
**状态**: 已完成（用户故事地图+MVP功能优先级+竞品对比已补充）
