# 广告领域本体设计

## 概述

本文档定义广告领域的核心本体模型，涵盖广告主、广告平台、广告创意、投放交易、效果监测等关键环节，用于指导广告知识库构建和智能化应用。

---

## 一、概念定义 (Concepts)

### 1.1 核心实体

| 概念 | 英文 | 定义 | 关键属性 |
|------|------|------|----------|
| 广告主 | Advertiser | 投放广告的品牌或商家 | 广告主ID、名称、行业、预算、营销目标 |
| 广告平台 | Ad Platform | 提供广告投放服务的互联网平台 | 平台ID、名称、类型、流量规模、服务范围 |
| 广告创意 | Ad Creative | 广告的内容和表现形式 | 创意ID、类型、标题、素材、尺寸、状态 |
| 广告活动 | Campaign | 广告投放的整体策划单元 | 活动ID、名称、目标、预算、时间范围 |
| 广告组 | Ad Group | 广告活动下的细分单元 | 组ID、名称、定向条件、出价策略 |
| 广告位 | Ad Space | 广告展示的位置资源 | 位ID、位置、尺寸、计费方式、流量质量 |
| 广告投放 | Ad Placement | 广告实际展示的实例 | 投放ID、展示次数、点击次数、消耗金额 |
| 竞价交易 | Bid Transaction | 广告位的竞价购买过程 | 交易ID、竞价价、成交价、交易时间 |
| 监测数据 | Tracking Data | 广告效果的追踪数据 | 记录ID、事件类型、时间戳、用户标识 |
| 报告 | Report | 广告效果的汇总统计 | 报告ID、时间范围、维度、指标数据 |
| 归因 | Attribution | 转化归因分析结果 | 归因ID、转化路径、贡献度、归因模型 |
| 受众包 | Audience Segment | 用户人群细分集合 | 包ID、名称、人群规模、更新频率 |
| 素材库 | Asset Library | 广告素材存储库 | 库ID、名称、素材列表、管理权限 |
| 出价策略 | Bidding Strategy | 竞价出价的规则设置 | 策略ID、类型、目标、出价上限 |
| 定向条件 | Targeting Criteria | 广告投放的用户筛选规则 | 定向ID、维度、条件值、覆盖人群 |

### 1.2 关系定义

```
广告主 ⊚ 发起 [广告活动] (一对多)
广告主 ⊚ 创建 [受众包] (一对多)
广告主 ⊚ 拥有 [素材库] (一对多)
广告平台 ⊚ 提供 [广告位] (一对多)
广告平台 ⊚ 管理 [广告主] (多对多)
广告平台 ⊚ 运行 [广告投放] (多对多)
广告活动 ⊚ 包含 [广告组] (一对多)
广告活动 ⊚ 关联 [广告创意] (多对多)
广告组 ⊚ 应用 [定向条件] (一对一)
广告组 ⊚ 使用 [出价策略] (一对一)
广告组 ⊚ 投放 [广告创意] (多对多)
广告位 ⊚ 承载 [广告投放] (一对多)
广告投放 ⊚ 展示 [广告创意] (一对一)
广告投放 ⊚ 参与 [竞价交易] (一对一)
竞价交易 ⊚ 获得 [广告位] (一对一)
监测数据 ⊚ 记录 [广告投放] (多对一)
监测数据 ⊚ 追踪 [用户行为] (一对一)
报告 ⊚ 统计 [广告活动] (多对一)
报告 ⊚ 汇总 [监测数据] (多对一)
归因 ⊚ 分析 [转化路径] (一对一)
受众包 ⊚ 应用 [定向条件] (多对一)
素材库 ⊚ 存储 [广告创意] (多对多)
```

### 1.3 广告平台类型

```
广告平台类型
├── 搜索引擎广告
│   ├── Google Ads
│   ├── 百度推广
│   ├── Bing Ads
│   └── 360搜索
├── 社交媒体广告
│   ├── Facebook Ads
│   ├── 微信广告
│   ├── 微博粉丝通
│   ├── 抖音巨量引擎
│   ├── Instagram Ads
│   └── Twitter Ads
├── 展示广告网络
│   ├── Google Display Network
│   ├── 阿里妈妈
│   ├── 腾讯广告
│   └── 百度信息流
├── 视频广告平台
│   ├── YouTube Ads
│   ├── 腾讯视频广告
│   ├── 爱奇艺广告
│   └── 哔哩哔哩广告
├── 原生广告平台
│   ├── Taboola
│   ├── Outbrain
│   └── 今日头条广告
├── 电商广告
│   ├── 亚马逊广告
│   ├── 淘宝直通车
│   ├── 京东快车
│   └── 拼多多推广
├── 移动应用广告
│   ├── Google AdMob
│   ├── 穿山甲
│   ├── 优量汇
│   └── Facebook Audience Network
└── 需求方平台 (DSP)
    ├── Trade Desk
    ├── 品友互动
    ├── 力美科技
    └── 舜飞科技
```

### 1.4 广告形式分类

