# ontology-platform 产品需求文档 (V2.0 生产级)

**文档版本**: V2.0  
**创建日期**: 2026-03-16  
**最后更新**: 2026-03-17  
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

### 3.4 数据分析模块

#### 3.4.1 推理数据分析

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| ANA-001 | 推理次数统计 | P1 | 按日/周/月统计推理调用量 |
| ANA-002 | 置信度分布 | P1 | 统计各置信度等级占比 |
| ANA-003 | 推理耗时分析 | P1 | P50/P95/P99响应时间统计 |
| ANA-004 | 热门查询分析 | P1 | 统计高频推理查询词 |
| ANA-005 | 推理成功率 | P1 | 成功/失败推理比例统计 |

#### 3.4.2 本体质量分析

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| ANA-006 | 实体完整度 | P1 | 统计实体属性完整率 |
| ANA-007 | 关系覆盖度 | P1 | 统计关系类型覆盖率 |
| ANA-008 | 知识盲区识别 | P1 | 识别高频但缺失的实体/关系 |
| ANA-009 | 置信度分布 | P1 | 各实体置信度等级分布 |
| ANA-010 | 知识增长趋势 | P1 | 实体/关系数量随时间变化 |

#### 3.4.3 用户行为分析

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| ANA-011 | 用户活跃度 | P1 | 日活/月活用户统计 |
| ANA-012 | 功能使用热图 | P1 | 各功能模块使用频率 |
| ANA-013 | 用户留存率 | P1 | 新增用户留存统计 |
| ANA-014 | API调用排行 | P1 | 各API端点调用排名 |

#### 3.4.4 数据可视化仪表盘

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| ANA-015 | 总览仪表盘 | P1 | 核心指标一屏展示 |
| ANA-016 | 推理统计面板 | P1 | 推理相关数据图表 |
| ANA-017 | 本体质量面板 | P1 | 本体质量指标图表 |
| ANA-018 | 用户行为面板 | P1 | 用户活动数据图表 |
| ANA-019 | 自定义报表 | P2 | 支持用户自定义指标组合 |
| ANA-020 | 数据导出 | P1 | 支持导出为CSV/Excel |

### 3.5 报表导出模块

#### 3.5.1 推理报告导出

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| RPT-001 | PDF推理报告 | P0 | 生成包含推理链的PDF报告 |
| RPT-002 | Markdown报告 | P0 | 生成Markdown格式推理报告 |
| RPT-003 | HTML报告 | P1 | 生成可交互HTML报告 |
| RPT-004 | 报告模板选择 | P1 | 支持多种报告模板 |
| RPT-005 | 报告水印 | P1 | 支持添加公司水印 |

#### 3.5.2 本体报告导出

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| RPT-006 | 本体结构报告 | P1 | 生成本体结构说明文档 |
| RPT-007 | 实体清单报表 | P1 | 导出全部实体为Excel |
| RPT-008 | 关系清单报表 | P1 | 导出全部关系为Excel |
| RPT-009 | 版本对比报告 | P1 | 两个版本差异报告 |

#### 3.5.3 统计分析报表

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| RPT-010 | 推理统计报表 | P1 | 周期推理数据统计报表 |
| RPT-011 | 质量分析报表 | P1 | 本体质量分析报告 |
| RPT-012 | 用户行为报表 | P1 | 用户活动统计报表 |
| RPT-013 | 自定义报表 | P2 | 用户自定义报表配置 |
| RPT-014 | 报表定时任务 | P2 | 自动生成定期报表 |
| RPT-015 | 报表订阅 | P2 | 邮件订阅定期报表 |

#### 3.5.4 导出格式支持

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| RPT-016 | PDF导出 | P0 | 高质量PDF文档输出 |
| RPT-017 | Excel导出 | P0 | 多Sheet Excel文件 |
| RPT-018 | CSV导出 | P0 | 通用CSV格式 |
| RPT-019 | JSON导出 | P1 | 结构化JSON数据 |
| RPT-020 | 图片导出 | P1 | 图表导出为PNG/SVG |

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

