# 咖啡领域本体 (Coffee Ontology)

## 1. 概述

本本体定义了咖啡领域的核心概念、分类体系、属性和关系，为知识图谱构建和语义推理提供标准化模型。

**命名空间**: `coffee-ontology`
**版本**: 1.0.0
**创建日期**: 2026-03-16

---

## 2. 核心类 (Core Classes)

### 2.1 咖啡豆 (CoffeeBean)

**定义**: 咖啡树的种子，是制作咖啡饮品的原料。

**子类**:
- 阿拉比卡咖啡豆 (ArabicaCoffeeBean)
- 罗布斯塔咖啡豆 (RobustaCoffeeBean)
- 利比里卡咖啡豆 (LibericaCoffeeBean)
- 埃塞尔萨咖啡豆 (ExcelsaCoffeeBean)

**属性**:
- `hasOrigin`: 产地 (引用: CoffeeRegion)
- `hasAltitude`: 种植海拔 (数值类型: 米)
- `hasProcessingMethod`: 处理方法 (枚举: 日晒/水洗/蜜处理/湿刨法)
- `hasRoastLevel`: 烘焙程度 (枚举: 浅烘/中烘/中深烘/深烘)
- `hasFlavorProfile`: 风味特征 (文本)
- `hasCaffeineContent`: 咖啡因含量 (数值类型: 毫克/克)
- `hasHarvestSeason`: 采摘季节 (枚举: 春/秋)
- `hasGrade`: 等级 (枚举: AA/A/B/C)
- `hasPrice`: 价格 (货币类型: 美元/公斤)

---

### 2.2 阿拉比卡咖啡豆 (ArabicaCoffeeBean)

**定义**: 最主要的商业咖啡品种，占全球咖啡产量的约60%。

**特征**:
- 咖啡因含量较低 (1.2%-1.5%)
- 酸度适中
- 风味复杂多样
- 适合精品咖啡

**著名产地**:
- 埃塞俄比亚 (Ethiopia)
- 哥伦比亚 (Colombia)
- 巴西 (Brazil)
- 危地马拉 (Guatemala)
- 肯尼亚 (Kenya)

**著名品种**:
- 波旁 (Bourbon)
- 铁皮卡 (Typica)
- 卡杜拉 (Caturra)
- 卡杜艾 (Catuai)
- 瑰夏 (Geisha)

---

### 2.3 罗布斯塔咖啡豆 (RobustaCoffeeBean)

**定义**: 产量第二大的咖啡品种，抗病性强。

**特征**:
- 咖啡因含量高 (2.2%-2.7%)
- 酸度低
- 苦味明显
- 风味较单一

**著名产地**:
- 越南 (Vietnam)
- 印度尼西亚 (Indonesia)
- 乌干达 (Uganda)
- 巴西 (Brazil)

---

### 2.4 咖啡烘焙 (CoffeeRoasting)

**定义**: 将生豆转化为可饮用咖啡豆的加工过程。

**子类**:
- 浅烘焙 (LightRoast)
- 中烘焙 (MediumRoast)
- 中深烘焙 (MediumDarkRoast)
- 深烘焙 (DarkRoast)

**属性**:
- `hasRoastTemperature`: 烘焙温度 (数值类型: 摄氏度)
- `hasRoastDuration`: 烘焙时间 (数值类型: 秒)
- `hasRoastDegree`: 烘焙度 (枚举: 1-10)
- `hasFirstCrack`: 第一次爆裂 (布尔值)
- `hasSecondCrack`: 第二次爆裂 (布尔值)
- `hasDevelopmentTimeRatio`: 发展时间比例 (百分比)

---

### 2.5 浅烘焙 (LightRoast)

**特征**:
- 烘焙温度: 180°C - 205°C
- 酸度高
- 风味清晰
- 能品尝到产地特色
- 咖啡因含量保留最多

**适用场景**: 手冲咖啡、滴滤咖啡

---

### 2.6 中烘焙 (MediumRoast)

**特征**:
- 烘焙温度: 205°C - 220°C
- 酸度适中
- 甜度提升
- 风味平衡
- 适合大多数冲煮方式

**适用场景**: 意式浓缩、美式咖啡、手冲

---

### 2.7 深烘焙 (DarkRoast)

