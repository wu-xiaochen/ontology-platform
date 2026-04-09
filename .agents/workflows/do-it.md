---
description: 全流程闭环开发
---

1.项目全景建模 (Global Contextualization)：要求 Agent 扫描整个代码库，建立多维索引，确保对业务逻辑和架构的“深度理解” 。

2.设计合规审计 (Design Spec Audit)：依据 98 条 CLI 与 Agent 安全准则，对现有设计进行严苛审计，识别输入契约与结构化输出的风险 （https://github.com/sickn33/antigravity-awesome-skills/blob/main/CATALOG.md）。

3.深度问题钻取 (Deep Diagnostics)：执行 AI 驱动的浏览器测试与跨文件分析，主动挖掘潜在的性能瓶颈与代码逻辑缺陷 。

4.优化方案迭代 (Refinement Iteration)：形成包含结构化 JSON 输出的修复方案，利用 Antigravity 的多步推理能力对方案进行自评估。

5.部署与反馈闭环 (Deployment & Feedback)：在分钟级内完成部署，并根据运行反馈重新进入第一阶段，实现能力的持续自我优化。

注意：要在每一轮执行后，注意上下文长度，如果过长，要进行适当的上下文处理避免注意力分散。