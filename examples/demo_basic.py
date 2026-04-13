"""
demo_basic.py - 基础用法演示

展示 Clawra 的核心功能：
1. 从文本学习知识（自动提取实体和关系）
2. 手动添加事实三元组
3. 执行前向链推理
4. 查询学习到的模式
5. 查看系统统计信息

运行方式:
    cd /Users/xiaochenwu/Desktop/ontology-platform
    python examples/demo_basic.py
"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 60)
    print("Clawra 基础用法演示")
    print("=" * 60)

    # ── Step 1: 初始化 Clawra ──────────────────────────────────────
    print("\n[Step 1] 初始化 Clawra...")
    from src.clawra import Clawra

    clawra = Clawra()
    print("  ✓ Clawra 初始化完成")

    # ── Step 2: 从文本学习知识 ──────────────────────────────────────
    print("\n[Step 2] 从文本学习知识...")
    learning_text = """
    燃气调压箱是城市燃气输配系统中的关键设备。
    它位于高中压调压站和用户之间，负责将高压燃气降至低压。
    调压箱内部包含调压器、阀门、安全阀和压力表。
    根据国家标准，调压箱需要定期维护检查。
    """
    result = clawra.learn(learning_text, domain_hint="gas_equipment")
    print(f"  ✓ 学习完成: success={result.get('success')}")
    print(f"    - 提取的实体数: {len(result.get('extracted_entities', []))}")
    print(f"    - 提取的关系数: {len(result.get('extracted_relations', []))}")
    print(f"    - 自动生成事实数: {result.get('facts_added', 0)}")
    print(f"    - 学习到的模式: {result.get('learned_patterns', [])}")

    # ── Step 3: 手动添加事实 ────────────────────────────────────────
    print("\n[Step 3] 手动添加事实三元组...")
    clawra.add_fact("调压箱A", "is_a", "燃气调压箱", confidence=0.95)
    clawra.add_fact("调压箱A", "位于", "住宅小区", confidence=0.90)
    clawra.add_fact("调压箱A", "出口压力", "0.35MPa", confidence=0.85)
    clawra.add_fact("燃气调压箱", "需要", "定期维护", confidence=0.92)
    print("  ✓ 添加了 4 条事实三元组")

    # ── Step 4: 执行前向链推理 ──────────────────────────────────────
    print("\n[Step 4] 执行前向链推理...")
    conclusions = clawra.reason(max_depth=3)
    print(f"  ✓ 推理完成，发现 {len(conclusions)} 条结论:")
    for c in conclusions[:5]:
        print(f"    → {c}")
    if len(conclusions) > 5:
        print(f"    ... 还有 {len(conclusions) - 5} 条结论")

    # ── Step 5: 查询模式 ────────────────────────────────────────────
    print("\n[Step 5] 查询学习到的模式...")
    patterns = clawra.query_patterns(domain="gas_equipment")
    print(f"  ✓ 找到 {len(patterns)} 个相关模式:")
    for p in patterns:
        print(f"    [{p['logic_type']}] {p['name']}: {p['description'][:50]}...")

    # ── Step 6: GraphRAG 检索 ───────────────────────────────────────
    print("\n[Step 6] GraphRAG 知识检索...")
    resp = clawra.retrieve_knowledge("调压箱 维护", top_k=5)
    print(f"  ✓ 检索到 {len(resp.results)} 条相关知识:")
    for r in resp.results:
        print(f"    [{r.source}] ({r.triple.subject}, {r.triple.predicate}, {r.triple.object}) score={r.score:.3f}")

    # ── Step 7: 系统统计 ───────────────────────────────────────────
    print("\n[Step 7] 系统统计信息...")
    stats = clawra.get_statistics()
    print(f"  ✓ 事实总数: {stats.get('facts', 0)}")
    print(f"  ✓ 图谱统计: {stats.get('graph', {})}")
    print(f"  ✓ 模式统计: {stats.get('patterns', {}).get('total_patterns', 0)} 个模式")

    print("\n" + "=" * 60)
    print("✅ demo_basic.py 完成！")
    print("=" * 60)
    print("\n下一步推荐:")
    print("  → python examples/demo_evolution_loop.py  查看进化闭环")
    print("  → python examples/demo_graphrag.py          查看 GraphRAG 检索")
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