**数据分析 API**

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/analytics/reasoning` | 推理统计 | `?period=day|week|month` | `ReasoningAnalyticsResponse` |
| GET | `/api/v1/analytics/confidence` | 置信度分布 | `?ontology_id=` | `ConfidenceDistributionResponse` |
| GET | `/api/v1/analytics/performance` | 性能分析 | `?period=` | `PerformanceAnalyticsResponse` |
| GET | `/api/v1/analytics/queries` | 热门查询 | `?limit=10` | `TopQueriesResponse` |
| GET | `/api/v1/analytics/ontology-quality` | 本体质量 | `?ontology_id=` | `OntologyQualityResponse` |
| GET | `/api/v1/analytics/knowledge-gaps` | 知识盲区 | `?ontology_id=` | `KnowledgeGapsResponse` |
| GET | `/api/v1/analytics/trends` | 增长趋势 | `?ontology_id=&metric=` | `TrendsResponse` |
| GET | `/api/v1/analytics/users` | 用户行为 | `?period=` | `UserAnalyticsResponse` |
| GET | `/api/v1/analytics/dashboard` | 仪表盘数据 | - | `DashboardResponse` |

**报表导出 API**

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/v1/reports/reasoning` | 生成推理报告 | `ReasoningReportRequest` | `ReportResponse` |
| GET | `/api/v1/reports/{id}/download` | 下载报告 | `?format=pdf|md|html` | `File` |
| POST | `/api/v1/reports/ontology` | 生成本体报告 | `OntologyReportRequest` | `ReportResponse` |
| POST | `/api/v1/reports/analytics` | 生成统计报表 | `AnalyticsReportRequest` | `ReportResponse` |
| GET | `/api/v1/reports` | 报告列表 | `?type=&status=` | `ReportListResponse` |
| DELETE | `/api/v1/reports/{id}` | 删除报告 | - | `DeleteResponse` |
| POST | `/api/v1/reports/scheduled` | 创建定时报表 | `ScheduledReportRequest` | `ScheduledReport` |
| GET | `/api/v1/reports/scheduled` | 定时报表列表 | - | `ScheduledReportListResponse` |
| PUT | `/api/v1/reports/scheduled/{id}` | 更新定时报表 | `ScheduledReportRequest` | `ScheduledReport` |
| DELETE | `/api/v1/reports/scheduled/{id}` | 删除定时报表 | - | `DeleteResponse` |

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

### 7.5 数据分析模块

| 验收项 | 验收条件 |
|--------|----------|
| 推理统计 | 按日/周/月统计推理次数，图表展示 |
| 置信度分布 | 展示各置信度等级占比饼图 |
| 耗时分析 | P50/P95/P99响应时间折线图 |
| 热门查询 | 展示Top 10高频推理查询 |
| 本体质量 | 实体完整度、关系覆盖度指标 |
| 知识盲区 | 识别并展示高频缺失的实体/关系 |
| 仪表盘 | 总览仪表盘展示核心指标 |
| 数据导出 | 支持导出统计数据为CSV/Excel |

### 7.6 报表导出模块

| 验收项 | 验收条件 |
|--------|----------|
| PDF推理报告 | 生成包含完整推理链的PDF文档 |
| Markdown报告 | 生成结构化Markdown报告 |
| 本体清单导出 | 导出实体/关系为Excel文件 |
| 统计分析报表 | 周期性统计数据报表生成 |
| 多格式支持 | 支持PDF/Excel/CSV/JSON/图片格式 |
| 报告模板 | 支持自定义报告模板 |
| 定时报表 | 支持配置定时生成报表任务 |

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

## 十三、商业模式

### 13.1 定价策略

#### 13.1.1 定价原则

| 原则 | 说明 |
|------|------|
| 价值导向 | 根据客户获得的推理能力、节省的时间定价 |
| 规模适配 | 支持小团队到大型企业的不同规模 |
| 透明定价 | 无隐藏费用，按需选择 |
| 长期优惠 | 年度订阅享折扣，鼓励长期合作 |

#### 13.1.2 版本定价

| 版本 | 价格 | 目标客户 | 核心功能 |
|------|------|----------|----------|
| **免费版** | ¥0 | 个人开发者、研究人员 | 3个本体、100次/日推理、基础图谱可视化 |
| **专业版** | ¥999/月 | 中小型团队 | 20个本体、5000次/日推理、GraphQL API、版本管理 |
| **企业版** | ¥30,000起/年 | 大型企业 | 无限本体、无限推理、专属支持、定制开发 |
| **API调用** | 按量付费 | 开发者、SaaS | ¥0.01/次推理、¥0.001/次图查询 |

#### 13.1.3 定价说明

