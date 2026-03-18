"""
核心推理引擎 - 采购供应链Agent平台
提供自然语言解析、智能推荐、审批规则引擎等AI能力
"""

import re
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class Priority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PurchaseStatus(Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PURCHASING = "purchasing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ParsedItem:
    """解析出的采购物品"""
    name: str
    quantity: int
    specifications: Optional[str] = None
    category: Optional[str] = None


@dataclass
class ParsedIntent:
    """解析后的采购意图"""
    items: List[ParsedItem]
    department: Optional[str] = None
    required_date: Optional[date] = None
    budget_range: Optional[tuple] = None
    priority: Priority = Priority.NORMAL
    purpose: Optional[str] = None
    confidence: float = 0.0
    suggestions: List[str] = field(default_factory=list)


class IntentParser:
    """采购需求自然语言解析引擎"""
    
    # 品类关键词映射
    CATEGORY_KEYWORDS = {
        "电脑": "电子设备/电脑",
        "笔记本": "电子设备/电脑",
        "台式机": "电子设备/电脑",
        "显示器": "电子设备/显示器",
        "打印机": "电子设备/打印机",
        "办公桌": "办公家具/桌子",
        "椅子": "办公家具/椅子",
        "打印机": "办公设备/打印机",
        "纸": "办公用品/纸张",
        "笔": "办公用品/文具",
    }
    
    # 部门关键词映射
    DEPARTMENT_KEYWORDS = {
        "研发": "研发部",
        "开发": "研发部",
        "技术": "研发部",
        "销售": "销售部",
        "市场": "市场部",
        "财务": "财务部",
        "人力": "人力资源部",
        "行政": "行政部",
        "运营": "运营部",
    }
    
    # 优先级关键词
    PRIORITY_KEYWORDS = {
        "紧急": Priority.URGENT,
        "加急": Priority.HIGH,
        "尽快": Priority.HIGH,
        "不急": Priority.LOW,
        "普通": Priority.NORMAL,
    }
    
    # 数量提取正则
    QUANTITY_PATTERN = r'(\d+)\s*(台|个|套|件|批|张|把|台|部|台)'
    
    # 金额提取正则
    AMOUNT_PATTERN = r'(\d+(?:\.\d+)?)\s*(万|千|元)'
    
    # 日期提取正则
    DATE_PATTERN = r'(\d{1,2})[月/](\d{1,2})|(\d{4})[-/](\d{1,2})[-/](\d{1,2})'

    def parse(self, intent_text: str) -> ParsedIntent:
        """解析自然语言采购需求"""
        
        # 提取数量
        items = self._extract_items(intent_text)
        
        # 提取部门
        department = self._extract_department(intent_text)
        
        # 提取日期
        required_date = self._extract_date(intent_text)
        
        # 提取预算
        budget_range = self._extract_budget(intent_text)
        
        # 提取优先级
        priority = self._extract_priority(intent_text)
        
        # 生成建议
        suggestions = self._generate_suggestions(items, intent_text)
        
        # 计算置信度
        confidence = self._calculate_confidence(items, department, required_date)
        
        return ParsedIntent(
            items=items,
            department=department,
            required_date=required_date,
            budget_range=budget_range,
            priority=priority,
            confidence=confidence,
            suggestions=suggestions
        )
    
    def _extract_items(self, text: str) -> List[ParsedItem]:
        """提取采购物品"""
        items = []
        
        # 尝试匹配"X台/个..."格式
        matches = re.findall(r'(\d+)\s*(台|个|套|件|批|张|把|部)\s*([^\s\d，,。]+)', text)
        
        for quantity, unit, name in matches:
            # 尝试识别品类
            category = None
            for keyword, cat in self.CATEGORY_KEYWORDS.items():
                if keyword in name or keyword in text:
                    category = cat
                    break
            
            items.append(ParsedItem(
                name=name,
                quantity=int(quantity),
                specifications=None,
                category=category
            ))
        
        # 如果没有匹配到数量，尝试匹配物品名称
        if not items:
            for keyword, cat in self.CATEGORY_KEYWORDS.items():
                if keyword in text:
                    items.append(ParsedItem(
                        name=keyword,
                        quantity=1,
                        category=cat
                    ))
                    break
        
        return items
    
    def _extract_department(self, text: str) -> Optional[str]:
        """提取部门"""
        for keyword, dept in self.DEPARTMENT_KEYWORDS.items():
            if keyword in text:
                return dept
        return None
    
    def _extract_date(self, text: str) -> Optional[date]:
        """提取日期"""
        # 匹配"X月X日"或"YYYY-MM-DD"
        match = re.search(r'(\d{1,2})[月/](\d{1,2})', text)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            current_year = datetime.now().year
            try:
                return date(current_year, month, day)
            except ValueError:
                pass
        
        match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', text)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                return date(year, month, day)
            except ValueError:
                pass
        
        return None
    
    def _extract_budget(self, text: str) -> Optional[tuple]:
        """提取预算范围"""
        matches = re.findall(r'(\d+(?:\.\d+)?)\s*(万|千|元)', text)
        if matches:
            amounts = []
            for amount_str, unit in matches:
                amount = float(amount_str)
                if unit == "万":
                    amount *= 10000
                elif unit == "千":
                    amount *= 1000
                amounts.append(amount)
            return (min(amounts), max(amounts))
        return None
    
    def _extract_priority(self, text: str) -> Priority:
        """提取优先级"""
        for keyword, priority in self.PRIORITY_KEYWORDS.items():
            if keyword in text:
                return priority
        return Priority.NORMAL
    
    def _generate_suggestions(self, items: List[ParsedItem], text: str) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if not items:
            suggestions.append("请明确采购的物品名称和数量")
        
        for item in items:
            if not item.category:
                suggestions.append(f"建议确认{item.name}的具体规格型号")
        
        if "月底" in text or "月初" in text:
            suggestions.append("建议确认具体的日期")
        
        return suggestions
    
    def _calculate_confidence(self, items: List[ParsedItem], department: Optional[str], 
                             required_date: Optional[date]) -> float:
        """计算解析置信度"""
        confidence = 0.5  # 基础置信度
        
        if items:
            confidence += 0.2
            if all(item.category for item in items):
                confidence += 0.1
        
        if department:
            confidence += 0.1
        
        if required_date:
            confidence += 0.1
        
        return min(confidence, 1.0)


class ApprovalRuleEngine:
    """审批规则引擎"""
    
    # 审批规则配置
    RULES = [
        {
            "id": "rule-001",
            "name": "小额采购自动通过",
            "condition": lambda amount: amount < 5000,
            "action": "auto_approve"
        },
        {
            "id": "rule-002",
            "name": "一般采购单签",
            "condition": lambda amount: 5000 <= amount < 50000,
            "action": "single_approval",
            "approver_role": "department_manager"
        },
        {
            "id": "rule-003",
            "name": "大额采购双签",
            "condition": lambda amount: amount >= 50000,
            "action": "multi_approval",
            "approvers": ["department_manager", "purchase_director"]
        }
    ]
    
    def evaluate(self, amount: float, category: Optional[str] = None) -> Dict[str, Any]:
        """评估审批规则"""
        
        for rule in self.RULES:
            if rule["condition"](amount):
                result = {
                    "matched": True,
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "action": rule["action"]
                }
                
                if rule["action"] == "auto_approve":
                    result["next_nodes"] = []
                    result["status"] = "approved"
                elif rule["action"] == "single_approval":
                    result["next_nodes"] = [
                        {"node_id": 1, "approver_role": rule["approver_role"], "status": "pending"}
                    ]
                    result["status"] = "pending_approval"
                elif rule["action"] == "multi_approval":
                    result["next_nodes"] = [
                        {"node_id": 1, "approver_role": approver, "status": "pending"}
                        for approver in rule["approvers"]
                    ]
                    result["status"] = "pending_approval"
                
                return result
        
        # 默认规则
        return {
            "matched": True,
            "rule_id": "default",
            "rule_name": "默认审批规则",
            "action": "single_approval",
            "next_nodes": [{"node_id": 1, "approver_role": "department_manager", "status": "pending"}],
            "status": "pending_approval"
        }


class SupplierRecommender:
    """智能供应商推荐引擎"""
    
    def __init__(self, supplier_repository):
        self.supplier_repo = supplier_repository
    
    def recommend(self, purchase_request_id: str, items: List[ParsedItem], 
                 category: Optional[str], top_n: int = 3) -> List[Dict[str, Any]]:
        """智能推荐供应商"""
        
        # 获取所有活跃供应商
        all_suppliers = self.supplier_repo.list_active()
        
        # 如果有品类要求，按品类过滤
        if category:
            all_suppliers = [s for s in all_suppliers if s.get("category") == category]
        
        # 计算匹配分数
        scored_suppliers = []
        for supplier in all_suppliers:
            score = self._calculate_match_score(supplier, items, category)
            scored_suppliers.append({
                "supplier_id": supplier.get("id"),
                "supplier_name": supplier.get("name"),
                "match_score": score,
                "historical_rating": supplier.get("rating", 0),
                "price_range": supplier.get("price_range"),
                "delivery_days": supplier.get("delivery_days", 7),
                "reasons": self._generate_reasons(supplier, score)
            })
        
        # 按匹配分数排序
        scored_suppliers.sort(key=lambda x: x["match_score"], reverse=True)
        
        return scored_suppliers[:top_n]
    
    def _calculate_match_score(self, supplier: Dict, items: List[ParsedItem], 
                               category: Optional[str]) -> float:
        """计算供应商匹配分数"""
        score = 0.5  # 基础分数
        
        # 历史评分因子
        rating = supplier.get("rating", 0)
        score += (rating / 5.0) * 0.3
        
        # 品类匹配因子
        if category and supplier.get("category") == category:
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_reasons(self, supplier: Dict, score: float) -> List[str]:
        """生成推荐理由"""
        reasons = []
        
        rating = supplier.get("rating", 0)
        if rating >= 4.5:
            reasons.append("历史合作评分高")
        
        if supplier.get("category"):
            reasons.append("同品类供货经验丰富")
        
        if supplier.get("bulk_discount"):
            reasons.append("支持批量采购优惠")
        
        if supplier.get("fast_delivery"):
            reasons.append("配送速度快")
        
        if supplier.get("good_after_sales"):
            reasons.append("售后服务保障好")
        
        return reasons[:3] if reasons else ["综合评分良好"]


class CostOptimizer:
    """成本优化建议引擎"""
    
    def analyze(self, purchase_requests: List[Dict], orders: List[Dict]) -> Dict[str, Any]:
        """分析成本优化机会"""
        
        suggestions = []
        
        # 分析1: 批量采购建议
        category_spending = {}
        for req in purchase_requests:
            for item in req.get("items", []):
                cat = item.get("category", "其他")
                amount = item.get("estimated_amount", 0)
                category_spending[cat] = category_spending.get(cat, 0) + amount
        
        for cat, amount in category_spending.items():
            if amount >= 100000:
                suggestions.append({
                    "type": "bulk_purchase",
                    "category": cat,
                    "current_spending": amount,
                    "suggestion": f"建议与供应商签订年度采购框架协议，预计可节省15-20%成本",
                    "potential_savings": amount * 0.15
                })
        
        # 分析2: 供应商替换建议
        supplier_performance = {}
        for order in orders:
            sid = order.get("supplier_id")
            if sid:
                if sid not in supplier_performance:
                    supplier_performance[sid] = {"orders": 0, "total_amount": 0}
                supplier_performance[sid]["orders"] += 1
                supplier_performance[sid]["total_amount"] += order.get("order_amount", 0)
        
        # 分析3: 支出分布分析
        department_spending = {}
        for req in purchase_requests:
            dept = req.get("department", "未知")
            department_spending[dept] = department_spending.get(dept, 0) + req.get("total_amount", 0)
        
        return {
            "suggestions": suggestions,
            "category_spending": category_spending,
            "department_spending": department_spending,
            "total_potential_savings": sum(s.get("potential_savings", 0) for s in suggestions)
        }


# 工厂函数
def create_intent_parser() -> IntentParser:
    """创建意图解析器"""
    return IntentParser()


def create_approval_engine() -> ApprovalRuleEngine:
    """创建审批规则引擎"""
    return ApprovalRuleEngine()


def create_supplier_recommender(supplier_repo) -> SupplierRecommender:
    """创建供应商推荐器"""
    return SupplierRecommender(supplier_repo)


def create_cost_optimizer() -> CostOptimizer:
    """创建成本优化器"""
    return CostOptimizer()
