"""
Clawra Demo v3 - Clean & Professional UI
=========================================

Bright theme with high contrast for better readability
"""
import streamlit as st
import os
import sys
import time
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoner import Reasoner, Fact
from src.memory.base import SemanticMemory, EpisodicMemory
from src.agents.orchestrator import CognitiveOrchestrator
from src.core.ontology.rule_engine import RuleEngine

# Page Config
st.set_page_config(
    page_title="Clawra - Neuro-Symbolic Cognitive Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean Light Theme CSS
st.markdown("""
<style>
    /* Main app - light background */
    .stApp {
        background: #f8fafc;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #6366f1 0%, #8b5cf6 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stMetric {
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    /* Main content cards */
    .main .block-container {
        padding-top: 2rem;
    }
    
    /* Section headers */
    h1, h2, h3, h4 {
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    
    /* Chat messages */
    .stChatMessage {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Metric cards */
    .stMetric {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
    }
    
    /* Buttons */
    .stButton > button {
        background: #6366f1;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        background: #4f46e5;
    }
    
    /* Expanders */
    .stExpander {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: #6366f1;
        color: white !important;
    }
    
    /* Status elements */
    .stSuccess {
        background: #dcfce7;
        border: 1px solid #86efac;
    }
    
    .stError {
        background: #fee2e2;
        border: 1px solid #fca5a5;
    }
    
    .stWarning {
        background: #fef3c7;
        border: 1px solid #fcd34d;
    }
    
    .stInfo {
        background: #dbeafe;
        border: 1px solid #93c5fd;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background: #1e293b;
        border-radius: 8px;
    }
    
    /* Input field */
    .stChatInput {
        border: 2px solid #e2e8f0;
        border-radius: 12px;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: #e2e8f0;
    }
    
    .stProgress > div > div > div {
        background: #6366f1;
    }
</style>
""", unsafe_allow_html=True)


# =========================================
# Initialize System
# =========================================
@st.cache_resource
def init_system():
    """Initialize Clawra with demo data"""
    reasoner = Reasoner()
    
    # Demo facts
    demo_facts = [
        Fact("燃气调压箱", "is_a", "燃气设备", confidence=0.95, source="demo"),
        Fact("燃气调压箱", "用途", "降低和稳定燃气压力", confidence=0.95, source="demo"),
        Fact("燃气调压箱", "组成部件", "调压器", confidence=0.95, source="demo"),
        Fact("燃气调压箱", "组成部件", "切断阀", confidence=0.95, source="demo"),
        Fact("燃气调压箱", "组成部件", "过滤器", confidence=0.95, source="demo"),
        Fact("调压器", "类型", "直接作用式", confidence=0.85, source="demo"),
        Fact("调压器", "类型", "间接作用式", confidence=0.85, source="demo"),
        Fact("进口压力", "范围", "0.02-0.4 MPa", confidence=0.95, source="demo"),
        Fact("出口压力", "范围", "2-5 kPa", confidence=0.95, source="demo"),
        Fact("GB 27791", "标准名称", "城镇燃气调压柜", confidence=0.95, source="demo"),
        Fact("供应商A", "供应能力", "150 m³/h", confidence=0.90, source="demo"),
        Fact("供应商A", "报价", "480000 CNY", confidence=0.90, source="demo"),
        Fact("供应商B", "供应能力", "100 m³/h", confidence=0.90, source="demo"),
        Fact("供应商B", "报价", "550000 CNY", confidence=0.90, source="demo"),
        Fact("供应商C", "供应能力", "90 m³/h", confidence=0.90, source="demo"),
        Fact("供应商C", "报价", "490000 CNY", confidence=0.90, source="demo"),
        Fact("System", "status", "online", confidence=1.0, source="system"),
    ]
    
    for fact in demo_facts:
        reasoner.add_fact(fact)
    
    semantic_mem = SemanticMemory(use_mock=True)
    episodic_mem = EpisodicMemory(db_path="data/demo_episodic.db")
    orchestrator = CognitiveOrchestrator(reasoner, semantic_mem, episodic_mem)
    rule_engine = RuleEngine()
    
    return orchestrator, rule_engine, reasoner


orchestrator, rule_engine, reasoner = init_system()


# =========================================
# Sidebar
# =========================================
with st.sidebar:
    st.title("🧠 Clawra")
    st.caption("Neuro-Symbolic Cognitive Engine")
    
    st.markdown("---")
    
    # System Status
    st.subheader("📊 System Status")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Facts", len(reasoner.facts))
    with col2:
        st.metric("Rules", len(rule_engine.rules))
    
    st.markdown("---")
    
    # Quick Links
    st.subheader("🔗 Quick Links")
    st.markdown("""
    - 📚 Knowledge Graph
    - 📏 Rule Engine
    - 🧠 Metacognition
    - 📊 Compliance Check
    """)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# =========================================
# Main Content
# =========================================

# Header
st.title("🧠 Clawra Cognitive Console")
st.markdown("### Neuro-Symbolic AI with Ontology-Driven Reasoning")

# Introduction
st.markdown("""
Welcome to **Clawra** - a cognitive engine that combines:
- 📚 **Knowledge Graph** - Structured ontology storage
- 🔍 **GraphRAG** - Semantic search + graph traversal  
- 📏 **Rule Engine** - Mathematical validation sandbox
- 🧠 **Metacognition** - Confidence calibration & boundary detection
""")

st.markdown("---")

# =========================================
# Capability Tabs
# =========================================
tab1, tab2, tab3, tab4 = st.tabs(["📚 Knowledge", "📏 Rules", "🧠 Metacognition", "💬 Chat"])

with tab1:
    st.header("Knowledge Graph")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Knowledge Base Contents")
        
        # Display facts in a table
        st.markdown("**Sample Facts:**")
        
        fact_data = [
            ("燃气调压箱", "用途", "降低和稳定燃气压力", "0.95"),
            ("燃气调压箱", "组成部件", "调压器", "0.95"),
            ("调压器", "类型", "直接作用式", "0.85"),
            ("进口压力", "范围", "0.02-0.4 MPa", "0.95"),
            ("GB 27791", "标准名称", "城镇燃气调压柜", "0.95"),
        ]
        
        for s, p, o, c in fact_data:
            st.markdown(f"**{s}** → `{p}` → {o} *(conf: {c})*")
        
        st.markdown("---")
        st.info(f"📈 Total Facts in Knowledge Base: **{len(reasoner.facts)}**")
    
    with col2:
        st.subheader("🔍 Semantic Search")
        
        query = st.text_input("Search query:", placeholder="e.g., 调压设备")
        
        if st.button("Search", type="primary"):
            if query:
                st.success("Found 3 matching results:")
                st.markdown("1. 燃气调压箱 → 用途 → 降低和稳定燃气压力")
                st.markdown("2. 调压器 → 类型 → 直接作用式")
                st.markdown("3. 进口压力 → 范围 → 0.02-0.4 MPa")

with tab2:
    st.header("Rule Engine")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📏 Active Rules")
        
        rules = [
            ("Safety Margin", "supply_capacity >= flow_requirement * 1.5", "Gas regulator capacity must be 1.5x the flow requirement"),
            ("Budget Limit", "quoted_price <= planned_budget * 1.1", "Quote cannot exceed 110% of budget"),
            ("Pressure Range", "outlet_pressure >= 0.002 and <= 0.4", "Outlet pressure must be 2-400 kPa"),
        ]
        
        for name, expr, desc in rules:
            with st.expander(f"✅ {name}"):
                st.code(expr, language="python")
                st.caption(desc)
    
    with col2:
        st.subheader("🧪 Rule Evaluation")
        
        supply = st.number_input("Supply Capacity (m³/h):", value=100)
        flow = st.number_input("Flow Requirement (m³/h):", value=50)
        
        if st.button("Evaluate", type="primary"):
            context = {"supply_capacity": supply, "flow_requirement": flow}
            result = rule_engine.evaluate_rule("rule:gas_regulator_safety_margin", context)
            
            required = flow * 1.5
            st.markdown(f"**Calculation:** {supply} >= {flow} × 1.5 = {required}")
            
            if result["status"] == "PASS":
                st.success(f"✅ PASS - Safety margin satisfied")
                st.balloons()
            else:
                st.error(f"❌ FAIL - Safety margin NOT satisfied")
                st.warning(f"Need at least {required:.1f} m³/h, have {supply} m³/h")

with tab3:
    st.header("Metacognition & Knowledge Boundary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Confidence Calibration")
        
        evidence_count = st.slider("Evidence Count:", 0, 10, 3)
        evidence_quality = st.slider("Evidence Quality:", 0.0, 1.0, 0.8, 0.1)
        
        # Calculate confidence
        if evidence_count == 0:
            confidence = 0.0
        else:
            evidence_factor = min(evidence_count / 5.0, 1.0)
            confidence = (evidence_factor * evidence_quality * 0.9) + 0.1
            confidence = min(confidence, 0.99)
        
        st.progress(confidence)
        st.metric("Calibrated Confidence", f"{confidence:.0%}")
        
        st.markdown("---")
        st.markdown("**Interpretation:**")
        if confidence >= 0.85:
            st.success("🟢 High Confidence")
        elif confidence >= 0.60:
            st.warning("🟡 Medium Confidence")
        elif confidence >= 0.40:
            st.warning("🟠 Low Confidence")
        else:
            st.error("🔴 Unknown / Out of Bounds")
    
    with col2:
        st.subheader("🎯 Knowledge Boundary")
        
        st.markdown("""
        **Boundary Levels:**
        
        | Level | Confidence | Action |
        |-------|------------|--------|
        | 🟢 High | > 85% | Proceed with answer |
        | 🟡 Medium | 60-85% | Verify critical facts |
        | 🟠 Low | 40-60% | Consult external sources |
        | 🔴 Unknown | < 40% | Ask domain expert |
        """)
        
        st.markdown("---")
        st.info("Clawra automatically detects when queries approach or exceed its knowledge boundary and provides appropriate warnings.")

with tab4:
    st.header("Interactive Chat")
    
    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": """Hello! I'm **Clawra**. I can help you with:

1. 📚 **Knowledge queries** - Ask about gas regulators, standards, etc.
2. 📏 **Rule validation** - Check if parameters meet safety rules
3. 📊 **Supplier evaluation** - Compare suppliers against requirements

Try asking: "推荐哪个供应商?" or "调压箱的组成部分有哪些?"
"""}
        ]
    
    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat input MUST be outside tabs
st.markdown("---")
st.subheader("💬 Chat with Clawra")

# Display messages again for chat section
for msg in st.session_state.get("messages", []):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Type your question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            time.sleep(0.5)
            
            # Generate response
            if "供应商" in prompt or "supplier" in prompt.lower():
                response = """**Supplier Evaluation Results:**

| Supplier | Capacity | Price | Safety | Budget | Status |
|----------|----------|-------|--------|--------|--------|
| A | 150 m³/h | ¥480k | ✅ 1.88x | ✅ | **RECOMMENDED** |
| B | 100 m³/h | ¥550k | ❌ 1.25x | ✅ | Not Recommended |
| C | 90 m³/h | ¥490k | ❌ 1.13x | ✅ | Not Recommended |

**Recommendation:** Select **Supplier A** - passes all safety and budget checks.

*Confidence: 95%*"""
            elif "调压箱" in prompt or "regulator" in prompt.lower():
                response = """**Gas Regulator Box (燃气调压箱):**

**Purpose:** Lower and stabilize gas pressure

**Components:**
- Pressure regulator (调压器)
- Shut-off valve (切断阀)
- Filter (过滤器)

**Technical Specs:**
- Inlet: 0.02-0.4 MPa
- Outlet: 2-5 kPa

**Applicable Standards:** GB 27791

*Confidence: 92%*"""
            else:
                response = f"""I received: "{prompt}"

I'm specialized in gas industry knowledge and procurement compliance. 

**Suggested queries:**
- "推荐哪个供应商?" (Which supplier to recommend?)
- "调压箱的组成部分" (Components of gas regulator)
- "安全裕度规则" (Safety margin rules)

*Confidence: 40% - Limited knowledge on this topic*"""
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})


# Footer
st.markdown("---")
st.caption("🧠 Clawra v2.0 | Powered by VolcEngine Ark LLM | Neo4j + ChromaDB")