| 版本 | 说明 |
|------|------|
| 免费版 | 限3个本体，100次/日推理，适合学习和评估 |
| 专业版 | 适合中小团队，支持20个本体，满足业务需求 |
| 企业版 | 含专属技术支持、定制开发、SLA保障 |
| API调用 | 适合需要在自身产品中集成推理能力的开发者 |

#### 13.1.4 增值服务

| 服务 | 价格 | 说明 |
|------|------|------|
| 现场部署 | ¥50,000起 | 客户现场部署实施 |
| 定制开发 | 另议 | 根据客户需求定制功能 |
| 培训服务 | ¥20,000/次 | 线上或线下培训 |
| 优先支持 | ¥10,000/年 | 7x24响应、优先修复 |

### 13.2 销售渠道

#### 13.2.1 直销模式

| 渠道 | 目标客户 | 销售方式 |
|------|----------|----------|
| 官网销售 | 中小企业、个人开发者 | 在线购买、自助服务 |
| 销售团队 | 大型企业、政府客户 | 线下洽谈、合同签订 |
| 电话销售 | 中型企业 | 电话沟通、远程演示 |

#### 13.2.2 渠道代理

| 代理商类型 | 合作方式 | 佣金比例 |
|------------|----------|----------|
| 行业集成商 | 打包解决方案 | 20-30% |
| 软件代理商 | 产品分销 | 15-25% |
| 云计算厂商 | 云市场入驻 | 分成模式 |

#### 13.2.3 合作伙伴

| 合作伙伴类型 | 合作模式 | 示例 |
|--------------|----------|------|
| AI产品厂商 | 技术授权 | AI Agent产品嵌入 |
| 行业解决方案商 | 行业定制 | 燃气、安全、金融 |
| 咨询公司 | 联合推广 | 数字化转型咨询 |

#### 13.2.4 在线渠道

| 渠道 | 说明 |
|------|------|
| 官网商城 | 在线购买、试用下载 |
| 云市场 | 阿里云、华为云、腾讯云 |
| 开源社区 | GitHub开源版本引流 |
| 行业论坛 | 技术博客、线上研讨会 |

#### 13.2.5 销售流程

```
线索获取 → 需求调研 → 方案设计 → 报价谈判 → 合同签订 → 交付实施 → 售后服务
    ↑                                                                      ↓
    └──────────────────────────────────────────────────────────────────────┘
                                      续费/扩展
```

#### 13.2.6 销售目标

| 阶段 | 时间 | 目标客户 | 预计收入 |
|------|------|----------|----------|
| 验证期 | 0-6个月 | 种子用户、免费版 | 验证产品市场匹配 |
| 成长期 | 6-18个月 | 中小企业、专业版 | 年收入100-300万 |
| 规模期 | 18-36个月 | 大型企业、企业版 | 年收入500-1000万 |
| 生态期 | 36个月+ | 渠道伙伴、API客户 | 年收入1000万+ |

---

## 九、运营策略

### 9.1 市场定位

| 定位维度 | 策略 |
|----------|------|
| 目标市场 | 中国企业级AI市场，重点关注燃气、安全、金融行业 |
| 差异化定位 | 可信AI推理引擎，消除AI幻觉，推理过程可追溯 |
| 核心卖点 | OWL推理 + 置信度标注 + 主动学习 + 国产化适配 |
| 竞争策略 | 以可解释AI和主动学习差异化国际大厂，以性价比和服务差异化开源方案 |

### 9.2 运营模式

#### 9.2.1 产品运营

| 策略 | 具体措施 |
|------|----------|
| 免费版运营 | 提供免费版吸引开发者，建立技术社区 |
| 版本迭代 | 按敏捷迭代，每2周一个小版本，每季度一个大版本 |
| 功能冻结 | 每个版本功能冻结后进入测试期，保证质量 |
| 用户反馈 | 建立用户反馈通道，产品决策优先考虑用户需求 |

#### 9.2.2 内容运营

| 渠道 | 内容策略 |
|------|----------|
| 官网 | 产品介绍、文档中心、视频教程、案例展示 |
| 公众号 | 技术干货、行业洞察、产品更新 |
| 技术博客 | 技术原理解析最佳实践、案例分享 |
| 视频号 | 产品演示、教程、线上研讨会回放 |
| 知乎/掘金 | 技术文章、问答互动 |

#### 9.2.3 社区运营