**特征**:
- 烘焙温度: 220°C - 250°C
- 酸度低
- 苦味明显
- 焦糖化风味
- 油脂丰富

**适用场景**: 意式浓缩、法压壶

---

## 3. 咖啡饮品 (CoffeeBeverage)

**定义**: 以咖啡豆为原料制成的各种饮品。

**子类**:
- 意式浓缩咖啡 (Espresso)
- 美式咖啡 (Americano)
- 拿铁咖啡 (Latte)
- 卡布奇诺 (Cappuccino)
- 摩卡咖啡 (Mocha)
- 玛奇朵 (Macchiato)
- 澳白咖啡 (FlatWhite)
- 冷萃咖啡 (ColdBrew)
- 冰滴咖啡 (IceDrip)
- 越南咖啡 (VietnameseCoffee)

**属性**:
- `hasBase`: 基础咖啡 (引用: Espresso)
- `hasMilk`: 牛奶 (引用: Milk)
- `hasMilkFoam`: 奶泡 (数值类型: 毫升)
- `hasSweetener`: 甜味剂 (引用: Sweetener)
- `hasFlavor`: 风味 (枚举: 香草/焦糖/榛子/肉桂)
- `hasTemperature`: 温度 (枚举: 热/冷/温)
- `hasVolume`: 容量 (毫升)
- `hasCaffeineContent`: 咖啡因含量 (毫克)
- `hasPreparationMethod`: 制作方法 (枚举: 萃取/冲泡/浸泡)
- `hasBrewTime`: 萃取时间 (秒)

---

### 3.1 意式浓缩咖啡 (Espresso)

**定义**: 通过高压萃取的高浓度咖啡，是许多咖啡饮品的基础。

**特征**:
- 压力: 9 bar
- 粉量: 18-20克
- 液量: 25-30毫升
- 萃取时间: 25-30秒
- 油脂层 (Crema): 金黄色

**分类**:
- 单份浓缩 (SingleShot): 25毫升
- 双份浓缩 (DoubleShot): 50毫升
- 瑞斯垂朵 (Ristretto): 15毫升
- 隆戈 (Lungo): 60毫升

---

### 3.2 美式咖啡 (Americano)

**定义**: 意式浓缩加水稀释的咖啡。

**配方**:
- 意式浓缩: 1-2份
- 热水: 150-240毫升

**变体**:
- 长美式 (LongBlack): 先水后浓缩
- 短美式 (ShortAmericano): 较少水

---

### 3.3 拿铁咖啡 (Latte)

**定义**: 意式浓缩与大量牛奶混合的咖啡饮品。

**配方**:
- 意式浓缩: 1份
- 蒸汽牛奶: 240毫升
- 奶泡: 1厘米厚度

**特征**:
- 咖啡与牛奶比例约 1:6
- 口感顺滑
- 奶味明显

---

### 3.4 卡布奇诺 (Cappuccino)

**定义**: 等量浓缩、牛奶和奶泡的经典咖啡饮品。

**配方**:
- 意式浓缩: 1份
- 牛奶: 适量
- 奶泡: 2厘米厚度

**特征**:
- 三层分明: 浓缩/牛奶/奶泡
- 奶泡占比高
- 适合拉花

---

### 3.5 摩卡咖啡 (Mocha)

**定义**: 含巧克力成分的咖啡饮品。

**配方**:
- 意式浓缩: 1份
- 巧克力酱: 15毫升
- 牛奶: 适量
- 奶泡: 顶层装饰
- 可可粉: 撒面

---

### 3.6 玛奇朵 (Macchiato)

**定义**: 浓缩咖啡以少量奶泡点缀。

**分类**:
- 浓缩玛奇朵 (EspressoMacchiato): 浓缩+少量奶泡
- 焦糖玛奇朵 (CaramelMacchiato): 牛奶+浓缩+焦糖

---

### 3.7 澳白咖啡 (Flat White)

**定义**: 起源于澳大利亚/新西兰的咖啡饮品。

**配方**:
- 意式浓缩: 1-2份
- 细奶泡: 薄层
- 容量: 150-180毫升

**特征**:
- 奶泡细腻
- 咖啡味突出
- 杯型较小

---

### 3.8 冷萃咖啡 (ColdBrew)