```
广告形式
├── 搜索广告 (Search Ads)
│   ├── 关键词广告
│   ├── 品牌广告
│   └── 购物广告
├── 展示广告 (Display Ads)
│   ├── 横幅广告 (Banner)
│   ├── 插屏广告 (Interstitial)
│   ├── 浮层广告 (Overlay)
│   ├── 贴片广告 (Skin)
│   └── 背投广告 (Pop-up)
├── 信息流广告 (Feed Ads)
│   ├── 原生信息流
│   ├── 推荐流广告
│   └── 社交动态广告
├── 视频广告 (Video Ads)
│   ├── 前贴片 (Pre-roll)
│   ├── 中贴片 (Mid-roll)
│   ├── 后贴片 (Post-roll)
│   ├── 暂停广告 (Pause)
│   └── 贴片信息流
├── 原生广告 (Native Ads)
│   ├── 推荐内容
│   ├── 赞助文章
│   ├── 品牌内容
│   └── 电商商品卡
├── 音频广告 (Audio Ads)
│   ├── 播客广告
│   ├── 音乐平台广告
│   └── 有声书广告
├── 邮件广告 (Email Ads)
│   ├── 新闻稿
│   ├── 促销邮件
│   └── 赞助内容
├── 社交媒体广告 (Social Ads)
│   ├── 图文帖子
│   ├── 故事广告
│   ├── 动态消息
│   └── 侧栏广告
└── 程序化广告 (Programmatic)
    ├── RTB实时竞价
    ├── 私有交易市场 (PMP)
    ├── 首选交易 (Preferred Deal)
    └── 程序化直投 (Programmatic Direct)
```

### 1.5 计费模式

```
计费模式
├── CPM (Cost Per Mille)
│   └── 千次展示成本
├── CPC (Cost Per Click)
│   └── 每次点击成本
├── CPA (Cost Per Action)
│   ├── CPS (Cost Per Sale) - 按销售
│   ├── CPL (Cost Per Lead) - 按线索
│   ├── CPI (Cost Per Install) - 按安装
│   └── CPV (Cost Per View) - 按观看
├── CPS (Cost Per Sale)
│   └── 按成交付费
├── oCPM (Optimized CPM)
│   └── 优化千次展示
├── CPCV (Cost Per Completed View)
│   └── 按完整观看付费
├── Flat Fee
│   └── 固定费用
├── CPD (Cost Per Day)
│   └── 按天计费
└── Revshare
    └── 收入分成
```

### 1.6 定向维度

```
定向维度
├── 人口统计 (Demographics)
│   ├── 年龄
│   ├── 性别
│   ├── 教育程度
│   ├── 职业
│   ├── 收入水平
│   └── 家庭状况
├── 地理位置 (Geographic)
│   ├── 国家
│   ├── 省市
│   ├── 城市
│   ├── 区县
│   ├── 商圈
│   └── 地理围栏
├── 兴趣偏好 (Interests)
│   ├── 兴趣爱好
│   ├── 消费偏好
│   ├── 生活方式
│   └── 价值观
├── 行为数据 (Behaviors)
│   ├── 购买行为
│   ├── 浏览行为
│   ├── 设备使用
│   ├── 应用使用
│   └── 内容偏好
├── 自定义受众 (Custom Audiences)
│   ├── 网站访客
│   ├── 客户列表
│   ├── 应用用户
│   └── 互动用户
├── 类似受众 (Lookalike Audiences)
│   └── 相似人群扩展
├── 再营销 (Retargeting)
│   ├── 网站再营销
│   ├── 动态再营销
│   ├── 应用再营销
│   └── 客户名单再营销
└── 场景定向 (Contextual)
    ├── 内容主题
    ├── 关键词
    ├── 设备类型
    ├── 操作系统
    ├── 网络类型
    └── 时间段
```

---

## 二、属性设计 (Properties)

### 2.1 实体属性

#### 广告主
| 属性名 | 类型 | 说明 |
|--------|------|------|
| advertiser_id | string | 广告主唯一标识 |
| advertiser_name | string | 广告主名称 |
| industry | enum | 所属行业 |
| company_size | enum | 公司规模 |
| budget | decimal | 总营销预算 |
| daily_budget | decimal | 日均预算 |
| marketing_objective | enum | 营销目标(品牌/转化/应用安装) |
| account_status | enum | 账户状态(正常/受限/冻结) |
| registration_date | date | 注册日期 |
| contact_info | json | 联系方式 |
| billing_method | enum | 结算方式(预付/后付) |
| currency | string | 结算币种 |
| timezone | string | 时区 |
| credit_limit | decimal | 信用额度 |

#### 广告平台
| 属性名 | 类型 | 说明 |
|--------|------|------|
| platform_id | string | 平台唯一标识 |
| platform_name | string | 平台名称 |
| platform_type | enum | 平台类型(搜索/社交/视频/DSP等) |
| monthly_traffic | int | 月均流量/覆盖用户数 |
| active_advertisers | int | 活跃广告主数量 |
| available_inventory | int | 可用广告位数量 |
| supported_formats | array | 支持的广告形式 |
| supported_billing_models | array | 支持的计费模式 |
| supported_targeting_dimensions | array | 支持的定向维度 |
| min_budget | decimal | 最低起投金额 |
| min_cpc | decimal | 最低CPC出价 |
| min_cpm | decimal | 最低CPM出价 |
| average_ctr | float | 平均点击率 |
| average_cvr | float | 平均转化率 |
| supported_regions | array | 支持的地区 |
| api_endpoint | string | API接口地址 |
| support_contact | string | 客服联系方式 |

