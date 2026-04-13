# Ontology Platform 核心模块 (Core SDK)

本目录包含 ontology-platform 的核心 SDK 组件，提供简洁的 API 供外部调用。

## 📁 文件结构

```
src/ontology_platform/
└── __init__.py   # 核心组件导出
```

## 🚀 核心组件

### 版本信息

```python
__version__ = "0.9.0-alpha"
```

### 导出组件

| 组件 | 说明 |
|------|------|
| `OntologyLoader` | 本体加载器 |
| `OntologyReasoner` | 本体推理器 |
| `ConfidenceEngine` | 置信度引擎 |

## 📖 使用示例

### 快速开始

```python
from ontology_platform import (
    OntologyLoader,
    OntologyReasoner,
    ConfidenceEngine,
    __version__
)

print(f"Using ontology-platform v{__version__}")

# 1. 加载本体
loader = OntologyLoader()
ontology = loader.load("path/to/ontology.ttl")

# 2. 创建推理器
reasoner = OntologyReasoner(ontology)

# 3. 执行推理
result = reasoner.infer(
    subject="KnowledgeGraph",
    predicate="relatedTo",
    max_depth=3
)

# 4. 计算置信度
confidence_engine = ConfidenceEngine()
confidence = confidence_engine.calculate(
    inference=result,
    evidence_sources=["ontology", "external_db"]
)

print(f"Inference confidence: {confidence.score:.2f}")
```

### 完整工作流

```python
from ontology_platform import OntologyLoader, OntologyReasoner, ConfidenceEngine

# 初始化
loader = OntologyLoader()
reasoner = OntologyReasoner(loader.load("domain_ontology.owl"))
confidence = ConfidenceEngine()

# 加载领域知识
agent_knowledge = {
    "type": "Supplier",
    "id": "SUP001",
    "properties": {
        "name": "Acme Components",
        "on_time_rate": 0.91,
        "quality_score": 0.88
    }
}

# 学习新知识
reasoner.learn(agent_knowledge)

# 添加推理规则
reasoner.add_rule({
    "id": "quality_threshold",
    "condition": "quality_score < 0.80",
    "conclusion": "Supplier poses quality risk",
    "confidence": 0.9
})

# 查询推理
result = reasoner.query("Is SUP001 safe to use?")

# 评估置信度
score = confidence.calculate(
    inference=result,
    evidence_sources=["rules", "data"]
)

print(f"Verdict: {result.conclusion}")
print(f"Confidence: {score:.2f}")
print(f"Reasoning: {result.reasoning_chain}")
```

## 🔧 组件详解

### OntologyLoader - 本体加载器

**功能**:
- 加载 RDF/OWL 格式的本体文件
- 支持多种格式：Turtle (.ttl), RDF/XML (.owl), N-Triples (.nt)
- 自动解析本体结构
- 缓存已加载的本体

**支持格式**:
```python
loader.load("ontology.ttl")      # Turtle 格式
loader.load("ontology.owl")      # RDF/XML 格式
loader.load("ontology.nt")       # N-Triples 格式
loader.load("ontology.jsonld")   # JSON-LD 格式
```

### OntologyReasoner - 本体推理器

**功能**:
- 基于本体的逻辑推理
- 规则推理支持
- 知识学习集成
- 推理链追溯

**核心方法**:
```python
# 学习新知识
reasoner.learn(knowledge_dict)

# 添加推理规则
reasoner.add_rule(rule_dict)

# 执行推理
result = reasoner.infer(subject, predicate, max_depth)

# 查询
result = reasoner.query(natural_language_question)
```

### ConfidenceEngine - 置信度引擎

**功能**:
- 计算推理结果的置信度
- 多证据源融合
- 置信度传播
- 不确定性量化

**核心方法**:
```python
# 计算置信度
score = confidence.calculate(
    inference=result,
    evidence_sources=["ontology", "data", "rules"]
)

# 置信度传播
propagated = confidence.propagate(
    initial_score=0.9,
    chain_length=3,
    decay_factor=0.95
)
```

## 🎯 应用场景

### 1. 智能问答系统

```python
from ontology_platform import OntologyLoader, OntologyReasoner, ConfidenceEngine

class QASystem:
    def __init__(self, ontology_path):
        self.loader = OntologyLoader()
        self.reasoner = OntologyReasoner(
            self.loader.load(ontology_path)
        )
        self.confidence = ConfidenceEngine()
    
    def answer(self, question: str):
        # 推理
        result = self.reasoner.query(question)
        
        # 计算置信度
        score = self.confidence.calculate(
            inference=result,
            evidence_sources=["ontology"]
        )
        
        # 返回带置信度的答案
        return {
            "answer": result.conclusion,
            "confidence": score,
            "reasoning": result.reasoning_chain
        }
```

### 2. 知识图谱构建

```python
from ontology_platform import OntologyLoader, OntologyReasoner

class KnowledgeGraphBuilder:
    def __init__(self):
        self.loader = OntologyLoader()
        self.reasoner = OntologyReasoner(
            self.loader.load("schema.owl")
        )
    
    def build_from_data(self, data_list):
        for item in data_list:
            self.reasoner.learn(item)
        
        # 推理隐含关系
        implicit = self.reasoner.infer_implicit_relations()
        
        return implicit
```

### 3. 决策支持系统

```python
from ontology_platform import OntologyLoader, OntologyReasoner, ConfidenceEngine

class DecisionSupport:
    def __init__(self):
        self.reasoner = OntologyReasoner(
            OntologyLoader().load("decision_ontology.owl")
        )
        self.confidence = ConfidenceEngine()
    
    def evaluate_risk(self, scenario):
        # 学习场景数据
        self.reasoner.learn(scenario)
        
        # 推理风险
        risk_result = self.reasoner.query("What is the risk level?")
        
        # 计算置信度
        confidence_score = self.confidence.calculate(
            inference=risk_result,
            evidence_sources=["rules", "data", "expert_knowledge"]
        )
        
        return {
            "risk_level": risk_result.conclusion,
            "confidence": confidence_score,
            "factors": risk_result.reasoning_chain
        }
```

## 📊 版本历史

### v0.9.0-alpha (Current)
- ✅ 核心 SDK 组件稳定
- ✅ 支持基本推理和置信度计算
- 🔄 持续优化性能

### 未来计划
- 📅 支持分布式推理
- 📅 集成更多本体格式
- 📅 增强置信度传播算法

## 🔗 相关模块

- [API 模块](../api/README.md) - RESTful/GraphQL 接口
- [Chunking 模块](../chunking/README.md) - 文档分块
- [Memory 模块](../memory/README.md) - 记忆治理
- [Ontology 模块](../ontology/README.md) - 底层实现

## 📚 完整文档

- [项目主 README](../../README.md)
- [快速开始指南](../../ontology_platform_quickstart.ipynb)
- [贡献指南](../../CONTRIBUTING.md)

## 🐛 问题反馈

如有问题或建议，请：
1. 查看 [Issue Tracker](https://github.com/wu-xiaochen/ontology-platform/issues)
2. 提交新的 Issue
3. 参与 [Discussions](https://github.com/wu-xiaochen/ontology-platform/discussions)
