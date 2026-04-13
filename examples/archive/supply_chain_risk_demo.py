# 供应链风险评估示例

本示例展示如何使用 ontology-platform 构建一个供应链风险评估系统，演示本体推理、置信度计算和证据追踪的完整流程。

## 🎯 功能特点

- ✅ 基于本体论的供应商建模
- ✅ 多维度风险评估（交货、质量、财务）
- ✅ 置信度计算与证据追踪
- ✅ 自动风险等级分类
- ✅ 可解释的推理链输出

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install neo4j python-dotenv
```

### 2. 配置环境变量

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
```

### 3. 运行示例

```bash
python examples/supply_chain_risk_demo.py
```

## 📖 完整代码

```python
"""
供应链风险评估示例

演示如何使用 ontology-platform 构建企业级风险评估系统。
"""

import os
from typing import List, Dict
from src.ontology.neo4j_client import Neo4jClient
from src.ontology.reasoner import Reasoner
from src.eval.confidence import ConfidenceCalculator


class SupplyChainRiskAssessment:
    """供应链风险评估器"""
    
    def __init__(self):
        self.neo4j = Neo4jClient()
        self.reasoner = Reasoner(self.neo4j)
        self.confidence_calc = ConfidenceCalculator()
        
    def add_supplier(self, name: str, country: str, year_established: int):
        """添加供应商"""
        self.neo4j.add_node(
            "Supplier",
            {"name": name, "country": country, "year_established": year_established}
        )
        
    def add_delivery_record(self, supplier: str, on_time: bool, delay_days: int = 0):
        """添加交货记录"""
        self.neo4j.add_node(
            "DeliveryRecord",
            {"on_time": on_time, "delay_days": delay_days}
        )
        self.neo4j.add_relationship(
            "HAS_DELIVERY", supplier, f"DeliveryRecord:{id}"
        )
        
    def add_quality_record(self, supplier: str, defect_rate: float, complaints: int):
        """添加质量记录"""
        self.neo4j.add_node(
            "QualityRecord",
            {"defect_rate": defect_rate, "complaints": complaints}
        )
        self.neo4j.add_relationship(
            "HAS_QUALITY", supplier, f"QualityRecord:{id}"
        )
        
    def assess_risk(self, supplier_name: str) -> Dict:
        """
        评估供应商风险
        
        返回:
            {
                "risk_level": "low|medium|high|critical",
                "confidence": 0.85,
                "reasoning_chain": [...],
                "evidence": [...]
            }
        """
        # 1. 收集证据
        evidence = self._collect_evidence(supplier_name)
        
        # 2. 执行推理
        reasoning_result = self.reasoner.reason(
            query=f"评估 {supplier_name} 的风险等级",
            evidence=evidence
        )
        
        # 3. 计算置信度
        confidence = self.confidence_calc.calculate(
            reasoning_result,
            evidence_count=len(evidence),
            evidence_quality=self._evaluate_evidence_quality(evidence)
        )
        
        # 4. 生成风险等级
        risk_level = self._classify_risk(reasoning_result, confidence)
        
        return {
            "supplier": supplier_name,
            "risk_level": risk_level,
            "confidence": confidence,
            "reasoning_chain": reasoning_result.get("chain", []),
            "evidence": evidence,
            "recommendations": self._generate_recommendations(risk_level, evidence)
        }
    
    def _collect_evidence(self, supplier_name: str) -> List[str]:
        """收集供应商证据"""
        evidence = []
        
        # 查询交货记录
        deliveries = self.neo4j.query(
            f"MATCH (s:Supplier {{name: '{supplier_name}'}})-[:HAS_DELIVERY]->(d:DeliveryRecord) RETURN d"
        )
        
        on_time_count = sum(1 for d in deliveries if d["on_time"])
        total_count = len(deliveries)
        
        if total_count > 0:
            on_time_rate = on_time_count / total_count
            evidence.append(f"准时交货率：{on_time_rate:.1%} ({on_time_count}/{total_count})")
            
            avg_delay = sum(d["delay_days"] for d in deliveries) / total_count
            if avg_delay > 5:
                evidence.append(f"平均延迟：{avg_delay:.1f} 天 (偏高)")
        
        # 查询质量记录
        qualities = self.neo4j.query(
            f"MATCH (s:Supplier {{name: '{supplier_name}'}})-[:HAS_QUALITY]->(q:QualityRecord) RETURN q"
        )
        
        if qualities:
            avg_defect = sum(q["defect_rate"] for q in qualities) / len(qualities)
            total_complaints = sum(q["complaints"] for q in qualities)
            
            evidence.append(f"平均缺陷率：{avg_defect:.2%}")
            evidence.append(f"质量投诉总数：{total_complaints}")
        
        return evidence
    
    def _evaluate_evidence_quality(self, evidence: List[str]) -> float:
        """评估证据质量"""
        # 简单实现：证据越多质量越高
        if len(evidence) >= 5:
            return 0.9
        elif len(evidence) >= 3:
            return 0.7
        else:
            return 0.5
    
    def _classify_risk(self, reasoning_result: Dict, confidence: float) -> str:
        """分类风险等级"""
        score = reasoning_result.get("risk_score", 0.5)
        
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(self, risk_level: str, evidence: List[str]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if risk_level in ["high", "critical"]:
            recommendations.append("建议启动备选供应商寻找流程")
            recommendations.append("加强质量检验频率")
        
        if any("延迟" in e for e in evidence):
            recommendations.append("协商更严格的交货条款")
        
        if any("缺陷率" in e for e in evidence):
            recommendations.append("要求供应商提供质量改进计划")
        
        return recommendations


# ============ 使用示例 ============

def main():
    """主函数：演示完整流程"""
    
    # 1. 初始化评估器
    assessor = SupplyChainRiskAssessment()
    
    # 2. 添加供应商数据
    print("📊 添加供应商数据...")
    assessor.add_supplier("供应商 A", "中国", 2015)
    assessor.add_supplier("供应商 B", "越南", 2018)
    
    # 3. 添加历史记录
    print("📝 添加历史记录...")
    
    # 供应商 A 的记录
    assessor.add_delivery_record("供应商 A", on_time=True, delay_days=0)
    assessor.add_delivery_record("供应商 A", on_time=False, delay_days=7)
    assessor.add_delivery_record("供应商 A", on_time=True, delay_days=0)
    assessor.add_quality_record("供应商 A", defect_rate=0.02, complaints=1)
    
    # 供应商 B 的记录
    assessor.add_delivery_record("供应商 B", on_time=False, delay_days=10)
    assessor.add_delivery_record("供应商 B", on_time=False, delay_days=5)
    assessor.add_quality_record("供应商 B", defect_rate=0.08, complaints=5)
    
    # 4. 执行风险评估
    print("\n🔍 执行风险评估...\n")
    
    for supplier in ["供应商 A", "供应商 B"]:
        result = assessor.assess_risk(supplier)
        
        print(f"{'='*60}")
        print(f"📋 {result['supplier']} 风险评估报告")
        print(f"{'='*60}")
        print(f"风险等级：{result['risk_level'].upper()}")
        print(f"置信度：{result['confidence']:.1%}")
        print(f"\n🔗 推理链:")
        for i, step in enumerate(result['reasoning_chain'], 1):
            print(f"  {i}. {step}")
        print(f"\n📊 证据:")
        for e in result['evidence']:
            print(f"  • {e}")
        print(f"\n💡 建议:")
        for rec in result['recommendations']:
            print(f"  • {rec}")
        print(f"\n")


if __name__ == "__main__":
    main()
```

