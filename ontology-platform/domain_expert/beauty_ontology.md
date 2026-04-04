# Beauty Ontology / 美容领域本体

## 概述

本文档定义了美容（Beauty）领域的领域本体，用于支持美容知识图谱、智能推荐、肤质分析、产品推荐等应用场景。

---

## 1. 核心实体类型

### 1.1 护肤品类 (Skincare Products)

| 实体ID | 中文名称 | 英文名称 | 定义 |
|--------|----------|----------|------|
| skincare_cleanser | 洁面产品 | Cleanser | 用于清洁面部皮肤的产品 |
| skincare_toner | 爽肤水/柔肤水 | Toner | 调理肌肤、补水的产品 |
| skincare_essence | 精华液 | Essence | 高浓度活性成分的护肤品 |
| skincare_serum | 精华素 | Serum | 针对特定肌肤问题的功能性精华 |
| skincare_moisturizer | 面霜/乳液 | Moisturizer | 保湿锁水的护肤品 |
| skincare_eye_cream | 眼霜 | Eye Cream | 专为眼部肌肤设计的保湿修护产品 |
| skincare_sunscreen | 防晒霜 | Sunscreen | 防护紫外线伤害的产品 |
| skincare_mask | 面膜 | Face Mask | 密集护理的面膜产品 |
| skincare_exfoliator | 去角质产品 | Exfoliator | 去除老化角质的产品 |
| skincare_mist | 喷雾 | Facial Mist | 补水保湿喷雾 |
| skincare_oil | 护肤油 | Face Oil | 滋养修护的油类护肤品 |
| skincare_cream | 晚霜 | Night Cream | 夜间修护的滋养霜 |

#### 1.1.1 洁面产品子类

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| cleanser_foam | 泡沫洁面 | Foam Cleanser |
| cleanser_gel | 凝胶洁面 | Gel Cleanser |
| cleanser_cream |  cream Cleanser |
| cleanser_oil | 洁面油 | Cleansing Oil |
| cleanser_balm | 洁面膏/卸妆膏 | Cleansing Balm |
| cleanser_water | 洁面水 | Cleansing Water |
| cleanser_bar | 洁面皂 | Soap Bar |
| cleanser_powder | 洁面粉 | Powder Cleanser |

#### 1.1.2 面膜子类

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| mask_sheet | 贴片面膜 | Sheet Mask |
| mask_cream | 乳霜面膜 | Cream Mask |
| mask_clay | 泥膜 | Clay Mask |
| mask_gel | 凝胶面膜 | Gel Mask |
| mask_peel | 撕拉面膜 | Peel-off Mask |
| mask_sleep | 睡眠面膜 | Sleeping Mask |
| mask_eye | 眼膜 | Eye Mask |

### 1.2 彩妆品类 (Makeup Products)

| 实体ID | 中文名称 | 英文名称 | 定义 |
|--------|----------|----------|------|
| makeup_base | 底妆产品 | Base Makeup | 打底遮瑕类产品 |
| makeup_eye | 眼妆产品 | Eye Makeup | 眼影、眼线、睫毛膏等 |
| makeup_lip | 唇妆产品 | Lip Makeup | 口红、唇釉、唇彩等 |
| makeup_cheek | 颊妆产品 | Cheek Makeup | 腮红、修容、高光等 |
| makeup_nail | 美甲产品 | Nail Makeup | 指甲油、甲油胶等 |
| makeup_brow | 眉部产品 | Eyebrow Makeup | 眉笔、眉粉、染眉膏等 |
| makeup_setting | 定妆产品 | Setting Makeup | 定妆喷雾、粉饼等 |

#### 1.2.1 底妆子类

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| base_foundation | 粉底液 | Foundation |
| base_cushion | 气垫 | Cushion |
| base_bbcream | BB霜 | BB Cream |
| base_cccream | CC霜 | CC Cream |
| base_concealer | 遮瑕膏 | Concealer |
| base_primer | 妆前乳 | Primer |
| base_primer_silicone | 硅基妆前乳 | Silicone Primer |
| base_primer_hydrating | 保湿妆前乳 | Hydrating Primer |
| base_primer_pore | 毛孔隐形膏 | Pore Primer |
| base_powder | 粉饼 | Powder |
| base_compact | 气垫粉饼 | Compact |
| base_tinted | 有色面霜 | Tinted Moisturizer |

#### 1.2.2 眼妆子类

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| eye_shadow_powder | 粉状眼影 | Powder Eyeshadow |
| eye_shadow_cream | 奶油眼影 | Cream Eyeshadow |
| eye_shadow_liquid | 液体眼影 | Liquid Eyeshadow |
| eye_shadow_palette | 眼影盘 | Eyeshadow Palette |
| eye_liner_pencil | 眼线笔 | Pencil Eyeliner |
| eye_liner_liquid | 液体眼线 | Liquid Eyeliner |
| eye_liner_gel | 凝胶眼线 | Gel Eyeliner |
| eye_mascara | 睫毛膏 | Mascara |
| eye_mascara_volumizing | 浓密睫毛膏 | Volumizing Mascara |
| eye_mascara_lengthening | 纤长睫毛膏 | Lengthening Mascara |
| eye_mascara_waterproof | 防水睫毛膏 | Waterproof Mascara |
| eye_eyelash_primer | 睫毛打底 | Lash Primer |
| eye_eyelash_ext | 假睫毛 | False Eyelashes |
| eye_eyebrow | 眉笔/眉粉 | Eyebrow Pencil/Powder |

