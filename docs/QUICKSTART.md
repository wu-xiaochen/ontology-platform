# Clawra 快速入门

> 5 分钟学会 Clawra 核心用法

---

## 环境准备

```bash
git clone https://github.com/wu-xiaochen/ontology-platform.git
cd ontology-platform
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY=your_key_here
```

---

## 1. 快速初始化

```python
from src.clawra import Clawra

# 轻量模式（无需 Neo4j/ChromaDB）
agent = Clawra(enable_memory=False)
```

---

## 2. 学习知识

```python
result = agent.learn(
    "燃气调压箱的作用是把高压燃气降低为恒定压力的低压或中压。"
    "使用规范要求：进气压力不能大于0.4MPa，否则存在泄漏爆炸风险。"
)

print(result["domain"])          # "gas_equipment"
print(result["facts_added"])     # 7
print(result["extracted_facts"]) # 三元组列表
```

---

## 3. 添加事实 + 推理

```python
# 添加事实
agent.add_fact("调压箱A", "is_a", "燃气调压箱", confidence=0.95)
agent.add_fact("燃气调压箱", "is_a", "压力设备", confidence=0.9)

# 前向链推理
conclusions = agent.reason(max_depth=3)

for step in conclusions:
    print(step.conclusion)
```

---

## 4. 混合检索

```python
agent.retriever.build_index()

resp = agent.retrieve_knowledge(
    query="燃气调压箱的安全规范",
    top_k=5,
    modes=["entity", "semantic"]
)

for r in resp.results:
    print(f"({r.triple.subject}) -[{r.triple.predicate}]-> ({r.triple.object})")
    print(f"  score={r.score:.3f}")
```

---

## 5. 规则引擎

```python
from src.core.ontology.rule_engine import RuleEngine, OntologyRule

engine = RuleEngine()

rule = OntologyRule(
    id="rule:safety",
    target_object_class="GasRegulator",
    expression="outlet_pressure >= 0.002 and outlet_pressure <= 0.4",
    description="出口压力必须在 2kPa~400kPa"
)
engine.register_rule(rule)

results = engine.evaluate_action_preconditions(
    "action:configure", "GasRegulator",
    {"outlet_pressure": 0.05, "inlet_pressure": 0.3}
)
```

---

## 6. 技能库

```python
from src.evolution.skill_library import Skill, SkillType

skill = Skill(
    id="skill:check",
    name="压力检查",
    skill_type=SkillType.CODE,
    content="def check(inlet, outlet): return {'safe': inlet <= 0.4}"
)
agent.skill_registry.register_skill(skill)

if "skill:check" in agent.skill_registry.callables:
    result = agent.skill_registry.callables["skill:check"](0.3, 0.05)
    print(result)
```

---

## 7. Web Demo

```bash
PYTHONPATH=. streamlit run examples/web_demo.py --server.port 8502
# 访问 http://localhost:8502
```

---

## 8. 进化闭环（v4.1 新功能）

```python
from src.evolution.evolution_loop import EvolutionLoop

loop = EvolutionLoop(
    meta_learner=agent.meta_learner,
    rule_discovery=agent.rule_discovery,
    evaluator=agent.evaluator,
    reasoner=agent.reasoner,
)

# 单步执行
result = loop.step({
    "text": "燃气调压箱出口压力 ≤ 0.4MPa",
    "phase": "perceive"
})

# 完整闭环（8阶段）
result = loop.run({
    "text": "燃气调压箱出口压力 ≤ 0.4MPa"
})
print(f"收敛: {result['converged']}, 失败: {len(result['feedback_signals'])}")
```

---

## 9. 社区检测（v4.1 新功能）

```python
# Leiden 算法社区检测
kg = agent.kg if hasattr(agent, 'kg') else None
kg.detect_communities(algorithm="leiden")

# 生成社区摘要
kg.generate_community_summaries()

# 跨社区推理
paths = kg.cross_community_reasoning("实体A", "实体B", max_hops=3)
```

---

## 10. REST API（需要启动服务）

```bash
# 终端 1: 启动 API 服务
PYTHONPATH=. uvicorn src.api.main:app --reload --port 8000

# 终端 2: 调用
curl -X POST http://localhost:8000/api/v1/learn \
  -H "Content-Type: application/json" \
  -d '{"text": "燃气调压箱的进气压力不能超过0.4MPa"}'
```

---

## 常见问题

**Q: 初始化报 `SQLite` 错误？**
A: 是警告，不影响运行。SQLite 用于血缘追踪，降级模式不影响核心功能。

**Q: 推理结果为空？**
A: 确保 `add_fact()` 添加了足够的事实三元组，推理依赖已有事实。

**Q: 检索分数很低？**
A: 检查 embedding 模型配置，确保使用的是与 LLM 配套的 embedding 服务。

**Q: 规则引擎报 `rule_engine` 属性错误？**
A: 使用独立的 `RuleEngine()` 实例，不要从 `Reasoner` 对象获取。
