# BMAD Iteration 4: 性能瓶颈与高危漏洞优化指南

## [B] 方案头脑风暴：核心隐患与优化空间

以严格的生产级标准审查代码，我们发现系统中仍潜藏以下 5 个关键的并发及性能漏洞：

### 1. 🚨 重大并发缺陷（Fake Async）
- **位置**：`src/agents/orchestrator.py`
- **问题**：`execute_task` 被定义为了 `async def`，但其内部却在调用 **同步版** 的 `OpenAI()` 客户端 (`client.chat.completions.create`)，并在异常重试时使用了 `time.sleep(wait_time)`！
- **后果**：这会导致灾难性的“阻塞事件循环”。在真实服务器中，一个用户的请求会在等待大模型或 `time.sleep` 的期间**完全锁死整个 Node/Thread**，后面的所有并发请求都必须排队。
- **治理**：必须将客户端替换为 `AsyncOpenAI`，使用 `await client.chat.completions.create(...)` 以及 `await asyncio.sleep(wait_time)`。

### 2. 💥 数学沙盒的资源耗尽漏洞（CPU/内存 DoS）
- **位置**：`src/core/ontology/rule_engine.py` (SafeMathSandbox)
- **问题**：虽然系统成功限制了 AST 深度防止深层递归，但却允许了 `ast.Pow` (指数运算) 和 `ast.Mult` (乘法)。
- **后果**：如果恶意 Rule 包含 `99999999 ** 99999999`，其 AST 深度只有 2，但执行时会瞬间锁死 CPU。若使用字符串字面量乘以大数字 `"a" * 999999999`，会瞬间导致服务器 OOM 内存溢出。
- **治理**：需要拦截过大的指数（底数或指数上限限制），或者通过安全的乘方计算函数替代 `ast.Pow`。

### 3. ⏱️ 潜意识修剪阻塞关键响应链路 (GC Latency Hit)
- **位置**：`src/agents/orchestrator.py`
- **问题**：`self.memory_governor.run_garbage_collection()` （记忆剪枝）配置在了回复用户响应之前**同步执行**。
- **后果**：随着 Neo4j 或图谱体积的增大，每次用户对话的延迟（Latency）会直线上升。
- **治理**：应将其解耦，通过 `asyncio.create_task()` 抛入后台静默执行，实现真正的非阻塞运行。

### 4. 🕸️ GraphRAG 返回爆炸（超级节点无限制）
- **位置**：`Orchestrator` 的 `tool_query_name` 执行逻辑中
- **问题**：基于正则表达式提取实体后，无脑调用 `find_neighbors(entity, depth=1)` 并全量灌入 Reasoner。
- **后果**：如果用户提问带有“实体”、“系统”等超级节点，全量提取会立刻导致 LLM 爆 Token，冲毁核心业务图细节。
- **治理**：必须在图查询中强加 `limit=15`（或其他常数阈值），强制防止拓扑爆炸。

### 5. ⚠️ 技术债：Pydantic V1/V2 报错
- **位置**：项目各处配置类及返回模型层
- **问题**：继续在使用已在 Pydantic V2 中弃用的 `class Config:` 元类，导致系统启停和测试中疯狂打印警告。
- **治理**：重构为官方推荐的 `model_config = ConfigDict(...)` 写法。