#### 广告创意
| 属性名 | 类型 | 说明 |
|--------|------|------|
| creative_id | string | 创意唯一标识 |
| creative_name | string | 创意名称 |
| creative_type | enum | 创意类型(图片/视频/文字/富媒体) |
| format | string | 规格尺寸(宽x高) |
| assets | array | 素材URL列表(图片/视频/文案) |
| title | string | 广告标题 |
| description | text | 广告描述 |
| call_to_action | enum | 行动号召(立即购买/了解更多/注册等) |
| landing_page_url | string | 落地页URL |
| deep_link | string | 深度链接(移动端) |
| tracking_url | string | 监测链接 |
| compliance_status | enum | 合规状态(待审核/已通过/已拒绝) |
| create_time | datetime | 创建时间 |
| update_time | datetime | 更新时间 |
| preview_url | string | 预览链接 |
| advertiser_id | string | 所属广告主 |
| rejection_reason | text | 拒绝原因(如有) |

#### 广告活动
| 属性名 | 类型 | 说明 |
|--------|------|------|
| campaign_id | string | 活动唯一标识 |
| campaign_name | string | 活动名称 |
| campaign_type | enum | 活动类型(品牌/效果/引流等) |
| objective | enum | 营销目标(曝光/点击/转化/应用安装) |
| budget | decimal | 总预算 |
| daily_budget | decimal | 日预算 |
| start_date | date | 开始日期 |
| end_date | date | 结束日期 |
| status | enum | 状态(计划中/进行中/已结束/已暂停) |
| targeting_type | enum | 投放范围(宽泛/精准) |
| delivery_optimization | enum | 投放优化策略 |
| advertiser_id | string | 所属广告主 |
| platform_id | string | 投放平台 |
| created_by | string | 创建人 |
| create_time | datetime | 创建时间 |
| total_impressions | int | 总曝光量 |
| total_clicks | int | 总点击量 |
| total_conversions | int | 总转化量 |
| total_spend | decimal | 总消耗 |
| average_cpm | float | 平均CPM |
| average_cpc | float | 平均CPC |
| average_cpa | float | 平均CPA |

#### 广告组
| 属性名 | 类型 | 说明 |
|--------|------|------|
| ad_group_id | string | 组唯一标识 |
| ad_group_name | string | 组名称 |
| campaign_id | string | 所属活动ID |
| budget | decimal | 组预算 |
| daily_budget | decimal | 组日预算 |
| status | enum | 状态(启用/暂停/已结束) |
| targeting | json | 定向条件配置 |
| bidding_strategy | enum | 出价策略(手动/自动) |
| bid_amount | decimal | 出价金额(手动模式) |
| target_cpa | decimal | 目标CPA(自动优化) |
| start_date | date | 开始日期 |
| end_date | date | 结束日期 |
| frequency_cap | int | 频次上限 |
| delivery_pace | enum | 投放节奏(均匀/加速) |
| creative_ids | array | 关联创意ID列表 |
| total_impressions | int | 总曝光量 |
| total_clicks | int | 总点击量 |
| total_conversions | int | 总转化量 |
| total_spend | decimal | 总消耗 |
| ctr | float | 点击率 |
| cvr | float | 转化率 |
| cpm | float | CPM成本 |
| cpc | float | CPC成本 |
| cpa | float | CPA成本 |

#### 广告位
| 属性名 | 类型 | 说明 |
|--------|------|------|
| adspace_id | string | 广告位唯一标识 |
| adspace_name | string | 广告位名称 |
| position | string | 位置描述(首页Banner/信息流等) |
| placement_type | enum | 广告形式(展示/视频/原生) |
| size | string | 尺寸规格 |
| inventory_type | enum | 库存类型(预留/竞价/包断) |
| billing_model | enum | 计费模式 |
| floor_price | decimal | 最低成交价 |
| estimated_impressions | int | 预估曝光量/日 |
| estimated_clicks | int | 预估点击量/日 |
| click_through_rate | float | 预估CTR |
| completion_rate | float | 预估完成率(视频) |
| quality_score | float | 质量得分 |
| category | array | 适用行业分类 |
| targeting_criteria | json | 支持的定向条件 |
| availability | enum | 可售状态(可售/已售/下架) |
| platform_id | string | 所属平台 |

#### 竞价交易
| 属性名 | 类型 | 说明 |
|--------|------|------|
| transaction_id | string | 交易唯一标识 |
| adspace_id | string | 广告位ID |
| adgroup_id | string | 广告组ID |
| bid_amount | decimal | 竞价出价 |
| win_price | decimal | 成交价格 |
| auction_type | enum | 竞价类型(第二高价/第一高价) |
| auction_result | enum | 竞价结果(成功/失败) |
| auction_time | datetime | 竞价时间 |
| auction_context | json | 竞价上下文(竞争情况) |
| targeting_match | boolean | 定向匹配情况 |
| creative_id | string | 获胜创意ID |
| impression_url | string | 展示URL(监测用) |
| click_url | string | 点击URL(监测用) |
| viewability | float | 可见性预估 |

#### 监测数据
| 属性名 | 类型 | 说明 |
|--------|------|------|
| event_id | string | 事件唯一标识 |
| event_type | enum | 事件类型(展示/点击/转化) |
| transaction_id | string | 关联交易ID |
| adgroup_id | string | 广告组ID |
| campaign_id | string | 活动ID |
| creative_id | string | 创意ID |
| adspace_id | string | 广告位ID |
| user_id | string | 用户标识(匿名化) |
| device_id | string | 设备标识 |
| ip_address | string | IP地址(脱敏) |
| user_agent | string | 用户代理 |
| timestamp | datetime | 事件时间戳 |
| country | string | 国家 |
| region | string | 地区 |
| city | string | 城市 |
| platform | string | 平台(Web/App) |
| os | string | 操作系统 |
| browser | string | 浏览器 |
| screen_resolution | string | 屏幕分辨率 |
| viewable | boolean | 是否可见展示 |
| viewable_time_ms | int | 可见时长(毫秒) |
| postback_url | string | 回调URL(转化事件) |

