# 电商领域本体设计

## 概述

本文档定义电商领域的核心本体模型，涵盖电商平台、交易流程、商品管理、支付物流、用户行为等关键领域，用于指导电商知识库构建和智能化应用。

---

## 一、概念定义 (Concepts)

### 1.1 核心实体

| 概念 | 英文 | 定义 | 关键属性 |
|------|------|------|----------|
| 电商平台 | E-commerce Platform | 提供线上商品交易服务的互联网平台 | 平台ID、名称、类型、流量、佣金比例 |
| 商家 | Seller | 在平台上开店销售商品的经营者 | 商家ID、店铺ID、名称、等级、评分 |
| 消费者 | Consumer | 在平台购物的个人用户 | 用户ID、昵称、等级、标签、行为数据 |
| 商品 | Product | 在平台上架销售的物品 | 商品ID、SKU、名称、类目、价格、库存 |
| 店铺 | Shop | 商家在平台上的线上店铺 | 店铺ID、名称、类型、评分、销量 |
| 订单 | Order | 消费者下单生成的交易凭证 | 订单编号、状态、金额、买家、卖家、时间 |
| 购物车 | Cart | 消费者暂存待结算商品的虚拟容器 | 购物车ID、用户ID、商品列表、数量 |
| 支付 | Payment | 订单金额的在线支付行为 | 支付单号、金额、方式、状态、时间 |
| 物流 | Logistics | 商品从卖家到买家的运输过程 | 物流单号、承运商、状态、轨迹、时效 |
| 评价 | Review | 消费者对商品或服务的反馈 | 评价ID、商品ID、评分、内容、图片、买家 |
| 售后 | After-sales | 退货、换货、维修等售后服务 | 售后单号、类型、状态、原因、处理结果 |
| 促销 | Promotion | 平台或商家开展的优惠活动 | 活动ID、名称、类型、力度、时间、门槛 |
| 优惠券 | Coupon | 可抵扣订单金额的电子凭证 | 优惠券ID、面额、使用门槛、有效期、发放对象 |
| 直播 | Live Stream | 电商直播带货形式 | 直播间ID、主播、观看人数、GMV、转化率 |
| 会员 | Member | 平台的注册用户 | 会员ID、等级、积分、权益、消费金额 |
| SKU | SKU | 商品的具体规格型号 | SKU ID、商品ID、规格、库存、价格 |
| 类目 | Category | 商品的分类体系 | 类目ID、名称、父类目、层级、属性 |
| 品牌 | Brand | 商品的品牌标识 | 品牌ID、名称、Logo、所属公司、热度 |
| 搜索 | Search | 用户在平台搜索商品的行为 | 搜索词、结果数、排序方式、点击商品 |
| 收藏 | Favorite | 用户收藏商品或店铺的行为 | 收藏ID、用户ID、类型、目标ID、时间 |
| 客服 | Customer Service | 解答咨询、处理问题的服务 | 会话ID、客服ID、用户ID、问题类型、解决状态 |

### 1.2 关系定义

```
电商平台 ⊚ 入驻 [商家] (一对多)
电商平台 ⊚ 服务 [消费者] (一对多)
电商平台 ⊚ 上架 [商品] (一对多)
电商平台 ⊚ 开展 [促销] (一对多)
商家 ⊚ 经营 [店铺] (一对一)
商家 ⊚ 发布 [商品] (一对多)
商家 ⊚ 承接 [订单] (一对多)
商家 ⊚ 发放 [优惠券] (一对多)
消费者 ⊚ 收藏 [商品] (多对多)
消费者 ⊚ 加入 [购物车] (一对多)
消费者 ⊚ 下单 [订单] (一对多)
消费者 ⊚ 完成 [支付] (一对多)
消费者 ⊚ 发起 [售后] (一对多)
消费者 ⊚ 撰写 [评价] (一对多)
店铺 ⊚ 展示 [商品] (一对多)
店铺 ⊚ 产生 [订单] (一对多)
店铺 ⊚ 关联 [品牌] (多对多)
订单 ⊚ 包含 [SKU] (多对多)
订单 ⊚ 关联 [支付] (一对一)
订单 ⊚ 记录 [物流] (一对一)
订单 ⊚ 触发 [评价] (一对多)
SKU ⊚ 属于 [商品] (多对一)
商品 ⊚ 关联 [类目] (多对一)
商品 ⊚ 关联 [品牌] (多对一)
商品 ⊚ 参与 [促销] (多对多)
优惠券 ⊚ 抵扣 [订单] (多对多)
直播 ⊚ 展示 [商品] (一对多)
直播 ⊚ 引导 [订单] (一对多)
```

