# Clawra SDK 使用指南

> 完整的 Clawra SDK 使用教程，从入门到精通。

---

## 1. SDK 概述

### 1.1 什么是 Clawra SDK

Clawra SDK 是与 Clawra 交互的官方 Python 客户端，提供：
- 简洁的 API 接口
- 异步支持
- 类型安全
- 自动重试
- 错误处理

### 1.2 安装

```bash
pip install clawra
```

或使用源码：

```bash
git clone https://github.com/wu-xiaochen/ontology-platform.git
cd ontology-platform
pip install -e .
```

---

## 2. 快速开始

### 2.1 基础初始化

```python
from src.clawra import Clawra

# 轻量模式（无需 Neo4j/ChromaDB）
agent = Clawra(enable_memory=False)

# 完整模式（推荐生产环境）
agent = Clawra(
    enable_memory=True,
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password"
)
```

### 2.2 你的第一个学习

```python
# 学习新知识
result = agent.learn(
    "燃气调压箱的出口压力必须 ≤ 0.4MPa，否则有爆炸风险。"
)

print(f"领域: {result['domain']}")
print(f"发现规则数: {len(result['learned_patterns'])}")
print(f"学习耗时: {result['learning_time']:.3f}s")
```

### 2.3 添加事实 + 推理

```python
# 添加事实
agent.add_fact("调压箱A", "is_a", "燃气调压箱", confidence=0.95)
agent.add_fact("燃气调压箱", "is_a", "燃气设备", confidence=0.9)
agent.add_fact("燃气设备", "has_property", "危险气体", confidence=1.0)

# 前向链推理
conclusions = agent.reason(max_depth=3)

for step in conclusions:
    print(f"因为: {step.premise}")
    print(f"所以: {step.conclusion}")
    print(f"依据: {step.rule_id}")
```

---

## 3. 核心 API

### 3.1 Clawra 主类

```python
class Clawra:
    """Clawra 认知引擎主类"""
    
    def learn(
        self,
        text: str,
        domain_hint: str = None,
        input_type: str = "text"
    ) -> Dict[str, Any]:
        """
        学习新知识
        
        Args:
            text: 输入文本
            domain_hint: 领域提示（可选）
            input_type: 输入类型 ("text", "structured", "interaction")
        
        Returns:
            学习结果字典
        """
        
    def add_fact(
        self,
        subject: str,
        predicate: str,
        object: str,
        confidence: float = 0.9
    ) -> bool:
        """
        添加事实到知识图谱
        
        Args:
            subject: 主语
            predicate: 谓语
            object: 宾语
            confidence: 置信度
        
        Returns:
            是否添加成功
        """
        
    def reason(
        self,
        max_depth: int = 10,
        target: str = None
    ) -> List[InferenceStep]:
        """
        执行推理
        
        Args:
            max_depth: 最大推理深度
            target: 目标对象（可选，用于后向链）
        
        Returns:
            推理步骤列表
        """
        
    def query(
        self,
        subject: str = None,
        predicate: str = None,
        object: str = None,
        min_confidence: float = 0.5
    ) -> List[Fact]:
        """
        查询知识图谱
        
        Args:
            subject: 主语（可选，支持模糊匹配）
            predicate: 谓语（可选）
            object: 宾语（可选）
            min_confidence: 最小置信度
        
        Returns:
            匹配的事实列表
        """
        
    def get_patterns(
        self,
        domain: str = None,
        logic_type: str = None
    ) -> List[LogicPattern]:
        """
        获取逻辑模式
        
        Args:
            domain: 领域过滤（可选）
            logic_type: 类型过滤（可选）
        
        Returns:
            匹配的逻辑模式列表
        """
        
    def retrieve_knowledge(
        self,
        query: str,
        top_k: int = 5,
        modes: List[str] = ["entity", "semantic"]
    ) -> RetrievalResult:
        """
        GraphRAG 混合检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数
            modes: 检索模式 ("entity", "semantic", "global", "smart")
        
        Returns:
            检索结果
        """
        
    def export_knowledge(
        self,
        format: str = "json",
        domain: str = None
    ) -> str:
        """
        导出知识
        
        Args:
            format: 导出格式 ("json", "rdf", "csv")
            domain: 领域过滤（可选）
        
        Returns:
            导出内容
        """
        
    def import_knowledge(
        self,
        content: str,
        format: str = "json"
    ) -> int:
        """
        导入知识
        
        Args:
            content: 导入内容
            format: 导入格式 ("json", "rdf", "csv")
        
        Returns:
            导入的事实数
        """
        
    def reset(self) -> None:
        """重置系统状态（保留配置，清除所有数据）"""
        
    def close(self) -> None:
        """关闭系统，释放资源"""
```