**定义**: 冷水长时间浸泡制成的咖啡。

**特征**:
- 水温: 冷水/冰水
- 浸泡时间: 12-24小时
- 酸度低
- 口感顺滑
- 咖啡因含量高

---

### 3.9 冰滴咖啡 (IceDrip)

**定义**: 冰水缓慢滴滤制成的咖啡。

**特征**:
- 萃取时间: 4-12小时
- 酸度极低
- 风味纯净
- 价格较高

---

### 3.10 越南咖啡 (VietnameseCoffee)

**定义**: 越南传统咖啡饮品。

**特征**:
- 使用罗布斯塔咖啡豆
- 加炼乳
- 使用越式滴滤壶
- 甜味明显

---

## 4. 咖啡设备 (CoffeeEquipment)

**定义**: 用于制作咖啡的各种设备和器具。

**子类**:
- 研磨机 (Grinder)
- 咖啡机 (CoffeeMachine)
- 冲煮器具 (BrewingDevice)
- 辅助器具 (Accessories)

**属性**:
- `hasBrand`: 品牌 (引用: Brand)
- `hasModel`: 型号 (文本)
- `hasPrice`: 价格 (货币类型)
- `hasMaterial`: 材质 (枚举: 不锈钢/陶瓷/塑料/玻璃)
- `hasCapacity`: 容量 (数值类型: 升/克)

---

### 4.1 研磨机 (Grinder)

**定义**: 将咖啡豆磨成粉末的设备。

**子类**:
- 刀片研磨机 (BladeGrinder)
- 锥形刀盘研磨机 (BurrGrinder-Conical)
- 平刀盘研磨机 (BurrGrinder-Flat)

**属性**:
- `hasGrindSetting`: 研磨刻度 (枚举: 极细/细/中细/中/粗/极粗)
- `hasMotorPower`: 电机功率 (瓦特)
- `hasGrindConsistency`: 研磨一致性 (百分比)

---

### 4.2 咖啡机 (CoffeeMachine)

**定义**: 用于制作咖啡的电动设备。

**子类**:
- 意式咖啡机 (EspressoMachine)
- 滴滤咖啡机 (DripCoffeeMachine)
- 胶囊咖啡机 (CapsuleMachine)
- 全自动咖啡机 (AutomaticCoffeeMachine)

#### 4.2.1 意式咖啡机 (EspressoMachine)

**属性**:
- `hasPressure`: 压力 (数值类型: bar)
- `hasBoilerType`: 锅炉类型 (单锅炉/双锅炉/热交换器)
- `hasWaterCapacity`: 水箱容量 (升)
- `hasPIDControl`: PID温控 (布尔值)
- `hasPreInfusion`: 预浸泡 (布尔值)

**品牌**:
- La Marzocco
- Rocket
- Rancilio
- Breville
- De'Longhi

#### 4.2.2 滴滤咖啡机 (DripCoffeeMachine)

**属性**:
- `hasWarmingPlate`: 保温盘 (布尔值)
- `hasFilterSize`: 滤杯尺寸 (枚举: 1-4杯)
- `hasAutoOff`: 自动关闭 (布尔值)

---

### 4.3 冲煮器具 (BrewingDevice)

**定义**: 手动或半自动制作咖啡的器具。

**子类**:
- 手冲滤杯 (PourOverDripper)
- 法压壶 (FrenchPress)
- 爱乐压 (AeroPress)
- 虹吸壶 (Siphon)
- 摩卡壶 (MokaPot)
- 越南滴滤壶 (VietnamesePhin)
- 冰滴壶 (IceDripper)
- 冷萃壶 (ColdBrewMaker)

#### 4.3.1 手冲滤杯 (PourOverDripper)

**类型**:
- V60滤杯 (V60Dripper)
- 锥形滤杯 (ConeDripper)
- 蛋糕滤杯 (FlatBottomDripper)

**属性**:
- `hasMaterial`: 材质 (陶瓷/玻璃/金属/塑料)
- `hasGrooves`: 沟槽数
- `hasSize`: 尺寸 (1-4人份)

**冲煮参数**:
- 粉水比: 1:15 - 1:17
- 水温: 90°C - 96°C
- 萃取时间: 2:30 - 3:30

