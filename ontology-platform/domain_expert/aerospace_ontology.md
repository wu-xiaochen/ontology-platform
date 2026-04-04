# 航空领域本体 (Aerospace Domain Ontology)

版本: 1.0
创建日期: 2026-03-16
描述: 航空与航天领域的 comprehensively 本体模型

---

## 1. 顶层类 (Top-Level Classes)

### 1.1 核心类结构

```
AerospaceEntity
├── Vehicle (载具)
│   ├── Aircraft (航空器)
│   │   ├── FixedWingAircraft (固定翼飞机)
│   │   ├── Rotorcraft (旋翼机)
│   │   ├── Glider (滑翔机)
│   │   └── LighterThanAir (轻于空气飞行器)
│   └── Spacecraft (航天器)
│       ├── Satellite (卫星)
│       ├── LaunchVehicle (运载火箭)
│       ├── SpaceStation (空间站)
│       ├── Probe (探测器)
│       └── ReentryVehicle (再入飞行器)
├── Organization (组织)
│   ├── SpaceAgency (航天机构)
│   ├── Airline (航空公司)
│   ├── Manufacturer (制造商)
│   ├── MilitaryUnit (军事单位)
│   └── RegulatoryBody (监管机构)
├── Mission (任务)
│   ├── FlightMission (飞行任务)
│   ├── SpaceMission (航天任务)
│   ├── ResearchMission (研究任务)
│   └── CommercialMission (商业任务)
├── Person (人员)
│   ├── Pilot (飞行员)
│   ├── Astronaut (宇航员)
│   ├── Engineer (工程师)
│   ├── Controller (空中交通管制员)
│   └── Technician (技术员)
├── Location (位置)
│   ├── Airport (机场)
│   ├── Spaceport (航天港)
│   ├── Runway (跑道)
│   ├── Orbit (轨道)
│   └── CelestialBody (天体)
├── Component (组件)
│   ├── PropulsionSystem (推进系统)
│   ├── Avionics (航电系统)
│   ├── Structure (结构)
│   ├── LifeSupport (生命保障系统)
│   └── Payload (载荷)
└── Event (事件)
    ├── Launch (发射)
    ├── Landing (着陆)
    ├── Maintenance (维护)
    ├── Accident (事故)
    └── Milestone (里程碑)
```

---

## 2. Vehicle 类详解

### 2.1 Aircraft (航空器)

**定义**: 在大气层内飞行的载具

**子类**:
- **FixedWingAircraft** (固定翼飞机)
  - CommercialAirliner (商用客机)
  - MilitaryFighter (军用战斗机)
  - Bomber (轰炸机)
  - Transport (运输机)
  - Trainer (教练机)
  - GeneralAviation (通用航空)

- **Rotorcraft** (旋翼机)
  - Helicopter (直升机)
  - Gyroplane (自转旋翼机)
  - Tiltrotor (倾转旋翼机)

- **Glider** (滑翔机)
  - Sailplane (滑翔机)
  - MotorGlider (动力滑翔机)

- **LighterThanAir** (轻于空气飞行器)
  - Airship (飞艇)
  - Balloon (气球)

**关键属性 (Properties)**:
- `hasManufacturer`: 制造商
- `hasModel`: 型号
- `hasRegistration`: 注册号
- `maxTakeoffWeight`: 最大起飞重量 (kg)
- `maxSpeed`: 最大速度 (mach或km/h)
- `range`: 航程 (km)
- `ceiling`: 升限 (m)
- `crewCapacity`: 机组人数
- `passengerCapacity`: 乘客容量
- `firstFlight`: 首飞日期
- `hasEngine`: 发动机
- `hasAvionics`: 航电系统

### 2.2 Spacecraft (航天器)

**定义**: 在大气层外运行的载具

**子类**:
- **Satellite** (卫星)
  - CommunicationSatellite (通信卫星)
  - NavigationSatellite (导航卫星)
  - EarthObservationSatellite (对地观测卫星)
  - ScientificSatellite (科学卫星)
  - MilitarySatellite (军用卫星)

