#!/usr/bin/env python3
"""
Clawra Framework - Web Demo (Streamlit Multipages)
├── 🤖 Agent Chat     - 自主推理对话
├── 🔬 Capabilities  - 能力演示 + API调用示例
└── 📡 API Reference  - SDK文档

Run: streamlit run examples/web_demo.py
"""

import sys
import streamlit as st
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# High Contrast Dark Theme CSS
st.html("""
<style>
    /* ── Reset & Base ── */
    .stApp { background: #0a0e17; }
    
    /* ── Typography ── */
    h1, h2, h3 { color: #ffffff !important; font-weight: 700 !important; }
    
    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #111827;
        border-right: 2px solid #1f2937;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2 { color: #f9fafb !important; }
    
    /* ── Metric cards ── */
    div[data-testid="stMetric"] {
        background: #111827 !important;
        border: 2px solid #374151 !important;
        border-radius: 12px !important;
    }
    div[data-testid="stMetricValue"] {
        color: #22d3ee !important;
        font-size: 1.9rem !important;
        font-weight: 800 !important;
    }
    div[data-testid="stMetricLabel"] { color: #9ca3af !important; }
    
    /* ── Alerts ── */
    div[data-testid="stAlert-success"] {
        background: #052e16; border-left: 5px solid #22c55e;
    }
    div[data-testid="stAlert-error"] {
        background: #2d0a0a; border-left: 5px solid #ef4444;
    }
    div[data-testid="stAlert-warning"] {
        background: #1c1408; border-left: 5px solid #f59e0b;
    }
    div[data-testid="stAlert-info"] {
        background: #0a1a2e; border-left: 5px solid #3b82f6;
    }
    
    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #22d3ee);
        color: white; border: none;
        font-weight: 700; border-radius: 10px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(99,102,241,0.4);
    }
    
    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background: #111827 !important;
        color: #f9fafb !important;
        border: 2px solid #374151 !important;
        border-radius: 8px !important;
    }
    .stTextInput label, .stTextArea label,
    .stNumberInput label, .stSelectbox label { color: #d1d5db !important; }
    
    /* ── Dividers ── */
    hr { border-color: #1f2937 !important; }
    
    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: #111827;
        border-radius: 8px;
        color: #f9fafb;
        font-weight: 600;
        border: 1px solid #374151;
    }
    
    /* ── Progress ── */
    .stProgress > div > div {
        background: linear-gradient(90deg, #6366f1, #22d3ee);
    }
    
    /* ── Chat bubbles ── */
    .user-bubble {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        max-width: 80%;
        margin-left: auto;
        margin-bottom: 8px;
    }
    .assistant-bubble {
        background: #1f2937;
        color: #f9fafb;
        border-radius: 18px 18px 18px 4px;
        padding: 12px 18px;
        max-width: 80%;
        margin-bottom: 8px;
        border: 1px solid #374151;
    }
    .tool-bubble {
        background: #0a1628;
        border: 1px solid #22d3ee;
        border-radius: 8px;
        padding: 8px 14px;
        color: #22d3ee;
        font-family: 'Courier New', monospace;
        font-size: 0.82rem;
        margin-bottom: 6px;
    }
    
    /* ── Code blocks ── */
    .stCodeBlock { background: #0d1117 !important; border-radius: 10px !important; border: 1px solid #30363d; }
    
    /* ── Page nav styling ── */
    .nav-indicator {
        text-align: center;
        padding: 0.5rem;
        color: #6b7280;
        font-size: 0.85rem;
    }
    
    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 8px 8px 0 0;
        color: #9ca3af;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #f9fafb; }
    .stTabs [aria-selected="true"] {
        background: #1f2937 !important;
        color: #22d3ee !important;
        border-color: #22d3ee !important;
    }
    
    /* ── JSON pretty ── */
    pre { color: #a5f3fc; background: #0d1117; border-radius: 8px; padding: 12px; }
    
    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #111827; }
    ::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }
</style>
""")

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Clawra Framework",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 Clawra Framework")
    st.markdown("**自主进化本体认知引擎**")
    st.divider()
    
    st.markdown("### 📌 快速导航")
    st.markdown("- 🤖 [Agent 对话](#agent-chat)")
    st.markdown("- 🔬 [能力演示](#capabilities)")
    st.markdown("- 📡 [API 文档](#api-reference)")
    
    st.divider()
    
    st.markdown("### ⚙️ 系统状态")
    if "clawra_ready" not in st.session_state:
        st.session_state.clawra_ready = False
    
    if st.button("🚀 初始化 Clawra", use_container_width=True, type="primary"):
        with st.spinner("初始化中..."):
            try:
                from src.clawra import Clawra
                st.session_state.clawra = Clawra(enable_memory=False)
                st.session_state.clawra_ready = True
                st.session_state.chat_history = []
                st.success("✅ 初始化成功")
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")
    
    if st.session_state.clawra_ready:
        stats = st.session_state.clawra.get_statistics()
        col1, col2 = st.columns(2)
        with col1: st.metric("事实", stats.get("facts", 0))
        with col2: st.metric("模式", stats.get("patterns", {}).get("total", 0))
        st.markdown(f"**领域**: `{stats.get('domain', 'unknown')}`")
    else:
        st.info("👆 请先初始化系统")
    
    st.divider()
    st.markdown("### ℹ️ 关于")
    st.caption("Clawra v4.0 | 自主进化 Agent 框架\n基于 MiniMax LLM + 知识图谱 + 神经符号融合")