#### 1.2.3 唇妆子类

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| lip_lipstick | 口红 | Lipstick |
| lip_gloss | 唇彩 | Lip Gloss |
| lip_stain | 唇釉 | Lip Stain |
| lip_balm | 润唇膏 | Lip Balm |
| lip_liner | 唇线笔 | Lip Liner |
| lip_tint | 染唇液 | Lip Tint |
| lip_oil | 唇油 | Lip Oil |
| lip_plumper | 丰唇蜜 | Lip Plumper |

#### 1.2.4 颊妆子类

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| cheek_blush_powder | 腮红粉 | Powder Blush |
| cheek_blush_cream | 奶油腮红 | Cream Blush |
| cheek_blush_liquid | 液体腮红 | Liquid Blush |
| cheek_bronzer | 修容 | Bronzer |
| cheek_highlighter | 高光 | Highlighter |
| cheek_contour | 轮廓盘 | Contour Kit |

### 1.3 护发产品 (Hair Care Products)

| 实体ID | 中文名称 | 英文名称 | 定义 |
|--------|----------|----------|------|
| hair_shampoo | 洗发水 | Shampoo | 清洁头发的产品 |
| hair_conditioner | 护发素 | Conditioner | 护理头发的产品 |
| hair_mask | 发膜 | Hair Mask | 深层护理的发膜 |
| hair_oil | 护发油 | Hair Oil | 滋养头发的油类产品 |
| hair_serum | 护发精华 | Hair Serum | 修护受损的精华产品 |
| hair_spray | 喷雾 | Hair Spray | 定型保湿喷雾 |
| hair_mousse | 慕斯 | Hair Mousse | 定型慕斯 |
| hair_gel | 发胶 | Hair Gel | 强力定型 |
| hair_wax | 发蜡 | Hair Wax | 塑形定型 |
| hair_pomade | 发膏 | Pomade | 光泽定型 |
| hair_cream | 发乳 | Hair Cream | 滋养造型 |
| hair_treatment | 护理产品 | Hair Treatment | 头发护理系列 |

#### 1.3.1 洗发水子类

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| shampoo_regular | 普通洗发水 | Regular Shampoo |
| shampoo_volumizing | 丰盈洗发水 | Volumizing Shampoo |
| shampoo_color_protect | 护色洗发水 | Color-Protecting Shampoo |
| shampoo_moisturizing | 保湿洗发水 | Moisturizing Shampoo |
| shampoo_anti_dandruff | 去屑洗发水 | Anti-Dandruff Shampoo |
| shampoo_clarifying | 深层清洁洗发水 | Clarifying Shampoo |
| shampoo_sulfate_free | 无硫酸盐洗发水 | Sulfate-Free Shampoo |
| shampoo_solid | 固体洗发水 | Shampoo Bar |

### 1.4 美甲产品 (Nail Products)

| 实体ID | 中文名称 | 英文名称 | 定义 |
|--------|----------|----------|------|
| nail_polish | 指甲油 | Nail Polish | 彩色指甲油 |
| nail_topcoat | 指甲面油 | Top Coat | 保护增亮面油 |
| nail_basecoat | 指甲底油 | Base Coat | 底层保护底油 |
| nail_gel | 甲油胶 | Gel Nail Polish | UV固化的凝胶指甲油 |
| nail_gel_builder | 建构胶 | Builder Gel | 塑形建构凝胶 |
| nail_acrylic | 丙烯酸甲 | Acrylic Powder | 延长甲用粉末 |
| nail_remover | 卸甲水 | Nail Polish Remover | 卸除指甲油的产品 |
| nail_file | 指甲锉 | Nail File | 修整指甲形状 |
| nail_clipper | 指甲剪 | Nail Clippers | 修剪指甲 |
| nail_buffer | 指甲抛光块 | Nail Buffer | 抛光指甲表面 |
| nail_care_oil | 指甲油 | Nail Oil | 护理指甲边缘 |

### 1.5 美容仪器 (Beauty Devices)

| 实体ID | 中文名称 | 英文名称 | 定义 |
|--------|----------|----------|------|
| device_cleanser | 洁面仪 | Cleansing Device | 电动洁面仪器 |
| device_microdermabrasion | 微晶磨皮仪 | Microdermabrasion Device | 物理去角质仪器 |
| device_led | LED美容仪 | LED Light Therapy Device | 光疗美容设备 |
| device_rf | 射频仪 | RF Device | 射频紧致仪器 |
| device_ultrasonic | 超声波仪 | Ultrasonic Device | 超声波导入仪器 |
| device_microcurrent | 微电流仪 | Microcurrent Device | 微电流提拉仪器 |
| device_dermaroller | 微针滚轮 | Dermaroller | 微针美容工具 |
| device_dermapen | 美塑枪 | Dermapen | 电动微针设备 |
| device_galvanic | 离子导入仪 | Galvanic Device | 离子导入导出仪器 |
| device_vacuum | 吸黑头仪 | Pore Vacuum | 真空吸黑头设备 |
| device_eyebrow | 电动修眉刀 | Electric Eyebrow Trimmer | 电动修眉工具 |
| device_hair_removal | 脱毛仪 | Hair Removal Device | 激光/光子脱毛仪器 |
| device_face_massager | 面部按摩仪 | Face Massager | 电动按摩仪器 |
| device_eye_massager | 眼部按摩仪 | Eye Massager | 眼部护理按摩仪 |
| device_hair_dryer | 吹风机 | Hair Dryer | 电吹风 |
| device_straightener | 直发器 | Hair Straightener | 拉直头发 |
| device_curler | 卷发器 | Curling Iron | 卷曲头发 |
| device_brush | 美容刷 | Beauty Brush | 电动清洁/按摩刷 |

---

## 2. 成分与原料 (Ingredients)

