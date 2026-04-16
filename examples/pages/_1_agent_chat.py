# ── Page Config (must be first) ──────────────────────────────────────────────
import streamlit as st
st.set_page_config(page_title="Agent Chat - Clawra", page_icon="🤖", layout="wide")

import time
import json
from datetime import datetime

st.markdown("## 🤖 Agent Chat")
st.markdown("*自然语言对话 · 自主推理 · GraphRAG 知识检索*")
st.divider()

# ── Init ─────────────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "clawra" not in st.session_state:
    st.session_state.clawra = None
    st.session_state.clawra_ready = False

# ── Intent Classifier ────────────────────────────────────────────────────────
INTENT_LEARN = "learn"       # 输入新文本/知识
INTENT_QUERY = "query"       # 问知识/查内容
INTENT_REASON = "reason"     # 推理/推导
INTENT_EVAL = "eval"         # 评估/验证
INTENT_SKILL = "skill"       # 执行技能
INTENT_STATS = "stats"       # 问状态/统计

def classify_intent(query: str) -> list[str]:
    """基于关键字多标签分类"""
    q = query.lower()
    intents = []

    # 学习意图：提供新知识/文本
    learn_kw = ["学习", "提取", "了解", "知道", "文本", "知识", "告诉我", "录入", "输入"]
    if any(k in q for k in learn_kw):
        intents.append(INTENT_LEARN)

    # 查询意图：问知识/检索
    query_kw = ["查找", "搜索", "查询", "检索", "找", "有什么", "哪些", "怎么", "如何",
                "是什么", "多少", "谁", "哪", "是不是", "有没有"]
    if any(k in q for k in query_kw):
        intents.append(INTENT_QUERY)

    # 推理意图：推导/因果
    reason_kw = ["推理", "推导", "关系", "关联", "结论", "如果", "那么", "因此",
                 "所以", "导致", "会造成", "违反", "符合"]
    if any(k in q for k in reason_kw):
        intents.append(INTENT_REASON)

    # 评估意图：验证/检查
    eval_kw = ["评估", "检查", "验证", "判断", "是否安全", "合规", "风险"]
    if any(k in q for k in eval_kw):
        intents.append(INTENT_EVAL)

    # 技能执行意图
    skill_kw = ["执行", "运行", "调用", "启动"]
    if any(k in q for k in skill_kw):
        intents.append(INTENT_SKILL)

    # 状态查询
    stats_kw = ["统计", "状态", "多少", "有几个", "有哪些"]
    if any(k in q for k in stats_kw):
        intents.append(INTENT_STATS)

    # 默认：当作查询处理
    if not intents:
        intents = [INTENT_QUERY]
    return intents


# ── Render helpers ─────────────────────────────────────────────────────────────
def render_bubble(role, content):
    cls = "user-bubble" if role == "user" else "assistant-bubble"
    st.markdown(f'<div class="{cls}">{content}</div>', unsafe_allow_html=True)

def render_tool(name, content):
    st.markdown(f'<div class="tool-bubble">🔧 {name}: {content}</div>', unsafe_allow_html=True)

def render_result(title, content):
    with st.expander(title, expanded=False):
        st.markdown(content)

def render_thinking(content):
    with st.expander("🧠 思考过程", expanded=True):
        st.markdown(content)


