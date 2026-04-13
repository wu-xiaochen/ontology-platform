#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采购价格分析推理场景
=============================
基于采购供应链本体进行采购价格分析

输入: 物料信息、历史价格、市场行情、采购量
输出: 价格分析、议价建议、采购时机建议
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Material:
    """物料实体"""
    material_id: str
    name: str
    category: str  # 原材料/设备/燃气设备
    unit: str
    current_price: float  # 当前采购价
    market_price: float   # 市场均价
    historical_prices: List[Dict]  # 历史价格 [{"date": "2026-01", "price": 100}]
    
@dataclass 
class Supplier:
    """供应商报价"""
    supplier_id: str
    supplier_name: str
    quoted_price: float
    lead_time: int  # 交付周期(天)
    discount: float  # 折扣率
    
@dataclass
class PriceAnalysis:
    """价格分析结果"""
    price_competitiveness: float  # 价格竞争力 0-100
    market_position: str  # 低于市场/等于市场/高于市场
    price_trend: str  # 上涨/平稳/下跌
    recommendations: List[str]
    best_timing: Optional[str]

def analyze_purchase_price(
    material: Material,
    suppliers: List[Supplier],
    purchase_quantity: int,
    contract_type: str  # 年度框架/单次采购
) -> PriceAnalysis:
    """
    采购价格分析推理引擎
    
    规则体系:
    - 价格竞争力: 报价与市场均价比对
    - 价格趋势: 基于历史价格分析
    - 议价空间: 基于采购量和供应商数量
    - 采购时机: 基于价格趋势和库存策略
    """
    recommendations = []
    
    # 1. 计算平均报价
    avg_quoted_price = sum(s.quoted_price for s in suppliers) / len(suppliers)
    
    # 2. 价格竞争力分析
    market_gap = (material.market_price - avg_quoted_price) / material.market_price * 100
    
    if market_gap > 10:
        price_competitiveness = 90
        market_position = "低于市场"
    elif market_gap > 0:
        price_competitiveness = 70 + (market_gap / 10) * 20
        market_position = "略低于市场"
    elif market_gap > -5:
        price_competitiveness = 50 + (market_gap + 5) / 5 * 20
        market_position = "等于市场"
    else:
        price_competitiveness = max(0, 50 + (market_gap + 5) / 5 * 30)
        market_position = "高于市场"
    
    # 3. 价格趋势分析
    if len(material.historical_prices) >= 3:
        prices = [p["price"] for p in sorted(material.historical_prices, key=lambda x: x["date"])]
        recent_avg = sum(prices[-3:]) / 3
        older_avg = sum(prices[:3]) / 3
        trend_ratio = (recent_avg - older_avg) / older_avg
        
        if trend_ratio > 0.05:
            price_trend = "上涨"
            recommendations.append("📈 价格呈上涨趋势，建议提前备货")
        elif trend_ratio < -0.05:
            price_trend = "下跌"
            recommendations.append("📉 价格呈下跌趋势，可延迟采购")
        else:
            price_trend = "平稳"
            recommendations.append("➡️ 价格平稳，按需采购即可")
    else:
        price_trend = "数据不足"
    
    # 4. 议价空间分析
    supplier_count = len(suppliers)
    quantity_factor = 1.0
    
    # 采购量阶梯折扣
    if purchase_quantity >= 1000:
        quantity_factor = 0.92
        recommendations.append("💰 采购量≥1000，建议要求8%以上折扣")
    elif purchase_quantity >= 500:
        quantity_factor = 0.95
        recommendations.append("💰 采购量≥500，建议要求5%以上折扣")
    elif purchase_quantity >= 100:
        quantity_factor = 0.97
    
    # 供应商竞争因素
    if supplier_count >= 5:
        recommendations.append("🏆 供应商≥5家，建议要求二次报价")
    elif supplier_count >= 3:
        recommendations.append("🤝 3家供应商充分比价，争取最优价格")
    
    # 合同类型影响
    if contract_type == "年度框架":
        recommendations.append("📝 签订年度框架协议，争取5-8%年降")
        quantity_factor *= 0.95
    
    # 5. 最佳采购时机建议
    if price_trend == "上涨":
        best_timing = "立即采购，越早越好"
    elif price_trend == "下跌":
        best_timing = "建议等待1-2个月"
    else:
        best_timing = "随时采购，关注促销时机"
    
    # 6. 特定品类建议
    if material.category == "燃气设备":
        recommendations.append("🔧 燃气设备需确认含安装调试服务")
        if "燃气表" in material.name or "调压器" in material.name:
            recommendations.append("📋 燃气表具需包含计量检定费用")
    
    return PriceAnalysis(
        price_competitiveness=round(price_competitiveness, 1),
        market_position=market_position,
        price_trend=price_trend,
        recommendations=recommendations,
        best_timing=best_timing
    )