### 1.3 商品类目体系

```
商品类目
├── 服装 (Apparel)
│   ├── 男装
│   ├── 女装
│   ├── 童装
│   ├── 内衣
│   └── 运动服
├── 鞋靴 (Footwear)
│   ├── 男鞋
│   ├── 女鞋
│   ├── 童鞋
│   └── 运动鞋
├── 美妆 (Beauty)
│   ├── 护肤品
│   ├── 彩妆
│   ├── 香水
│   └── 美容工具
├── 数码 (Digital)
│   ├── 手机
│   ├── 电脑
│   ├── 平板
│   ├── 配件
│   └── 智能设备
├── 家电 (Appliances)
│   ├── 大家电
│   ├── 小家电
│   ├── 厨卫电器
│   └── 个护电器
├── 食品 (Food)
│   ├── 水果生鲜
│   ├── 零食坚果
│   ├── 饮料冲调
│   ├── 粮油调味
│   └── 保健食品
├── 家居 (Home)
│   ├── 家具
│   ├── 家纺
│   ├── 家居饰品
│   └── 收纳整理
├── 母婴 (Baby)
│   ├── 奶粉尿裤
│   ├── 童装童鞋
│   ├── 玩具乐器
│   └── 孕产用品
├── 运动 (Sports)
│   ├── 运动鞋服
│   ├── 健身器材
│   ├── 户外装备
│   └── 体育用品
├── 图书 (Books)
│   ├── 小说
│   ├── 教育
│   ├── 科技
│   └── 期刊杂志
└── 医药 (Pharmacy)
    ├── 药品
    ├── 医疗器械
    ├── 隐形眼镜
    └── 保健用品
```

### 1.4 电商平台类型

```
电商平台类型
├── B2C (企业对消费者)
│   ├── 天猫
│   ├── 京东
│   ├── 苏宁易购
│   └── 唯品会
├── C2C (消费者对消费者)
│   ├── 淘宝
│   ├── 闲鱼
│   └── 转转
├── B2B (企业对企业)
│   ├── 阿里巴巴
│   ├── 慧聪网
│   └── 1688
├── 社交电商
│   ├── 拼多多
│   ├── 小红书
│   └── 抖音电商
├── 跨境电商
│   ├── 亚马逊
│   ├── 速卖通
│   ├── 虾皮
│   └── 天猫国际
└── 垂直电商
    ├── 贝贝网
    ├── 蜜芽
    └── 当当
```

---

## 二、属性设计 (Properties)

### 2.1 实体属性

#### 电商平台
| 属性名 | 类型 | 说明 |
|--------|------|------|
| platform_id | string | 平台唯一标识 |
| platform_name | string | 平台名称 |
| platform_type | enum | 平台类型(B2C/C2C/B2B/跨境) |
| monthly_active_users | int | 月活跃用户数 |
| gm | decimal | 年度交易额 |
| commission_rate | float | 佣金比例 |
| established_date | date | 成立日期 |
| headquarters | string | 总部所在地 |

#### 商家
| 属性名 | 类型 | 说明 |
|--------|------|------|
| seller_id | string | 商家唯一标识 |
| shop_id | string | 店铺ID |
| seller_name | string | 商家名称 |
| seller_type | enum | 类型(旗舰店/专营店/企业店) |
| credit_score | int | 信用评分 |
| service_score | float | 服务评分 |
| logistics_score | float | 物流评分 |
| description_score | float | 描述评分 |
| sales_volume | int | 累计销量 |
| product_count | int | 在售商品数 |
| registration_capital | decimal | 注册资本 |
| established_years | int | 经营年限 |