### 2.1 保湿成分 (Humectants)

| 实体ID | 中文名称 | 英文名称 | 功效 |
|--------|----------|----------|------|
| ing_hyaluronic_acid | 透明质酸/玻尿酸 | Hyaluronic Acid | 深层保湿、锁水 |
| ing_glycerin | 甘油 | Glycerin | 保湿、吸湿 |
| ing_butylene_glycol | 丁二醇 | Butylene Glycol | 保湿、溶剂 |
| ing_propanediol | 丙二醇 | Propanediol | 保湿、溶剂 |
| ing_sorbitol | 山梨糖醇 | Sorbitol | 保湿 |
| ing_urea | 尿素 | Urea | 保湿、软化角质 |
| ing_sodium_pca | PCA钠 | Sodium PCA | 天然保湿因子 |
| ing_ceramide | 神经酰胺 | Ceramide | 修复屏障、保湿 |
| ing_squalane | 角鲨烷 | Squalane | 保湿、滋养 |
| ing_shea_butter | 乳木果油 | Shea Butter | 滋养、保湿 |

### 2.2 抗氧化成分 (Antioxidants)

| 实体ID | 中文名称 | 英文名称 | 功效 |
|--------|----------|----------|------|
| ing_vitamin_c | 维生素C/抗坏血酸 | Vitamin C | 美白、抗氧化 |
| ing_vitamin_e | 维生素E/生育酚 | Vitamin E | 抗氧化、滋养 |
| ing_resveratrol | 白藜芦醇 | Resveratrol | 抗衰老、抗氧化 |
| ing_green_tea | 绿茶提取物 | Green Tea Extract | 抗氧化、抗炎 |
| ing_ferulic_acid | 阿魏酸 | Ferulic Acid | 抗氧化、增强功效 |
| ing_idebenone | 艾地苯 | Idebenone | 强效抗氧化 |
| ing_ubiquinone | 辅酶Q10 | Coenzyme Q10 | 抗氧化、能量 |
| ing_astaxanthin | 虾青素 | Astaxanthin | 超强抗氧化 |
| ing_betacarotene | β-胡萝卜素 | Beta-Carotene | 抗氧化、维A原 |

### 2.3 美白成分 (Whitening Agents)

| 实体ID | 中文名称 | 英文名称 | 功效 |
|--------|----------|----------|------|
| ing_arbutin | 熊果苷 | Arbutin | 美白、淡斑 |
| ing_kojic_acid | 曲酸 | Kojic Acid | 美白、抑制黑色素 |
| ing_licorice | 甘草提取物 | Licorice Extract | 美白、抗炎 |
| ing_niacinamide | 烟酰胺 | Niacinamide | 美白、控油、抗炎 |
| ing_tranexamic_acid | 传明酸 | Tranexamic Acid | 美白、淡斑 |
| ing_ellagic_acid | 鞣花酸 | Ellagic Acid | 美白、抗氧化 |
| ing_sodium_l_ascorbyl_phosphate | VC磷酸酯钠 | SAP | 稳定维C、美白 |
| ing_ascorbyl_glucoside | VC葡糖苷 | AA2G | 稳定维C、美白 |
| ing_ethyl_ascorbic_acid | 乙基维C | EAC | 稳定维C、美白 |

### 2.4 抗衰老成分 (Anti-Aging Ingredients)

| 实体ID | 中文名称 | 英文名称 | 功效 |
|--------|----------|----------|------|
| ing_retinol | 视黄醇/维A醇 | Retinol | 抗衰老、促进胶原 |
| ing_retinal | 视黄醛 | Retinal | 维A衍生物、强效 |
| ing_adapolene | 阿达帕林 | Adapalene | 维A衍生物、祛痘抗老 |
| ing_peptides | 多肽/胜肽 | Peptides | 抗衰老、紧致 |
| ing_collagen | 胶原蛋白 | Collagen | 保湿、紧致 |
| ing_adenosine | 腺苷 | Adenosine | 抗衰老、紧致 |
| ing_centella | 积雪草提取物 | Centella Asiatica | 修护、抗炎、抗老 |
| ing_bakuchiol | 补骨脂酚 | Bakuchiol | 植物维A、抗老 |
| ing_snail_mucin | 蜗牛粘液 | Snail Mucin | 修护、保湿、抗老 |
| ing_propolis | 蜂胶 | Propolis | 抗菌、抗炎、修护 |

### 2.5 祛痘成分 (Anti-Acne Ingredients)

| 实体ID | 中文名称 | 英文名称 | 功效 |
|--------|----------|----------|------|
| ing_salicylic_acid | 水杨酸 | Salicylic Acid | 祛痘、去角质 |
| ing_benzoyl_peroxide | 过氧化苯甲酰 | Benzoyl Peroxide | 杀菌、祛痘 |
| ing_sulfur | 硫磺 | Sulfur | 祛痘、控油 |
| ing_tea_tree | 茶树精油 | Tea Tree Oil | 抗菌、祛痘 |
| ing_niacinamide | 烟酰胺 | Niacinamide | 抗炎、控油 |
| ing_zinc | 锌 | Zinc | 控油、抗炎 |
| ing_azelaic_acid | 壬二酸 | Azelaic Acid | 祛痘、美白 |
| ing_rosemary | 迷迭香提取物 | Rosemary Extract | 抗菌、抗氧化 |

### 2.6 舒缓成分 (Soothing Ingredients)