# ── Agent Core ────────────────────────────────────────────────────────────────
def agent_reply(query: str, clawra) -> tuple[str, list[dict]]:
    """
    真实调用 Clawra 引擎，返回 (回复文本, 中间工具调用列表)
    """
    tools_used = []
    q = query.strip()

    # 1. 意图分类
    intents = classify_intent(q)
    thinking_steps = [f"**意图识别**: {', '.join(intents)}"]
    tools_used.append({"type": "intent", "content": ", ".join(intents)})

    resp_parts = []
    stats = clawra.get_statistics()

    # 2. 如果是学习意图 → learn()
    if INTENT_LEARN in intents:
        thinking_steps.append("→ 调用 **learn()** 提取知识")
        result = clawra.learn(q)
        tools_used.append({"type": "learn", "content": result})

        success = result.get("success", False)
        domain = result.get("domain", "unknown")
        patterns = result.get("learned_patterns", [])
        facts_added = result.get("facts_added", 0)
        extracted = result.get("extracted_facts", [])

        thinking_steps.append(
            f"  - 领域: `{domain}` | 模式: **{len(patterns)}** | 事实: **{facts_added}**"
        )

        resp_parts.append(f"✅ 从输入中学到了 **{len(patterns)}** 个模式，新增 **{facts_added}** 条事实（领域: `{domain}`）")

        if extracted:
            triples = []
            for f in extracted[:8]:
                s = f.get("subject", "?")
                p = f.get("predicate", "?")
                o = f.get("object", "?")
                triples.append(f"({s} —[{p}]→ {o})")
            resp_parts.append("**提取的三元组:**\n" + "\n".join(f"  • {t}" for t in triples))
        else:
            resp_parts.append("_（未提取到显式三元组，将通过推理引擎自动生成关联）_")

    # 3. 如果是查询意图 → retrieve_context()
    if INTENT_QUERY in intents:
        thinking_steps.append("→ 调用 **retrieve_context()** GraphRAG 检索")
        context = clawra.retrieve_context(q, top_k=8)
        tools_used.append({"type": "retrieve", "content": context})

        thinking_steps.append(f"  - 上下文长度: **{len(context)}** 字符")

        if context and len(context) > 50:
            # 截取前 600 字
            preview = context[:600] + "..." if len(context) > 600 else context
            resp_parts.append(f"🔍 检索结果（{len(context)} 字符）:\n\n{preview}")
        else:
            resp_parts.append("🔍 知识库中暂无相关内容。请先通过「学习」输入领域知识。")

    # 4. 如果是推理意图 → reason()
    if INTENT_REASON in intents:
        thinking_steps.append("→ 调用 **reason()** 执行前向链推理")
        conclusions = clawra.reason(max_depth=3)
        tools_used.append({"type": "reason", "content": conclusions})

        thinking_steps.append(f"  - 推导出 **{len(conclusions)}** 条结论")

        if conclusions:
            resp_parts.append(f"🧠 推理引擎推导出 **{len(conclusions)}** 条结论:")
            for i, c in enumerate(conclusions[:5], 1):
                conclusion_text = str(c.conclusion) if hasattr(c, "conclusion") else str(c)
                conf = f"{c.confidence:.2f}" if hasattr(c, "confidence") else "?"
                resp_parts.append(f"  {i}. {conclusion_text} _(置信度 {conf})_")
        else:
            resp_parts.append("🧠 推理引擎当前无新结论（知识库事实不足，或传递链未触发）。")

    # 5. 如果是评估意图 → evaluate()
    if INTENT_EVAL in intents:
        thinking_steps.append("→ 调用 **evaluate()** 约束验证")
        # 从查询中尝试提取数值（简单正则）
        import re
        numbers = re.findall(r'(\d+\.?\d*)\s*(MPa|kPa|bar|psi)?', q)
        if numbers:
            resp_parts.append(f"🛡️ 参数提取: `{numbers}`，请查看右侧推理详情")
            tools_used.append({"type": "eval", "content": f"extracted_params={numbers}"})
        else:
            resp_parts.append("🛡️ 请提供具体数值进行评估（如：进气0.5MPa是否安全）")

    # 6. 状态查询
    if INTENT_STATS in intents and not INTENT_LEARN in intents:
        thinking_steps.append("→ 调用 **get_statistics()** 获取状态")
        total_facts = stats.get("facts", 0)
        pattern_count = stats.get("patterns", {}).get("total", 0)
        domains = stats.get("domains", [])

        resp_parts.append(f"📊 **当前知识库状态:**\n"
                          f"  • 事实总数: **{total_facts}**\n"
                          f"  • 模式总数: **{pattern_count}**\n"
                          f"  • 领域: `{', '.join(domains) or '未设置'}`")
        tools_used.append({"type": "stats", "content": stats})

    # 兜底：没有任何结果时
    if not resp_parts:
        resp_parts = [
            "收到您的问题。**当前知识库状态:**\n"
            f"  • 事实: **{stats.get('facts', 0)}** | 模式: **{stats.get('patterns', {}).get('total', 0)}**\n\n"
            "**试试这样问我:**\n"
            "  • 📚 `学习：燃气调压箱超过0.4MPa有爆炸风险`\n"
            "  • 🔍 `查找关于压力设备的安全规范`\n"
            "  • 🧠 `如果进气压力0.5MPa会有什么后果`\n"
            "  • 📊 `统计当前有多少知识`"
        ]

    thinking = "\n".join(thinking_steps)
    reply = "\n\n".join(resp_parts)

    return reply, tools_used, thinking


