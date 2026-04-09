# BMAD Iteration 5: Mem0 情节记忆层企业级硬化

## [B] 方案头脑风暴：核心隐患与优化空间

针对目前的 Mem0 集成，我们识别出以下 4 个关键风险点：

### 1. 🚨 嵌入模型 (Embedder) 配置缺失
- **隐患**：当前代码显式跳过了 `embedder` 配置，依赖 Mem0 默认行为。
- **后果**：在使用国产模型（如豆包/系统级代理）时，Mem0 默认会尝试连接 OpenAI 官方 API，导致使用国产 API Key 出现 401 或因 BaseURL 不匹配导致 404。
- **治理**：必须在 `config_dict` 中显式指定 `embedder` 的 `provider`, `model` 和 `openai_base_url`。

### 2. 🐒 Monkeypatch 的健壮性
- **隐患**：当前仅拦截了 `generate_response`。
- **后果**：豆包不仅不支持 `response_format={"type": "json_object"}`，其 Embedding 返回结构或并发限制也可能与 OpenAI 略有差异。
- **治理**：扩展 Patch 层，统一处理 OpenAI 兼容层在豆包环境下的共性问题（如特定 Header 或 Response 结构修正）。

### 3. 📉 降级逻辑的“热备”一致性
- **隐患**：当云端服务（如 Qdrant 或 LLM）不可用时，系统会切回本地 Chroma。
- **后果**：如果切换发生在运行时，之前的短期记忆可能丢失。
- **治理**：在初始化阶段增加自检（Self-Test），确保路径通顺，同时在 fallback 时记录明确的状态位。

### 4. 🔗 零硬编码配置扩展
- **隐患**：`EpisodicMemoryManager` 内部仍有一些硬编码的路径和策略。
- **治理**：将 Mem0 相关的 `vector_store` 类型、路径等参数提取至 `ConfigManager`。

## [M] 技术方案建模 (Modeling)

### 数据结构定义
```python
@dataclass
class MemoryConfig:
    # ... 现有配置 ...
    episodic_provider: str = "mem0"
    episodic_vector_store: str = "qdrant" # 或 chroma
    episodic_db_path: str = "./data/mem0_qdrant"
```

### 接口契约
- `EpisodicMemoryManager.add_interaction(text, metadata)`: 异步安全记录
- `EpisodicMemoryManager.get_structured_context(query)`: 增强 RAG 的标准输出

## [A] 对抗性审查 (Adversarial)

- **问**：如果 `EMBEDDING_MODEL` 没配置怎么办？
- **答**：系统将抛出明确警告并强制 fallback 到本地，绝不静默失败。
- **问**：Monkeypatch 会不会影响性能？
- **答**：Patch 只做简单的字典检查和移除，消耗在纳秒级，远小于网络延迟。

## [D] 开发规约 (Development Rules)
- 遵循逐行中文注释。
- 使用 `ConfigManager` 获取所有参数。
- 严禁 TODO。