| 社区 | 运营策略 |
|------|----------|
| GitHub | 开源版本托管，issue跟踪，积极回应PR |
| 微信群 | 用户群、开发者群、VIP客户群分层运营 |
| 论坛 | 官方论坛，技术问答，案例分享 |
| 线下活动 | 参加行业会议、举办技术meetup |

### 9.3 增长策略

#### 9.3.1 用户增长漏斗

```
曝光 → 认知 → 兴趣 → 试用 → 付费 → 留存 → 推荐
  ↓     ↓      ↓     ↓     ↓     ↓     ↓
SEO   文档   Demo  免费版 专业版 续费   口碑
广告   视频   试用  试用    方案   培训   案例
KOL   文章   咨询  引导    谈判   服务   推荐
```

#### 9.3.2 增长策略矩阵

| 阶段 | 目标 | 核心策略 |
|------|------|----------|
| 启动期 | 获取种子用户 | 免费版推广、技术社区运营、行业KOL合作 |
| 成长期 | 扩大用户规模 | 搜索引擎优化、内容营销、渠道代理拓展 |
| 规模期 | 提升市场份额 | 行业解决方案、标杆案例复制、大客户直销 |

#### 9.3.3 用户获取渠道

| 渠道 | 优先级 | 获客成本 | 转化周期 |
|------|--------|----------|----------|
| 官网SEO/SEM | 高 | 中 | 1-3个月 |
| 技术社区（掘金、知乎） | 高 | 低 | 3-6个月 |
| 行业会议/展览 | 中 | 高 | 1-2个月 |
| 渠道代理商 | 中 | 中 | 1-3个月 |
| 客户推荐 | 高 | 低 | 即时 |
| 免费版转化 | 高 | 低 | 1-6个月 |

### 9.4 定价运营

| 策略 | 具体措施 |
|------|----------|
| 版本梯度 | 免费版→专业版→企业版，清晰的价值差异 |
| 试用策略 | 免费版无限制使用，专业版14天试用，企业版定制试点 |
| 促销活动 | 新用户首单折扣、年度订阅优惠、团购优惠 |
| 定价调整 | 每年Q4评估定价，保持市场竞争力 |

### 9.5 数据运营

| 指标 | 监控内容 | 目标值 |
|------|----------|--------|
| 用户数 | 日活、月活、新增、留存 | 月活增速>10% |
| 转化率 | 免费→专业版转化率 | >5%/月 |
| 收入 | ARR、MRR、客单价 | 年增长100%+ |
| NPS | 用户净推荐值 | >50 |
| 客服满意度 | 响应时间、解决率 | 响应<4h，解决率>90% |

---

## 十、客户成功计划

### 10.1 客户成功定义

客户成功（Customer Success）是以客户为中心，确保客户在使用产品过程中实现预期价值，并持续产生商业价值的管理体系。

### 10.2 客户成功目标

| 目标 | 指标 | 目标值 |
|------|------|--------|
| 客户满意度 | NPS评分 | >50 |
| 产品采用率 | 核心功能使用率 | >80% |
| 客户留存率 | 年度续费率 | >90% |
| 客户增长 | 扩展销售率 | >30% |
| 价值实现 | 客户ROI | >200% |

### 10.3 客户分层服务

#### 10.3.1 客户分层标准

| 层级 | 划分标准 | 服务模式 |
|------|----------|----------|
| **旗舰客户** | 年消费≥30万或战略意义 | 专属客户成功经理+技术顾问+7x24支持 |
| **重点客户** | 年消费5-30万 | 客户成功经理+工作日支持 |
| **标准客户** | 年消费<5万 | 自助服务+社区支持 |
| **免费客户** | 免费版用户 | 社区支持+文档自助 |

#### 10.3.2 服务内容矩阵

| 服务内容 | 旗舰客户 | 重点客户 | 标准客户 |
|----------|----------|----------|----------|
| 专属客户成功经理 | ✅ | △ | ❌ |
| 技术顾问支持 | ✅ | △ | ❌ |
| 7x24热线支持 | ✅ | ❌ | ❌ |
| 定期业务回顾 | 月度 | 季度 | ❌ |
| 定制培训 | ✅ | ✅ | ❌ |
| 现场部署服务 | ✅ | 协商 | ❌ |
| 优先新功能体验 | ✅ | ✅ | ❌ |
| SLA保障 | 99.9% | 99.5% | 99% |

### 10.4 客户成功旅程

#### 10.4.1 客户生命周期

