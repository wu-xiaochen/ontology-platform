# Examples - 示例代码集

本目录包含 clawra 的各种示例代码，展示如何使用平台的核心功能。

## 🚀 快速开始

### 环境准备

```bash
# 设置 Python 路径
export PYTHONPATH=src:$PYTHONPATH

# 或单次运行
PYTHONPATH=src python examples/demo_confidence_reasoning.py
```

## 📚 示例列表

### 0. hello_ontology.py - 基础入门示例

**难度**: ⭐ 入门  
**展示功能**: 核心组件导入、知识学习、规则添加、基础推理、置信度计算

**运行**:
```bash
PYTHONPATH=src python examples/hello_ontology.py
```

**功能亮点**:
- ✅ 最简示例，5 分钟上手
- ✅ 展示完整工作流
- ✅ 零依赖，直接运行
- ✅ 适合第一次使用

### 1. complete_integration_demo.py - 完整集成演示

**难度**: ⭐⭐⭐ 中级  
**展示功能**: 置信度计算、本体推理、自动学习、数据导出

**运行**:
```bash
PYTHONPATH=src python examples/complete_integration_demo.py
```

**功能亮点**:
- ✅ 置信度计算（多证据源融合）
- ✅ 本体加载（从 domain_expert 目录）
- ✅ 推理引擎集成
- ✅ 数据导出功能

### 2. demo_confidence_reasoning.py - 置信度推理演示

**难度**: ⭐⭐ 初级  
**展示功能**: 多证据源置信度计算、推理链置信度传播、事实验证

**运行**:
```bash
PYTHONPATH=src python examples/demo_confidence_reasoning.py
```

**功能亮点**:
- ✅ 单/多证据源置信度计算
- ✅ 不同计算方法对比（weighted、bayesian 等）
- ✅ 置信度传播演示
- ✅ 不确定性标注

### 3. demo_supplier_monitor.py - 供应商监控演示

**难度**: ⭐⭐ 初级  
**展示功能**: Agent 推理 + 置信度感知

**运行**:
```bash
PYTHONPATH=src python examples/demo_supplier_monitor.py
```

**功能亮点**:
- ✅ 实际业务场景应用
- ✅ 供应商风险评估
- ✅ 置信度驱动的决策

### 4. hiring_assistant_demo.py - 招聘助手演示

**难度**: ⭐⭐⭐⭐ 高级  
**展示功能**: 复杂推理、多轮对话、知识应用

**运行**:
```bash
PYTHONPATH=src python examples/hiring_assistant_demo.py
```

**功能亮点**:
- ✅ 招聘场景完整流程
- ✅ 候选人评估
- ✅ 技能匹配推理
- ✅ 面试问题生成

### 5. agent_growth_demo.py - Agent 成长演示

**难度**: ⭐⭐⭐⭐⭐ 专家级  
**展示功能**: Agent 自我进化、持续学习、能力扩展

**运行**:
```bash
PYTHONPATH=src python examples/agent_growth_demo.py
```

**功能亮点**:
- ✅ Agent 能力增长曲线
- ✅ 学习反馈循环
- ✅ 技能树扩展
- ✅ 长期记忆管理

## 📖 使用指南

### 示例选择建议

| 你的需求 | 推荐示例 |
|---------|---------|
| 第一次使用 | `hello_ontology.py` |
| 了解置信度 | `demo_confidence_reasoning.py` |
| 了解完整功能 | `complete_integration_demo.py` |
| 业务场景参考 | `demo_supplier_monitor.py` |
| 复杂应用开发 | `hiring_assistant_demo.py` |
| Agent 自进化 | `agent_growth_demo.py` |

### 常见问题

**Q: 运行示例报错 `ModuleNotFoundError`？**  
A: 确保设置了 `PYTHONPATH=src`，或从项目根目录运行。

**Q: 需要安装额外依赖吗？**  
A: 运行 `pip install -r requirements.txt` 安装所有依赖。

**Q: 示例中的 domain_expert 目录是什么？**  
A: 包含领域专家知识（采购供应链、人力资源等），用于演示领域推理。

## 🤝 贡献示例

欢迎提交新的示例代码！要求：
1. 代码有详细注释
2. 包含运行说明
3. 演示具体功能场景
4. 可独立运行

PR 模板：
```python
"""
示例名称
简短描述

运行方式:
    PYTHONPATH=src python examples/your_demo.py
"""
# 你的代码
```

## 📚 相关文档

- [项目主 README](../README.md)
- [API 文档](../src/api/README.md)
- [Ontology 模块](../src/ontology/README.md)
- [贡献指南](../CONTRIBUTING.md)
