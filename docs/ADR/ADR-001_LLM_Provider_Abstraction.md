# ADR-001: LLM Provider Abstraction Layer

> 状态: **已通过** | 日期: 2026-04-05

---

## 背景

Clawra 需要支持多种 LLM 提供商（OpenAI、Claude、Ollama、MiniMax），且需要能够灵活切换。同时需要：
- 支持同步/异步调用
- 自动重试与降级
- 请求超时控制
- 成本追踪

---

## 决策

### 方案选择

| 方案 | 优点 | 缺点 |
|------|------|------|
| **A. 抽象 Provider 接口** | 灵活、可扩展、统一接口 | 需要维护抽象层 |
| B. 硬编码 OpenAI | 简单快速 | 锁定供应商 |
| C. 使用 LangChain | 生态完善 | 过重、定制性差 |

**选择：方案 A - 抽象 Provider 接口**

### 核心设计

```python
# src/llm/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMProvider(ABC):
    """LLM Provider 抽象基类"""

    @abstractmethod
    def chat(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.7,
        timeout: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """发送对话请求"""
        pass

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """获取文本嵌入"""
        pass

    def health_check(self) -> bool:
        """健康检查"""
        return True
```

```python
# src/llm/providers/openai.py
class OpenAIProvider(LLMProvider):
    """OpenAI Provider"""

    def __init__(self, api_key: str, base_url: str = None, **kwargs):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.default_model = "gpt-4"

    def chat(self, messages, model=None, temperature=0.7, timeout=30, **kwargs):
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            timeout=timeout
        )
        return {"content": response.choices[0].message.content}
```

---

## 后果

### 正面

- ✅ 支持任意 LLM 提供商（只需实现 `LLMProvider` 接口）
- ✅ 统一错误处理和重试逻辑
- ✅ 便于测试（Mock Provider）
- ✅ 便于成本追踪和监控

### 负面

- ❌ 增加一层抽象，稍微复杂
- ❌ 每个 Provider 需要单独维护

### 风险

- ⚠️ Provider 接口变更需要同步更新所有实现

---

## 实现清单

- [x] `src/llm/base.py` - 抽象基类
- [x] `src/llm/providers/openai.py` - OpenAI 实现
- [x] `src/llm/providers/anthropic.py` - Claude 实现
- [x] `src/llm/providers/ollama.py` - Ollama 实现
- [x] `src/llm/providers/minimax.py` - MiniMax 实现
- [x] `src/llm/client.py` - 统一客户端（自动选择 Provider）
- [x] `src/llm/router.py` - 降级路由逻辑

---

## 相关 ADR

- [ADR-003](./ADR-003_Evolution_Loop_Architecture.md) - Evolution Loop 中的 LLM 调用策略