#### 消费者
| 属性名 | 类型 | 说明 |
|--------|------|------|
| user_id | string | 用户唯一标识 |
| nickname | string | 昵称 |
| avatar_url | string | 头像URL |
| gender | enum | 性别 |
| age_range | int | 年龄段 |
| member_level | enum | 会员等级 |
| credit_score | int | 信用分 |
| total_spent | decimal | 累计消费 |
| order_count | int | 订单数量 |
| favorite_count | int | 收藏数量 |
| cart_item_count | int | 购物车商品数 |
| tags | array | 用户标签 |
| first_purchase_date | date | 首次购买日期 |
| last_active_date | datetime | 最后活跃时间 |

#### 商品
| 属性名 | 类型 | 说明 |
|--------|------|------|
| product_id | string | 商品唯一标识 |
| sku_count | int | SKU数量 |
| product_name | string | 商品名称 |
| category_id | string | 类目ID |
| brand_id | string | 品牌ID |
| main_image | string | 主图URL |
| images | array | 图片列表 |
| description | text | 商品描述 |
| original_price | decimal | 原价 |
| current_price | decimal | 当前价 |
| discount | float | 折扣率 |
| sales_volume | int | 销量 |
| review_count | int | 评价数 |
| rating | float | 评分 |
| stock | int | 库存 |
| status | enum | 状态(在售/下架/售罄) |
| create_time | datetime | 上架时间 |
| update_time | datetime | 更新时间 |

#### 订单
| 属性名 | 类型 | 说明 |
|--------|------|------|
| order_id | string | 订单唯一标识 |
| order_no | string | 订单编号 |
| buyer_id | string | 买家ID |
| seller_id | string | 卖家ID |
| shop_id | string | 店铺ID |
| order_status | enum | 订单状态 |
| order_amount | decimal | 订单金额 |
| product_amount | decimal | 商品金额 |
| discount_amount | decimal | 优惠金额 |
| freight | decimal | 运费 |
| payment_method | enum | 支付方式 |
| payment_time | datetime | 支付时间 |
| create_time | datetime | 下单时间 |
| pay_time | datetime | 支付时间 |
| deliver_time | datetime | 发货时间 |
| receive_time | datetime | 收货时间 |
| finish_time | datetime | 完成时间 |

#### SKU
| 属性名 | 类型 | 说明 |
|--------|------|------|
| sku_id | string | SKU唯一标识 |
| product_id | string | 商品ID |
| sku_code | string | SKU编码 |
| specs | json | 规格属性 |
| price | decimal | 价格 |
| original_price | decimal | 原价 |
| stock | int | 库存 |
| sales_volume | int | 销量 |
| weight | float | 重量(g) |
| bar_code | string | 条码 |

### 2.2 订单状态流转

```
订单状态
├── 待付款 (Pending Payment)
│   └── 买家下单后，等待支付
├── 已付款 (Paid)
│   └── 支付成功，等待发货
├── 待发货 (Processing)
│   └── 已付款，等待卖家发货
├── 已发货 (Shipped)
│   └── 卖家已发货，等待收货
├── 待确认 (Confirming)
│   └── 物流显示签收，等待确认
├── 已完成 (Completed)
│   └── 买家确认收货，交易完成
└── 已取消 (Cancelled)
    ├── 待付款取消 → 用户主动取消/超时自动取消
    ├── 已付款取消 → 退款成功
    └── 售后取消 → 售后处理完成后取消
```

### 2.3 售后类型

```
售后类型
├── 退款 (Refund)
│   └── 仅退款，不退货
├── 退货退款 (Return & Refund)
│   └── 退货并退款
├── 换货 (Exchange)
│   └── 换同款商品
├── 维修 (Repair)
│   └── 返厂维修
├── 赔偿 (Compensation)
│   └── 缺件/破损补偿
└── 投诉 (Complaint)
    └── 服务投诉处理
```

---

## 三、业务规则 (Business Rules)

### 3.1 交易规则

