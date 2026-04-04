# 采购供应链垂直领域Agent平台

> 基于AI Agent的智能采购供应链管理平台

## 项目概述

本项目是面向采购供应链场景的垂直领域Agent平台，通过AI Agent能力实现：
- 采购流程自动化
- 智能供应商管理
- 数据驱动的决策支持

## 目录结构

```
agent-platform/
├── src/
│   ├── core/              # 核心推理引擎
│   │   └── engine.py      # AI推理引擎
│   ├── models/            # 数据模型
│   │   └── __init__.py    # 实体定义
│   ├── api/               # API接口层
│   ├── services/          # 业务服务层
│   ├── ontology/          # 领域本体
│   │   └── procurement.py # 采购供应链本体
│   └── utils/             # 工具函数
├── tests/                 # 测试用例
├── config/                # 配置文件
├── docs/                  # 文档
├── PRD-垂直领域Agent平台.md  # 产品需求文档
└── README.md              # 本文件
```

## 核心功能

### 1. 智能意图解析 (IntentParser)

将自然语言采购需求解析为结构化数据：

```python
from src.core.engine import create_intent_parser

parser = create_intent_parser()
result = parser.parse("我们需要采购50台Dell笔记本电脑，用于研发部门")

print(result.items)        # [ParsedItem(name='笔记本电脑', quantity=50, ...)]
print(result.department)   # '研发部'
print(result.confidence)   # 0.92
```

### 2. 审批规则引擎 (ApprovalRuleEngine)

根据金额自动路由审批流程：

```python
from src.core.engine import create_approval_engine

engine = create_approval_engine()
result = engine.evaluate(amount=250000)

# 结果:
# {
#   "matched": True,
#   "rule_name": "大额采购双签",
#   "action": "multi_approval",
#   "next_nodes": [
#       {"node_id": 1, "approver_role": "department_manager", "status": "pending"},
#       {"node_id": 2, "approver_role": "purchase_director", "status": "pending"}
#   ]
# }
```

### 3. 智能供应商推荐 (SupplierRecommender)

基于采购需求智能匹配供应商：

```python
from src.core.engine import create_supplier_recommender

# 假设有一个供应商仓库
recommender = create_supplier_recommender(supplier_repo)
recommendations = recommender.recommend(
    purchase_request_id="PR-20260316-001",
    items=[ParsedItem(name="电脑", quantity=50, category="电子设备/电脑")],
    category="电子设备/电脑",
    top_n=3
)
```

### 4. 成本优化分析 (CostOptimizer)

分析采购数据，提供成本优化建议：

```python
from src.core.engine import create_cost_optimizer

optimizer = create_cost_optimizer()
analysis = optimizer.analyze(purchase_requests, orders)

# 返回:
# {
#   "suggestions": [...],           # 优化建议
#   "category_spending": {...},     # 品类支出分析
#   "department_spending": {...},   # 部门支出分析
#   "total_potential_savings": ...   # 预计节省金额
# }
```

## 数据模型

### 核心实体

| 实体 | 说明 |
|------|------|
| User | 用户(采购专员/采购经理/总监/财务) |
| Supplier | 供应商 |
| PurchaseRequest | 采购申请 |
| Order | 采购订单 |
| ApprovalFlow | 审批流程 |
| SupplierEvaluation | 供应商评估 |

### 使用示例

```python
from src.models import (
    PurchaseRequest, 
    PurchaseRequestItem,
    Priority,
    PurchaseRequestStatus
)

# 创建采购申请
pr = PurchaseRequest(
    title="研发部门笔记本电脑采购",
    requester_id="user-001",
    department="研发部",
    priority=Priority.NORMAL,
    total_amount=250000
)

# 添加采购明细
item = PurchaseRequestItem(
    name="Dell笔记本电脑",
    category="电子设备/电脑",
    quantity=50,
    estimated_unit_price=5000,
    estimated_amount=250000
)
pr.items.append(item)

print(pr.to_dict())
```

## 领域本体

### 品类层级

```python
from src.ontology.procurement import (
    get_category_hierarchy,
    get_supplier_by_category,
    get_approval_rules
)

# 获取品类层级
hierarchy = get_category_hierarchy("电子设备/电脑")
# {
#   "parent": "电子设备",
#   "children": ["电脑", "显示器", "打印机", ...],
#   "attributes": {...}
# }

# 获取品类供应商
suppliers = get_supplier_by_category("电子设备/电脑")

# 获取适用审批规则
rules = get_approval_rules(amount=60000, category="电子设备/电脑")
```

## 安装与运行

### 环境要求

- Python 3.9+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
python -m pytest tests/
```

### 使用示例

```python
# 完整使用示例
from src.core.engine import (
    create_intent_parser,
    create_approval_engine,
    create_cost_optimizer
)
from src.models import PurchaseRequest, PurchaseRequestItem
from src.ontology.procurement import get_supplier_by_category

# 1. 解析采购需求
parser = create_intent_parser()
intent = parser.parse("我们需要采购50台Dell笔记本电脑，用于研发部门")

# 2. 创建采购申请
pr = PurchaseRequest(
    title="研发部门笔记本电脑采购",
    department=intent.department,
    total_amount=5000 * 50  # 假设单价5000
)

# 3. 评估审批规则
engine = create_approval_engine()
approval_result = engine.evaluate(amount=pr.total_amount)

# 4. 获取推荐供应商
category = intent.items[0].category if intent.items else None
if category:
    suppliers = get_supplier_by_category(category)

# 5. 成本优化分析
optimizer = create_cost_optimizer()
# analysis = optimizer.analyze(requests, orders)

print(f"✅ 采购申请: {pr.title}")
print(f"✅ 审批规则: {approval_result['rule_name']}")
print(f"✅ 推荐供应商数量: {len(suppliers)}")
```

## 审批规则配置

| 金额范围 | 审批规则 |
|----------|----------|
| < 5000元 | 自动通过 |
| 5000-50000元 | 部门经理审批 |
| ≥ 50000元 | 部门经理 + 采购总监双签 |

## 版本

- **版本**: 1.0.0
- **日期**: 2026-03-16

## 相关文档

- [PRD - 垂直领域Agent平台](./PRD-垂直领域Agent平台.md)
