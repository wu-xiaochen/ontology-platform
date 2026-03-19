# Watch Ontology / 腕表领域本体

## 概述

本文档定义了腕表（Watch）领域的领域本体，用于支持腕表知识图谱、智能推荐、鉴定评估、收藏管理等应用场景。

---

## 1. 核心实体类型

### 1.1 腕表大类 (Watch Category)

| 实体ID | 中文名称 | 英文名称 | 定义 |
|--------|----------|----------|------|
| watch_mechanical | 机械表 | Mechanical Watch | 以机械发条为动力源的腕表 |
| watch_quartz | 石英表 | Quartz Watch | 以石英晶体振荡器为动力源的腕表 |
| watch_automatic | 自动机械表 | Automatic Watch | 依靠佩戴者手腕运动自动上链的机械表 |
| watch_manual | 手动机械表 | Manual Watch | 需要手动上链的机械表 |
| watch_smart | 智能手表 | Smart Watch | 具有智能化功能的电子腕表 |
| watch_hybrid | 混合智能表 | Hybrid Watch | 传统机械外观结合智能功能的腕表 |
| watch_fashion | 时装表 | Fashion Watch | 以时尚设计为主的腕表 |
| watch_luxury | 奢华腕表 | Luxury Watch | 高端材质与复杂工艺的腕表 |
| watch_sport | 运动表 | Sport Watch | 专为运动场景设计的腕表 |
| watch_diver | 潜水表 | Diver's Watch | 具有高防水性能的腕表 |
| watch_pilot | 飞行员表 | Pilot Watch | 专为飞行员设计的腕表 |
| watch_racing | 赛车表 | Racing Watch | 专为赛车运动设计的腕表 |
| watch_dress | 正装表 | Dress Watch | 正式场合佩戴的简约腕表 |
| watch_field | 军表 | Field Watch | 军事用途的耐用腕表 |
| watch_chronograph | 计时码表 | Chronograph | 具有计时功能的腕表 |

### 1.2 腕表细分类 (Watch Subcategory)

**按功能分类：**
| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| watch_complication | 复杂功能表 | Complication Watch |
| watch_tourbillon | 陀飞轮表 | Tourbillon Watch |
| watch_perpetual | 万年历表 | Perpetual Calendar |
| watch_chronometer | 天文台表 | Chronometer |
| watch GMT | GMT腕表 | GMT Watch |
| watch_alarm | 响闹表 | Alarm Watch |
| watch_repeat | 三问表 | Minute Repeater |
| watch_moonphase | 月相表 | Moon Phase Watch |
| watch_power_reserve | 动力储存显示表 | Power Reserve Watch |
| watch_world_time | 世界时区表 | World Time Watch |
| watch_split_seconds | 双秒追针表 | Split Seconds Chronograph |

**按形态分类：**
| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| watch_round | 圆形腕表 | Round Watch |
| watch_square | 方形腕表 | Square Watch |
| watch_cushion | 枕形腕表 | Cushion Watch |
| watch_bottle | 酒桶形腕表 | Barrel Watch |
| watch_tonneau | 吨形腕表 | Tonneau Watch |
| watch_oval | 椭圆形腕表 | Oval Watch |
| watch_rectangle | 长方形腕表 | Rectangle Watch |
| watch_asymmetric | 不对称形腕表 | Asymmetric Watch |

---

## 2. 机芯类型 (Movement)

### 2.1 机械机芯 (Mechanical Movement)

| 实体ID | 中文名称 | 英文名称 | 定义 |
|--------|----------|----------|------|
| mov_manual_wind | 手动上链机芯 | Manual Wind Movement | 需手动转动表冠上链 |
| mov_automatic | 自动上链机芯 | Automatic Movement | 通过摆陀自动上链 |
| mov_hand_wound | 手上链机芯 | Hand Wound Movement | 传统手动上链机制 |
| mov_kinetic |  Kinetic机芯 | Kinetic Movement | 精工开发的自动石英混合机芯 |

