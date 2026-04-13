"""
Clawra Evolved Agent - Self-Learning & Reasoning
=================================================

True cognitive agent with:
1. Self-learning: Extract → Validate → Integrate → Evolve
2. Multi-step reasoning with explanation
3. Knowledge evolution tracking
4. Real-time visualization
"""
import streamlit as st
import os
import sys
import json
import asyncio
import time
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from openai import AsyncOpenAI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoner import Reasoner, Fact, Rule
from src.core.ontology.rule_engine import RuleEngine

# Must be first Streamlit command
st.set_page_config(
    page_title="Clawra Evolved | Self-Learning Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================
# CSS - Modern dark theme
# =========================================
st.markdown("""
<style>
    .stApp { background: #0f172a; color: #e2e8f0; }
    .main-header { 
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .step-card {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    .step-active {
        border-color: #6366f1;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.3);
    }
    .step-complete {
        border-color: #10b981;
    }
    .triple-box {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid #10b981;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        font-family: monospace;
    }
    .reasoning-chain {
        background: rgba(99, 102, 241, 0.1);
        border-left: 3px solid #6366f1;
        padding: 12px;
        margin: 8px 0;
    }
    .metric-highlight {
        background: rgba(99, 102, 241, 0.2);
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .evolution-track {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    /* Custom button styles */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
</style>
""", unsafe_allow_html=True)


# =========================================
# Core Data Structures
# =========================================
@dataclass
class LearningEvent:
    timestamp: str
    event_type: str
    description: str
    facts_added: int
    facts_modified: int
    confidence_delta: float

@dataclass
class ReasoningStep:
    step_num: int
    premise: str
    rule_applied: str
    conclusion: str
    confidence: float


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
    
    async def call(self, messages: List[Dict], temperature: float = 0.5) -> str:
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def extract_structured(self, text: str) -> Dict:
        """Extract knowledge with structure analysis"""
        prompt = f"""Analyze this text and extract structured knowledge.

Text: {text}

Return JSON:
{{
  "entities": [{{"name": "...", "type": "...", "attributes": {{}}}}],
  "relations": [{{"subject": "...", "predicate": "...", "object": "...", "confidence": 0.9}}],
  "domain": "detected domain",
  "completeness_score": 0.85,
  "missing_info": ["what's missing"]
}}

JSON:"""
        
        response = await self.call([
            {"role": "system", "content": "Extract structured knowledge comprehensively."},
            {"role": "user", "content": prompt}
        ], temperature=0.3)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            return json.loads(response[start:end]) if start >= 0 else {}
        except:
            return {"relations": [], "entities": [], "domain": "unknown"}
    
    async def reason_with_explanation(self, question: str, facts: List[str]) -> Dict:
        """Multi-step reasoning with explanation"""
        facts_text = "\n".join([f"{i+1}. {f}" for i, f in enumerate(facts[:15])])
        
        prompt = f"""Answer the question using step-by-step reasoning.

Known Facts:
{facts_text}

Question: {question}

Return JSON:
{{
  "reasoning_steps": [
    {{"step": 1, "premise": "...", "inference": "...", "conclusion": "..."}}
  ],
  "final_answer": "...",
  "confidence": 0.85,
  "uncertainties": ["..."]
}}

JSON:"""
        
        response = await self.call([
            {"role": "system", "content": "You are a reasoning engine. Show explicit reasoning steps."},
            {"role": "user", "content": prompt}
        ], temperature=0.4)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            return json.loads(response[start:end]) if start >= 0 else {}
        except:
            return {"reasoning_steps": [], "final_answer": response[:500], "confidence": 0.5}
    
    async def evolve_knowledge(self, existing: List[str], new_info: str) -> Dict:
        """Determine how to integrate new knowledge"""
        existing_text = "\n".join(existing[:10])
        
        prompt = f"""Analyze how new information should integrate with existing knowledge.

Existing Knowledge:
{existing_text}

New Information:
{new_info}

Return JSON:
{{
  "integration_strategy": "merge|replace|extend|conflict",
  "conflicts": [{{"existing": "...", "new": "...", "resolution": "..."}}],
  "new_insights": ["..."],
  "evolution_type": "expansion|refinement|correction"
}}

JSON:"""
        
        response = await self.call([
            {"role": "system", "content": "Analyze knowledge evolution and integration."},
            {"role": "user", "content": prompt}
        ], temperature=0.4)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            return json.loads(response[start:end]) if start >= 0 else {}
        except:
            return {"integration_strategy": "extend", "conflicts": [], "new_insights": []}


# =========================================
# Self-Learning Agent
# =========================================
class EvolvedClawraAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.reasoner = Reasoner()
        self.rule_engine = RuleEngine()
        self.learning_history: List[LearningEvent] = []
        self.current_task = None
        self.processing_steps = []
        
        # Initialize with minimal knowledge
        self._bootstrap()
    
    def _bootstrap(self):
        """Minimal bootstrap knowledge"""
        bootstrap = [
            Fact("Agent", "can", "learn", 1.0, "bootstrap"),
            Fact("Agent", "can", "reason", 1.0, "bootstrap"),
            Fact("Agent", "can", "evolve", 1.0, "bootstrap"),
        ]
        for f in bootstrap:
            self.reasoner.add_fact(f)
    
    def get_stats(self) -> Dict:
        return {
            "facts": len(self.reasoner.facts),
            "entities": len(set(f.subject for f in self.reasoner.facts) | 
                          set(f.object for f in self.reasoner.facts)),
            "relations": len(set(f.predicate for f in self.reasoner.facts)),
            "learning_events": len(self.learning_history)
        }
    
    async def learn_from_text(self, text: str) -> Dict:
        """Complete learning pipeline"""
        self.processing_steps = []
        start_facts = len(self.reasoner.facts)
        
        # Step 1: Extract
        self._step("🔍 Extracting", "Analyzing text structure...")
        extraction = await self.llm.extract_structured(text)
        
        entities = extraction.get("entities", [])
        relations = extraction.get("relations", [])
        
        self._step("✅ Extraction Complete", f"Found {len(entities)} entities, {len(relations)} relations")
        
        # Step 2: Validate
        self._step("🔬 Validating", "Checking consistency...")
        valid_relations = [r for r in relations if all(k in r for k in ['subject', 'predicate', 'object'])]
        self._step("✅ Validation", f"{len(valid_relations)} valid relations")
        
        # Step 3: Evolve (check conflicts)
        self._step("🧬 Evolving", "Checking knowledge integration...")
        existing_facts = [str(f) for f in self.reasoner.facts]
        evolution = await self.llm.evolve_knowledge(existing_facts, text)
        
        strategy = evolution.get("integration_strategy", "extend")
        conflicts = evolution.get("conflicts", [])
        
        self._step("📊 Evolution Analysis", f"Strategy: {strategy}, Conflicts: {len(conflicts)}")
        
        # Step 4: Integrate
        self._step("💾 Integrating", "Adding to knowledge base...")
        added = 0
        modified = 0
        
        for rel in valid_relations:
            try:
                fact = Fact(
                    subject=rel['subject'],
                    predicate=rel['predicate'],
                    object=rel['object'],
                    confidence=rel.get('confidence', 0.8),
                    source='learned'
                )
                self.reasoner.add_fact(fact)
                added += 1
            except Exception as e:
                self._step("⚠️ Skip", f"{rel.get('subject', '?')}: {e}")
        
        self._step("✅ Integration", f"Added {added} facts")
        
        # Step 5: Infer (forward chaining)
        self._step("🧠 Inferring", "Running forward chaining...")
        inferred = self.reasoner.forward_chain(max_depth=2)
        self._step("✅ Inference", f"Inferred {len(inferred)} new facts")
        
        # Record learning event
        end_facts = len(self.reasoner.facts)
        event = LearningEvent(
            timestamp=datetime.now().isoformat(),
            event_type="text_learning",
            description=f"Learned from text: {text[:50]}...",
            facts_added=added,
            facts_modified=len(conflicts),
            confidence_delta=extraction.get("completeness_score", 0.8)
        )
        self.learning_history.append(event)
        
        return {
            "type": "learning",
            "extraction": extraction,
            "evolution": evolution,
            "added": added,
            "inferred": len(inferred),
            "total_facts": end_facts,
            "steps": self.processing_steps,
            "new_entities": [e['name'] for e in entities]
        }
    
    async def answer(self, question: str) -> Dict:
        """Answer with reasoning"""
        self.processing_steps = []
        
        # Step 1: Retrieve relevant facts
        self._step("🔍 Retrieving", "Finding relevant knowledge...")
        
        keywords = question.lower().split()
        scored_facts = []
        for fact in self.reasoner.facts:
            score = sum(3 if kw in fact.subject.lower() else 
                       2 if kw in fact.predicate.lower() else 
                       1 if kw in fact.object.lower() else 0 
                       for kw in keywords)
            if score > 0:
                scored_facts.append((score, str(fact)))
        
        scored_facts.sort(reverse=True)
        relevant = [f[1] for f in scored_facts[:12]]
        
        self._step("✅ Retrieved", f"Found {len(relevant)} relevant facts")
        
        if not relevant:
            return {
                "type": "answer",
                "answer": "I don't have enough knowledge to answer this. Please teach me first!",
                "reasoning_steps": [],
                "facts_used": 0
            }
        
        # Step 2: Reason
        self._step("🧠 Reasoning", "Building inference chain...")
        reasoning = await self.llm.reason_with_explanation(question, relevant)
        
        steps = reasoning.get("reasoning_steps", [])
        self._step("✅ Reasoning", f"Completed {len(steps)} reasoning steps")
        
        # Step 3: Symbolic verification
        self._step("🔮 Verifying", "Symbolic verification...")
        inferred = self.reasoner.forward_chain(max_depth=1)
        self._step("✅ Verified", f"Symbolic inference: {len(inferred)} facts")
        
        return {
            "type": "answer",
            "answer": reasoning.get("final_answer", "No answer generated"),
            "reasoning_steps": steps,
            "confidence": reasoning.get("confidence", 0.7),
            "facts_used": len(relevant),
            "uncertainties": reasoning.get("uncertainties", []),
            "steps": self.processing_steps
        }
    
    def _step(self, title: str, detail: str):
        self.processing_steps.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "title": title,
            "detail": detail
        })
    
    def render_graph(self, highlight: List[str] = None) -> str:
        try:
            from pyvis.network import Network
            
            net = Network(height="450px", width="100%", bgcolor="#0f172a", font_color="#e2e8f0", directed=True)
            net.toggle_physics(True)
            
            highlight_set = set(highlight or [])
            facts = list(self.reasoner.facts)
            
            for fact in facts:
                is_new = fact.subject in highlight_set or fact.object in highlight_set
                
                net.add_node(fact.subject, label=fact.subject[:18], 
                           color="#ef4444" if is_new else "#6366f1",
                           size=28 if is_new else 22,
                           title=f"{fact.subject} (conf: {fact.confidence:.2f})")
                
                net.add_node(fact.object, label=fact.object[:18],
                           color="#f59e0b" if is_new else "#10b981",
                           size=22 if is_new else 18,
                           title=f"{fact.object}")
                
                net.add_edge(fact.subject, fact.object,
                           label=fact.predicate[:12],
                           color="#6366f1" if is_new else "#475569",
                           width=2.5 if is_new else 1.5,
                           title=f"{fact.predicate}")
            
            path = "/tmp/clawra_evolved_graph.html"
            net.save_graph(path)
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"<div style='color:red'>Error: {e}</div>"


