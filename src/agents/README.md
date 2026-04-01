# Agents - 智能体框架

本目录包含 ontology-platform 的智能体（Agent）核心框架，支持多智能体协作、元认知推理和任务编排。

## 📁 文件结构

```
agents/
├── __init__.py          # 模块导出
├── base.py              # Agent 基类定义
├── metacognition.py     # 元认知能力（自我反思、置信度评估）
└── orchestrator.py      # 多智能体编排器（任务分配、协作调度）
```

## 🚀 核心功能

### 1. 基类 Agent (`base.py`)

定义所有智能体的通用接口：

```python
from src.agents.base import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, name: str, role: str):
        super().__init__(name=name, role=role)
    
    async def execute(self, task: str) -> str:
        """执行任务并返回结果"""
        pass
```

**核心方法**:
- `execute(task)`: 执行给定任务
- `reflect()`: 自我反思（调用元认知模块）
- `get_confidence()`: 获取当前置信度

### 2. 元认知能力 (`metacognition.py`)

提供智能体的自我监控和反思能力：

```python
from src.agents.metacognition import MetacognitionModule

meta = MetacognitionModule(agent=my_agent)
confidence = meta.evaluate_confidence(result)
reflection = meta.reflect_on_task(task, result, confidence)
```

**功能**:
- ✅ 置信度评估（基于证据、推理链、历史表现）
- ✅ 自我反思（识别错误、改进策略）
- ✅ 不确定性标注（明确"不知道"的边界）

### 3. 多智能体编排 (`orchestrator.py`)

协调多个智能体协作完成复杂任务：

```python
from src.agents.orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()
orchestrator.register_agent(researcher_agent)
orchestrator.register_agent(analyst_agent)
orchestrator.register_agent(writer_agent)

result = await orchestrator.execute_complex_task(
    task="分析市场趋势并生成报告",
    strategy="pipeline"  # 或 "parallel", "consensus"
)
```

**编排策略**:
- `pipeline`: 流水线模式（A→B→C 顺序执行）
- `parallel`: 并行模式（所有 Agent 同时执行）
- `consensus`: 共识模式（投票/加权平均）

## 📖 使用示例

### 示例 1: 创建单个智能体

```python
from src.agents.base import BaseAgent
from src.agents.metacognition import MetacognitionModule

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Researcher", role="数据研究员")
        self.meta = MetacognitionModule(self)
    
    async def execute(self, task: str) -> str:
        result = self.research(task)
        confidence = self.meta.evaluate_confidence(result)
        return f"{result} (置信度：{confidence:.2%})"
```

### 示例 2: 多智能体协作

```python
from src.agents.orchestrator import MultiAgentOrchestrator

# 创建编排器
orch = MultiAgentOrchestrator()

# 注册智能体
orch.register_agent(data_collector)
orch.register_agent(data_analyst)
orch.register_agent(report_writer)

# 执行复杂任务
report = await orch.execute_complex_task(
    "收集 Q1 销售数据并生成分析报告",
    strategy="pipeline"
)
```

## 🔧 配置选项

### 元认知模块配置

```python
from src.agents.metacognition import MetacognitionConfig

config = MetacognitionConfig(
    confidence_threshold=0.7,      # 置信度阈值
    reflection_enabled=True,       # 启用反思
    uncertainty_penalty=0.1,       # 不确定性惩罚
    evidence_weight=0.4            # 证据权重
)
```

### 编排器配置

```python
from src.agents.orchestrator import OrchestratorConfig

config = OrchestratorConfig(
    max_retries=3,                 # 最大重试次数
    timeout_seconds=300,           # 任务超时
    consensus_threshold=0.6,       # 共识阈值
    load_balancing="round_robin"   # 负载均衡策略
)
```

## 📚 相关文档

- [完整示例](../../examples/hiring_assistant_demo.py) - 招聘助手多智能体应用
- [Agent 成长演示](../../examples/agent_growth_demo.py) - 智能体自我进化
- [核心模块](../core/README.md) - 底层基础设施

## 🤝 贡献指南

添加新的 Agent 类型时：
1. 继承 `BaseAgent` 类
2. 实现 `execute()` 方法
3. 集成元认知模块（可选但推荐）
4. 添加单元测试

## ⚠️ 注意事项

- 所有 Agent 方法必须是 `async` 异步的
- 置信度范围：0.0 ~ 1.0
- 元认知反思会增加 10-20% 的延迟，但显著提升质量
- 多智能体协作时注意资源竞争和死锁问题