---

## 4. 进阶用法

### 4.1 领域自适应学习

```python
# 自动检测领域
result = agent.learn(
    "患者需要定期服用胰岛素控制血糖，这是医疗诊断治疗方案。"
)
print(f"识别领域: {result['domain']}")
# → medical

# 指定领域提示
result = agent.learn(
    "这是供应商风险评估的规则。",
    domain_hint="procurement"
)
```

### 4.2 批量学习

```python
# 批量学习
texts = [
    "燃气调压箱的出口压力必须 ≤ 0.4MPa。",
    "燃气调压箱需要每6个月维护一次。",
    "燃气调压箱的进气压力范围是 0.02-0.4MPa。",
]

results = []
for text in texts:
    result = agent.learn(text)
    results.append(result)

# 统计
success_count = sum(1 for r in results if r['success'])
print(f"成功率: {success_count}/{len(results)}")
```

### 4.3 自定义规则

```python
from src.evolution.unified_logic import LogicPattern, LogicType

# 创建自定义规则
pattern = LogicPattern(
    id="rule:custom:gas_pressure",
    logic_type=LogicType.RULE,
    name="燃气压力安全规则",
    description="燃气调压箱出口压力不得超过0.4MPa",
    conditions=[
        {"subject": "?X", "predicate": "is_a", "object": "燃气调压箱"},
        {"subject": "?X", "predicate": "出口压力", "object": "?P"}
    ],
    actions=[
        {"type": "constrain", "predicate": "pressure_check", "condition": "?P <= 0.4"}
    ],
    confidence=0.95,
    domain="gas_equipment"
)

# 添加到逻辑层
agent.logic_layer.add_pattern(pattern)
```

### 4.4 置信度管理

```python
# 查询低置信度事实
facts = agent.query(min_confidence=0.3)

# 查询特定置信度范围
high_conf_facts = [f for f in facts if f.confidence >= 0.8]

# 手动更新置信度
for fact in high_conf_facts:
    fact.confidence = min(fact.confidence + 0.05, 1.0)
```

### 4.5 GraphRAG 检索

```python
# 基础检索
result = agent.retrieve_knowledge(
    query="燃气调压箱的安全规范",
    top_k=5
)

# 只用语义检索
result = agent.retrieve_knowledge(
    query="设备维护周期",
    top_k=5,
    modes=["semantic"]
)

# 只用实体检索
result = agent.retrieve_knowledge(
    query="调压箱A 的相关信息",
    top_k=5,
    modes=["entity"]
)

# 全局检索（社区级别）
result = agent.retrieve_knowledge(
    query="燃气设备相关的所有知识",
    top_k=10,
    modes=["global"]
)

# 智能检索（组合）
result = agent.retrieve_knowledge(
    query="燃气调压箱的安全管理和维护",
    top_k=5,
    modes=["smart"]
)

# 处理结果
for item in result.results:
    print(f"内容: {item.content}")
    print(f"来源: {item.source}")
    print(f"得分: {item.score:.3f}")
    print(f"类型: {item.match_type}")
```

---

## 5. 异步 API

