# Clawra 测试策略

> 全面覆盖的测试体系，确保质量稳定。

---

## 1. 测试原则

### 1.1 核心原则

- **测试先行**：先写测试，再写实现（测试驱动开发）
- **零 mock 不测试**：如无法 mock，则跳过该测试
- **快速反馈**：单元测试 < 1 秒，集成测试 < 30 秒
- **真实环境**：生产环境配置用于验收测试

### 1.2 测试金字塔

```
         ┌──────────┐
         │   E2E    │   ← 最终用户场景，Mock 最小化
         │   Tests  │
        ┌┴──────────┴┐
        │ Integration │   ← 多模块协作，可用 mock
        │   Tests     │
       ┌┴─────────────┴┐
       │   Unit Tests  │   ← 单模块内部逻辑，大量 mock
       └────────────────┘
```

---

## 2. 测试类型

### 2.1 单元测试

**目标**：每个函数/类方法的独立行为

**示例**（`test_meta_learner.py`）：

```python
import pytest
from unittest.mock import MagicMock, patch

from src.evolution.meta_learner import MetaLearner

class TestMetaLearner:
    """MetaLearner 单元测试"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM 客户端"""
        mock = MagicMock()
        mock.chat.return_value = '{"strategy": "deep_analysis", "confidence": 0.9}'
        return mock

    @pytest.fixture
    def meta_learner(self, mock_llm):
        """创建 MetaLearner 实例（mock LLM）"""
        return MetaLearner(llm_client=mock_llm)

    def test_init(self, meta_learner):
        """测试初始化"""
        assert meta_learner is not None
        assert meta_learner.history_window == 10

    def test_analyze_pattern_quality(self, meta_learner):
        """测试模式质量分析"""
        pattern = MagicMock()
        pattern.quality_score = 0.5

        with patch.object(meta_learner, '_call_llm') as mock:
            mock.return_value = {"quality": 0.8, "suggestions": ["增加约束"]}
            result = meta_learner.analyze_pattern_quality(pattern)

        assert result['quality'] > 0.5

    def test_suggest_improvement(self, meta_learner):
        """测试改进建议生成"""
        pattern = MagicMock()
        pattern.id = "test_pattern"
        pattern.logic_type = "RULE"

        with patch.object(meta_learner, '_call_llm') as mock:
            mock.return_value = {"strategy": "add_constraint", "priority": "high"}
            result = meta_learner.suggest_improvement(pattern)

        assert 'strategy' in result
```

### 2.2 集成测试

**目标**：多模块协作的正确性

**示例**（`test_evolution_loop.py`）：

```python
import pytest
from unittest.mock import patch, MagicMock

from src.evolution.evolution_loop import EvolutionLoop
from src.core.ontology import OntologyEngine

class TestEvolutionLoop:
    """EvolutionLoop 集成测试"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM"""
        mock = MagicMock()
        mock.chat.return_value = '{"strategy": "test", "confidence": 0.9}'
        return mock

    @pytest.fixture
    def evolution_loop(self, mock_llm):
        """创建完整 EvolutionLoop（mock 所有外部依赖）"""
        with patch('src.evolution.meta_learner.MetaLearner._call_llm'):
            loop = EvolutionLoop(
                llm_client=mock_llm,
                enable_memory=False
            )
            return loop

    def test_full_loop_execution(self, evolution_loop):
        """测试完整进化循环"""
        # 添加测试数据
        evolution_loop.kg.add_fact("测试实体", "is_a", "测试类型")

        # 执行单步
        with patch.object(evolution_loop, '_call_llm') as mock:
            mock.return_value = {"action": "continue"}
            result = evolution_loop.step()

        assert 'phase' in result
        assert result['success'] is True
```

### 2.3 端到端测试

**目标**：真实用户场景（可选用 LLM 调用）

**示例**：

