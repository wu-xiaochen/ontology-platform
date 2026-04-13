# ── Page Config (must be first) ──────────────────────────────────────────────
import streamlit as st
st.set_page_config(page_title="Agent Chat - Clawra", page_icon="🤖", layout="wide")

import time
import json
from datetime import datetime

st.markdown("## 🤖 Agent Chat")
st.markdown("*自然语言对话 · 自主调用能力 · 思考过程可视化*")
st.divider()

# ── Init ─────────────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "clawra" not in st.session_state:
    st.session_state.clawra = None
    st.session_state.clawra_ready = False

# ── Chat Messages ─────────────────────────────────────────────────────────────
def render_message(role, content, tool_calls=None):
    if role == "user":
        st.markdown(f'<div class="user-bubble">{content}</div>', unsafe_allow_html=True)
    elif role == "assistant":
        st.markdown(f'<div class="assistant-bubble">{content}</div>', unsafe_allow_html=True)
    elif role == "tool":
        st.markdown(f'<div class="tool-bubble">🔧 Tool: {content}</div>', unsafe_allow_html=True)
    elif role == "thinking":
        with st.expander("🧠 思考过程", expanded=True):
            st.markdown(content)
    elif role == "result":
        with st.expander("📊 执行结果", expanded=False):
            st.markdown(content)

# ── Left: Chat Window ─────────────────────────────────────────────────────────
col_chat, col_info = st.columns([3, 1])

with col_chat:
    # Display history
    for msg in st.session_state.chat_history:
        role = msg["role"]
        content = msg["content"]
        if role == "thinking":
            render_message(role, content)
        elif role == "tool_result":
            with st.expander(f"🔧 工具调用: {msg.get('tool','')}", expanded=False):
                st.markdown(f"`{msg.get('content','')}`")
        else:
            render_message(role, content)
    
    # Input
    with st.container():
        user_input = st.chat_input("输入问题，按 Enter 发送...", key="chat_input")
    
    if user_input and st.session_state.clawra_ready:
        # Show user message
        render_message("user", user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Simulate agent thinking (placeholder - real impl needs async streaming)
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown(
            '<div class="assistant-bubble">🧠 正在分析问题...</div>',
            unsafe_allow_html=True
        )
        
        # ── Real agent logic ────────────────────────────────────────────────
        # We'll implement a real synchronous version here that does:
        # 1. Determine intent
        # 2. Call appropriate tools (learn/reason/retrieve)
        # 3. Stream intermediate results
        # ─────────────────────────────────────────────────────────────────────
        
        try:
            clawra = st.session_state.clawra
            query = user_input
            
            # Detect intent and route
            q_lower = query.lower()
            
            # ── Tool call: learn() ──────────────────────────────────────────
            learn_keywords = ["学习", "提取", "了解", "知道", "文本", "知识"]
            reason_keywords = ["推理", "推导", "关系", "关联", "结论", "如果"]
            retrieve_keywords = ["查找", "搜索", "查询", "检索", "找"]
            eval_keywords = ["评估", "质量", "健康", "状态"]
            
            results = []
            
            if any(k in q_lower for k in learn_keywords):
                thinking_placeholder.markdown(
                    '<div class="assistant-bubble">🔍 正在从文本提取知识...</div>',
                    unsafe_allow_html=True
                )
                time.sleep(0.5)
                result = clawra.learn(query)
                results.append({
                    "type": "learn",
                    "success": result.get("success"),
                    "domain": result.get("domain"),
                    "patterns": len(result.get("learned_patterns", [])),
                    "facts": result.get("facts_added", 0),
                    "extracted": result.get("extracted_facts", [])[:5]
                })
                thinking_placeholder.markdown(
                    '<div class="assistant-bubble">📚 知识提取完成，正在推理...</div>',
                    unsafe_allow_html=True
                )
                time.sleep(0.3)
            
            # Always do reasoning if facts exist
            conclusions = clawra.reason(max_depth=2)
            if conclusions:
                results.append({
                    "type": "reason",
                    "conclusions": len(conclusions),
                    "top": [str(c.conclusion)[:100] for c in conclusions[:3]]
                })
            
            # Build response
            thinking_placeholder.empty()
            
            if results:
                resp_lines = []
                for r in results:
                    if r["type"] == "learn":
                        resp_lines.append(
                            f"✅ 从您的输入中学到了 **{r['patterns']}** 个模式，"
                            f"提取了 **{r['facts']}** 条事实三元组。"
                        )
                        if r["extracted"]:
                            resp_lines.append("**提取的知识：**")
                            for f in r["extracted"]:
                                resp_lines.append(
                                    f"  • ({f.get('subject')}) —[{f.get('predicate')}]→ ({f.get('object')})"
                                )
                    elif r["type"] == "reason":
                        resp_lines.append(f"🧠 推理引擎推导出 **{r['conclusions']}** 条新结论。")
                        for c in r["top"]:
                            resp_lines.append(f"  • {c}")
                
                resp = "\n\n".join(resp_lines)
                render_message("assistant", resp)
                st.session_state.chat_history.append({"role": "assistant", "content": resp})
            else:
                resp = (
                    "我理解您的问题了。\n\n"
                    "**我可以帮您：**\n"
                    "• 📚 **学习知识** — 输入文本，自动提取三元组\n"
                    "• 🧠 **推理** — 添加事实，自动推导结论\n"
                    "• 🔍 **检索** — GraphRAG 混合检索\n"
                    "• 🛡️ **规则引擎** — 业务约束评估\n"
                    "• ⚙️ **技能执行** — 调用注册技能\n\n"
                    "请告诉我您想做什么？"
                )
                render_message("assistant", resp)
                st.session_state.chat_history.append({"role": "assistant", "content": resp})
                
        except Exception as e:
            thinking_placeholder.empty()
            render_message("assistant", f"❌ 出错了: {e}")
            st.session_state.chat_history.append({"role": "assistant", "content": f"错误: {e}"})
    
    elif user_input and not st.session_state.clawra_ready:
        st.warning("⚠️ 请先在侧边栏点击 **初始化 Clawra**")
    
    # Clear button
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ── Right: Conversation Intelligence ──────────────────────────────────────────
with col_info:
    st.markdown("### 🧩 能力路由")
    
    if st.session_state.clawra_ready:
        # Stats
        stats = st.session_state.clawra.get_statistics()
        st.metric("📊 知识事实", stats.get("facts", 0))
        st.metric("🧠 推理结论", "—")
        st.metric("🔍 检索次数", "—")
        
        st.divider()
        st.markdown("### 🔀 路由能力")
        capabilities = {
            "📚 learn()": "文本 → 知识三元组",
            "🧠 reason()": "事实 → 逻辑推理",
            "🔍 retrieve()": "query → 检索结果",
            "⚙️ execute_skill()": "技能ID → 执行结果",
            "🛡️ evaluate()": "参数 → 约束验证",
        }
        for cap, desc in capabilities.items():
            st.markdown(f"**{cap}**")
            st.caption(f"_{desc}_")
    else:
        st.info("初始化后显示路由信息")
    
    st.divider()
    st.markdown("### 💡 示例问题")
    examples = [
        "燃气调压箱超过0.4MPa会有什么风险？",
        "学习：燃气调压箱需要每半年维护",
        "查找关于压力设备的安全规范",
        "评估：进气0.5MPa, 出气0.05MPa是否安全",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:10]}", use_container_width=True):
            # Auto-fill and submit
            st.session_state[f"chat_input_{ex[:10]}"] = ex
            st.rerun()
