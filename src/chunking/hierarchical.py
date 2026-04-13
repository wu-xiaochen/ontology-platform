"""层次化文档分块器

实现基于文档结构的智能分块，保留语义完整性。
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re


@dataclass
class Chunk:
    """文档块"""
    text: str
    start_offset: int
    end_offset: int
    level: str  # section, subsection, paragraph
    heading: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass 
class DocumentStructure:
    """文档结构"""
    title: str
    headings: List[Dict[str, Any]]
    sections: List[Dict[str, Any]]


class HierarchicalChunker:
    """
    层次化文档分块器
    
    特性:
    - 自动识别文档标题层级
    - 智能分块，保持语义完整
    - 动态调整 max_tokens 适配不同 LLM
    
    示例:
        chunker = HierarchicalChunker(max_tokens=4096)
        chunks = chunker.chunk(long_document)
        for chunk in chunks:
            print(f"Level: {chunk.level}, Tokens: {len(chunk.text.split())}")
    """
    
    # 不同 LLM 的上下文限制
    LLM_LIMITS = {
        "gpt-4": 8192,
        "gpt-4-turbo": 128000,
        "gpt-3.5-turbo": 16385,
        "llama3.1": 8192,
        "llama3": 8192,
        "mixtral": 32000,
        "default": 4096,
    }
    
    def __init__(
        self, 
        max_tokens: int = 4096,
        overlap_tokens: int = 256,
        llm_model: str = "default"
    ):
        """
        初始化分块器
        
        Args:
            max_tokens: 最大 token 数
            overlap_tokens: 重叠 token 数（保持上下文连贯）
            llm_model: LLM 模型名称（用于自动适配限制）
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.llm_model = llm_model
        self._limit = self.LLM_LIMITS.get(llm_model, self.LLM_LIMITS["default"])
        # 实际处理限制设为 80% 以留出生成空间
        self._effective_limit = int(self._limit * 0.8)
    
    def estimate_tokens(self, text: str) -> int:
        """估算 token 数量（支持中英文混合）"""
        # 对于中文，简单按字符数估算（1字≈1.5-2 tokens，安全起见按 1.5 算）
        # 英文按 0.75 词/token 算
        words = text.split()
        if len(words) < len(text) / 5: # 启发式：如果空格很少，说明是中文为主
            return int(len(text) * 1.5)
        return int(len(words) / 0.75)
    
    def parse_structure(self, text: str) -> DocumentStructure:
        """
        解析文档结构，识别标题层级
        
        支持格式:
        - Markdown: # ## ### 
        - HTML: <h1> <h2> <h3>
        - 带数字: 1. 1.1 1.1.1
        """
        lines = text.split('\n')
        headings = []
        sections = []
        
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        html_pattern = r'<h([1-6])[^>]*>(.+)</h\1>'
        numbered_pattern = r'^(\d+(?:\.\d+)*)\s+(.+)$'
        
        for i, line in enumerate(lines):
            # Markdown 标题
            md_match = re.match(heading_pattern, line)
            if md_match:
                level = len(md_match.group(1))
                headings.append({
                    "level": level,
                    "text": md_match.group(2),
                    "line": i
                })
                continue
                
            # HTML 标题
            html_match = re.match(html_pattern, line, re.IGNORECASE)
            if html_match:
                headings.append({
                    "level": int(html_match.group(1)),
                    "text": html_match.group(2),
                    "line": i
                })
                continue
                
            # 数字标题
            num_match = re.match(numbered_pattern, line.strip())
            if num_match and i > 0:
                dot_count = num_match.group(1).count('.') + 1
                headings.append({
                    "level": dot_count,
                    "text": num_match.group(2),
                    "line": i
                })
        
        return DocumentStructure(
            title=headings[0]["text"] if headings else "Untitled",
            headings=headings,
            sections=sections
        )
    
    def chunk(self, text: str) -> List[Chunk]:
        """
        对文档进行层次化分块
        
        Args:
            text: 输入文档文本
            
        Returns:
            分块后的 Chunk 列表
        """
        structure = self.parse_structure(text)
        lines = text.split('\n')
        
        chunks = []
        current_chunk_text = []
        current_chunk_start = 0
        current_heading = None
        
        for i, line in enumerate(lines):
            # 检查是否为标题行
            is_heading = any(h["line"] == i for h in structure.headings)
            if is_heading:
                # 保存当前块
                if current_chunk_text:
                    chunk_text = '\n'.join(current_chunk_text)
                    if self.estimate_tokens(chunk_text) > 100:  # 忽略太短的块
                        chunks.append(Chunk(
                            text=chunk_text,
                            start_offset=current_chunk_start,
                            end_offset=i,
                            level="content",
                            heading=current_heading,
                            metadata={"lines": len(current_chunk_text)}
                        ))
                    current_chunk_text = []
                    current_chunk_start = i
                
                # 找到对应标题
                for h in structure.headings:
                    if h["line"] == i:
                        current_heading = h["text"]
                        break
                continue
            
            # 添加非标题行
            current_chunk_text.append(line)
            
            # 检查是否需要分块
            chunk_text = '\n'.join(current_chunk_text)
            if self.estimate_tokens(chunk_text) >= self._effective_limit:
                # 保存当前块
                chunks.append(Chunk(
                    text=chunk_text,
                    start_offset=current_chunk_start,
                    end_offset=i,
                    level="content",
                    heading=current_heading,
                    metadata={"lines": len(current_chunk_text)}
                ))
                # 保留最后 overlap_tokens 部分作为下一个块的开始
                if self.overlap_tokens > 0:
                    overlap_text = ' '.join(chunk_text.split()[-self.overlap_tokens:])
                    current_chunk_text = [overlap_text]
                    current_chunk_start = i - len(current_chunk_text) + 1
                else:
                    current_chunk_text = []
                    current_chunk_start = i + 1
        
        # 保存最后的块
        if current_chunk_text:
            chunk_text = '\n'.join(current_chunk_text)
            if self.estimate_tokens(chunk_text) > 100:
                chunks.append(Chunk(
                    text=chunk_text,
                    start_offset=current_chunk_start,
                    end_offset=len(lines),
                    level="content",
                    heading=current_heading,
                    metadata={"lines": len(current_chunk_text)}
                ))
        
        return chunks
    
    def chunk_by_paragraphs(self, text: str, min_tokens: int = 100) -> List[Chunk]:
        """
        简单的段落分块（备用方法）
        
        Args:
            text: 输入文本
            min_tokens: 最小 token 数
            
        Returns:
            Chunk 列表
        """
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_pos = 0
        
        for para in paragraphs:
            if not para.strip():
                continue
            para = para.strip()
            if self.estimate_tokens(para) < min_tokens:
                continue
            start = text.find(para, current_pos)
            chunks.append(Chunk(
                text=para,
                start_offset=start,
                end_offset=start + len(para),
                level="paragraph",
                metadata={}
            ))
            current_pos = start + len(para)
        
        return chunks