### 2.2 石英机芯 (Quartz Movement)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| mov_quartz_analog | 模拟石英机芯 | Analog Quartz Movement |
| mov_quartz_digital | 数字石英机芯 | Digital Quartz Movement |
| mov_quartz_chrono | 石英计时机芯 | Quartz Chronograph Movement |
| mov_solar_quartz | 光动能机芯 | Solar Quartz Movement |
| mov_ecodrives | 光动能(西铁城) | Eco-Drive Movement |
| mov_tough_mvt | 强韧机芯 | Tough Movement |

### 2.3 高级复杂机芯 (Haute Horlogerie Movement)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| mov_tourbillon | 陀飞轮机芯 | Tourbillon Movement |
| mov_flying_tourbillon | 飞行陀飞轮机芯 | Flying Tourbillon Movement |
| mov_minute_repeater | 三问机芯 | Minute Repeater Movement |
| mov_perpetual_calendar | 万年历机芯 | Perpetual Calendar Movement |
| mov_annual_calendar | 年历机芯 | Annual Calendar Movement |
| mov_chronograph | 计时码表机芯 | Chronograph Movement |
| mov_column_wheel | 导柱轮机芯 | Column Wheel Movement |
| mov_vertical_clutch | 垂直离合机芯 | Vertical Clutch Movement |

---

## 3. 材质 (Materials)

### 3.1 表壳材质 (Case Material)

| 实体ID | 中文名称 | 英文名称 | 特性 |
|--------|----------|----------|------|
| mat_stainless_304 | 304不锈钢 | 304 Stainless Steel | 常用表壳材质，耐腐蚀 |
| mat_stainless_316 | 316L不锈钢 | 316L Stainless Steel | 医疗级不锈钢，低过敏 |
| mat_steel_904L | 904L精钢 | 904L Steel | 劳力士专用，极耐腐蚀 |
| mat_silver_925 | 925纯银 | 925 Sterling Silver | 柔软，易划伤 |
| mat_gold_18K | 18K黄金 | 18K Gold | 75%黄金+其他金属 |
| mat_gold_14K | 14K黄金 | 14K Gold | 58.3%黄金 |
| mat_rose_gold | 玫瑰金 | Rose Gold | 铜色合金，时尚 |
| mat_white_gold | 白金 | White Gold | 铂金合金，银白色 |
| mat_platinum | 铂金 | Platinum | 稀有贵金属 |
| mat_titanium | 钛金属 | Titanium | 轻盈坚固 |
| mat_ceramic | 陶瓷 | Ceramic | 耐磨不易褪色 |
| mat_carbon | 碳纤维 | Carbon Fiber | 轻盈高科技 |
| mat_bronze | 青铜 | Bronze | 复古氧化质感 |
| mat_tungsten | 钨钢 | Tungsten | 超高硬度 |
| mat_sapphire | 蓝宝石 | Sapphire | 顶级表镜材质 |
| mat_exotic_alloy |  exotic合金 | Exotic Alloy | 特殊合金材质 |

### 3.2 表盘材质 (Dial Material)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| dial_enamel | 珐琅表盘 | Enamel Dial |
| dial_guilloche | 玑镂表盘 | Guilloche Dial |
| dial_sunburst | 太阳纹表盘 | Sunburst Dial |
| dial_guilloché_sunburst | 玑镂太阳纹 | Guilloché Sunburst |
| dial_lacquer | 漆面表盘 | Lacquer Dial |
| dial_metal | 金属表盘 | Metal Dial |
| dial_pearl | 珍珠母贝表盘 | Mother of Pearl Dial |
| dial_skeleton | 镂空表盘 | Skeleton Dial |
| dial_grand_feuille | 大叶纹表盘 | Grand Feu Dial |
| dial_meteorite | 陨石表盘 | Meteorite Dial |

