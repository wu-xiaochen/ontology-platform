# PRD - 垂直领域Agent平台（采购供应链场景）

**版本:** 1.0  
**状态:** 草稿  
**创建日期:** 2026-03-16  
**负责人:** 产品团队  
**场景:** 采购供应链

---

## 1. 产品概述

### 1.1 产品背景

传统采购供应链管理存在以下痛点：
- **流程繁琐**：采购申请、审批、询价、订单执行等环节依赖人工操作，效率低下
- **信息孤岛**：供应商信息、价格数据、库存状态分散在不同系统中
- **决策困难**：缺乏智能化的数据分析支持采购决策
- **响应慢**：供应链异常响应不及时，影响业务连续性

### 1.2 产品定位

构建面向采购供应链场景的垂直领域Agent平台，通过AI Agent能力实现采购流程自动化、智能供应商管理、数据驱动的决策支持。

### 1.3 目标用户

| 角色 | 职责 | 核心需求 |
|------|------|----------|
| 采购专员 | 发起采购、询价管理 | 快速创建采购单、智能匹配供应商 |
| 采购经理 | 审批、供应商管理 | 审批流程自动化、供应商评估 |
| 供应链总监 | 战略规划、数据分析 | 全链路可视化、智能决策建议 |
| 财务 | 付款、预算控制 | 预算合规检查、自动对账 |

---

## 2. 用户故事

### 2.1 采购申请自动化

**作为** 采购专员  
**我希望** 通过自然语言描述采购需求，AI自动生成采购申请单  
**以便** 简化采购申请流程，减少手动填写工作量

**验收标准：**
- 用户输入"我们需要采购50台Dell笔记本电脑，用于研发部门"
- Agent自动提取：商品名称、数量、用途部门、预算范围（可选）
- 生成结构化采购申请单，包含：物品明细、预估金额、审批人、紧急程度

### 2.2 智能供应商匹配

**作为** 采购专员  
**我希望** Agent根据采购需求智能推荐合适的供应商  
**以便** 快速找到最优供应商，缩短询价周期

**验收标准：**
- 基于历史采购数据、供应商评价、商品类目进行智能匹配
- 返回TOP 3推荐供应商，包含：供应商名称、历史合作评分、报价参考区间
- 支持一键发起询价单

### 2.3 采购审批流智能路由

**作为** 采购经理  
**我希望** 系统根据采购金额、类别自动确定审批人并触发审批  
**以便** 审批流程合规且高效

**验收标准：**
- 定义审批规则引擎（金额阈值、类别特殊规则）
- 金额<5000：自动通过
- 金额5000-50000：部门经理审批
- 金额>50000：部门经理+采购总监审批
- 审批节点超时自动催办

### 2.4 供应商全生命周期管理

**作为** 采购经理  
**我希望** Agent能够自动收集供应商信息，进行定期评估  
**以便** 全面了解供应商表现，优化供应商结构

**验收标准：**
- 新供应商入库：自动抓取公开信息（工商、资质）
- 定期评估：基于交付质量、价格竞争力、服务响应生成评分
- 异常预警：交付延迟、质量问题自动告警

### 2.5 供应链数据分析与洞察

**作为** 供应链总监  
**我希望** Agent能够分析采购数据，提供成本优化建议  
**以便** 持续降低采购成本，优化供应链策略

**验收标准：**
- 采购支出分析：按部门、类别、供应商多维度分析
- 价格趋势分析：关键物料价格走势预测
- 优化建议：批量采购建议、供应商替换建议

### 2.6 合同与订单智能执行

**作为** 采购专员  
**我希望** Agent能够跟踪订单执行状态，自动处理异常  
**以便** 确保采购物资及时到位

**验收标准：**
- 订单状态自动跟踪（已下单→已发货→已到货→已验收）
- 异常自动识别（延迟交货、质量问题）
- 自动触发补货或索赔流程

---

## 3. 功能流程

### 3.1 采购申请流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  用户发起   │───▶│  Agent解析  │───▶│  生成申请单 │───▶│  提交审批   │
│  采购需求   │    │  需求意图   │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                              │
                   ┌─────────────────────────────────────────┘
                   ▼
            ┌─────────────┐
            │  审批规则    │
            │  引擎路由    │
            └─────────────┘
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────────┐
│ 自动通过 │  │ 部门经理 │  │ 部门+总监   │
│ (<5k)   │  │  审批   │  │  双审批     │
└─────────┘  └─────────┘  └─────────────┘
```

### 3.2 供应商管理流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  供应商入库  │───▶│  信息补全   │───▶│  资格审核   │───▶│  正式合作   │
│  (申请/Agent│    │  (Agent自动 │    │  (资质验证) │    │             │
│   推荐)     │    │   抓取)     │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                              │
     ┌───────────────────────────────────────────────────────┘
     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  定期评估    │───▶│  评分生成    │───▶│  异常预警    │───▶│  优化建议   │
│  (月度/季度)│    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 3.3 订单执行跟踪流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  订单创建   │───▶│  供应商确认  │───▶│  发货跟踪   │───▶│  到货验收   │
│             │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                                       │                   │
      │                                       ▼                   ▼
      │                              ┌─────────────┐    ┌─────────────┐
      │                              │  物流状态   │    │  质量检验   │
      │                              │  同步       │    │             │
      │                              └─────────────┘    └─────────────┘
      │                                       │                   │
      └───────────────────────────────────────┴───────────────────┘
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │  异常处理   │
                                    │  (延迟/质量)│
                                    └─────────────┘
```

