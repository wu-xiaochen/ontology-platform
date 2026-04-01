# 酒类领域本体 (Wine & Spirits Ontology)

## 1. 概述

本本体定义了酒类饮品领域的核心概念、分类体系、属性和关系，为知识图谱构建和语义推理提供标准化模型。

**命名空间**: `wine-ontology`
**版本**: 1.0.0
**创建日期**: 2026-03-16

---

## 2. 核心类 (Core Classes)

### 2.1 酒类饮品 (AlcoholicBeverage)

**定义**: 含有乙醇的饮品总称。

**子类**:
- 葡萄酒 (Wine)
- 啤酒 (Beer)
- 烈酒 (Spirits)
- 蒸馏酒 (DistilledBeverage)
- 配制酒 (Liqueur)
- 清酒 (Sake)
- 黄酒 (Huangjiu)
- 啤酒类 (MaltBeverage)

**属性**:
- `hasAlcoholContent`: 酒精度数 (数值类型: 百分比)
- `hasOrigin`: 产地 (引用: Region)
- `hasBrand`: 品牌 (引用: Brand)
- `hasVintage`: 年份 (整数)
- `hasPrice`: 价格 (货币类型)
- `hasVolume`: 容量 (毫升)
- `hasTastingNotes`: 品尝笔记 (文本)

---

### 2.2 葡萄酒 (Wine)

**定义**: 由葡萄发酵而成的酒类。

**子类**:
- 红葡萄酒 (RedWine)
- 白葡萄酒 (WhiteWine)
- 桃红葡萄酒 (RoséWine)
- 起泡酒 (SparklingWine)
- 加强葡萄酒 (FortifiedWine)

**属性**:
- `hasGrapeVariety`: 葡萄品种 (引用: GrapeVariety)
- `hasRegion`: 产区 (引用: WineRegion)
- `hasAgePotential`: 陈年潜力 (整数: 年)
- `hasBarrelAging`: 橡木桶陈酿 (布尔值)
- `hasSugarLevel`: 含糖量 (枚举: Dry/Semi-Dry/Sweet/Semi-Sweet)

#### 2.2.1 红葡萄酒 (RedWine)

**特征**: 采用红/黑葡萄带皮发酵

**典型品种**:
- 赤霞珠 (Cabernet Sauvignon)
- 梅洛 (Merlot)
- 黑皮诺 (Pinot Noir)
- 西拉 (Syrah/Shiraz)
- 品丽珠 (Cabernet Franc)

#### 2.2.2 白葡萄酒 (WhiteWine)

**特征**: 采用白葡萄或去皮红葡萄发酵

**典型品种**:
- 霞多丽 (Chardonnay)
- 长相思 (Sauvignon Blanc)
- 雷司令 (Riesling)
- 维欧尼 (Viognier)
- 琼瑶浆 (Gewürztraminer)

#### 2.2.3 起泡酒 (SparklingWine)

**定义**: 含有二氧化碳气泡的葡萄酒

**类型**:
- 香槟 (Champagne)
- 卡瓦 (Cava)
- 普罗塞克 (Prosecco)
- 蓝布鲁斯科 (Lambrusco)

---

### 2.3 啤酒 (Beer)

**定义**: 由麦芽、啤酒花和水发酵而成的酒类。

**子类**:
- 艾尔啤酒 (Ale)
- 拉格啤酒 (Lager)
- 世涛啤酒 (Stout)
- 波特啤酒 (Porter)
- 小麦啤酒 (WheatBeer)

**属性**:
- `hasIBU`: 苦度单位 (整数: 0-100)
- `hasSRM`: 色度值 (整数)
- `hasMaltVariety`: 麦芽品种 (引用: MaltVariety)
- `hasHopVariety`: 啤酒花品种 (引用: HopVariety)
- `hasBrewery`: 酿酒厂 (引用: Brewery)

---

### 2.4 烈酒 (Spirits)

**定义**: 通过蒸馏得到的酒精度数较高的酒类。

**子类**:
- 白兰地 (Brandy)
- 威士忌 (Whiskey)
- 伏特加 (Vodka)
- 朗姆酒 (Rum)
- 金酒 (Gin)
- 龙舌兰 (Tequila)
- 中国白酒 (Baijiu)

