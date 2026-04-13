"""
demo_leiden_community.py - Leiden 社区检测演示

展示 KnowledgeGraph 的社区检测能力：
1. 构建燃气领域的知识图谱
2. 使用 Leiden 算法检测社区
3. 使用 Louvain、Girvan-Newman、Label Propagation 等其他算法
4. 生成社区摘要
5. 跨社区推理（查询不同社区实体间的关联路径）
6. 获取实体所属社区

注意：Leiden 算法需要安装 leidenalg 包：
    pip install leidenalg igraph
    如果未安装，会自动回退到 Louvain 算法

运行方式:
    cd /Users/xiaochenwu/Desktop/ontology-platform
    python examples/demo_leiden_community.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 60)
    print("Leiden 社区检测演示")
    print("=" * 60)

    # ── Step 1: 初始化知识图谱 ────────────────────────────────────
    print("\n[Step 1] 初始化知识图谱...")
    from src.core.knowledge_graph import KnowledgeGraph

    kg = KnowledgeGraph()
    print("  ✓ 知识图谱初始化完成")

    # ── Step 2: 构建燃气领域知识图谱 ───────────────────────────────
    print("\n[Step 2] 构建燃气领域知识图谱...")

    # 设备社区
    device_facts = [
        ("调压箱", "is_a", "燃气设备", 0.95),
        ("调压器", "is_a", "燃气设备", 0.95),
        ("安全阀", "is_a", "燃气设备", 0.95),
        ("阀门", "is_a", "燃气设备", 0.95),
        ("压力表", "is_a", "燃气设备", 0.95),
        ("流量计", "is_a", "燃气设备", 0.95),
        ("调压箱", "contains", "调压器", 0.95),
        ("调压箱", "contains", "安全阀", 0.95),
        ("调压箱", "contains", "阀门", 0.95),
        ("调压箱", "contains", "压力表", 0.95),
        ("调压器", "contains", "阀芯", 0.90),
        ("安全阀", "contains", "弹簧", 0.85),
    ]
    for s, p, o, c in device_facts:
        kg.add_triple(s, p, o, confidence=c)

    # 压力等级社区
    pressure_facts = [
        ("高压燃气", "pressure_range", "0.4-1.6MPa", 0.90),
        ("中压燃气", "pressure_range", "0.01-0.4MPa", 0.90),
        ("低压燃气", "pressure_range", "< 0.01MPa", 0.90),
        ("调压箱", "connect", "高压燃气", 0.95),
        ("调压箱", "connect", "中压燃气", 0.95),
        ("调压器", "reduce", "高压燃气到中压燃气", 0.90),
        ("调压器", "reduce", "中压燃气到低压燃气", 0.90),
    ]
    for s, p, o, c in pressure_facts:
        kg.add_triple(s, p, o, confidence=c)

    # 维护社区
    maintenance_facts = [
        ("调压箱", "requires", "定期维护", 0.92),
        ("调压器", "requires", "定期维护", 0.92),
        ("安全阀", "requires", "定期校验", 0.92),
        ("维护周期", "of", "调压箱", 0.90),
        ("维护周期", "value", "每年一次", 0.90),
        ("校验周期", "of", "安全阀", 0.90),
        ("校验周期", "value", "每年一次", 0.90),
        ("维护内容", "includes", "检查密封性", 0.85),
        ("维护内容", "includes", "校准压力", 0.85),
        ("维护内容", "includes", "更换密封件", 0.85),
    ]
    for s, p, o, c in maintenance_facts:
        kg.add_triple(s, p, o, confidence=c)

    # 地点社区
    location_facts = [
        ("调压站", "is_a", "设施", 0.90),
        ("住宅小区", "has", "调压箱A", 0.90),
        ("工业园区", "has", "调压箱B", 0.90),
        ("商业综合体", "has", "调压箱C", 0.90),
        ("调压箱A", "located_at", "住宅小区", 0.90),
        ("调压箱B", "located_at", "工业园区", 0.90),
        ("调压箱C", "located_at", "商业综合体", 0.90),
        ("高压燃气管网", "connects", "调压站", 0.90),
        ("中压燃气管网", "distributes", "住宅小区", 0.85),
        ("中压燃气管网", "distributes", "工业园区", 0.85),
    ]
    for s, p, o, c in location_facts:
        kg.add_triple(s, p, o, confidence=c)

    print(f"  ✓ 添加了 {len(device_facts) + len(pressure_facts) + len(maintenance_facts) + len(location_facts)} 条三元组")

    # ── Step 3: 图谱统计 ──────────────────────────────────────────
    print("\n[Step 3] 图谱统计信息...")
    stats = kg.statistics()
    print(f"  ✓ 实体数: {stats.get('node_count', 0)}")
    print(f"  ✓ 关系数: {stats.get('edge_count', 0)}")
    print(f"  ✓ 三元组数: {stats.get('triple_count', 0)}")

    # ── Step 4: Leiden 社区检测 ───────────────────────────────────
    print("\n[Step 4] Leiden 社区检测...")
    from src.core.knowledge_graph import LEIDEN_AVAILABLE
    print(f"  Leiden 可用: {'是' if LEIDEN_AVAILABLE else '否（将回退到 Louvain）'}")

    communities = kg.detect_communities(algorithm="leiden")
    print(f"  ✓ 检测到 {len(communities)} 个社区:")
    for i, comm in enumerate(communities[:10]):
        entity_preview = list(comm.entities)[:5]
        print(f"    社区 {comm.id}: {entity_preview}... (size={comm.size})")

    # ── Step 5: 其他算法对比 ───────────────────────────────────────
    print("\n[Step 5] 其他算法对比...")

    algorithms = ["louvain", "label_propagation"]
    for algo in algorithms:
        try:
            comms = kg.detect_communities(algorithm=algo)
            print(f"  {algo}: 检测到 {len(comms)} 个社区")
        except Exception as e:
            print(f"  {algo}: 失败 - {e}")

    # ── Step 6: 社区摘要生成 ───────────────────────────────────────
    print("\n[Step 6] 生成社区摘要...")
    summaries = kg.generate_community_summaries()
    print(f"  ✓ 生成了 {len(summaries)} 个社区摘要:")
    for comm_id, summary in list(summaries.items())[:5]:
        print(f"    社区 {comm_id}: {summary[:80]}...")

    # ── Step 7: 跨社区推理 ─────────────────────────────────────────
    print("\n[Step 7] 跨社区推理...")
    # 查询"调压箱A"和"高压燃气"之间的路径（跨社区）
    paths = kg.cross_community_reasoning(
        entity_a="调压箱A",
        entity_b="高压燃气",
        max_hops=3
    )
    print(f"  ✓ 调压箱A <-> 高压燃气 找到 {len(paths)} 条关联路径:")
    for i, path in enumerate(paths[:5]):
        hops = path.get("hops", [])
        print(f"    路径 {i+1}: {' -> '.join(hops)}")

    # 查询"住宅小区"和"调压器"之间的路径
    paths2 = kg.cross_community_reasoning(
        entity_a="住宅小区",
        entity_b="调压器",
        max_hops=3
    )
    print(f"\n  ✓ 住宅小区 <-> 调压器 找到 {len(paths2)} 条关联路径:")
    for i, path in enumerate(paths2[:3]):
        hops = path.get("hops", [])
        print(f"    路径 {i+1}: {' -> '.join(hops)}")

    # ── Step 8: 查询实体的社区归属 ────────────────────────────────
    print("\n[Step 8] 查询实体社区归属...")
    entities_to_check = ["调压箱", "调压器", "住宅小区", "高压燃气", "维护周期"]
    for entity in entities_to_check:
        comm_id = kg.get_entity_community(entity)
        print(f"  ✓ {entity} -> 社区 {comm_id}")

    # ── Step 9: 获取社区成员 ──────────────────────────────────────
    print("\n[Step 9] 获取社区成员...")
    if communities:
        first_comm = communities[0]
        members = kg.get_community_members(first_comm.id)
        print(f"  ✓ 社区 {first_comm.id} 的成员 ({len(members)} 个):")
        for m in members[:10]:
            print(f"    - {m}")

    # ── Step 10: 社区级别检索 ─────────────────────────────────────
    print("\n[Step 10] 社区级别知识检索...")
    # 获取社区内所有三元组
    if communities:
        comm_id = communities[0].id
        triples_in_comm = kg.get_community_triples(comm_id)
        print(f"  ✓ 社区 {comm_id} 内有 {len(triples_in_comm)} 条三元组:")
        for t in triples_in_comm[:5]:
            print(f"    - ({t.subject}, {t.predicate}, {t.object})")

    print("\n" + "=" * 60)
    print("✅ demo_leiden_community.py 完成！")
    print("=" * 60)
    print("\n下一步推荐:")
    print("  → python examples/demo_basic.py            基础用法")
    print("  → python examples/demo_evolution_loop.py    进化闭环")
    print("  → python examples/demo_graphrag.py          GraphRAG 检索")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