### 3.3 表带材质 (Strap Material)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| strap_leather | 皮革表带 | Leather Strap |
| strap_cowhide | 牛皮表带 | Cowhide Strap |
| strap_alligator | 鳄鱼皮表带 | Alligator Strap |
| strap_calfskin | 小牛皮表带 | Calfskin Strap |
| strap_shark | 鲨鱼皮表带 | Shark Skin Strap |
| strap_ ostrich | 鸵鸟皮表带 | Ostrich Strap |
| strap_rubber | 橡胶表带 | Rubber Strap |
| strap_silicone | 硅胶表带 | Silicone Strap |
| strap_nato | NATO表带 | NATO Strap |
| strap_stainless | 不锈钢表带 | Stainless Steel Bracelet |
| strap_ceramic | 陶瓷表带 | Ceramic Bracelet |
| strap_titanium | 钛金属表带 | Titanium Bracelet |
| strap_rose_gold | 玫瑰金表带 | Rose Gold Bracelet |
| strap_fabric | 织物表带 | Fabric Strap |
| strap_velcro | 魔术贴表带 | Velcro Strap |

### 3.4 表镜材质 (Crystal Material)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| crystal_mineral | 矿物玻璃 | Mineral Crystal |
| crystal_sapphire | 蓝宝石玻璃 | Sapphire Crystal |
| crystal_acrylic | 亚克力玻璃 | Acrylic Crystal |
| crystal_hesalite |  Hesalite玻璃 | Hesalite Crystal |
| crystal_flat | 平面蓝宝石 | Flat Sapphire |
| crystal_domed | 拱形蓝宝石 | Domed Sapphire |
| crystal_box | 盒式蓝宝石 | Box Sapphire |

---

## 4. 功能与复杂功能 (Complications)

### 4.1 基础功能 (Basic Functions)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| func_time | 时分秒显示 | Time Display |
| func_date | 日期显示 | Date Display |
| func_day | 星期显示 | Day Display |
| func_full_calendar | 全历显示 | Full Calendar |
| func_24h | 24小时制显示 | 24-Hour Display |
| func_luminescent | 夜光功能 | Luminous Display |

### 4.2 复杂功能 (Complications)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| comp_chronograph | 计时功能 | Chronograph |
| comp_perpetual_calendar | 万年历 | Perpetual Calendar |
| comp_annual_calendar | 年历 | Annual Calendar |
| comp_moonphase | 月相显示 | Moon Phase |
| comp_tourbillon | 陀飞轮 | Tourbillon |
| comp_minute_repeater | 三问报时 | Minute Repeater |
| comp_gmt | 格林尼治时间 | GMT |
| comp_world_time | 世界时区 | World Time |
| comp_alarm | 闹钟功能 | Alarm |
| comp_power_reserve | 动力储存显示 | Power Reserve Indicator |
| comp_flyback | 飞返功能 | Flyback Chronograph |
| comp_split_seconds | 双秒追针 | Split Seconds |
| comp_equation_of_time | 时间等式 | Equation of Time |
| comp_vertical_clutch | 垂直离合 | Vertical Clutch |
| comp_column_wheel | 导柱轮 | Column Wheel |

### 4.3 智能功能 (Smart Features)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| smart_heart_rate | 心率监测 | Heart Rate Monitoring |
| smart_spo2 | 血氧监测 | SpO2 Monitoring |
| smart_sleep | 睡眠追踪 | Sleep Tracking |
| smart_gps | GPS定位 | GPS Tracking |
| smart_nfc | NFC支付 | NFC Payment |
| smart_phone_notification | 手机通知 | Phone Notifications |
| smart_voice | 语音助手 | Voice Assistant |
| smart_apps | 应用程序 | App Support |
| smart_music | 音乐控制 | Music Control |
| smart_weather | 天气显示 | Weather Display |
| smart_compass | 电子罗盘 | Digital Compass |
| smart_altimeter | 高度计 | Altimeter |
| smart_barometer | 气压计 | Barometer |

---

## 5. 品牌 (Brands)

### 5.1 顶级奢华品牌 (Ultra-Luxury)

