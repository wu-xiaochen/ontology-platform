# Fashion Ontology / 时尚领域本体

## 概述

本文档定义了时尚（Fashion）领域的领域本体，用于支持时尚知识图谱、智能推荐、设计辅助等应用场景。

---

## 1. 核心实体类型

### 1.1 服装大类 (Apparel Category)

| 实体ID | 中文名称 | 英文名称 | 定义 |
|--------|----------|----------|------|
| apparel_top | 上装 | Top | 穿着于上半身的服装 |
| apparel_bottom | 下装 | Bottom | 穿着于下半身的服装 |
| apparel_outerwear | 外套 | Outerwear | 穿在最外层的服装 |
| apparel_dress | 连衣裙/连体裤 | Dress/Overall | 上下连体的服装 |
| apparel_onesie | 连体衣 | Onesie | 上下连体的紧身服装 |
| apparel_activewear | 运动服装 | Activewear | 用于运动的功能性服装 |
| apparel_formal | 正装 | Formal Wear | 正式场合穿着的服装 |
| apparel_casual | 休闲装 | Casual Wear | 日常休闲穿着的服装 |
| apparel_underwear | 内衣 | Underwear |贴身穿着的衣物 |
| apparel_swimwear | 泳装 | Swimwear | 游泳时穿着的服装 |

### 1.2 服装细分类 (Apparel Subcategory)

**上装子类：**
| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| top_tshirt | T恤 | T-Shirt |
| top_shirt | 衬衫 | Shirt |
| top_blouse | 女衬衫 | Blouse |
| top_sweater | 毛衣 | Sweater |
| top_hoodie | 连帽卫衣 | Hoodie |
| top_tank | 背心 | Tank Top |
| top_vest | 马甲 | Vest |
| top_cardigan | 开衫 | Cardigan |
| top_polo | POLO衫 | Polo Shirt |

**下装子类：**
| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| bottom_pants | 裤子 | Pants |
| bottom_jeans | 牛仔裤 | Jeans |
| bottom_shorts | 短裤 | Shorts |
| bottom_skirt | 裙子 | Skirt |
| bottom_leggings | 紧身裤 | Leggings |
| bottom_trousers | 西裤 | Trousers |
| bottom_joggers | 运动裤 | Joggers |
| bottom_cargo | 工装裤 | Cargo Pants |

**外套子类：**
| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| outer_jacket | 夹克 | Jacket |
| outer_coat | 大衣 | Coat |
| outer_parka | 派克大衣 | Parka |
| outer_blazer | 西装外套 | Blazer |
| outer_bomber | 飞行员夹克 | Bomber Jacket |
| outer_denim | 牛仔外套 | Denim Jacket |
| outer_trench | 风衣 | Trench Coat |
| outer_raincoat | 雨衣 | Raincoat |
| outer_down | 羽绒服 | Down Jacket |

### 1.3 配饰 (Accessories)

| 实体ID | 中文名称 | 英文名称 | 子类 |
|--------|----------|----------|------|
| acc_headwear | 头饰 | Headwear | 帽子、发带、头巾 |
| acc_eyewear | 眼镜 | Eyewear | 太阳镜、眼镜 |
| acc_jewelry | 珠宝首饰 | Jewelry | 项链、耳环、手镯、戒指 |
| acc_bag | 包袋 | Bag | 手提包、单肩包、双肩包、钱包 |
| acc_watch | 手表 | Watch | - |
| acc_belt | 腰带 | Belt | - |
| acc_scarf | 围巾 | Scarf | - |
| acc_gloves | 手套 | Gloves | - |
| acc_socks | 袜子 | Socks | - |
| acc_tie | 领带 | Tie | 领带、领结 |
| acc_ handkerchief | 方巾 | Handkerchief | - |
| acc_umbrella | 伞 | Umbrella | - |
| acc_earrings | 耳饰 | Earrings | 耳钉、耳坠、耳夹 |