```
 onboarding → 价值实现 → 规模使用 → 续费/扩展 → 推荐
     ↓           ↓          ↓          ↓          ↓
  1-2周       1-3个月    3-12个月   年度        持续
```

#### 10.4.2 各阶段关键动作

| 阶段 | 时间 | 关键动作 | 责任人 |
|------|------|----------|--------|
| **Onboarding** | 第1-2周 | 1. 欢迎邮件 + 专属客户经理联系 2. 产品培训（2小时） 3. 第一个本体导入协助 4. 初始配置检查 | CSM |
| **价值实现** | 第1-3个月 | 1. 首次成功推理庆祝 2. 使用情况回顾 3. 功能采用指导 4. 解决使用问题 | CSM |
| **规模使用** | 第3-12个月 | 1. 季度业务回顾 2. 最佳实践分享 3. 扩展使用场景 4. 客户声音收集 | CSM+技术 |
| **续费/扩展** | 年度 | 1. 续费前3个月沟通 2. ROI总结报告 3. 扩展需求挖掘 4. 合同洽谈 | CSM+销售 |
| **推荐** | 持续 | 1. 成功案例采访 2. 客户推荐激励 3. 行业案例分享 | 市场+CSM |

### 10.5 客户健康度管理

#### 10.5.1 健康度评分模型

| 维度 | 权重 | 指标 |
|------|------|------|
| 产品使用 | 40% | 登录频率、功能使用率、API调用量 |
| 价值实现 | 30% | 核心功能采用、业务目标达成、ROI |
| 客户满意度 | 20% | NPS、投诉/表扬、支持满意度 |
| 商业价值 | 10% | 续费意愿、扩展潜力、推荐意愿 |

#### 10.5.2 健康度等级

| 等级 | 分数 | 状态 | 行动 |
|------|------|------|------|
| 绿色 | 80-100 | 健康 | 保持维护，定期沟通 |
| 黄色 | 60-79 | 风险 | 主动关怀，解决问题 |
| 红色 | <60 | 危机 | 升级处理，高层介入 |

#### 10.5.3 预警触发条件

| 预警级别 | 触发条件 | 处理措施 |
|----------|----------|----------|
| 低危 | 连续2周未登录 | 邮件关怀，提供帮助 |
| 中危 | 连续4周未登录 | 电话沟通，了解原因 |
| 高危 | 连续8周未登录/投诉 | 客户经理介入，升级处理 |
| 严重 | 合同到期前无续费意向 | 销售+CSM联合挽留 |

### 10.6 客户价值实现

#### 10.6.1 价值衡量指标

| 客户类型 | 核心价值指标 | 衡量方式 |
|----------|--------------|----------|
| 燃气行业 | 安全隐患识别率提升 | 对比使用前后数据 |
| 安全生产 | 事故预防准确率 | 案例统计 |
| 金融风控 | 风险识别效率 | 处理时间对比 |
| 采购供应链 | 供应商评估准确率 | 评估结果验证 |

#### 10.6.2 ROI计算模型

```
客户ROI = (收益提升 + 成本节省) / 产品投入

其中：
- 收益提升 = 决策效率提升 × 单位决策价值
- 成本节省 = 人力节省 + 错误减少损失
- 产品投入 = 软件费用 + 实施费用 + 运维费用
```

#### 10.6.3 价值报告

| 报告类型 | 发送频率 | 内容 |
|----------|----------|------|
| 使用月报 | 月度 | 功能使用数据、亮点事件、优化建议 |
| 季度价值报告 | 季度 | ROI分析、案例成果、后续建议 |
| 年度总结报告 | 年度 | 价值回顾、规划建议、下年度计划 |

### 10.7 客户成功团队

#### 10.7.1 团队结构

| 角色 | 职责 | 配置 |
|------|------|------|
| 客户成功总监 | 团队管理、策略制定、跨部门协调 | 1人 |
| 客户成功经理 | 重点/旗舰客户管理 | 1人/20客户 |
| 技术支持工程师 | 技术问题解决、培训 | 1人/30客户 |
| 客户成功运营 | 数据分析、内容制作、活动组织 | 1人 |

#### 10.7.2 团队KPI

| 角色 | 核心KPI |
|------|---------|
| 客户成功总监 | 续费率、NPS、团队管理 |
| 客户成功经理 | 客户满意度、健康度、续费率 |
| 技术支持工程师 | 响应时间、解决率、首次解决率 |
| 客户成功运营 | 内容产出、活动参与度 |