def select_best_supplier(
    material: Material,
    suppliers: List[Supplier],
    priority: str = "price"  # price/delivery/quality
) -> Dict[str, Any]:
    """
    供应商选择推理
    
    参数:
    - priority: 优先级 - price(价格优先)/delivery(交付优先)/quality(质量优先)
    """
    scored_suppliers = []
    
    for supplier in suppliers:
        score = 0
        price_score = (material.market_price - supplier.quoted_price) / material.market_price * 100
        delivery_score = max(0, 100 - supplier.lead_time * 2)
        
        if priority == "price":
            score = price_score * 0.6 + delivery_score * 0.4
        elif priority == "delivery":
            score = delivery_score * 0.6 + price_score * 0.4
        else:  # quality (默认选A级供应商)
            score = (100 if supplier.discount >= 0.05 else 50) + price_score * 0.3
        
        scored_suppliers.append({
            "supplier": supplier,
            "score": round(score, 2),
            "price_score": round(price_score, 2),
            "delivery_score": round(delivery_score, 2)
        })
    
    # 按得分排序
    scored_suppliers.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "recommended": scored_suppliers[0],
        "alternatives": scored_suppliers[1:],
        "priority": priority
    }

def print_price_analysis_report(
    material: Material,
    suppliers: List[Supplier],
    analysis: PriceAnalysis,
    selection: Dict
):
    """打印价格分析报告"""
    print("=" * 70)
    print("💰 采购价格分析报告")
    print("=" * 70)
    print(f"物料: {material.name} (ID: {material.material_id})")
    print(f"类别: {material.category}")
    print(f"采购量: {material.unit} x {selection.get('quantity', 'N/A')}")
    print(f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    # 供应商报价对比
    print("📋 供应商报价对比:")
    for i, s in enumerate(suppliers, 1):
        gap = (material.market_price - s.quoted_price) / material.market_price * 100
        gap_str = f"+{gap:.1f}%" if gap > 0 else f"{gap:.1f}%"
        print(f"  {i}. {s.supplier_name}: ¥{s.quoted_price}/{material.unit} (市场{gap_str})")
    
    print("-" * 70)
    print(f"📊 价格竞争力: {analysis.price_competitiveness}/100")
    print(f"📍 市场定位: {analysis.market_position}")
    print(f"📈 价格趋势: {analysis.price_trend}")
    print(f"⏰ 最佳采购时机: {analysis.best_timing}")
    
    print("-" * 70)
    print("💡 分析建议:")
    for i, rec in enumerate(analysis.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print("-" * 70)
    print("🏆 供应商推荐:")
    rec = selection["recommended"]
    print(f"  首选: {rec['supplier'].supplier_name}")
    print(f"  报价: ¥{rec['supplier'].quoted_price}/{material.unit}")
    print(f"  综合得分: {rec['score']}")
    if selection["alternatives"]:
        alt = selection["alternatives"][0]["supplier"]
        print(f"  备选: {alt.supplier_name} (¥{alt.quoted_price}/{material.unit})")
    
    print("=" * 70)

# 示例运行
if __name__ == "__main__":
    # 创建测试物料数据
    test_material = Material(
        material_id="MAT-001",
        name="家用燃气表 G2.5",
        category="燃气设备",
        unit="台",
        current_price=180,
        market_price=200,
        historical_prices=[
            {"date": "2025-10", "price": 175},
            {"date": "2025-11", "price": 178},
            {"date": "2025-12", "price": 185},
            {"date": "2026-01", "price": 190},
            {"date": "2026-02", "price": 200},
        ]
    )
    
    # 创建供应商报价
    test_suppliers = [
        Supplier("SUP-A", "燃气设备A厂", 175, 15, 0.08),
        Supplier("SUP-B", "燃气设备B厂", 185, 10, 0.05),
        Supplier("SUP-C", "燃气设备C厂", 195, 20, 0.02),
    ]
    
    # 执行价格分析
    quantity = 500
    contract = "年度框架"
    
    analysis = analyze_purchase_price(test_material, test_suppliers, quantity, contract)
    selection = select_best_supplier(test_material, test_suppliers, priority="price")
    selection["quantity"] = quantity
    
    # 输出报告
    print_price_analysis_report(test_material, test_suppliers, analysis, selection)
