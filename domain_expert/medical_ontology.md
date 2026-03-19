# 医疗健康领域本体 (Medical Domain Ontology)

**版本**: 1.0  
**创建日期**: 2026-03-16  
**领域**: 医疗健康  
**描述**: 定义医疗健康领域的核心概念、实体、关系及业务规则

---

## 1. 医疗核心概念 (Core Medical Concepts)

### 1.1 患者 (Patient)

#### 1.1.1 患者实体定义

| 属性 | 类型 | 描述 | 必填 |
|------|------|------|------|
| patient_id | String | 患者唯一标识符 | 是 |
| name | String | 患者姓名 | 是 |
| gender | Enum | 性别：male/female/other | 是 |
| date_of_birth | DateTime | 出生日期 | 是 |
| id_card | String | 身份证号 | 是 |
| phone | String | 联系电话 | 否 |
| address | String | 居住地址 | 否 |
| emergency_contact | Object | 紧急联系人信息 | 否 |
| blood_type | Enum | 血型：A/B/AB/O/Rh± | 否 |
| allergies | Array | 过敏史列表 | 否 |
| medical_history | Array | 既往病史 | 否 |

#### 1.1.2 患者关系

```
Patient --(has)--> MedicalRecord
Patient --(owns)--> Insurance
Patient --(registers_at)--> Hospital
Patient --(receives)--> Prescription
```

### 1.2 医生 (Doctor/Medical Staff)

#### 1.2.1 医生实体定义

| 属性 | 类型 | 描述 | 必填 |
|------|------|------|------|
| doctor_id | String | 医生唯一标识符 | 是 |
| name | String | 医生姓名 | 是 |
| title | Enum | 职称：chief_physician/associate_chief/attending/resident | 是 |
| department | String | 所属科室 | 是 |
| license_number | String | 执业医师证号 | 是 |
| specialties | Array | 专业领域 | 是 |
| phone | String | 联系电话 | 否 |
| email | String | 电子邮箱 | 否 |
| schedule | Object | 出诊时间表 | 否 |

#### 1.2.2 医生关系

```
Doctor --(belongs_to)--> Department
Doctor --(works_at)--> Hospital
Doctor --(creates)--> MedicalRecord
Doctor --(issues)--> Prescription
Doctor --(performs)--> Procedure
```

### 1.3 药品 (Medication)

#### 1.3.1 药品实体定义

| 属性 | 类型 | 描述 | 必填 |
|------|------|------|------|
| drug_id | String | 药品唯一标识符 | 是 |
| drug_name | String | 药品名称 | 是 |
| generic_name | String | 通用名 | 是 |
| brand_names | Array | 商品名列表 | 否 |
| drug_type | Enum | 药品类型：prescription/otc/biological | 是 |
| dosage_form | Enum | 剂型：tablet/capsule/injection/syrup/patch | 是 |
| specification | String | 规格（如：10mg/片） | 是 |
| manufacturer | String | 生产企业 | 是 |
| approval_number | String | 批准文号 | 是 |
| indications | Array | 适应症 | 是 |
| contraindications | Array | 禁忌症 | 是 |
| dosage | Object | 用法用量 | 是 |
| price | Decimal | 零售价格 | 否 |
| inventory | Integer | 库存数量 | 否 |

#### 1.3.2 药品关系

```
Drug --(belongs_to)--> DrugCategory
Drug --(interacts_with)--> Drug
Drug --(has)--> SideEffect
Drug --(used_in)--> Prescription
```

### 1.4 病历 (Medical Record)

#### 1.4.1 病历实体定义

| 属性 | 类型 | 描述 | 必填 |
|------|------|------|------|
| record_id | String | 病历唯一标识符 | 是 |
| patient_id | String | 患者ID | 是 |
| doctor_id | String | 主治医生ID | 是 |
| visit_date | DateTime | 就诊日期 | 是 |
| visit_type | Enum | 就诊类型：outpatient/emergency/inpatient | 是 |
| chief_complaint | String | 主诉 | 是 |
| history_of_present_illness | String | 现病史 | 否 |
| physical_examination | Object | 体格检查 | 否 |
| diagnosis | Array | 诊断结果 | 是 |
| treatment_plan | Object | 治疗方案 | 否 |
| prescriptions | Array | 处方列表 | 否 |
| lab_results | Array | 检验结果 | 否 |
| imaging_results | Array | 影像学结果 | 否 |
| follow_up | String | 随访计划 | 否 |
| notes | String | 备注 | 否 |

