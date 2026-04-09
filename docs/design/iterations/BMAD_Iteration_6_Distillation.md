# BMAD Iteration 6: 自主技能蒸馏 (The Voyager-Loop)

## [B] 方案头脑风暴：核心隐患与优化空间

将推理路径转化为可执行代码是 Agent 进化的“圣杯”，但也存在以下 4 个重大技术风险：

### 1. 🚨 执行沙箱的安全逃逸
- **隐患**：生成的 Python 代码如果包含 `__builtins__` 篡改或巧妙的混淆代码，可能绕过简单的正则检查。
- **治理**：必须使用 AST (Abstract Syntax Tree) 进行深度静态检查，并维护严格的模块白名单。

### 2. 🌀 技能爆炸与冗余
- **隐患**：Agent 可能会为每个类似的任务都生成一个略有不同的技能。
- **治理**：在蒸馏前通过 `EpisodicMemory` 的语义搜索检查是否存在相似技能，若存在则进行“技能合并”而非新建。

### 3. 📉 技能质量反馈断裂
- **隐患**：生成的代码可能有 Bug。
- **治理**：引入“试用期”制度。新生成的技能初始状态为 `CANDIDATE`，只有在后续成功运行且得到正向反馈后方可转为 `ACTIVE`。

### 4. 🔗 命名冲突与可发现性
- **隐患**：LLM 生成的函数名可能冲突。
- **治理**：使用 `skill_v1_{slug}` 风格的命名空间，并将元数据存入本体图谱。

## [M] 技术方案建模 (Modeling)

### 核心契约：蒸馏决策引擎
```python
def should_distill(trace: List[str], metrics: Dict) -> bool:
    # 判据：成功、高置信度、且属于重复出现的逻辑模式
    pass
```

### 核心契约：动态工具加载器
```python
def load_and_inject_as_tool(skill: Skill) -> ToolDefinition:
    # 将磁盘上的 .py 文件动态转化为 Orchestrator 可识别的 Tool
    pass
```

## [A] 对抗性审查 (Adversarial)

- **问**：为什么不直接用 LLM 改写代码，要做蒸馏？
- **答**：蒸馏后的 Python 代码执行性能远高于多次 LLM 推理，且能实现逻辑的“确定性固化”。
- **问**：如果生成的函数报错，会挂掉整个系统吗？
- **答**：所有技能执行必须包裹在 `try-except` 中，且失败时会自动触发 `MetaLearner` 的技能降级评分。

## [D] 开发规约 (Development Rules)
- 所有生成的技能文件必须包含标准 Header（创建时间、来源、SHA256）。
- 严格遵循 `src/utils/config.py` 中的安全配置。
