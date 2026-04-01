"""
示例数据生成器
用于演示和测试的示例数据
"""

from src.models import (
    User, Supplier, PurchaseRequest, PurchaseRequestItem,
    Order, OrderItem, ApprovalFlow, ApprovalNode,
    SupplierEvaluation,
    UserRole, SupplierStatus, PurchaseRequestStatus, OrderStatus, ApprovalStatus, Priority
)
from datetime import datetime, date, timedelta
import uuid


def create_sample_users():
    """创建示例用户"""
    return [
        User(id="user-001", name="张三", email="zhangsan@company.com", 
             department="研发部", role=UserRole.PURCHASER),
        User(id="user-002", name="李四", email="lisi@company.com",
             department="研发部", role=UserRole.PURCHASE_MANAGER),
        User(id="user-003", name="王五", email="wangwu@company.com",
             department="采购部", role=UserRole.DIRECTOR),
        User(id="user-004", name="赵六", email="zhaoliu@company.com",
             department="财务部", role=UserRole.FINANCE),
    ]


def create_sample_suppliers():
    """创建示例供应商"""
    return [
        Supplier(
            id="sup-001", name="联想官方旗舰店", code="SUP-001",
            category="电子设备/电脑", rating=4.8,
            contact_name="张经理", contact_phone="13800138001",
            contact_email="zhang@lianxiang.com", status=SupplierStatus.ACTIVE,
            delivery_days=7, price_range="4500-15000", bulk_discount=True
        ),
        Supplier(
            id="sup-002", name="京东企业购", code="SUP-002",
            category="全品类", rating=4.5,
            contact_name="李经理", contact_phone="13800138002",
            status=SupplierStatus.ACTIVE,
            delivery_days=3, price_range="varies", fast_delivery=True, good_after_sales=True
        ),
        Supplier(
            id="sup-003", name="得力集团", code="SUP-003",
            category="办公用品", rating=4.7,
            contact_name="王经理", contact_phone="13800138003",
            status=SupplierStatus.ACTIVE,
            delivery_days=5, price_range="1-500", bulk_discount=True
        ),
        Supplier(
            id="sup-004", name="震旦家具", code="SUP-004",
            category="办公家具", rating=4.6,
            contact_name="赵经理", contact_phone="13800138004",
            status=SupplierStatus.ACTIVE,
            delivery_days=14, price_range="1000-10000"
        ),
    ]


def create_sample_purchase_requests(users):
    """创建示例采购申请"""
    pr1 = PurchaseRequest(
        id="PR-20260316-001",
        title="研发部门笔记本电脑采购",
        requester_id=users[0].id,
        department="研发部",
        status=PurchaseRequestStatus.PENDING_APPROVAL,
        priority=Priority.NORMAL,
        total_amount=250000,
        budget=300000,
        required_date=date(2026, 3, 31),
        purpose="研发人员办公设备更新"
    )
    pr1.items = [
        PurchaseRequestItem(
            request_id=pr1.id,
            name="Dell笔记本电脑",
            category="电子设备/电脑",
            specifications="i7/16G/512G SSD",
            quantity=50,
            unit="台",
            estimated_unit_price=5000,
            estimated_amount=250000
        )
    ]
    
    pr2 = PurchaseRequest(
        id="PR-20260316-002",
        title="办公用品采购",
        requester_id=users[0].id,
        department="行政部",
        status=PurchaseRequestStatus.APPROVED,
        priority=Priority.LOW,
        total_amount=3000,
        budget=5000
    )
    pr2.items = [
        PurchaseRequestItem(
            request_id=pr2.id,
            name="A4纸",
            category="办公用品/纸张",
            quantity=100,
            unit="包",
            estimated_unit_price=20,
            estimated_amount=2000
        ),
        PurchaseRequestItem(
            request_id=pr2.id,
            name="中性笔",
            category="办公用品/文具",
            quantity=50,
            unit="支",
            estimated_unit_price=2,
            estimated_amount=100
        )
    ]
    
    pr3 = PurchaseRequest(
        id="PR-20260315-001",
        title="办公家具采购",
        requester_id=users[0].id,
        department="财务部",
        status=PurchaseRequestStatus.COMPLETED,
        priority=Priority.NORMAL,
        total_amount=80000,
        budget=100000,
        required_date=date(2026, 3, 10)
    )
    pr3.items = [
        PurchaseRequestItem(
            request_id=pr3.id,
            name="办公桌",
            category="办公家具/桌子",
            quantity=20,
            unit="张",
            estimated_unit_price=2500,
            estimated_amount=50000
        ),
        PurchaseRequestItem(
            request_id=pr3.id,
            name="办公椅",
            category="办公家具/椅子",
            quantity=20,
            unit="把",
            estimated_unit_price=1500,
            estimated_amount=30000
        )
    ]
    
    return [pr1, pr2, pr3]


def create_sample_orders(prs, suppliers):
    """创建示例订单"""
    orders = []
    
    # 为已完成采购的申请创建订单
    for pr in prs:
        if pr.status == PurchaseRequestStatus.COMPLETED:
            order = Order(
                id=f"OR-{pr.id.split('-')[1]}-001",
                request_id=pr.id,
                supplier_id=suppliers[3].id,  # 震旦家具
                status=OrderStatus.ACCEPTED,
                order_amount=pr.total_amount,
                delivery_date=pr.required_date,
                actual_delivery_date=pr.required_date - timedelta(days=1)
            )
            for item in pr.items:
                order.items.append(OrderItem(
                    order_id=order.id,
                    name=item.name,
                    quantity=item.quantity,
                    unit_price=item.estimated_unit_price,
                    amount=item.estimated_amount
                ))
            orders.append(order)
    
    return orders


class MockSupplierRepository:
    """模拟供应商仓库"""
    
    def __init__(self, suppliers):
        self._suppliers = {s.id: s for s in suppliers}
    
    def list_active(self):
        return [
            {k: v for k, v in s.to_dict().items() if k != '_supplier'}
            for s in self._suppliers.values() 
            if s.status.value == "active"
        ]
    
    def get_by_id(self, supplier_id):
        return self._suppliers.get(supplier_id)


def get_all_samples():
    """获取所有示例数据"""
    users = create_sample_users()
    suppliers = create_sample_suppliers()
    prs = create_sample_purchase_requests(users)
    orders = create_sample_orders(prs, suppliers)
    
    return {
        "users": users,
        "suppliers": suppliers,
        "purchase_requests": prs,
        "orders": orders,
        "supplier_repo": MockSupplierRepository(suppliers)
    }


if __name__ == "__main__":
    data = get_all_samples()
    print("✅ 示例数据生成完成")
    print(f"   - 用户: {len(data['users'])}")
    print(f"   - 供应商: {len(data['suppliers'])}")
    print(f"   - 采购申请: {len(data['purchase_requests'])}")
    print(f"   - 订单: {len(data['orders'])}")