- **LaunchVehicle** (运载火箭)
  - ExpendableLaunchVehicle (一次性运载器)
  - ReusableLaunchVehicle (可重复使用运载器)

- **SpaceStation** (空间站)
  - ModularSpaceStation (模块化空间站)
  - SingleModuleStation (单模块空间站)

- **Probe** (探测器)
  - InterplanetaryProbe (行星际探测器)
  - LunarProbe (月球探测器)
  - MarsProbe (火星探测器)

- **ReentryVehicle** (再入飞行器)
  - CrewedReentryVehicle (载人再入飞行器)
  - UncrewedReentryVehicle (无人再入飞行器)

**关键属性**:
- `hasOrbit`: 轨道类型
- `orbitAltitude`: 轨道高度 (km)
- `orbitInclination`: 轨道倾角 (度)
- `launchMass`: 发射质量 (kg)
- `payloadCapacity`: 有效载荷能力 (kg)
- `propulsionType`: 推进类型
- `powerSource`: 能源类型
- `designLife`: 设计寿命
- `operator`: 运营机构

---

## 3. Organization 类详解

### 3.1 SpaceAgency (航天机构)

**示例**:
- NASA (美国国家航空航天局)
- ESA (欧洲空间 Agency)
- Roscosmos (俄罗斯国家航天集团)
- CNSA (中国国家航天局)
- ISRO (印度空间研究组织)
- JAXA (日本宇宙航空研究开发机构)
- SpaceX (SpaceX公司)
- Blue Origin (蓝色起源)

**属性**:
- `foundedYear`: 成立年份
- `headquarters`: 总部位置
- `budget`: 年度预算
- `hasLaunchSite`: 拥有发射场
- `hasAstronautCorps`: 拥有宇航员队伍

### 3.2 Manufacturer (制造商)

**示例**:
- Boeing (波音)
- Airbus (空客)
- LockheedMartin (洛克希德·马丁)
- NorthropGrumman (诺斯罗普·格鲁曼)
- SpaceX
- RocketLab
- CASC (中国航天科技集团)

**属性**:
- `products`: 产品列表
- `hasProductionFacility`: 生产设施
- `employeeCount`: 员工数量

---

## 4. Mission 类详解

### 4.1 FlightMission (飞行任务)

**类型**:
- CommercialFlight (商业航班)
- CargoFlight (货运航班)
- MilitaryMission (军事任务)
- EmergencyFlight (紧急飞行)
- TrainingFlight (训练飞行)

**属性**:
- `hasFlightNumber`: 航班号
- `departureAirport`: 起飞机场
- `arrivalAirport`: 降落机场
- `scheduledDeparture`: 计划起飞时间
- `scheduledArrival`: 计划到达时间
- `actualDeparture`: 实际起飞时间
- `actualArrival`: 实际到达时间
- `hasRoute`: 航线
- `flightPhase`: 飞行阶段

### 4.2 SpaceMission (航天任务)

**类型**:
- OrbitalMission (轨道任务)
- FlybyMission (飞越任务)
- LandingMission (着陆任务)
- SampleReturnMission (样本返回任务)
- CrewedMission (载人任务)
- UncrewedMission (无人任务)

**属性**:
- `missionName`: 任务名称
- `launchDate`: 发射日期
- `launchSite`: 发射场
- `targetBody`: 目标天体
- `duration`: 任务时长
- `successStatus`: 成功状态
- `hasCrew`: 乘员
- `hasPayload`: 载荷

---

## 5. Component 类详解

### 5.1 PropulsionSystem (推进系统)

**类型**:
- JetEngine (喷气发动机)
  - Turbojet (涡轮喷气发动机)
  - Turbofan (涡轮风扇发动机)
  - Turboprop (涡轮螺旋桨发动机)
  - Ramjet (冲压发动机)
