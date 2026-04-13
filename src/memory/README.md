# Memory 模块 (Memory Governance)

本目录提供 Agent 长期记忆的语义健康度监控与治理功能，确保记忆系统的质量与稳定性。

## 📁 文件结构

```
src/memory/
├── governance.py   # 记忆治理器实现
├── monitor.py      # 时间序列监控（如果存在）
└── __init__.py     # 模块导出
```

## 🚀 核心功能

### MemoryGovernance - 记忆治理器

**解决的问题**:
- Agent 记忆随时间漂移，导致行为不稳定
- 本体类层次结构逐渐偏离设计
- 记忆一致性无法自动验证
- 缺乏健康度量化指标

**核心特性**:
- ✅ 本体健康度评估（0-100 分）
- ✅ 类层次结构漂移检测
- ✅ 属性一致性验证
- ✅ 逻辑一致性检查
- ✅ 自动修复建议生成

### 健康度指标

| 指标 | 权重 | 说明 |
|------|------|------|
| 类覆盖率 | 30% | 本体类的使用覆盖程度 |
| 属性一致性 | 30% | 属性值类型和范围一致性 |
| 逻辑一致性 | 40% | 无矛盾推理、无循环依赖 |

## 📖 使用示例

### 基础健康检查

```python
from ontology_platform.memory import MemoryGovernance

# 创建治理器
gov = MemoryGovernance(memory_graph)

# 执行全面健康检查
health = gov.check_health()

print(f"总体健康度：{health.overall_score}/100")
print(f"类覆盖率：{health.class_coverage}%")
print(f"属性一致性：{health.property_consistency}%")
print(f"逻辑一致性：{'✓' if health.logical_consistency else '✗'}")

# 查看漂移警告
for alert in health.drift_alerts:
    print(f"⚠️ {alert.type}: {alert.description}")

# 查看修复建议
for rec in health.recommendations:
    print(f"💡 {rec}")
```

### 漂移检测

```python
# 设置基准快照
gov.set_baseline()

# ... Agent 运行一段时间 ...

# 检测相对于基准的漂移
drift_alerts = gov.detect_drift()

if drift_alerts:
    print(f"检测到 {len(drift_alerts)} 个漂移问题")
    for alert in drift_alerts:
        if alert.severity == "high":
            print(f"🔴 严重：{alert.description}")
            print(f"   影响实体：{alert.affected_entities}")
```

### 自动修复建议

```python
health = gov.check_health()

if health.overall_score < 70:
    print("健康度低于阈值，建议修复:")
    gov.suggest_remediation(health)
    
    # 可能的建议:
    # - "建议清理未使用的类：UnusedClass1, UnusedClass2"
    # - "检测到属性类型冲突：age 应为 int，发现 str 类型"
    # - "循环依赖检测：A → B → C → A"
```

## 📊 数据模型

### HealthReport - 健康度报告

```python
@dataclass
class HealthReport:
    overall_score: float          # 总体得分 (0-100)
    class_coverage: float         # 类覆盖率 (%)
    property_consistency: float   # 属性一致性 (%)
    logical_consistency: bool     # 逻辑一致性
    drift_alerts: List[DriftAlert]  # 漂移警告列表
    last_check: datetime          # 最后检查时间
    recommendations: List[str]    # 修复建议
```

### DriftAlert - 漂移警告

```python
@dataclass
class DriftAlert:
    type: str                     # 类型：class_drift/property_drift/relationship_drift
    severity: str                 # 严重程度：low/medium/high
    description: str              # 描述
    affected_entities: List[str]  # 影响实体
    timestamp: datetime           # 时间戳
```

## 🔧 核心方法

### `check_health() -> HealthReport`

执行全面的健康度检查。

**检查项**:
1. 类覆盖率检查
2. 属性一致性检查
3. 逻辑一致性检查
4. 漂移检测

