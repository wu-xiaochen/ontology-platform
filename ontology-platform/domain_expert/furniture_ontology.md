# 家具领域本体 (Furniture Ontology)

> 版本: 1.0  
> 创建日期: 2026-03-16  
> 领域: 家具行业

## 1. 核心概念 (Core Concepts)

### 1.1 家具 (Furniture)

**定义**: 供人们日常生活和社会活动使用的可移动或固定的器具。

**子类**:
- 坐具 (Seating): 椅子、凳子、沙发、躺椅等
- 桌具 (Tables): 餐桌、书桌、咖啡桌、茶几等
- 床具 (Beds): 单人床、双人床、上下铺等
- 柜类 (Cabinets): 衣柜、书柜、鞋柜、橱柜等
- 架类 (Shelving): 书架、置物架、展示架等
- 屏风 (Screens): 隔断屏风、装饰屏风等
- 灯具 (Lighting): 台灯、落地灯、吊灯等

### 1.2 材质 (Material)

**定义**: 家具制作所使用的原材料。

**常见材质**:
- 木材 (Wood): 实木、人造板（刨花板、密度板、胶合板）
- 金属 (Metal): 钢、铁、铝、铜、不锈钢
- 塑料 (Plastic): PP、PE、PVC、ABS
- 玻璃 (Glass): 钢化玻璃、夹胶玻璃、磨砂玻璃
- 皮革 (Leather): 真皮、仿皮、超纤皮
- 织物 (Fabric): 棉、麻、丝、绒布、涤纶
- 石材 (Stone): 大理石、花岗岩、人造石
- 竹材 (Bamboo)
- 藤材 (Rattan)

### 1.3 风格 (Style)

**定义**: 家具呈现的艺术设计风格。

**风格分类**:
- 现代简约 (Modern Minimalist)
- 北欧风格 (Nordic/Scandinavian)
- 中式传统 (Traditional Chinese)
- 日式 (Japanese/Zen)
- 欧式古典 (European Classical)
- 美式乡村 (American Country)
- 工业风 (Industrial)
- 复古 (Vintage/Retro)
- 法式优雅 (French Elegance)
- 意式现代 (Italian Modern)

### 1.4 空间 (Space)

**定义**: 家具摆放或服务的室内空间类型。

**空间类型**:
- 客厅 (Living Room)
- 卧室 (Bedroom)
- 餐厅 (Dining Room)
- 书房 (Study/Office)
- 厨房 (Kitchen)
- 卫生间 (Bathroom)
- 阳台 (Balcony)
- 玄关 (Entrance/Hallway)
- 商业空间 (Commercial): 餐厅、咖啡厅、办公室、酒店

---

## 2. 属性 (Properties)

### 2.1 基础属性

| 属性名 | 说明 | 数据类型 |
|--------|------|----------|
| name | 家具名称 | 文本 |
| model_number | 型号 | 文本 |
| brand | 品牌 | 文本 |
| color | 颜色 | 文本 |
| weight | 重量 | 数值 (kg) |
| warranty | 保修期 | 文本 |

### 2.2 尺寸属性

| 属性名 | 说明 | 数据类型 |
|--------|------|----------|
| length | 长度 | 数值 (cm) |
| width | 宽度 | 数值 (cm) |
| height | 高度 | 数值 (cm) |
| seat_height | 座高 | 数值 (cm) |
| bed_length | 床长 | 数值 (cm) |
| bed_width | 床宽 | 数值 (cm) |

### 2.3 功能属性

| 属性名 | 说明 | 数据类型 |
|--------|------|----------|
| foldable | 可折叠 | 布尔值 |
| adjustable | 可调节 | 布尔值 |
| removable_cover | 可拆卸外套 | 布尔值 |
| storage | 收纳功能 | 布尔值 |
| stackable | 可堆叠 | 布尔值 |
| wheeled | 带轮子 | 布尔值 |

---

## 3. 关系 (Relationships)

```
家具
├── is_made_of (由...制作) → 材质
├── belongs_to_style (属于...风格) → 风格
├── fits_in_space (适用于...空间) → 空间
├── can_be_paired_with (可搭配) → 家具
├── is_part_of (是...的一部分) → 家具组合
└── manufactured_by (由...制造) → 品牌/厂商
```

---

## 4. 家具子类详细定义

### 4.1 椅子 (Chair)

**定义**: 有背或无背的坐具。

**子类**:
- 餐椅 (Dining Chair)
- 办公椅 (Office Chair)
- 休闲椅 (Lounge Chair)
- 摇椅 (Rocking Chair)
- 吧椅 (Bar Stool)
- 儿童椅 (Kids Chair)
- 电脑椅 (Gaming Chair)

