"""
分层分块器测试 (Hierarchical Chunker Tests)

测试文档分块功能的正确性和性能。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from ontology_platform.chunking import HierarchicalChunker, Chunk


class TestHierarchicalChunker:
    """测试 HierarchicalChunker 类"""
    
    def test_initialization(self):
        """测试初始化"""
        chunker = HierarchicalChunker(max_tokens=4096, overlap_tokens=256)
        
        assert chunker.max_tokens == 4096
        assert chunker.overlap_tokens == 256
        assert chunker.llm_model == "default"
    
    def test_llm_model_limits(self):
        """测试不同 LLM 模型的上下文限制"""
        # 测试 GPT-4
        chunker_gpt4 = HierarchicalChunker(llm_model="gpt-4")
        assert chunker_gpt4._limit == 8192
        
        # 测试 GPT-4 Turbo
        chunker_turbo = HierarchicalChunker(llm_model="gpt-4-turbo")
        assert chunker_turbo._limit == 128000
        
        # 测试 Llama 3.1
        chunker_llama = HierarchicalChunker(llm_model="llama3.1")
        assert chunker_llama._limit == 8192
        
        # 测试默认模型
        chunker_default = HierarchicalChunker(llm_model="unknown_model")
        assert chunker_default._limit == 4096
    
    def test_effective_limit_calculation(self):
        """测试实际处理限制计算（80% 规则）"""
        chunker = HierarchicalChunker(max_tokens=4096)
        
        # 实际限制应该是 80%
        expected_limit = int(4096 * 0.8)
        assert chunker._effective_limit == expected_limit
    
    def test_token_estimation(self):
        """测试 token 估算"""
        chunker = HierarchicalChunker()
        
        # 简单文本估算
        text = "This is a test document with some words."
        tokens = chunker.estimate_tokens(text)
        
        # 应该有合理的 token 数
        assert tokens > 0
        assert isinstance(tokens, int)
        
        # 更长文本应该有更多 token
        long_text = "This is a much longer document with many more words. " * 10
        long_tokens = chunker.estimate_tokens(long_text)
        assert long_tokens > tokens
    
    def test_chunk_simple_document(self):
        """测试简单文档分块"""
        chunker = HierarchicalChunker(max_tokens=1000)
        
        document = """
# 标题

这是一段简单的文本内容。

## 子标题

这是子标题下的内容。
"""
        
        chunks = chunker.chunk(document)
        
        # 应该至少生成一个块
        assert len(chunks) >= 1
        
        # 每个块应该有正确属性
        for chunk in chunks:
            assert isinstance(chunk, Chunk)
            assert hasattr(chunk, 'text')
            assert hasattr(chunk, 'level')
            assert hasattr(chunk, 'start_offset')
            assert hasattr(chunk, 'end_offset')
    
    def test_chunk_with_overlap(self):
        """测试重叠分块"""
        chunker = HierarchicalChunker(
            max_tokens=500,
            overlap_tokens=50
        )
        
        # 创建足够长的文档
        document = "\n".join([f"段落 {i}: " + "x" * 100 for i in range(10)])
        
        chunks = chunker.chunk(document)
        
        # 应该有多个块
        assert len(chunks) > 1
        
        # 检查重叠（相邻块应该有内容重叠）
        if len(chunks) >= 2:
            # 第二个块的开始应该包含第一个块的部分内容
            assert chunks[1].start_offset < chunks[0].end_offset
    
    def test_chunk_preserves_structure(self):
        """测试分块保留文档结构"""
        chunker = HierarchicalChunker(max_tokens=2000)
        
        document = """
# 主标题

## 章节 1
章节 1 的内容。

## 章节 2
章节 2 的内容。

### 子章节 2.1
子章节的内容。
"""
        
        chunks = chunker.chunk(document)
        
        # 检查是否有标题信息
        chunks_with_headings = [c for c in chunks if c.heading]
        assert len(chunks_with_headings) > 0
        
        # 检查层级信息
        levels = [c.level for c in chunks]
        assert any(level in ['section', 'subsection', 'paragraph'] for level in levels)
    
    def test_empty_document(self):
        """测试空文档处理"""
        chunker = HierarchicalChunker()
        
        # 空字符串
        chunks = chunker.chunk("")
        assert len(chunks) == 0 or (len(chunks) == 1 and not chunks[0].text.strip())
        
        # 只有空白
        chunks = chunker.chunk("   \n\n   ")
        assert len(chunks) == 0 or (len(chunks) == 1 and not chunks[0].text.strip())
    
    def test_very_long_document(self):
        """测试超长文档分块"""
        chunker = HierarchicalChunker(max_tokens=500)
        
        # 创建很长的文档
        document = "\n".join([f"段落 {i}: " + "This is some content. " * 10 for i in range(100)])
        
        chunks = chunker.chunk(document)
        
        # 应该分成多个块
        assert len(chunks) > 1
        
        # 每个块的 token 数应该在限制内
        for chunk in chunks:
            tokens = chunker.estimate_tokens(chunk.text)
            assert tokens <= chunker.max_tokens * 1.2  # 允许 20% 容差


class TestChunkDataclass:
    """测试 Chunk 数据类"""
    
    def test_chunk_creation(self):
        """测试 Chunk 创建"""
        chunk = Chunk(
            text="Test content",
            start_offset=0,
            end_offset=12,
            level="section",
            heading="Test Heading",
            metadata={"key": "value"}
        )
        
        assert chunk.text == "Test content"
        assert chunk.start_offset == 0
        assert chunk.end_offset == 12
        assert chunk.level == "section"
        assert chunk.heading == "Test Heading"
        assert chunk.metadata == {"key": "value"}
    
    def test_chunk_default_values(self):
        """测试 Chunk 默认值"""
        chunk = Chunk(
            text="Test",
            start_offset=0,
            end_offset=4,
            level="paragraph"
        )
        
        # 可选字段应该有默认值
        assert chunk.heading is None
        assert chunk.metadata is None


class TestPerformance:
    """性能测试"""
    
    def test_chunking_performance(self):
        """测试分块性能"""
        import time
        
        chunker = HierarchicalChunker(max_tokens=1000)
        
        # 创建中等大小文档
        document = "\n".join([f"章节 {i}:\n" + "Content here. " * 20 for i in range(50)])
        
        start_time = time.time()
        chunks = chunker.chunk(document)
        elapsed = time.time() - start_time
        
        # 应该在合理时间内完成（1 秒）
        assert elapsed < 1.0, f"分块耗时 {elapsed:.2f}秒，超过预期"
        
        # 应该有输出
        assert len(chunks) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
