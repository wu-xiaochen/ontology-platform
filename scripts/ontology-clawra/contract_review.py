#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同条款审查推理场景
=============================
基于采购供应链本体进行合同条款智能审查

输入: 合同文本/合同条款数据
输出: 条款合规性评估、风险点识别、修改建议
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class Contract:
    """采购合同实体"""
    contract_id: str
    contract_type: str  # 采购合同/框架协议/服务合同
    buyer: str  # 采购商
    supplier: str  # 供应商
    amount: float  # 合同金额
    payment_terms: str  # 付款条款
    delivery_terms: str  # 交付条款
    quality_terms: str  # 质量条款
    warranty_period: int  # 质保期(月)
    penalty_rate: float  # 违约费率(%)
    price_protection: bool  # 价格保护
    exclusivity: bool  # 独家供应
    renewal_terms: str  # 续约条款
    
@dataclass
class ClauseReview:
    """条款审查结果"""
    clause_name: str
    status: str  # 合规/风险/严重风险/建议优化
    current_text: str
    issue: Optional[str]
    suggestion: str
    severity: str  # 高/中/低

@dataclass
class ContractReviewResult:
    """合同审查结果"""
    overall_score: float  # 0-100
    compliance_count: int
    risk_count: int
    critical_count: int
    clause_reviews: List[ClauseReview]
    recommendations: List[str]

def review_contract(contract: Contract) -> ContractReviewResult:
    """
    合同条款审查推理引擎
    
    规则体系:
    - 付款条款: 账期、预付款比例
    - 交付条款: 交付时间、地点、验收
    - 质量条款: 检验标准、保修
    - 违约责任: 违约金比例
    - 价格保护: 市场降价处理
    - 续约条款: 提前通知期
    """
    clause_reviews = []
    recommendations = []
    
    # 1. 付款条款审查
    payment_review = review_payment_terms(contract)
    clause_reviews.append(payment_review)
    
    # 2. 交付条款审查
    delivery_review = review_delivery_terms(contract)
    clause_reviews.append(delivery_review)
    
    # 3. 质量条款审查
    quality_review = review_quality_terms(contract)
    clause_reviews.append(quality_review)
    
    # 4. 违约责任审查
    penalty_review = review_penalty_terms(contract)
    clause_reviews.append(penalty_review)
    
    # 5. 价格保护审查
    price_protection_review = review_price_protection(contract)
    clause_reviews.append(price_protection_review)
    
    # 6. 续约条款审查
    renewal_review = review_renewal_terms(contract)
    clause_reviews.append(renewal_review)
    
    # 7. 燃气设备特殊条款审查
    if "燃气" in contract.supplier or "燃气" in str(contract.__dict__):
        gas_review = review_gas_special_terms(contract)
        clause_reviews.append(gas_review)
    
    # 计算综合评分
    risk_count = sum(1 for r in clause_reviews if r.status in ["风险", "严重风险"])
    critical_count = sum(1 for r in clause_reviews if r.status == "严重风险")
    compliance_count = sum(1 for r in clause_reviews if r.status == "合规")
    
    overall_score = 100 - (risk_count * 15) - (critical_count * 20)
    overall_score = max(0, overall_score)
    
    # 生成总体建议
    if overall_score >= 80:
        recommendations.append("✅ 合同条款整体良好，可按程序签约")
    elif overall_score >= 60:
        recommendations.append("⚠️ 合同存在一定风险，建议与供应商协商优化")
    else:
        recommendations.append("🚨 合同风险较高，建议法务部门重点审核")
    
    if risk_count > 0:
        recommendations.append(f"📋 建议重点关注{risk_count}个风险条款")
    
    # 条款特定建议
    for review in clause_reviews:
        if review.status in ["风险", "严重风险"]:
            recommendations.append(f"  • {review.clause_name}: {review.suggestion}")
    
    return ContractReviewResult(
        overall_score=round(overall_score, 1),
        compliance_count=compliance_count,
        risk_count=risk_count,
        critical_count=critical_count,
        clause_reviews=clause_reviews,
        recommendations=recommendations
    )

