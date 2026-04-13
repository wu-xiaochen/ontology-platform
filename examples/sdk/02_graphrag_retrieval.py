#!/usr/bin/env python3
"""
Clawra SDK Example 02 — GraphRAG 检索
展示如何构建知识索引并执行混合检索

Run: PYTHONPATH=. python examples/sdk/02_graphrag_retrieval.py
"""

from src.clawra import Clawra

agent = Clawra(enable_memory=False)

# 先学习一些知识
print("📚 先学习一些燃气领域知识...")
knowledge_texts = [
    "燃气调压箱的作用是把高压燃气降低为恒定压力的低压或中压。",
    "使用规范要求：进气压力不能大于0.4MPa，否则存在泄漏爆炸风险。",
    "调压箱通常配备安全阀和监控系统。",
    "燃气调压箱的维护周期为每半年一次。",
    "调压箱需要定期检查密封性能。",
]

for text in knowledge_texts:
    agent.learn(text)

print(f"✅ 学完了，图谱有 {agent.get_statistics()['facts']} 条事实\n")

# ── 构建索引 ─────────────────────────────────────────────────────────────────
print("=" * 60)
print("🔍 构建 GraphRAG 检索索引")
print("=" * 60)

agent.retriever.build_index()
print("✅ 索引构建完成\n")

# ── 检索 ─────────────────────────────────────────────────────────────────────
queries = [
    "燃气调压箱的安全规范",
    "调压设备维护",
    "压力设备类型",
]

for query in queries:
    print(f"\nQuery: \"{query}\"")
    print("-" * 40)
    
    resp = agent.retrieve_knowledge(query, top_k=5, modes=["entity", "semantic"])
    
    print(f"  找到 {len(resp.results)} 条结果:")
    for i, r in enumerate(resp.results, 1):
        print(f"    #{i} (score={r.score:.3f}, source={r.source})")
        print(f"        ({r.triple.subject}) -[{r.triple.predicate}]-> ({r.triple.object})")
