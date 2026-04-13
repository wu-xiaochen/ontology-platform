#!/usr/bin/env python3
"""
Clawra SDK Example 01 — 快速开始
学习如何初始化 Clawra 并执行第一次知识提取

Run: PYTHONPATH=. python examples/sdk/01_quickstart.py
"""

from src.clawra import Clawra

# ── 1. 初始化 ───────────────────────────────────────────────────────────────
# 无外部依赖的轻量模式，适合快速实验
print("=" * 60)
print("1️⃣ 初始化 Clawra (轻量模式)")
print("=" * 60)

agent = Clawra(enable_memory=False)
print(f"✅ Clawra 初始化成功")
print(f"   图谱事实数: {agent.get_statistics()['facts']}")

# ── 2. learn() — 知识提取 ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("2️⃣ learn() — 从文本提取知识三元组")
print("=" * 60)

text = (
    "燃气调压箱的作用是把高压燃气降低为恒定压力的低压或中压。"
    "使用规范要求：进气压力不能大于0.4MPa，否则存在泄漏爆炸风险。"
    "调压箱通常配备安全阀和监控系统。"
)

result = agent.learn(text)

print(f"✅ 学习成功!")
print(f"   检测领域: {result['domain']}")
print(f"   学到模式: {len(result['learned_patterns'])}")
print(f"   新增事实: {result['facts_added']}")
print(f"\n   提取的三元组:")
for i, fact in enumerate(result["extracted_facts"][:6], 1):
    print(f"   {i}. ({fact['subject']}) -[{fact['predicate']}]-> ({fact['object']})")

# ── 3. add_fact() — 添加事实 ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("3️⃣ add_fact() — 添加自定义事实")
print("=" * 60)

agent.add_fact("调压箱A", "is_a", "燃气调压箱", confidence=0.95)
agent.add_fact("调压箱A", "has_component", "安全阀", confidence=0.9)
agent.add_fact("安全阀", "is_a", "安全装置", confidence=0.95)
agent.add_fact("燃气调压箱", "is_a", "压力设备", confidence=0.9)
agent.add_fact("压力设备", "is_a", "工业设备", confidence=0.85)

print(f"✅ 添加了 5 条事实")
print(f"   图谱总事实数: {agent.get_statistics()['facts']}")

# ── 4. reason() — 推理 ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("4️⃣ reason() — 前向链推理")
print("=" * 60)

conclusions = agent.reason(max_depth=3)

print(f"🧠 推理完成，推导出 {len(conclusions)} 条新结论:")
for i, step in enumerate(conclusions[:5], 1):
    c = step.conclusion if hasattr(step, 'conclusion') else step
    print(f"   {i}. {c}")

print("\n✅ 完整流程演示完毕！")
print("   要运行 Web Demo: PYTHONPATH=. streamlit run examples/web_demo.py")