### 10.8 客户反馈机制

| 反馈渠道 | 响应时间 | 处理流程 |
|----------|----------|----------|
| 客户经理 | 即时 | 记录→处理→反馈→归档 |
| 客服工单 | 4小时 | 受理→分派→处理→回访→关闭 |
| NPS调研 | 季度 | 发送→分析→行动计划→执行→跟踪 |
| 客户访谈 | 季度 | 预约→访谈→记录→分析→改进 |

### 10.9 客户成功工具

| 工具 | 用途 |
|------|------|
| CRM系统 | 客户信息管理、跟进记录 |
| 健康度监控平台 | 自动监控客户使用数据 |
| 知识库 | 常见问题、解决方案 |
| 培训平台 | 在线培训、视频课程 |
| 客户社区 | 交流互动、经验分享 |

---

## 十四、风险分析

### 14.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| OWL解析复杂度 | 高 | 调研成熟库(RDFLib)，预留缓冲时间 |
| Neo4j性能 | 中 | 预先性能测试，优化查询 |
| GraphQL复杂性 | 中 | 使用成熟框架(Strawberry) |
| 主动学习误触发 | 中 | 默认禁用，用户授权开启 |

### 14.2 产品风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 用户对可解释性接受度 | 中 | 收集早期用户反馈 |
| 本体构建门槛 | 中 | 提供模板和示例 |
| 自动学习隐私风险 | 高 | 严格权限控制，不读取敏感文件 |

---

## 十五、附录

### 15.1 参考文档

- ontology-clawra SKILL.md (v3.3)
- 技术架构文档 (cto/architecture.md)
- API接口文档

### 15.2 术语表

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

### 15.3 v3.3 核心升级说明

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

## 十六、国际化和多租户支持

### 16.1 国际化设计 (i18n)

#### 16.1.1 国际化目标

| 维度 | 目标 |
|------|------|
| 界面语言 | 支持中/英双语，可扩展更多语言 |
| 本体多语言 | 支持多语言本体标签和描述 |
| API多语言 | API响应支持多语言错误提示 |
| 文档 | 提供中英文技术文档 |

#### 16.1.2 国际化架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      国际化架构                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│   │   前端i18n   │    │   后端i18n   │    │   本体i18n   │    │
│   │   (i18next)  │    │   (gettext)  │    │   (RDF标签)  │    │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    │
│          │                   │                   │            │
│          ▼                   ▼                   ▼            │
│   ┌──────────────────────────────────────────────────────┐   │
│   │                    语言资源层                           │   │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐       │   │
│   │  │  zh-CN.json│  │  en-US.json│  │ 更多语言... │       │   │
│   │  └────────────┘  └────────────┘  └────────────┘       │   │
│   └──────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 16.1.3 功能需求

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| I18N-001 | 前端界面中英文切换 | P0 | 用户可切换中英文，界面即时更新 |
| I18N-002 | 语言偏好持久化 | P0 | 刷新页面保持语言选择 |
| I18N-003 | 本体多语言标签 | P0 | 实体/关系支持多语言名称和描述 |
| I18N-004 | API错误信息多语言 | P0 | 错误信息根据Accept-Language返回 |
| I18N-005 | 日期/数字格式化 | P0 | 按区域设置格式化 |
| I18N-006 | 推理结果多语言 | P1 | 推理结论支持多语言输出 |
| I18N-007 | 报表多语言 | P1 | 导出的报表支持多语言 |
| I18N-008 | 语言扩展框架 | P1 | 预留扩展接口支持更多语言 |

#### 16.1.4 本体多语言模型

```yaml
# 多语言本体
MultiLingualOntology:
  id: UUID
  default_locale: String  # 默认语言，如 "zh-CN"
  supported_locales: [String]  # 支持的语言列表
  
# 多语言实体
MultiLingualEntity:
  id: UUID
  labels: Map[locale, String]  # locale -> label
  descriptions: Map[locale, String]  # locale -> description
  aliases: Map[locale, [String]]  # locale -> aliases[]
  
# 多语言关系
MultiLingualRelation:
  id: UUID
  labels: Map[locale, String]  # locale -> label
```

