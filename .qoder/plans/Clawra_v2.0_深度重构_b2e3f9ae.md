# Clawra v2.0 — 轻量级自进化知识引擎深度重构

## 一、现状诊断（基于代码逐行分析）

### 致命缺陷

| # | 模块 | 问题 | 影响 |
|---|------|------|------|
| 1 | `Reasoner.facts` (list) | 线性扫描 O(n)，无索引 | 1000+ 事实时推理严重退化 |
| 2 | `UnifiedMemory` (manager.py) | 6个核心方法全是 `pass` 占位符 | 记忆系统形同虚设 |
| 3 | 知识检索 (`query_patterns`) | 遍历所有 patterns 做 keyword.lower() in desc | 无语义理解，召回率极低 |
| 4 | Reasoner ↔ LogicLayer | 两套独立知识体系，互不通信 | 学到的 LogicPattern 无法参与推理 |
| 5 | 外部依赖 Neo4j | 必须运行 Neo4j 实例才有图能力 | 违背"轻量可嵌入 SDK"定位 |
| 6 | 无反馈闭环 | learn() 写入后无评估、无淘汰、无优化 | 知识只增不减，噪声累积 |

### 架构差距 vs 行业标杆

| 能力维度 | Clawra 现状 | LightRAG/Palantir 标杆 | 差距 |
|---------|------------|----------------------|------|
| 知识存储 | list + dict | 嵌入式图 + 向量双索引 | 巨大 |
| 检索方式 | 关键词遍历 | 实体级+关系级双层 Graph-RAG | 巨大 |
| 推理引擎 | 字符串模式匹配 | 类型化三元组 + 索引推理 | 中等 |
| 自进化 | 单向写入 | 反馈→评估→淘汰→优化闭环 | 巨大 |
| 动作层 | LogicPattern 无执行力 | Kinetic Ontology 动态操作 | 大 |

---

## 二、目标架构 — 三层引擎 (Semantic → Kinetic → Dynamic)

参考 Palantir 三层本体 + LightRAG 双层检索 + CORAL 自进化：

```
┌─────────────────────────────────────────────────┐
│             Dynamic Layer (自进化层)              │
│  反馈闭环 · 知识淘汰 · 策略优化 · 自主进化        │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────┐
│             Kinetic Layer (动作层)                │
│  工具注册 · Action执行 · 规则触发 · 副作用管理     │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────┐
│           Semantic Layer (语义知识层)              │
│  嵌入式图 · 向量索引 · 双层检索 · 类型化三元组     │
└─────────────────────────────────────────────────┘
```

---

## 三、实施计划 — 6 个 Phase，渐进式重构

### Phase 1: 嵌入式知识图谱引擎 (替代 Neo4j + list)
> 目标：零外部依赖的高性能图存储，替代 Reasoner.facts 和 Neo4j

**Task 1.1: 构建 `KnowledgeGraph` 核心类**
- 文件: `src/core/knowledge_graph.py` (新建)
- 基于 NetworkX DiGraph 构建轻量图引擎
- 核心数据结构：
  - `TypedTriple(subject, predicate, object, confidence, source, timestamp, metadata)`
  - 三级索引：SPO索引（subject→triples）、PO索引（predicate→triples）、OS索引（object→triples）
- 核心方法：
  - `add_triple()` — O(1) 索引写入，自动去重+置信度合并
  - `query(subject?, predicate?, object?, min_confidence?)` — 索引加速查询
  - `neighbors(entity, depth, direction)` — BFS图遍历
  - `subgraph(entities)` — 子图提取
  - `merge(other_graph)` — 图合并
  - `serialize() / deserialize()` — JSON持久化
- 性能目标：10万三元组 < 50MB内存，查询 < 1ms

**Task 1.2: 重构 Reasoner 使用 KnowledgeGraph**
- 文件: `src/core/reasoner.py` (重构)
- 将 `self.facts: list[Fact]` 替换为 `self.graph: KnowledgeGraph`
- `add_fact()` → `graph.add_triple()`
- `query()` → `graph.query()` (索引加速)
- `forward_chain()` 使用索引匹配规则，避免全量扫描
- 保持 API 向后兼容

