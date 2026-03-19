#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供应商风险评估推理场景
=============================
基于采购供应链本体进行供应商风险评估推理

输入: 供应商基础信息、绩效数据、财务数据
输出: 风险等级评分、风险因子分析、预警建议
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Supplier:
    """供应商实体"""
    supplier_id: str
    name: str
    category: str  # 原材料/设备/服务/燃气设备
    grade: str  # A/B/C/D
    delivery_otd: float  # 准时交付率 %
    defect_rate: float  # 不良率 %
    price_change: float  # 价格变化 %
    response_time: float  # 响应时间(小时)
    financial_health: str  # 良好/一般/差
    single_source_ratio: float  # 单一供应商占比 %
    certifications: List[str]  # 资质证书列表
    incident_count: int  # 质量事故次数
    contract_count: int  # 订单数量
    
@dataclass  
class RiskResult:
    """风险评估结果"""
    risk_level: str  # 高/中/低
    risk_score: float  # 0-100
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]

def evaluate_supplier_risk(supplier: Supplier) -> RiskResult:
    """
    供应商风险评估推理引擎
    
    规则体系:
    - 交付风险: OTD < 90% 触发高风险
    - 质量风险: 不良率 > 2% 或有事故记录
    - 价格风险: 价格波动 > 10%
    - 财务风险: 财务状况差
    - 供应风险: 单一供应商占比 > 60%
    """
    risk_factors = []
    risk_score = 0.0
    
    # 1. 交付风险评估
    if supplier.delivery_otd < 90:
        risk_score += 25
        risk_factors.append({
            "type": "交付风险",
            "severity": "高" if supplier.delivery_otd < 80 else "中",
            "detail": f"准时交付率仅{supplier.delivery_otd}%，低于90%阈值",
            "rule_id": "DR-001"
        })
    elif supplier.delivery_otd < 95:
        risk_score += 10
        risk_factors.append({
            "type": "交付风险", 
            "severity": "低",
            "detail": f"准时交付率{supplier.delivery_otd}%，接近95%目标",
            "rule_id": "DR-002"
        })
    
    # 2. 质量风险评估
    if supplier.defect_rate > 2.0:
        risk_score += 25
        risk_factors.append({
            "type": "质量风险",
            "severity": "高",
            "detail": f"来料不良率{supplier.defect_rate}%，超过2%阈值",
            "rule_id": "QR-001"
        })
    elif supplier.defect_rate > 1.0:
        risk_score += 10
        risk_factors.append({
            "type": "质量风险",
            "severity": "中", 
            "detail": f"来料不良率{supplier.defect_rate}%，需关注",
            "rule_id": "QR-002"
        })
    
    if supplier.incident_count > 0:
        risk_score += 20
        risk_factors.append({
            "type": "质量风险",
            "severity": "高",
            "detail": f"历史质量事故{supplier.incident_count}次",
            "rule_id": "QR-003"
        })
    
    # 3. 价格风险评估
    if abs(supplier.price_change) > 10:
        risk_score += 15
        risk_factors.append({
            "type": "价格波动风险",
            "severity": "中",
            "detail": f"价格波动{supplier.price_change}%，超过10%阈值",
            "rule_id": "PR-001"
        })
    
    # 4. 财务风险评估
    if supplier.financial_health == "差":
        risk_score += 20
        risk_factors.append({
            "type": "财务风险",
            "severity": "高",
            "detail": "供应商财务状况较差",
            "rule_id": "FR-001"
        })
    elif supplier.financial_health == "一般":
        risk_score += 10
        risk_factors.append({
            "type": "财务风险",
            "severity": "中",
            "detail": "供应商财务状况一般",
            "rule_id": "FR-002"
        })
    
    # 5. 供应集中度风险
    if supplier.single_source_ratio > 60:
        risk_score += 15
        risk_factors.append({
            "type": "供应集中风险",
            "severity": "高",
            "detail": f"单一供应商占比{supplier.single_source_ratio}%，超过60%",
            "rule_id": "SR-001"
        })
    
    # 计算最终风险等级
    if risk_score >= 60:
        risk_level = "高"
    elif risk_score >= 30:
        risk_level = "中"
    else:
        risk_level = "低"
    
    # 生成建议
    recommendations = generate_recommendations(supplier, risk_factors, risk_level)
    
    return RiskResult(
        risk_level=risk_level,
        risk_score=min(risk_score, 100),
        risk_factors=risk_factors,
        recommendations=recommendations
    )

