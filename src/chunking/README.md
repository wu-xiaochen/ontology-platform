# Chunking 模块 (Hierarchical Context Chunking)

本目录提供智能文档分块功能，解决长文档嵌入溢出问题，保留跨章节逻辑关系。

## 📁 文件结构

```
src/chunking/
├── hierarchical.py   # 层次化文档分块器实现
└── __init__.py       # 模块导出
```

## 🚀 核心功能

### HierarchicalChunker - 层次化文档分块器

**解决的问题**:
- 长文档超过 LLM max_tokens 限制
- 简单按 token 截断破坏语义完整性
- 跨章节逻辑关系丢失

**核心特性**:
- ✅ 基于文档标题层级智能分块
- ✅ 自动适配不同 LLM 的上下文限制
- ✅ 保留章节间重叠上下文（overlap）
- ✅ 保持语义完整性

### 支持的主要 LLM 模型

| 模型 | 上下文限制 | 实际处理限制 (80%) |
|------|-----------|------------------|
| gpt-4 | 8,192 | 6,553 |
| gpt-4-turbo | 128,000 | 102,400 |
| gpt-3.5-turbo | 16,385 | 13,108 |
| llama3.1 | 8,192 | 6,553 |
| llama3 | 8,192 | 6,553 |
| mixtral | 32,000 | 25,600 |

## 📖 使用示例

### 基础用法

```python
from ontology_platform.chunking import HierarchicalChunker

# 创建分块器（自动适配 GPT-4）
chunker = HierarchicalChunker(
    max_tokens=4096,
    overlap_tokens=256
)

# 分块长文档
chunks = chunker.chunk(long_document)

# 处理每个块
for chunk in chunks:
    print(f"Level: {chunk.level}")
    print(f"Heading: {chunk.heading}")
    print(f"Tokens: {chunker.estimate_tokens(chunk.text)}")
    print(f"Content: {chunk.text[:100]}...")
```

### 针对不同 LLM 模型

```python
# 为 Llama 3.1 优化
llama_chunker = HierarchicalChunker(
    llm_model="llama3.1",  # 自动设置为 8192 tokens
    overlap_tokens=512
)

# 为 GPT-4 Turbo 优化（超长上下文）
turbo_chunker = HierarchicalChunker(
    llm_model="gpt-4-turbo",  # 支持 128K tokens
    overlap_tokens=1024
)
```

### 自定义分块参数

```python
chunker = HierarchicalChunker(
    max_tokens=2048,        # 自定义 token 限制
    overlap_tokens=128,     # 章节间重叠
    llm_model="default"
)
```

## 📊 数据模型

### Chunk - 文档块

```python
@dataclass
class Chunk:
    text: str                    # 块内容
    start_offset: int            # 起始位置
    end_offset: int              # 结束位置
    level: str                   # 层级：section/subsection/paragraph
    heading: Optional[str]       # 标题
    metadata: Dict[str, Any]     # 元数据
```

### DocumentStructure - 文档结构

```python
@dataclass 
class DocumentStructure:
    title: str                       # 文档标题
    headings: List[Dict[str, Any]]   # 标题列表
    sections: List[Dict[str, Any]]   # 章节列表
```

## 🔧 核心方法

### `chunk(document: str) -> List[Chunk]`

将文档按层次结构分块。

**参数**:
- `document`: 要分块的完整文档文本

**返回**:
- `List[Chunk]`: 分块后的文档块列表

**示例**:
```python
chunks = chunker.chunk("""
# 知识图谱简介

## 什么是知识图谱
知识图谱是一种...

## 应用场景
知识图谱应用于...
""")

# 输出:
# Chunk 1: level="section", heading="什么是知识图谱"
# Chunk 2: level="section", heading="应用场景"
```

### `estimate_tokens(text: str) -> int`

估算文本的 token 数量。

**说明**: 使用简化估算（1 token ≈ 0.75 词）

**示例**:
```python
tokens = chunker.estimate_tokens("This is a test document.")
print(tokens)  # 输出：~8 tokens
```

## 🎯 应用场景

### 1. RAG 系统文档处理

```python
# 将长文档分块后嵌入
chunks = chunker.chunk(manual_document)
for chunk in chunks:
    embedding = embed(chunk.text)
    store_in_vector_db(embedding, chunk.text)
```

### 2. 长文档问答

```python
# 分块后逐块问答，合并结果
chunks = chunker.chunk(research_paper)
answers = []
for chunk in chunks:
    answer = llm.query(chunk.text, question)
    answers.append(answer)
final_answer = merge_answers(answers)
```

### 3. 文档摘要生成

```python
# 分块摘要后汇总
chunks = chunker.chunk(long_report)
summaries = []
for chunk in chunks:
    summary = llm.summarize(chunk.text)
    summaries.append(f"{chunk.heading}: {summary}")
final_summary = "\n".join(summaries)
```

## 📈 性能优化

### 重叠策略（Overlap）

- **推荐值**: 256-512 tokens
- **作用**: 保持跨块上下文连贯性
- **代价**: 轻微增加总 token 数

### 实际处理限制

分块器自动将 max_tokens 的 80% 作为实际限制，预留 20% 给 LLM 生成空间。

```python
# 设置 max_tokens=4096
# 实际分块限制 = 4096 * 0.8 = 3,276 tokens
# 剩余 820 tokens 用于 LLM 生成回答
```

## 🔗 相关模块

- [Memory 模块](../memory/README.md) - 记忆治理
- [API 模块](../api/README.md) - API 接口
- [Ontology 模块](../ontology/README.md) - 本体论核心

## 📚 参考资料

- [LLM Context Window Limits](https://platform.openai.com/docs/models/gpt-4-turbo-and-gpt-4)
- [Document Chunking Strategies](https://langchain.com/docs/modules/data_connection/document_transformers/)
