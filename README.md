# ontology-platform

> 让每个Agent都拥有真正的成长能力。

## 🎯 是什么

**ontology-platform** 是一个Agent成长框架。

类比：它是Agent的"大学"——Agent在运行中通过三大特性成长，而非等待下一次训练。

```
孩子成长 = 经验(记忆) + 逻辑推理 + 因果认知 + 元认知
                    ↓
Agent成长 = 本体记忆 + 逻辑推理引擎 + 因果推理 + 置信度自知
```

## 🔥 三大核心能力

### 1. 学习特性
本体能够自学习、自更新、自构建——Agent在运行中学习物理规律，实时进化。

```python
# Agent运行中学习新规则
ontology.learn(
    concept="供应商风险",
    rule=Rule("高风险供应商 → 增加备选"),
    confidence=0.85,
    source="history:采购失败案例"
)
```

### 2. 推理能力
结构化逻辑推理 + 因果推理，让Agent具备模型外的推理能力，而非纯概率匹配。

```python
# Agent进行因果推理
result = ontology.reason(
    query="为什么这批零件质量下降？",
    reasoning_type="causal",  # vs "logical"
    trace=True  # 返回完整推理链
)
# → 输出：推理路径 + 每步置信度 + 最终结论
```

### 3. 元认知能力
知道自己知道什么、不知道什么——置信度自知 + 知识边界识别。

```python
# Agent表达不确定性
response = ontology.ask("量子计算的未来")
if response.confidence < 0.6:
    return "我对这个领域不确定，建议查阅专业资料"
```

## 📊 对比传统方案

| 方案 | 记忆 | 推理 | 元认知 | 幻觉消除 | 成长性 |
|------|------|------|--------|---------|--------|
| **ontology-platform** | ✅ 结构化 | ✅ 因果+逻辑 | ✅ | ✅ | ✅ 实时 |
| Mem0 | ✅ | ❌ | ❌ | ❌ | ❌ |
| RAG | ✅ | ❌ | ❌ | ⚠️ | ❌ |
| Fine-tuning | ⚠️ | ❌ | ❌ | ❌ | ✅但慢 |
| 知识图谱 | ✅ | ⚠️ | ❌ | ⚠️ | ❌ |

## 🏗️ 架构

```
ontology-platform
│
├── 🟦 Memory-System（记忆层）
│   ├── 本体存储（OWL/RDF）
│   ├── 向量索引（语义检索）
│   └── 动态衰减（遗忘机制）
│
├── 🟨 Reasoning-Engine（推理层）
│   ├── 规则引擎（逻辑推理）
│   ├── 因果推理（链追溯）
│   └── 置信度传播（概率更新）
│
└── 🟥 Meta-Cognition（元认知层）
    ├── 置信度自知（知道自己多确定）
    ├── 知识边界（知道自己不知道什么）
    └── 推理自省（能解释推理路径）
```

## 🔌 接入方式

### MCP协议（推荐）
```json
{
  "mcpServer": "ontology-platform",
  "capabilities": ["memory", "reasoning", "metacognition"]
}
```

### API
```bash
curl -X POST http://localhost:8000/reason \
  -d '{"query": "...", "type": "causal"}'
```

### Python SDK
```bash
pip install ontology-platform
```
```python
from ontology_platform import Agent

agent = Agent(memory=Ontology())
agent.learn(experience)
result = agent.reason(query)
```

### Skill
```
OpenClaw Skill: ontology-clawra
```

## 🚀 快速开始

```bash
# 克隆
git clone https://github.com/wu-xiaochen/ontology-platform.git
cd ontology-platform

# 安装
pip install -r requirements.txt

# 启动
python -m src.api.main
```

## 📖 文档

- [Architecture](docs/architecture.md) - 系统架构详解
- [Roadmap](docs/roadmap.md) - 产品路线图
- [PRD](docs/prd-v2.md) - 产品需求文档
- [Examples](docs/examples/) - 使用示例

## ⚖️ 许可协议

**部分开源协议** - 详见 [LICENSE](LICENSE)

- ✅ 免费使用：学习、研究、教育、公开开发协作
- ⚠️ 需要授权：商业产品集成、私有部署、SaaS服务
- 🚫 禁止：去掉署名、闭源fork、非法使用

**申请授权**：[GitHub Issues](https://github.com/wu-xiaochen/ontology-platform/issues)

## 📦 核心功能

- **本体推理引擎**：结构化知识表示 + 逻辑/因果推理
- **置信度追踪**：每条结论附带置信度标注
- **主动学习**：从用户反馈中持续更新本体
- **多领域本体库**：54+预置领域本体（供应链/医疗/金融等）
- **API + SDK + MCP**：多种接入方式

## 🎯 目标用户

- AI应用开发者
- 企业知识管理
- 垂直领域Agent开发者
- RAG/知识图谱开发者

---

*"让AI拥有可信赖的推理能力"*