#### 4.3.2 法压壶 (FrenchPress)

**特征**:
- 浸泡式萃取
- 金属滤网
- 保留油脂
- 口感醇厚

**冲煮参数**:
- 粉水比: 1:12 - 1:15
- 水温: 90°C - 96°C
- 浸泡时间: 4分钟

#### 4.3.3 爱乐压 (AeroPress)

**特征**:
- 压力萃取
- 便于携带
- 多种冲煮方式
- 易于清洗

---

### 4.4 辅助器具 (Accessories)

**子类**:
- 电子秤 (Scale)
- 温度计 (Thermometer)
- 拉花缸 (Pitcher)
- 咖啡杯 (CoffeeCup)
- 滤纸 (FilterPaper)
- 清洁工具 (CleaningTools)

---

## 5. 咖啡相关实体 (Related Entities)

### 5.1 牛奶 (Milk)

**定义**: 咖啡饮品中常用的奶类添加物。

**类型**:
- 全脂牛奶 (WholeMilk)
- 脱脂牛奶 (SkimMilk)
- 燕麦奶 (OatMilk)
- 杏仁奶 (AlmondMilk)
- 豆奶 (SoyMilk)
- 椰奶 (CoconutMilk)

**属性**:
- `hasFatContent`: 脂肪含量 (百分比)
- `hasProteinContent`: 蛋白质含量 (百分比)
- `hasSugarContent`: 糖含量 (百分比)
- `isDairy`: 是否为动物奶 (布尔值)
- `hasSteamingPerformance`: 蒸汽性能 (枚举: 优秀/良好/一般)

---

### 5.2 甜味剂 (Sweetener)

**类型**:
- 蔗糖 (Sugar)
- 红糖 (BrownSugar)
- 零卡路里甜味剂 (ZeroCalorieSweetener)
- 枫糖浆 (MapleSyrup)
- 蜂蜜 (Honey)
- 焦糖酱 (CaramelSyrup)
- 香草糖浆 (VanillaSyrup)

---

### 5.3 咖啡产区 (CoffeeRegion)

**定义**: 咖啡豆的种植产地。

**主要产区**:
- 非洲 (Africa)
  - 埃塞俄比亚 (Ethiopia)
  - 肯尼亚 (Kenya)
  - 卢旺达 (Rwanda)
  - 坦桑尼亚 (Tanzania)
- 中南美洲 (Central & South America)
  - 巴西 (Brazil)
  - 哥伦比亚 (Colombia)
  - 危地马拉 (Guatemala)
  - 哥斯达黎加 (Costa Rica)
  - 巴拿马 (Panama)
- 亚太地区 (Asia Pacific)
  - 印度尼西亚 (Indonesia)
  - 越南 (Vietnam)
  - 云南 (Yunnan)
  - 巴布亚新几内亚 (Papua New Guinea)

---

### 5.4 咖啡品牌 (CoffeeBrand)

**商业咖啡品牌**:
- 星巴克 (Starbucks)
- 雀巢 (Nescafé)
- 麦斯威尔 (Maxwell)
- ucc

**精品咖啡品牌**:
- Blue Bottle
- Stumptown
- Intelligentsia
- Verve

**咖啡设备品牌**:
- La Marzocco
- Mazzer
- Mahlkönig
- Hario

---

## 6. 冲煮参数 (Brewing Parameters)

### 6.1 研磨度 (GrindSize)

| 研磨度 | 适用器具 | 萃取时间 |
|--------|----------|----------|
| 极细 | 土耳其咖啡 | 2-3分钟 |
| 细 | 意式浓缩 | 25-30秒 |
| 中细 | 手冲V60 | 2-3分钟 |
| 中 | 爱乐压 | 1-2分钟 |
| 粗 | 法压壶 | 4分钟 |
| 极粗 | 冷萃 | 12-24小时 |

---

### 6.2 水温 (WaterTemperature)

| 烘焙程度 | 建议水温 |
|----------|----------|
| 浅烘 | 93°C - 96°C |
| 中烘 | 90°C - 93°C |
| 深烘 | 85°C - 90°C |

---

### 6.3 粉水比 (CoffeeToWaterRatio)

