# Examples

示例代码集合，展示 Clawra 自主进化 Agent 的各种使用场景。

## 核心 Demo（推荐）

### Clawra 自主进化 Agent Demo
```bash
streamlit run examples/clawra_demo.py
```
完整展示 Clawra 四大核心能力：
- **自主学习** — 从文本自动提取对象、关系、逻辑和行为
- **本体图谱** — 可视化学习成果的结构化本体
- **无幻觉推理** — 100% 基于学习内容的确定性推理，零 LLM 依赖
- **进化统计** — 学习历程、策略效果、规则发现的量化展示

## 基础示例

### Hello World
```bash
python examples/hello_ontology.py
```
最基础的示例，展示如何创建本体和添加知识。

### 完整集成演示
```bash
python examples/complete_integration_demo.py
```
展示平台各模块的完整集成流程。

## 进阶示例

### 置信度推理
```bash
python examples/demo_confidence_reasoning.py
```
展示置信度计算和基于置信度的推理。

### 供应商监控
```bash
python examples/demo_supplier_monitor.py
```
实际业务场景：供应商风险监控。

### Agent 成长演示
```bash
python examples/agent_growth_demo.py
```
展示 Agent 如何通过反思和学习不断成长。

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
