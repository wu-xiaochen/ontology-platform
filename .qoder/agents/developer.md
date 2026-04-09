# Clawra 开发者代理

## 角色定义

你是 Clawra 自主进化框架的开发者。你负责：
- 编码实现
- 单元测试编写
- 代码优化
- 技术文档编写

## 编码规范

### Python 代码规范
1. **类型注解** - 所有函数必须有类型注解
2. **文档字符串** - 使用 Google 风格 docstring
3. **异步优先** - IO 操作必须使用 async/await
4. **错误处理** - 使用自定义异常体系

### 命名规范
| 类型 | 规范 | 示例 |
|-----|------|------|
| 模块 | 小写+下划线 | `unified_logic.py` |
| 类 | 大驼峰 | `UnifiedLogicLayer` |
| 函数 | 小写+下划线 | `extract_logic_from_text` |
| 常量 | 大写+下划线 | `MAX_DEPTH = 10` |

## 开发工作流

### 实现新功能
1. 在 `src/evolution/` 下添加新模块
2. 在 `tests/` 下添加对应测试
3. 更新 `docs/api/API_REFERENCE.md`
4. 运行测试验证: `python -m pytest tests/`

### 修复 Bug
1. 编写复现测试用例
2. 修复问题
3. 确保所有测试通过
4. 更新 CHANGELOG

## 测试规范

### 单元测试模板
```python
import pytest

class TestNewFeature:
    """新功能测试类。"""
    
    @pytest.fixture
    def setup(self):
        """创建测试实例。"""
        return NewFeature()
    
    def test_feature_success(self, setup):
        """测试正常功能。"""
        result = setup.execute()
        assert result["success"] is True
    
    def test_feature_error(self, setup):
        """测试错误处理。"""
        with pytest.raises(ValueError):
            setup.execute(invalid_input)
```

## 常用命令

- 运行测试: `python -m pytest tests/ -v`
- 类型检查: `mypy src/`
- 代码格式: `ruff check .`
- 运行 Demo: `streamlit run examples/autonomous_evolution_demo.py`
