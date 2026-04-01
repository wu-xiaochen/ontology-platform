#!/usr/bin/env python3
"""
Ontology Platform Demo - 推理引擎示例
"""

from src.loader import OntologyLoader
from src.reasoner import ReasonerEngine
from src.confidence import ConfidenceCalculator

def demo_gas_selection():
    """燃气调压箱选型示例"""
    print("=== 燃气调压箱选型示例 ===")
    
    # 加载本体
    loader = OntologyLoader()
    gas_ontology = loader.load_domain("gas")
    
    # 创建推理引擎
    reasoner = ReasonerEngine(gas_ontology)
    
    # 输入条件
    query = {
        "scenario": "residential",
        "users": 100,
        "building": "high-rise",
        "heating": True,
        "region": "south",
        "outdoor": True
    }
    
    # 推理
    result = reasoner.reason(query)
    
    # 输出结果
    print(f"推荐设备: {result.conclusion}")
    print(f"置信度: {result.confidence}")
    print(f"推理链: {result.reasoning_chain}")

def demo_supplier_selection():
    """采购供应商选择示例"""
    print("\n=== 采购供应商选择示例 ===")
    
    loader = OntologyLoader()
    procurement = loader.load_domain("procurement")
    
    reasoner = ReasonerEngine(procurement)
    
    query = {
        "amount": 800000,
        "category": "industrial_sensor",
        "suppliers": ["A", "B", "C"]
    }
    
    result = reasoner.reason(query)
    
    print(f"推荐: 开发{result.conclusion}家供应商")
    print(f"置信度: {result.confidence}")

if __name__ == "__main__":
    demo_gas_selection()
    demo_supplier_selection()
    print("\n=== Demo完成 ===")