| 实体ID | 中文名称 | 英文名称 | 产地 |
|--------|----------|----------|------|
| brand_rolex | 劳力士 | Rolex | 瑞士 |
| brand_patek | 百达翡丽 | Patek Philippe | 瑞士 |
| brand_audemars | 爱彼 | Audemars Piguet | 瑞士 |
| brand_vacheron | 江诗丹顿 | Vacheron Constantin | 瑞士 |
| brand_jaeger | 积家 | Jaeger-LeCoultre | 瑞士 |
| brand_cartier | 卡地亚 | Cartier | 法国 |
| brand_piaget | 伯爵 | Piaget | 瑞士 |
| brand_breguet | 宝玑 | Breguet | 瑞士 |
| brand_blancpain | 宝珀 | Blancpain | 瑞士 |
| brand_iwc | 万国表 | IWC Schaffhausen | 瑞士 |
| brand_omega | 欧米茄 | Omega | 瑞士 |
| brand_a_lange | 朗格 | A. Lange & Söhne | 德国 |

### 5.2 奢华品牌 (Luxury)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| brand_zenith | 真力时 | Zenith |
| brand_breitling | 百年灵 | Breitling |
| brand_tag_heuer | 泰格豪雅 | TAG Heuer |
| brand_tudor | 帝舵 | Tudor |
| brand_panerai | 沛纳海 | Panerai |
| brand_jaeger_ultra | 积家翻转 | Jaeger Reverso |
| brand_longines | 浪琴 | Longines |
| brand_baume | 宝名 | Baume & Mercier |
| brand_girard | 芝柏 | Girard-Perregaux |
| brand_ulysse | 雅典表 | Ulysse Nardin |
| brand_hublot | 宇舶 | Hublot |
| brand_richard | 理查德米勒 | Richard Mille |

### 5.3 豪华品牌 (Premium)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| brand_tissot | 天梭 | Tissot |
| brand_hamilton | 漢米尔顿 | Hamilton |
| brand_oris | 豪雅时 | Oris |
| brand_mido | 美度 | Mido |
| brand_ball | 波尔表 | Ball Watch |
| brand_citizen | 西铁城 | Citizen |
| brand_seiko | 精工 | Seiko |
| brand_grand_seiko | 大精工 | Grand Seiko |
| brand_orient | 东方表 | Orient |
| brand_casio | 卡西欧 | Casio |
| brand_gshock | 卡西欧G-SHOCK | G-SHOCK |

### 5.4 时尚品牌 (Fashion)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| brand_dw | 丹尼尔惠灵顿 | Daniel Wellington |
| brand_fossil |化石 | Fossil |
| brand_mk | 迈克高仕 | Michael Kors |
| brand_tommy |  Tommy Hilfiger |
| brand_hugoboss | 胡戈波士 | Hugo Boss |
| brand_armani | 阿玛尼 | Emporio Armani |
| brand_burberry | 巴宝莉 | Burberry |
| brand_gucci | 古驰 | Gucci |
| brand_hermes | 爱马仕 | Hermès |

---

## 6. 防水等级 (Water Resistance)

| 实体ID | 中文名称 | 英文名称 | 适用场景 |
|--------|----------|----------|----------|
| water_30m | 30米防水 | 30m/3ATM | 生活防水，防溅水 |
| water_50m | 50米防水 | 50m/5ATM | 洗手、洗车 |
| water_100m | 100米防水 | 100m/10ATM | 游泳 |
| water_200m | 200米防水 | 200m/20ATM | 浮潜 |
| water_300m | 300米防水 | 300m/30ATM | 潜水 |
| water_500m | 500米防水 | 500m/50ATM | 专业潜水 |
| water_1000m | 1000米防水 | 100m/100ATM | 深海潜水 |
| water_1000m_plus | 1000米+防水 | 1000m+ | 饱和潜水 |

---

## 7. 表径尺寸 (Case Diameter)

| 实体ID | 中文名称 | 英文名称 | 适合人群 |
|--------|----------|----------|----------|
| size_28mm | 28mm | 28mm | 女性/纤瘦手腕 |
| size_32mm | 32mm | 32mm | 女性/中性 |
| size_34mm | 34mm | 34mm | 女性/小型男性 |
| size_36mm | 36mm | 36mm | 中性/经典 |
| size_38mm | 38mm | 38mm | 男性/正装 |
| size_40mm | 40mm | 40mm | 男性/主流 |
| size_42mm | 42mm | 42mm | 男性/运动 |
| size_44mm | 44mm | 44mm | 大尺寸/运动 |
| size_46mm | 46mm | 46mm | 超大尺寸 |
| size_48mm | 48mm | 48mm | 极限大尺寸 |

