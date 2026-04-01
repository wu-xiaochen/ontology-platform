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
    """渲染单个推理节点（鲁棒性升级版）"""
    tool = node.get("tool", "Unknown")
    latency = node.get("latency", "0s")
    result = node.get("result", {})
    
    with st.container():
        st.markdown(f"#### 🔌 {tool} | {latency}")
        
        # 1. 结构化状态检查
        if isinstance(result, dict):
            status = result.get("status", "UNKNOWN")
            
            if status == "BLOCKED":
                st.error(f"🚫 **审计拦截**: {result.get('summary', '被拦截')}")
                if "risks" in result:
                    for risk in result["risks"]:
                        st.caption(f"⚠️ {risk}")
                return
            
            if status == "ERROR":
                st.error(f"❌ **执行错误**: {result.get('msg', '未知故障')}")
                return

            if "summary" in result:
                st.info(result["summary"])

            # 专用工具渲染逻辑
            if tool == "ingest_knowledge":
                if "accepted_triples" in result:
                    triples = [t.get("triple", "") for t in result["accepted_triples"]]
                    st.code("\n".join(triples), language="text")
            
            elif tool == "query_graph":
                col1, col2 = st.columns([3, 1])
                with col1:
                    if "reasoning_chain" in result and result["reasoning_chain"]:
                        st.write("**🧠 逻辑推导链:**")
                        for s in result["reasoning_chain"]:
                            st.caption(f"- {s.get('conclusion', '')}")
                    
                    if "metacognition" in result:
                        meta = result["metacognition"]
                        st.info(f"💡 {meta.get('result', 'Thinking...')}")
                
                with col2:
                    if "vector_context" in result:
                        st.write("**🔍 向量召回:**")
                        st.caption(f"Hits: {len(result['vector_context'])}")
            
            elif tool == "execute_action":
                if "impact" in result:
                    st.success(result["impact"])
        else:
            st.write(str(result))

# =========================================
# 主界面对话逻辑
# =========================================
st.title("💡 Clawra Cognitive Console")

# 聊天记录显示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "trace" in msg and msg["trace"]:
            with st.expander("🧐 深度认知轨迹 (High-Fidelity Reasoning Trace)", expanded=False):
                for node in msg["trace"]:
                    render_trace_node(node)

# 输入框
if prompt := st.chat_input("灌输知识或发起逻辑查询..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    with st.chat_message("assistant"):
        status = st.status("🚀 Clawra 正在激发神经突触...", expanded=True)
        try:
            # 强化型线程隔离异步运行器 (彻底解决 uvloop 冲突)
            import threading
            from concurrent.futures import ThreadPoolExecutor

            def _run_in_new_loop(msgs, prompt):
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        st.session_state.orchestrator.execute_task(msgs, custom_prompt=prompt)
                    )
                finally:
                    new_loop.close()

            start_time = time.time()
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    _run_in_new_loop, 
                    st.session_state.messages, 
                    st.session_state.get("custom_system_prompt")
                )
                response = future.result()
            
            latency = time.time() - start_time
            
            # 更新状态展示
            trace_logs = response.get("trace", [])
            for node in trace_logs:
                status.write(f"✅ {node.get('tool')} ({node.get('latency', '0s')})")
            
            status.update(label=f"✨ 推理完成 (耗时 {latency:.2f}s)", state="complete", expanded=False)
            
            # 显示回复
            st.markdown(response["message"])
            
            # 保存到 session
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["message"],
                "trace": trace_logs
            })
            
            # 强制刷新 UI
            st.rerun()

        except Exception as e:
            st.error(f"致命故障: {e}")
            status.update(label="❌ 推理引擎熔断", state="error", expanded=True)