### 1.4 鞋履 (Footwear)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| shoe_sneakers | 运动鞋 | Sneakers |
| shoe_heels | 高跟鞋 | Heels |
| shoe_boots | 靴子 | Boots |
| shoe_sandals | 凉鞋 | Sandals |
| shoe_loafers | 乐福鞋 | Loafers |
| shoe_oxfords | 牛津鞋 | Oxfords |
| shoe_flats | 平底鞋 | Flats |
| shoe_slippers | 拖鞋 | Slippers |
| shoe_ankle | 低帮鞋 | Ankle Boots |

---

## 2. 面料与材质 (Materials)

### 2.1 天然纤维 (Natural Fibers)

| 实体ID | 中文名称 | 英文名称 | 特性 |
|--------|----------|----------|------|
| mat_cotton | 棉 | Cotton | 透气、吸湿、柔软 |
| mat_silk | 丝绸 | Silk | 光滑、柔软、有光泽 |
| mat_wool | 羊毛 | Wool | 保暖、柔软、有弹性 |
| mat_linen | 亚麻 | Linen | 透气、吸湿、凉爽 |
| mat_cashmere | 羊绒 | Cashmere | 柔软、保暖、高端 |
| mat_hemp | 大麻 | Hemp | 耐用、透气、环保 |
| mat_silk_mulberry | 桑蚕丝 | Mulberry Silk | 高品质丝绸 |
| mat_silk_tussah | 柞蚕丝 | Tussah Silk | 野生丝绸 |

### 2.2 人造纤维 (Synthetic Fibers)

| 实体ID | 中文名称 | 英文名称 | 特性 |
|--------|----------|----------|------|
| mat_polyester | 涤纶 | Polyester | 抗皱、耐磨、易护理 |
| mat_nylon | 尼龙 | Nylon | 强度高、轻便、耐磨 |
| mat_acrylic | 腈纶 | Acrylic | 柔软、保暖、羊毛感 |
| mat_spandex | 氨纶 | Spandex | 弹性好、舒适 |
| mat_rayon | 人造丝 | Rayon | 柔软、光泽、吸湿 |
| mat_acetate | 醋酯纤维 | Acetate | 光泽、柔软 |
| mat_modal | 莫代尔 | Modal | 柔软、吸湿 |
| mat_tencel | 天丝 | Tencel | 环保、柔软、光泽 |
| mat_velvet | 天鹅绒 | Velvet | 柔软、光滑、有光泽 |

### 2.3 混纺面料 (Blended Fabrics)

| 实体ID | 中文名称 | 英文名称 | 成分 |
|--------|----------|----------|------|
| mat_tc | 涤棉 | T/C | 涤纶+棉 |
| mat_cvc | 棉涤 | CVC | 棉+涤纶 |
| mat_wool_blend | 混纺羊毛 | Wool Blend | 羊毛+其他纤维 |
| mat_denim | 牛仔布 | Denim | 棉+其他 |

---

## 3. 时尚风格 (Fashion Styles)

### 3.1 主流风格

| 实体ID | 中文名称 | 英文名称 | 特征描述 |
|--------|----------|----------|----------|
| style_classic | 经典风格 | Classic | 简约、永恒、优雅 |
| style_casual | 休闲风格 | Casual | 舒适、自然、随性 |
| style_street | 街头风格 | Street | 潮流、个性、叛逆 |
| style_business | 商务风格 | Business | 专业、干练、正式 |
| style_sporty | 运动风格 | Sporty | 功能性、活力、舒适 |
| style_bohemian | 波西米亚 | Bohemian | 浪漫、民族、异域 |
| style_vintage | 复古风格 | Vintage | 怀旧、经典、再流行 |
| style_minimalist | 极简主义 | Minimalist | 简洁、功能性、少即是多 |
| style_glamorous | 华丽风格 | Glamorous | 奢华、性感、戏剧性 |
| style_edgy | 前卫风格 | Edgy | 酷、叛逆、独特 |
| style_preppy | 学院风格 | Preppy | 学院、正式、优雅 |
| style_athleisure | 运动休闲 | Athleisure | 运动+休闲混搭 |
| style_normcore | Normcore | Normcore | 朴素、舒适、中性 |
| style_y2k | Y2K风格 | Y2K | 千禧年、数字化、年轻 |
| style_kawaii | 卡哇伊 | Kawaii | 可爱、粉色、少女 |

