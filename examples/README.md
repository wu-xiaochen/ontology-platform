# Clawra Engine 示例集

本目录包含 Clawra 自主进化 Agent 框架的完整示例代码，涵盖核心功能模块。所有示例均为真实可运行的代码（非占位符）。

---

## 快速开始

```bash
cd /Users/xiaochenwu/Desktop/ontology-platform
python examples/demo_basic.py
```

---

## 核心示例（推荐入门）

| 示例文件 | 功能 | 难度 |
|---------|------|------|
| `demo_basic.py` | Clawra 基础用法：学习、推理、检索、统计 | ⭐ |
| `demo_evolution_loop.py` | 8 阶段自主进化闭环演示 | ⭐⭐⭐ |
| `demo_graphrag.py` | GraphRAG 多模式检索（Local/Global/Hybrid） | ⭐⭐⭐ |
| `demo_pattern_versioning.py` | Pattern 版本管理、回滚、合并 | ⭐⭐⭐⭐ |
| `demo_leiden_community.py` | Leiden 社区检测与跨社区推理 | ⭐⭐⭐⭐ |

---

## 示例详解

### 1. demo_basic.py — 基础用法

**功能覆盖：** Clawra 核心 API 的入门演示。

**运行：**
```bash
python examples/demo_basic.py
```

**步骤说明：**

```
[Step 1] 初始化 Clawra
    创建 Clawra 实例，内部自动初始化推理引擎、知识图谱、GraphRAG 检索器等组件。

[Step 2] 从文本学习知识
    调用 clawra.learn(text, domain_hint) 从一段燃气调压箱文本中自动提取：
    - 实体（调压箱、调压器、安全阀）
    - 关系（位于、包含、需要）
    - 模式（定期维护规则）
    - 自动生成事实三元组写入推理引擎

[Step 3] 手动添加事实三元组
    调用 clawra.add_fact(subject, predicate, object, confidence) 手动添加：
    - 调压箱A is_a 燃气调压箱
    - 调压箱A 位于 住宅小区
    - ...

[Step 4] 执行前向链推理
    调用 clawra.reason(max_depth=3) 执行确定性前向链推理：
    - 从已有事实出发，推导隐含结论
    - 零 LLM 依赖，无幻觉

[Step 5] 查询学习到的模式
    调用 clawra.query_patterns(domain=...) 按领域/类型/关键词过滤已学习的模式。

[Step 6] GraphRAG 知识检索
    调用 clawra.retrieve_knowledge(query, top_k, modes=["entity","semantic"])
    - 多路召回（实体检索 + 语义检索）
    - RRF 融合排序

[Step 7] 系统统计信息
    调用 clawra.get_statistics() 获取：
    - 事实总数、图谱统计、模式统计
```

**预期输出：**
```
[Step 1] 初始化 Clawra...
  ✓ Clawra 初始化完成
[Step 2] 从文本学习知识...
  ✓ 学习完成: success=True
    - 提取的实体数: 5
    - 提取的关系数: 4
    - 自动生成事实数: 4
[Step 3] 手动添加事实三元组...
  ✓ 添加了 4 条事实三元组
[Step 4] 执行前向链推理...
  ✓ 推理完成，发现 3 条结论
    → 调压箱A 是 燃气设备
    → 调压箱A 需要 定期维护
    ...
[Step 5] 查询学习到的模式...
  ✓ 找到 2 个相关模式:
    [rule] gas_maintenance_rule: 调压箱应定期维护检查...
[Step 6] GraphRAG 知识检索...
  ✓ 检索到 5 条相关知识:
    [entity] (调压箱, 需要, 定期维护) score=0.923
[Step 7] 系统统计信息...
  ✓ 事实总数: 12
  ✓ 图谱统计: {'node_count': 8, 'edge_count': 12}
```

---

### 2. demo_evolution_loop.py — 进化闭环演示

**功能覆盖：** EvolutionLoop 8 阶段自主进化闭环的完整演示。

**运行：**
```bash
python examples/demo_evolution_loop.py
```

**步骤说明：**

