# Examples

示例代码集合，展示 ontology-platform 的各种使用场景。

## 快速开始

### 1. Hello World
```bash
python examples/hello_ontology.py
```
最基础的示例，展示如何创建本体和添加知识。

### 2. 完整集成演示
```bash
python examples/complete_integration_demo.py
```
展示平台各模块的完整集成流程。

## 进阶示例

### 3. 置信度推理
```bash
python examples/demo_confidence_reasoning.py
```
展示置信度计算和基于置信度的推理。

### 4. 供应商监控
```bash
python examples/demo_supplier_monitor.py
```
实际业务场景：供应商风险监控。

### 5. 招聘助手
```bash
python examples/hiring_assistant_demo.py
```
完整的招聘助手应用，包含：
- 简历解析
- 候选人匹配
- 面试问题生成

### 6. 供应链风险评估
```bash
python examples/supply_chain_risk_demo.py
```
企业级供应链风控系统，展示：
- 多维度风险评估（交货、质量、财务）
- 置信度计算与证据追踪
- 自动风险等级分类
- 可解释的推理链输出

## 高级示例

### 7. Agent 成长演示
```bash
python examples/agent_growth_demo.py
```
展示 Agent 如何通过反思和学习不断成长。

### 8. Clawra 全栈演示
```bash
python examples/clawra_full_stack_demo.py
```
Clawra 系统的全栈功能演示。

### 9. Phase 3 高级功能
```bash
python examples/phase3_advanced_demo.py
```
Phase 3 的高级功能展示。

### 10. Phase 5 企业级功能
```bash
python examples/phase5_enterprise_demo.py
```
企业级功能演示，包括：
- 多租户支持
- 权限管理
- 审计日志

## Web 应用

### Streamlit 应用
```bash
streamlit run examples/streamlit_app.py
```
交互式 Web 界面，可视化展示平台功能。

## 运行要求

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
export OPENAI_API_KEY="your_api_key"
```

## 示例分类

| 难度 | 示例 | 用途 |
|------|------|------|
| ⭐ | hello_ontology.py | 入门 |
| ⭐⭐ | complete_integration_demo.py | 基础集成 |
| ⭐⭐⭐ | demo_confidence_reasoning.py | 置信度 |
| ⭐⭐⭐ | demo_supplier_monitor.py | 业务场景 |
| ⭐⭐⭐⭐ | hiring_assistant_demo.py | 完整应用 |
| ⭐⭐⭐⭐⭐ | agent_growth_demo.py | Agent 成长 |
| ⭐⭐⭐⭐⭐ | supply_chain_risk_demo.py | 企业级供应链风控 |

## 贡献示例

欢迎提交新的示例！要求：
1. 代码完整可运行
2. 包含详细注释
3. 更新 README.md
4. 添加必要的测试