#### 16.1.5 API设计

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/i18n/locales` | 获取支持的语言列表 |
| GET | `/api/v1/i18n/translations/{locale}` | 获取翻译资源 |
| PUT | `/api/v1/users/me/locale` | 设置用户语言偏好 |
| GET | `/api/v1/ontologies/{id}/entities?locale=zh-CN` | 按语言查询实体 |

#### 16.1.6 前端实现

| 组件 | 技术栈 | 说明 |
|------|--------|------|
| 国际化框架 | i18next | React组件集成 |
| 语言切换器 | React Context | 全局语言状态管理 |
| 日期格式化 | day.js | 基于locale的日期格式 |
| 数字格式化 | Intl.NumberFormat | 基于locale的数字格式 |

---

### 16.2 多租户支持

#### 16.2.1 多租户架构

| 架构模式 | 说明 | 适用场景 |
|----------|------|----------|
| **独立数据库** | 每个租户独立数据库 | 数据完全隔离，高安全要求 |
| **共享数据库独立Schema** | 共享数据库，租户独立Schema | 中等隔离需求，降低成本 |
| **共享数据库共享Schema** | 共享数据库和Schema，通过tenant_id隔离 | 低隔离需求，高并发场景 |

**本产品采用**: 共享数据库独立Schema模式（可配置切换）

```
┌─────────────────────────────────────────────────────────────────┐
│                      多租户架构                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    应用层                                │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│   │  │  租户A UI    │  │  租户B UI    │  │  租户C UI    │     │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                  租户隔离层 (Tenant Context)            │   │
│   │   ┌─────────────────────────────────────────────────┐  │   │
│   │   │  Tenant ID: 从 JWT/Header/Subdomain 获取        │  │   │
│   │   │  Tenant Filter: 自动注入租户ID                  │  │   │
│   │   │  Data Scope: 租户数据隔离                       │  │   │
│   │   └─────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   数据访问层                            │   │
│   │   ┌─────────────────────────────────────────────────┐  │   │
│   │   │          PostgreSQL (共享库独立Schema)         │  │   │
│   │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐           │  │   │
│   │   │  │ tenant_a │ │ tenant_b │ │ tenant_c │           │  │   │
│   │   │  └─────────┘ └─────────┘ └─────────┘           │  │   │
│   │   └─────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 16.2.2 租户识别方式

| 方式 | 说明 | 配置优先级 |
|------|------|------------|
| **Subdomain** | tenant.platform.com | 高（推荐） |
| **Header** | X-Tenant-ID | 高 |
| **JWT Claim** | token中包含tenant_id | 高 |
| **Query Param** | ?tenant=xxx | 低（调试用） |

#### 16.2.3 功能需求

| 功能ID | 功能描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| TEN-001 | 租户创建 | P0 | 管理员可创建新租户 |
| TEN-002 | 租户配置 | P0 | 配置租户名称、logo、域名 |
| TEN-003 | 租户用户管理 | P0 | 租户内用户隔离管理 |
| TEN-004 | 租户本体隔离 | P0 | 每个租户本体独立，互不可见 |
| TEN-005 | 租户图谱隔离 | P0 | Neo4j中租户数据隔离 |
| TEN-006 | 租户配额管理 | P0 | 配置租户API配额、存储上限 |
| TEN-007 | 租户角色权限 | P0 | 租户内RBAC权限控制 |
| TEN-008 | 租户数据导出 | P1 | 租户可导出自身数据 |
| TEN-009 | 租户计费 | P1 | 按租户使用量计费 |
| TEN-010 | 租户数据清理 | P1 | 租户注销后数据清理 |
| TEN-011 | 跨租户查询 | P2 | 超级管理员可跨租户查询 |

#### 16.2.4 数据模型

```yaml
# 租户
Tenant:
  id: UUID
  name: String
  slug: String  # 用于subdomain
  logo: String
  domain: String
  status: Enum[ACTIVE, SUSPENDED, DELETED]
  plan: Enum[FREE, PROFESSIONAL, ENTERPRISE]
  quota:
    api_calls_per_day: Int
    storage_mb: Int
    max_entities: Int
    max_ontologies: Int
  created_at: DateTime
  updated_at: DateTime

# 租户用户
TenantUser:
  id: UUID
  tenant_id: UUID
  user_id: UUID
  role: Enum[OWNER, ADMIN, MEMBER, VIEWER]
  status: Enum[ACTIVE, INVITED, DISABLED]
  invited_at: DateTime
  joined_at: DateTime

# 租户配置
TenantConfig:
  tenant_id: UUID
  locale: String  # 默认语言
  timezone: String
  custom_domain: String
  saml_enabled: Boolean
  features: Map[String, Boolean]  # 功能开关
```