| 冲煮方式 | 粉水比 |
|----------|--------|
| 意式浓缩 | 1:2 |
| 手冲 | 1:15 - 1:17 |
| 法压壶 | 1:12 - 1:15 |
| 冷萃 | 1:8 - 1:5 |

---

## 7. 咖啡产业链 (Coffee Industry Chain)

### 7.1 种植环节 (Cultivation)

**参与者**:
- 咖啡农 (CoffeeFarmer)
- 庄园主 (EstateOwner)
- 合作社 (Cooperative)

**活动**:
- 种植 (Planting)
- 采摘 (Harvesting)
- 初加工 (PrimaryProcessing)

---

### 7.2 加工环节 (Processing)

**处理方法**:
- 日晒法 (NaturalProcess)
- 水洗法 (WashedProcess)
- 蜜处理 (HoneyProcess)
- 湿刨法 (WetHulledProcess)

---

### 7.3 贸易环节 (Trade)

**参与者**:
- 出口商 (Exporter)
- 进口商 (Importer)
- 烘焙商 (Roaster)
- 经销商 (Distributor)

---

### 7.4 零售环节 (Retail)

**业态**:
- 精品咖啡店 (SpecialtyCoffeeShop)
- 连锁咖啡品牌 (ChainCoffeeBrand)
- 便利店咖啡 (ConvenienceStoreCoffee)
- 家庭咖啡 (HomeCoffee)

---

## 8. 感官评价 (Sensory Evaluation)

### 8.1 杯测 (Cupping)

**评估指标**:
- 香气 (Aroma)
- 风味 (Flavor)
- 酸度 (Acidity)
- 甜度 (Sweetness)
- 醇厚度 (Body)
- 余韵 (Aftertaste)
- 平衡度 (Balance)

**评分体系**:
- SCA评分: 80-100分
- Q Grader认证

---

### 8.2 风味描述 (Flavor Descriptors)

**水果类**:
- 柑橘 (Citrus)
- 浆果 (Berry)
- 苹果 (Apple)
- 热带水果 (Tropical)

**甜味类**:
- 焦糖 (Caramel)
- 巧克力 (Chocolate)
- 坚果 (Nutty)
- 蜂蜜 (Honey)

**花香类**:
- 茉莉花 (Jasmine)
- 玫瑰 (Rose)
- 薰衣草 (Lavender)

---

## 9. 关系图谱 (Relationship Graph)

```
CoffeeBean (咖啡豆)
  ├─ hasOrigin → CoffeeRegion (产地)
  ├─ hasProcessing → ProcessingMethod (处理方法)
  ├─ hasRoast → CoffeeRoasting (烘焙)
  └─ isTypeOf → [Arabica/Robusta]

CoffeeRoasting (烘焙)
  ├─ hasLevel → RoastLevel (烘焙度)
  ├─ produces → RoastedBean (烘焙豆)
  └─ uses → CoffeeBean (原料豆)

CoffeeBeverage (咖啡饮品)
  ├─ madeFrom → Coffee (咖啡基底)
  ├─ contains → Milk (牛奶)
  ├─ madeBy → BrewingMethod (冲煮方法)
  └─ servedIn → CoffeeCup (咖啡杯)

Espresso (意式浓缩)
  ├─ extractedBy → EspressoMachine (咖啡机)
  ├─ groundBy → Grinder (研磨机)
  └─ hasParameter → BrewParameters (萃取参数)

CoffeeEquipment (设备)
  ├─ manufacturedBy → Brand (品牌)
  └─ usedFor → BrewingMethod (冲煮方式)
```

---

## 10. 本体复用 (Ontology Reuse)

**可复用的标准本体**:
- FOAF (人物组织)
- GeoNames (地理位置)
- Schema.org (通用概念)
- Dublin Core (元数据)

**命名空间映射**:
```xml
prefix coffee: <http://coffee-ontology.org/>
prefix foaf: <http://xmlns.com/foaf/0.1/>
prefix geo: <http://www.geonames.org/ontology#>
prefix schema: <https://schema.org/>
```

---

## 11. 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 1.0.0 | 2026-03-16 | 初始版本 |

---

## 12. 参考资料

- SCA (Specialty Coffee Association) 标准
- World Coffee Research 品种数据库
- SCAA 杯测评分表
- 咖啡冲煮最佳实践指南