**属性**:
- `hasDistillationMethod`: 蒸馏方法 (枚举: PotStill/ColumnStill)
- `hasAgingDuration`: 陈酿时长 (整数: 年)
- `hasBarrelType`: 桶类型 (引用: BarrelType)
- `hasBaseIngredient`: 基础原料 (引用: Ingredient)

---

### 2.5 配制酒/利口酒 (Liqueur)

**定义**: 在蒸馏酒中添加香料、果实或奶油等调味而成的甜酒。

**类型**:
- 君度 (Cointreau)
- 咖啡利口酒 (Kahlua)
- 百利甜 (Baileys)
- 杜本内 (Dubonnet)
- 味美思 (Vermouth)

---

## 3. 葡萄品种 (GrapeVariety)

### 3.1 红葡萄品种

| 品种 | 原产地 | 典型特征 | 著名产区 |
|------|--------|----------|----------|
| 赤霞珠 | 法国波尔多 | 单宁强、结构感强 | 波尔多、纳帕谷 |
| 梅洛 | 法国波尔多 | 果香浓郁、口感柔顺 | 波尔多 |
| 黑皮诺 | 法国勃艮第 | 优雅、轻盈 | 勃艮第、俄勒冈 |
| 西拉 | 法国罗纳河谷 | 浓郁、辛辣 | 澳大利亚、法国 |

### 3.2 白葡萄品种

| 品种 | 原产地 | 典型特征 | 著名产区 |
|------|--------|----------|----------|
| 霞多丽 | 法国勃艮第 | 多样性、高品质 | 勃艮第、加州 |
| 长相思 | 法国卢瓦尔河谷 | 酸度高、青草味 | 卢瓦尔、新西兰 |
| 雷司令 | 德国 | 酸度适中、果香 | 德国、阿尔萨斯 |
| 琼瑶浆 | 德国/意大利 | 芳香浓郁 | 阿尔萨斯 |

---

## 4. 产区 (WineRegion)

### 4.1 法国

- **波尔多 (Bordeaux)**: 左岸/右岸分界
- **勃艮第 (Burgundy)**: 特级园体系
- **香槟 (Champagne)**: 起泡酒圣地
- **罗纳河谷 (Rhône Valley)**: 北罗/南罗
- **阿尔萨斯 (Alsace)**: 白葡萄酒

### 4.2 意大利

- **托斯卡纳 (Tuscany)**: 基安蒂/布鲁奈罗
- **皮埃蒙特 (Piedmont)**: 巴罗洛/巴巴莱斯科
- **威尼托 (Veneto)**: 普罗塞克/阿玛罗尼

### 4.3 西班牙

- **里奥哈 (Rioja)**: 橡木桶陈酿分级
- **杜埃罗河岸 (Ribera del Duero)**: 丹魄
- **普里奥拉 (Priorat)**: 加泰罗尼亚

### 4.4 新世界

- **美国纳帕谷 (Napa Valley)**: 赤霞珠
- **阿根廷门多萨 (Mendoza)**: 马尔贝克
- **澳大利亚巴罗萨 (Barossa)**: 设拉子
- **新西兰马尔堡 (Marlborough)**: 长相思
- **智利空加瓜谷 (Colchagua)**: 佳美娜

---

## 5. 品牌与酒庄 (Brand & Estate)

### 5.1 品牌类型

- **名庄 (Great Estate)**: 如拉菲、木桐
- **精品酒庄 (Boutique Winery)**: 小规模手工酿酒
- **商业品牌 (Commercial Brand)**: 大批量生产
- **合作社 (Cooperative)**: 酒农联合

### 5.2 著名品牌示例

- **拉菲古堡 (Château Lafite Rothschild)**
- **木桐酒庄 (Château Mouton Rothschild)**
- **奥比昂酒庄 (Château Haut-Brion)**
- **玛歌酒庄 (Château Margaux)**

---

## 6. 酿酒相关概念

### 6.1 酿酒工艺 (Winemaking)