---

## 4. API设计

### 4.1 核心API列表

#### 4.1.1 采购申请管理

| API | 方法 | 路径 | 描述 |
|-----|------|------|------|
| 创建采购申请 | POST | /api/v1/purchase-requests | 创建新的采购申请 |
| 查询采购申请 | GET | /api/v1/purchase-requests/{id} | 获取采购申请详情 |
| 列表采购申请 | GET | /api/v1/purchase-requests | 条件查询采购申请列表 |
| 更新采购申请 | PUT | /api/v1/purchase-requests/{id} | 更新采购申请 |
| 取消采购申请 | DELETE | /api/v1/purchase-requests/{id} | 取消采购申请 |
| AI解析采购需求 | POST | /api/v1/agent/parse-purchase-intent | 自然语言解析为采购申请 |

#### 4.1.2 供应商管理

| API | 方法 | 路径 | 描述 |
|-----|------|------|------|
| 创建供应商 | POST | /api/v1/suppliers | 创建新供应商 |
| 查询供应商 | GET | /api/v1/suppliers/{id} | 获取供应商详情 |
| 列表供应商 | GET | /api/v1/suppliers | 条件查询供应商列表 |
| 更新供应商 | PUT | /api/v1/suppliers/{id} | 更新供应商信息 |
| 供应商评估 | POST | /api/v1/suppliers/{id}/evaluate | 生成供应商评估报告 |
| AI推荐供应商 | POST | /api/v1/agent/recommend-suppliers | 根据需求智能推荐供应商 |

#### 4.1.3 订单管理

| API | 方法 | 路径 | 描述 |
|-----|------|------|------|
| 创建订单 | POST | /api/v1/orders | 创建采购订单 |
| 查询订单 | GET | /api/v1/orders/{id} | 获取订单详情 |
| 列表订单 | GET | /api/v1/orders | 条件查询订单列表 |
| 更新订单状态 | PUT | /api/v1/orders/{id}/status | 更新订单状态 |
| 订单跟踪 | GET | /api/v1/orders/{id}/tracking | 获取订单物流跟踪信息 |

#### 4.1.4 审批管理

| API | 方法 | 路径 | 描述 |
|-----|------|------|------|
| 提交审批 | POST | /api/v1/approvals | 发起审批流程 |
| 审批操作 | POST | /api/v1/approvals/{id}/action | 审批通过/拒绝 |
| 查询审批 | GET | /api/v1/approvals/{id} | 获取审批详情 |
| 待办审批列表 | GET | /api/v1/approvals/pending | 获取当前用户待办审批 |

#### 4.1.5 数据分析

| API | 方法 | 路径 | 描述 |
|-----|------|------|------|
| 采购支出分析 | GET | /api/v1/analytics/spending | 采购支出多维分析 |
| 价格趋势分析 | GET | /api/v1/analytics/price-trend | 物料价格趋势 |
| 成本优化建议 | POST | /api/v1/agent/cost-optimization | AI生成成本优化建议 |

---

### 4.2 核心API详细设计

#### 4.2.1 AI解析采购需求

**请求:**
```http
POST /api/v1/agent/parse-purchase-intent
Content-Type: application/json
Authorization: Bearer {token}

{
  "intent_text": "我们需要采购50台Dell笔记本电脑，用于研发部门，最好月底前到货"
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "parsed": {
      "items": [
        {
          "name": "Dell笔记本电脑",
          "quantity": 50,
          "specifications": "默认配置",
          "category": "电子设备/电脑"
        }
      ],
      "department": "研发部门",
      "required_date": "2026-03-31",
      "budget_range": null,
      "priority": "normal"
    },
    "confidence": 0.92,
    "suggestions": [
      "建议确认具体型号配置",
      "是否需要预装软件"
    ]
  }
}
```

#### 4.2.2 AI推荐供应商