---

## 8. 属性 (Attributes)

### 8.1 外观属性 (Visual Attributes)

| 属性ID | 中文名称 | 英文名称 | 取值范围 |
|--------|----------|----------|----------|
| attr_case_shape | 表壳形状 | Case Shape | 圆形、方形、酒桶形、枕形、椭圆形 |
| attr_case_finish | 表壳抛光 | Case Finish | 抛光、磨砂、拉丝、镀金、间金 |
| attr_dial_color | 表盘颜色 | Dial Color | 黑、白、蓝、绿、棕、灰、粉、紫、金 |
| attr_dial_index | 时标类型 | Index Type | 阿拉伯数字、罗马数字、条形、点形 |
| attr_hand_style | 指针风格 | Hand Style | 柳叶针、太子妃针、剑针、棒形针 |
| attr_bezel_type | 表圈类型 | Bezel Type | 固定式、旋转式、测速圈、潜水圈 |
| attr_crown_type | 表冠类型 | Crown Type | 旋入式、非旋入式、护肩式 |
| attr_case_thickness | 表壳厚度 | Case Thickness | 薄型(<8mm)、标准(8-12mm)、厚型(>12mm) |

### 8.2 机芯属性 (Movement Attributes)

| 属性ID | 中文名称 | 英文名称 | 取值范围 |
|--------|----------|----------|----------|
| attr_frequency | 振频 | Frequency | 21600vph, 28800vph, 36000vph |
| attr_power_reserve | 动力储存 | Power Reserve | 24h, 42h, 48h, 72h, 100h+ |
| attr_jewels | 宝石数 | Jewels | 17, 25, 30, 40, 50+ |
| attr_accuracy | 精度等级 | Accuracy | 瑞士天文台(COSC)、品牌认证、通用 |
| attr_chronometer | 天文台认证 | Chronometer | 是/否 |
| attr_escape | 擒纵类型 | Escapement | 瑞士杠杆式、锚式、叉式 |

### 8.3 价格属性 (Price Attributes)

| 属性ID | 中文名称 | 英文名称 | 取值范围 |
|--------|----------|----------|----------|
| attr_price_range | 价格区间 | Price Range | 入门(<5k)、中端(5k-20k)、高端(20k-100k)、顶级(>100k) |
| attr_market_value | 市场价值 | Market Value | 具体金额 |
| attr_collection | 系列 | Collection | 具体系列名称 |
| attr_edition | 限量编号 | Edition Number | 限量数量 |

---

## 9. 认证与标准 (Certifications)

| 实体ID | 中文名称 | 英文名称 | 说明 |
|--------|----------|----------|------|
| cert_cosc | 瑞士天文台认证 | COSC Certification | 每日误差-4/+6秒 |
| cert_chronometer | 官方天文台认证 | Official Chronometer | 更严格的认证 |
| cert_geneve | 日内瓦印记 | Geneva Seal | 日内瓦产区优质印记 |
| cert_fleurier | 弗洛里耶认证 | Fleurier Quality Foundation | 瑞士高端认证 |
| cert_poincon | 瑞士官方印记 | Poinçon de Genève | 日内瓦制表工艺认证 |
| cert_gs | Grand Seiko认证 | Grand Seiko Certification | 精工高端认证 |
| cert_chronofiable | Chronofiable认证 | Chronofiable | 防水及功能测试 |
| cert_rohs | ROHS认证 | ROHS | 环保认证 |

---

## 10. 关系定义 (Relationships)

### 10.1 组成关系 (Part-of)