| 实体ID | 中文名称 | 英文名称 | 功效 |
|--------|----------|----------|------|
| ing_aloe_vera | 芦荟 | Aloe Vera | 舒缓、修护 |
| ing_chamomile | 洋甘菊 | Chamomile | 舒缓、抗炎 |
| ing_centella | 积雪草 | Centella Asiatica | 修护、抗炎 |
| ing_cica | 雪积草 | Cica | 修护、舒缓 |
| ing_allantoin | 尿囊素 | Allantoin | 修护、舒缓 |
| ing_panthenol | 泛醇/维生素B5 | Panthenol | 保湿、修护 |
| ing_bisabolol | 红没药醇 | Bisabolol | 舒缓、抗炎 |
| ing_madecassoside | 积雪草苷 | Madecassoside | 修护、抗炎 |
| ing_asiaticoside | 积雪草酸 | Asiaticoside | 修护、促进胶原 |

### 2.7 去角质成分 (Exfoliating Ingredients)

| 实体ID | 中文名称 | 英文名称 | 功效 |
|--------|----------|----------|------|
| ing_aha | AHA/果酸 | Alpha Hydroxy Acid | 化学去角质 |
| ing_glycolic_acid | 甘醇酸 | Glycolic Acid | 分子量最小的AHA |
| ing_lactic_acid | 乳酸 | Lactic Acid | 温和AHA、保湿 |
| ing_mandelic_acid | 杏仁酸 | Mandelic Acid | 温和AHA、适合敏感肌 |
| ing_tartaric_acid | 酒石酸 | Tartaric Acid | AHA、去角质 |
| ing_bha | BHA/水杨酸 | Beta Hydroxy Acid | 脂溶性去角质 |
| ing_pha | 多羟基酸 | Polyhydroxy Acid | 温和第三代果酸 |
| ing_glucose | 葡萄糖酸内酯 | Gluconolactone | 温和PHA |
| ing_lactobionic_acid | 乳糖酸 | Lactobionic Acid | 超级温和PHA |
| ing_papain | 木瓜蛋白酶 | Papain | 酶去角质 |
| ing_bromelain | 菠萝蛋白酶 | Bromelain | 酶去角质 |

### 2.8 防晒成分 (Sunscreen Agents)

| 实体ID | 中文名称 | 英文名称 | 类型 |
|--------|----------|----------|------|
| ing_avobenzone | 阿伏苯宗 | Avobenzone | 化学防晒 |
| ing_homosalate | 胡莫柳酯 | Homosalate | 化学防晒 |
| ing_octinoxate | 桂皮酸盐 | Octinoxate | 化学防晒 |
| ing_octocrylene | 奥克立林 | Octocrylene | 化学防晒 |
| ing_tinosorb_s | 双-乙基己基苯酚 | Tinosorb S | 化学防晒 |
| ing_tinosorb_m | 天来施M | Tinosorb M | 化学防晒 |
| ing_uvinul_a_plus | 乙基己基 | Uvinul A Plus | 化学防晒 |
| ing_uvinul_n_539 | - | Uvinul N 539 | 化学防晒 |
| ing_zinc_oxide | 氧化锌 | Zinc Oxide | 物理防晒 |
| ing_titanium_dioxide | 二氧化钛 | Titanium Dioxide | 物理防晒 |

---

## 3. 肤质与发质类型 (Skin & Hair Types)

### 3.1 肤质类型 (Skin Types)

| 实体ID | 中文名称 | 英文名称 | 特征 |
|--------|----------|----------|------|
| skin_normal | 中性皮肤 | Normal Skin | 水油平衡、细腻毛孔 |
| skin_oily | 油性皮肤 | Oily Skin | 毛孔粗大、易长痘 |
| skin_dry | 干性皮肤 | Dry Skin | 缺水、容易紧绷 |
| skin_combination | 混合性皮肤 | Combination Skin | T区油U区干 |
| skin_sensitive | 敏感性皮肤 | Sensitive Skin | 易红、易过敏 |
| skin_acne | 痘痘肌 | Acne-Prone Skin | 易长痘痘 |
| skin_aging | 熟龄肌肤 | Aging Skin | 有细纹、松弛 |
| skin_dehydrated | 缺水肌肤 | Dehydrated Skin | 外油内干、水油失衡 |

### 3.2 肤色类型 (Skin Tones)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| tone_fair | 白皙肤色 | Fair |
| tone_light | 浅肤色 | Light |
| tone_medium | 中等肤色 | Medium |
| tone_tan | 古铜肤色 | Tan |
| tone_dark | 深肤色 | Dark |
| tone_deep | 深黑肤色 | Deep |

### 3.3 发质类型 (Hair Types)

#### 3.3.1 按头发质地

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| hair_straight | 直发 | Straight Hair |
| hair_wavy | 波浪发 | Wavy Hair |
| hair_curly | 卷发 | Curly Hair |
| hair_coily | 紧密卷发 | Coily Hair |

#### 3.3.2 按发质状况

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| hair_normal | 正常发质 | Normal Hair |
| hair_oily | 油性发质 | Oily Hair |
| hair_dry | 干性发质 | Dry Hair |
| hair_colored | 染烫发质 | Color-Treated Hair |
| hair_fine | 细软发质 | Fine Hair |
| hair_thick | 粗硬发质 | Thick Hair |
| hair_damaged | 受损发质 | Damaged Hair |
| hair_thinning | 稀疏发质 | Thinning Hair |

### 3.4 指甲类型 (Nail Types)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| nail_normal | 正常指甲 | Normal Nails |
| nail_brittle | 脆弱指甲 | Brittle Nails |
| nail_layer | 分层指甲 | Splitting Nails |
| nail_ridged | 竖纹指甲 | Ridged Nails |
| nail_weak | 薄弱指甲 | Weak Nails |

---

## 4. 美容服务 (Beauty Services)

### 4.1 面部护理服务 (Facial Services)

