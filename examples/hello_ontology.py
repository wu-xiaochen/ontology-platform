"""
基础示例 - Hello Ontology Platform

运行方式:
    cd /path/to/Ontology-platform
    python examples/hello_ontology.py
"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，使 src. 前缀导入生效
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 60)
    print("Hello, Ontology Platform!")
    print("=" * 60)

    # 1. 知识图谱
    print("\n📚 Step 1: 知识图谱")
    from src.core.knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph()
    kg.add_triple("知识图谱", "is_a", "AI技术", confidence=0.95)
    kg.add_triple("本体论", "is_a", "AI技术", confidence=0.90)
    kg.add_triple("知识图谱", "uses", "本体论", confidence=0.85)
    kg.add_triple("本体论", "defines", "概念和关系", confidence=0.92)
    print("  ✓ 添加了 4 条知识三元组")
    results = kg.query(subject="知识图谱")
    print(f"  ✓ 查询「知识图谱」: {len(results)} 条结果")
    for r in results:
        print(f"    → {r.subject} --{r.predicate}--> {r.object} (置信度: {r.confidence:.0%})")

    # 2. 推理引擎
    print("\n🔍 Step 2: 推理引擎")
    from src.core.reasoner import Reasoner, Fact
    reasoner = Reasoner()
    reasoner.add_fact(Fact("知识图谱", "is_a", "AI技术"))
    reasoner.add_fact(Fact("AI技术", "belongs_to", "计算机科学"))
    print("  ✓ 添加了 2 条事实")
    result = reasoner.forward_chain()
    # InferenceResult 的 conclusions 属性包含推理结论列表
    print(f"  ✓ 推理得到 {len(result.conclusions)} 条新结论 (总置信度: {result.total_confidence.value:.2f})")
    for c in result.conclusions:
        print(f"    → {c}")

    # 3. 置信度计算
    print("\n📊 Step 3: 置信度计算")
    from src.eval.confidence import ConfidenceCalculator, Evidence
    calc = ConfidenceCalculator()
    score = calc.calculate(evidence=[Evidence(source="ERP系统", reliability=0.95, content="合格")])
    print(f"  ✓ 单证据源置信度: {score.value:.2%}")

    # 4. 社区检测
    print("\n🌐 Step 4: 社区检测")
    communities = kg.detect_communities()
    print(f"  ✓ 检测到 {len(communities)} 个知识社区")

    # 5. 分页与内存监控
    print("\n💾 Step 5: 分页与内存监控")
    page = kg.load_page(offset=0, limit=2)
    print(f"  ✓ 第一页: {len(page)} 条三元组")
    mem = kg.get_memory_usage()
    print(f"  ✓ 三元组数: {mem.get('triple_count', 0)}, 读: {mem.get('read_count', 0)}, 写: {mem.get('write_count', 0)}")

    print("\n" + "=" * 60)
    print("✅ 基础示例完成！")
    print("=" * 60)
    print("\n📚 下一步:")
    print("  - python examples/demo_confidence_reasoning.py")
    print("  - python examples/complete_integration_demo.py")
    print("  - streamlit run examples/clawra_demo.py")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