**返回**:
- `HealthReport`: 包含所有指标和警告的报告

**阈值配置**:
```python
COVERAGE_THRESHOLD = 0.8      # 最低覆盖率 80%
CONSISTENCY_THRESHOLD = 0.9   # 最低一致性 90%
DRIFT_THRESHOLD = 0.15        # 漂移阈值 15%
```

### `_check_class_coverage() -> float`

检查本体类的使用覆盖程度。

**逻辑**:
- 统计已实例化的类 vs 总类数
- 识别未使用的类
- 计算覆盖率

### `_check_property_consistency() -> float`

检查属性值的一致性。

**检查项**:
- 类型一致性（如 age 应为 int）
- 范围一致性（如 score 应在 0-100）
- 格式一致性（如 date 应为 ISO 格式）

### `_check_logical_consistency() -> bool`

检查逻辑一致性。

**检查项**:
- 无矛盾推理
- 无循环依赖
- 继承关系正确

### `_detect_drift() -> List[DriftAlert]`

检测记忆漂移。

**漂移类型**:
- `class_drift`: 类层次结构变化
- `property_drift`: 属性定义变化
- `relationship_drift`: 关系模式变化

## 🎯 应用场景

### 1. 定期健康检查

```python
# 每天定时检查
import schedule
from datetime import datetime

def daily_health_check():
    health = gov.check_health()
    log = {
        "date": datetime.now(),
        "score": health.overall_score,
        "alerts": len(health.drift_alerts)
    }
    save_to_monitoring(log)

schedule.every().day.at("02:00").do(daily_health_check)
```

### 2. 部署前验证

```python
# 部署前确保记忆健康
def pre_deployment_check():
    health = gov.check_health()
    
    if health.overall_score < 80:
        raise DeploymentError(
            f"记忆健康度 {health.overall_score} 低于阈值 80"
        )
    
    if not health.logical_consistency:
        raise DeploymentError("检测到逻辑不一致")
    
    return True
```

### 3. 异常行为诊断

```python
# Agent 行为异常时诊断
def diagnose_agent_behavior():
    health = gov.check_health()
    
    # 检查是否有严重漂移
    severe_drifts = [a for a in health.drift_alerts if a.severity == "high"]
    
    if severe_drifts:
        print("发现严重漂移，可能导致行为异常:")
        for drift in severe_drifts:
            print(f"  - {drift.description}")
        
        # 建议回滚到基准
        gov.rollback_to_baseline()
```

## 📈 监控集成

### Prometheus 指标

```python
from prometheus_client import Gauge

MEMORY_HEALTH_SCORE = Gauge('memory_health_score', '记忆健康度评分')
MEMORY_DRIFT_ALERTS = Gauge('memory_drift_alerts', '漂移警告数量')

def update_metrics(health: HealthReport):
    MEMORY_HEALTH_SCORE.set(health.overall_score)
    MEMORY_DRIFT_ALERTS.set(len(health.drift_alerts))
```

### 告警规则

```yaml
# Prometheus 告警规则
- alert: MemoryHealthLow
  expr: memory_health_score < 70
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "记忆健康度低于 70"
    
- alert: MemoryLogicalInconsistency
  expr: memory_logical_consistency == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "检测到逻辑不一致"
```

## 🔗 相关模块

- [Chunking 模块](../chunking/README.md) - 文档分块
- [API 模块](../api/README.md) - API 接口
- [Ontology 模块](../ontology/README.md) - 本体论核心

## 📚 设计原则

1. **可观测性**: 所有记忆操作可追踪、可审计
2. **可恢复性**: 支持回滚到历史基准
3. **可解释性**: 所有警告和建议都有明确解释
4. **自动化**: 支持自动修复建议生成

## ⚠️ 注意事项

- 健康检查是计算密集型操作，建议定期而非实时执行
- 漂移检测需要先设置基准快照
- 修复建议仅供参考，重大修改需人工审核