### 3.2 地域/文化风格

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| style_parisian | 法式风格 | Parisian |
| style_japanese | 日系风格 | Japanese |
| style_korean | 韩系风格 | Korean |
| style_american | 美式风格 | American |
| style_british | 英伦风格 | British |
| style_italian | 意式风格 | Italian |
| style_scandinavian | 北欧风格 | Scandinavian |
| style_indian | 印度风格 | Indian |
| style_african | 非洲风格 | African |

---

## 4. 颜色与图案 (Colors & Patterns)

### 4.1 色彩体系

**基础色：**
| 实体ID | 中文名称 | 英文名称 | 色值 |
|--------|----------|----------|------|
| color_black | 黑色 | Black | #000000 |
| color_white | 白色 | White | #FFFFFF |
| color_gray | 灰色 | Gray | #808080 |
| color_navy | 深蓝色 | Navy | #000080 |
| color_blue | 蓝色 | Blue | #0000FF |
| color_red | 红色 | Red | #FF0000 |
| color_pink | 粉色 | Pink | #FFC0CB |
| color_green | 绿色 | Green | #008000 |
| color_yellow | 黄色 | Yellow | #FFFF00 |
| color_orange | 橙色 | Orange | #FFA500 |
| color_purple | 紫色 | Purple | #800080 |
| color_brown | 棕色 | Brown | #A52A2A |
| color_beige | 米色 | Beige | #F5F5DC |
| color_khaki | 卡其色 | Khaki | #C3B091 |
| color_camel | 驼色 | Camel | #C19A6B |
| color_cream | 奶油色 | Cream | #FFFDD0 |
| color_burgundy | 酒红色 | Burgundy | #800020 |
| color_teal | 青绿色 | Teal | #008080 |
| color_coral | 珊瑚色 | Coral | #FF7F50 |
| color_mint | 薄荷绿 | Mint | #98FF98 |

### 4.2 图案类型

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| pattern_solid | 纯色 | Solid |
| pattern_stripe | 条纹 | Stripe |
| pattern_plaid | 格子 | Plaid |
| pattern_check | 棋盘格 | Check |
| pattern_dots | 波点 | Polka Dot |
| pattern_floral | 花朵 | Floral |
| pattern_abstract | 抽象 | Abstract |
| pattern_geometric | 几何 | Geometric |
| pattern_animal | 动物纹 | Animal Print |
| pattern_leopard | 豹纹 | Leopard |
| pattern_zebra | 斑马纹 | Zebra |
| pattern_snake | 蛇纹 | Snake |
| pattern_camo | 迷彩 | Camouflage |
| pattern_paisley | 佩斯利 | Paisley |
| pattern_herringbone | 人字纹 | Herringbone |

---

## 5. 设计与工艺 (Design & Craftsmanship)

### 5.1 服装细节

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| detail_collar | 领子 | Collar |
| detail_neckline | 领口 | Neckline |
| detail_sleeve | 袖子 | Sleeve |
| detail_cuff | 袖口 | Cuff |
| detail_waist | 腰身 | Waist |
| detail_hem | 下摆 | Hem |
| detail_zipper | 拉链 | Zipper |
| detail_button | 纽扣 | Button |
| detail_pocket | 口袋 | Pocket |
| detail_hood | 帽子 | Hood |
| detail_zip | 口袋拉链 | Zipper Pocket |
| detail_pleat | 褶皱 | Pleat |
| detail_ruffle | 荷叶边 | Ruffle |
| detail_lace | 蕾丝 | Lace |
| detail_embroidery | 刺绣 | Embroidery |
| detail_print | 印花 | Print |
| detail_sequin | 亮片 | Sequin |
| detail_beading | 珠饰 | Beading |
| detail_patch | 补丁 | Patch |

### 5.2 领型

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| collar_round | 圆领 | Round Neck |
| collar_v | V领 | V-Neck |
| collar_u | U领 | U-Neck |
| collar_scoop | 船领 | Scoop Neck |
| collar_henley | 亨利领 | Henley Neck |
| collar_poloshirt | POLO领 | Polo Collar |
| collar_shirt | 衬衫领 | Shirt Collar |
| collar_mandarin | 中式领 | Mandarin Collar |
| collar_sweetheart | 心形领 | Sweetheart Neckline |
| collar_off_shoulder | 露肩领 | Off-Shoulder |
| collar_square | 方领 | Square Neck |