| 实体ID | 中文名称 | 英文名称 | 描述 |
|--------|----------|----------|------|
| svc_facial_basic | 基础面部护理 | Basic Facial | 清洁、补水、保湿 |
| svc_facial_deep | 深层清洁护理 | Deep Cleansing Facial | 毛孔清洁、去黑头 |
| svc_facial_hydrating | 补水护理 | Hydrating Facial | 深层补水、锁水 |
| svc_facial_anti_aging | 抗衰老护理 | Anti-Aging Facial | 提拉、紧致、抗皱 |
| svc_facial_whitening | 美白护理 | Whitening Facial | 淡斑、美白、提亮 |
| svc_facial_acne | 祛痘护理 | Acne Treatment Facial | 控油、祛痘、消炎 |
| svc_facial_sensitive | 敏感护理 | Sensitive Skin Facial | 舒缓、修护屏障 |
| svc_facial_led | LED光护理 | LED Light Therapy | 红光/蓝光/黄光护理 |
| svc_facial_microderm | 微晶磨皮 | Microdermabrasion | 物理去角质 |
| svc_facial_chemical_peel | 果酸换肤 | Chemical Peel | 化学去角质 |
| svc_facial_mesotherapy | 美塑疗法 | Mesotherapy | 中胚层疗法 |
| svc_facial_gold_needle | 黄金微针 | RF Microneedling | 射频微针 |

### 4.2 身体护理服务 (Body Care Services)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| svc_body_scrub | 身体磨砂 | Body Scrub |
| svc_body_wrap | 身体裹敷 | Body Wrap |
| svc_body_slimming | 纤体护理 | Slimming Treatment |
| svc_body_detox | 排毒护理 | Detox Treatment |
| svc_body_cellulite | 瘦身护理 | Cellulite Treatment |
| svc_body_breast_care | 胸部护理 | Breast Care |
| svc_body_hand_foot | 手足护理 | Hand & Foot Care |

### 4.3 美甲服务 (Nail Services)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| svc_manicure | 修甲 | Manicure |
| svc_pedicure | 足部护理 | Pedicure |
| svc_gel_manicure | 光疗甲 | Gel Manicure |
| svc_acrylic_nail | 水晶甲 | Acrylic Nails |
| svc_nail_art | 美甲艺术 | Nail Art |
| svc_nail_extension | 指甲延长 | Nail Extension |
| svc_nail_repair | 指甲修补 | Nail Repair |

### 4.4 美发服务 (Hair Services)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| svc_haircut | 美发剪裁 | Haircut |
| svc_blow_dry | 吹风造型 | Blow Dry |
| svc_hair_color | 染发 | Hair Coloring |
| svc_highlight | 挑染 | Highlights |
| svc_balayage | 渐变染 | Balayage |
| svc_perm | 烫发 | Perm |
| svc_straightening | 直发处理 | Hair Straightening |
| svc_hair_treatment | 头发护理 | Hair Treatment |
| svc_hair_spa | 头发水疗 | Hair Spa |
| svc_keratin | 角蛋白护理 | Keratin Treatment |

### 4.5 纹绣服务 (Permanent Makeup Services)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| svc_eyebrow_embroidery | 纹眉 | Eyebrow Embroidery |
| svc_eyeliner_tattoo | 纹眼线 | Eyeliner Tattoo |
| svc_lip_tattoo | 纹唇 | Lip Tattoo |
| svc_scalp_tattoo | 纹发际线 | Scalp Micropigmentation |
| svc_areola_tattoo | 乳晕纹绣 | Areola Tattoo |

### 4.6 睫毛服务 (Eyelash Services)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| svc_lash_lift | 睫毛翘睫 | Lash Lift |
| svc_lash_extension | 睫毛延长 | Lash Extension |
| svc_lash_perm | 睫毛烫 | Lash Perm |
| svc_lash_tinting | 睫毛染色 | Lash Tint |

---

## 5. 美容手法与技术 (Techniques & Methods)

### 5.1 按摩手法 (Massage Techniques)

| 实体ID | 中文名称 | 英文名称 | 描述 |
|--------|----------|----------|------|
| tech_lymphatic | 淋巴按摩 | Lymphatic Massage | 促进淋巴循环排水肿 |
| tech_acupressure | 穴位按压 | Acupressure | 中医穴位按摩 |
| tech_shiatsu | 指压按摩 | Shiatsu | 日式指压疗法 |
| tech_guasha | 刮痧 | Gua Sha | 中医刮痧疗法 |
| tech_jade_roller | 玉石滚轮 | Jade Rolling | 面部按摩工具 |
| tech_gua_sha_tool | 刮痧板 | Gua Sha Tool | 刮痧按摩工具 |
| tech_face_yoga | 面部瑜伽 | Face Yoga | 面部肌肉锻炼 |
| tech_cupping | 拔罐 | Cupping | 身体拔罐疗法 |

### 5.2 导入技术 (Delivery Technologies)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| tech_iontophoresis | 离子导入 | Iontophoresis |
| tech_sonophoresis | 超声波导入 | Sonophoresis |
| tech_electroporation | 电穿孔 | Electroporation |
| tech_microchannel | 微通道导入 | Microchannel Delivery |
| tech_pressure_injection | 压力注射 | Pressure Injection |
| tech_cryotherapy | 冷冻疗法 | Cryotherapy |
| tech_thermal_therapy | 热疗 | Thermal Therapy |

### 5.3 护肤步骤 (Skincare Routine Steps)

