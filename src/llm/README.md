# LLM Module

大语言模型集成模块，提供统一的 LLM 接口和缓存策略。

## 核心组件

### api.py
LLM API 统一接口：
- 支持多种 LLM 提供商（OpenAI, Anthropic, Local LLMs）
- 统一的请求/响应格式
- 错误处理和重试机制

### caching.py
缓存系统：
- 语义缓存（Semantic Cache）
- 精确匹配缓存
- 缓存失效策略

### cache_strategy.py
缓存策略：
- LRU（最近最少使用）
- TTL（生存时间）
- 基于相似度的缓存

### api/ 子目录
各 LLM 提供商的适配器：
- OpenAI 适配器
- Anthropic 适配器
- Local LLM 适配器（Ollama, LM Studio）

## 使用示例

```python
from src.llm.api import LLMClient
from src.llm.caching import SemanticCache

# 初始化
client = LLMClient(provider="openai", model="gpt-4")
cache = SemanticCache(threshold=0.85)

# 带缓存的调用
response = client.chat(
    messages=[{"role": "user", "content": "Hello"}],
    use_cache=True
)
```

## 支持的 LLM 提供商

| 提供商 | 状态 | 备注 |
|--------|------|------|
| OpenAI | ✅ | 完整支持 |
| Anthropic | ✅ | 完整支持 |
| Ollama | ✅ | 本地部署 |
| LM Studio | ✅ | 本地部署 |
| vLLM | 🚧 | 开发中 |

## 缓存策略

### 语义缓存
- 使用向量相似度匹配
- 阈值可配置（默认 0.85）
- 自动过期

### 精确缓存
- 完全相同的 prompt
- 永不过期
- 最高命中率

## 性能指标

- 缓存命中率：> 60%
- 响应时间：平均 < 200ms（缓存命中）
- 并发支持：100+ QPS

## 依赖

- openai >= 1.0.0
- anthropic >= 0.5.0
- chromadb >= 0.4.0
- tiktoken >= 0.5.0