```python
import pytest

@pytest.mark.e2e
@pytest.mark.slow
class TestRealScenarios:
    """端到端真实场景测试（需要真实 LLM）"""

    @pytest.fixture
    def agent(self):
        """使用真实 Agent"""
        from src.clawra import Clawra
        return Clawra(enable_memory=False, timeout=60)

    def test_gas_safety_scenario(self, agent):
        """燃气安全检查场景"""
        # 学习规则
        result = agent.learn(
            "燃气调压箱出口压力不得超过0.4MPa。"
        )
        assert result['success']

        # 添加事实
        agent.add_fact("调压箱A", "is_a", "燃气调压箱")
        agent.add_fact("调压箱A", "出口压力", "0.5MPa")

        # 推理
        conclusions = agent.reason()

        # 验证
        danger_found = any("危险" in c.conclusion for c in conclusions)
        assert danger_found, "应该检测到超压危险"
```

---

## 3. Mock 策略

### 3.1 LLM Mock

```python
@pytest.fixture
def mock_llm():
    """Mock LLM 客户端"""
    mock = MagicMock()
    mock.chat.return_value = '{"intent": "learn", "entities": [], "relations": []}'
    return mock

# 在测试中使用
with patch('src.evolution.meta_learner.MetaLearner._call_llm', mock_llm):
    result = meta_learner.analyze(...)
```

### 3.2 Neo4j Mock

```python
@pytest.fixture
def mock_neo4j():
    """Mock Neo4j 驱动"""
    mock = MagicMock()
    mock.session.return_value.__enter__ = MagicMock()
    mock.session.return_value.__exit__ = MagicMock()
    return mock
```

### 3.3 ChromaDB Mock

```python
@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB 客户端"""
    mock = MagicMock()
    mock.get_collection.return_value.query.return_value = {
        'documents': [['测试文档']],
        'distances': [[0.1]]
    }
    return mock
```

---

## 4. 测试数据

### 4.1 固定测试数据

```python
# tests/fixtures/sample_knowledge.py

SAMPLE_FACTS = [
    ("调压箱A", "is_a", "燃气调压箱"),
    ("调压箱B", "is_a", "燃气调压箱"),
    ("燃气调压箱", "is_a", "燃气设备"),
]

SAMPLE_PATTERNS = [
    {
        "id": "rule:gas:pressure",
        "logic_type": "RULE",
        "name": "燃气压力规则",
        "confidence": 0.95,
    }
]
```

### 4.2 临时测试数据

```python
import tempfile
import os

@pytest.fixture
def temp_kb():
    """临时知识库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_path = os.path.join(tmpdir, "test_kb")
        os.makedirs(kb_path)
        yield kb_path
```

---

## 5. 运行测试

### 5.1 快速单元测试（跳过慢速）

```bash
# 运行所有非慢速测试
pytest tests/ -m "not slow" -v

# 只运行单元测试
pytest tests/unit/ -v

# 只运行某个模块
pytest tests/test_meta_learner.py -v
```

### 5.2 完整测试套件

```bash
# 运行所有测试（包括慢速 E2E）
pytest tests/ -v --timeout=300

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### 5.3 调试模式

```bash
# 在第一个失败处停止
pytest tests/ -x

# 显示打印输出
pytest tests/ -s

# 只运行上次失败的测试
pytest tests/ --lf
```

---

## 6. 持续集成

### 6.1 GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-timeout

      - name: Run tests
        run: |
          pytest tests/ -m "not slow" --timeout=60 -v

      - name: Run slow tests
        if: github.event_name == 'schedule'
        run: |
          pytest tests/ -m slow --timeout=300 -v
```

### 6.2 定时全量测试

```yaml
# 每周日凌晨运行完整测试
on:
  schedule:
    - cron: '0 0 * * 0'
```

---

## 7. 覆盖率要求

| 模块 | 最低覆盖率 |
|------|----------|
| `src/core/` | 80% |
| `src/evolution/` | 85% |
| `src/memory/` | 75% |
| `src/retrieval/` | 80% |
| `src/api/` | 70% |
| **整体** | **80%** |

---

## 8. 性能基准

```python
import time

def test_reasoning_performance():
    """推理性能基准：10秒内完成"""
    agent = Clawra(enable_memory=False)

    # 准备 100 条事实
    for i in range(100):
        agent.add_fact(f"实体{i}", "is_a", "测试类型")

    start = time.time()
    conclusions = agent.reason(max_depth=5)
    elapsed = time.time() - start

    assert elapsed < 10, f"推理耗时 {elapsed:.1f}s，超过 10s 限制"
```

---

**最后更新**: 2026-04-13
