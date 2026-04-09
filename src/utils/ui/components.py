"""
Clawra Neural Console - UI Components
Encapsulated rendering logic for high-fidelity interactive elements.
"""

import streamlit as st
import json
from .theme import COLORS

def render_metric_dashboard(session_facts, graph_facts, is_connected):
    """渲染仪表盘指标"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Neural Synapses", session_facts, help="推理引擎当前加载的活跃三元组数量")
    with col2:
        st.metric("Graph Density", graph_facts, help="物理存储（SQLite/Neo4j）中的全量知识节点数量")
    with col3:
        status = "Active" if is_connected else "Local"
        st.metric("Core Engine", status, delta="- High" if is_connected else "Offline Fallback", delta_color="normal")

def render_trace_card(node):
    """渲染高保真推理轨迹卡片"""
    tool = node.get("tool", "Unknown")
    latency = node.get("latency", "0s")
    result = node.get("result", {})
    
    # 区分系统思考和工具调用
    is_thought = "💭" in tool or "Internal Reasoning" in tool
    border_color = COLORS['primary'] if not is_thought else COLORS['accent']
    
    st.markdown(f"""
    <div class="trace-card" style="border-left-color: {border_color}">
        <div class="trace-header">
            <span class="agent-tag" style="background: {border_color}">{tool.split()[-1] if ' ' in tool else tool}</span>
            <span class="latency-tag">⚡ {latency}</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 1. 结构化结果渲染
    if isinstance(result, dict):
        status = result.get("status", "SUCCESS")
        
        if status == "BLOCKED":
            st.error(f"🚨 **Security Block**: {result.get('summary')}")
            if "risks" in result:
                for risk in result["risks"]:
                    st.caption(f"⚠️ {risk}")
        
        elif status == "ERROR":
            st.error(f"❌ **Fault**: {result.get('msg')}")
        
        else:
            if "summary" in result and not is_thought:
                st.markdown(f"**Outcome**: {result['summary']}")
            
            # 专用渲染 logic
            if tool == "ingest_knowledge":
                if "accepted_triples" in result:
                    triples = [t.get("triple", "") for t in result["accepted_triples"]]
                    st.code("\n".join(triples), language="text")
            
            elif tool == "query_graph":
                if "reasoning_chain" in result and result["reasoning_chain"]:
                    st.markdown("**Symbolic Inference:**")
                    for s in result["reasoning_chain"]:
                        st.caption(f"↳ {s.get('conclusion')}")
                
                if "metacognition" in result:
                    meta = result["metacognition"]
                    if meta.get("result"):
                        st.markdown(f"""<div class="reasoning-bubble">💡 {meta['result']}</div>""", unsafe_allow_html=True)

            elif tool == "execute_action":
                if "impact" in result:
                    st.success(f"Execution OK: {result['impact']}")
            
            # 思维链条概览
            if is_thought:
                summary = result.get("summary") or result.get("result", "")
                if summary:
                    st.markdown(f"_{summary}_")

    else:
        st.text(str(result))
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_header():
    """渲染主标题与 Subheader"""
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 30px;">
        <img src="https://img.icons8.com/isometric/100/brain.png" width="60" style="margin-right: 20px;"/>
        <div>
            <h1 style="margin: 0; font-weight: 800; letter-spacing: -1px; background: linear-gradient(90deg, #00D4FF, #FF6B6B); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                CLAWRA NEURAL CONSOLE
            </h1>
            <p style="margin: 0; color: {COLORS['text_dark']}; font-weight: 500;">
                Production-Grade Autonomous Cognitive Framework v4.0
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
