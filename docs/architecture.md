# ontology-platform 架构文档

**版本**：v1.0
**更新**：2026-03-19
**状态**：愿景版

---

## 核心理念

```
孩子成长 = 经验(记忆) + 逻辑推理 + 因果认知 + 元认知
                    ↓
Agent成长 = 本体记忆 + 逻辑推理引擎 + 因果推理 + 置信度自知
```

## 为什么需要ontology-platform？

### 当前Agent的困境

| 能力来源 | 问题 |
|---------|------|
| 训练 | 太慢、无法实时学习 |
| Fine-tuning | 成本高、可能遗忘原有能力 |
| RAG | 只是检索，没有推理 |
| 知识图谱 | 静态，无法主动学习 |

**核心问题**：Agent无法像孩子一样在运行中成长。

### 解决方案

让Agent拥有：
1. **实时学习** - 运行中获取新知识
2. **结构化推理** - 而非纯概率匹配
3. **元认知** - 知道自己知道什么
4. **幻觉消除** - 通过置信度约束

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ontology-platform                         │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Memory    │  │  Reasoning  │  │   Meta      │       │
│  │   System    │  │   Engine    │  │  Cognition  │       │
│  │  (记忆层)    │  │  (推理层)   │  │  (元认知层)  │       │
│  └──────┬──────┘  └──────┬─────┘  └──────┬──────┘       │
│         │                │                 │              │
│         └────────────────┼─────────────────┘              │
│                          │                                  │
│                   ┌──────▼──────┐                        │
│                   │   Core API   │                        │
│                   │   (核心API)   │                        │
│                   └──────┬──────┘                        │
│                          │                                  │
│         ┌────────────────┼────────────────┐              │
│         │                │                │              │
│   ┌─────▼─────┐  ┌──────▼──────┐  ┌──────▼──────┐      │
│   │    MCP     │  │    REST     │  │    SDK      │      │
│   │  Protocol  │  │    API      │  │  Python/JS  │      │
│   └───────────┘  └─────────────┘  └─────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 模块1：Memory-System（记忆层）

### 功能
- 本体存储：OWL/RDF格式的结构化知识
- 向量索引：语义相似性检索
- 动态衰减：模拟人类遗忘机制

### 核心数据结构

```python
class OntologyConcept:
    id: str                    # 唯一标识
    name: str                  # 概念名称
    properties: dict           # 属性
    relations: list[Relation]  # 关系
    confidence: float          # 置信度 0-1
    source: str                # 来源
    learned_at: datetime        # 学习时间
    last_accessed: datetime    # 最后访问

class Rule:
    id: str
    antecedent: str            # 前提条件
    consequent: str            # 结论
    confidence: float          # 规则置信度
    applicability: str           # 适用范围
```

### 存储引擎
- **主存储**：SQLite + RDFlib（轻量级）
- **可选升级**：Neo4j（图数据库）
- **向量索引**：ChromaDB（语义检索）

---

## 模块2：Reasoning-Engine（推理层）

### 功能
- 规则引擎：正向/反向链推理
- 因果推理：链追溯、可解释
- 置信度传播：概率更新

### 推理类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `logical` | 规则匹配 | "如果高风险供应商 → 找备选" |
| `causal` | 因果追溯 | "为什么质量下降？根因是什么？" |
| `abductive` | 假设推理 | "结果X，最可能的原因是什么？" |
| `analogical` | 类比推理 | "类似情况过去怎么处理？" |

### 推理链示例

```
Query: "为什么这批零件质量下降？"

推理链：
Step 1: 质量下降 → 供应商问题 (confidence: 0.92)
  依据: 历史数据中3次同类事件

Step 2: 供应商问题 → 原材料问题 (confidence: 0.78)
  依据: 规则"原材料问题 → 质量下降"

Step 3: 原材料问题 → 天气影响 (confidence: 0.65)
  依据: 本周暴雨记录

最终结论：可能由天气导致原材料问题，进而影响质量
置信度：0.65
建议行动：检查原材料储备 + 天气对供应链影响评估
```

---

## 模块3：Meta-Cognition（元认知层）

### 功能
- 置信度自知：知道自己多确定
- 知识边界：知道自己不知道什么
- 推理自省：能解释推理路径

### 核心机制

```python
class MetaCognition:
    def evaluate_confidence(self, query: str, answer: str) -> float:
        """评估答案的置信度"""
        # 检查知识边界
        # 检查推理链完整性
        # 检查历史准确率
        return confidence  # 0-1

    def identify_knowledge_boundary(self, query: str) -> bool:
        """判断问题是否超出知识边界"""
        return is_out_of_boundary

    def explain_reasoning(self, reasoning_id: str) -> Explanation:
        """返回推理过程的可解释说明"""
        return Explanation(
            steps=[...],
            confidence_per_step=[...],
            final_confidence=...,
            alternative_paths=[...]
        )
```

### 元认知输出示例

```
Query: "量子计算的未来是什么？"

元认知响应：
├── 置信度自知：0.45（我对这个领域不确定）
├── 知识边界：量子物理、量子算法 - 非核心知识区
├── 推理自省：无法进行因果推理（缺乏领域规则）
└── 建议：查阅专业论文 + 咨询量子计算专家
```

---

## API设计

### Core API

```python
# 学习
POST /api/v1/learn
{
    "concept": {...},
    "rule": {...},      # 可选
    "confidence": 0.85,
    "source": "user:采购专家对话"
}

# 推理
POST /api/v1/reason
{
    "query": "为什么质量下降？",
    "type": "causal",      # logical | causal | abductive | analogical
    "trace": True,
    "confidence_threshold": 0.6
}

# 元认知
POST /api/v1/metacognition/evaluate
{
    "query": "...",
    "answer": "..."
}

# 知识检索
GET /api/v1/search
{
    "query": "供应商风险",
    "top_k": 10,
    "include_confidence": True
}
```

---

## 接入协议

### MCP Protocol

```json
{
  "mcpServer": {
    "name": "ontology-platform",
    "version": "1.0.0",
    "capabilities": {
      "memory": {
        "learn": true,
        "retrieve": true,
        "forget": true
      },
      "reasoning": {
        "logical": true,
        "causal": true,
        "abductive": true,
        "analogical": true
      },
      "metacognition": {
        "confidence": true,
        "knowledge_boundary": true,
        "explain": true
      }
    }
  }
}
```

---

## 技术栈

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| 本体存储 | RDFlib + SQLite | 轻量级、标准化 |
| 图数据库 | Neo4j（可选）| 生产级扩展 |
| 向量索引 | ChromaDB | 轻量、嵌入式 |
| 推理引擎 | 自研 + Jina | 因果推理 |
| API框架 | FastAPI | Python原生、高性能 |
| SDK | Python + TypeScript | 双语言支持 |

---

## 路线图

详见 [roadmap.md](roadmap.md)

---

*最后更新：2026-03-19*
