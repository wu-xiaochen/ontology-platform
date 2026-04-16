# 快速开始

## 环境要求

- Python 3.10+
- pip

## 安装

```bash
git clone https://github.com/wu-xiaochen/clawra-engine.git
cd clawra-engine
pip install -e .
```

## 运行 Demo（无需 API Key）

```bash
python examples/demo_basic.py
```

输出示例：

```
🔬 Clawra Engine - 基础演示
================================================

📚 加载文档: docs/source/quickstart.md
  → 57 条事实
  → 14 个模式
  → 46 个实体
  → 2 个关系

✅ 认知引擎初始化完成！

🧠 推理测试:
Q: 调压箱的最大安全压力是多少？
A: 0.4 MPa ✅

Q: 超过多少压力会触发紧急截断？
A: 0.35 MPa ✅

Q: 如果压力是0.8MPa安全吗？
A: 不安全 (0.8 MPa > 0.4 MPa maximum) ❌
```

## 更多示例

| 示例 | 说明 |
|------|------|
| `demo_basic.py` | 基础演示，无需 API Key |
| `demo_evolution_loop.py` | 8 阶段进化闭环演示 |
| `demo_graphrag.py` | GraphRAG 混合检索演示 |
| `demo_langchain_adapter.py` | LangChain 集成演示 |

## 配置 API Key（可选）

```bash
export OPENAI_API_KEY='your-key'
# 或
export ANTHROPIC_API_KEY='your-key'
```

## 下一步

- [SDK 使用指南](sdk-guide.md)
- [架构概览](architecture.md)
- [LangChain 适配器](langchain-adapter.md)
