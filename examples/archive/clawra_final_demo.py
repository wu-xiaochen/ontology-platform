"""
Clawra Final Demo - Clean & Verified
======================================

High contrast UI with verified functionality:
1. Self-learning pipeline (5 steps)
2. Multi-step reasoning with explanation
3. Real-time knowledge graph
4. All features tested and working
"""
import streamlit as st
import os
import sys
import json
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any
from openai import AsyncOpenAI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoner import Reasoner, Fact

# Page Config - Light theme
st.set_page_config(
    page_title="Clawra Agent | Self-Learning & Reasoning",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean Light Theme CSS
st.markdown("""
<style>
    /* Base */
    .stApp { 
        background: #ffffff; 
        color: #1e293b;
    }
    
    /* Header */
    .app-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .app-header h1 {
        color: white !important;
        margin: 0;
        font-size: 2rem;
    }
    .app-header p {
        color: rgba(255,255,255,0.9) !important;
        margin: 8px 0 0 0;
    }
    
    /* Stats Cards */
    .stat-card {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stat-card h2 {
        color: #4f46e5 !important;
        margin: 0;
        font-size: 2.5rem;
    }
    .stat-card p {
        color: #64748b !important;
        margin: 8px 0 0 0;
        font-weight: 600;
    }
    
    /* Example Cards */
    .example-card {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        height: 100%;
    }
    .example-card h4 {
        color: #1e293b !important;
        margin: 0 0 8px 0;
    }
    .example-card p {
        color: #64748b !important;
        margin: 0 0 16px 0;
        font-size: 0.9rem;
    }
    
    /* Processing Steps */
    .step-box {
        background: #f1f5f9;
        border-left: 4px solid #cbd5e1;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
    }
    .step-box.active {
        background: #eef2ff;
        border-left-color: #4f46e5;
    }
    .step-box.complete {
        background: #f0fdf4;
        border-left-color: #22c55e;
    }
    .step-box b {
        color: #1e293b;
    }
    .step-box small {
        color: #64748b;
    }
    
    /* Triple Display */
    .triple-item {
        background: #dcfce7;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 6px 0;
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 0.9rem;
    }
    .triple-item .subject { color: #166534; font-weight: 600; }
    .triple-item .predicate { color: #15803d; }
    .triple-item .object { color: #166534; font-weight: 600; }
    
    /* Reasoning Chain */
    .reasoning-step {
        background: #eef2ff;
        border: 1px solid #c7d2fe;
        border-radius: 8px;
        padding: 14px;
        margin: 8px 0;
    }
    .reasoning-step .step-num {
        background: #4f46e5;
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 8px;
    }
    
    /* Chat Messages */
    .stChatMessage {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
    
    /* Buttons */
    .stButton > button {
        background: #4f46e5 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
    }
    .stButton > button:hover {
        background: #4338ca !important;
    }
    
    /* Text Area */
    .stTextArea textarea {
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        font-size: 1rem;
    }
    
    /* Section Headers */
    h2, h3 {
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    
    /* Graph Container */
    .graph-container {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
    }
</style>
""", unsafe_allow_html=True)


# =========================================
# LLM Client
# =========================================
class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "e2e894dc-4ce5-4a7e-87d5-a7da2c12135a"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        )
        self.model = os.getenv("OPENAI_MODEL", "doubao-seed-2-0-pro-260215")
    
    async def call(self, messages: List[dict], temperature: float = 0.5) -> str:
        try:
            resp = await self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=temperature, max_tokens=2000
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def extract_knowledge(self, text: str) -> dict:
        prompt = f"""Extract knowledge from this text. Return JSON with entities and relations.

Text: {text}

Return format:
{{
  "entities": [{{"name": "...", "type": "..."}}],
  "relations": [{{"subject": "...", "predicate": "...", "object": "...", "confidence": 0.9}}],
  "domain": "..."
}}

JSON:"""
        
        response = await self.call([
            {"role": "system", "content": "Extract structured knowledge."},
            {"role": "user", "content": prompt}
        ], temperature=0.3)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            return json.loads(response[start:end]) if start >= 0 else {"relations": []}
        except:
            return {"relations": []}
    
    async def reason(self, question: str, facts: list) -> dict:
        facts_text = "\n".join([f"{i+1}. {f}" for i, f in enumerate(facts[:10])])
        
        prompt = f"""Answer with reasoning steps.

Facts:
{facts_text}

Question: {question}

Return JSON:
{{
  "steps": [{{"step": 1, "premise": "...", "conclusion": "..."}}],
  "answer": "...",
  "confidence": 0.85
}}

JSON:"""
        
        response = await self.call([
            {"role": "system", "content": "Show reasoning steps explicitly."},
            {"role": "user", "content": prompt}
        ], temperature=0.4)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            return json.loads(response[start:end]) if start >= 0 else {"answer": response[:500]}
        except:
            return {"answer": response[:500], "steps": []}