**请求:**
```http
POST /api/v1/agent/recommend-suppliers
Content-Type: application/json
Authorization: Bearer {token}

{
  "purchase_request_id": "PR-20260316-001",
  "top_n": 3
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "supplier_id": "SUP-001",
        "supplier_name": "联想官方旗舰店",
        "match_score": 0.95,
        "historical_rating": 4.8,
        "price_range": "4500-5000",
        "delivery_days": 7,
        "reasons": [
          "历史合作评分高",
          "同品类供货经验丰富",
          "支持批量采购优惠"
        ]
      },
      {
        "supplier_id": "SUP-002",
        "supplier_name": "京东企业购",
        "match_score": 0.88,
        "historical_rating": 4.5,
        "price_range": "4800-5200",
        "delivery_days": 3,
        "reasons": [
          "配送速度快",
          "售后保障好"
        ]
      }
    ]
  }
}
```

#### 4.2.3 创建采购申请

**请求:**
```http
POST /api/v1/purchase-requests
Content-Type: application/json
Authorization: Bearer {token}

{
  "title": "研发部门笔记本电脑采购",
  "items": [
    {
      "name": "Dell笔记本电脑",
      "category": "电子设备/电脑",
      "quantity": 50,
      "estimated_unit_price": 5000,
      "specifications": "i7/16G/512G SSD"
    }
  ],
  "department": "研发部门",
  "required_date": "2026-03-31",
  "priority": "normal",
  "purpose": "研发人员办公设备更新",
  "budget": 250000,
  "approver_ids": ["user-001"]
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "id": "PR-20260316-001",
    "title": "研发部门笔记本电脑采购",
    "status": "pending_approval",
    "total_amount": 250000,
    "created_by": "user-001",
    "created_at": "2026-03-16T10:00:00Z",
    "items": [...],
    "approval_flow": {
      "current_node": "部门经理审批",
      "next_nodes": ["采购总监审批"]
    }
  }
}
```

---

## 5. 数据模型

### 5.1 核心实体关系

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    User         │       │  Purchase       │       │    Supplier     │
│    (用户)        │       │    Request      │       │    (供应商)     │
│                 │       │    (采购申请)    │       │                 │
│ - id            │──────▶│ - id             │◀──────│ - id            │
│ - name          │       │ - title          │       │ - name          │
│ - email         │       │ - user_id        │       │ - category      │
│ - department    │       │ - supplier_id    │       │ - rating        │
│ - role          │       │ - status         │       │ - status        │
└─────────────────┘       │ - total_amount   │       └─────────────────┘
                          │ - required_date  │              ▲
                          └─────────────────┘              │
                                 │                          │
                                 ▼                          │
                          ┌─────────────────┐              │
                          │    Order        │              │
                          │    (订单)        │              │
                          │                 │──────────────┘
                          │ - id            │
                          │ - request_id    │
                          │ - supplier_id   │
                          │ - status        │
                          │ - items         │
                          │ - tracking_info │
                          └─────────────────┘
