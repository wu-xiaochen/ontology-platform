"""分层上下文分块模块 (Hierarchical Context Chunking)

本模块提供智能文档分块功能，解决长文档嵌入溢出问题。

核心特性:
- 基于文档结构的智能分块
- LLM max_tokens 自适应适配
- 保留跨章节逻辑关系

使用示例:
    from ontology_platform.chunking import HierarchicalChunker
    
    chunker = HierarchicalChunker(
        max_tokens=4096,
        overlap_tokens=256
    )
    chunks = chunker.chunk(document)
"""
from .hierarchical import HierarchicalChunker, Chunk, DocumentStructure

__all__ = [
    "HierarchicalChunker", 
    "Chunk",
    "DocumentStructure",
]