| 实体ID | 中文名称 | 英文名称 | 顺序 |
|--------|----------|----------|------|
| step_double_cleanse | 双重清洁 | Double Cleanse | 1 |
| step_exfoliate | 去角质 | Exfoliation | 2 |
| step_toner | 使用爽肤水 | Toner | 3 |
| step_essence | 使用精华液 | Essence | 4 |
| step_serum | 使用精华素 | Serum | 5 |
| step_eye_cream | 使用眼霜 | Eye Cream | 6 |
| step_moisturizer | 使用面霜 | Moisturizer | 7 |
| step_eye_cream_evening | 晚间眼霜 | Evening Eye Cream | 8 |
| step_face_oil | 使用护肤油 | Face Oil | 9 |
| step_sunscreen | 使用防晒 | Sunscreen | 10 |
| step_mask | 使用面膜 | Mask | 偶尔 |
| step_lip_balm | 使用唇膏 | Lip Balm | 随时 |

---

## 6. 品牌与制造商 (Brands & Manufacturers)

### 6.1 高端美妆品牌 (Luxury Brands)

| 实体ID | 中文名称 | 英文名称 | 产地 |
|--------|----------|----------|------|
| brand_la_mer | 海蓝之谜 | La Mer | 美国 |
| brand_dior | 迪奥 | Dior | 法国 |
| brand_chanel | 香奈儿 | Chanel | 法国 |
| brand_guerlain | 娇兰 | Guerlain | 法国 |
| brand_estee_lauder | 雅诗兰黛 | Estée Lauder | 美国 |
| brand_lancome | 兰蔻 | Lancôme | 法国 |
| brand_skii | SK-II | SK-II | 日本 |
| brand_la_praroque | 莱珀妮 | La Prairie | 瑞士 |
| brand_clinique | 倩碧 | Clinique | 美国 |
| brand_clarins | 娇韵诗 | Clarins | 法国 |

### 6.2 药妆品牌 (Cosmeceutical Brands)

| 实体ID | 中文名称 | 英文名称 | 产地 |
|--------|----------|----------|------|
| brand_vichy | 薇姿 | Vichy | 法国 |
| brand_laroche | 理肤泉 | La Roche-Posay | 法国 |
| brand_avene | 雅漾 | Avène | 法国 |
| brand_cerave | 适乐肤 | CeraVe | 美国 |
| brand_the_ordinary | The Ordinary | The Ordinary | 加拿大 |
| brand_paulas_choice | 宝拉珍选 | Paula's Choice | 美国 |
| brand_drunk_elephant | 醉象 | Drunk Elephant | 美国 |
| brand_cosrx | Cosrx | Cosrx | 韩国 |
| brand_some_by_mi |所未米 | Some By Mi | 韩国 |
| brand_centricel | 芯丝翠 | NeoStrata | 美国 |

### 6.3 日韩美妆品牌 (Asian Beauty Brands)

| 实体ID | 中文名称 | 英文名称 | 产地 |
|--------|----------|----------|------|
| brand_shiseido | 资生堂 | Shiseido | 日本 |
| brand_kanebo | 嘉娜宝 | Kanebo | 日本 |
| brand_kose | 高丝 | Kose | 日本 |
| brand_innisfree | 悦诗风吟 | Innisfree | 韩国 |
| brand_etude_house | 伊蒂之屋 | Etude House | 韩国 |
| brandLaneige | 兰芝 | Laneige | 韩国 |
| brandSulwhasoo | 雪花秀 | Sulwhasoo | 韩国 |
| brand_hera | 赫妍 | Hera | 韩国 |
| brand_oomacha | 奥蜜思 | Obagi | 日本 |
| brand_hada_labo | 肌研 | Hada Labo | 日本 |

### 6.4 开架品牌 (Mass Market Brands)

| 实体ID | 中文名称 | 英文名称 | 产地 |
|--------|----------|----------|------|
| brand_maybelline | 美宝莲 | Maybelline | 美国 |
| brand_loreal | 巴黎欧莱雅 | L'Oréal | 法国 |
| brand_garnier | 卡尼尔 | Garnier | 法国 |
| brand_nivea | 妮维雅 | Nivea | 德国 |
| brand_cetaphil | 丝塔芙 | Cetaphil | 法国 |
| brand_olay | 玉兰油 | Olay | 美国 |
| brand_simple | Simple | Simple | 英国 |
| brand_cotz | 确美同 | Coppertone | 美国 |

### 6.5 纯净美妆品牌 (Clean Beauty Brands)

| 实体ID | 中文名称 | 英文名称 | 产地 |
|--------|----------|----------|------|
| brand_rms_beauty | RMS Beauty | RMS Beauty | 美国 |
| brand_kjaer_weis | 凯尔特玫瑰 | Kjaer Weis | 丹麦 |
| brand_il_makiage | Il Makiage | Il Makiage | 美国 |
| brand_glossier | 歌露白 | Glossier | 美国 |
| brand_fenty | 蕾哈娜美妆 | Fenty Beauty | 美国 |
| brand_rare_beauty | 贝妃玲 | Rare Beauty | 美国 |
| brand_elta_md | Elta MD | Elta MD | 美国 |

---

## 7. 美容工具与配件 (Tools & Accessories)

