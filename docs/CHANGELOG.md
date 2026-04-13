# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.1.0] - 2026-04-13

### Added

#### Evolution Loop（进化闭环）
- **完整8阶段闭环**（`EvolutionLoop`，821行）：Perceive → Learn → Reason → Execute → Evaluate → DetectDrift → ReviseRules → UpdateKG
- **失败反馈路由**：推理错误/规则冲突/漂移检测 → 自动回流 MetaLearner 重学
- **MetaLearn Phase**：失败信号专用处理阶段
- **Phase 钩子注册**：支持自定义回调 `register_hook(phase, callback)`

#### Pattern 版本控制
- `add_pattern()`：保存旧版本历史
- `get_pattern_history(pattern_id)`：查询所有版本
- `compare_versions(pattern_id, v1, v2)`：版本 diff
- `rollback_pattern(pattern_id, target_version)`：回滚到指定版本
- `_archive_pattern_version()`：版本归档
- `current_version` 属性

#### 规则相似度去重
- `PatternVectorizer`：LogicPattern 向量化（embedding + 特征哈希降级）
- `similarity(p1, p2)`：余弦相似度计算
- `merge_similar_patterns()`：自动合并高相似度规则（阈值 0.85）
- `detect_redundancy()`：返回冗余规则列表
- 配置参数：`similarity_threshold`, `enable_auto_merge`

#### Skill 可执行性
- `SkillDistiller` 大幅增强（70 → 433行）
- `Skill.execute(params)`：支持参数传入，返回执行结果
- `SafeExecutor`：沙盒 AST 执行（禁止文件IO、网络请求等危险操作）
- 技能注册时验证可执行性
- 支持 Python 代码片段和结构化指令两种格式

#### GraphRAG 社区检测增强
- **Leiden 算法**（`pip install leidenalg`）：保证社区连接性，比 Louvain 更精确
- `detect_communities(algorithm="leiden")`：一键切换
- `generate_community_summaries(llm_client)`：LLM 生成社区主题摘要
- `_build_heuristic_summary()`：无 LLM 时的降级摘要
- `cross_community_reasoning(a, b, max_hops)`：跨社区推理路径发现
- `_build_community_description()`：社区关系文本构建

#### 测试
- 新增 `test_evolution_loop.py`（20个测试用例，覆盖所有 Phase + 失败路由 + 状态管理）

### Fixed
- `unified_logic.py`：`import time` 缺失（`NameError: time not defined`）
- `test_sdk_hardening.py`：`evolve()` async 调用修复（`IsolatedAsyncioTestCase`）
- `EvolutionConfig`：新增 `max_iterations`, `convergence_threshold`, `enable_meta_learner`, `enable_rule_discovery`

### Changed
- `pyproject.toml` version：`4.0.0-alpha.1` → `4.1.0-alpha`
- `docs/`：新增11个文档（PROJECT_OVERVIEW, PHILOSOPHY, EVOLUTION_LOOP, ROADMAP, CONFIGURATION, SDK_GUIDE, INTEGRATION_GUIDE, TROUBLESHOOTING, TESTING_STRATEGY, DEPLOYMENT, CHANGELOG）
- `docs/ADR/`：新增4个架构决策记录（ADR-001~004）

---

## [4.0.0] - 2026-04-10

### Added
- Clawra 核心架构 v4.0
- Skill Distiller 技能蒸馏
- UnifiedSkillRegistry 技能库
- BehaviorLearner 行为学习
- Distillation 知识蒸馏
- 完整文档体系