**特有属性**:
- seat_width (座宽)
- back_height (靠背高)
- armrest (扶手): 有/无

### 4.2 沙发 (Sofa)

**定义**: 带有软垫的多人坐具。

**子类**:
- 单人沙发 (Armchair/Loveseat)
- 双人沙发 (Two-seater Sofa)
- 三人沙发 (Three-seater Sofa)
- L型沙发 (L-shaped Sofa)
- 懒人沙发 (Bean Bag)
- 沙发床 (Sofa Bed)
- 电动沙发 (Power Sofa)

**特有属性**:
- seat_depth (座深)
- cushion_count (坐垫数量)
- filling_material (填充物)
- frame_material (框架材质)

### 4.3 桌子 (Table)

**定义**: 有平面支撑的家具，用于放置物品或用餐。

**子类**:
- 餐桌 (Dining Table)
- 书桌 (Desk)
- 咖啡桌 (Coffee Table)
- 茶几 (Side Table)
- 梳妆台 (Vanity Table)
- 会议桌 (Conference Table)
- 折叠桌 (Folding Table)

**特有属性**:
- shape (形状): 圆形/方形/长方形/椭圆形
- tabletop_thickness (台面厚度)
- leg_count (桌腿数量)
- extendable (可扩展)

### 4.4 床 (Bed)

**定义**: 用于睡眠的家具。

**子类**:
- 单人床 (Single Bed)
- 双人床 (Double Bed)
- 大床 (King Bed)
- 特大床 (Super King)
- 上下铺 (Bunk Bed)
- 榻榻米 (Tatami)
- 折叠床 (Folding Bed)

**特有属性**:
- mattress_size (床垫尺寸)
- mattress_thickness (床垫厚度)
- headboard_height (床头板高度)
- under_bed_storage (床下收纳)
- bed_frame_material (床架材质)

### 4.5 柜类 (Cabinet)

**定义**: 带门或抽屉的储物家具。

**子类**:
- 衣柜 (Wardrobe)
- 书柜 (Bookcase)
- 鞋柜 (Shoe Cabinet)
- 橱柜 (Kitchen Cabinet)
- 电视柜 (TV Stand)
- 餐边柜 (Sideboard)
- 床头柜 (Nightstand)

**特有属性**:
- door_count (门数量)
- drawer_count (抽屉数量)
- shelf_count (隔板数量)
- handle_type (把手类型)
- hinge_type (铰链类型)

---

## 5. 本体实例示例

### 示例: 现代简约餐厅椅

```json
{
  "type": "Chair",
  "subtype": "Dining Chair",
  "name": "Modern Minimalist Dining Chair",
  "properties": {
    "material": {
      "frame": "Wood - Oak",
      "seat": "Fabric - Grey"
    },
    "dimensions": {
      "length": 45,
      "width": 52,
      "height": 82,
      "seat_height": 45
    },
    "style": "Modern Minimalist",
    "color": "Grey",
    "weight_capacity": 120,
    "foldable": false,
    "stackable": true,
    "fits_space": ["Dining Room", "Kitchen", "Restaurant"],
    "brand": "IKEA",
    "price_range": "Medium"
  }
}
```

### 示例: L型布艺沙发

```json
{
  "type": "Sofa",
  "subtype": "L-shaped Sofa",
  "name": "北欧风L型布艺沙发",
  "properties": {
    "material": {
      "frame": "Solid Wood",
      "fabric": "Linen - Light Grey",
      "filling": "High-resilience Foam"
    },
    "dimensions": {
      "width": 280,
      "depth": 180,
      "height": 85,
      "seat_depth": 60,
      "seat_height": 42
    },
    "style": "Nordic",
    "color": "Light Grey",
    "cushion_count": 5,
    "chaise_longue": true,
    "storage": true,
    "removable_cover": true,
    "fits_space": ["Living Room"],
    "brand": "NORDLI",
    "warranty": "10 years"
  }
}
```

---

## 6. 领域规则 (Domain Rules)

1. **尺寸适配规则**: 椅子座高一般在 40-50cm，办公椅可调节至 40-65cm
2. **承重规则**: 成人椅子承重 ≥ 100kg，儿童椅子 ≥ 50kg
3. **材质组合**: 金属腿+木质座面 = 常见组合
4. **空间匹配**: 餐桌周围至少留 60cm 通道空间
5. **床尺寸标准**: 
   - 单人床: 90cm × 200cm
   - 双人床: 150cm × 200cm  
   - 大床: 180cm × 200cm

---

## 7. 扩展方向

- 添加家具价格等级
- 添加环保认证属性 (FSC, E0级环保)
- 添加安装难度属性
- 添加用户评价维度
- 添加室内设计师推荐组合