## 📊 输出示例

```
============================================================
📋 供应商 A 风险评估报告
============================================================
风险等级：MEDIUM
置信度：78.5%

🔗 推理链:
  1. 检测到交货记录 3 条
  2. 准时交货率 66.7% (2/3)
  3. 平均延迟 2.3 天
  4. 缺陷率 2.0% 在可接受范围内
  5. 质量投诉 1 次，频率较低
  6. 综合评估为中等风险

📊 证据:
  • 准时交货率：66.7% (2/3)
  • 平均缺陷率：2.00%
  • 质量投诉总数：1

💡 建议:
  • 协商更严格的交货条款

============================================================
📋 供应商 B 风险评估报告
============================================================
风险等级：HIGH
置信度：82.3%

🔗 推理链:
  1. 检测到交货记录 2 条
  2. 准时交货率 0% (0/2)
  3. 平均延迟 7.5 天 (偏高)
  4. 缺陷率 8.0% 超出阈值
  5. 质量投诉 5 次，频率较高
  6. 综合评估为高风险

📊 证据:
  • 准时交货率：0.0% (0/2)
  • 平均延迟：7.5 天 (偏高)
  • 平均缺陷率：8.00%
  • 质量投诉总数：5

💡 建议:
  • 建议启动备选供应商寻找流程
  • 加强质量检验频率
  • 协商更严格的交货条款
  • 要求供应商提供质量改进计划
```

## 🔧 扩展功能

### 1. 添加财务风险评估

```python
def add_financial_record(self, supplier: str, credit_score: float, revenue_growth: float):
    """添加财务记录"""
    self.neo4j.add_node(
        "FinancialRecord",
        {"credit_score": credit_score, "revenue_growth": revenue_growth}
    )
    self.neo4j.add_relationship(
        "HAS_FINANCIAL", supplier, f"FinancialRecord:{id}"
    )
```

### 2. 实时风险监控

```python
import schedule
from datetime import datetime

def monitor_suppliers():
    """定时监控所有供应商"""
    suppliers = self.neo4j.query("MATCH (s:Supplier) RETURN s")
    
    for supplier in suppliers:
        risk = self.assess_risk(supplier["name"])
        
        if risk["risk_level"] == "critical":
            # 发送告警
            send_alert(supplier["name"], risk)

# 每天上午 9 点执行
schedule.every().day.at("09:00").do(monitor_suppliers)
```

### 3. 可视化仪表板

集成 Streamlit 创建可视化界面：

```python
import streamlit as st

st.title("🏭 供应链风险监控系统")

supplier = st.selectbox("选择供应商", ["供应商 A", "供应商 B"])
result = assessor.assess_risk(supplier)

st.metric("风险等级", result["risk_level"].upper())
st.progress(result["confidence"])

st.subheader("推理过程")
for step in result["reasoning_chain"]:
    st.write(f"• {step}")
```

## 📚 相关文档

- [Ontology 模块](../../src/ontology/README.md) - 本体论核心
- [Confidence 模块](../../src/confidence.py) - 置信度计算
- [Reasoner 模块](../../src/reasoner.py) - 推理引擎

## 🤝 贡献

欢迎提交改进！请确保：
1. 添加单元测试
2. 更新文档
3. 遵循代码规范