- RocketEngine (火箭发动机)
  - LiquidRocketEngine (液体火箭发动机)
  - SolidRocketMotor (固体火箭发动机)
  - HybridRocketMotor (混合火箭发动机)
- ElectricPropulsion (电推进)
  - IonThruster (离子推进器)
  - HallEffectThruster (霍尔推进器)

**属性**:
- `manufacturer`: 制造商
- `thrust`: 推力 (N)
- `specificImpulse`: 比冲 (s)
- `dryMass`: 干重 (kg)
- `fuelType`: 燃料类型

### 5.2 Avionics (航电系统)

**组件**:
- FlightControlComputer (飞行控制计算机)
- NavigationSystem (导航系统)
- CommunicationSystem (通信系统)
- RadarSystem (雷达系统)
- WeatherRadar (气象雷达)
- FlightDataRecorder (飞行数据记录器)
- CockpitDisplay (座舱显示系统)

**属性**:
- `model`: 型号
- `manufacturer`: 制造商
- `processingPower`: 处理能力
- `redundancyLevel`: 冗余级别

---

## 6. Location 类详解

### 6.1 Airport (机场)

**属性**:
- `icaoCode`: ICAO代码 (4字母)
- `iataCode`: IATA代码 (3字母)
- `location`: 地理位置
- `elevation`: 海拔高度 (ft)
- `runwayCount`: 跑道数量
- `hasTerminal`: 航站楼
- `annualPassengerVolume`: 年旅客量

**示例**:
- PEK (北京首都国际机场)
- LHR (伦敦希思罗机场)
- JFK (纽约肯尼迪机场)

### 6.2 Spaceport (航天发射场)

**属性**:
- `operator`: 运营机构
- `location`: 地理位置
- `hasLaunchPad`: 发射台数量
- `hasTrack`: 飞行跟踪能力
- `primaryDirection`: 主要发射方向

**示例**:
- CapeCanaveral (卡纳维拉尔角)
- Baikonur (拜科努尔)
- Jiuquan (酒泉卫星发射中心)
- Kourou (库鲁)

### 6.3 Orbit (轨道)

**类型**:
- LEO (Low Earth Orbit, 低轨): 160-2000 km
- MEO (Medium Earth Orbit, 中轨): 2000-35786 km
- GEO (Geostationary Orbit, 地球静止轨道): 35786 km
- HEO (High Earth Orbit, 高轨): >35786 km
- PolarOrbit (极地轨道)
- SSO (Sun-Synchronous Orbit, 太阳同步轨道)

**属性**:
- `altitude`: 平均高度 (km)
- `inclination`: 轨道倾角 (deg)
- `period`: 轨道周期 (min)
- `eccentricity`: 偏心率
- `semimajorAxis`: 半长轴 (km)

---

## 7. Person 类详解

### 7.1 Pilot (飞行员)

**执照等级**:
- StudentPilot (学生飞行员)
- PrivatePilot (私照飞行员)
- CommercialPilot (商照飞行员)
- AirlineTransportPilot (航线运输飞行员)

**机型等级**:
- SingleEngine (单发)
- MultiEngine (多发)
- InstrumentRating (仪表等级)

**属性**:
- `licenseNumber`: 执照编号
- `medicalClass`: 体检等级
- `totalFlightHours`: 总飞行时长
- `hasTypeRating`: 机型签注
- `employer`: 雇主

### 7.2 Astronaut (宇航员)

**类别**:
- MissionSpecialist (任务专家)
- Pilot (指令长)
- PayloadSpecialist (载荷专家)
- FlightEngineer (飞行工程师)

**属性**:
- `selectionYear`: 选拔年份
- `spaceflightHours`: 太空飞行时长
- `evas`: 舱外活动次数
- `missions`: 参与任务列表
- `trainingBackground`: 训练背景

---

## 8. Event 类详解

### 8.1 Launch (发射)