#### 报告
| 属性名 | 类型 | 说明 |
|--------|------|------|
| report_id | string | 报告唯一标识 |
| report_type | enum | 报告类型(常规/定制) |
| date_range | json | 时间范围(start_date, end_date) |
| dimensions | array | 统计维度(广告主/活动/组/创意等) |
| metrics | array | 指标列表(展示/点击/消耗等) |
| data | json | 报告数据(按维度聚合) |
| total_rows | int | 数据行数 |
| generated_time | datetime | 生成时间 |
| format | enum | 输出格式(CSV/Excel/JSON) |
| campaign_id | string | 活动ID(过滤条件) |
| adgroup_id | string | 组ID(过滤条件) |
| creative_id | string | 创意ID(过滤条件) |
| advertiser_id | string | 广告主ID |
| platform_id | string | 平台ID |

#### 出价策略
| 属性名 | 类型 | 说明 |
|--------|------|------|
| strategy_id | string | 策略唯一标识 |
| strategy_name | string | 策略名称 |
| strategy_type | enum | 策略类型(手动CPC/自动/目标CPA/ROAS) |
| optimization_goal | enum | 优化目标(点击/转化/展示) |
| learning_phase_duration | int | 学习期时长(小时) |
| bid_adjustments | json | 时段/地域出价调整系数 |
| budget_optimization | boolean | 预算优化开关 |
| audience_expansion | boolean | 人群拓展开关 |
| performance_goal | decimal | 性能目标值(如CPA上限) |
| platform_id | string | 适用平台 |
| is_default | boolean | 是否默认策略 |

#### 受众包
| 属性名 | 类型 | 说明 |
|--------|------|------|
| segment_id | string | 人群包唯一标识 |
| segment_name | string | 人群包名称 |
| segment_type | enum | 类型(自定义/类似/再营销) |
| audience_source | enum | 数据来源(网站/应用/CRM/第一方) |
| audience_size | int | 人群规模 |
| update_frequency | enum | 更新频率(实时/每日/每周) |
| retention_period_days | int | 数据保留天数 |
| creation_date | date | 创建日期 |
| last_updated | datetime | 最后更新时间 |
| advertiser_id | string | 所属广告主 |
| data_hash | string | 数据哈希(用于匹配) |
| privacy_level | enum | 隐私级别(聚合/匿名/去标识) |
| matching_rate | float | 平台匹配率预估 |
| targeting_rules | json | 定向规则定义 |

---

### 2.2 广告状态流转

```
广告活动状态
├── 计划中 (Planning)
│   └── 创建完成，等待开始投放
├── 进行中 (Running)
│   └── 正常投放中
├── 已结束 (Ended)
│   └── 达到结束日期自动结束
├── 已暂停 (Paused)
│   └── 手动暂停投放
└── 预算耗尽 (Budget Exhausted)
    └── 日预算/总预算用完

广告创意状态
├── 草稿 (Draft)
│   └── 未提交审核
├── 待审核 (Pending Review)
│   └── 等待平台审核
├── 已通过 (Approved)
│   └── 审核通过可投放
├── 已拒绝 (Rejected)
│   └── 审核未通过，需修改
├── 已投放 (Active)
│   └── 正在使用中
└── 已停用 (Inactive)
    └── 历史创意，不再使用
```

### 2.3 投放策略类型

```
出价策略
├── 手动出价 (Manual Bidding)
│   ├── CPC手动出价
│   └── CPM手动出价
├── 自动出价 (Automated Bidding)
│   ├── 最大化点击
│   ├── 最大化转化
│   ├── 目标CPA
│   ├── 目标ROAS
│   └── 目标展示份额
├── 智能出价 (Smart Bidding)
│   ├── 增强CPC
│   ├── 目标展示次数
│   └── 目标曝光份额
└── 时段出价 (Dayparting)
    ├── 标准时段调整
    └── 智能时段优化
```

### 2.4 转化事件类型

```
转化事件
├── 网站转化
│   ├── 页面浏览
│   ├── 添加到购物车
│   ├── 发起结账
│   ├── 完成购买
│   ├── 注册账号
│   └── 提交表单
├── 应用转化
│   ├── 应用安装
│   ├── 应用打开
│   ├── 注册账号
│   ├── 完成教程
│   ├── 首次付费
│   └── 订阅服务
├── 线下转化
│   ├── 门店到访
│   ├── 电话咨询
│   └── 预约试驾
└── 自定义事件
    ├── 内容阅读
    ├── 视频观看
    ├── 分享传播
    ├── 关键行为
    └── 游戏内事件
```

---

## 三、业务规则 (Business Rules)

### 3.1 投放规则

| 规则 | 说明 |
|------|------|
| 预算控制 | 日预算达到上限自动暂停，总预算控制整体消耗 |
| 时段控制 | 可设置投放时间段，非投放时段不展示 |
| 地域限制 | 定向省份/城市/商圈，非目标区域不投放 |
| 频次控制 | 同一用户在指定周期内最多展示N次 |
| 竞价优先级 | 综合出价、质量得分、相关性确定获胜概率 |
| 优化学习期 | 新策略需要积累数据(通常24-48小时) |
| 预算分配 | 表现好的广告组/创意自动获得更多预算 |
| 阶梯出价 | 根据竞争激烈程度动态调整出价 |

### 3.2 创意规则