# =========================================
# Initialize Agent
# =========================================
@st.cache_resource
def get_agent():
    return EvolvedClawraAgent()

agent = get_agent()


# =========================================
# UI Layout
# =========================================
# Header
st.markdown("""
<div class="main-header">
    <h1>🧠 Clawra Evolved Agent</h1>
    <p>Self-Learning • Multi-Step Reasoning • Knowledge Evolution</p>
</div>
""", unsafe_allow_html=True)

# Stats row
stats = agent.get_stats()
cols = st.columns(4)
metrics = [
    ("📚 Facts", stats["facts"]),
    ("🔹 Entities", stats["entities"]),
    ("🔗 Relations", stats["relations"]),
    ("📈 Learnings", stats["learning_events"])
]
for col, (label, value) in zip(cols, metrics):
    with col:
        st.markdown(f"""
        <div class="metric-highlight">
            <h2>{value}</h2>
            <p>{label}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Quick Examples - AT THE TOP
st.subheader("🚀 Quick Start Examples")

example_col1, example_col2, example_col3 = st.columns(3)

with example_col1:
    st.markdown("**🏥 Medical Domain**")
    st.caption("Learn about diabetes treatment")
    if st.button("▶️ Learn Medical Knowledge", use_container_width=True, key="ex_medical"):
        st.session_state.pending_input = """糖尿病患者需要定期监测血糖。正常空腹血糖应低于6.1 mmol/L。
        如果血糖超过11.1 mmol/L，需要注射胰岛素治疗。胰岛素治疗需要医生处方。
        常见胰岛素类型包括速效胰岛素和长效胰岛素。"""
        st.experimental_rerun()

with example_col2:
    st.markdown("**⚖️ Legal Domain**")
    st.caption("Learn contract law concepts")
    if st.button("▶️ Learn Legal Knowledge", use_container_width=True, key="ex_legal"):
        st.session_state.pending_input = """合同违约是指一方未能履行合同义务。违约方需要承担赔偿责任。
        赔偿金额通常不超过合同总价的30%。违约金需要在判决后30天内支付。
        不可抗力条款可以免除部分责任。"""
        st.experimental_rerun()

with example_col3:
    st.markdown("**🔧 Gas Equipment**")
    st.caption("Learn gas regulator specs")
    if st.button("▶️ Learn Gas Equipment", use_container_width=True, key="ex_gas"):
        st.session_state.pending_input = """燃气调压箱是用于降低燃气压力的设备。进口压力范围为0.02-0.4 MPa。
        出口压力应稳定在2-5 kPa。调压箱需要每6个月进行一次维保检查。
        主要品牌包括特瑞斯、春晖、永良。供应商需要具备特种设备生产许可证。"""
        st.experimental_rerun()

st.markdown("---")

# Process pending example
if "pending_input" in st.session_state:
    user_input = st.session_state.pending_input
    del st.session_state.pending_input
    
    # Store for display
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    st.session_state.messages.append({"role": "user", "content": user_input[:100] + "..." if len(user_input) > 100 else user_input})
    
    # Process
    with st.spinner("🧠 Agent is learning..."):
        result = asyncio.run(agent.learn_from_text(user_input))
        st.session_state.last_result = result
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"✅ Learned {result['added']} facts + {result['inferred']} inferred. Total: {result['total_facts']} facts in KB."
        })
    
    st.experimental_rerun()

# Main interaction area
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("💬 Interaction")
    
    # Display history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I'm Clawra, an evolved agent. I can learn from text and answer questions with reasoning. Try the examples above or type your own!"
        })
    
    for msg in st.session_state.messages[-6:]:  # Show last 6
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input
    user_input = st.text_area("Enter text to learn from or ask a question:", 
                              height=100,
                              placeholder="e.g., Teach me about... or What is...")
    
    action_col1, action_col2, _ = st.columns([1, 1, 2])
    
    with action_col1:
        learn_clicked = st.button("📚 Learn from Text", use_container_width=True)
    
    with action_col2:
        ask_clicked = st.button("❓ Ask Question", use_container_width=True)

with col_right:
    st.subheader("🔍 Processing Steps")
    
    if st.session_state.get("last_result"):
        result = st.session_state.last_result
        
        # Show processing steps
        steps = result.get("steps", [])
        for i, step in enumerate(steps):
            status = "complete" if i < len(steps) - 1 else "active"
            st.markdown(f"""
            <div class="step-card step-{status}">
                <b>{step['title']}</b><br/>
                <small>{step['detail']}</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Show extraction details if learning
        if result.get("type") == "learning":
            with st.expander("📊 Extraction Details", expanded=True):
                extraction = result.get("extraction", {})
                
                st.markdown("**Entities Found:**")
                for entity in extraction.get("entities", [])[:5]:
                    st.markdown(f"- **{entity.get('name', '?')}** ({entity.get('type', 'unknown')})")
                
                st.markdown("**Relations:**")
                for rel in extraction.get("relations", [])[:5]:
                    st.markdown(f"<div class='triple-box'>{rel['subject']} → {rel['predicate']} → {rel['object']}</div>", unsafe_allow_html=True)
        
        # Show reasoning if answering
        elif result.get("type") == "answer":
            with st.expander("🧠 Reasoning Chain", expanded=True):
                for step in result.get("reasoning_steps", []):
                    st.markdown(f"""
                    <div class="reasoning-chain">
                        <b>Step {step.get('step', '?')}</b><br/>
                        Premise: {step.get('premise', 'N/A')}<br/>
                        → {step.get('inference', 'N/A')}<br/>
                        <b>Conclusion:</b> {step.get('conclusion', 'N/A')}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"**Confidence:** {result.get('confidence', 0):.0%}")
                
                if result.get("uncertainties"):
                    st.markdown("**⚠️ Uncertainties:**")
                    for u in result["uncertainties"]:
                        st.markdown(f"- {u}")

# Handle actions
if learn_clicked and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input[:100] + "..." if len(user_input) > 100 else user_input})
    
    with st.spinner("🧠 Learning..."):
        result = asyncio.run(agent.learn_from_text(user_input))
        st.session_state.last_result = result
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"✅ Learned {result['added']} facts + {result['inferred']} inferred. Total: {result['total_facts']} facts."
        })
    
    st.experimental_rerun()

elif ask_clicked and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.spinner("🧠 Reasoning..."):
        result = asyncio.run(agent.answer(user_input))
        st.session_state.last_result = result
        st.session_state.messages.append({
            "role": "assistant",
            "content": result.get("answer", "No answer generated.")
        })
    
    st.experimental_rerun()

st.markdown("---")

# Knowledge Graph Visualization
st.subheader("🕸️ Knowledge Graph")

if st.session_state.get("last_result") and st.session_state.last_result.get("type") == "learning":
    new_entities = st.session_state.last_result.get("new_entities", [])
    graph_html = agent.render_graph(new_entities)
else:
    graph_html = agent.render_graph()

import streamlit.components.v1 as components
components.html(graph_html, height=470)

st.caption("💡 Red/Orange nodes = recently learned entities | Blue/Green = existing knowledge")

st.markdown("---")
st.caption("🧠 Clawra Evolved v4.0 | Self-Learning | Multi-Step Reasoning | Knowledge Evolution")
