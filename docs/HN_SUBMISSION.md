# Hacker News 投稿素材

## 投稿地址
https://news.ycombinator.com/submit

## 标题（选一个）
**Primary:**
Show HN: Clawra – AI agents that learn their own rules from text (no more prompt engineering)

**备选（更personal）：
I spent 2 years building with LangChain, then built my own framework – here's what I learned

## 正文（直接复制粘贴）

```
After 2 years with LangChain, I built my own AI agent framework
with a different premise: what if the AI learned rules from text?

The problem with LangChain isn't the orchestration (that part is great).
The problem is: every new rule, every constraint, every business logic
— you write it in a prompt. Forever.

Clawra ( https://github.com/wu-xiaochen/clawra-engine ) solves this
differently. You give it text. It learns.

Demo (no API key needed):
  git clone https://github.com/wu-xiaochen/clawra-engine.git
  cd clawra-engine
  pip install -e .
  python examples/demo_basic.py

What it does:
- Learns rules from natural language text automatically
- Enforces them via symbolic logic (not prompts)
- 8-stage evolution loop: AI gets smarter from its own mistakes
- GraphRAG hybrid retrieval
- AST-level math sandbox (LLM can't DoS you with exponential math)
- MCP server for Claude Code integration (3-line config)

Architecture: neurosymbolic fusion — LLM for understanding,
symbolic logic for what must never be violated.

433 tests, 10 runnable examples, MIT license.

Would love feedback from anyone who's felt the "prompt engineering
maintenance" pain I described.
```

## 注意事项
- 标题要包含 "Show HN:" 前缀
- 正文控制在 3-4 段，太长没人看
- 附上 repo 链接
- 最后用 "Would love feedback" 或类似语气收尾，HN用户喜欢谦逊的开场

## 投稿后
记得在 HN 帖子里评论互动，有人问问题要答