```
[Step 1] 初始化组件
    从 Clawra 实例中提取所需组件（MetaLearner, RuleDiscovery,
    Evaluator, Reasoner, LogicLayer, ContradictionChecker），
    构造 EvolutionLoop 实例。

[Step 2] 单步执行各进化阶段
    演示通过 loop.step({...}) 逐阶段执行：
    - PERCEIVE: 解析输入文本，提取结构化信息
    - LEARN:    调用 MetaLearner 从文本中发现逻辑模式
    - REASON:   执行前向链推理
    - EXECUTE:  应用规则动作
    每个阶段返回 PhaseResult，包含 success、duration、data、error。

[Step 3] 执行完整进化闭环
    调用 loop.run(input_data) 自动按顺序执行全部 8 个阶段：
    - PERCEIVE → LEARN → REASON → EXECUTE
    - EVALUATE → DETECT_DRIFT → REVISE_RULES → UPDATE_KG
    返回完整执行报告（episode_id、迭代次数、各阶段结果、反馈信号）。

[Step 4] 注册阶段回调钩子
    通过 loop.register_hook(EvolutionPhase, callback_fn) 注册回调。
    每次对应阶段执行后自动触发回调，收集执行信息。

[Step 5] 再次执行并触发回调
    验证回调钩子机制，记录触发次数。

[Step 6] 知识质量评估
    调用 clawra.evaluate_knowledge() 执行：
    - 生命周期转换（CANDIDATE → ACTIVE → STALE → ARCHIVED）
    - 置信度衰减
    - 质量评分
```

**预期输出：**
```
[Step 3] 执行完整进化闭环...
  闭环执行结果:
    episode_id: demo_ep_001
    迭代次数: 8
    是否收敛: True
    整体成功: True
    反馈信号数: 0
  各阶段执行情况:
    ✅ perceive: 0.012s | {'text': '调压箱需要配备安全阀...'} | ...
    ✅ learn: 0.234s | {'patterns_created': [...]} | ...
    ✅ reason: 0.089s | {'conclusions': [...]} | ...
    ...
```

---

### 3. demo_graphrag.py — GraphRAG 检索

**功能覆盖：** GraphRAG 多层次检索系统的完整演示。

**运行：**
```bash
python examples/demo_graphrag.py
```

**步骤说明：**

```
[Step 1] 初始化并构建知识图谱
    创建 Clawra 实例，添加 20 条燃气领域事实三元组，
    涵盖设备组件、压力等级、维护规则、地理位置等维度。

[Step 2] Entity Search（实体检索）
    调用 clawra.retrieve_knowledge(query="调压器", modes=["entity"])
    - 精确/模糊匹配实体名称
    - 返回关联的三元组子图

[Step 3] Semantic Search（语义检索）
    调用 clawra.retrieve_knowledge(query="设备维护 周期 检查", modes=["semantic"])
    - 基于 TF-IDF 文本相似度
    - 不依赖关键词精确匹配

[Step 4] Hybrid Search（混合检索）
    调用 clawra.retrieve_knowledge(query="调压箱 维护", modes=["entity","semantic"])
    - 多路召回 + Reciprocal Rank Fusion (RRF) 融合排序
    - 综合多维度分数（相关性、置信度、新鲜度、访问频率）

[Step 5] Local Search（局部搜索）
    调用 retriever.local_search(query, center_entity, top_k)
    - 以指定实体为中心，通过 BFS 扩展邻居子图
    - 适合细粒度的实体关联查询

[Step 6] Global Search（全局搜索）
    调用 retriever.global_search(query, top_k)
    - 先进行社区检测（Leiden/Louvain）
    - 在社区粒度上进行摘要检索
    - 适合高层次概念性问题

[Step 7] 构建 LLM 上下文
    调用 clawra.retrieve_context(query, top_k)
    - 将检索结果组装为 LLM 可消费的结构化文本
    - 按相关性排序，截断到 token 限制

[Step 8] 检索使用追踪
    查看 evaluator 的使用追踪统计，
    每次 retrieve_knowledge 命中的知识都会记录到使用追踪中。
```