| 规则 | 说明 |
|------|------|
| 下单规则 | 购物车商品达到起购量、库存充足、地址有效 |
| 支付规则 | 支持支付宝、微信、银行卡等多种方式 |
| 限购规则 | 某些商品有购买数量限制 |
| 防刷规则 | 同一用户/地址/IP单日下单上限控制 |
| 价保规则 | 订单完成后N天内降价可申请差价补偿 |

### 3.2 商家规则

| 规则 | 说明 |
|------|------|
| 入驻条件 | 需要企业资质、缴纳保证金、通过审核 |
| 评分体系 | 描述相符、服务态度、物流速度三项评分 |
| 违规处罚 | 售假、虚假宣传、延迟发货等扣分处罚 |
| 流量分配 | 评分高、销量好的店铺获得更多曝光 |
| 佣金政策 | 不同类目有不同佣金比例 |

### 3.3 消费者权益

| 权益 | 说明 |
|------|------|
| 7天无理由退货 | 签收7天内可无理由退货(特殊商品除外) |
| 15天换货 | 15天内可申请换货 |
| 极速退款 | 信用好的用户可享未收货极速退款 |
| 运费险 | 退货时可获得运费补偿 |
| 保障服务 | 正品保障、假一赔三等承诺 |

---

## 四、指标体系 (Metrics)

### 4.1 平台指标

| 指标 | 英文 | 说明 |
|------|------|------|
| GMV | Gross Merchandise Volume | 交易总额 |
| 活跃用户数 | MAU | 月活跃用户数 |
| 订单量 | Order Volume | 成交订单数量 |
| 客单价 | AOV | 平均每单金额 |
| 转化率 | Conversion Rate | 浏览到下单的比例 |
| 复购率 | Repurchase Rate | 重复购买的用户比例 |
| 退货率 | Return Rate | 退货订单比例 |

### 4.2 商家指标

| 指标 | 英文 | 说明 |
|------|------|------|
| 销售额 | Sales | 店铺总销售额 |
| 销量 | Sales Volume | 销售商品数量 |
| 访客数 | UV | 店铺访问人数 |
| 浏览量 | PV | 页面浏览次数 |
| 转化率 | CVR | 访客到下单比例 |
| 好评率 | Positive Rate | 好评占比 |
| 动销率 | SKU Movement Rate | 有销量的SKU占比 |
| 库存周转率 | Inventory Turnover | 库存周转效率 |

### 4.3 商品指标

| 指标 | 英文 | 说明 |
|------|------|------|
| 销量 | Sales | 商品总销量 |
| 销售额 | Revenue | 商品总销售额 |
| 收藏数 | Favorites | 收藏该商品的用户数 |
| 加购数 | Cart Adds | 加入购物车次数 |
| 浏览量 | Views | 商品页浏览次数 |
| 转化率 | Conversion | 浏览到购买比例 |
| 评分 | Rating | 商品综合评分 |
| 退货率 | Return Rate | 商品退货比例 |

---

## 五、数据模型 (Data Model)

### 5.1 核心表结构

#### 用户表 (users)
```sql
CREATE TABLE users (
    user_id VARCHAR(64) PRIMARY KEY,
    nickname VARCHAR(128),
    avatar_url VARCHAR(512),
    gender ENUM('male', 'female', 'unknown'),
    phone VARCHAR(20),
    email VARCHAR(128),
    member_level INT DEFAULT 1,
    credit_score INT DEFAULT 500,
    total_spent DECIMAL(12,2) DEFAULT 0,
    order_count INT DEFAULT 0,
    status ENUM('active', 'inactive', 'banned') DEFAULT 'active',
    created_at DATETIME,
    updated_at DATETIME
);
```