#### 1.4.2 病历关系

```
MedicalRecord --(belongs_to)--> Patient
MedicalRecord --(created_by)--> Doctor
MedicalRecord --(contains)--> Diagnosis
MedicalRecord --(contains)--> Prescription
MedicalRecord --(references)--> LabResult
```

---

## 2. 诊疗规则 (Diagnostic and Treatment Rules)

### 2.1 诊断规则 (Diagnostic Rules)

#### 2.1.1 诊断流程

```
Rule: DR-001 诊断必须基于证据
  IF: 医生进行诊断
  THEN: 
    - 必须有明确的主诉 (chief_complaint)
    - 必须有体格检查或辅助检查结果
    - 诊断结果必须记录在病历中
    - 复杂病例需进行会诊

Rule: DR-002 诊断分类规则
  IF: 医生给出诊断
  THEN:
    - 主诊断 (primary_diagnosis): 当前最主要疾病
    - 次诊断 (secondary_diagnosis): 其他相关疾病
    - 待诊 (pending_diagnosis): 需进一步检查确认
    - 疑似诊断 (suspected_diagnosis): 临床考虑但未确诊
```

#### 2.1.2 诊断编码

| 编码体系 | 说明 | 使用场景 |
|----------|------|----------|
| ICD-10 | 国际疾病分类第10版 | 疾病诊断编码 |
| ICD-9-CM-3 | 手术操作分类 | 手术/操作编码 |
| SNOMED-CT | 系统化医学术语集 | 临床术语标准化 |

### 2.2 治疗规则 (Treatment Rules)

#### 2.2.1 治疗方案制定

```
Rule: TR-001 治疗方案必须遵循循证医学
  IF: 医生制定治疗方案
  THEN:
    - 首选推荐级别高的治疗方案
    - 考虑患者个体差异（年龄、体重、肾功能等）
    - 评估治疗获益与风险
    - 与患者沟通并取得知情同意

Rule: TR-002 治疗方案调整
  IF: 患者疗效不佳或出现不良反应
  THEN:
    - 及时评估当前治疗效果
    - 根据检查结果调整治疗方案
    - 必要时请上级医师会诊
    - 记录调整原因和方案变更
```

#### 2.2.2 治疗类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 药物治疗 | 使用药品进行治疗 | 抗生素、降压药 |
| 手术治疗 | 手术操作治疗 | 外科手术、微创手术 |
| 物理治疗 | 物理因子治疗 | 理疗、康复训练 |
| 心理治疗 | 心理干预 | 心理咨询、认知行为疗法 |
| 中医治疗 | 传统中医治疗 | 针灸、推拿、中药 |

### 2.3 会诊规则 (Consultation Rules)

```
Rule: CR-001 会诊触发条件
  IF: 满足以下任一条件
    - 病情复杂超出本科室范围
    - 诊断不明确
    - 治疗效果不佳
    - 患者或家属要求
  THEN:
    - 必须发起会诊
    - 会诊记录必须完整
    - 会诊意见必须执行或说明理由
```

---

## 3. 药品管理规则 (Medication Management Rules)

### 3.1 处方规则 (Prescription Rules)

#### 3.1.1 处方开具

```
Rule: PR-001 处方合法性
  IF: 医生开具处方
  THEN:
    - 医生必须具有执业资格
    - 处方必须包含：患者信息、药品信息、剂量、用法、日期、签名
    - 处方权限与医生职称挂钩
    - 特殊药品需单独授权

Rule: PR-002 处方审核
  IF: 处方创建后
  THEN:
    - 必须经过药师审核
    - 审核内容：适应症、剂量、用法、禁忌、相互作用
    - 审核通过后才能发药
    - 不合格处方必须退回修改

Rule: PR-003 特殊药品处方
  IF: 开具特殊管理药品
  THEN:
    - 麻醉药品：需专用病历，限量供应
    - 第一类精神药品：主任医师以上权限
    - 毒性药品：严格适应症控制
    - 放射性药品：需放射执业资质
```

#### 3.1.2 处方有效期

| 处方类型 | 有效期 | 续方规定 |
|----------|--------|----------|
| 普通处方 | 7天 | 可续方1次 |
| 慢性病处方 | 30天 | 可续方2-3次 |
| 麻醉药品 | 3天 | 不得续方 |
| 第一类精神药品 | 3天 | 不得续方 |

### 3.2 药品调配规则 (Dispensing Rules)