**预期输出：**
```
[Step 4] Hybrid Search（混合检索）...
  ✓ 检索到 10 条结果 (RRF 融合排序):
    [entity] (调压箱, 需要, 定期维护)
        综合分=0.923 相关性=0.950 置信度=0.920
[Step 6] Global Search（全局搜索）...
  ✓ 全局搜索找到 5 条结果:
    [社区0] (调压箱, contains, 调压器) score=0.912
    [社区0] (调压箱, contains, 安全阀) score=0.895
    [社区1] (高压燃气, pressure_range, 0.4-1.6MPa) score=0.887
```

---

### 4. demo_pattern_versioning.py — Pattern 版本控制

**功能覆盖：** UnifiedLogicLayer 的 Pattern 版本管理全流程。

**运行：**
```bash
python examples/demo_pattern_versioning.py
```

**步骤说明：**

```
[Step 1] 初始化
    创建 Clawra，访问 logic_layer (UnifiedLogicLayer 实例)。

[Step 2] 添加初始 Pattern (v1)
    手动构造 LogicPattern 对象（包含 conditions、actions），
    调用 logic_layer.add_pattern(pattern) 写入存储。
    Pattern 结构：id、logic_type（rule/behavior/policy/constraint）、
    name、description、conditions、actions、confidence、domain、version。

[Step 3] 更新 Pattern（自动创建 v2）
    同一 ID 再次 add_pattern(新版)：
    - 旧版本自动归档到 _pattern_history
    - 版本号从 1 升至 2
    - 置信度根据历史使用动态调整

[Step 4] 添加更多 Pattern
    添加 3 个额外 Pattern，涵盖维护规则和校验规则，
    模拟真实场景中多个并发规则。

[Step 5] 获取 Pattern 版本历史
    调用 logic_layer.get_pattern_history(pattern_id)
    返回该 ID 的所有历史版本列表（按 version 排序）。

[Step 6] 对比两个版本
    调用 logic_layer.compare_versions(pattern_id, v1, v2)
    返回两版本间的差异字段（description、conditions、actions、confidence）。

[Step 7] 回滚到指定版本
    调用 logic_layer.rollback_pattern(pattern_id, target_version=1)
    - 从历史记录恢复目标版本
    - 当前版本切换为目标版本
    - 返回操作是否成功

[Step 8] 检测冗余 Pattern
    调用 logic_layer.find_redundant_patterns()
    - 发现条件/动作高度相似的 Pattern 对
    - 支持后续合并操作

[Step 9] 合并相似 Pattern (dry-run)
    调用 logic_layer.merge_similar_patterns(threshold=0.8, dry_run=True)
    - dry_run=True 只返回候选，不实际合并
    - 返回 (pattern_a_id, pattern_b_id, similarity) 列表

[Step 10] 查看所有 Pattern
    遍历 logic_layer.patterns 查看当前所有活跃 Pattern。

[Step 11] 统计信息
    调用 logic_layer.get_statistics() 获取：
    - total_patterns、by_type、by_domain 等聚合统计
```

**预期输出：**
```
[Step 5] 获取 Pattern 版本历史...
  ✓ gas_pressure_rule_v1 共有 2 个历史版本:
    v1: 调压箱出口压力不得超过 0.4MPa (置信度: 0.85)
    v2: 调压箱出口压力不得超过 0.35MPa（已修订... (置信度: 0.90)
[Step 7] 回滚到 v1...
  ✓ 回滚: 成功
    当前版本: 1
[Step 9] 合并相似 Pattern (dry-run)...
  ✓ 建议合并 1 对 Pattern:
    - Pattern A: maintenance_rule_001
      Pattern B: maintenance_rule_002
      相似度: 0.857
```

---

### 5. demo_leiden_community.py — Leiden 社区检测

**功能覆盖：** KnowledgeGraph 社区检测与跨社区推理。

**运行：**
```bash
python examples/demo_leiden_community.py
```

**注意：** Leiden 算法需要安装 `leidenalg` 和 `igraph`：
```bash
pip install leidenalg igraph
```
如果未安装，会自动回退到 Louvain 算法（无需手动处理）。

**步骤说明：**

