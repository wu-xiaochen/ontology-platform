import streamlit as st
import os
import sys
import time
import json
import asyncio
import re
from datetime import datetime

# 修复导入路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入 UI 核心模块 (V4.0 新模型)
from src.utils.ui.theme import apply_theme, COLORS
from src.utils.ui.components import render_metric_dashboard, render_trace_card, render_header
from src.utils.ui.graph_renderer import NeuralGraphRenderer

# 核心后端导入
from src.core.reasoner import Reasoner, Fact
from src.memory.base import SemanticMemory
from src.memory.episodic_enhanced import EpisodicMemoryManager
from src.agents.orchestrator import CognitiveOrchestrator

# =========================================
# 页面基础配置
# =========================================
st.set_page_config(
    page_title="Clawra Neural Console",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 应用全局设计系统 (Awesome Design MD)
apply_theme()

# =========================================
# 后端初始化与 Session 状态管理
# =========================================
@st.cache_resource
def init_core():
    """初始化 Clawra 认知中枢核心逻辑"""
    reasoner = Reasoner()
    # 默认公理
    reasoner.facts.append(Fact("System", "status", "online", source="kernel_boot"))
    
    # 数据库配置
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "clawra2026")
    
    semantic_mem = SemanticMemory(uri=neo4j_uri, user=neo4j_user, password=neo4j_pass)
    semantic_mem.connect()
    
    episodic_mem = EpisodicMemoryManager()
    return CognitiveOrchestrator(reasoner, semantic_mem, episodic_mem)

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = init_core()
    st.session_state.messages = []
    st.session_state.graph_renderer = NeuralGraphRenderer()

orchestrator = st.session_state.orchestrator

# =========================================
# 侧边栏：高级控制台
# =========================================
with st.sidebar:
    st.markdown("### 🛠️ Neural Parameters")
    
    # 记忆管理
    with st.expander("Memory Management", expanded=True):
        if st.button("🚀 Trigger Self-Evolution", use_container_width=True):
            with st.spinner("Distilling skills..."):
                try:
                    # 修复: 核心 evolve 已经是 async def，使用 asyncio 运行
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(orchestrator.evolve())
                    st.success(f"Evolution Completed: {results.get('results', {})}")
                except Exception as e:
                    st.error(f"Evolution Fault: {e}")
        
        if st.button("🗑️ Purge Thinking Store", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # 实体归一化预览
    with st.expander("Glossary Alignments"):
        st.dataframe(
            [{"Term": k, "Standard": v} for k, v in orchestrator.semantic_memory.entity_synonyms.items()],
            height=200
        )

# =========================================
# 主界面渲染 (Command Dashboard Layout)
# =========================================
render_header()

# 1. 第一排：实时健康指标
session_facts = len(orchestrator.reasoner.facts)
graph_facts = orchestrator.semantic_memory.get_total_facts_count()
connected = orchestrator.semantic_memory.is_connected

render_metric_dashboard(session_facts, graph_facts, connected)

st.markdown("<br>", unsafe_allow_html=True)

# 2. 第二排：核心交互区 (7:3 分区)
left_col, right_col = st.columns([7, 3])

with left_col:
    # --- 交互式知识图谱展示 (Centerpiece) ---
    st.markdown("#### 🕸️ Neural Knowledge Graph (Autonomous Discovery)")
    
    # 聚合显示事实 (Session + Sampling)
    display_facts = list(orchestrator.reasoner.facts)
    if len(display_facts) < 15:
        # 获取采样事实
        samples = orchestrator.semantic_memory.get_sample_triples(limit=40)
        display_facts.extend(samples)
    
    html_graph = st.session_state.graph_renderer.render(display_facts)
    import streamlit.components.v1 as components
    components.html(html_graph, height=550)
    
    with st.expander("📄 View Knowledge Triplet Registry", expanded=False):
        st.table([{"Subject": f.subject, "Predicate": f.predicate, "Object": f.object, "Source": f.source} for f in display_facts])

with right_col:
    # --- 聊天与推理轨迹舱 (Interaction Zone) ---
    st.markdown("#### 💬 Cognitive Interface")
    
    # 对话容器（带滚动条）
    chat_container = st.container(height=450)
    
    with chat_container:
        if not st.session_state.messages:
            st.info("Neural link established. Awaiting input...")
            
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "trace" in msg:
                    with st.expander("View Deep Trace", expanded=False):
                        for node in msg["trace"]:
                            render_trace_card(node)

    # 输入控制
    if prompt := st.chat_input("Inject knowledge or query the graph..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                status = st.status("🧠 Firing Neural Synapses...", expanded=True)
                try:
                    start_time = time.time()
                    
                    # 异步执行任务
                    async def _execute():
                        return await orchestrator.execute_task(st.session_state.messages)
                    
                    # 在 Streamlit 中同步运行异步任务的高级处理
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(_execute())
                    
                    duration = time.time() - start_time
                    status.update(label=f"Refinement Complete ({duration:.2f}s)", state="complete")
                    
                    # 渲染结果
                    st.markdown(response.get("message", "Logic flow failure"))
                    
                    # 渲染推理轨迹
                    for node in response.get("trace", []):
                        render_trace_card(node)
                        
                    # 缓存状态
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.get("message", ""),
                        "trace": response.get("trace", [])
                    })
                    
                except Exception as e:
                    st.error(f"Neural Melt: {e}")
                    status.update(label="Critical Failure", state="error")
        
        # 即使渲染完成后也刷新页面以同步指标和图谱
        st.rerun()

# =========================================
# 页脚
# =========================================
st.markdown("---")
st.caption(f"© 2026 Clawra Cognitive Systems | Last Pulse: {datetime.now().strftime('%H:%M:%S')}")