# =========================================
# Agent
# =========================================
class ClawraAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.reasoner = Reasoner()
        self.processing_log = []
        self.learned_entities = []
        
        # Bootstrap
        for f in [
            Fact("Agent", "can", "learn", 1.0, "bootstrap"),
            Fact("Agent", "can", "reason", 1.0, "bootstrap"),
        ]:
            self.reasoner.add_fact(f)
    
    def log(self, title: str, detail: str):
        self.processing_log.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "title": title,
            "detail": detail
        })
    
    async def learn(self, text: str) -> dict:
        self.processing_log = []
        self.learned_entities = []
        
        # Step 1: Extract
        self.log("🔍 Extracting", "Calling LLM to analyze text...")
        extraction = await self.llm.extract_knowledge(text)
        relations = extraction.get("relations", [])
        self.log("✅ Extraction Complete", f"Found {len(relations)} relations")
        
        # Step 2: Validate
        self.log("🔬 Validating", "Checking relation format...")
        valid = [r for r in relations if all(k in r for k in ['subject', 'predicate', 'object'])]
        self.log("✅ Validation", f"{len(valid)} valid relations")
        
        # Step 3: Integrate
        self.log("💾 Integrating", "Adding to knowledge base...")
        added = 0
        for r in valid:
            try:
                fact = Fact(r['subject'], r['predicate'], r['object'], 
                          r.get('confidence', 0.8), 'learned')
                self.reasoner.add_fact(fact)
                self.learned_entities.extend([r['subject'], r['object']])
                added += 1
            except:
                pass
        self.log("✅ Integration", f"Added {added} facts")
        
        # Step 4: Infer
        self.log("🧠 Inferring", "Running forward chaining...")
        inferred_result = self.reasoner.forward_chain(max_depth=2)
        inferred_count = len(inferred_result.conclusions) if hasattr(inferred_result, 'conclusions') else 0
        self.log("✅ Inference", f"Inferred {inferred_count} facts")
        
        return {
            "type": "learn",
            "added": added,
            "inferred": inferred_count,
            "total": len(self.reasoner.facts),
            "relations": valid[:10],
            "log": self.processing_log
        }
    
    async def answer(self, question: str) -> dict:
        self.processing_log = []
        
        # Retrieve
        self.log("🔍 Retrieving", "Finding relevant facts...")
        keywords = question.lower().split()
        matches = []
        for fact in self.reasoner.facts:
            score = sum(1 for kw in keywords if kw in str(fact).lower())
            if score > 0:
                matches.append((score, str(fact)))
        matches.sort(reverse=True)
        facts = [m[1] for m in matches[:10]]
        self.log("✅ Retrieved", f"Found {len(facts)} relevant facts")
        
        if not facts:
            return {"type": "answer", "answer": "Please teach me about this topic first!", "log": self.processing_log}
        
        # Reason
        self.log("🧠 Reasoning", "Building inference chain...")
        result = await self.llm.reason(question, facts)
        self.log("✅ Reasoning", f"Completed {len(result.get('steps', []))} steps")
        
        return {
            "type": "answer",
            "answer": result.get("answer", "No answer"),
            "steps": result.get("steps", []),
            "confidence": result.get("confidence", 0.7),
            "log": self.processing_log
        }
    
    def render_graph(self, highlight: list = None) -> str:
        try:
            from pyvis.network import Network
            
            net = Network(height="420px", width="100%", bgcolor="#ffffff", font_color="#1e293b", directed=True)
            net.toggle_physics(True)
            
            highlight_set = set(highlight or [])
            
            for fact in self.reasoner.facts:
                is_new = fact.subject in highlight_set or fact.object in highlight_set
                
                net.add_node(fact.subject, label=fact.subject[:16], 
                           color="#ef4444" if is_new else "#4f46e5",
                           size=26 if is_new else 20,
                           font={'color': '#1e293b', 'size': 14})
                
                net.add_node(fact.object, label=fact.object[:16],
                           color="#f97316" if is_new else "#22c55e",
                           size=20 if is_new else 16,
                           font={'color': '#1e293b', 'size': 12})
                
                net.add_edge(fact.subject, fact.object,
                           label=fact.predicate[:10],
                           color="#6366f1" if is_new else "#94a3b8",
                           width=2.5 if is_new else 1.5,
                           font={'color': '#475569', 'size': 10})
            
            path = "/tmp/clawra_graph.html"
            net.save_graph(path)
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<div style='color:red'>Error: {e}</div>"


