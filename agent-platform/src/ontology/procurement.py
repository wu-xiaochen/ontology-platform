"""
采购供应链示例本体 (Ontology)
定义采购供应链领域的概念、关系和实例
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum


# ==================== 本体定义 ====================

class OntologyClass:
    """本体类定义"""
    
    # 核心类
    USER = "User"
    SUPPLIER = "Supplier"
    PURCHASE_REQUEST = "PurchaseRequest"
    PURCHASE_ORDER = "PurchaseOrder"
    APPROVAL_FLOW = "ApprovalFlow"
    ITEM = "Item"
    CONTRACT = "Contract"
    
    # 概念类
    CATEGORY = "Category"
    DEPARTMENT = "Department"
    APPROVAL_RULE = "ApprovalRule"
    EVALUATION_METRIC = "EvaluationMetric"


class OntologyRelation:
    """本体关系定义"""
    
    # 主体关系
    REQUESTS = "requests"           # 用户发起采购申请
    BELONGS_TO = "belongs_to"       # 属于部门
    APPROVED_BY = "approved_by"      # 被审批人审批
    APPROVES = "approves"           # 审批人审批
    
    # 客体关系
    CREATED_BY = "created_by"       # 创建者
    ASSIGNED_TO = "assigned_to"     # 分配给
    SUPPLIES = "supplies"           # 供应商供应
    ORDERED_FROM = "ordered_from"   # 从供应商订购
    CONTAINS = "contains"           # 包含items
    
    # 状态关系
    HAS_STATUS = "has_status"        # 有状态
    TRACKED_BY = "tracked_by"       # 被跟踪


# ==================== 品类本体 ====================

CATEGORY_ONTOLOGY = {
    "电子设备": {
        "children": ["电脑", "显示器", "打印机", "复印机", "扫描仪"],
        "attributes": {
            "电脑": {
                "subcategories": ["台式机", "笔记本", "工作站", "服务器"],
                "typical_price_range": "4000-20000",
                "suppliers": ["联想", "Dell", "HP", "苹果"]
            },
            "显示器": {
                "subcategories": ["普通", "曲面", "4K", "带鱼屏"],
                "typical_price_range": "800-5000",
                "suppliers": ["Dell", "LG", "三星", "AOC"]
            }
        }
    },
    "办公家具": {
        "children": ["桌子", "椅子", "柜子", "书架", "会议桌"],
        "attributes": {
            "桌子": {
                "subcategories": ["办公桌", "会议桌", "培训桌"],
                "typical_price_range": "500-5000",
                "suppliers": ["宜家", "震旦", "圣奥"]
            }
        }
    },
    "办公用品": {
        "children": ["文具", "纸张", "耗材", "包装"],
        "attributes": {
            "文具": {
                "subcategories": ["笔", "本", "文件夹", "订书机"],
                "typical_price_range": "1-100",
                "suppliers": ["得力", "齐心", "晨光"]
            }
        }
    },
    "办公设备": {
        "children": ["打印机", "复印机", "投影仪", "会议系统"],
        "attributes": {}
    },
    "服务类": {
        "children": ["咨询服务", "培训服务", "维修服务", "保洁服务"],
        "attributes": {}
    }
}


# ==================== 供应商本体 ====================

SUPPLIER_ONTOLOGY = {
    "联想官方旗舰店": {
        "code": "SUP-001",
        "category": "电子设备/电脑",
        "rating": 4.8,
        "strengths": ["品牌授权", "批量优惠", "快速配送"],
        " weaknesses": ["价格较高"],
        "delivery_days": 7,
        "price_range": "4500-15000",
        "certifications": ["ISO9001", "高新技术企业"]
    },
    "京东企业购": {
        "code": "SUP-002",
        "category": "全品类",
        "rating": 4.5,
        "strengths": ["配送快", "售后好", "开票方便"],
        "weaknesses": ["价格无优势"],
        "delivery_days": 3,
        "price_range": " varies",
        "certifications": ["ISO27001"]
    },
    "得力集团": {
        "code": "SUP-003",
        "category": "办公用品",
        "rating": 4.7,
        "strengths": ["价格实惠", "品类齐全", "质量可靠"],
        "weaknesses": ["配送较慢"],
        "delivery_days": 5,
        "price_range": "1-500",
        "certifications": ["ISO9001"]
    },
    "震旦家具": {
        "code": "SUP-004",
        "category": "办公家具",
        "rating": 4.6,
        "strengths": ["品质好", "设计优", "服务佳"],
        "weaknesses": ["价格偏高"],
        "delivery_days": 14,
        "price_range": "1000-10000",
        "certifications": ["ISO9001", "环境标志产品"]
    }
}


# ==================== 审批规则本体 ====================

APPROVAL_RULE_ONTOLOGY = {
    "rules": [
        {
            "id": "rule-001",
            "name": "小额采购自动通过",
            "description": "金额小于5000元的采购申请自动通过",
            "condition": {
                "field": "amount",
                "operator": "lt",
                "value": 5000
            },
            "action": {
                "type": "auto_approve",
                "bypass_approval": True
            },
            "applicable_roles": ["purchaser", "purchase_manager"]
        },
        {
            "id": "rule-002",
            "name": "一般采购单签",
            "description": "金额5000-50000元需要部门经理审批",
            "condition": {
                "field": "amount",
                "operator": "gte",
                "value": 5000
            },
            "action": {
                "type": "single_approval",
                "approver": {
                    "role": "department_manager",
                    "required": True
                }
            }
        },
        {
            "id": "rule-003",
            "name": "大额采购双签",
            "description": "金额50000元以上需要部门经理和采购总监双重审批",
            "condition": {
                "field": "amount",
                "operator": "gte",
                "value": 50000
            },
            "action": {
                "type": "multi_approval",
                "approvers": [
                    {"role": "department_manager", "order": 1},
                    {"role": "purchase_director", "order": 2}
                ]
            }
        },
        {
            "id": "rule-004",
            "name": "特殊品类审批",
            "description": "IT设备采购需要IT部门会签",
            "condition": {
                "field": "category",
                "operator": "in",
                "value": ["电子设备/电脑", "电子设备/显示器", "办公设备"]
            },
            "action": {
                "type": "co_sign",
                "co_signer": {
                    "role": "it_manager"
                }
            }
        }
    ]
}


# ==================== 供应商评估指标本体 ====================

EVALUATION_METRIC_ONTOLOGY = {
    "metrics": [
        {
            "id": "delivery",
            "name": "交付评分",
            "description": "评估供应商按时交付能力",
            "weight": 0.25,
            "factors": [
                {"name": "按时交付率", "weight": 0.5},
                {"name": "交付响应速度", "weight": 0.3},
                {"name": "物流跟踪及时性", "weight": 0.2}
            ]
        },
        {
            "id": "quality",
            "name": "质量评分",
            "description": "评估供应商产品质量",
            "weight": 0.30,
            "factors": [
                {"name": "产品合格率", "weight": 0.6},
                {"name": "质量问题处理", "weight": 0.4}
            ]
        },
        {
            "id": "price",
            "name": "价格评分",
            "description": "评估供应商价格竞争力",
            "weight": 0.25,
            "factors": [
                {"name": "价格水平", "weight": 0.5},
                {"name": "价格稳定性", "weight": 0.3},
                {"name": "批量优惠", "weight": 0.2}
            ]
        },
        {
            "id": "service",
            "name": "服务评分",
            "description": "评估供应商服务质量",
            "weight": 0.20,
            "factors": [
                {"name": "响应速度", "weight": 0.4},
                {"name": "售后服务", "weight": 0.4},
                {"name": "沟通配合", "weight": 0.2}
            ]
        }
    ],
    "rating_levels": [
        {"level": "A", "score_range": [4.5, 5.0], "description": "优秀"},
        {"level": "B", "score_range": [4.0, 4.5], "description": "良好"},
        {"level": "C", "score_range": [3.5, 4.0], "description": "合格"},
        {"level": "D", "score_range": [3.0, 3.5], "description": "待改进"},
        {"level": "E", "score_range": [0, 3.0], "description": "不合格"}
    ]
}


# ==================== 部门本体 ====================

DEPARTMENT_ONTOLOGY = {
    "研发部": {
        "code": "DEPT-001",
        "manager_role": "研发经理",
        "budget_owner": True,
        "common_categories": ["电子设备/电脑", "电子设备/显示器", "办公设备"]
    },
    "销售部": {
        "code": "DEPT-002",
        "manager_role": "销售经理",
        "budget_owner": True,
        "common_categories": ["办公用品", "办公设备"]
    },
    "市场部": {
        "code": "DEPT-003",
        "manager_role": "市场经理",
        "budget_owner": True,
        "common_categories": ["办公用品", "服务类/推广服务"]
    },
    "财务部": {
        "code": "DEPT-004",
        "manager_role": "财务经理",
        "budget_owner": False,
        "common_categories": ["办公设备", "办公家具"]
    },
    "人力资源部": {
        "code": "DEPT-005",
        "manager_role": "HR总监",
        "budget_owner": True,
        "common_categories": ["办公用品", "服务类/培训服务"]
    },
    "行政部": {
        "code": "DEPT-006",
        "manager_role": "行政经理",
        "budget_owner": True,
        "common_categories": ["办公家具", "办公用品", "服务类/保洁服务"]
    },
    "运营部": {
        "code": "DEPT-007",
        "manager_role": "运营经理",
        "budget_owner": True,
        "common_categories": ["电子设备/电脑", "办公设备"]
    }
}


# ==================== 本体查询接口 ====================

def get_category_hierarchy(category: str) -> Dict[str, Any]:
    """获取品类层级关系"""
    for parent, data in CATEGORY_ONTOLOGY.items():
        if category.startswith(parent):
            return {
                "parent": parent,
                "children": data.get("children", []),
                "attributes": data.get("attributes", {})
            }
    return {}


def get_supplier_by_category(category: str) -> List[Dict[str, Any]]:
    """根据品类获取供应商列表"""
    results = []
    for name, data in SUPPLIER_ONTOLOGY.items():
        if category.startswith(data.get("category", "").split("/")[0]):
            results.append({
                "name": name,
                "code": data.get("code"),
                "rating": data.get("rating"),
                "delivery_days": data.get("delivery_days")
            })
    return results


def get_approval_rules(amount: float = None, category: str = None) -> List[Dict]:
    """获取适用的审批规则"""
    rules = APPROVAL_RULE_ONTOLOGY["rules"]
    applicable = []
    
    for rule in rules:
        condition = rule.get("condition", {})
        
        if amount is not None and condition.get("field") == "amount":
            op = condition.get("operator")
            val = condition.get("value")
            if op == "lt" and amount < val:
                applicable.append(rule)
            elif op == "gte" and amount >= val:
                applicable.append(rule)
        elif category is not None and condition.get("field") == "category":
            if category in condition.get("value", []):
                applicable.append(rule)
    
    return applicable


def get_evaluation_metrics() -> List[Dict]:
    """获取评估指标体系"""
    return EVALUATION_METRIC_ONTOLOGY["metrics"]


def get_department_info(department: str) -> Dict:
    """获取部门信息"""
    return DEPARTMENT_ONTOLOGY.get(department, {})


# ==================== 本体导出 ====================

def export_ontology() -> Dict[str, Any]:
    """导出完整本体"""
    return {
        "category": CATEGORY_ONTOLOGY,
        "supplier": SUPPLIER_ONTOLOGY,
        "approval_rule": APPROVAL_RULE_ONTOLOGY,
        "evaluation_metric": EVALUATION_METRIC_ONTOLOGY,
        "department": DEPARTMENT_ONTOLOGY
    }
