# Show HN: ontology-platform – The first agent framework with a built-in bullshit detector

**Submitted by:** u/wu_xiaochen  
**Project:** https://github.com/wu-xiaochen/ontology-platform  
**Live Demo:** https://colab.research.google.com/github/wu-xiaochen/ontology-platform/blob/main/ontology_platform_quickstart.ipynb

---

## The Problem

I kept seeing AI agents hallucinate with complete confidence. Whether it's a customer support bot giving wrong answers, or a research assistant making up citations—the problem isn't that agents lack information. **The problem is they don't know when they're uncertain.**

Traditional frameworks (LangChain, Mem0, RAG systems) give agents memory and retrieval, but no metacognition. They're like a person who never says "I don't know."

## What I Built

**ontology-platform** is an agent framework that adds:

1. **Confidence Scoring** - Every answer comes with a confidence level (0.0 to 1.0)
2. **Reasoning Traces** - You can see exactly how the agent reached its conclusion
3. **Knowledge Boundaries** - The agent explicitly flags when it's outside its expertise
4. **Runtime Learning** - Add new rules instantly without retraining

### Example

```python
from ontology import Agent

agent = Agent()

result = agent.ask("Should we trust this supplier?")

print(f"Confidence: {result.confidence}")  
# → 0.89 (CONFIRMED) or 0.45 (SPECULATIVE)

print(f"Reasoning:")
for step in result.reasoning_chain:
    print(f"  • {step}")
# Shows the full logical chain

if result.confidence < 0.6:
    print(result.verdict)  
    # → "I don't have enough information. Need more data."
```

## How It's Different

| Feature | LangChain | Mem0 | ontology-platform |
|---------|-----------|------|-------------------|
| Memory | ❌ | ✅ | ✅ |
| Reasoning | ❌ | ❌ | ✅ |
| Confidence scores | ❌ | ❌ | ✅ |
| Knows when uncertain | ❌ | ❌ | ✅ |

Think of it as **RAG + reasoning engine + metacognition layer**.

## Technical Details

- **Storage:** RDF/OWL ontologies (structured knowledge graphs), not just vectors
- **Reasoning:** Forward/backward chaining with confidence propagation
- **Size:** ~5MB (much lighter than vector-based frameworks)
- **Deployment:** Fully local, no cloud dependency (enterprise-friendly)

## Try It

```bash
pip install ontology-platform
```

Or play with the [Colab demo](https://colab.research.google.com/github/wu-xiaochen/ontology-platform/blob/main/ontology_platform_quickstart.ipynb) (5 minutes).

## Questions for the Community

1. **Has anyone else tackled hallucination at the reasoning layer?** Most solutions seem to focus on better retrieval or fine-tuning, but not on making agents aware of their own uncertainty.

2. **What use cases would benefit most from confidence-aware agents?** I've been focusing on supply chain risk assessment, but curious about other domains.

3. **Trade-offs:** Structured ontologies require more upfront modeling than pure vector search. Is this worth it for your use case?

## Roadmap

- [ ] TypeScript/JavaScript SDK (currently Python only)
- [ ] Pre-built domain ontologies (healthcare, finance, legal)
- [ ] Integration with popular LLM providers (OpenAI, Anthropic, local models)
- [ ] Visual reasoning trace explorer

## Feedback Welcome

This is my first major open-source project. Would love honest feedback on:
- API design (is it intuitive?)
- Documentation (what's confusing?)
- Use cases (what would you build with this?)

GitHub: https://github.com/wu-xiaochen/ontology-platform

---

**Edit 1:** Thanks for the warm welcome! Answering questions as fast as I can.

**Edit 2:** Someone asked about comparison with probabilistic programming—great point! I'll add a section to the docs covering this.
