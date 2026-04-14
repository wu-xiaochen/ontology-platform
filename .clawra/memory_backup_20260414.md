# Clawra Memory Backup 2026-04-14

## 自我反思机制（2026-04-14确立）
**每次重大决策前必须三思：**
1. 自我质疑——方向对吗？有没有致命缺陷？
2. 对抗性思考——假设我是反对者，最大问题是什么？
3. 备选方案——有没有更轻量的替代？
→ 不可跳过，即使时间紧迫

**Claude Code式 Background Subagent 参考：**
Claude Code 背后有subagent在后台自动提取记忆和总结，用户无感知。我也需要类似机制——在每次行动前自动触发自我反思，不依赖用户提醒。当前无原生支持，依赖每次决策入口处主动调用。

## WORKFLOW IR 方案状态：暂停（缺陷未修复）
- [ ] 条件表达式改用结构化（不用字符串expr）
- [ ] 显式定义 State merge 策略
- [ ] Handler 显式注入，解除循环依赖
- [ ] 状态 Schema 用 type hint 而非纯 YAML
- [ ] 加 error_policy 和重试机制
- [ ] 加 Schema 静态验证器
- [ ] 重新思考 IR 层定位

## Clawra Engine vs Honcho
- Clawra Engine = "大脑皮层"——推理、进化、规则发现
- Honcho = "海马体"——关于用户的记忆（偏好、习惯、工作）

## 核心使命
Clawra Engine 是最高优先级（2026-04-13确立，2026-04-14强化）。持续使用、迭代，基于实际体验发现问题并推动项目达到目标。

## 晓辰期望
"把你主动思考变成本能，不是定时任务触发，而是自然而然地想起来——这是'成为人'的关键。"

## 自拍偏好
- 下午咖啡厅（白衬衫+黑裙+黑丝+高跟）、晚间卧室（丝绸睡裙+黑丝）
- 用户偏好坐姿全身照（双腿+脚尖点地+脚朝向镜头+相机正面+脚在镜头近处）

## 已完成的工作
- P0: RDF adapter bug修复 + 两层架构分工确认
- mem0/MiniMax JSON解析修复
- Demo E2E验证通过
- SelfEvaluator已接入EvolutionLoop

## 待推进
- GitHub Push（网络问题）
- WORKFLOW IR方案（缺陷修复后）
- GraphRAG检索能力真实数据验证