def review_payment_terms(contract: Contract) -> ClauseReview:
    """付款条款审查"""
    # 解析付款条款
    advance_payment = 0
    if "预付" in contract.payment_terms:
        match = re.search(r'(\d+)%', contract.payment_terms)
        if match:
            advance_payment = int(match.group(1))
    
    # 风险评估
    if advance_payment > 30:
        return ClauseReview(
            clause_name="付款条款",
            status="严重风险",
            current_text=contract.payment_terms,
            issue=f"预付款比例{advance_payment}%过高",
            suggestion="预付款建议控制在30%以内，或要求银行保函",
            severity="高"
        )
    elif advance_payment > 20:
        return ClauseReview(
            clause_name="付款条款",
            status="风险",
            current_text=contract.payment_terms,
            issue=f"预付款比例{advance_payment}%偏高",
            suggestion="建议控制在20%以内",
            severity="中"
        )
    else:
        return ClauseReview(
            clause_name="付款条款",
            status="合规",
            current_text=contract.payment_terms,
            issue=None,
            suggestion="付款条款合理",
            severity="低"
        )

def review_delivery_terms(contract: Contract) -> ClauseReview:
    """交付条款审查"""
    # 解析交付周期
    delivery_days = 30  # 默认30天
    if "天" in contract.delivery_terms:
        match = re.search(r'(\d+)天', contract.delivery_terms)
        if match:
            delivery_days = int(match.group(1))
    
    # 风险评估
    if contract.amount > 100000 and delivery_days > 45:
        return ClauseReview(
            clause_name="交付条款",
            status="风险",
            current_text=contract.delivery_terms,
            issue=f"大额合同交付周期{delivery_days}天较长",
            suggestion="建议缩短交付周期或分批交付",
            severity="中"
        )
    else:
        return ClauseReview(
            clause_name="交付条款",
            status="合规",
            current_text=contract.delivery_terms,
            issue=None,
            suggestion="交付条款合理",
            severity="低"
        )

def review_quality_terms(contract: Contract) -> ClauseReview:
    """质量条款审查"""
    # 风险评估
    if contract.warranty_period < 12:
        return ClauseReview(
            clause_name="质量条款",
            status="风险",
            current_text=f"质保期{contract.warranty_period}个月",
            issue="质保期过短",
            suggestion="建议工业品质保期不少于12个月",
            severity="中"
        )
    elif contract.warranty_period >= 24:
        return ClauseReview(
            clause_name="质量条款",
            status="合规",
            current_text=f"质保期{contract.warranty_period}个月",
            issue=None,
            suggestion="质保期充足",
            severity="低"
        )
    else:
        return ClauseReview(
            clause_name="质量条款",
            status="合规",
            current_text=f"质保期{contract.warranty_period}个月",
            issue=None,
            suggestion="质保期合理",
            severity="低"
        )

def review_penalty_terms(contract: Contract) -> ClauseReview:
    """违约责任审查"""
    # 风险评估
    if contract.penalty_rate < 0.5:
        return ClauseReview(
            clause_name="违约责任",
            status="严重风险",
            current_text=f"违约金{contract.penalty_rate}%/天",
            issue="违约金比例过低，无法约束供应商",
            suggestion="建议违约金不低于合同金额1%/天",
            severity="高"
        )
    elif contract.penalty_rate < 1.0:
        return ClauseReview(
            clause_name="违约责任",
            status="风险",
            current_text=f"违约金{contract.penalty_rate}%/天",
            issue="违约金比例偏低",
            suggestion="建议提高至1%/天",
            severity="中"
        )
    else:
        return ClauseReview(
            clause_name="违约责任",
            status="合规",
            current_text=f"违约金{contract.penalty_rate}%/天",
            issue=None,
            suggestion="违约金比例合理",
            severity="低"
        )

def review_price_protection(contract: Contract) -> ClauseReview:
    """价格保护审查"""
    if not contract.price_protection:
        return ClauseReview(
            clause_name="价格保护",
            status="风险",
            current_text="无价格保护",
            issue="缺少价格保护条款",
            suggestion="建议增加合同期内市场降价需同步调整的条款",
            severity="中"
        )
    else:
        return ClauseReview(
            clause_name="价格保护",
            status="合规",
            current_text="含价格保护",
            issue=None,
            suggestion="已包含价格保护",
            severity="低"
        )