| 规则 | 说明 |
|------|------|
| 尺寸规范 | 各广告位有固定尺寸要求(如300x250、728x90) |
| 文件大小 | 图片<150KB，视频<50MB，时长<30s |
| 格式要求 | 图片支持JPG/PNG/GIF，视频支持MP4/MOV |
| 内容合规 | 不包含违规内容(政治/暴力/色情/虚假宣传) |
| 文案限制 | 标题<30字符，描述<100字符 |
| 落地页要求 | 页面可访问、无恶意跳转、加载速度<3s |
| 品牌标识 | 需包含品牌Logo或明确品牌标识 |
| 行动号召 | 必须有明确的CTA按钮或文案 |

### 3.3 定向规则

| 规则 | 说明 |
|------|------|
| 人群覆盖 | 定向条件组合后需有足够覆盖量(>1000) |
| 排除逻辑 | 同时选择"包含"和"排除"时，排除优先级高 |
| 受众上限 | 单广告组定向人群不能超过平台上限(通常1000万) |
| 相似度阈值 | 类似受众相似度需>80%才可创建 |
| 再营销窗口 | 再营销人群最短时效(通常30天内) |
| 交叉定向 | 多条件组合使用 AND 逻辑 |
| 定向层级 | 可设置"宽泛/精准"影响投放范围 |

### 3.4 计费与结算

| 规则 | 说明 |
|------|------|
| 结算周期 | 按日/周/月结算，有账期(通常7-30天) |
| 金额门槛 | 达到最小结算金额才触发付款 |
| 退款政策 | 异常流量(作弊)可追回已结算金额 |
| 单价保护 | 某些平台有CPM/CPC价格保护机制 |
| 优惠折扣 | 预存款、季度合约、大客户折扣 |
| 多币种 | 不同地区使用当地货币结算 |
| 税率 | 根据地区政策可能额外收取税费 |

---

## 四、效果指标 (Performance Metrics)

### 4.1 核心指标

| 指标 | 英文 | 计算公式 | 说明 |
|------|------|----------|------|
| 展示量 | Impressions | 广告被展示的次数 | 同一用户多次展示计多次 |
| 点击量 | Clicks | 广告被点击的次数 | 同一用户多次点击计多次 |
| 点击率 | CTR | Clicks / Impressions × 100% | 衡量创意吸引力 |
| 转化量 | Conversions | 完成目标行为的次数 | 下载、注册、购买等 |
| 转化率 | CVR | Conversions / Clicks × 100% | 衡量落地页效果 |
| 消耗 | Spend | 实际花费金额 | 按实际成交价计算 |
| CPM | CPM | Spend / Impressions × 1000 | 千次展示成本 |
| CPC | CPC | Spend / Clicks | 平均点击成本 |
| CPA | CPA | Spend / Conversions | 平均转化成本 |
| ROAS | ROAS | Revenue / Spend | 广告投资回报率 |
| ROI | ROI | (Revenue - Spend) / Spend × 100% | 投资回报率 |
| 观看率 | View Rate | Completed Views / Impressions | 视频广告完成率 |
| 互动率 | Engagement Rate | Engagements / Impressions | 互动(点赞/分享)率 |
| 频次 | Frequency | Impressions / Unique Users | 人均展示次数 |
| 覆盖人数 | Reach | Unique Users | 独立用户数 |
| 跳出率 | Bounce Rate | Bounces / Visits | 落地页跳出率 |
| 页面停留 | Time on Page | Sum(Visit Duration) / Visits | 平均停留时长 |

### 4.2 质量指标

| 指标 | 英文 | 说明 |
|------|------|------|
| 质量得分 | Quality Score | 平台综合评分(相关性/着陆体验/预期CTR) |
| 可见展示率 | Viewability Rate | 符合可见标准(50%像素>1s)的展示占比 |
| 无效流量比例 | IVT Rate | 机器人/无效流量占比 |
| 落地页速度 | Landing Page Speed | 页面加载时间(秒) |
| 广告疲劳度 | Ad Fatigue | 同一用户重复曝光导致CTR下降 |
| 归因准确度 | Attribution Accuracy | 归因模型与真实贡献的吻合度 |
| 观众重合度 | Audience Overlap | 多广告组受众重叠比例 |

### 4.3 高级指标

| 指标 | 英文 | 说明 |
|------|------|------|
| LTV | Lifetime Value | 用户生命周期价值 |
| ROAS 7-day | 7-Day ROAS | 7天内累积ROAS |
| ROAS 30-day | 30-Day ROAS | 30天内累积ROAS |
| 边际ROAS | Marginal ROAS | 额外花费带来的增量收入比 |
| 辅助转化 | Assisted Conversions | 转化路径中非最终点击的贡献 |
| 多触点归因 | MTA | Multi-Touch Attribution多触点贡献分析 |
| 增量提升 | Incrementality | 实验组相比对照组的提升效果 |
| 品牌 lift | Brand Lift | 品牌认知度/考虑度提升(通过调研) |

---

## 五、技术架构 (Technical Architecture)

### 5.1 系统组件

