"""
采购供应链Agent平台 - 核心模块

目录结构:
agent-platform/
├── src/
│   ├── core/          # 核心推理引擎
│   │   ├── __init__.py
│   │   └── engine.py   # AI推理引擎(意图解析、审批规则、供应商推荐、成本优化)
│   ├── models/         # 数据模型
│   │   └── __init__.py # 实体定义(用户、供应商、采购申请、订单、审批)
│   ├── api/           # API接口层
│   ├── services/      # 业务服务层
│   ├── ontology/      # 领域本体
│   │   └── procurement.py  # 采购供应链本体(品类、供应商、审批规则)
│   └── utils/         # 工具函数
├── tests/             # 测试用例
├── config/            # 配置文件
├── docs/              # 文档
└── README.md          # 本文件
"""

from .core.engine import (
    IntentParser,
    ApprovalRuleEngine,
    SupplierRecommender,
    CostOptimizer,
    create_intent_parser,
    create_approval_engine,
    create_supplier_recommender,
    create_cost_optimizer,
    ParsedIntent,
    ParsedItem,
    Priority,
    PurchaseStatus
)

from .models import (
    User,
    Supplier,
    PurchaseRequest,
    PurchaseRequestItem,
    Order,
    OrderItem,
    ApprovalFlow,
    ApprovalNode,
    SupplierEvaluation,
    UserRole,
    SupplierStatus,
    PurchaseRequestStatus,
    OrderStatus,
    ApprovalStatus,
    Priority as ModelPriority
)

__all__ = [
    # Core
    "IntentParser",
    "ApprovalRuleEngine", 
    "SupplierRecommender",
    "CostOptimizer",
    "create_intent_parser",
    "create_approval_engine",
    "create_supplier_recommender",
    "create_cost_optimizer",
    "ParsedIntent",
    "ParsedItem",
    "Priority",
    "PurchaseStatus",
    # Models
    "User",
    "Supplier",
    "PurchaseRequest",
    "PurchaseRequestItem",
    "Order",
    "OrderItem",
    "ApprovalFlow",
    "ApprovalNode",
    "SupplierEvaluation",
    "UserRole",
    "SupplierStatus",
    "PurchaseRequestStatus",
    "OrderStatus",
    "ApprovalStatus",
    "ModelPriority",
]

__version__ = "1.0.0"
