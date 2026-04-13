"""
demo_graphrag.py - GraphRAG 检索演示

展示 GraphRAG 的多种检索模式：
1. Entity Search（实体检索）- 精确/模糊匹配实体
2. Semantic Search（语义检索）- 基于 TF-IDF 文本相似度
3. Local Search（局部搜索）- 基于实体邻居扩展
4. Global Search（全局搜索）- 社区级摘要检索
5. Hybrid Search（混合检索）- 多路召回 + RRF 融合

运行方式:
    cd /Users/xiaochenwu/Desktop/ontology-platform
    python examples/demo_graphrag.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 60)
    print("GraphRAG 检索系统演示")
    print("=" * 60)

    # ── Step 1: 初始化并构建知识图谱 ─────────────────────────────
    print("\n[Step 1] 初始化并构建知识图谱...")
    from src.clawra import Clawra

    clawra = Clawra()

    # 添加丰富的领域知识
    facts = [
        ("燃气调压箱", "是", "关键设备", 0.95),
        ("燃气调压箱", "位于", "高中压调压站和用户之间", 0.90),
        ("燃气调压箱", "功能", "将高压燃气降至低压", 0.95),
        ("调压器", "是", "调压箱组件", 0.95),
        ("安全阀", "是", "调压箱组件", 0.95),
        ("阀门", "是", "调压箱组件", 0.95),
        ("压力表", "是", "调压箱组件", 0.95),
        ("调压器", "功能", "调节燃气压力", 0.92),
        ("安全阀", "功能", "超压泄压保护", 0.95),
        ("调压箱", "维护周期", "每年一次", 0.85),
        ("调压器", "维护周期", "每半年一次", 0.85),
        ("高压燃气", "压力范围", "0.4-1.6MPa", 0.90),
        ("低压燃气", "压力范围", "< 0.01MPa", 0.90),
        ("调压箱A", "位于", "住宅小区", 0.90),
        ("调压箱B", "位于", "工业园区", 0.90),
        ("调压箱A", "类型", "箱式调压装置", 0.90),
        ("调压箱B", "类型", "柜式调压装置", 0.90),
        ("住宅小区", "用气类型", "居民用气", 0.90),
        ("工业园区", "用气类型", "工业用气", 0.90),
    ]

    for s, p, o, c in facts:
        clawra.add_fact(s, p, o, confidence=c)

    print(f"  ✓ 添加了 {len(facts)} 条事实三元组")

    # ── Step 2: Entity Search（实体检索）──────────────────────────
    print("\n[Step 2] Entity Search（实体检索）...")
    resp = clawra.retrieve_knowledge(
        query="调压器",
        top_k=10,
        modes=["entity"]
    )
    print(f"  ✓ 检索到 {len(resp.results)} 条结果:")
    for r in resp.results:
        print(f"    [{r.source}] ({r.triple.subject}, {r.triple.predicate}, {r.triple.object}) score={r.score:.3f}")

    # ── Step 3: Semantic Search（语义检索）────────────────────────
    print("\n[Step 3] Semantic Search（语义检索）...")
    resp = clawra.retrieve_knowledge(
        query="设备维护 周期 检查",
        top_k=8,
        modes=["semantic"]
    )
    print(f"  ✓ 检索到 {len(resp.results)} 条结果:")
    for r in resp.results:
        print(f"    [{r.source}] ({r.triple.subject}, {r.triple.predicate}, {r.triple.object}) score={r.score:.3f}")

    # ── Step 4: Hybrid Search（混合检索）────────────────────────────
    print("\n[Step 4] Hybrid Search（混合检索）...")
    resp = clawra.retrieve_knowledge(
        query="调压箱 维护",
        top_k=10,
        modes=["entity", "semantic"]
    )
    print(f"  ✓ 检索到 {len(resp.results)} 条结果 (RRF 融合排序):")
    for r in resp.results:
        print(f"    [{r.source}] ({r.triple.subject}, {r.triple.predicate}, {r.triple.object})")
        print(f"        综合分={r.score:.3f} 相关性={r.relevance_score:.3f} 置信度={r.confidence_score:.3f}")

    # ── Step 5: Local Search（局部搜索）────────────────────────────
    print("\n[Step 5] Local Search（局部搜索）...")
    from src.core.retriever import SearchMode
    retriever = clawra.retriever

    local_results = retriever.local_search(
        query="调压箱A 的配置",
        center_entity="调压箱A",
        top_k=8
    )
    print(f"  ✓ 局部搜索找到 {len(local_results.results)} 条结果:")
    for r in local_results.results:
        print(f"    [{r.source}] ({r.triple.subject}, {r.triple.predicate}, {r.triple.object}) score={r.score:.3f}")

    # ── Step 6: Global Search（全局搜索）───────────────────────────
    print("\n[Step 6] Global Search（全局搜索）...")
    global_results = retriever.global_search(
        query="调压箱 维护 周期",
        top_k=5
    )
    print(f"  ✓ 全局搜索找到 {len(global_results.results)} 条结果:")
    for r in global_results.results:
        print(f"    [社区{r.community_id}] ({r.triple.subject}, {r.triple.predicate}, {r.triple.object}) score={r.score:.3f}")

    # ── Step 7: 构建上下文 ─────────────────────────────────────────
    print("\n[Step 7] 构建 LLM 可消费的结构化上下文...")
    context = clawra.retrieve_context(
        query="调压箱 组件 功能",
        top_k=10
    )
    print(f"  ✓ 上下文长度: {len(context)} 字符")
    print(f"  上下文预览:\n{context[:300]}...")

    # ── Step 8: 检索使用追踪 ───────────────────────────────────────
    print("\n[Step 8] 查看检索统计...")
    stats = clawra.get_statistics()
    eval_stats = stats.get("evaluation", {})
    print(f"  ✓ 检索命中统计:")
    print(f"    - 评估知识数: {eval_stats.get('total_evaluated', 0)}")
    print(f"    - 使用追踪记录: {eval_stats.get('usage_records', 0)}")

    print("\n" + "=" * 60)
    print("✅ demo_graphrag.py 完成！")
    print("=" * 60)
    print("\n下一步推荐:")
    print("  → python examples/demo_pattern_versioning.py 查看 Pattern 版本控制")
    print("  → python examples/demo_leiden_community.py  查看 Leiden 社区检测")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