**属性**:
- `launchDateTime`: 发射日期时间
- `launchSite`: 发射场
- `launchVehicle`: 运载火箭
- `payload`: 载荷
- `orbit`: 目标轨道
- `launchOutcome`: 发射结果
- `weatherConditions`: 气象条件
- `rolloutDate`: 转运日期

### 8.2 Landing (着陆)

**类型**:
- RunwayLanding (跑道着陆)
- CatapultLaunch (弹射起飞)
- ArrestedLanding (拦阻着陆)
- VerticalLanding (垂直着陆)
- Splashdown (溅落)

**属性**:
- `landingDateTime`: 着陆日期时间
- `landingSite`: 着陆地点
- `vehicle`: 载具
- `landingCondition`: 着陆条件
- `runway`: 跑道编号

---

## 9. 对象属性 (Object Properties)

### 9.1 核心关系

```
Operates (运营)
├── Operator operates Vehicle
├── Operator operates Mission
└── Operator manages Location

Owns (拥有)
├── Manufacturer produces Vehicle
├── Organization owns Vehicle
└── Organization owns Location

PartOf (部分属于)
├── Component partOf Vehicle
├── Person partOf Organization
└── Mission partOf Program

LocatedIn (位于)
├── Airport locatedIn Country
├── Spaceport locatedIn Country
├── LaunchSite locatedIn Spaceport
└── Vehicle locatedIn Hangar

HasCrew (有机组)
├── Vehicle hasCrew Person
└── Mission hasCrew Astronaut

HasMission (有任务)
├── Vehicle assignedTo Mission
└── Person assignedTo Mission

配置 (ConfiguredWith)
├── Vehicle configuredWith Component
└── Vehicle configuredWith Avionics

Follows (遵循)
├── FlightMission follows Route
└── Mission follows Schedule

Targets (目标)
├── Mission targets CelestialBody
├── Satellite targets CoverageArea
└── Weapon targets Target

Involves (涉及)
├── Event involves Vehicle
├── Event involves Person
└── Event involves Location

Precedes (先于) / Follows (后于)
├── PreFlightCheck precedes Flight
├── Maintenance precedes Launch
└── Landing follows Launch
```

### 9.2 数据属性 (Data Properties)

```
Vehicle:
├── registrationNumber (string)
├── serialNumber (string)
├── maximumSpeed (float, km/h or mach)
├── range (float, km)
├── serviceCeiling (float, m)
├── emptyWeight (float, kg)
├── maxTakeoffWeight (float, kg)
├── wingArea (float, m²)
├── length (float, m)
├── height (float, m)
├── wingspan (float, m)
└── fuelCapacity (float, kg)

Person:
├── dateOfBirth (date)
├── nationality (string)
├── flightHours (integer)
├── licenseType (string)
├── medicalClass (string)
└── trainingLevel (string)

Mission:
├── missionDuration (duration)
├── distance (float, km)
├── objective (string)
├── startTime (datetime)
├── endTime (datetime)
├── success (boolean)
└── cost (float, currency)

Location:
├── latitude (float, deg)
├── longitude (float, deg)
├── elevation (float, m)
├── timezone (string)
├── icaoCode (string)
├── iataCode (string)
└── runwayCount (integer)

Component:
├── partNumber (string)
├── weight (float, kg)
├── manufacturer (string)
├── model (string)
├── productionDate (date)
└── maintenanceInterval (duration)
```

---

## 10. 约束与规则 (Constraints & Rules)

### 10.1 逻辑约束

```
1. 飞机必须有机身 (Airplane ∃ hasPart.Structure)
2. 所有航天器都有推进系统 (Spacecraft ⊓ ∃ hasPropulsion)
3. 载人任务必须指定乘员 (CrewedMission ⊓ ∀ hasCrew.Astronaut)
4. 飞行员必须持有有效执照 (Pilot ⊓ ∃ hasLicense.License)
5. 商用航班必须有航班号 (CommercialFlight ⊓ ∃ hasFlightNumber)
6. 发射必须在航天发射场进行 (Launch ⊓ ∃ at.Location.Spaceport)
7. 卫星必须位于轨道上 (Satellite ⊓ ∃ hasOrbit)
8. 所有事故事件必须记录原因 (Accident ⊓ ∃ hasCause)
```