### 5.1 异步初始化

```python
import asyncio
from src.clawra import Clawra

async def main():
    agent = await Clawra.create(enable_memory=True)

if __name__ == "__main__":
    asyncio.run(main())
```

### 5.2 异步学习

```python
async def batch_learn(texts: List[str]):
    agent = await Clawra.create()
    
    tasks = [agent.learn(text) for text in texts]
    results = await asyncio.gather(*tasks)
    
    return results
```

---

## 6. 错误处理

### 6.1 异常类型

```python
from src.core.errors import (
    ClawraError,
    ValidationError,
    LearningError,
    InferenceError,
    ConnectionError
)

try:
    result = agent.learn(text)
except ValidationError as e:
    print(f"输入验证失败: {e}")
except LearningError as e:
    print(f"学习过程错误: {e}")
except InferenceError as e:
    print(f"推理错误: {e}")
except ConnectionError as e:
    print(f"数据库连接错误: {e}")
except ClawraError as e:
    print(f"通用错误: {e}")
```

### 6.2 重试机制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def learn_with_retry(agent, text):
    return agent.learn(text)
```

---

## 7. 性能优化

### 7.1 缓存配置

```python
agent = Clawra(
    enable_memory=True,
    cache_size=1000,      # 缓存大小
    enable_cache=True      # 启用缓存
)
```

### 7.2 批量操作

```python
# 使用批量操作减少网络开销
agent.add_fact_batch([
    ("调压箱A", "is_a", "燃气调压箱"),
    ("调压箱B", "is_a", "燃气调压箱"),
    ("调压箱C", "is_a", "燃气调压箱"),
])
```

### 7.3 连接池

```python
agent = Clawra(
    enable_memory=True,
    connection_pool_size=10  # 连接池大小
)
```

---

## 8. 完整示例

### 8.1 燃气安全检查 Agent

```python
from src.clawra import Clawra

# 初始化
agent = Clawra(enable_memory=False)

# 学习安全规则
agent.learn("燃气调压箱的出口压力必须 ≤ 0.4MPa，否则有爆炸风险。")
agent.learn("燃气调压箱需要每6个月维护一次。")
agent.learn("超过10年的调压箱必须更换。")

# 添加设备信息
agent.add_fact("调压箱A", "is_a", "燃气调压箱")
agent.add_fact("调压箱A", "出口压力", "0.5MPa")
agent.add_fact("调压箱A", "使用年限", "12年")

# 执行推理
conclusions = agent.reason()

# 检查危险
for step in conclusions:
    if "爆炸风险" in step.conclusion or "更换" in step.conclusion:
        print(f"⚠️ 警告: {step.conclusion}")
        print(f"   依据: {step.rule_id}")
```

### 8.2 供应商评估 Agent

```python
from src.clawra import Clawra

agent = Clawra()

# 学习评估规则
agent.learn("供应商评级A表示优秀，B表示良好，C表示一般。")
agent.learn("连续3个月交付及时率≥99%的供应商应评为A级。")
agent.learn("有重大质量事故的供应商直接评为D级。")

# 添加供应商数据
agent.add_fact("供应商X", "is_a", "供应商")
agent.add_fact("供应商X", "评级", "B")
agent.add_fact("供应商X", "交付及时率", "99.5%")

# 推理评估
conclusions = agent.reason()

for step in conclusions:
    print(f"结论: {step.conclusion}")
```

---

## 9. SDK 示例代码

```bash
# 示例代码位置
examples/sdk/
├── 01_quickstart.py      # 快速开始
├── 02_graphrag_retrieval.py  # GraphRAG 检索
├── 03_skill_and_rules.py  # 技能与规则
└── 04_agent_chatbot.py   # Agent 聊天机器人

# 运行示例
python examples/sdk/01_quickstart.py
python examples/sdk/02_graphrag_retrieval.py
```

---

**最后更新**: 2026-04-13
