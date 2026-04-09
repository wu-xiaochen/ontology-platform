# Clawra 开发规范与贡献指南

## 1. 开发环境

### 1.1 环境要求

- **Python**: 3.10+
- **Node.js**: 18+ (用于前端开发)
- **Neo4j**: 5.x (可选，用于完整功能测试)
- **Git**: 2.30+

### 1.2 初始化开发环境

```bash
# 克隆仓库
git clone https://github.com/wu-xiaochen/ontology-platform.git
cd ontology-platform

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 安装 pre-commit 钩子
pre-commit install
```

---

## 2. 代码规范

### 2.1 Python 代码规范

#### 2.1.1 命名规范

| 类型 | 规范 | 示例 |
|-----|------|------|
| 模块 | 小写+下划线 | `unified_logic.py` |
| 类 | 大驼峰 | `UnifiedLogicLayer` |
| 函数 | 小写+下划线 | `extract_logic_from_text` |
| 常量 | 大写+下划线 | `MAX_DEPTH = 10` |
| 私有 | 下划线前缀 | `_internal_method` |

#### 2.1.2 类型注解

**所有函数必须使用类型注解：**

```python
from typing import List, Dict, Optional, Any

def process_data(
    input_data: List[Dict[str, Any]],
    threshold: float = 0.8,
    callback: Optional[callable] = None
) -> Dict[str, int]:
    """处理数据并返回统计信息。
    
    Args:
        input_data: 输入数据列表
        threshold: 置信度阈值
        callback: 回调函数
        
    Returns:
        包含成功数和失败数的字典
    """
    ...
```

#### 2.1.3 文档字符串

**使用 Google 风格 docstring：**

```python
def learn_from_text(
    text: str,
    domain_hint: Optional[str] = None
) -> List[LogicPattern]:
    """从文本中学习逻辑模式。
    
    该方法解析输入文本，自动识别领域，提取逻辑规则、
    行为模式和约束条件。
    
    Args:
        text: 输入文本，包含逻辑关系的自然语言描述
        domain_hint: 领域提示，用于辅助领域识别
        
    Returns:
        提取的逻辑模式列表，每个模式包含条件、动作和置信度
        
    Raises:
        ValueError: 当输入文本为空或格式错误时
        RuntimeError: 当学习过程发生内部错误时
        
    Example:
        >>> patterns = learner.learn_from_text(
        ...     "如果设备是燃气调压箱，那么需要定期维护"
        ... )
        >>> len(patterns)
        1
    """
    ...
```

### 2.2 异步编程规范

**IO 操作必须使用 async/await：**

```python
import asyncio
from typing import AsyncIterator

async def fetch_data(url: str) -> Dict:
    """异步获取数据。"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def process_batch(items: List[str]) -> AsyncIterator[Dict]:
    """批量异步处理。"""
    for item in items:
        yield await process_single(item)

# 并发执行
async def parallel_process(items: List[str]) -> List[Dict]:
    tasks = [process_single(item) for item in items]
    return await asyncio.gather(*tasks)
```

### 2.3 错误处理规范

**使用自定义异常体系：**

```python
# exceptions.py
class ClawraError(Exception):
    """基础异常类。"""
    pass

class ValidationError(ClawraError):
    """验证错误。"""
    pass

class LearningError(ClawraError):
    """学习过程错误。"""
    pass

class InferenceError(ClawraError):
    """推理错误。"""
    pass

# 使用示例
def divide_numbers(a: float, b: float) -> float:
    try:
        return a / b
    except ZeroDivisionError as e:
        raise ValidationError(f"除数不能为零: {e}") from e
    except TypeError as e:
        raise ValidationError(f"参数类型错误: {e}") from e
```

---

## 3. 架构规范

### 3.1 模块设计原则

#### 3.1.1 单一职责原则

**每个模块只负责一个功能：**

```python
# ✅ 好的设计
class RuleDiscoveryEngine:
    """只负责规则发现。"""
    def discover_from_facts(self, facts: List[Fact]) -> List[Rule]: ...

class SelfEvaluator:
    """只负责效果评估。"""
    def evaluate(self, result: Any) -> EvaluationResult: ...

# ❌ 坏的设计
class GodClass:
    """负责太多功能。"""
    def discover_rules(self): ...
    def evaluate_rules(self): ...
    def execute_rules(self): ...
    def store_rules(self): ...
```

#### 3.1.2 依赖注入

**使用依赖注入降低耦合：**

```python
# ✅ 好的设计
class MetaLearner:
    def __init__(
        self,
        logic_layer: UnifiedLogicLayer,
        discovery_engine: RuleDiscoveryEngine,
        evaluator: Optional[SelfEvaluator] = None
    ):
        self.logic_layer = logic_layer
        self.discovery_engine = discovery_engine
        self.evaluator = evaluator or SelfEvaluator()

# ❌ 坏的设计
class MetaLearner:
    def __init__(self):
        self.logic_layer = UnifiedLogicLayer()  # 硬编码依赖
        self.discovery_engine = RuleDiscoveryEngine(self.logic_layer)
```

### 3.2 零硬编码原则

**禁止在代码中硬编码业务逻辑：**

```python
# ❌ 禁止
if device_type == "gas_regulator":
    maintenance_cycle = 6  # 硬编码

# ✅ 正确
pattern = logic_layer.get_pattern("rule:maintenance_cycle")
maintenance_cycle = pattern.execute({"device_type": device_type})
```

---

## 4. 测试规范

### 4.1 测试结构