def generate_recommendations(supplier: Supplier, risk_factors: List[Dict], risk_level: str) -> List[str]:
    """根据风险因素生成应对建议"""
    recommendations = []
    
    # 基于风险类型生成建议
    for factor in risk_factors:
        if factor["type"] == "交付风险":
            if supplier.delivery_otd < 90:
                recommendations.append("⚠️ 立即启动备选供应商开发计划")
                recommendations.append("📋 要求供应商提交交付改善方案")
        elif factor["type"] == "质量风险":
            recommendations.append("🔍 加严到货检验，增加抽检比例")
            if supplier.category == "燃气设备":
                recommendations.append("🔧 燃气设备需额外核查计量器具许可证")
        elif factor["type"] == "价格波动风险":
            recommendations.append("💰 签订价格保护条款，锁定年度价格")
            recommendations.append("📈 考虑期货套保或多元化采购")
        elif factor["type"] == "财务风险":
            recommendations.append("💳 缩短付款账期或采用预付款")
            recommendations.append("🔎 持续监控供应商经营状态")
        elif factor["type"] == "供应集中风险":
            recommendations.append("🏭 立即开发2家以上备选供应商")
    
    # 整体建议
    if risk_level == "高":
        recommendations.insert(0, "🚨 高风险供应商，建议暂停新订单")
        recommendations.insert(1, "📞 24小时内与供应商管理层沟通")
    elif risk_level == "中":
        recommendations.insert(0, "⚡ 中风险供应商，纳入重点监控")
    
    return recommendations

def print_risk_report(supplier: Supplier, result: RiskResult):
    """打印风险评估报告"""
    print("=" * 60)
    print(f"📊 供应商风险评估报告")
    print("=" * 60)
    print(f"供应商: {supplier.name} (ID: {supplier.supplier_id})")
    print(f"类别: {supplier.category}")
    print(f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    print(f"🚨 风险等级: {result.risk_level}")
    print(f"📈 风险评分: {result.risk_score}/100")
    print("-" * 60)
    
    if result.risk_factors:
        print("🔍 风险因子:")
        for i, factor in enumerate(result.risk_factors, 1):
            severity_icon = "🔴" if factor["severity"] == "高" else "🟡" if factor["severity"] == "中" else "🟢"
            print(f"  {i}. {severity_icon} {factor['type']} ({factor['severity']})")
            print(f"     {factor['detail']}")
            print(f"     规则依据: {factor['rule_id']}")
    else:
        print("✅ 未发现明显风险因子")
    
    print("-" * 60)
    print("💡 应对建议:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print("=" * 60)

# 示例运行
if __name__ == "__main__":
    # 创建测试供应商数据
    test_supplier = Supplier(
        supplier_id="SUP-001",
        name="某燃气设备有限公司",
        category="燃气设备",
        grade="B",
        delivery_otd=87.5,  # 低于90%
        defect_rate=1.8,    # 接近2%
        price_change=12,    # 超过10%
        response_time=6,
        financial_health="一般",
        single_source_ratio=65,  # 超过60%
        certifications=["ISO9001", "计量器具许可证"],
        incident_count=1,
        contract_count=50
    )
    
    # 执行风险评估
    result = evaluate_supplier_risk(test_supplier)
    
    # 输出报告
    print_risk_report(test_supplier, result)
