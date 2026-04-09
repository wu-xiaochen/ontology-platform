# BMAD Iteration 2 Design Spec

## 1. Abstract Lock Mechanism
To achieve Micro-service/Distributed readiness, `SemanticMemory` and `EpisodicMemory` will no longer hardcode `threading.Lock()`. We introduce a Lock interface that can be overridden:

```python
class LockProvider:
    def __enter__(self): pass
    def __exit__(self, exc_type, exc_val, exc_tb): pass

class ThreadLockProvider(LockProvider):
    # wrapper around threading.Lock()
```

## 2. Text Chunking for `LLMKnowledgeExtractor`
To extract from long manuals and Pdfs safely, we remove the `text[:3000]` hard slice. 
We introduce chunking boundaries using punctuation (`\n\n`, `. `).

**Algorithm:**
- Split raw text into sentences/paragraphs.
- Accumulate chunks until `max_text_length_per_chunk` (e.g., 2000 chars) is approached.
- Send each chunk to LLM.
- **Merge Logic**:
  - `entities`: Deduplicate by `name`.
  - `relations`: Deduplicate by `(subject, predicate, object)`.
  - `rules`: Deduplicate by `condition + action`.

## 3. RLHF Optimization Cycle
`EpisodicMemory` acts as our DPO dataset store. We introduce `export_rlhf_dataset(filepath)`.
**Format generated**:
```jsonl
{"messages": [{"role": "system", "content": "You are Clawra."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```
Data is pulled directly from the agent's Trace when `reward > 0` or a `correction` is applied.