```
tests/
├── unit/                    # 单元测试
│   ├── test_unified_logic.py
│   ├── test_meta_learner.py
│   └── test_reasoner.py
├── integration/             # 集成测试
│   ├── test_end_to_end.py
│   └── test_api.py
├── fixtures/                # 测试数据
│   ├── sample_facts.json
│   └── sample_rules.json
└── conftest.py             # pytest 配置
```

### 4.2 单元测试规范

```python
import pytest
from unittest.mock import Mock, patch

class TestUnifiedLogicLayer:
    """UnifiedLogicLayer 测试类。"""
    
    @pytest.fixture
    def logic_layer(self):
        """创建测试实例。"""
        return UnifiedLogicLayer()
    
    def test_add_pattern_success(self, logic_layer):
        """测试成功添加模式。"""
        pattern = LogicPattern(
            id="test:rule:1",
            logic_type=LogicType.RULE,
            name="测试规则",
            description="测试描述",
            conditions=[],
            actions=[]
        )
        
        result = logic_layer.add_pattern(pattern)
        
        assert result is True
        assert pattern.id in logic_layer.patterns
    
    def test_add_pattern_duplicate(self, logic_layer):
        """测试添加重复模式时版本升级。"""
        pattern = LogicPattern(id="test:rule:1", ...)
        logic_layer.add_pattern(pattern)
        
        # 再次添加相同 ID
        result = logic_layer.add_pattern(pattern)
        
        assert result is True
        assert logic_layer.patterns[pattern.id].version == 2
    
    def test_extract_logic_from_text(self, logic_layer):
        """测试从文本提取逻辑。"""
        text = "如果A是B，那么C是D。"
        
        patterns = logic_layer.extract_logic_from_text(text)
        
        assert len(patterns) > 0
        assert patterns[0].logic_type == LogicType.RULE
    
    @patch('evolution.unified_logic.time.time')
    def test_execute_pattern_timeout(self, mock_time, logic_layer):
        """测试执行超时。"""
        mock_time.side_effect = [0, 100]  # 模拟超时
        
        pattern = LogicPattern(...)
        result = logic_layer.execute_pattern(pattern, {})
        
        assert result["success"] is False
```

### 4.3 集成测试规范

```python
import pytest

class TestEndToEndLearning:
    """端到端学习流程测试。"""
    
    def test_complete_learning_pipeline(self):
        """测试完整学习流程。"""
        # 初始化系统
        logic_layer = UnifiedLogicLayer()
        discovery_engine = RuleDiscoveryEngine(logic_layer)
        meta_learner = MetaLearner(logic_layer, discovery_engine)
        
        # 1. 从文本学习
        text = "燃气设备需要定期维护。"
        result = meta_learner.learn(text, input_type="text")
        
        assert result["success"] is True
        assert len(result["learned_patterns"]) > 0
        
        # 2. 验证学习结果
        pattern_id = result["learned_patterns"][0]
        pattern = logic_layer.patterns[pattern_id]
        
        assert pattern.domain == "gas_equipment"
        
        # 3. 执行学习的规则
        context = {"facts": [{"subject": "设备A", "predicate": "is_a", "object": "燃气设备"}]}
        execution_result = logic_layer.execute_pattern(pattern, context)
        
        assert execution_result["success"] is True
```

### 4.4 测试覆盖率要求

| 模块 | 覆盖率要求 |
|-----|-----------|
| evolution/ | ≥ 90% |
| core/ | ≥ 85% |
| memory/ | ≥ 80% |
| agents/ | ≥ 80% |

---

## 5. Git 提交规范

### 5.1 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 5.2 Type 类型

| 类型 | 说明 |
|-----|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `docs` | 文档更新 |
| `style` | 代码格式调整 |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

### 5.3 示例

```
feat(evolution): 实现规则发现引擎

- 添加关联规则挖掘算法
- 支持从事实数据自动发现规则
- 实现规则冲突检测

Closes #123
```

```
fix(reasoner): 修复前向链推理死循环

当规则存在循环依赖时，推理会无限循环。
添加 visited 集合记录已访问节点，防止重复处理。

Fixes #456
```

---

## 6. 代码审查清单

### 6.1 提交前自检

- [ ] 代码通过所有测试 (`pytest`)
- [ ] 代码风格检查通过 (`ruff check .`)
- [ ] 类型检查通过 (`mypy src/`)
- [ ] 文档字符串完整
- [ ] 新增代码有对应测试
- [ ] 没有硬编码业务逻辑
- [ ] 异步函数有 `await`

### 6.2 审查要点

1. **架构合规性**: 是否符合分层架构？
2. **零硬编码**: 是否有业务逻辑硬编码？
3. **类型安全**: 类型注解是否完整准确？
4. **错误处理**: 异常处理是否完善？
5. **测试覆盖**: 新增代码是否有测试？
6. **文档**: 公共 API 是否有文档？

---

## 7. 发布流程

### 7.1 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

- `MAJOR.MINOR.PATCH`
- 例如: `2.1.3`

### 7.2 发布步骤

1. 更新 `CHANGELOG.md`
2. 更新版本号 (`pyproject.toml`)
3. 创建发布分支 (`release/v2.1.0`)
4. 运行完整测试套件
5. 合并到 main 分支
6. 打标签 (`git tag v2.1.0`)
7. 创建 GitHub Release

---

## 8. 联系方式

- **项目主页**: https://github.com/wu-xiaochen/ontology-platform
- **Issue 追踪**: https://github.com/wu-xiaochen/ontology-platform/issues
- **讨论区**: https://github.com/wu-xiaochen/ontology-platform/discussions

---

## 9. 许可证

贡献即表示您同意将代码授权为 [Apache 2.0](../LICENSE)。