### 7.1 化妆工具 (Makeup Tools)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| tool_brush_set | 化妆刷套装 | Brush Set |
| tool_brush_foundation | 粉底刷 | Foundation Brush |
| tool_brush_eyeshadow | 眼影刷 | Eyeshadow Brush |
| tool_brush_blush | 腮红刷 | Blush Brush |
| tool_brush_contour | 修容刷 | Contour Brush |
| tool_brush_highlighter | 高光刷 | Highlighter Brush |
| tool_brush_lip | 口红刷 | Lip Brush |
| tool_sponge | 美妆蛋 | Beauty Sponge |
| tool_sponge_latex | 乳胶美妆蛋 | Latex Sponge |
| tool_silicone_sponge | 硅胶粉扑 | Silicone Sponge |
| tool_puff | 粉扑 | Powder Puff |
| tool_tweezers | 镊子 | Tweezers |
| tool_eyelash_curler | 睫毛夹 | Eyelash Curler |
| tool_sharpener | 铅笔刀 | Pencil Sharpener |
| tool_mirror | 化妆镜 | Makeup Mirror |
| tool_organizer | 化妆包 | Makeup Bag |

### 7.2 护肤工具 (Skincare Tools)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| tool_jade_roller | 玉石滚轮 | Jade Roller |
| tool_guasha | 刮痧板 | Gua Sha Board |
| tool_dermaroller | 微针滚轮 | Dermaroller |
| tool_face_mask_brush | 面膜刷 | Mask Brush |
| tool_extractor | 粉刺针 | Extractor |
| tool_lipliner_brush | 唇线刷 | Lip Brush |
| tool_spoolie | 螺旋眉刷 | Spoolie Brush |
| tool_eyebrow_scissors | 眉剪 | Eyebrow Scissors |
| tool_tissue | 化妆棉 | Cotton Pad |
| tool_cotton | 棉片 | Cotton |
| tool_earbud | 棉签 | Cotton Swab |

---

## 8. 美容问题与症状 (Beauty Concerns)

### 8.1 皮肤问题 (Skin Concerns)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| concern_acne | 痘痘 | Acne |
| concern_blackhead | 黑头 | Blackheads |
| concern_whitehead | 白头 | Whiteheads |
| concern_pimple | 粉刺 | Pimples |
| concern_cystic_acne | 囊肿型痘痘 | Cystic Acne |
| concern_dark_spots | 色斑 | Dark Spots |
| concern_hyperpigmentation | 色素沉着 | Hyperpigmentation |
| concern_age_spots | 老年斑 | Age Spots |
| concern_freckles | 雀斑 | Freckles |
| concern_post_inflammatory | 炎症后色素沉着 | PIH |
| concern_wrinkles | 皱纹 | Wrinkles |
| concern_fine_lines | 细纹 | Fine Lines |
| concern_sagging | 松弛 | Sagging |
| concern_dullness | 暗沉 | Dullness |
| concern_pores | 毛孔粗大 | Enlarged Pores |
| concern_oiliness | 油光 | Oiliness |
| concern_dryness | 干燥 | Dryness |
| concern_dehydration | 缺水 | Dehydration |
| concern_redness | 泛红 | Redness |
| concern_rosacea | 玫瑰痤疮 | Rosacea |
| concern_sensitivity | 敏感 | Sensitivity |
| concern_allergy | 过敏 | Allergic Reaction |
| concern_eczema | 湿疹 | Eczema |
| concern_psoriasis | 银屑病 | Psoriasis |
| concern_scar | 疤痕 | Scarring |
| concern_stretch_marks | 妊娠纹 | Stretch Marks |
| concern_cellulite | 橘皮组织 | Cellulite |
| concern_dark_circles | 黑眼圈 | Dark Circles |
| concern_puffiness | 浮肿 | Puffiness |
| concern_bags | 眼袋 | Under-eye Bags |
| concern_tired_eyes | 疲劳眼 | Tired Eyes |
| concern_eye_wrinkles | 眼部皱纹 | Eye Wrinkles |

### 8.2 头发问题 (Hair Concerns)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| hair_concern_dandruff | 头皮屑 | Dandruff |
| hair_concern_thinning | 脱发 | Hair Thinning |
| hair_concern_breakage | 断发 | Hair Breakage |
| hair_concern_split_ends | 分叉 | Split Ends |
| hair_concern_frizz | 毛躁 | Frizz |
| hair_concern_damage | 受损 | Damage |
| hair_concern_dryness | 干燥 | Dryness |
| hair_concern_oily_scalp | 油头 | Oily Scalp |
| hair_concern_color_fade | 褪色 | Color Fading |
| hair_concern_flat_volume | 扁塌 | Lack of Volume |
| hair_concern_curl_pattern | 卷度问题 | Curl Pattern Issues |
| hair_concern_lice | 头虱 | Lice Infestation |
| hair_concern_scalp_acne | 头皮痘 | Scalp Acne |
| hair_concern_premature_graying | 白发 | Premature Graying |

---

## 9. 美容职业与角色 (Beauty Professionals)

### 9.1 面部美容 (Facial)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| prof_esthetician | 美容师 | Esthetician |
| prof_facial_specialist | 面部护理专家 | Facial Specialist |
| prof_skincare_therapist | 护肤理疗师 | Skincare Therapist |
| prof_skin_consultant | 皮肤咨询师 | Skin Consultant |

### 9.2 彩妆 (Makeup)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| prof_makeup_artist | 化妆师 | Makeup Artist |
| prof_celebrity_mua | 明星化妆师 | Celebrity Makeup Artist |
| prof_bridal_mua | 新娘化妆师 | Bridal Makeup Artist |

### 9.3 美发 (Hair)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| prof_hair_stylist | 发型师 | Hair Stylist |
| prof_hair_colorist | 染发师 | Hair Colorist |
| prof_hair_cutter | 理发师 | Hair Cutter |
| prof_barber | 男士理发师 | Barber |

### 9.4 美甲 (Nails)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| prof_nail_technician | 美甲师 | Nail Technician |
| prof_nail_artist | 美甲艺术家 | Nail Artist |
| prof_manicurist | 修甲师 | Manicurist |