```

### 5.2 详细数据模型

#### 5.2.1 用户 (User)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 用户ID |
| name | string | 是 | 用户姓名 |
| email | string | 是 | 邮箱 |
| department | string | 是 | 部门 |
| role | string | 是 | 角色: purchaser/purchase_manager/director/finance |
| phone | string | 否 | 电话 |

#### 5.2.2 供应商 (Supplier)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 供应商ID |
| name | string | 是 | 供应商名称 |
| code | string | 是 | 供应商编码 |
| category | string | 是 | 供应类别 |
| contact_name | string | 否 | 联系人 |
| contact_phone | string | 否 | 联系电话 |
| contact_email | string | 否 | 联系邮箱 |
| address | string | 否 | 地址 |
| rating | decimal | 是 | 综合评分(0-5) |
| status | string | 是 | 状态: active/inactive/suspended |
| credit_level | string | 否 | 信用等级 |
| created_at | datetime | 是 | 创建时间 |
| updated_at | datetime | 是 | 更新时间 |

#### 5.2.3 采购申请 (PurchaseRequest)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 申请ID (格式: PR-YYYYMMDD-XXX) |
| title | string | 是 | 申请标题 |
| requester_id | string | 是 | 申请人ID |
| department | string | 是 | 需求部门 |
| status | string | 是 | 状态: draft/pending_approval/approved/rejected/purchasing/completed/cancelled |
| priority | string | 是 | 优先级: low/normal/high/urgent |
| total_amount | decimal | 是 | 总金额 |
| budget | decimal | 否 | 预算 |
| required_date | date | 否 | 要求到货日期 |
| purpose | string | 否 | 采购用途 |
| approval_flow_id | string | 否 | 审批流程ID |
| current_approval_node | string | 否 | 当前审批节点 |
| items | array | 是 | 采购明细 |
| created_at | datetime | 是 | 创建时间 |
| updated_at | datetime | 是 | 更新时间 |

#### 5.2.4 采购明细 (PurchaseRequestItem)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 明细ID |
| request_id | string | 是 | 所属申请ID |
| name | string | 是 | 物品名称 |
| category | string | 是 | 类别 |
| specifications | string | 否 | 规格型号 |
| quantity | integer | 是 | 数量 |
| unit | string | 是 | 单位 |
| estimated_unit_price | decimal | 是 | 预估单价 |
| estimated_amount | decimal | 是 | 预估金额 |

#### 5.2.5 订单 (Order)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 订单ID (格式: OR-YYYYMMDD-XXX) |
| request_id | string | 是 | 关联采购申请ID |
| supplier_id | string | 是 | 供应商ID |
| status | string | 是 | 状态: created/confirmed/producing/shipped/in_transit/delivered/accepted/rejected |
| order_amount | decimal | 是 | 订单金额 |
| paid_amount | decimal | 否 | 已付金额 |
| delivery_date | date | 否 | 计划交付日期 |
| actual_delivery_date | date | 否 | 实际交付日期 |
| tracking_number | string | 否 | 物流单号 |
| tracking_info | json | 否 | 物流详情 |
| items | array | 是 | 订单明细 |
| contract_id | string | 否 | 合同ID |
| created_at | datetime | 是 | 创建时间 |
| updated_at | datetime | 是 | 更新时间 |

#### 5.2.6 审批流程 (ApprovalFlow)

| 字段 | 类型 | 必填 |说明|
|------|------|------|-----|
| id | string | 是 | 流程ID |
| flow_type | string | 是 | 流程类型: purchase_request/order/payment |
| target_id | string | 是 | 目标对象ID |
| status | string | 是 | 状态: pending/approved/rejected |
| current_node | integer | 是 | 当前节点(从1开始) |
| nodes | array | 是 | 审批节点列表 |
| history | array | 是 | 审批历史 |
| created_at | datetime | 是 | 创建时间 |
| updated_at | datetime | 是 | 更新时间 |

**审批节点 (ApprovalNode):**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| node_id | integer | 是 | 节点序号 |
| approver_id | string | 是 | 审批人ID |
| approver_name | string | 是 | 审批人姓名 |
| status | string | 是 | 状态: pending/approved/rejected |
| comment | string | 否 | 审批意见 |
| action_time | datetime | 否 | 审批时间 |

#### 5.2.7 供应商评估 (SupplierEvaluation)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 评估ID |
| supplier_id | string | 是 | 供应商ID |
| evaluation_date | date | 是 | 评估日期 |
| period_type | string | 是 | 周期类型: monthly/quarterly/annual |
| delivery_score | decimal | 是 | 交付评分 |
| quality_score | decimal | 是 | 质量评分 |
| price_score | decimal | 是 | 价格评分 |
| service_score | decimal | 是 | 服务评分 |
| overall_score | decimal | 是 | 综合评分 |
| evaluation_by | string | 是 | 评估人 |
| comments | string | 否 | 评估备注 |

---

## 6. 非功能需求

### 6.1 性能要求

- API响应时间: P99 < 500ms
- 支持并发用户: ≥500
- 数据同步延迟: < 5秒

### 6.2 安全要求

- 身份认证: JWT Token
- 权限控制: RBAC
- 数据加密: 敏感数据AES-256
- 审计日志: 所有操作记录

### 6.3 可用性要求

- 系统可用性: ≥99.9%
- 容灾备份: 日备份 + 实时同步

---

## 7. 术语表

| 术语 | 说明 |
|------|------|
| PR | Purchase Request，采购申请 |
| PO | Purchase Order，采购订单 |
| RFQ | Request For Quotation，询价单 |
| SOW | Statement of Work，工作说明书 |
| SKU | Stock Keeping Unit，库存单位 |
|Lead Time | 交货周期 |

---

## 8. 附录

### 8.1 审批规则配置示例

```json
{
  "rules": [
    {
      "id": "rule-001",
      "name": "小额采购自动通过",
      "condition": "amount < 5000",
      "action": "auto_approve"
    },
    {
      "id": "rule-002",
      "name": "一般采购单签",
      "condition": "amount >= 5000 && amount < 50000",
      "action": "single_approval",
      "approver_role": "department_manager"
    },
    {
      "id": "rule-003",
      "name": "大额采购双签",
      "condition": "amount >= 50000",
      "action": "multi_approval",
      "approvers": ["department_manager", "purchase_director"]
    }
  ]
}
```

---

*文档版本记录*
| 版本 | 日期 | 修改人 | 修改内容 |
|------|------|--------|----------|
| 1.0 | 2026-03-16 | 产品团队 | 初始版本 |