```
[Step 1] 初始化知识图谱
    直接创建 KnowledgeGraph 实例（不依赖 Clawra 高级封装）。

[Step 2] 构建燃气领域知识图谱
    人工构建 4 个语义社区（共 39 条三元组）：
    - 设备社区（调压箱 contains 调压器/安全阀/阀门/压力表）
    - 压力等级社区（高压/中压/低压燃气，reduce 关系）
    - 维护社区（requires 定期维护/校验，维护周期）
    - 地点社区（调压站、住宅小区、工业园区，located_at）

[Step 3] 图谱统计信息
    调用 kg.statistics() 查看 node_count、edge_count、triple_count。

[Step 4] Leiden 社区检测
    调用 kg.detect_communities(algorithm="leiden")：
    - Leiden 是 Louvain 的改进版本，保证社区连接性
    - 更快的收敛速度和更高的模块度
    - 返回 Community 对象列表，每个包含 id、entities、size、triple_count

[Step 5] 其他算法对比
    分别使用 louvain 和 label_propagation 算法检测社区，
    展示不同算法的检测结果差异。

[Step 6] 生成社区摘要
    调用 kg.generate_community_summaries()
    - 为每个社区生成描述性摘要
    - 包含核心实体、高频谓词、社区规模等信息

[Step 7] 跨社区推理
    调用 kg.cross_community_reasoning(entity_a, entity_b, max_hops)：
    - 查询两个实体之间的所有连通路径（最多 3 跳）
    - 展示跨社区的语义关联（如"住宅小区"如何关联到"调压器"）

[Step 8] 查询实体社区归属
    调用 kg.get_entity_community(entity)
    - 快速查询某实体属于哪个社区

[Step 9] 获取社区成员
    调用 kg.get_community_members(community_id)
    - 列出指定社区内的所有实体成员

[Step 10] 社区级别知识检索
    调用 kg.get_community_triples(community_id)
    - 获取社区内所有三元组，用于社区粒度的知识查询
```

**预期输出：**
```
[Step 4] Leiden 社区检测...
  Leiden 可用: 是
  ✓ 检测到 4 个社区:
    社区 0: ['调压箱', '调压器', '安全阀', '阀门', '压力表']... (size=12)
    社区 1: ['高压燃气', '中压燃气', '低压燃气', '调压器']... (size=9)
    社区 2: ['维护周期', '校验周期', '调压箱', '安全阀']... (size=9)
    社区 3: ['住宅小区', '工业园区', '调压箱A', '调压箱B']... (size=9)
[Step 7] 跨社区推理...
  ✓ 调压箱A <-> 高压燃气 找到 2 条关联路径:
    路径 1: 调压箱A -> connect -> 高压燃气
    路径 2: 调压箱A -> is_a -> 燃气设备 -> connect -> 高压燃气
```

---

## 环境配置

```bash
# 安装依赖
cd /Users/xiaochenwu/Desktop/ontology-platform
pip install -r requirements.txt

# 可选：安装 Leiden 算法依赖（用于 demo_leiden_community.py）
pip install leidenalg igraph

# 环境变量（可选，部分功能需要）
# 在 .env 文件中配置：
# MINIMAX_API_KEY=your_api_key_here
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password
```

---

## 目录结构

```
examples/
├── README.md                      # 本文件
├── demo_basic.py                  # 基础用法 ⭐
├── demo_evolution_loop.py         # 进化闭环 ⭐⭐⭐
├── demo_graphrag.py               # GraphRAG 检索 ⭐⭐⭐
├── demo_pattern_versioning.py     # Pattern 版本控制 ⭐⭐⭐⭐
├── demo_leiden_community.py       # Leiden 社区检测 ⭐⭐⭐⭐
├── demo_supplier_monitor.py       # 供应商监控业务场景
├── demo_confidence_reasoning.py   # 置信度推理
├── full_demo.py                   # 完整功能演示
├── full_agent_demo.py             # Agent 完整演示
├── streamlit_app.py               # Web 可视化应用
└── archive/                       # 历史示例（参考）
```

---

## 扩展阅读

- 核心框架：`src/clawra.py` — Clawra 主类
- 进化引擎：`src/evolution/evolution_loop.py` — EvolutionLoop
- 知识图谱：`src/core/knowledge_graph.py` — KnowledgeGraph
- 检索引擎：`src/core/retriever.py` — GraphRetriever
- 逻辑层：`src/evolution/unified_logic.py` — UnifiedLogicLayer