### 5.3 袖型

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| sleeve_long | 长袖 | Long Sleeve |
| sleeve_short | 短袖 | Short Sleeve |
| sleeve_sleeveless | 无袖 | Sleeveless |
| sleeve_three_quarter | 七分袖 | Three-Quarter Sleeve |
| sleeve_cap | 短袖/盖袖 | Cap Sleeve |
| sleeve_bell | 喇叭袖 | Bell Sleeve |
| sleeve_butterfly | 蝴蝶袖 | Butterfly Sleeve |
| sleeve_raglan | 插肩袖 | Raglan Sleeve |
| sleeve_puff | 泡泡袖 | Puff Sleeve |

---

## 6. 品牌与设计师 (Brands & Designers)

### 6.1 品牌类型

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| brand_luxury | 奢侈品牌 | Luxury Brand |
| brand_designer | 设计师品牌 | Designer Brand |
| brand_premium | 高端品牌 | Premium Brand |
| brand_mid_range | 中端品牌 | Mid-Range Brand |
| brand_mass | 大众品牌 | Mass Market Brand |
| brand_fast_fashion | 快时尚 | Fast Fashion |
| brand_streetwear | 潮牌 | Streetwear Brand |
| brand_sports | 运动品牌 | Sports Brand |

### 6.2 著名品牌示例

**奢侈品牌：**
- Chanel (香奈儿)
- Louis Vuitton (路易威登)
- Gucci (古驰)
- Prada (普拉达)
- Dior (迪奥)
- Hermès (爱马仕)
- Burberry (博柏利)
- Versace (范思哲)

**设计师品牌：**
- Alexander McQueen
- Balenciaga
- Givenchy
- Valentino
- Off-White
- Supreme

**快时尚品牌：**
- Zara
- H&M
- Uniqlo (优衣库)
- Gap
- Forever 21

---

## 7. 场景与场合 (Occasions)

| 实体ID | 中文名称 | 英文名称 | 描述 |
|--------|----------|----------|------|
| occ_work | 工作/职场 | Work | 办公室商务场合 |
| occ_casual | 日常休闲 | Casual | 日常生活 |
| occ_date | 约会 | Date | 浪漫约会场合 |
| occ_party | 派对 | Party | 社交派对 |
| occ_formal | 正式场合 | Formal | 正式活动、典礼 |
| occ_wedding | 婚礼 | Wedding | 婚礼场合 |
| occ_sport | 运动 | Sport | 运动健身 |
| occ_beach | 海滩 | Beach | 海边度假 |
| occ_travel | 旅行 | Travel | 旅行出游 |
| occ_ceremony | 仪式 | Ceremony | 颁奖、毕业等 |
| occ_dinner | 晚宴 | Dinner | 正式晚餐 |
| occ_holiday | 节日 | Holiday | 节日庆祝 |

---

## 8. 季节与气候 (Seasons & Climate)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| season_spring | 春季 | Spring |
| season_summer | 夏季 | Summer |
| season_autumn | 秋季 | Autumn |
| season_winter | 冬季 | Winter |
| season_all | 四季通用 | All Season |

---

## 9. 关系定义 (Relationships)

### 9.1 服装结构关系

```
Apparel (服装)
├── has_category → Category (属于某大类)
├── has_subcategory → Subcategory (属于某细分类)
├── made_of → Material (由某面料制成)
├── features → Detail (具有某细节设计)
├── belongs_to_style → Style (属于某风格)
├── suitable_for_occasion → Occasion (适合某场合)
├── suitable_for_season → Season (适合某季节)
└── has_color → Color (具有某颜色)
```

### 9.2 搭配关系

```
Outfit (穿搭)
├── consists_of → Apparel (包含多件服装)
├── includes → Accessory (搭配配饰)
├── matches → Footwear (搭配鞋履)
└── appropriate_for → Occasion (适合某场合)
```

### 9.3 品牌关系

```
Brand
├── produces → Apparel (生产服装)
├── has_designer → Designer (签约设计师)
├── belongs_to → BrandType (属于某品牌类型)
└── competes_with → Brand (与某品牌竞争)
```