```
广告系统架构
├── 广告主端 (Advertiser Console)
│   ├── 账户管理
│   ├──  Campaign/Ad Group管理
│   ├── 创意管理
│   ├── 预算与出价设置
│   ├── 报告与分析
│   └── 发票与结算
├── 平台管理端 (Platform Admin)
│   ├── 广告主审核
│   ├── 广告位管理
│   ├── 创意审核
│   ├── 违规处理
│   ├── 数据监控
│   └── 财务对账
├── 竞价引擎 (Bidding Engine)
│   ├── 实时竞价 (RTB)
│   ├── 竞价排序 (Auction)
│   ├── 出价计算 (Bid Calculation)
│   └── 预算控制 (Budget pacing)
├── 定向引擎 (Targeting Engine)
│   ├── 用户画像匹配
│   ├── 实时过滤
│   ├── 受众包加载
│   └── 规则引擎
├── 创意引擎 (Creative Engine)
│   ├── 创意组合 (Dynamic Creative)
│   ├── 素材管理
│   ├── 预览生成
│   └── 版本控制
├── 监测系统 (Tracking System)
│   ├── 展示监测 (Impression Tracking)
│   ├── 点击监测 (Click Tracking)
│   ├── 转化追踪 (Conversion Tracking)
│   ├── 归因分析 (Attribution)
│   └── 反作弊检测 (Fraud Detection)
├── 数据仓库 (Data Warehouse)
│   ├── 原始日志存储
│   ├── 数据清洗
│   ├── 聚合统计
│   └── 数据导出
└── 报告服务 (Reporting Service)
    ├── 实时数据
    ├── 历史报告
    ├── 自定义查询
    └── API接口
```

### 5.2 数据传输协议

| 协议 | 用途 | 说明 |
|------|------|------|
| OpenRTB | 竞价请求/响应 | 实时竞价标准协议(2.5版本) |
| VAST | 视频广告 | Video Ad Serving Template |
| VPAID | 视频交互 | Video Player Ad Interface Definition |
| MRAID | 移动Rich媒体 | Mobile Rich Media Ad Interface |
| ClickMacro | 点击追踪 | 平台替换宏生成追踪URL |
| Postback | 转化回调 | 服务器到服务器的转化回传 |
| S2S | 服务器到服务器 | 数据对接主要方式 |
| Pixel | 前端监测 | 图片像素监测 |

### 5.3 API接口分类

| API类型 | 用途 | 认证方式 |
|---------|------|----------|
| 管理API | Campaign/Ad Group/Creative CRUD | OAuth 2.0 |
| 竞价API | 实时竞价参与 | OpenRTB标准 |
| 报告API | 查询统计数据 | API Key / OAuth |
| 追踪API | 接收点击/转化回调 | IP白名单 / 签名 |
| 预算API | 预算调整与控制 | API Key |
| 素材API | 上传/管理创意素材 | OAuth 2.0 |
| 受众API | 创建/管理人群包 | OAuth 2.0 |

---

## 六、行业术语 (Glossary)

| 术语 | 英文 | 定义 |
|------|------|------|
| DSP | Demand Side Platform | 需求方平台，广告主或代理商使用的投放平台 |
| SSP | Supply Side Platform | 供应方平台，媒体主使用的广告位管理平台 |
| Ad Exchange | Ad Exchange | 广告交易平台，连接DSP和SSP的竞价市场 |
| DMP | Data Management Platform | 数据管理平台，用于用户数据收集和细分 |
| RTB | Real-Time Bidding | 实时竞价，每次展示实时决定广告投放 |
| PMP | Private Marketplace | 私有交易市场，邀请制的优选交易 |
| Header Bidding | Header Bidding | 页头竞价，同时向多个Ad Exchange竞价 |
| oRTB | OpenRTB | 开放式实时竞价协议标准 |
| IAC | Interactive Advertising Bureau | 互动广告局，制定行业标准 |
| CTR | Click-Through Rate | 点击率 |
| CVR | Conversion Rate | 转化率 |
| CPA | Cost Per Acquisition | 按转化计费 |
| CPC | Cost Per Click | 按点击计费 |
| CPM | Cost Per Mille | 按展示计费，千次费用 |
| CPI | Cost Per Install | 按安装计费 |
| CPL | Cost Per Lead | 按线索计费 |
| oCPM | optimized CPM | 优化CPM，按转化概率出价 |
| ROAS | Return On Ad Spend | 广告花费回报率 |
| ROI | Return On Investment | 投资回报率 |
| Viewability | Viewability | 广告可见性标准(如50%像素>1秒) |
| IVT | Invalid Traffic | 无效流量，包括机器人和作弊流量 |
| Brand Safety | Brand Safety | 品牌安全，避免广告出现在违规内容旁 |
| Frequency Capping | Frequency Capping | 频次控制，限制同一用户看到广告的次数 |
| Geo-Targeting | Geo-Targeting | 地理定向 |
| Retargeting | Retargeting | 再营销，针对之前互动过的用户 |
| Lookalike | Lookalike Audience | 类似受众，基于种子用户相似度寻找新用户 |
| A/B Testing | A/B Testing | 对比测试，比较不同广告创意或策略效果 |
| Attribution | Attribution | 归因，确定哪个广告触发了用户转化 |
| Last Click | Last Click Attribution | 最后点击归因，将转化归功于最后点击 |
| First Click | First Click Attribution | 首次点击归因 |
| Linear | Linear Attribution | 线性归因，平均分配各触点贡献 |
| Time Decay | Time Decay Attribution | 时间衰减归因，越靠近转化的触点权重越高 |
| U-Shape | U-Shape Attribution | U型归因，首尾触点权重高 |
| Macro | Macro | 宏替换，在URL中动态替换参数 |
| Pixel | Tracking Pixel | 追踪像素，用于监测展示/点击/转化 |
| Postback URL | Postback URL | 转化回调地址，服务器接收转化数据 |
| Creative ID | Creative ID | 创意ID，广告创意的唯一标识符 |
| Click ID | Click ID | 点击ID，用于追踪点击和后续转化 |
| Click Fraud | Click Fraud | 点击作弊，人为或机器模拟点击 |

