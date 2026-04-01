"""
基础示例 - Hello Ontology Platform

这是 ontology-platform 最简单的入门示例，展示基本使用流程。

运行方式:
    PYTHONPATH=src python examples/hello_ontology.py
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    """演示 ontology-platform 的基础用法"""
    
    print("=" * 60)
    print("Hello, Ontology Platform!")
    print("=" * 60)
    
    # 1. 导入核心组件
    from ontology_platform import (
        OntologyLoader,
        OntologyReasoner,
        ConfidenceEngine,
        __version__
    )
    
    print(f"\n✅ 使用版本：v{__version__}")
    
    # 2. 创建推理器（使用内置简单本体）
    print("\n📚 初始化推理器...")
    reasoner = OntologyReasoner(ontology=None)  # 可以先不加载本体
    
    # 3. 学习一些基础知识
    print("\n🧠 学习基础知识...")
    
    knowledge = [
        {
            "type": "Concept",
            "id": "KnowledgeGraph",
            "properties": {
                "name": "知识图谱",
                "description": "一种语义网络，用于表示实体及其关系",
                "category": "AI"
            }
        },
        {
            "type": "Concept",
            "id": "Ontology",
            "properties": {
                "name": "本体论",
                "description": "对概念和关系的正式规范",
                "category": "AI"
            }
        },
        {
            "type": "Relationship",
            "from": "KnowledgeGraph",
            "to": "Ontology",
            "relation": "uses",
            "description": "知识图谱使用本体论来定义结构"
        }
    ]
    
    for item in knowledge:
        reasoner.learn(item)
        print(f"  ✓ 学习了：{item.get('name', item.get('id'))}")
    
    # 4. 添加推理规则
    print("\n📐 添加推理规则...")
    
    rule = {
        "id": "ai_category_rule",
        "name": "AI 分类规则",
        "condition": "category == 'AI'",
        "conclusion": "属于人工智能领域",
        "confidence": 0.95
    }
    
    reasoner.add_rule(rule)
    print(f"  ✓ 添加了规则：{rule['name']}")
    
    # 5. 执行推理
    print("\n🔍 执行推理...")
    
    result = reasoner.infer(
        subject="KnowledgeGraph",
        predicate="category",
        max_depth=2
    )
    
    print(f"  推理结果：{result.get('conclusion', '无结果')}")
    print(f"  推理链：{result.get('reasoning_chain', [])}")
    
    # 6. 计算置信度
    print("\n📊 计算置信度...")
    
    confidence_engine = ConfidenceEngine()
    
    # 模拟推理结果
    inference_result = {
        "conclusion": "知识图谱属于人工智能领域",
        "evidence": ["category == 'AI'"],
        "chain_length": 1
    }
    
    confidence = confidence_engine.calculate(
        inference=inference_result,
        evidence_sources=["rules", "data"]
    )
    
    print(f"  置信度得分：{confidence.score:.2%}")
    print(f"  证据源：{confidence.evidence_sources}")
    print(f"  不确定性：{confidence.uncertainty:.2%}")
    
    # 7. 查询
    print("\n❓ 执行查询...")
    
    query_result = reasoner.query("知识图谱是什么？")
    print(f"  回答：{query_result.get('conclusion', '无法回答')}")
    
    print("\n" + "=" * 60)
    print("✅ 基础示例完成！")
    print("=" * 60)
    print("\n📚 下一步:")
    print("  - 查看 demo_confidence_reasoning.py 了解更多置信度计算")
    print("  - 查看 complete_integration_demo.py 了解完整集成")
    print("  - 查看 API 文档：src/api/README.md")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        print("\n请确保:")
        print("  1. 已安装依赖：pip install -r requirements.txt")
        print("  2. PYTHONPATH 设置正确：export PYTHONPATH=src:$PYTHONPATH")
        sys.exit(1)