| 关系ID | 英文名称 | 定义 | 示例 |
|--------|----------|------|------|
| has_movement | has_movement | 腕表搭载的机芯 | 劳力士Submariner has_movement 劳力士3235机芯 |
| has_case | has_case | 腕表的表壳 | 任何腕表 has_case 不锈钢表壳 |
| has_dial | has_dial | 腕表的表盘 | 任何腕表 has_dial 黑色太阳纹表盘 |
| has_strap | has_strap | 腕表的表带 | 任何腕表 has_strap 鳄鱼皮表带 |
| has_crystal | has_crystal | 腕表的表镜 | 任何腕表 has_crystal 蓝宝石玻璃 |
| has_bezel | has_bezel | 腕表的表圈 | 潜水表 has_bezel 陶瓷旋转表圈 |
| has_crown | has_crown | 腕表的表冠 | 任何腕表 has_crown 旋入式表冠 |

### 10.2 归属关系 (Belongs-to)

| 关系ID | 英文名称 | 定义 | 示例 |
|--------|----------|------|------|
| belongs_to_brand | belongs_to_brand | 所属品牌 | 劳力士Submariner belongs_to_brand 劳力士 |
| belongs_to_collection | belongs_to_collection | 所属系列 | 帝舵Pelagos belongs_to_collection 帝舵Pelagos系列 |
| belongs_to_category | belongs_to_category | 所属类别 | 沛纳海Luminor belongs_to_category 运动表 |

### 10.3 认证关系 (Certified-by)

| 关系ID | 英文名称 | 定义 | 示例 |
|--------|----------|------|------|
| certified_by | certified_by | 通过某种认证 | 欧米茄海马 certified_by 瑞士天文台认证 |
| meets_standard | meets_standard | 符合标准 | 潜水表 meets_standard ISO 6425 |

### 10.4 功能关系 (Has-function)

| 关系ID | 英文名称 | 定义 | 示例 |
|--------|----------|------|------|
| has_complication | has_complication | 具有复杂功能 | 复杂功能表 has_complication 万年历 |
| water_resistant_to | water_resistant_to | 防水深度 | 潜水表 water_resistant_to 300米 |

---

## 11. 应用场景 (Use Cases)

### 11.1 智能推荐场景

- **日常通勤**：推荐正装表或简约款
- **运动健身**：推荐运动表或智能手表
- **正式场合**：推荐正装表或奢华品牌
- **收藏投资**：推荐限量版或复杂功能表
- **初学者入门**：推荐入门级品牌如天梭、美度

### 11.2 鉴定评估场景

- **真伪鉴定**：核对机芯型号、表壳序列号
- **成色评估**：检查划痕、氧化、功能状态
- **价值评估**：根据品牌、系列、限量编号估价
- **来源追溯**：查询生产年份、保养记录

### 11.3 维修保养场景

- **保养周期**：机械表3-5年，石英表电池1-2年
- **常见问题**：走时不准、防水失效、表带更换
- **官方服务**：品牌官方维修点认证

---

## 12. 知识图谱示例

### 示例：劳力士Submariner Date 126610LN

```
实体：
- 品牌：劳力士 (Rolex)
- 系列：潜航者型 (Submariner)
- 型号：126610LN
- 类型：自动机械潜水表
- 表径：41mm
- 表壳：904L不锈钢
- 表圈：黑色陶瓷旋转表圈
- 表盘：黑色
- 表带：904L不锈钢蚝式表带
- 机芯：劳力士3235自动上链机芯
- 动力储存：70小时
- 防水深度：300米
- 认证：瑞士天文台认证

关系：
- 劳力士Submariner belongs_to_brand 劳力士
- 劳力士Submariner belongs_to_collection Submariner系列
- 劳力士Submariner belongs_to_category 潜水表
- 劳力士Submariner has_movement 劳力士3235机芯
- 劳力士Submariner has_case 904L不锈钢表壳
- 劳力士Submariner has_bezel 陶瓷旋转表圈
- 劳力士Submariner water_resistant_to 300米
- 劳力士Submariner certified_by 瑞士天文台认证
```

---

## 13. 参考文献

- 《高级钟表学》(Haute Horlogerie)
- 瑞士钟表工业联合会 (FH Federation)
- 日内瓦印记标准 (Poinçon de Genève)
- ISO 764 磁性手表标准
- ISO 6425 潜水手表标准
- 瑞士天文台认证 (COSC) 标准

---

*本文档为腕表领域本体定义，支持知识图谱构建与智能应用开发。*