#### 16.2.5 API设计

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| POST | `/api/v1/tenants` | 创建租户 | 超级管理员 |
| GET | `/api/v1/tenants` | 租户列表 | 超级管理员 |
| GET | `/api/v1/tenants/{id}` | 租户详情 | 租户管理员 |
| PUT | `/api/v1/tenants/{id}` | 更新租户 | 租户管理员 |
| DELETE | `/api/v1/tenants/{id}` | 删除租户 | 超级管理员 |
| GET | `/api/v1/tenants/{id}/users` | 租户用户列表 | 租户管理员 |
| POST | `/api/v1/tenants/{id}/users` | 邀请用户 | 租户管理员 |
| PUT | `/api/v1/tenants/{id}/quota` | 更新配额 | 超级管理员 |
| GET | `/api/v1/tenants/{id}/usage` | 使用统计 | 租户管理员 |
| GET | `/api/v1/tenants/{id}/billing` | 计费信息 | 租户管理员 |

#### 16.2.6 权限模型

```
┌─────────────────────────────────────────────────────────────────┐
│                      多租户权限模型                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   权限层级: 超级管理员 > 租户管理员 > 租户成员 > 租户查看者        │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  超级管理员 (Super Admin)                               │   │
│   │  - 管理所有租户                                         │   │
│   │  - 跨租户数据访问                                       │   │
│   │  - 系统配置                                             │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  租户管理员 (Tenant Admin)                              │   │
│   │  - 管理本租户用户                                       │   │
│   │  - 管理本租户本体和图谱                                 │   │
│   │  - 配置租户设置                                         │   │
│   │  - 查看本租户使用统计                                   │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  租户成员 (Tenant Member)                               │   │
│   │  - 使用本体和推理服务                                   │   │
│   │  - 管理自己创建的本体                                   │   │
│   │  - 不可管理其他用户                                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  租户查看者 (Tenant Viewer)                             │   │
│   │  - 只读访问                                             │   │
│   │  - 不可修改任何资源                                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 16.2.7 隔离实现

| 层级 | 隔离方式 |
|------|----------|
| **数据库** | PostgreSQL Schema隔离 |
| **图数据库** | Neo4j节点label + property过滤 |
| **文件存储** | 租户目录隔离 (tenant_id/) |
| **缓存** | Redis key添加租户前缀 |
| **消息队列** | 租户topic隔离 |

#### 16.2.8 配额管理

| 配额项 | 免费版 | 专业版 | 企业版 |
|--------|--------|--------|--------|
| 每日API调用 | 100 | 5,000 | 无限制 |
| 最大实体数 | 1,000 | 50,000 | 无限制 |
| 最大本体数 | 3 | 20 | 无限制 |
| 图数据库存储 | 100MB | 5GB | 无限制 |
| 用户数 | 3 | 20 | 无限制 |
| 自定义域名 | ❌ | ✅ | ✅ |
| SSO集成 | ❌ | ❌ | ✅ |
| 专属支持 | ❌ | 邮件 | 7x24 |

---

### 16.3 国际化与多租户结合

#### 16.3.1 设计原则

| 原则 | 说明 |
|------|------|
| 租户级语言设置 | 每个租户可设置默认语言 |
| 用户级语言覆盖 | 用户可覆盖租户默认设置 |
| 本体语言独立 | 本体多语言与界面语言独立配置 |
| 租户资源隔离 | 翻译资源也按租户隔离 |

#### 16.3.2 配置流程

```
1. 超级管理员创建租户 → 设置默认语言
2. 租户管理员配置租户 → 上传logo、设置域名
3. 用户登录 → 继承租户语言，可自行切换
4. 本体管理 → 实体支持多语言标签
```

---

## 十七、版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| V1.0 | 2026-03-15 | 初始版本 |
| V2.0 | 2026-03-16 | 完善功能需求、技术架构、API设计 |
| V2.1 | 2026-03-17 | 补充数据分析模块、报表导出模块 |
| V2.2 | 2026-03-17 | 补充国际化设计、多租户支持 |

---

**文档版本**: V2.2  
**创建日期**: 2026-03-16  
**最后更新**: 2026-03-17 00:25  
**状态**: 已完成