---

## 10. 属性定义 (Properties)

### 10.1 服装属性

| 属性名 | 中文 | 类型 | 描述 |
|--------|------|------|------|
| name | 名称 | String | 服装名称 |
| price | 价格 | Float | 零售价 |
| currency | 货币 | String | 货币单位 |
| gender | 性别 | Enum | 男/女/中性 |
| age_group | 年龄段 | Enum | 儿童/青少年/成人/老年 |
| size | 尺码 | String | XS/S/M/L/XL等 |
| color | 颜色 | String | 主色 |
| pattern | 图案 | String | 图案类型 |
| material | 面料 | String | 主要面料 |
| care_instruction | 洗涤说明 | String | 护理方式 |
| season | 季节 | String | 适用季节 |
| occasion | 场合 | String | 适用场合 |
| style | 风格 | String | 风格 |
| fit | 版型 | Enum | 修身/宽松/标准 |
| length | 衣长 | Enum | 短款/常规/长款 |
| sleeve_length | 袖长 | Enum | 无袖/短袖/长袖 |
| neckline | 领型 | String | 领口类型 |
| waistline | 腰线 | Enum | 高腰/中腰/低腰 |
| closure_type | 闭合方式 | String | 纽扣/拉链/套头 |
| decoration | 装饰 | String | 装饰元素 |
| pattern_type | 图案类型 | String | 印花类型 |

### 10.2 配饰属性

| 属性名 | 中文 | 类型 | 描述 |
|--------|------|------|------|
| material | 材质 | String | 材质 |
| metal_type | 金属类型 | String | 金属材质 |
| gemstone | 宝石 | String | 镶嵌宝石 |
| size | 尺寸 | String | 尺寸 |
| capacity | 容量 | String | 包容量 |
| strap_type | 肩带类型 | String | 肩带样式 |

---

## 11. 时尚术语 (Fashion Terminology)

### 11.1 行业术语

| 术语 | 英文 | 定义 |
|------|------|------|
| 趋势 | Trend | 特定时期内的流行方向 |
| 季节系列 | Collection | 品牌按季节发布的产品系列 |
| 时装周 | Fashion Week | 品牌展示新系列的时装发布活动 |
| T台 | Runway | 时装秀的展示台 |
| 高级定制 | Haute Couture | 高级定制服装 |
| 成衣 | Ready-to-Wear | 批量生产的成衣 |
| 胶囊系列 | Capsule Collection | 限量经典系列 |
| 快时尚 | Fast Fashion | 快速响应流行的商业模式 |
| 复古 | Vintage | 具有时代特征的复古服饰 |
| 古着 | Retro | 复古风格的新服装 |

### 11.2 服装部位术语

| 术语 | 英文 | 定义 |
|------|------|------|
| 肩线 | Shoulder Line | 服装肩部的轮廓线 |
| 胸围 | Bust | 胸部一周的围度 |
| 腰围 | Waist | 腰部一周的围度 |
| 臀围 | Hip | 臀部一周的围度 |
| 衣长 | Length | 服装从肩到下摆的长度 |
| 袖长 | Sleeve Length | 袖子从肩到袖口的长度 |
| 下摆 | Hem | 服装底部的边缘 |
| 领口 | Neckline | 领子周围的开口 |

---

## 12. 本体元数据

| 属性 | 值 |
|------|-----|
| 本体名称 | Fashion Ontology |
| 版本 | 1.0 |
| 创建日期 | 2026-03-16 |
| 语言 | 中文/English |
| 领域 | 时尚/服装 |
| 维护者 | OpenClaw Agent |
| 应用场景 | 知识图谱、智能推荐、设计辅助 |

---

## 13. 扩展建议

### 未来可扩展领域

1. **可持续时尚** - 环保材料、二手交易、古着鉴定
2. **时尚电商** - 商品属性、库存、促销
3. **体型分类** - 身材类型、尺码推荐
4. **色彩搭配** - 配色理论、搭配建议
5. **趋势预测** - 流行趋势分析
6. **虚拟试衣** - 尺码推荐、虚拟形象

---

*本文档为时尚领域本体的基础版本，后续可根据实际应用需求进行扩展和细化。*
