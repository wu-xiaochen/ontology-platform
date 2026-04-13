#!/usr/bin/env python3
"""
Clawra SDK Example 04 — 构建 Agent Chatbot
展示如何用 Clawra 构建一个燃气安全知识问答 Agent

Run: PYTHONPATH=. python examples/sdk/04_agent_chatbot.py
"""

from src.clawra import Clawra

# ── 初始化 Agent ──────────────────────────────────────────────────────────────
print("🤖 初始化 Clawra Agent...")
agent = Clawra(enable_memory=False)

# 预置燃气领域知识
print("📚 注入燃气领域知识...")
domain_knowledge = [
    "燃气调压箱的作用是把高压燃气降低为恒定压力的低压或中压。",
    "使用规范要求：进气压力不能大于0.4MPa，否则存在泄漏爆炸风险。",
    "调压箱通常配备安全阀和监控系统。",
    "燃气调压箱的维护周期为每半年一次。",
    "调压箱需要定期检查密封性能和压力参数。",
    "安全阀的作用是在超压时自动泄压，保护设备安全。",
]
for text in domain_knowledge:
    agent.learn(text)

print(f"✅ 知识注入完成，图谱事实数: {agent.get_statistics()['facts']}\n")

# ── 问答循环 ─────────────────────────────────────────────────────────────────
questions = [
    "燃气调压箱的进气压力上限是多少？",
    "超过这个压力会有什么风险？",
    "调压箱需要多久维护一次？",
    "调压箱有哪些安全装置？",
]

for q in questions:
    print("=" * 60)
    print(f"👤 用户: {q}")
    print("-" * 60)
    
    # 1. 学习用户问题中的新知识
    result = agent.learn(q)
    
    # 2. 检索相关知识
    agent.retriever.build_index()
    resp = agent.retrieve_knowledge(q, top_k=3, modes=["entity", "semantic"])
    
    # 3. 推理
    conclusions = agent.reason(max_depth=2)
    
    # 4. 构造回答
    print(f"🤖 Clawra:")
    
    if resp.results:
        print(f"   📊 检索到 {len(resp.results)} 条相关知识:")
        for r in resp.results[:3]:
            print(f"      • ({r.triple.subject}) -[{r.triple.predicate}]-> ({r.triple.object})")
    
    if conclusions:
        print(f"   🧠 推理出 {len(conclusions)} 条新结论:")
        for c in conclusions[:2]:
            c_str = str(c.conclusion) if hasattr(c, 'conclusion') else str(c)
            print(f"      • {c_str[:60]}")
    
    print()