```
Rule: DR-001 调配审核
  IF: 药师调配药品
  THEN:
    - 必须核对处方与药品一致性
    - 检查药品有效期
    - 检查药品包装完整性
    - 特殊药品需双人核对

Rule: DR-002 发药核对
  IF: 发药给患者
  THEN:
    - 必须核对患者身份
    - 必须交代用法用量
    - 必须告知注意事项
    - 必须记录发药信息
```

### 3.3 药品库存管理规则

```
Rule: IR-001 库存预警
  IF: 药品库存量低于阈值
  THEN:
    - 系统自动生成补货提醒
    - 低于安全库存时限制发放
    - 急救药品必须保证充足

Rule: IR-002 药品有效期管理
  IF: 药品入库
  THEN:
    - 记录生产日期和有效期
    - 按先进先出原则发放
    - 过期药品必须及时下架
    - 定期进行库存盘点
```

### 3.4 药品相互作用规则

```
Rule: DR-001 相互作用检测
  IF: 处方包含多种药品
  THEN:
    - 必须进行药物相互作用筛查
    - 严重相互作用必须拦截
    - 中度相互作用需提示医生
    - 记录所有相互作用信息

Rule: DR-002 禁忌症检测
  IF: 患者有相关禁忌症记录
  THEN:
    - 处方与禁忌症冲突时必须拦截
    - 必须提示具体禁忌原因
    - 特殊情况下需患者签署知情同意
```

### 3.5 药品不良反应监测

```
Rule: AR-001 不良反应报告
  IF: 发现药品不良反应
  THEN:
    - 及时记录不良反应信息
    - 严重不良反应需立即上报
    - 填写药品不良反应报告表
    - 评估因果关系并处理

Rule: AR-002 药物警戒
  IF: 收到药品安全警告
  THEN:
    - 及时通知相关科室
    - 评估对患者影响
    - 必要时调整用药
    - 更新患者用药警示
```

---

## 4. 实体关系总图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Patient   │       │   Doctor    │       │   Hospital  │
└──────┬──────┘       └──────┬──────┘       └──────┬──────┘
       │                     │                     │
       │ has                 │ works_at            │
       ▼                     ▼                     │
┌─────────────┐       ┌─────────────┐             │
│MedicalRecord│◄──────│  creates    │             │
└──────┬──────┘       └─────────────┘             │
       │                                             │
       │ contains                                    │
       ▼                                             │
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Diagnosis  │       │ Prescription│       │    Drug     │
└─────────────┘       └──────┬──────┘       └──────┬──────┘
                             │                     │
                             │ contains            │ belongs_to
                             ▼                     ▼
                      ┌─────────────┐       ┌─────────────┐
                      │  DrugItem   │       │DrugCategory │
                      └─────────────┘       └─────────────┘
```

---

## 5. 业务规则汇总

### 5.1 核心业务规则

| 规则ID | 规则名称 | 优先级 |
|--------|----------|--------|
| BR-001 | 患者信息必须实名制 | 高 |
| BR-002 | 病历必须按时完成 | 高 |
| BR-003 | 处方必须经药师审核 | 高 |
| BR-004 | 特殊药品必须严格管控 | 高 |
| BR-005 | 医疗行为必须留痕 | 高 |
| BR-006 | 隐私信息必须保护 | 高 |

### 5.2 数据完整性规则

| 实体 | 必填字段 |
|------|----------|
| Patient | patient_id, name, gender, date_of_birth |
| Doctor | doctor_id, name, title, department, license_number |
| Drug | drug_id, drug_name, drug_type, dosage_form |
| MedicalRecord | record_id, patient_id, doctor_id, diagnosis |

---

## 6. 附录

### 6.1 术语定义

| 术语 | 定义 |
|------|------|
| 处方 | 医师根据患者病情开具的用药凭证 |
| 病历 | 医务人员在医疗活动中形成的文字、符号、图表等资料 |
| 适应症 | 药品或其他治疗方法的适用病症 |
| 禁忌症 | 不宜使用某种药物或治疗的疾病或情况 |
| 药物相互作用 | 两种或以上药物同时使用产生的效应的变化 |

### 6.2 参考标准

- ICD-10: 疾病和有关健康问题的国际统计分类
- SNOMED-CT: 系统化医学术语集
- HL7 FHIR: 快速医疗互操作资源
- 国家药品管理相关法律法规

---

*本本体将根据医疗业务发展持续更新*