**Task 1.3: 迁移 Clawra 主类**
- 文件: `src/clawra.py` (修改)
- `self.reasoner` 的 facts 操作无缝切到图引擎
- 废弃 `UnifiedMemory` 的 Neo4j 依赖
- 确保 187 个测试全部通过

---

### Phase 2: Graph-RAG 双层检索 (替代关键词遍历)
> 参考 LightRAG 的实体级+关系级检索

**Task 2.1: 构建 `GraphRetriever` 检索器**
- 文件: `src/core/retriever.py` (新建)
- 实现三种检索模式：
  1. **实体检索** — 精确/模糊匹配实体，返回其关联子图
  2. **关系检索** — 按谓词类型检索三元组链
  3. **语义检索** — 基于文本相似度的向量检索 (可选，依赖 embedding)
- 检索融合：多路召回 + 置信度加权排序
- 轻量实现：不依赖外部向量库，使用 TF-IDF 或简单 embedding 做文本匹配

**Task 2.2: 实现 `ContextBuilder` 上下文构建器**
- 文件: `src/core/retriever.py` (同文件)
- 将检索结果组装为 LLM 可消费的结构化上下文
- 格式：`[实体定义] + [相关关系] + [适用规则]`
- 上下文窗口管理：按相关性排序，截断到 token 限制

**Task 2.3: 重构 Clawra 的知识查询流程**
- 修改 `query_patterns()` 使用 GraphRetriever
- 修改 Agent 对话中的知识检索，从遍历改为图检索
- 在 demo 中展示检索命中率提升

---

### Phase 3: 统一知识表示 (合并 Reasoner + LogicLayer)
> 消除两套独立知识体系

**Task 3.1: 统一 `TypedTriple` 和 `LogicPattern`**
- LogicPattern 的 conditions/actions 转化为图中的规则节点
- 规则节点通过特殊谓词 (`_condition_of`, `_action_of`) 关联到图中
- 查询规则 = 查询图中的规则子图

**Task 3.2: 重构 UnifiedLogicLayer 为图的视图层**
- `UnifiedLogicLayer` 不再独立存储 patterns，而是读写 KnowledgeGraph
- `add_pattern()` → 在图中创建规则节点 + 关系边
- `get_patterns_by_domain()` → 图查询
- 保持接口兼容

**Task 3.3: 废弃 UnifiedMemory (manager.py)**
- KnowledgeGraph 内置持久化，替代 UnifiedMemory 的所有功能
- 删除或标记为 deprecated

---

### Phase 4: 反馈闭环自进化 (参考 CORAL + SEAgent)
> 从"只写不评"升级为"写入→评估→淘汰→优化"

**Task 4.1: 知识质量评估器 `KnowledgeEvaluator`**
- 文件: `src/evolution/evaluator.py` (新建)
- 评估维度：
  - **一致性**: 新知识是否与已有知识矛盾
  - **冗余度**: 是否已存在语义等价的知识
  - **置信度衰减**: 长期未被引用的知识自动降权
  - **引用频率**: 被推理/检索引用的次数
- 输出：knowledge_score (0-1)

**Task 4.2: 知识生命周期管理**
- 知识状态机: `CANDIDATE → ACTIVE → STALE → ARCHIVED`
- 新学到的知识初始为 CANDIDATE，经评估后升为 ACTIVE
- 长期未引用自动降为 STALE，最终 ARCHIVED
- 置信度 < 阈值的知识自动清理

**Task 4.3: 学习效果反馈回路**
- 在 `learn()` 返回后，追踪该知识在后续推理/检索中的使用情况
- 用使用频率和成功率反向调整 MetaLearner 的策略权重
- 实现 `provide_feedback()` 的真实闭环

---

### Phase 5: Kinetic Layer 动作引擎 (参考 Palantir)
> 让 LogicPattern 真正可执行

**Task 5.1: 轻量 Action Runtime**
- 文件: `src/core/action_runtime.py` (新建)
- 支持的动作类型：
  - `infer`: 推导新三元组（已有）
  - `notify`: 触发通知/webhook
  - `validate`: 校验数据是否满足约束
  - `transform`: 数据格式转换
  - `execute`: 调用注册的 Python 函数
- 沙箱执行：所有动作在受限环境中运行

