import streamlit as st
import os
import sys
import time
import json
import asyncio
import re

# 增加 src 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.reasoner import Reasoner, Fact
from memory.base import SemanticMemory, EpisodicMemory
from agents.orchestrator import CognitiveOrchestrator

# =========================================
# 页面配置：Dark Mode & Wide Layout
# =========================================
st.set_page_config(
    page_title="Clawra | 动力学本体认知引擎", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS：现代感、描边、毛玻璃效果
st.markdown("""
<style>
    .reportview-container {
        background: #0E1117;
    }
    .stMetric {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    .trace-card {
        border-left: 4px solid #00D4FF;
        padding-left: 15px;
        margin-bottom: 20px;
        background: rgba(0, 212, 255, 0.02);
    }
    .agent-tag {
        background: #FF6B6B;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_orchestrator():
    """初始化 Clawra 认知中枢"""
    reasoner = Reasoner()
    # 默认预装一些核心公理
    reasoner.facts.append(Fact("System", "status", "online", confidence=1.0))
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "clawra2026")
    
    semantic_mem = SemanticMemory(uri=neo4j_uri, user=neo4j_user, password=neo4j_pass)
    semantic_mem.connect()
    
    episodic_mem = EpisodicMemory()
    return CognitiveOrchestrator(reasoner, semantic_mem, episodic_mem)

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = init_orchestrator()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好，我是 **Clawra**。我不仅仅是一个对话模型，我是一个具备本体约束和逻辑推导能力的认知智能体。你可以输入业务文档让我存储，或向我咨询复杂的语义关联。"}
    ]

# =========================================
# Sidebar: 状态监控 & 交互式图谱
# =========================================
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/brain.png", width=80)
    st.title("Clawra Neural Hub")
    st.caption("v3.3 Kinetic Edition")
    st.markdown("---")

    # [Gemini Optimization] 提示词自定义
    with st.expander("🛠️ 认知人格设定 (Prompt Override)"):
        custom_system_prompt = st.text_area(
            "System Prompt", 
            placeholder="留空则使用默认配置...",
            help="在这里可以强制设定 Agent 的思考逻辑和语气。"
        )

    # 引擎实时指标
    reasoner = st.session_state.orchestrator.reasoner
    fact_count = len(reasoner.facts)
    
    m1, m2 = st.columns(2)
    m1.metric("Reasoner Facts", fact_count)
    m2.metric("ChromaDB", "Connected")

    if st.session_state.orchestrator.semantic_memory.is_connected:
        st.success("🟢 Neo4j: Active")
    else:
        st.warning("🟡 Graph: Local")
    
    st.markdown("---")
    st.subheader("🕸️ 交互式本体图谱")
    
    # 渲染图谱函数
    def render_graph_html(height="400px"):
        try:
            from pyvis.network import Network
            net = Network(height=height, width="100%", bgcolor="#0E1117", font_color="white", directed=True)
            net.force_atlas_2based()
            for fact in reasoner.facts:
                net.add_node(fact.subject, label=fact.subject, color="#00D4FF", size=20)
                net.add_node(fact.object, label=fact.object, color="#FF6B6B", size=15)
                net.add_edge(fact.subject, fact.object, label=fact.predicate, color="#FFFFFF", width=1)
            path = "temp_graph.html"
            net.save_graph(path)
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
            os.remove(path)
            return html
        except Exception as e:
            return f"图谱渲染失败: {e}"

    if fact_count > 0:
        import streamlit.components.v1 as components
        html = render_graph_html()
        components.html(html, height=450)
        
        # [Gemini Optimization] 最大化图谱
        @st.dialog("🌍 本地动力学图谱全景", width="large")
        def show_large_graph():
            full_html = render_graph_html(height="800px")
            components.html(full_html, height=850)
        
        if st.button("🔍 最大化查看图谱", use_container_width=True):
            show_large_graph()
    else:
        st.info("等待知识灌输...")

    st.markdown("---")
    if st.button("🗑️ 清空对话 (Clear)", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# =========================================
# 常规渲染函数
# =========================================
def render_trace_node(node):
    """渲染单个推理节点"""
    tool = node.get("tool", "Unknown")
    args = node.get("args", {})
    result = node.get("result", {})
    
    with st.container():
        st.markdown(f"#### 🔌 {tool} | {node.get('latency', '')}")
        
        # Ingest 结果
        if tool == "ingest_knowledge":
            if "accepted_triples" in result:
                st.write(f"✅ **新发现公理 ({len(result['accepted_triples'])}):**")
                triples = [t["triple"] for t in result["accepted_triples"]]
                st.code("\n".join(triples), language="text")
            if "rejected_triples" in result:
                st.write("❌ **被拒绝冲突项:**")
                for r in result["rejected_triples"]:
                    st.caption(f"{r['triple']} — {r['reason']}")
        
        # Query 结果
        elif tool == "query_graph":
            col1, col2 = st.columns([2, 1])
            with col1:
                if "reasoning_chain" in result and result["reasoning_chain"]:
                    st.write("**🧠 逻辑推导链 (Forward Chaining):**")
                    for step in result["reasoning_chain"]:
                        st.caption(f"- IF `{step['premise']}` THEN `{step['conclusion']}` (Conf: {step['confidence']:.2f})")
                
                if "metacognition" in result:
                    meta = result["metacognition"]
                    st.write("**💡 元认知反思:**")
                    st.info(meta.get("result", "Thinking..."))
            
            with col2:
                if "grain_check" in result:
                    grain = result["grain_check"]
                    st.write("**🛡️ 粒度审计:**")
                    if grain["status"] == "SAFE":
                        st.success("Grain Verified")
                    else:
                        st.error(f"Grain Risk: {grain['risk_level']}")
                        st.caption(grain["message"])
        
        # Action 结果
        elif tool == "execute_action":
            st.write(f"⚡ **Kinetic Action:** `{result.get('summary', 'Executing')}`")
            if "execution_impact" in result:
                st.success(result["execution_impact"])

# =========================================
# 主界面对话逻辑
# =========================================
st.title("💡 Clawra Cognitive Console")

# 聊天记录显示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "trace" in msg:
            with st.expander("🧐 深度认知轨迹 (High-Fidelity Reasoning Trace)"):
                for node in msg["trace"]:
                    render_trace_node(node)

# 输入框
if prompt := st.chat_input("灌输知识或发起逻辑查询..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 实时思考动画
        status = st.status("🚀 Clawra 正在激发神经突触...", expanded=True)
        
        start_time = time.time()
        # 执行 Orchestrator 任务
        response_data = asyncio.run(st.session_state.orchestrator.execute_task(st.session_state.messages))
        latency = time.time() - start_time
        
        # 更新状态节点
        trace_logs = response_data.get("trace", [])
        for node in trace_logs:
            status.update(label=f"✅ 已完成 {node.get('tool')} 调用", state="running")
            time.sleep(0.1)
        
        status.update(label=f"✨ 推理完成 (耗时 {latency:.2f}s)", state="complete", expanded=False)
        
        reply = response_data.get("message", "")
        st.markdown(reply)
        
        # 记录和保存
        st.session_state.messages.append({
            "role": "assistant", 
            "content": reply, 
            "trace": trace_logs
        })
        
        # 重新运行刷新 UI
        st.rerun()