### 9.5 身体护理 (Body)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| prof_massage_therapist | 按摩理疗师 | Massage Therapist |
| prof_body_wrap_specialist | 身体裹敷专家 | Body Wrap Specialist |
| prof_slimming_consultant | 纤体顾问 | Slimming Consultant |

### 9.6 医疗美容 (Medical Aesthetics)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| prof_plastic_surgeon | 整形外科医生 | Plastic Surgeon |
| prof_dermatologist | 皮肤科医生 | Dermatologist |
| prof_cosmetic_dentist | 美容牙医 | Cosmetic Dentist |
| prof_injectable_specialist | 注射专家 | Injectable Specialist |
| prof_laser_technician | 激光技师 | Laser Technician |

---

## 10. 颜色与色号 (Colors & Shades)

### 10.1 肤色色调 (Skin Undertones)

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| undertone_warm | 暖调 | Warm Undertone |
| undertone_cool | 冷调 | Cool Undertone |
| undertone_neutral | 中性调 | Neutral Undertone |
| undertone_olive | 橄榄调 | Olive Undertone |

### 10.2 常见产品色号分类

| 实体ID | 中文名称 | 英文名称 | 适用肤色 |
|--------|----------|----------|----------|
| shade_fair_light | 浅肤色系 | Fair/Light | Fair, Light |
| shade_medium | 中等肤色系 | Medium | Medium, Tan |
| shade_medium_deep | 中深肤色系 | Medium Deep | Deep |
| shade_deep | 深肤色系 | Deep | Deep, Dark |

---

## 11. 美容趋势与风格 (Beauty Trends & Styles)

### 11.1 化妆风格

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| style_glass_skin | 玻璃肌 | Glass Skin |
| style_gradient_lips | 咬唇妆 | Gradient Lips |
| style_ponytail | 马尾造型 | Ponytail |
| style_bubble_hair | 泡泡辫 | Bubble Pigtails |
| style_eyebrow | 眉形 | Eyebrow Shape |
| style_no_makeup | 伪素颜 | No-Makeup Look |
| style_smoky_eye | 烟熏妆 | Smoky Eye |
| style_cat_eye | 猫眼妆 | Cat Eye |
| style_contour | 修容风格 | Contouring |
| style_baking | 烘焙法 | Baking |

### 11.2 护肤趋势

| 实体ID | 中文名称 | 英文名称 |
|--------|----------|----------|
| trend_k_beauty | 韩式护肤 | K-Beauty |
| trend_j_beauty | 日式护肤 | J-Beauty |
| trend_clean_beauty | 纯净美妆 | Clean Beauty |
| trend_sustainable | 可持续美妆 | Sustainable Beauty |
| trend_vegan | 纯素美妆 | Vegan Beauty |
| trend_blue_light | 蓝光防护 | Blue Light Protection |
| trend_retinol | 视黄醇流行 | Retinol Trend |
| trend_skin_barrier | 屏障修护 | Skin Barrier Care |

---

## 12. 相关关系定义

### 12.1 产品-成分关系

| 关系类型 | 描述 | 示例 |
|----------|------|------|
| contains | 包含 | 某精华液 contains 维生素C |
| active_ingredient | 活性成分 | 某眼霜 active_ingredient 咖啡因 |
| suitable_for_skin_type | 适合肤质 | 某保湿霜 suitable_for_skin_type 干性皮肤 |
| targets_concern | 针对问题 | 某祛痘凝胶 targets_concern 痘痘 |

### 12.2 服务-工具关系

| 关系类型 | 描述 | 示例 |
|----------|------|------|
| uses_tool | 使用工具 | 面部护理 uses_tool 洁面仪 |
| requires_equipment | 需要设备 | LED光疗 requires_equipment LED美容仪 |

### 12.3 技术-效果关系

| 关系类型 | 描述 | 示例 |
|----------|------|------|
| achieves | 达到效果 | 淋巴按摩 achieves 排水肿 |
| suitable_for | 适合人群 | 果酸换肤 suitable_for 油性皮肤 |

### 12.4 品牌-产品关系

| 关系类型 | 描述 | 示例 |
|----------|------|------|
| manufactures | 生产 | 品牌X manufactures 精华液 |
| product_line | 产品系列 | 品牌Y product_line 抗衰老系列 |

---

## 13. 使用场景

### 13.1 推荐系统

- **肤质匹配**：根据用户肤质推荐合适的产品
- **成分筛选**：基于用户对成分的偏好或过敏史筛选产品
- **问题导向**：针对特定皮肤问题推荐解决方案
- **预算适配**：根据价格区间推荐合适品牌

### 13.2 知识图谱

- **产品知识**：建立产品、成分、功效之间的关联
- **问答系统**：回答用户关于美容产品、服务、技术的问题
- **对比分析**：提供不同产品之间的对比维度

### 13.3 智能顾问

- **护肤方案**：根据肤质、季节、年龄提供护肤步骤建议
- **产品搭配**：避免成分冲突，推荐有效搭配
- **进度追踪**：记录使用效果，提供持续建议

---

## 14. 参考标准

- **国际化妆品术语**：INCI (International Nomenclature of Cosmetic Ingredients)
- **皮肤科学分类**：基于皮肤病理学标准
- **行业规范**：符合各国化妆品监管要求
- **功效宣称**：遵循科学验证标准

---

## 版本记录

- v1.0 (2025-03-16): 初始版本，包含护肤、彩妆、护发、美甲、仪器、成分、肤质、服务、技术、品牌、工具、问题、职业、颜色、趋势等16个主要类别，约300+个实体

---

*本本体遵循开放共享原则，可用于学术研究、商业应用和教育培训。使用时请注明出处。*