---

## 七、典型业务流程 (Workflow Examples)

### 7.1 广告投放流程

```
1. 广告主注册 → 提交资质 → 平台审核 → 账户开通
2. 创建Campaign → 设置目标/预算/时间
3. 创建Ad Group → 设置定向/出价/频控
4. 上传Creative → 提交审核 → 平台审核通过
5. Creative关联Ad Group → 广告开始投放
6. 系统实时竞价 → 竞价获胜 → 广告展示
7. 用户点击 → 跳转落地页 → 发生转化
8. 监测数据收集 → 报告生成 → 广告主分析
9. 账户余额不足 → 充值续费 → 继续投放
```

### 7.2 竞价交易流程

```
1. 用户访问网页/App → 广告位请求
2. SSP发送Bid Request到Ad Exchange
3. Ad Exchange广播给多个DSP
4. 各DSP根据用户画像和可用广告返回Bid Response
5. Auction执行，按规则决定获胜广告
6. 获胜广告返回给SSP
7. 广告展示给用户，同时发送展示回调
8. 用户点击广告，跳转并发送点击回调
9. 用户完成转化，发送转化回调
10. 各方根据协议结算费用
```

### 7.3 创意审核流程

```
1. 广告主提交创意素材和文案
2. 系统自动初审(尺寸/格式/敏感词)
3. 进入人工审核队列
4. 审核员检查内容合规性
   ├── 无违规内容(政治/暴力/色情)
   ├── 品牌标识清晰
   ├── 无夸大宣传
   ├── 落地页可访问
   └── 行动号召合理
5. 审核通过 → 创意状态变更为"已通过"
6. 或审核拒绝 → 创意状态变更为"已拒绝"，需修改重提
7. 特殊情况 → 标记为"需加急"或"人工复核"
```

---

## 八、数据字典参考 (Data Dictionary)

### 8.1 枚举值定义

#### 广告平台类型 (platform_type)
- `search` - 搜索引擎广告
- `social` - 社交媒体广告
- `display` - 展示广告网络
- `video` - 视频广告平台
- `native` - 原生广告平台
- `ecommerce` - 电商广告
- `mobile` - 移动应用广告
- `dsp` - 需求方平台

#### 广告形式 (creative_type)
- `image` - 图片广告
- `video` - 视频广告
- `text` - 文字广告
- `richmedia` - 富媒体广告
- `carousel` - 轮播广告
- `collection` - 商品集合广告
- `playable` - 试玩广告

#### 营销目标 (marketing_objective)
- `brand_awareness` - 品牌认知
- `reach` - 覆盖人数
- `traffic` - 流量获取
- `engagement` - 互动提升
- `conversions` - 转化提升
- `lead_generation` - 线索获取
- `app_installs` - 应用安装
- `sales` - 销售增长

#### 事件类型 (event_type)
- `impression` - 展示
- `click` - 点击
- `view` - 视频观看
- `engagement` - 互动(点赞/分享/评论)
- `conversion` - 转化
- `add_to_cart` - 加入购物车
- `purchase` - 购买
- `registration` - 注册
- `install` - 安装

#### 地区代码 (region/country)
- 使用ISO 3166-1两位国家代码
- 中国省份使用标准缩写(如: 京、沪、粤)
- 城市使用标准化名称

#### 行业分类 (industry)
- `retail` - 零售
- `fashion` - 时尚
- `beauty` - 美妆
- `automotive` - 汽车
- `finance` - 金融
- `real_estate` - 房地产
- `travel` - 旅游
- `education` - 教育
- `healthcare` - 医疗健康
- `technology` - 科技
- `entertainment` - 娱乐
- `food_beverage` - 食品饮料
- `sports` - 体育
- `home_furnishings` - 家居装修

---

## 九、最佳实践建议 (Best Practices)

### 9.1 账户结构设计

- **分层清晰**: 广告主 → Campaign → Ad Group → Creative 四层结构
- **命名规范**: 使用统一命名规则便于管理和分析
- **预算分配**: 根据历史表现动态调整各Campaign预算
- **隔离测试**: 每次A/B测试只改变一个变量

### 9.2 定向策略

- **测试阶段**: 初期使用较宽定向积累数据
- **优化阶段**: 根据数据表现逐步收紧定向
- **排除重叠**: 避免多Ad Group受众过度重合
- **善用类似受众**: 基于种子用户拓展高质量人群

### 9.3 创意优化

- **A/B测试**: 持续测试标题、图片、CTA组合
- **本地化**: 针对不同地区/文化定制创意
- **移动优先**: 多数流量来自移动端，针对小屏优化
- **加载速度**: 素材文件大小控制，避免影响用户体验
- **动态创意**: 利用动态元素自动匹配用户兴趣

### 9.4 出价管理

- **设置合理CPA上限**: 确保盈利空间
- **使用自动出价**: 数据充足后切换智能出价
- **监控学习期**: 新策略需等待48小时数据积累
- **分时段调整**: 根据转化时段特征调整出价系数

### 9.5 监测与归因

- **埋点规范**: 统一事件命名和数据格式
- **多触点归因**: 使用U-Shape或时间衰减模型
- **增量测试**: 通过Geo-Test或Holdout验证真实增量
- **异常检测**: 建立IVT监控及时发现作弊流量
- **归因窗口**: 根据业务周期设置合理归因窗口(7-30天)