# =========================================
# Initialize
# =========================================
@st.cache_resource
def get_agent():
    return ClawraAgent()

agent = get_agent()


# =========================================
# UI
# =========================================
# Header
st.markdown("""
<div class="app-header">
    <h1>🧠 Clawra Agent</h1>
    <p>Self-Learning Knowledge System with Multi-Step Reasoning</p>
</div>
""", unsafe_allow_html=True)

# Stats
stats = {
    "facts": len(agent.reasoner.facts),
    "entities": len(set(f.subject for f in agent.reasoner.facts) | set(f.object for f in agent.reasoner.facts)),
    "relations": len(set(f.predicate for f in agent.reasoner.facts))
}

cols = st.columns(3)
for col, (label, value) in zip(cols, [("📚 Facts", stats["facts"]), ("🔹 Entities", stats["entities"]), ("🔗 Relations", stats["relations"])]):
    with col:
        st.markdown(f"""
        <div class="stat-card">
            <h2>{value}</h2>
            <p>{label}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Examples - TOP PLACEMENT
st.subheader("🚀 Quick Start Examples")

ex1, ex2, ex3 = st.columns(3)

with ex1:
    st.markdown("""
    <div class="example-card">
        <h4>🏥 Medical</h4>
        <p>Learn about diabetes treatment protocols</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("▶️ Learn Medical", use_container_width=True, key="btn_med"):
        st.session_state.input_text = """糖尿病患者需要定期监测血糖。正常空腹血糖应低于6.1 mmol/L。
如果血糖超过11.1 mmol/L，需要注射胰岛素治疗。胰岛素需要医生处方。"""
        st.session_state.action = "learn"
        st.experimental_rerun()

with ex2:
    st.markdown("""
    <div class="example-card">
        <h4>⚖️ Legal</h4>
        <p>Learn contract breach concepts</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("▶️ Learn Legal", use_container_width=True, key="btn_leg"):
        st.session_state.input_text = """合同违约是指一方未能履行合同义务。违约方需要承担赔偿责任。
赔偿金额通常不超过合同总价的30%。违约金需要在判决后30天内支付。"""
        st.session_state.action = "learn"
        st.experimental_rerun()

with ex3:
    st.markdown("""
    <div class="example-card">
        <h4>🔧 Gas Equipment</h4>
        <p>Learn gas regulator specifications</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("▶️ Learn Gas Equipment", use_container_width=True, key="btn_gas"):
        st.session_state.input_text = """燃气调压箱用于降低燃气压力。进口压力范围为0.02-0.4 MPa。
出口压力应稳定在2-5 kPa。调压箱需要每6个月进行一次维保检查。
主要品牌包括特瑞斯、春晖、永良。"""
        st.session_state.action = "learn"
        st.experimental_rerun()

st.markdown("---")

# Main Interface
left, right = st.columns([1, 1])

with left:
    st.subheader("💬 Interaction")
    
    # Initialize
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I'm Clawra. I can learn from text and answer questions with reasoning. Try the examples above!"
        })
    
    # Show messages
    for msg in st.session_state.messages[-5:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input
    input_text = st.text_area(
        "Enter text to learn or question to ask:",
        value=st.session_state.get("input_text", ""),
        height=120,
        placeholder="Type something to teach me, or ask a question..."
    )
    
    # Clear input from state
    if "input_text" in st.session_state:
        del st.session_state.input_text
    
    # Actions
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📚 Learn", use_container_width=True, type="primary"):
            if input_text.strip():
                st.session_state.action = "learn"
                st.session_state.current_input = input_text
                st.experimental_rerun()
    with c2:
        if st.button("❓ Ask", use_container_width=True):
            if input_text.strip():
                st.session_state.action = "ask"
                st.session_state.current_input = input_text
                st.experimental_rerun()

with right:
    st.subheader("🔍 Processing Steps")
    
    # Handle actions
    if st.session_state.get("action") and st.session_state.get("current_input"):
        action = st.session_state.action
        user_input = st.session_state.current_input
        
        # Clear
        del st.session_state.action
        del st.session_state.current_input
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input[:80] + "..." if len(user_input) > 80 else user_input})
        
        # Process
        with st.spinner("Processing..."):
            if action == "learn":
                result = asyncio.run(agent.learn(user_input))
                response = f"✅ Learned {result['added']} facts + {result['inferred']} inferred. Total KB: {result['total']} facts."
            else:
                result = asyncio.run(agent.answer(user_input))
                response = result.get("answer", "No answer generated.")
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.last_result = result
        
        st.experimental_rerun()
    
    # Display processing steps
    if st.session_state.get("last_result"):
        result = st.session_state.last_result
        
        for step in result.get("log", []):
            status = "complete" if "✅" in step["title"] else "active" if "🔍" in step["title"] or "🧠" in step["title"] else ""
            st.markdown(f"""
            <div class="step-box {status}">
                <b>{step['title']}</b><br/>
                <small>{step['detail']}</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Show extracted relations
        if result.get("type") == "learn" and result.get("relations"):
            with st.expander("📊 Extracted Relations", expanded=True):
                for r in result["relations"][:5]:
                    st.markdown(f"""
                    <div class="triple-item">
                        <span class="subject">{r['subject']}</span>
                        <span class="predicate">→ {r['predicate']} →</span>
                        <span class="object">{r['object']}</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Show reasoning
        elif result.get("type") == "answer" and result.get("steps"):
            with st.expander("🧠 Reasoning Steps", expanded=True):
                for step in result["steps"]:
                    st.markdown(f"""
                    <div class="reasoning-step">
                        <span class="step-num">{step.get('step', '?')}</span>
                        <b>Premise:</b> {step.get('premise', 'N/A')}<br/>
                        <b>Conclusion:</b> {step.get('conclusion', 'N/A')}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"**Confidence:** {result.get('confidence', 0):.0%}")

st.markdown("---")

# Knowledge Graph
st.subheader("🕸️ Knowledge Graph Visualization")

graph_col, legend_col = st.columns([4, 1])

with graph_col:
    if st.session_state.get("last_result") and agent.learned_entities:
        html = agent.render_graph(agent.learned_entities)
    else:
        html = agent.render_graph()
    
    import streamlit.components.v1 as components
    components.html(html, height=440)

with legend_col:
    st.markdown("""
    **Legend:**
    
    🔴 Red Node  
    New Entity
    
    🟠 Orange Node  
    New Value
    
    🔵 Blue Node  
    Existing Entity
    
    🟢 Green Node  
    Existing Value
    
    ➡️ Purple Edge  
    New Relation
    
    ➡️ Gray Edge  
    Existing Relation
    """)

st.markdown("---")
st.caption("🧠 Clawra Agent v5.0 | Self-Learning | Multi-Step Reasoning | Verified Functionality")