- **采收 (Harvest)**: 葡萄采摘时机
- **破碎 (Crushing)**: 葡萄破皮
- **发酵 (Fermentation)**: 酵母转化糖为酒精
- **压榨 (Pressing)**: 分离酒液
- **陈酿 (Aging)**: 橡木桶/瓶中成熟
- **装瓶 (Bottling)**: 最终封装

### 6.2 酿造参数

| 参数 | 描述 | 典型值 |
|------|------|--------|
| pH | 酸度 | 3.0-4.0 |
| TA | 可滴定酸度 | 4-8 g/L |
| 残糖 | 发酵后糖分 | 0-20 g/L |
| 酒精度 | 乙醇体积 | 11-15% |

---

## 7. 酒杯与饮用 (Glassware & Service)

### 7.1 酒杯类型

- **波尔多杯**: 适合赤霞珠等浓郁红酒
- **勃艮第杯**: 适合黑皮诺等优雅红酒
- **白葡萄酒杯**: 较小、保持低温
- **香槟杯**: 细长气泡保持
- ** ISO杯**: 标准品鉴杯

### 7.2 服务温度

| 酒类型 | 温度 (°C) |
|--------|------------|
| 红葡萄酒 | 16-18 |
| 白葡萄酒 | 8-12 |
| 起泡酒 | 6-8 |
| 烈酒 | 室温或加冰 |

---

## 8. 品鉴术语 (Tasting Terminology)

### 8.1 外观 (Appearance)

- **透明度**: 清澈/浑浊
- **颜色**: 深浅、色调
- **挂杯**: 酒泪/腿

### 8.2 香气 (Aroma)

- **一类香气**: 葡萄本身香
- **二类香气**: 发酵产生
- **三类香气**: 陈酿形成

### 8.3 风味 (Palate)

- **单宁**: 涩感、收敛性
- **酸度**: 清新、活泼
- **酒体**: 轻盈/饱满
- **余味**: 长度和特征

---

## 9. 关系图谱

```
AlcoholicBeverage
├── Wine (葡萄酒)
│   ├── RedWine
│   │   └── GrapeVariety → Cabernet Sauvignon, Merlot, Pinot Noir
│   ├── WhiteWine
│   │   └── GrapeVariety → Chardonnay, Sauvignon Blanc
│   ├── RoséWine
│   ├── SparklingWine → Champagne, Prosecco
│   └── FortifiedWine → Port, Sherry
├── Beer (啤酒)
│   ├── Ale
│   ├── Lager
│   └── Stout
├── Spirits (烈酒)
│   ├── Whiskey → Bourbon, Scotch
│   ├── Vodka
│   ├── Gin
│   ├── Rum
│   ├── Tequila
│   └── Baijiu (白酒)
└── Liqueur (配制酒)
```

---

## 10. 实例示例

### 实例1: 拉菲古堡 2010

```json
{
  "type": "RedWine",
  "name": "Château Lafite Rothschild 2010",
  "hasAlcoholContent": 13.5,
  "hasVintage": 2010,
  "hasGrapeVariety": "Cabernet Sauvignon",
  "hasRegion": "Bordeaux, Pauillac",
  "hasBrand": "Domaines Barons de Rothschild",
  "hasPrice": 3500,
  "hasTastingNotes": "黑醋栗、雪松、矿物味，单宁细腻，陈年潜力50年+"
}
```

### 实例2: 奔富葛兰许

```json
{
  "type": "RedWine",
  "name": "Penfolds Grange",
  "hasAlcoholContent": 14.5,
  "hasVintage": 2018,
  "hasGrapeVariety": "Shiraz",
  "hasRegion": "Australia, South Australia",
  "hasBrand": "Penfolds",
  "hasPrice": 700,
  "hasTastingNotes": "浓郁黑色水果、巧克力、香料，结构宏大"
}
```

---

## 11. 本体扩展

本本体可根据需要扩展以下方向：

- **美食搭配**: 食物与酒类搭配规则
- **收藏投资**: 酒类投资价值评估
- **供应链**: 从葡萄到酒杯的全程追溯
- **健康科学**: 饮酒与健康关系
- **文化历史**: 酒类发展史与文化背景

---

*本本体由 ontology-platform 自动生成*