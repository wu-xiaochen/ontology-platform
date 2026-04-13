"""
Episodic Enhanced Memory - 基于 Mem0 的长效记忆增强层
"""
import os
import logging
from typing import List, Dict, Any, Optional
from mem0 import Memory
from mem0.llms.openai import OpenAILLM
from ..utils.config import get_config

logger = logging.getLogger(__name__)

# --- v5.0 Hardening: Monkeypatch Mem0 to fix Doubao compatibility ---
# Doubao 不支持 response_format={"type": "json_object"}，需要拦截并移除
_original_generate = OpenAILLM.generate_response

def _patched_generate(self, messages, response_format=None, **kwargs):
    # 如果检测到 json_object 模式，静默移除以兼容国产大模型
    if response_format and isinstance(response_format, dict) and response_format.get("type") == "json_object":
        return _original_generate(self, messages, response_format=None, **kwargs)
    return _original_generate(self, messages, response_format=response_format, **kwargs)

OpenAILLM.generate_response = _patched_generate
# -----------------------------------------------------------------

class EpisodicMemoryManager:
    """
    长效情节记忆管理器
    
    集成 Mem0 实现：
    1. 跨会话的用户偏好记忆
    2. 交互上下文的语义沉淀
    3. 意图感知的知识检索增强
    """
    
    def __init__(self, user_id: str = "default_user"):
        self.config = get_config()
        self.user_id = user_id
        
        # --- v5.0 Hardening: Self-repairing initialization ---
        # 核心硬化：显式指定嵌入模型 (Embedder) 以兼容国产大模型 API
        try:
            # 获取数据存储路径，确保目录存在以供 Qdrant 本地模式使用
            memory_path = os.path.join(self.config.app.data_dir, "mem0_qdrant")
            os.makedirs(memory_path, exist_ok=True) # 创建数据目录
            
            # 构造 Mem0 统一配置字典，遵循零硬编码原则从 ConfigManager 读取
            config_dict = {
                "vector_store": { # 向量数据库配置
                    "provider": "qdrant", 
                    "config": {"path": memory_path} # 本地持久化路径
                },
                "llm": { # 语言模型配置 (用于记忆总结与提取)
                    "provider": "openai", # 使用 OpenAI 兼容接口
                    "config": {
                        "model": self.config.llm.model, # 模型 ID (如 doubao-seed-...)
                        "api_key": self.config.llm.api_key, # 访问密钥
                        "openai_base_url": self.config.llm.base_url # 兼容层 BaseURL
                    }
                },
                "embedder": { # 嵌入模型配置 (关键硬化项)
                    "provider": "openai", # 使用 OpenAI 兼容接口进行向量化
                    "config": {
                        "model": self.config.llm.embedding_model, # 显式指定向量模型 ID
                        "api_key": self.config.llm.api_key, # 复用密钥
                        "openai_base_url": self.config.llm.embedding_base_url # 指定向量服务 BaseURL
                    }
                },
                "version": "v1.1" # 锁定 Mem0 配置协议版本
            }
            
            # 调用 Mem0 工厂方法初始化实例
            self.memory = Memory.from_config(config_dict)
            logger.info(f"Mem0 情节记忆层初始化成功 (Embedder: {self.config.llm.embedding_model})")
        except Exception as e:
            logger.warning(f"Mem0 初始化失败，启用内置 Chroma 降级方案: {e}")
            from .vector_adapter import ChromaMemory
            self.memory = ChromaMemory(collection_name="episodic_fallback")
            self._is_fallback = True

    def add_interaction(self, text: str, metadata: Optional[Dict] = None):
        """记录一次交互"""
        if not self.memory: return
        try:
            if hasattr(self, '_is_fallback'):
                from .vector_adapter import Document
                self.memory.add_documents([Document(content=text, metadata=metadata or {})])
            else:
                self.memory.add(text, user_id=self.user_id, metadata=metadata)
        except Exception as e:
            # v5.0 Hardening: 如果在运行时发现模型不存在 (404)，立即切换到本地热备模式
            if "404" in str(e) or "Not Found" in str(e):
                logger.warning(f"检测到云端记忆服务模型不匹配，自动切入本地内联热备存储...")
                from .vector_adapter import ChromaMemory
                self.memory = ChromaMemory(collection_name="episodic_hot_fallback")
                self._is_fallback = True
                self.add_interaction(text, metadata) # 迁移重试
            else:
                logger.error(f"存入情节记忆失败: {e}")

    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索历史记忆"""
        if not self.memory: return []
        try:
            if hasattr(self, '_is_fallback'):
                results = self.memory.similarity_search(query, top_k=limit)
                return [{"text": r.content} for r in results]
            return self.memory.search(query, user_id=self.user_id, limit=limit)
        except Exception as e:
            logger.error(f"搜索情节记忆失败: {e}")
            return []

    def get_structured_context(self, query: str) -> str:
        """获取结构化的背景语境，用于增强 RAG"""
        memories = self.search_memories(query)
        if not memories:
            return ""
            
        context = "\n[从长效记忆中发现的相关背景]:\n"
        for m in memories:
            content = m.get("text", m.get("memory", ""))
            context += f"- {content}\n"
        return context