#### 商家表 (sellers)
```sql
CREATE TABLE sellers (
    seller_id VARCHAR(64) PRIMARY KEY,
    shop_id VARCHAR(64),
    seller_name VARCHAR(128),
    seller_type ENUM('flagship', 'franchise', 'enterprise'),
    credit_score INT DEFAULT 500,
    service_score DECIMAL(3,2) DEFAULT 5.00,
    logistics_score DECIMAL(3,2) DEFAULT 5.00,
    description_score DECIMAL(3,2) DEFAULT 5.00,
    sales_volume INT DEFAULT 0,
    product_count INT DEFAULT 0,
    status ENUM('pending', 'active', 'suspended') DEFAULT 'pending',
    created_at DATETIME,
    updated_at DATETIME
);
```

#### 商品表 (products)
```sql
CREATE TABLE products (
    product_id VARCHAR(64) PRIMARY KEY,
    category_id VARCHAR(64),
    brand_id VARCHAR(64),
    product_name VARCHAR(256),
    main_image VARCHAR(512),
    images JSON,
    description TEXT,
    original_price DECIMAL(10,2),
    current_price DECIMAL(10,2),
    sales_volume INT DEFAULT 0,
    review_count INT DEFAULT 0,
    rating DECIMAL(2,1) DEFAULT 5.0,
    status ENUM('draft', 'active', 'offline', 'deleted') DEFAULT 'draft',
    created_at DATETIME,
    updated_at DATETIME
);
```

#### 订单表 (orders)
```sql
CREATE TABLE orders (
    order_id VARCHAR(64) PRIMARY KEY,
    order_no VARCHAR(64) UNIQUE,
    buyer_id VARCHAR(64),
    seller_id VARCHAR(64),
    shop_id VARCHAR(64),
    order_status ENUM('pending', 'paid', 'processing', 'shipped', 'confirming', 'completed', 'cancelled') DEFAULT 'pending',
    order_amount DECIMAL(10,2),
    product_amount DECIMAL(10,2),
    discount_amount DECIMAL(10,2) DEFAULT 0,
    freight DECIMAL(8,2) DEFAULT 0,
    payment_method ENUM('alipay', 'wechat', 'card', 'balance'),
    payment_time DATETIME,
    receiver_name VARCHAR(64),
    receiver_phone VARCHAR(20),
    receiver_address TEXT,
    create_time DATETIME,
    pay_time DATETIME,
    deliver_time DATETIME,
    receive_time DATETIME,
    finish_time DATETIME
);
```

#### SKU表 (skus)
```sql
CREATE TABLE skus (
    sku_id VARCHAR(64) PRIMARY KEY,
    product_id VARCHAR(64),
    sku_code VARCHAR(64),
    specs JSON,
    price DECIMAL(10,2),
    original_price DECIMAL(10,2),
    stock INT DEFAULT 0,
    sales_volume INT DEFAULT 0,
    weight DECIMAL(8,2),
    bar_code VARCHAR(64),
    status ENUM('active', 'disabled') DEFAULT 'active',
    created_at DATETIME
);
```

---

## 六、应用场景 (Use Cases)

### 6.1 智能客服
- 解答商品咨询、订单查询、物流追踪
- 处理退换货、投诉建议
- 个性化商品推荐

### 6.2 个性化推荐
- 基于用户行为的商品推荐
- 相似商品推荐
- 猜你喜欢

### 6.3 商家运营分析
- 销售数据分析
- 竞品分析
- 库存预警

### 6.4 风险控制
- 欺诈检测
- 恶意订单识别
- 信用评估

### 6.5 供应链优化
- 需求预测
- 库存管理
- 物流调度

---

## 七、附录 (Appendix)

### 7.1 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| GMV | Gross Merchandise Volume | 成交总额 |
| UV | Unique Visitor | 独立访客数 |
| PV | Page View | 页面浏览量 |
| CTR | Click Through Rate | 点击率 |
| CVR | Conversion Rate | 转化率 |
| ROI | Return on Investment | 投资回报率 |
| AOV | Average Order Value | 客单价 |
| CAC | Customer Acquisition Cost | 用户获取成本 |
| LTV | Life Time Value | 用户生命周期价值 |

### 7.2 参考资料

- 淘宝开放平台文档
- 京东商家帮助中心
- 天猫商家规则
- 拼多多商家入驻协议

---

*本文档为电商领域本体设计初稿，持续迭代更新中。*