### 9.6 隐私合规

- **数据脱敏**: 用户标识使用哈希或匿名化
- **同意管理**: 获取用户数据使用授权(Cookie Consent)
- **GDPR/CCPA**: 遵守欧盟、加州用户数据保护法规
- **数据保留**: 设置合理的数据保留期限
- **最小化收集**: 只收集必要的追踪数据

---

## 十、常见问题 (FAQ)

### 10.1 投放相关

**Q: 广告审核需要多长时间？**
A: 通常自动化审核<1小时，人工审核<24小时。敏感行业可能延长。

**Q: 为什么广告没展现？**
A: 可能原因: 预算耗尽、出价过低、定向人群过窄、广告处于暂停状态、审核未通过、竞争激烈、质量得分低。

**Q: CTR/CVR下降怎么办？**
A: 检查因素: 广告疲劳(频次过高)、竞争环境变化、季节性波动、素材老化、落地页问题、竞争对手优化。

**Q: 如何控制预算消耗速度？**
A: 使用预算Pacing(均匀/加速)、设置日预算上限、调整bid、降低出价、暂停效果差的Ad Group。

### 10.2 技术相关

**Q: 如何确保归因准确性？**
A: 使用正确的归因窗口、合理分配跨设备归因、排除内部点击、设置转化延迟时间、使用S2S回传而非仅Cookie。

**Q: 什么是Click ID(Clid)？**
A: Click ID是在用户点击广告时生成的唯一标识，用于追踪该点击带来的后续转化，是归因的关键数据。

**Q: Postback URL如何配置？**
A: 需在平台设置中配置服务器接收地址，确保公网可访问，并验证签名防止数据篡改。

**Q: 如何检测异常流量？**
A: 监控指标: CTR/CVR异常升高、单一IP/设备集中点击、非正常时间段活跃、点击与转化时间间隔异常。

### 10.3 优化相关

**Q: 多久需要更新一次创意？**
A: 建议每1-2周更新创意避免广告疲劳，CTR下降>20%时考虑更换。

**Q: 如何确定最佳出价？**
A: 参考历史CPA数据，确保CPA < LTV×毛利率。使用自动出价让系统优化，但设置合理的CPA上限。

**Q: 测试新广告平台注意事项？**
A: 小预算测试(5-10%总预算)、设置清晰KPI对比基准、测试足够时间(至少2周)、评估归因数据质量。

**Q: 类似受众效果不好怎么办？**
A: 检查种子用户质量、扩大种子用户规模、调整相似度阈值、尝试不同数据源、避免过度定向。

---

## 十一、参考标准与法规 (Standards & Regulations)

### 11.1 行业标准

- **OpenRTB 2.5**: 实时竞价协议规范
- **VAST 4.2**: 视频广告服务模板
- **VPAID 2.0**: 视频播放器广告接口
- **MRAID 3.0**: 移动富媒体广告接口
- **IAB Display Creative Guidelines**: 展示广告创意规范
- **IAB Tech Lab Standards**: 技术标准汇编

### 11.2 隐私法规

| 法规 | 地区 | 要点 |
|------|------|------|
| GDPR | 欧盟 | 用户数据保护、同意机制、数据可携权 |
| CCPA/CPRA | 加州 | 消费者隐私权、数据出售限制 |
| PIPL | 中国 | 个人信息保护法、最小必要原则 |
| LGPD | 巴西 | 类似GDPR的巴西数据保护法 |
| DPA | 印度 | 数字个人数据保护法案 |
| APPI | 日本 | 个人情报保护法 |

### 11.3 品牌安全标准

- **IAB Ads.txt**: 广告资源关系声明，防止域名欺诈
- **IAB ads.cert**: 广告资源认证协议
- **IAB Tech Lab Content Taxonomy**: 内容分类，避免不当关联
- **ARA (Ad Fraud Resistance)**: 反作弊标准
- **Viewability Standard**: 可见性标准(MRC标准: 50%像素>1秒)

---

## 十二、附录 (Appendices)

### 12.1 常用指标计算速查

```
CTR = Clicks ÷ Impressions × 100%
CVR = Conversions ÷ Clicks × 100%
CPM = Spend ÷ (Impressions ÷ 1000)
CPC = Spend ÷ Clicks
CPA = Spend ÷ Conversions
ROAS = Revenue ÷ Spend
ROI = (Revenue - Spend) ÷ Spend × 100%
```

### 12.2 数据延迟说明

| 数据类型 | 典型延迟 | 说明 |
|----------|----------|------|
| 展示数据 | 实时-1小时 | 日志收集聚合时间 |
| 点击数据 | 实时-30分钟 | 通常较快 |
| 转化数据 | 1-24小时 | 后端回传可能有延迟 |
| 结算数据 | 24-72小时 | 扣除异常流量后确认 |
| 跨设备归因 | 24-48小时 | 需要数据匹配 |

### 12.3 性能基准参考

| 指标 | 行业平均 | 优秀水平 |
|------|----------|----------|
| 展示广告CTR | 0.1%-0.5% | >1% |
| 搜索广告CTR | 2%-5% | >10% |
| 信息流CTR | 1%-3% | >5% |
| 电商转化率 | 1%-3% | >5% |
| 视频完成率 | 50%-70% | >85% |
| 平均CPC | 行业差异大 | <行业平均50% |
| 平均CPA | 行业差异大 | <LTV 30% |

---

*文档版本: 1.0*
*最后更新: 2025-03-16*
*维护团队: 广告产品组*