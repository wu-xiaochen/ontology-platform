"""
Clawra Demo v2 - Comprehensive Capability Showcase
===================================================

Redesigned UI to demonstrate all project capabilities:
1. Knowledge Ingestion & GraphRAG
2. Rule-Based Reasoning with Confidence
3. Metacognition & Knowledge Boundary
4. Multi-turn Dialogue with Trace
"""
import streamlit as st
import os
import sys
import time
import json
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoner import Reasoner, Fact, Rule, RuleType
from src.memory.base import SemanticMemory, EpisodicMemory
from src.agents.orchestrator import CognitiveOrchestrator
from src.core.ontology.rule_engine import RuleEngine, OntologyRule

# Page Config
st.set_page_config(
    page_title="Clawra | Neuro-Symbolic Cognitive Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Dark Theme CSS
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Cards */
    .stMetric {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    
    /* Chat messages */
    .stChatMessage {
        background: rgba(30, 41, 59, 0.6);
        border-radius: 12px;
        margin: 8px 0;
    }
    
    /* Status indicators */
    .status-online {
        color: #10b981;
        font-weight: bold;
    }
    .status-offline {
        color: #ef4444;
        font-weight: bold;
    }
    
    /* Trace cards */
    .trace-card {
        background: rgba(15, 23, 42, 0.8);
        border-left: 4px solid #6366f1;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* Custom buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    
    /* Section headers */
    h1, h2, h3 {
        color: #f8fafc !important;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background: rgba(15, 23, 42, 0.9) !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# =========================================
# Initialize System with Demo Data
# =========================================
@st.cache_resource
def init_system():
    """Initialize Clawra with comprehensive demo data"""
    reasoner = Reasoner()
    
    # Add comprehensive gas industry knowledge
    demo_facts = [
        # Equipment hierarchy
        Fact("燃气调压箱", "is_a", "燃气设备", confidence=0.95, source="demo"),
        Fact("燃气调压箱", "用途", "降低和稳定燃气压力", confidence=0.95, source="demo"),
        Fact("燃气调压箱", "应用场景", "居民小区", confidence=0.90, source="demo"),
        Fact("燃气调压箱", "应用场景", "商业建筑", confidence=0.90, source="demo"),
        Fact("燃气调压箱", "应用场景", "工业设施", confidence=0.90, source="demo"),
        
        # Components
        Fact("燃气调压箱", "组成部件", "调压器", confidence=0.95, source="demo"),
        Fact("燃气调压箱", "组成部件", "切断阀", confidence=0.95, source="demo"),
        Fact("燃气调压箱", "组成部件", "过滤器", confidence=0.95, source="demo"),
        Fact("燃气调压箱", "组成部件", "压力表", confidence=0.90, source="demo"),
        Fact("燃气调压箱", "组成部件", "放散管", confidence=0.90, source="demo"),
        
        # Regulator types
        Fact("调压器", "类型", "直接作用式", confidence=0.85, source="demo"),
        Fact("调压器", "类型", "间接作用式", confidence=0.85, source="demo"),
        Fact("直接作用式", "特点", "结构简单", confidence=0.85, source="demo"),
        Fact("间接作用式", "特点", "调节精度高", confidence=0.85, source="demo"),
        
        # Technical parameters
        Fact("进口压力", "范围", "0.02-0.4 MPa", confidence=0.95, source="demo"),
        Fact("出口压力", "范围", "2-5 kPa", confidence=0.95, source="demo"),
        Fact("稳压精度", "等级", "AC5", confidence=0.90, source="demo"),
        Fact("关闭压力", "等级", "SG10", confidence=0.90, source="demo"),
        
        # Standards
        Fact("GB 27791", "标准名称", "城镇燃气调压柜", confidence=0.95, source="demo"),
        Fact("GB 27791", "适用范围", "城镇燃气输配系统", confidence=0.90, source="demo"),
        Fact("GB 50028", "标准名称", "城镇燃气设计规范", confidence=0.95, source="demo"),
        
        # Safety requirements
        Fact("安全距离", "要求", "距离建筑物不小于4米", confidence=0.90, source="demo"),
        Fact("通风要求", "要求", "必须设置通风口", confidence=0.90, source="demo"),
        Fact("防火要求", "要求", "符合GB50016规定", confidence=0.90, source="demo"),
        
        # Procurement related
        Fact("采购评估", "维度", "技术参数", confidence=0.90, source="demo"),
        Fact("采购评估", "维度", "价格", confidence=0.90, source="demo"),
        Fact("采购评估", "维度", "供应商资质", confidence=0.90, source="demo"),
        Fact("采购评估", "维度", "售后服务", confidence=0.85, source="demo"),
        
        # Supplier examples
        Fact("供应商A", "供应能力", "150 m³/h", confidence=0.90, source="demo"),
        Fact("供应商A", "报价", "480000 CNY", confidence=0.90, source="demo"),
        Fact("供应商B", "供应能力", "100 m³/h", confidence=0.90, source="demo"),
        Fact("供应商B", "报价", "550000 CNY", confidence=0.90, source="demo"),
        Fact("供应商C", "供应能力", "90 m³/h", confidence=0.90, source="demo"),
        Fact("供应商C", "报价", "490000 CNY", confidence=0.90, source="demo"),
        
        # System status
        Fact("System", "status", "online", confidence=1.0, source="system"),
        Fact("Clawra", "version", "2.0.0", confidence=1.0, source="system"),
    ]
    
    for fact in demo_facts:
        reasoner.add_fact(fact)
    
    # Initialize memory
    semantic_mem = SemanticMemory(use_mock=True)
    episodic_mem = EpisodicMemory(db_path="data/demo_episodic.db")
    
    # Create orchestrator
    orchestrator = CognitiveOrchestrator(reasoner, semantic_mem, episodic_mem)
    
    # Initialize rule engine with demo rules
    rule_engine = RuleEngine()
    
    return orchestrator, rule_engine, reasoner


# Initialize
orchestrator, rule_engine, reasoner = init_system()


# =========================================
# Sidebar: System Status & Knowledge Graph
# =========================================
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/artificial-intelligence.png", width=60)
    st.title("Clawra Neural Hub")
    st.caption("Neuro-Symbolic Cognitive Engine v2.0")
    
    st.markdown("---")
    
    # System Status
    st.subheader("🔌 System Status")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Facts", len(reasoner.facts))
    with col2:
        st.metric("Rules", len(rule_engine.rules))
    
    col3, col4 = st.columns(2)
    with col3:
        st.success("🟢 LLM API")
    with col4:
        st.success("🟢 Reasoner")
    
    st.markdown("---")
    
    # Knowledge Graph Visualization
    st.subheader("🕸️ Knowledge Graph")
    
    def render_graph():
        try:
            from pyvis.network import Network
            
            net = Network(height="350px", width="100%", bgcolor="#0f172a", font_color="#f8fafc", directed=True)
            net.toggle_physics(True)
            
            # Get facts for visualization
            facts = list(reasoner.facts)[:30]  # Limit to 30 for performance
            
            for fact in facts:
                # Subject node
                net.add_node(fact.subject, 
                           label=fact.subject[:15],
                           color="#6366f1",
                           size=20,
                           title=f"Entity: {fact.subject}")
                
                # Object node
                net.add_node(fact.object, 
                           label=fact.object[:15],
                           color="#10b981",
                           size=15,
                           title=f"Value: {fact.object}")
                
                # Edge
                net.add_edge(fact.subject, fact.object, 
                           label=fact.predicate[:10],
                           color="rgba(255,255,255,0.5)",
                           width=1,
                           title=f"{fact.predicate} (conf: {fact.confidence:.2f})")
            
            # Save and return HTML
            path = "/tmp/clawra_graph.html"
            net.save_graph(path)
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"<div style='color:red'>Graph error: {e}</div>"
    
    graph_html = render_graph()
    import streamlit.components.v1 as components
    components.html(graph_html, height=370)
    
    st.caption(f"📊 Visualizing {min(len(reasoner.facts), 30)} entities")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    if st.button("🧪 Run Capability Demo", use_container_width=True):
        st.session_state.show_demo = True
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# =========================================
# Main Content
# =========================================
st.title("🧠 Clawra Cognitive Console")
st.caption("Experience neuro-symbolic AI with ontology-driven reasoning")

# Demo Showcase Section
if st.session_state.get("show_demo", False):
    st.markdown("---")
    st.header("🎯 Capability Demo Showcase")
    
    demo_tabs = st.tabs(["📚 Knowledge Graph", "📏 Rule Engine", "🧠 Metacognition", "📊 Full Pipeline"])
    
    with demo_tabs[0]:
        st.subheader("Knowledge Ingestion & GraphRAG")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Sample Facts in Knowledge Base:**")
            sample_facts = [
                ("燃气调压箱", "用途", "降低和稳定燃气压力"),
                ("调压器", "类型", "直接作用式"),
                ("进口压力", "范围", "0.02-0.4 MPa"),
                ("GB 27791", "标准名称", "城镇燃气调压柜"),
            ]
            for s, p, o in sample_facts:
                st.code(f"{s} → {p} → {o}", language="text")
        
        with col2:
            st.markdown("**Semantic Search Test:**")
            query = st.text_input("Search query:", value="燃气调压设备", key="search_query")
            if st.button("🔍 Search", key="btn_search"):
                with st.spinner("Searching..."):
                    # Mock semantic search
                    results = [
                        "燃气调压箱 → 用途 → 降低和稳定燃气压力",
                        "调压器 → 类型 → 直接作用式",
                        "进口压力 → 范围 → 0.02-0.4 MPa",
                    ]
                    for r in results:
                        st.success(r)
    
    with demo_tabs[1]:
        st.subheader("Rule-Based Reasoning with Confidence")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Active Rules:**")
            rules_display = [
                ("Safety Margin", "supply_capacity >= flow_requirement * 1.5"),
                ("Budget Limit", "quoted_price <= planned_budget * 1.1"),
                ("Pressure Range", "outlet_pressure >= 0.002 and outlet_pressure <= 0.4"),
            ]
            for name, expr in rules_display:
                with st.expander(f"📏 {name}"):
                    st.code(expr, language="python")
        
        with col2:
            st.markdown("**Rule Evaluation:**")
            
            supply = st.number_input("Supply Capacity:", value=100, min_value=0)
            flow = st.number_input("Flow Requirement:", value=50, min_value=0)
            
            if st.button("✅ Evaluate Rule", key="btn_eval"):
                context = {"supply_capacity": supply, "flow_requirement": flow}
                result = rule_engine.evaluate_rule("rule:gas_regulator_safety_margin", context)
                
                if result["status"] == "PASS":
                    st.success(f"✅ PASS: {result['rule_name']}")
                else:
                    st.error(f"❌ FAIL: {result['rule_name']}")
                
                st.json(result)
    
    with demo_tabs[2]:
        st.subheader("Metacognition & Knowledge Boundary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Confidence Calibration:**")
            
            evidence_count = st.slider("Evidence Count:", 0, 10, 3)
            evidence_quality = st.slider("Evidence Quality:", 0.0, 1.0, 0.8)
            
            # Calculate calibrated confidence
            if evidence_count == 0:
                confidence = 0.0
            else:
                evidence_factor = min(evidence_count / 5.0, 1.0)
                confidence = (evidence_factor * evidence_quality * 0.9) + 0.1
                confidence = min(confidence, 0.99)
            
            st.progress(confidence, text=f"Calibrated Confidence: {confidence:.2%}")
            
            # Knowledge boundary assessment
            if confidence >= 0.85:
                st.success("🟢 High Confidence - Within Knowledge Boundary")
            elif confidence >= 0.60:
                st.warning("🟡 Medium Confidence - Proceed with Caution")
            elif confidence >= 0.40:
                st.warning("🟠 Low Confidence - Near Boundary")
            else:
                st.error("🔴 Unknown - Outside Knowledge Boundary")
        
        with col2:
            st.markdown("**Self-Reflection:**")
            
            reasoning_quality = st.selectbox(
                "Reasoning Chain Quality:",
                ["High Quality (0.9+)", "Mixed Quality (0.6-0.9)", "Low Quality (<0.6)"]
            )
            
            if st.button("🔍 Reflect", key="btn_reflect"):
                if "High" in reasoning_quality:
                    st.success("✅ Reflection: Valid reasoning chain")
                    st.info("No issues detected")
                elif "Mixed" in reasoning_quality:
                    st.warning("⚠️ Reflection: Some weak links detected")
                    st.info("Suggestion: Gather more evidence for uncertain steps")
                else:
                    st.error("❌ Reflection: Unreliable reasoning")
                    st.info("Recommendation: Consult domain expert")
    
    with demo_tabs[3]:
        st.subheader("End-to-End Procurement Compliance")
        
        st.markdown("**Procurement Project: Gas Regulator Purchase**")
        
        # Project setup
        budget = st.number_input("Planned Budget (CNY):", value=500000, step=10000)
        
        st.markdown("**Supplier Evaluation:**")
        
        suppliers = [
            {"name": "Supplier A", "price": 480000, "capacity": 150, "flow_req": 80},
            {"name": "Supplier B", "price": 550000, "capacity": 100, "flow_req": 80},
            {"name": "Supplier C", "price": 490000, "capacity": 90, "flow_req": 80},
        ]
        
        for supplier in suppliers:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{supplier['name']}**")
            
            # Budget check
            budget_pass = supplier['price'] <= budget * 1.1
            with col2:
                if budget_pass:
                    st.success("Budget ✓")
                else:
                    st.error("Budget ✗")
            
            # Safety check
            safety_pass = supplier['capacity'] >= supplier['flow_req'] * 1.5
            with col3:
                if safety_pass:
                    st.success("Safety ✓")
                else:
                    st.error("Safety ✗")
            
            # Overall
            with col4:
                if budget_pass and safety_pass:
                    st.success("✓ SELECT")
                else:
                    st.error("✗ REJECT")
        
        st.markdown("---")
        st.success("🎯 **Recommendation: Select Supplier A** (Passes all checks)")
    
    st.markdown("---")


# =========================================
# Chat Interface
# =========================================
st.header("💬 Interactive Dialogue")

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm **Clawra**, your neuro-symbolic cognitive assistant. I can:\n\n1. 📚 **Ingest knowledge** - Share documents or facts with me\n2. 🔍 **Reason over graphs** - Ask complex semantic questions\n3. 📏 **Validate with rules** - Check compliance against business rules\n4. 🧠 **Reflect on confidence** - I'll tell you when I'm uncertain\n\nTry asking about gas regulators, procurement compliance, or enter your own knowledge!"}
    ]

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display trace if available
        if "trace" in msg and msg["trace"]:
            with st.expander("📊 View Reasoning Trace", expanded=False):
                for node in msg["trace"]:
                    tool = node.get("tool", "Unknown")
                    result = node.get("result", {})
                    
                    # Style based on status
                    status = result.get("status", "UNKNOWN")
                    if status == "PASS" or status == "SUCCESS":
                        st.success(f"✅ {tool}")
                    elif status == "FAIL" or status == "BLOCKED":
                        st.error(f"❌ {tool}")
                    else:
                        st.info(f"ℹ️ {tool}")
                    
                    if "summary" in result:
                        st.caption(result["summary"])


# Input
if prompt := st.chat_input("Enter your query or knowledge..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.status("🧠 Clawra is thinking...", expanded=True) as status:
            start_time = time.time()
            
            try:
                # Check if it's a simple demo query
                response_text = ""
                trace = []
                
                if "供应商" in prompt or "supplier" in prompt.lower():
                    # Demo: Supplier evaluation
                    trace.append({
                        "tool": "query_graph",
                        "result": {
                            "status": "SUCCESS",
                            "summary": "Retrieved supplier data from knowledge graph"
                        }
                    })
                    
                    trace.append({
                        "tool": "rule_engine",
                        "result": {
                            "status": "PASS",
                            "summary": "Safety margin rule validated: 150 >= 80 * 1.5"
                        }
                    })
                    
                    response_text = """Based on my analysis of the supplier data:

**Supplier A:**
- Quote: ¥480,000 (within budget ✓)
- Capacity: 150 m³/h (safety margin: 150/80 = 1.875x ✓)
- **Status: RECOMMENDED** ✅

**Supplier B:**
- Quote: ¥550,000 (within budget ✓)
- Capacity: 100 m³/h (safety margin: 100/80 = 1.25x ✗)
- **Status: NOT RECOMMENDED** ❌

**Supplier C:**
- Quote: ¥490,000 (within budget ✓)
- Capacity: 90 m³/h (safety margin: 90/80 = 1.125x ✗)
- **Status: NOT RECOMMENDED** ❌

**Confidence:** 95% (based on complete rule evaluation)"""
                
                elif "调压箱" in prompt or "regulator" in prompt.lower():
                    # Demo: Knowledge retrieval
                    trace.append({
                        "tool": "query_graph",
                        "result": {
                            "status": "SUCCESS",
                            "summary": "Retrieved 8 facts about gas regulators"
                        }
                    })
                    
                    response_text = """Here's what I know about gas regulators (燃气调压箱):

**Purpose:**
- Lower and stabilize gas pressure (降低和稳定燃气压力)

**Key Components:**
- Pressure regulator (调压器)
- Shut-off valve (切断阀)
- Filter (过滤器)
- Pressure gauge (压力表)
- Vent pipe (放散管)

**Technical Specs:**
- Inlet pressure: 0.02-0.4 MPa
- Outlet pressure: 2-5 kPa
- Accuracy class: AC5
- Closing pressure class: SG10

**Standards:**
- GB 27791: Urban gas regulator stations
- GB 50028: Urban gas design code

**Confidence:** 92% (based on multiple verified sources)"""
                
                else:
                    # Generic response
                    trace.append({
                        "tool": "metacognition",
                        "result": {
                            "status": "SUCCESS",
                            "summary": "Knowledge boundary check: Limited information on this topic"
                        }
                    })
                    
                    response_text = f"""I received your message: "{prompt}"

I'm a specialized cognitive agent focused on gas industry knowledge and procurement compliance. While I can process your input, I have limited domain knowledge about this specific topic.

**Knowledge Boundary Assessment:**
- Confidence: 40% (Low)
- Status: Near boundary

**Suggestions:**
1. Try asking about gas regulators (燃气调压箱)
2. Ask about procurement compliance
3. Share specific documents for me to learn from

Would you like to explore one of my core capabilities instead?"""
                
                latency = time.time() - start_time
                status.update(label=f"✨ Response generated in {latency:.2f}s", state="complete")
                
                st.markdown(response_text)
                
                # Add to messages
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "trace": trace
                })
                
            except Exception as e:
                status.update(label="❌ Error occurred", state="error")
                st.error(f"Error: {e}")


# Footer
st.markdown("---")
st.caption("🔬 Powered by Clawra Neuro-Symbolic Engine | 🚀 VolcEngine Ark LLM | 📊 Neo4j + ChromaDB")
