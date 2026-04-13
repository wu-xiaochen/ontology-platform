# ADR-003: Evolution Loop Architecture

> 状态: **已通过** | 日期: 2026-04-10

---

## 背景

Clawra 需要一个自进化闭环系统，能够：
- 从经验中学习（Meta-Learner）
- 发现并提取新规则（Rule Discovery）
- 自动评估和修正（Self-Evaluator + Self-Correction）
- 技能的自动打包（Skill Distiller）

同时需要处理进化失败、规则冲突、性能退化等问题。

---

## 决策

### 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Evolution Loop (8 Phases)                │
│                                                             │
│  ┌───────┐   ┌────────┐   ┌────────┐   ┌──────────┐       │
│  │Perceive│ → │ Reason │ → │ Execute│ → │ Evaluate │       │
│  └───────┘   └────────┘   └────────┘   └──────────┘       │
│       ↑                                        │           │
│       │          ┌──────────────────────┐     │           │
│       └──────────│  Meta-Learner +      │←────┘           │
│                  │  Rule Discovery      │                  │
│                  │  (自动规则生成)       │                  │
│                  └──────────────────────┘                  │
│                           │                                │
│       ┌───────────────────┼───────────────────┐            │
│       ↓                   ↓                   ↓            │
│  ┌──────────┐      ┌───────────┐      ┌─────────────┐      │
│  │Self-     │      │Skill      │      │Pattern      │      │
│  │Correction │      │Distiller  │      │VersionCtrl  │      │
│  └──────────┘      └───────────┘      └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. MetaLearner（可选阶段）

```python
class MetaLearner:
    """元学习器：分析学习策略，决定如何学习"""

    def analyze_failure(self, failure_context: Dict) -> StrategyRecommendation:
        """分析失败原因，推荐改进策略"""
        pass

    def generate_hypothesis(self, pattern: LogicPattern) -> List[Hypothesis]:
        """为模式生成改进假设"""
        pass

    def update_learning_policy(self, policy: LearningPolicy) -> None:
        """更新学习策略"""
        pass
```

#### 2. RuleDiscovery（自动规则生成）

```python
class RuleDiscovery:
    """规则发现：从交互历史中提取规则"""

    def discover_from_interaction(
        self,
        interaction: Interaction,
        min_confidence: float = 0.7
    ) -> List[LogicPattern]:
        """从交互中发现规则"""
        pass

    def detect_conflicts(
        self,
        new_pattern: LogicPattern,
        existing_patterns: List[LogicPattern]
    ) -> List[Conflict]:
        """检测规则冲突"""
        pass

    def merge_similar(
        self,
        patterns: List[LogicPattern]
    ) -> List[LogicPattern]:
        """合并相似规则（去重）"""
        pass
```

#### 3. SelfEvaluator（自我评估）

```python
class SelfEvaluator:
    """自我评估器：评估进化效果"""

    def evaluate_inference(
        self,
        inference: Inference,
        ground_truth: Dict = None
    ) -> EvaluationResult:
        """评估推理结果"""
        pass

    def calculate_metrics(self) -> Dict[str, float]:
        """计算核心指标"""
        # Precision, Recall, F1, Drift Score, Pattern Quality,
        # Inference Latency, Knowledge Coverage, Skill Readiness
        pass
```

### Phase 流程

| Phase | 输入 | 处理 | 输出 |
|-------|------|------|------|
| 1. Perceive | 外部输入 | 解析、分类 | 结构化事件 |
| 2. Reason | 事件 + KG | 图推理 | 候选结论 |
| 3. Execute | 结论 | 执行动作 | 执行结果 |
| 4. Evaluate | 结果 | 与预期对比 | 差距分析 |
| 5. Detect Drift | 评估结果 | 漂移检测 | 漂移信号 |
| 6. Revise Rules | 漂移信号 | 规则修正 | 新/改规则 |
| 7. Update KG | 新规则 | 知识更新 | 更新的 KG |
| 8. Learn | 学习历史 | 模式学习 | 技能更新 |

---

## 进化失败处理

```python
class EvolutionFailureHandler:
    """进化失败处理器"""

    # 失败 → 反馈循环回到 Meta-Learner
    def handle_failure(
        self,
        failure: EvolutionFailure,
        loop_state: LoopState
    ) -> FeedbackSignal:
        """处理进化失败"""
        if failure.type == "inference_error":
            # 推理错误 → 回退 + 重试
            return FeedbackSignal(
                target_phase="Reason",
                action="retry_with_simpler_rules",
                confidence_boost=False
            )
        elif failure.type == "pattern_conflict":
            # 规则冲突 → 触发冲突解决
            return FeedbackSignal(
                target_phase="MetaLearner",
                action="resolve_conflict",
                confidence_boost=False
            )
        elif failure.type == "drift_detected":
            # 漂移检测 → 重新学习
            return FeedbackSignal(
                target_phase="MetaLearner",
                action="relearn",
                confidence_boost=True
            )
```

---

## 后果

### 正面

- ✅ 8 阶段闭环，覆盖完整进化生命周期
- ✅ MetaLearner 驱动策略优化
- ✅ 失败自动反馈，不卡死
- ✅ 支持规则冲突检测和合并
- ✅ Skill Distiller 将进化结果固化为可执行技能

### 负面

- ❌ 复杂度较高，需要仔细调参
- ❌ LLM 调用频繁，成本较高
- ❌ 需要监控多个指标

### 风险缓解

- ⚠️ 使用可选 Phase（部分场景可跳过 Meta-Learner）
- ⚠️ 配置最大迭代次数防止无限循环
- ⚠️ 启用降级策略（Evolution Loop 失败回退到基础推理）

---

## 实现清单

- [x] `src/evolution/evolution_loop.py` - 8 阶段闭环
- [x] `src/evolution/meta_learner.py` - MetaLearner
- [x] `src/evolution/rule_discovery.py` - RuleDiscovery
- [x] `src/evolution/self_evaluator.py` - SelfEvaluator
- [x] `src/evolution/self_correction.py` - SelfCorrection
- [x] `src/evolution/skill_distiller.py` - Skill Distiller
- [x] `src/evolution/failure_handler.py` - 失败处理

---

## 相关 ADR

- [ADR-001](./ADR-001_LLM_Provider_Abstraction.md) - MetaLearner 依赖 LLM Provider
- [ADR-004](./ADR-004_Configuration_Management.md) - Evolution Loop 参数通过配置管理