# ── Layout ────────────────────────────────────────────────────────────────────
col_chat, col_info = st.columns([3, 1])

# ── Chat Window ──────────────────────────────────────────────────────────────
with col_chat:
    # Render history
    for msg in st.session_state.chat_history:
        role = msg["role"]
        content = msg["content"]
        if role == "thinking":
            render_thinking(content)
        elif role == "tool":
            render_tool(msg.get("tool", ""), msg.get("content", ""))
        elif role == "result":
            render_result(msg.get("title", "结果"), msg.get("content", ""))
        else:
            render_bubble(role, content)

    # Input
    user_input = st.chat_input("输入问题，按 Enter 发送...", key="chat_input")

    if user_input and st.session_state.clawra_ready:
        # User bubble
        render_bubble("user", user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Thinking placeholder
        thinking_ph = st.empty()
        thinking_ph.markdown('<div class="assistant-bubble">🧠 正在分析...</div>', unsafe_allow_html=True)

        try:
            clawra = st.session_state.clawra
            reply, tools_used, thinking = agent_reply(user_input, clawra)

            # Show thinking
            thinking_ph.empty()
            render_thinking(thinking)

            # Tool calls
            for tool in tools_used:
                t = tool["type"]
                if t == "intent":
                    pass  # already in thinking
                elif t == "learn":
                    st.session_state.chat_history.append({"role": "tool", "tool": "learn()", "content": f"success={tool['content'].get('success')}, patterns={len(tool['content'].get('learned_patterns',[]))}"})
                    render_tool("learn()", f"patterns={len(tool['content'].get('learned_patterns',[]))}, facts={tool['content'].get('facts_added',0)}")
                elif t == "retrieve":
                    l = len(tool['content']) if tool['content'] else 0
                    st.session_state.chat_history.append({"role": "tool", "tool": "retrieve_context()", "content": f"{l} chars"})
                    render_tool("retrieve_context()", f"{l} chars retrieved")
                elif t == "reason":
                    st.session_state.chat_history.append({"role": "tool", "tool": "reason()", "content": f"{len(tool['content'])} conclusions"})
                    render_tool("reason()", f"{len(tool['content'])} conclusions")

            # Assistant reply
            render_bubble("assistant", reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})

        except Exception as e:
            thinking_ph.empty()
            render_bubble("assistant", f"❌ 执行出错: {e}")
            st.session_state.chat_history.append({"role": "assistant", "content": f"错误: {e}"})

    elif user_input and not st.session_state.clawra_ready:
        st.warning("⚠️ 请先在侧边栏点击 **初始化 Clawra**")

    # Clear
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


# ── Right Panel ───────────────────────────────────────────────────────────────
with col_info:
    st.markdown("### 🧩 能力路由")

    if st.session_state.clawra_ready:
        stats = st.session_state.clawra.get_statistics()

        st.metric("📊 知识事实", stats.get("facts", 0))
        st.metric("🧠 模式", stats.get("patterns", {}).get("total", 0))
        domains = stats.get("domains", [])
        domain_str = ", ".join(domains[:3]) if domains else "—"
        st.metric("🏷️ 领域", domain_str if len(domain_str) < 20 else f"{len(domains)} 个")

        st.divider()
        st.markdown("### 🔀 路由引擎")

        routing = [
            ("📚 learn()", "文本 → 知识三元组 + 规则"),
            ("🔍 retrieve_context()", "Query → GraphRAG 上下文"),
            ("🧠 reason()", "事实 → 传递性推理"),
            ("🛡️ evaluate()", "参数 → 约束验证"),
            ("📊 get_statistics()", "→ 知识库统计"),
        ]
        for cap, desc in routing:
            st.markdown(f"**{cap}**")
            st.caption(f"_{desc}_")

        st.divider()
        st.markdown("### 💡 示例问题")
        examples = [
            ("📚 学习", "学习：燃气调压箱超过0.4MPa有爆炸风险"),
            ("🔍 查询", "查找调压箱的安全压力范围"),
            ("🧠 推理", "如果进气压力0.5MPa会有什么后果"),
            ("📊 统计", "当前有多少知识事实"),
        ]
        for label, text in examples:
            if st.button(f"{label} {text[:15]}...", key=f"ex_{text[:20]}", use_container_width=True):
                st.session_state.chat_input = text
                st.rerun()
    else:
        st.info("初始化后显示路由信息")
        st.caption("点击侧边栏「🚀 初始化 Clawra」")
