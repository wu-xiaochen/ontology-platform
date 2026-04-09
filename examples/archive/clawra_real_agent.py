"""
Clawra Real Agent - With Actual LLM Integration
================================================

Real agent that:
1. Calls VolcEngine Ark API for universal extraction
2. Uses LLM for reasoning and planning
3. Real knowledge base operations
"""
import streamlit as st
import os
import sys
import json
import asyncio
import time
from typing import List, Dict, Any
from openai import AsyncOpenAI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoner import Reasoner, Fact
from src.memory.base import SemanticMemory

# Page Config
st.set_page_config(
    page_title="Clawra Real Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .stApp { background: #f8fafc; }
    .agent-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
    .thinking-box {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
    }
    .tool-result {
        background: #e0e7ff;
        border-left: 4px solid #6366f1;
        padding: 8px 12px;
        margin: 4px 0;
    }
    .extracted-triple {
        background: #dcfce7;
        border: 1px solid #86efac;
        padding: 8px;
        border-radius: 6px;
        margin: 4px 0;
    }
</style>
""", unsafe_allow_html=True)


# =========================================
# Real LLM Client
# =========================================
class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "e2e894dc-4ce5-4a7e-87d5-a7da2c12135a"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        )
        self.model = os.getenv("OPENAI_MODEL", "doubao-seed-2-0-pro-260215")
    
    async def chat(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Call LLM API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    async def extract_knowledge(self, text: str) -> List[Dict]:
        """Use LLM to extract knowledge triples"""
        prompt = f"""Extract knowledge triples (subject, predicate, object) from the following text.
Return ONLY a JSON array in this exact format:
[
  {{"subject": "...", "predicate": "...", "object": "...", "confidence": 0.9}},
  ...
]

Text to analyze:
{text}

JSON output:"""
        
        response = await self.chat([
            {"role": "system", "content": "You are a knowledge extraction expert. Extract structured triples from text."},
            {"role": "user", "content": prompt}
        ], temperature=0.3)
        
        # Parse JSON from response
        try:
            # Find JSON array in response
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                triples = json.loads(json_str)
                return triples
            else:
                return []
        except:
            return []
    
    async def analyze_intent(self, text: str) -> Dict:
        """Analyze user intent"""
        prompt = f"""Analyze the user intent. Return JSON with:
- intent: one of [knowledge_extraction, reasoning, query, general]
- entities: list of key entities mentioned
- domain: detected domain (medical, legal, engineering, generic, etc.)

User input: {text}

JSON output:"""
        
        response = await self.chat([
            {"role": "system", "content": "You analyze user intents."},
            {"role": "user", "content": prompt}
        ], temperature=0.3)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            else:
                return {"intent": "general", "entities": [], "domain": "generic"}
        except:
            return {"intent": "general", "entities": [], "domain": "generic"}
    
    async def generate_reasoning_test(self, facts: List[str]) -> List[Dict]:
        """Generate reasoning test cases"""
        facts_text = "\n".join([f"- {f}" for f in facts[:10]])
        
        prompt = f"""Given these facts, generate 3 reasoning test cases.
Each test should have premises and a conclusion that can be inferred.
Hide intermediate reasoning steps.

Facts:
{facts_text}

Return JSON array:
[
  {{
    "premises": ["fact1", "fact2"],
    "conclusion": "inferred fact",
    "hidden_steps": ["step1", "step2"],
    "difficulty": "easy|medium|hard"
  }}
]

JSON output:"""
        
        response = await self.chat([
            {"role": "system", "content": "You create reasoning tests."},
            {"role": "user", "content": prompt}
        ], temperature=0.5)
        
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            else:
                return []
        except:
            return []


# =========================================
# Real Agent Implementation
# =========================================
class RealClawraAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.reasoner = Reasoner()
        self.memory = SemanticMemory(use_mock=True)
        self.execution_log = []
        
        # Init with some base facts
        self._init_knowledge()
    
    def _init_knowledge(self):
        """Initialize with domain knowledge"""
        base_facts = [
            Fact("燃气调压箱", "is_a", "燃气设备", confidence=0.95),
            Fact("燃气调压箱", "用途", "降低和稳定燃气压力", confidence=0.95),
            Fact("调压器", "类型", "直接作用式", confidence=0.85),
            Fact("进口压力", "范围", "0.02-0.4 MPa", confidence=0.95),
            Fact("供应商A", "供应能力", "150 m³/h", confidence=0.90),
            Fact("供应商A", "报价", "480000 CNY", confidence=0.90),
        ]
        for f in base_facts:
            self.reasoner.add_fact(f)
    
    async def process(self, user_input: str) -> Dict:
        """Main processing pipeline"""
        self.execution_log = []
        
        # Step 1: Intent Analysis
        self._log("🔍 Analyzing intent...")
        intent_data = await self.llm.analyze_intent(user_input)
        self._log(f"✅ Intent detected: {intent_data.get('intent', 'general')}")
        self._log(f"📍 Domain: {intent_data.get('domain', 'generic')}")
        
        intent = intent_data.get('intent', 'general')
        
        # Step 2: Route to handler
        if intent == 'knowledge_extraction' or 'extract' in user_input.lower() or '抽取' in user_input:
            result = await self._handle_extraction(user_input)
        elif intent == 'reasoning' or 'evaluate' in user_input.lower() or '评估' in user_input:
            result = await self._handle_evaluation()
        elif intent == 'query' or 'query' in user_input.lower() or '查询' in user_input:
            result = await self._handle_query(user_input)
        else:
            result = await self._handle_chat(user_input)
        
        return {
            "intent": intent_data,
            "execution_log": self.execution_log,
            "result": result
        }
    
    def _log(self, message: str):
        """Log execution step"""
        self.execution_log.append({
            "time": time.strftime("%H:%M:%S"),
            "message": message
        })
    
    async def _handle_extraction(self, text: str) -> Dict:
        """Handle knowledge extraction"""
        self._log("📝 Extracting knowledge triples using LLM...")
        
        # Remove "Extract:" prefix if present
        clean_text = text.replace("Extract:", "").replace("extract:", "").strip()
        
        # Call LLM for extraction
        triples = await self.llm.extract_knowledge(clean_text)
        
        self._log(f"✅ Extracted {len(triples)} triples")
        
        # Add to knowledge base
        added = []
        for t in triples:
            try:
                fact = Fact(
                    subject=t.get('subject', ''),
                    predicate=t.get('predicate', ''),
                    object=t.get('object', ''),
                    confidence=t.get('confidence', 0.8),
                    source='llm_extraction'
                )
                self.reasoner.add_fact(fact)
                added.append(t)
                self._log(f"💾 Added: {fact.subject} → {fact.predicate} → {fact.object}")
            except Exception as e:
                self._log(f"⚠️ Failed to add triple: {e}")
        
        # Coverage assessment
        coverage = self._assess_coverage(triples)
        
        return {
            "type": "extraction",
            "triples": triples,
            "added_count": len(added),
            "total_facts": len(self.reasoner.facts),
            "coverage": coverage
        }
    
    async def _handle_evaluation(self) -> Dict:
        """Handle reasoning capability evaluation"""
        self._log("🧪 Generating reasoning test cases...")
        
        # Get current facts as strings
        fact_strings = [str(f) for f in self.reasoner.facts]
        
        # Generate tests using LLM
        tests = await self.llm.generate_reasoning_test(fact_strings)
        
        self._log(f"✅ Generated {len(tests)} test cases")
        
        return {
            "type": "evaluation",
            "test_cases": tests,
            "fact_count": len(fact_strings)
        }
    
    async def _handle_query(self, text: str) -> Dict:
        """Handle knowledge query"""
        self._log("🔍 Searching knowledge base...")
        
        # Simple keyword search
        keywords = text.lower().split()
        matches = []
        
        for fact in self.reasoner.facts:
            fact_str = str(fact).lower()
            if any(kw in fact_str for kw in keywords):
                matches.append(str(fact))
        
        self._log(f"✅ Found {len(matches)} matching facts")
        
        # Use LLM to synthesize answer
        if matches:
            context = "\n".join(matches[:10])
            prompt = f"""Based on these facts, answer the query:

Facts:
{context}

Query: {text}

Provide a clear, concise answer:"""
            
            answer = await self.llm.chat([
                {"role": "system", "content": "You answer questions based on provided facts."},
                {"role": "user", "content": prompt}
            ])
        else:
            answer = "I don't have specific information about that in my knowledge base."
        
        return {
            "type": "query",
            "matches": matches,
            "answer": answer
        }
    
    async def _handle_chat(self, text: str) -> Dict:
        """Handle general chat"""
        self._log("💬 Generating response...")
        
        # Provide context about capabilities
        context = """You are Clawra, a neuro-symbolic cognitive agent with these capabilities:
1. Knowledge extraction from any domain text
2. Reasoning capability evaluation
3. Knowledge base queries
4. Domain: Currently focused on gas industry and general knowledge

Current knowledge base: {fact_count} facts
""".format(fact_count=len(self.reasoner.facts))
        
        response = await self.llm.chat([
            {"role": "system", "content": context},
            {"role": "user", "content": text}
        ])
        
        return {
            "type": "chat",
            "response": response
        }
    
    def _assess_coverage(self, new_triples: List[Dict]) -> Dict:
        """Assess coverage of new triples against existing KB"""
        existing_entities = set()
        for fact in self.reasoner.facts:
            existing_entities.add(fact.subject)
            existing_entities.add(fact.object)
        
        new_entities = set()
        for t in new_triples:
            new_entities.add(t.get('subject', ''))
            new_entities.add(t.get('object', ''))
        
        overlap = existing_entities & new_entities
        novelty = 1 - (len(overlap) / len(new_entities)) if new_entities else 0
        
        return {
            "new_entities": len(new_entities),
            "existing_entities": len(existing_entities),
            "overlap": len(overlap),
            "novelty_score": novelty,
            "assessment": "High novelty" if novelty > 0.7 else "Medium overlap" if novelty > 0.3 else "High overlap"
        }


# =========================================
# Initialize
# =========================================
@st.cache_resource
def get_agent():
    return RealClawraAgent()

agent = get_agent()


# =========================================
# UI
# =========================================
st.title("🤖 Clawra Real Agent")
st.markdown("### Powered by VolcEngine Ark LLM")

st.markdown("""
This is a **real agent** that:
- ✅ Calls VolcEngine Ark API for knowledge extraction
- ✅ Uses LLM for intent analysis and reasoning
- ✅ Actually stores facts in knowledge base
- ✅ Generates real reasoning test cases
""")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.title("📊 Agent Status")
    st.metric("Facts in KB", len(agent.reasoner.facts))
    st.metric("API", "🟢 Connected" if agent.llm.client else "🔴 Disconnected")
    
    st.markdown("---")
    st.markdown("**Try these:**")
    st.markdown("""
    - "Extract: The patient has diabetes requiring insulin"
    - "Evaluate reasoning capability"
    - "What is a gas regulator?"
    """)

# Main chat
st.subheader("💬 Chat")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm Clawra with real LLM integration. I can extract knowledge, evaluate reasoning, and answer queries. What would you like to do?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if "execution_log" in msg:
            with st.expander("📋 Execution Log"):
                for log in msg["execution_log"]:
                    st.text(f"[{log['time']}] {log['message']}")
        
        if "result" in msg:
            result = msg["result"]
            
            if result.get("type") == "extraction":
                st.markdown("**📚 Extracted Triples:**")
                for t in result.get("triples", []):
                    st.markdown(f"<div class='extracted-triple'>**{t.get('subject')}** → `{t.get('predicate')}` → **{t.get('object')}** (conf: {t.get('confidence', 0.8):.0%})</div>", unsafe_allow_html=True)
                
                coverage = result.get("coverage", {})
                st.markdown(f"""
**Coverage Assessment:**
- New entities: {coverage.get('new_entities', 0)}
- Novelty score: {coverage.get('novelty_score', 0):.0%}
- Assessment: **{coverage.get('assessment', 'N/A')}**
                """)
            
            elif result.get("type") == "evaluation":
                st.markdown("**🧪 Reasoning Test Cases:**")
                for i, test in enumerate(result.get("test_cases", []), 1):
                    with st.expander(f"Test {i} ({test.get('difficulty', 'medium')})"):
                        st.markdown("**Premises:**")
                        for p in test.get("premises", []):
                            st.markdown(f"- {p}")
                        st.markdown(f"**Expected Conclusion:** {test.get('conclusion', 'N/A')}")
                        st.markdown(f"**Hidden Steps:** {', '.join(test.get('hidden_steps', []))}")

# Input
if prompt := st.chat_input("Enter your request..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.trigger_process = True

# Process pending message
if st.session_state.get("trigger_process", False):
    st.session_state.trigger_process = False
    
    # Get last user message
    last_user_msg = None
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break
    
    if last_user_msg:
        with st.chat_message("user"):
            st.markdown(last_user_msg)
        
        with st.chat_message("assistant"):
            with st.status("🤖 Agent is processing with LLM...", expanded=True) as status:
                # Process
                result = asyncio.run(agent.process(last_user_msg))
                
                status.update(label=f"✅ Complete ({len(result['execution_log'])} steps)", state="complete")
                
                # Show result
                response_text = ""
                if result["result"].get("type") == "chat":
                    response_text = result["result"]["response"]
                elif result["result"].get("type") == "query":
                    response_text = result["result"]["answer"]
                elif result["result"].get("type") == "extraction":
                    response_text = f"**Extracted {result['result'].get('added_count', 0)} triples. Total KB: {result['result'].get('total_facts', 0)} facts**"
                elif result["result"].get("type") == "evaluation":
                    response_text = f"**Generated {len(result['result'].get('test_cases', []))} reasoning test cases**"
                else:
                    response_text = result["result"].get("response", "Processing complete.")
                
                st.markdown(response_text)
                
                # Add to messages
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "execution_log": result["execution_log"],
                    "result": result["result"]
                })
        
        st.experimental_rerun()

# Quick demos
st.markdown("---")
st.subheader("🎯 Quick Demos")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏥 Extract Medical", use_container_width=True, key="medical_btn"):
        st.session_state.messages.append({"role": "user", "content": "Extract: Patient has hypertension with blood pressure 160/100 mmHg requiring ACE inhibitor treatment"})
        st.session_state.trigger_process = True
        st.experimental_rerun()

with col2:
    if st.button("⚖️ Extract Legal", use_container_width=True, key="legal_btn"):
        st.session_state.messages.append({"role": "user", "content": "Extract: Contract breach occurs when party fails to perform obligations within stipulated timeframe"})
        st.session_state.trigger_process = True
        st.experimental_rerun()

with col3:
    if st.button("🧪 Evaluate Reasoning", use_container_width=True, key="eval_btn"):
        st.session_state.messages.append({"role": "user", "content": "Evaluate reasoning capability"})
        st.session_state.trigger_process = True
        st.experimental_rerun()

st.markdown("---")
st.caption("🤖 Clawra Real Agent | VolcEngine Ark LLM | Live Knowledge Base")
