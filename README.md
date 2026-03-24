# ontology-platform

### 让每个 Agent 都拥有真正的成长能力

> We don't build agents. We give agents the ability to evolve.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wu-xiaochen/ontology-platform/blob/main/ontology_platform_quickstart.ipynb)
[![PyPI Version](https://img.shields.io/pypi/v/ontology-platform?color=blue)](https://pypi.org/project/ontology-platform/)
[![Python Versions](https://img.shields.io/pypi/pythonversions/ontology-platform?color=blue)](https://pypi.org/project/ontology-platform/)
[![License](https://img.shields.io/github/license/wu-xiaochen/ontology-platform?color=green)](LICENSE)
[![CI Status](https://img.shields.io/github/actions/workflow/status/wu-xiaochen/ontology-platform/ci.yml?branch=main&label=CI)](https://github.com/wu-xiaochen/ontology-platform/actions)
[![Stars](https://img.shields.io/github/stars/wu-xiaochen/ontology-platform?color=yellow)](https://github.com/wu-xiaochen/ontology-platform/stargazers)

---

## ⚡ Quick Start

**🚀 5分钟上手体验**: [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wu-xiaochen/ontology-platform/blob/main/ontology_platform_quickstart.ipynb)

### pip install

```bash
pip install ontology-platform
```

### 从源码安装

```bash
git clone https://github.com/wu-xiaochen/ontology-platform.git
cd ontology-platform
pip install -e .
```

### 运行Demo

```bash
PYTHONPATH=src python examples/demo_supplier_monitor.py
```

---

## 🔥 Live Demo Output

```
=====================================================================
ontology-platform Demo: Autonomous Supplier Monitor
=====================================================================

[1] Loading 5 suppliers into ontology...
    ✓ Acme Components → on_time: 0.91, quality: 0.88
    ✓ Global Parts Ltd → on_time: 0.85, quality: 0.72
    ...

[2] Defining initial reasoning rules...
    ✓ 3 rules loaded

[3] Running baseline risk assessment...
    Confidence: 0.91
    Reasoning chain:
      [1] SUP002: on_time_rate = 0.85 < 0.88 threshold
      [2] SUP002: quality_score = 0.72 < 0.80 threshold
      [3] Rule "combined_risk" triggered

[4] Agent knows when it doesn't know...
    Confidence: 0.52
    → "I don't have enough confidence. Need more information."
```

---

## 🎯 What Makes It Different

| Capability | Traditional RAG + LLM | Mem0 | ontology-platform |
|-----------|----------------------|------|------------------|
| **Persistent memory** | ✅ | ✅ | ✅ |
| **Structured knowledge graph** | ❌ | ❌ | ✅ |
| **Causal reasoning** | ❌ | ❌ | ✅ |
| **Confidence scoring** | ❌ | ❌ | ✅ |
| **Reasoning trace** | ❌ | ❌ | ✅ |
| **Runtime rule learning** | ❌ | ❌ | ✅ |
| **Meta-cognition** | ❌ | ❌ | ✅ |

---

## 📦 Core Features

### 1. Reasoning Engine

```python
from ontology.reasoner import OntologyReasoner, ConfidenceLevel

reasoner = OntologyReasoner()
result = reasoner.reason(
    query="delivery risk",
    context={"entity_id": "SUP002"}
)
print(f"Confidence: {result.confidence}")  # → ASSUMED/CONFIRMED
print(f"Conclusion: {result.conclusion}")
```

### 2. Meta-Cognition

```python
# Agent knows when it doesn't know
if result.confidence == ConfidenceLevel.SPECULATIVE:
    return "需要更多信息来做出可靠判断"
```

### 3. Runtime Learning

```python
reasoner.add_rule({
    "id": "rule_delivery_risk",
    "condition": "on_time_rate < 0.85",
    "conclusion": "供应商存在交付风险",
    "weight": 0.9
})
```

---

## 📖 Documentation

- [Quick Start Guide](docs/quickstart.md)
- [API Reference](docs/api.md)
- [Examples](examples/)
- [Changelog](CHANGELOG.md)

---

## 🤝 Contributing

```bash
git clone https://github.com/wu-xiaochen/ontology-platform.git
cd ontology-platform
pip install -e ".[dev]"
PYTHONPATH=src python examples/demo_supplier_monitor.py
```

---

## 📄 License

MIT License

---

## 🔗 Links

**GitHub**: https://github.com/wu-xiaochen/ontology-platform  
**Issues**: https://github.com/wu-xiaochen/ontology-platform/issues
