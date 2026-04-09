# Tests - 测试套件

本目录包含 clawra 的单元测试和集成测试。

## 📁 测试文件结构

```
tests/
├── test_confidence.py   # 置信度计算测试
├── test_evidence.py     # 证据管理测试
├── test_reasoner.py     # 推理引擎测试
├── test_chunking.py     # 文档分块测试
├── test_memory.py       # 记忆治理测试
└── __init__.py
```

## 🚀 运行测试

### 运行所有测试

```bash
# 从项目根目录
pytest tests/

# 带详细输出
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 运行单个测试文件

```bash
# 运行置信度测试
pytest tests/test_confidence.py -v

# 运行推理引擎测试
pytest tests/test_reasoner.py -v

# 运行证据测试
pytest tests/test_evidence.py -v

# 运行分块测试
pytest tests/test_chunking.py -v

# 运行记忆治理测试
pytest tests/test_memory.py -v
```

### 运行特定测试

```bash
# 运行特定测试函数
pytest tests/test_confidence.py::test_basic_calculation -v

# 运行包含特定名称的测试
pytest tests/ -k "confidence" -v
```

## 📊 测试覆盖

### 当前覆盖模块

| 模块 | 测试文件 | 测试数 | 状态 |
|------|---------|--------|------|
| 置信度计算 | `test_confidence.py` | 4 | ✅ |
| 证据管理 | `test_evidence.py` | 3 | ✅ |
| 推理引擎 | `test_reasoner.py` | 8 | ✅ |
| 文档分块 | `test_chunking.py` | 13 | ✅ |
| 记忆治理 | `test_memory.py` | 15 | ✅ |

### 待补充测试

- [ ] `src/api/main.py` - API 端点测试
- [ ] `src/ontology/neo4j_client.py` - Neo4j 集成测试
- [ ] `src/ontology/rdf_adapter.py` - RDF 适配测试
- [ ] `src/cache_strategy.py` - 缓存策略测试
- [ ] `src/security.py` - 安全模块测试
- [ ] `src/permissions.py` - 权限管理测试

## 📝 测试示例

### 置信度测试示例

```python
from src.eval.confidence import ConfidenceCalculator, Evidence

def test_weighted_average():
    """测试加权平均计算"""
    calc = ConfidenceCalculator()
    evidence = [
        Evidence(source="A", reliability=0.9, content="test1"),
        Evidence(source="B", reliability=0.8, content="test2"),
    ]
    result = calc.calculate(evidence, method="weighted")
    assert 0.8 < result.value < 0.9
```

### 推理引擎测试示例

```python
from src.core.reasoner import Reasoner, Fact

def test_modus_ponens():
    """测试假言推理"""
    reasoner = Reasoner()
    reasoner.add_fact(Fact("P", True))
    reasoner.add_rule("P -> Q")
    
    result = reasoner.query("Q")
    assert result is True
```

## 🔧 测试最佳实践

1. **命名规范**: 测试函数使用 `test_` 前缀
2. **独立性**: 每个测试应独立运行，不依赖其他测试
3. **覆盖率**: 新代码应包含对应测试
4. **Mock**: 外部依赖（数据库、API）使用 Mock

## 📈 持续集成

测试在以下情况自动运行：
- Git commit 前（pre-commit hook）
- Pull Request 提交时
-  nightly build

## 🤝 贡献测试

添加新测试时：
1. 在对应测试文件中添加测试函数
2. 确保测试可独立运行
3. 添加适当的断言和注释
4. 运行完整测试套件确保无破坏

## 📚 相关文档

- [pytest 文档](https://docs.pytest.org/)
- [项目主 README](../README.md)
- [贡献指南](../CONTRIBUTING.md)
