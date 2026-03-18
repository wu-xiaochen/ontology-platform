"""
数据模型 - 采购供应链Agent平台
定义所有核心实体和数据结构
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid


class UserRole(Enum):
    PURCHASER = "purchaser"           # 采购专员
    PURCHASE_MANAGER = "purchase_manager"  # 采购经理
    DIRECTOR = "director"            # 总监
    FINANCE = "finance"               # 财务


class SupplierStatus(Enum):
    ACTIVE = "active"         # 活跃
    INACTIVE = "inactive"     # 未激活
    SUSPENDED = "suspended"   # 暂停合作


class PurchaseRequestStatus(Enum):
    DRAFT = "draft"                   # 草稿
    PENDING_APPROVAL = "pending_approval"  # 待审批
    APPROVED = "approved"             # 已审批
    REJECTED = "rejected"             # 已拒绝
    PURCHASING = "purchasing"         # 采购中
    COMPLETED = "completed"           # 已完成
    CANCELLED = "cancelled"           # 已取消


class OrderStatus(Enum):
    CREATED = "created"               # 已创建
    CONFIRMED = "confirmed"           # 已确认
    PRODUCING = "producing"           # 生产中
    SHIPPED = "shipped"               # 已发货
    IN_TRANSIT = "in_transit"         # 运输中
    DELIVERED = "delivered"           # 已送达
    ACCEPTED = "accepted"             # 已验收
    REJECTED = "rejected"             # 已拒绝


class ApprovalStatus(Enum):
    PENDING = "pending"       # 待审批
    APPROVED = "approved"     # 已通过
    REJECTED = "rejected"     # 已拒绝


class Priority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class User:
    """用户模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    department: str = ""
    role: UserRole = UserRole.PURCHASER
    phone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "role": self.role.value,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class Supplier:
    """供应商模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    code: str = ""
    category: str = ""
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    rating: float = 0.0
    status: SupplierStatus = SupplierStatus.ACTIVE
    credit_level: Optional[str] = None
    price_range: Optional[str] = None
    delivery_days: int = 7
    bulk_discount: bool = False
    good_after_sales: bool = False
    fast_delivery: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "category": self.category,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "address": self.address,
            "rating": self.rating,
            "status": self.status.value,
            "credit_level": self.credit_level,
            "price_range": self.price_range,
            "delivery_days": self.delivery_days,
            "bulk_discount": self.bulk_discount,
            "good_after_sales": self.good_after_sales,
            "fast_delivery": self.fast_delivery,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class PurchaseRequestItem:
    """采购申请明细"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    name: str = ""
    category: str = ""
    specifications: Optional[str] = None
    quantity: int = 0
    unit: str = "个"
    estimated_unit_price: float = 0.0
    estimated_amount: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "request_id": self.request_id,
            "name": self.name,
            "category": self.category,
            "specifications": self.specifications,
            "quantity": self.quantity,
            "unit": self.unit,
            "estimated_unit_price": self.estimated_unit_price,
            "estimated_amount": self.estimated_amount
        }


@dataclass
class PurchaseRequest:
    """采购申请模型"""
    id: str = field(default_factory=lambda: f"PR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:3]}")
    title: str = ""
    requester_id: str = ""
    department: str = ""
    status: PurchaseRequestStatus = PurchaseRequestStatus.DRAFT
    priority: Priority = Priority.NORMAL
    total_amount: float = 0.0
    budget: Optional[float] = None
    required_date: Optional[date] = None
    purpose: Optional[str] = None
    approval_flow_id: Optional[str] = None
    current_approval_node: Optional[str] = None
    items: List[PurchaseRequestItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "requester_id": self.requester_id,
            "department": self.department,
            "status": self.status.value,
            "priority": self.priority.value,
            "total_amount": self.total_amount,
            "budget": self.budget,
            "required_date": self.required_date.isoformat() if self.required_date else None,
            "purpose": self.purpose,
            "approval_flow_id": self.approval_flow_id,
            "current_approval_node": self.current_approval_node,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class OrderItem:
    """订单明细"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    name: str = ""
    quantity: int = 0
    unit_price: float = 0.0
    amount: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "name": self.name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "amount": self.amount
        }


@dataclass
class Order:
    """采购订单模型"""
    id: str = field(default_factory=lambda: f"OR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:3]}")
    request_id: str = ""
    supplier_id: str = ""
    status: OrderStatus = OrderStatus.CREATED
    order_amount: float = 0.0
    paid_amount: float = 0.0
    delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    tracking_number: Optional[str] = None
    tracking_info: Optional[Dict] = None
    items: List[OrderItem] = field(default_factory=list)
    contract_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "request_id": self.request_id,
            "supplier_id": self.supplier_id,
            "status": self.status.value,
            "order_amount": self.order_amount,
            "paid_amount": self.paid_amount,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "actual_delivery_date": self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            "tracking_number": self.tracking_number,
            "tracking_info": self.tracking_info,
            "items": [item.to_dict() for item in self.items],
            "contract_id": self.contract_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class ApprovalNode:
    """审批节点"""
    node_id: int = 0
    approver_id: str = ""
    approver_name: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    comment: Optional[str] = None
    action_time: Optional[datetime] = None


@dataclass
class ApprovalFlow:
    """审批流程模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    flow_type: str = ""  # purchase_request, order, payment
    target_id: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    current_node: int = 1
    nodes: List[ApprovalNode] = field(default_factory=list)
    history: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "flow_type": self.flow_type,
            "target_id": self.target_id,
            "status": self.status.value,
            "current_node": self.current_node,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "approver_id": n.approver_id,
                    "approver_name": n.approver_name,
                    "status": n.status.value,
                    "comment": n.comment,
                    "action_time": n.action_time.isoformat() if n.action_time else None
                }
                for n in self.nodes
            ],
            "history": self.history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class SupplierEvaluation:
    """供应商评估模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    supplier_id: str = ""
    evaluation_date: date = field(default_factory=date.today)
    period_type: str = "quarterly"  # monthly, quarterly, annual
    delivery_score: float = 0.0
    quality_score: float = 0.0
    price_score: float = 0.0
    service_score: float = 0.0
    overall_score: float = 0.0
    evaluation_by: str = ""
    comments: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "evaluation_date": self.evaluation_date.isoformat(),
            "period_type": self.period_type,
            "delivery_score": self.delivery_score,
            "quality_score": self.quality_score,
            "price_score": self.price_score,
            "service_score": self.service_score,
            "overall_score": self.overall_score,
            "evaluation_by": self.evaluation_by,
            "comments": self.comments
        }