def review_renewal_terms(contract: Contract) -> ClauseReview:
    """续约条款审查"""
    # 解析续约通知期
    notice_days = 30  # 默认30天
    if "续约" in contract.renewal_terms or "提前" in contract.renewal_terms:
        match = re.search(r'(\d+)天', contract.renewal_terms)
        if match:
            notice_days = int(match.group(1))
    
    # 风险评估
    if notice_days < 30:
        return ClauseReview(
            clause_name="续约条款",
            status="风险",
            current_text=f"提前{notice_days}天通知",
            issue="续约通知期过短",
            suggestion="建议提前60天启动续约评估",
            severity="中"
        )
    else:
        return ClauseReview(
            clause_name="续约条款",
            status="合规",
            current_text=f"提前{notice_days}天通知",
            issue=None,
            suggestion="续约条款合理",
            severity="低"
        )

def review_gas_special_terms(contract: Contract) -> ClauseReview:
    """燃气设备特殊条款审查"""
    # 燃气设备需要特殊资质和合规要求
    issues = []
    
    # 检查是否包含计量检定条款
    if "检定" not in contract.quality_terms:
        issues.append("缺少计量检定条款")
    
    # 检查是否包含安装资质要求
    if "安装" not in contract.delivery_terms and contract.contract_type == "采购合同":
        issues.append("缺少安装调试条款")
    
    # 检查特种设备许可
    if contract.amount > 50000:
        issues.append("建议核查供应商特种设备安装许可")
    
    if issues:
        return ClauseReview(
            clause_name="燃气设备特殊条款",
            status="风险",
            current_text="标准条款",
            issue="; ".join(issues),
            suggestion="燃气设备采购需满足计量法规和特种设备要求",
            severity="中"
        )
    else:
        return ClauseReview(
            clause_name="燃气设备特殊条款",
            status="合规",
            current_text="含特殊条款",
            issue=None,
            suggestion="已包含燃气设备特殊要求",
            severity="低"
        )

def print_contract_review_report(contract: Contract, result: ContractReviewResult):
    """打印合同审查报告"""
    print("=" * 70)
    print("📜 合同条款审查报告")
    print("=" * 70)
    print(f"合同编号: {contract.contract_id}")
    print(f"合同类型: {contract.contract_type}")
    print(f"采购商: {contract.buyer}")
    print(f"供应商: {contract.supplier}")
    print(f"合同金额: ¥{contract.amount:,.2f}")
    print(f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    # 总体评分
    score_emoji = "✅" if result.overall_score >= 80 else "⚠️" if result.overall_score >= 60 else "🚨"
    print(f"{score_emoji} 综合评分: {result.overall_score}/100")
    print(f"  合规条款: {result.compliance_count} | 风险条款: {result.risk_count} | 严重风险: {result.critical_count}")
    
    print("-" * 70)
    print("📋 条款审查详情:")
    for review in result.clause_reviews:
        status_icon = {
            "合规": "✅",
            "风险": "⚠️",
            "严重风险": "🚨",
            "建议优化": "💡"
        }.get(review.status, "❓")
        
        severity_color = {
            "高": "🔴",
            "中": "🟡",
            "低": "🟢"
        }.get(review.severity, "")
        
        print(f"\n  {status_icon} {review.clause_name} [{severity_color}{review.severity}]")
        print(f"     现状: {review.current_text}")
        if review.issue:
            print(f"     问题: {review.issue}")
        print(f"     建议: {review.suggestion}")
    
    print("-" * 70)
    print("💡 总体建议:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print("=" * 70)

# 示例运行
if __name__ == "__main__":
    # 创建测试合同数据
    test_contract = Contract(
        contract_id="CON-2026-001",
        contract_type="框架协议",
        buyer="某燃气公司",
        supplier="某燃气设备有限公司",
        amount=500000,
        payment_terms="预付20%，货到30%，验收30%，质保20%",
        delivery_terms="签订后30天内首批交付，后续按订单要求",
        quality_terms="按国家标准验收，质保期24个月",
        warranty_period=24,
        penalty_rate=0.8,
        price_protection=True,
        exclusivity=False,
        renewal_terms="合同到期前60天启动续约评估"
    )
    
    # 执行合同审查
    result = review_contract(test_contract)
    
    # 输出报告
    print_contract_review_report(test_contract, result)