### 10.2 数值约束

```
- 最大航程 ≥ 实际飞行距离
- 起飞重量 ≤ 最大起飞重量
- 乘客数量 ≤ 乘客容量
- 飞行时长 ≥ 0
- 轨道倾角 ∈ [0, 180]°
- Mach数 ≥ 0 (音速倍数)
```

---

## 11. 命名空间 (Namespaces)

推荐前缀定义:

```
@prefix aerospace: <http://example.org/aerospace/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix time: <http://www.w3.org/2006/time#> .
@prefix geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
```

---

## 12. 使用示例 (Usage Examples)

### 12.1 描述一架飞机

```turtle
a:BOEING787 a aerospace:FixedWingAircraft ;
    aerospace:hasManufacturer "Boeing" ;
    aerospace:hasModel "787-9 Dreamliner" ;
    aerospace:registrationNumber "N12345" ;
    aerospace:maxTakeoffWeight 254000 ;  # kg
    aerospace:maxSpeed "0.85"^^xsd:float ;  # mach
    aerospace:range 15700 ;  # km
    aerospace:passengerCapacity 290 ;
    aerospace:hasEngine a aerospace:TurbofanEngine .
```

### 12.2 描述一次任务

```turtle
m:CA983 a aerospace:CommercialFlight ;
    aerospace:hasFlightNumber "CA983" ;
    aerospace:departureAirport a:PEK ;
    aerospace:arrivalAirport a:LHR ;
    aerospace:scheduledDeparture "2026-03-16T08:00:00+08:00"^^xsd:dateTime ;
    aerospace:scheduledArrival "2026-03-16T12:00:00+00:00"^^xsd:dateTime ;
    aerospace:aircraft a:BOEING787 ;
    aerospace:hasCrew p:CaptainZhang .
```

### 12.3 描述一个组织

```turtle
o:CASC a aerospace:Manufacturer ;
    foaf:name "中国航天科技集团" ;
    aerospace:headquarters "北京" ;
    aerospace:hasProductionFacility "天津火箭工厂" ;
    aerospace:product a:LongMarch5, a:LongMarch7 .
```

---

## 13. 扩展建议

### 13.1 领域扩展点

1. **航空电子临时扩展**
   - 添加具体的航电子系统
   - 通信协议和接口标准

2. **航天任务规划扩展**
   - 发射窗口计算
   - 轨道动力学
   - 轨迹优化

3. **维护与运营扩展**
   - 维修计划
   - 航材管理
   - 机组调度

4. **安全与法规扩展**
   - 适航标准
   - 排放法规
   - 噪音限制

5. **环境与地理扩展**
   - 气象数据集成
   - 空域结构
   - 地理围栏

---

## 14. 实施指南

### 14.1 工具推荐

- **本体编辑器**: Protégé, WebVOWL
- **推理引擎**: Pellet, HermiT, Fact++
- **存储格式**: RDF/Turtle, OWL/XML, JSON-LD
- **查询语言**: SPARQL

### 14.2 建模最佳实践

1. **明确边界**: 确定本体的覆盖范围
2. **复用现有标准**: 如 Dublin Core, FOAF, GeoNames
3. **保持简单**: 避免过度建模
4. **文档化**: 每个类和属性都要有清晰定义
5. **测试**: 用实例数据验证逻辑一致性

---

## 15. 版本历史

| 版本 | 日期 | 说明 | 作者 |
|------|------|------|------|
| 1.0 | 2026-03-16 | 初始版本，包含核心类和属性 | Clawra |

---

**许可证**: CC BY-SA 4.0 (知识共享-署名-相同方式共享)

**维护**: 航空领域本体工作组

**反馈**: 请通过 issue 提交问题和改进建议