**Task 5.2: 事件驱动触发**
- 当图中写入新三元组时，自动匹配 condition 触发规则
- 实现 `on_triple_added` 钩子
- 支持规则链（一个规则的 action 触发另一个规则的 condition）

---

### Phase 6: 性能优化 + 测试加固
> 确保重构后性能和稳定性

**Task 6.1: 性能基准测试**
- 补充 benchmark：1K/10K/100K 三元组的写入/查询/推理耗时
- 对比重构前后的性能数据
- 目标：查询 < 1ms，推理 < 100ms (1K 事实)

**Task 6.2: 测试覆盖**
- 为所有新模块编写单元测试
- 确保原有 187 个测试不回退
- 集成测试：完整的 learn → store → retrieve → reason → feedback 流程

**Task 6.3: Demo 更新**
- 更新 clawra_demo.py 展示新能力
- 新增"知识图谱可视化"Tab（使用 networkx + matplotlib）
- 新增"检索对比"面板（关键词 vs Graph-RAG）

---

## 四、实施优先级和依赖关系

```
Phase 1 (知识图谱) ──→ Phase 2 (Graph-RAG检索) ──→ Phase 3 (统一表示)
                                                         │
                                                         ▼
                                                   Phase 4 (自进化闭环)
                                                         │
                                                         ▼
                                                   Phase 5 (动作引擎)
                                                         │
                                                         ▼
                                                   Phase 6 (性能+测试)
```

Phase 1 是地基，必须首先完成。Phase 2-3 紧密耦合可并行设计。Phase 4-5 是高阶能力。Phase 6 贯穿始终。

## 五、技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 嵌入式图 | NetworkX DiGraph + 自定义索引 | 零依赖，纯Python，足够轻量 |
| 持久化 | JSON Lines (.jsonl) | 人类可读，增量写入，无数据库依赖 |
| 向量检索 | 内置 TF-IDF (可选 sentence-transformers) | 轻量优先，重依赖可选 |
| LLM | OpenAI-compatible API (不变) | 保持兼容 VolcEngine/OpenAI |
| 测试 | pytest (不变) | 项目已有完善的测试体系 |

## 六、预计代码改动量

| Phase | 新增文件 | 修改文件 | 预计代码行 |
|-------|---------|---------|-----------|
| 1 | 1 (knowledge_graph.py) | 2 (reasoner.py, clawra.py) | ~500 |
| 2 | 1 (retriever.py) | 2 (clawra.py, demo) | ~400 |
| 3 | 0 | 3 (unified_logic.py, clawra.py, manager.py) | ~300 |
| 4 | 1 (evaluator.py) | 2 (meta_learner.py, clawra.py) | ~350 |
| 5 | 1 (action_runtime.py) | 1 (unified_logic.py) | ~300 |
| 6 | 0 | 3 (benchmark, tests, demo) | ~400 |
| **合计** | **4 新文件** | **~10 文件修改** | **~2250 行** |

## 七、立即可执行的 Phase 1 详细规格

Phase 1 Task 1.1 的 `KnowledgeGraph` 类核心接口：

```python
class KnowledgeGraph:
    """轻量级嵌入式知识图谱引擎"""
    
    def __init__(self, persist_path: Optional[str] = None):
        self._graph = nx.DiGraph()           # NetworkX 有向图
        self._spo_index: Dict[str, Set]      # subject → triple_ids
        self._po_index: Dict[str, Set]       # predicate → triple_ids
        self._os_index: Dict[str, Set]       # object → triple_ids
        self._triples: Dict[str, TypedTriple] # id → triple
    
    def add_triple(self, s, p, o, confidence=0.9, source="learned", metadata=None) -> str
    def remove_triple(self, triple_id: str) -> bool
    def query(self, s=None, p=None, o=None, min_conf=0.0) -> List[TypedTriple]
    def neighbors(self, entity: str, depth=1, direction="both") -> SubGraph
    def entities(self) -> Set[str]
    def predicates(self) -> Set[str]
    def subgraph(self, entities: Set[str]) -> 'KnowledgeGraph'
    def merge(self, other: 'KnowledgeGraph') -> int
    def save(self, path: str) -> None
    def load(self, path: str) -> None
    def statistics(self) -> Dict[str, Any]
```

准备好后，请确认是否开始 Phase 1 的实现。
