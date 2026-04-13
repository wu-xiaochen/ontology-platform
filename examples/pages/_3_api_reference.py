# ── Page Config
import streamlit as st
st.set_page_config(page_title="API Reference - Clawra", page_icon="\U0001f4e1", layout="wide")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.markdown("## \U0001f4e1 API Reference")
st.markdown("*Python SDK \xb7 REST API \xb7 WebSocket \xb7 完整集成示例*")
st.divider()

def ep_card(method, path, desc, color="#22d3ee"):
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:12px;margin:6px 0'>"
        f"<span style='background:{color};color:#000;font-weight:800;font-size:0.75rem;"
        f"padding:3px 10px;border-radius:6px'>{method}</span>"
        f"<code style='color:#f97316;font-size:0.9rem'>{path}</code>"
        f"<span style='color:#9ca3af;font-size:0.85rem'>{desc}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

def params_tbl(params):
    header = "| 参数 | 类型 | 必填 | 说明 |\n|------|------|------|------|"
    rows = []
    for name, typ, req, desc in params:
        req_str = "\u2705" if req else "\u274c"
        rows.append(f"| `{name}` | `{typ}` | {req_str} | {desc} |")
    st.markdown(header + "\n" + "\n".join(rows))

tab1, tab2, tab3, tab4 = st.tabs(["\U0001f40d Python SDK", "\U0001f310 REST API", "\U0001f518 WebSocket", "\U0001f4a1 集成示例"])

# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Clawra \u6838\u5fc3\u7c7b \u2014 SDK \u6587\u6863")

    with st.expander("\U0001f4d7 `Clawra()` \u2014 \u521d\u59cb\u5316", expanded=False):
        st.code("from src.clawra import Clawra\n\nagent = Clawra(enable_memory=False)", language="python")
        params_tbl([
            ("enable_memory", "bool", False, "\u542f\u7528\u6301\u4e45\u5316\u8bb0\u5fc6\uff08\u9700 Neo4j/ChromaDB\uff09"),
            ("neo4j_enabled", "bool", False, "\u542f\u7528 Neo4j \u56fe\u6570\u636e\u5e93"),
            ("chroma_enabled", "bool", False, "\u542f\u7528 ChromaDB \u5411\u91cf\u6570\u636e\u5e93"),
        ])
        st.markdown("**\u8fd4\u56de\u503c:** `Clawra` \u5b9e\u4f8b")

    with st.expander("\U0001f4d7 `clawra.learn(text, domain_hint)` \u2014 \u77e5\u8bc6\u63d0\u53d6", expanded=True):
        st.markdown("\u4ece\u6587\u672c\u81ea\u52a8\u63d0\u53d6\u77e5\u8bc6\u4e09\u5143\u7ec4\u3001\u89c4\u5219\u548c\u9886\u57df\u6a21\u5f0f\u3002")
        st.code('result = agent.learn(\n    "\u71c3\u6c14\u8c03\u538b\u7bb1\u7684\u8fdb\u6c14\u538b\u529b\u4e0d\u80fd\u5927\u4e8e0.4MPa\uff0c\u5426\u5219\u6709\u7206\u70b8\u98ce\u9669\u3002"\n)', language="python")
        params_tbl([
            ("text", "str", True, "\u5f85\u5b66\u4e60\u7684\u6587\u672c\u5185\u5bb9"),
            ("domain_hint", "str", False, "\u9886\u57df\u63d0\u793a\uff08medical/legal/gas_equipment\uff09"),
            ("confidence", "float", False, "\u7f6e\u4fe1\u5ea6\u9608\u503c\uff08\u9ed8\u8ba4 0.7\uff09"),
        ])
        st.markdown("**\u8fd4\u56de\u503c:** `dict`")
        st.code('{"success": true, "domain": "gas_equipment", "facts_added": 7, "extracted_facts": []}', language="json")

    with st.expander("\U0001f4d7 `clawra.add_fact()` \u2014 \u6dfb\u52a0\u4e8b\u5b9e", expanded=False):
        st.markdown("\u5411\u77e5\u8bc6\u56fe\u8c31\u6dfb\u52a0\u4e09\u5143\u7ec4\u3002")
        params_tbl([
            ("subject", "str", True, "\u4e3b\u4f53"),
            ("predicate", "str", True, "谓词"),
            ("object", "str", True, "\u5ba2\u4f53"),
            ("confidence", "float", False, "\u7f6e\u4fe1\u5ea6 0~1\uff08\u9ed8\u8ba4 0.9\uff09"),
        ])
        st.code('agent.add_fact("\u8c03\u538b\u7bb1A", "is_a", "\u71c3\u6c14\u8c03\u538b\u7bb1", confidence=0.95)', language="python")

    with st.expander("\U0001f4d7 `clawra.reason(max_depth)` \u2014 \u524d\u5411\u94fe\u63a8\u7406", expanded=False):
        st.markdown("\u6267\u884c\u524d\u5411\u94fe\u63a8\u7406\uff0c\u81ea\u52a8\u63a8\u5bfc\u65b0\u7ed3\u8bba\u3002")
        params_tbl([("max_depth", "int", False, "\u63a8\u7406\u6df1\u5ea6\uff08\u9ed8\u8ba4 3\uff09")])
        st.code("conclusions = agent.reason(max_depth=3)\nfor step in conclusions:\n    print(step.conclusion)", language="python")

    with st.expander("\U0001f4d7 `clawra.retrieve_knowledge()` \u2014 GraphRAG \u68c0\u7d22", expanded=False):
        st.markdown("entity + semantic \u6df7\u5408\u68c0\u7d22\u3002")
        params_tbl([
            ("query", "str", True, "\u68c0\u7d22 query"),
            ("top_k", "int", False, "\u8fd4\u56de Top-K\uff08\u9ed8\u8ba4 5\uff09"),
            ("modes", "List[str]", False, "entity / semantic / hybrid"),
        ])
        st.code("agent.retriever.build_index()\nresp = agent.retrieve_knowledge(\"燃气调压箱安全规范\", top_k=5)\nfor r in resp.results:\n    print(r.triple.subject)", language="python")

    with st.expander("\U0001f4d7 `clawra.evaluate_knowledge()` \u2014 \u81ea\u8bc4\u4f30", expanded=False):
        st.code("result = agent.evaluate_knowledge()\nprint(result)", language="python")

    with st.expander("\U0001f4d7 `clawra.skill_registry` \u2014 \u6280\u80fd\u5e93", expanded=False):
        st.code("from src.evolution.skill_library import Skill, SkillType\nskill = Skill(id=\"skill:check\", name=\"检查\", skill_type=SkillType.CODE, content=\"def check(x): return {'ok': x > 0}\")\nagent.skill_registry.register_skill(skill)\nif \"skill:check\" in agent.skill_registry.callables:\n    print(agent.skill_registry.callables[\"skill:check\"](42))", language="python")

# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### REST API Endpoints")
    st.markdown("\u57fa\u4e8e FastAPI\uff0c\u5b8c\u6574 OpenAPI \u6587\u6863: `GET /docs`")
    st.code("Authorization: Bearer <API_KEY>", language="bash")
    st.markdown("---")
    st.markdown("#### \u7aef\u70b9\u4e00\u89c8")
    ep_card("POST", "/api/v1/learn", "\u4ece\u6587\u672c\u63d0\u53d6\u77e5\u8bc6", "#22c55e")
    ep_card("POST", "/api/v1/facts", "\u6dfb\u52a0\u77e5\u8bc6\u4e09\u5143\u7ec4", "#22c55e")
    ep_card("POST", "/api/v1/reason", "\u6267\u884c\u63a8\u7406", "#22c55e")
    ep_card("GET",  "/api/v1/knowledge", "\u67e5\u8be2\u77e5\u8bc6\u56fe\u8c31", "#3b82f6")
    ep_card("POST", "/api/v1/retrieve", "GraphRAG \u68c0\u7d22", "#22c55e")
    ep_card("GET",  "/api/v1/evaluate", "\u77e5\u8bc6\u8d28\u91cf\u8bc4\u4f30", "#3b82f6")
    ep_card("POST", "/api/v1/skills", "\u6ce8\u518c\u6280\u80fd", "#22c55e")
    ep_card("GET",  "/api/v1/rules", "\u67e5\u8be2\u89c4\u5219\u5217\u8868", "#3b82f6")
    ep_card("POST", "/api/v1/rules/evaluate", "\u89c4\u5219\u8bc4\u4f30", "#22c55e")
    ep_card("GET",  "/api/v1/stats", "\u7cfb\u7edf\u7edf\u8ba1", "#3b82f6")

    st.markdown("---")
    with st.expander("POST /api/v1/learn \u2014 \u8bf7\u6c42/\u54cd\u5e94\u793a\u4f8b", expanded=False):
        st.markdown("**Request Body**")
        st.code("""{"text": "燃气调压箱的进气压力不能大于0.4MPa", "domain_hint": "gas_equipment"}""", language="json")
        st.markdown("**Response**")
        st.code("""{"success": true, "domain": "gas_equipment", "facts_added": 7}""", language="json")

    with st.expander("POST /api/v1/reason \u2014 \u8bf7\u6c42/\u54cd\u5e94\u793a\u4f8b", expanded=False):
        st.markdown("**Request Body**")
        st.code("""{"max_depth": 3}""", language="json")
        st.markdown("**Response**")
        st.code("""{"conclusions_count": 4, "conclusions": [{"subject": "调压箱A", "predicate": "is_a", "object": "设备"}]}""", language="json")

    with st.expander("POST /api/v1/retrieve \u2014 \u8bf7\u6c42/\u54cd\u5e94\u793a\u4f8b", expanded=False):
        req_json = '{"query": "燃气调压箱安全规范", "top_k": 5}'
        resp_json = '{"results": [{"triple": {"subject": "燃气调压箱", "predicate": "配备", "object": "安全阀"}, "score": 0.823, "source": "entity"}], "total": 5}'
        st.code("// Request\n" + req_json + "\n\n// Response\n" + resp_json, language="json")

# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### WebSocket \u2014 \u6d41\u5f0f Agent \u5bf9\u8bdd")
    st.markdown("\u9002\u5408\u524d\u7aef Agent \u754c\u9762\u5b9e\u65f6\u6d41\u5f0f\u8f93\u51fa\u3002")
    ws_code = """import websockets, json, asyncio

async def agent_chat():
    uri = "ws://localhost:8000/ws/agent"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "type": "user_message",
            "content": "燃气调压箱超过0.4MPa会有什么风险？"
        }))
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "tool_call":
                print(f"\U0001f527 {data['tool']}: {data['params']}")
            elif data["type"] == "tool_result":
                print(f"\u2705 {data['result']}")
            elif data["type"] == "final":
                print(f"\U0001f4ac {data['content']}")
                break

asyncio.run(agent_chat())"""
    st.code(ws_code, language="python")
    st.markdown("---")
    params_tbl([
        ("user_message", "object", True, "\u53d1\u9001\uff1a\u7528\u6237\u6d88\u606f"),
        ("tool_call", "object", False, "\u63a5\u6536\uff1aAgent \u8c03\u7528\u5de5\u5177"),
        ("tool_result", "object", False, "\u63a5\u6536\uff1a\u5de5\u5177\u6267\u884c\u7ed3\u679c"),
        ("thinking", "object", False, "\u63a5\u6536\uff1a\u601d\u8003\u8fc7\u7a0b"),
        ("final", "object", False, "\u63a5\u6536\uff1a\u6700\u7ec8\u56de\u590d"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### \U0001f4a1 \u96c6\u6210\u793a\u4f8b")

    with st.expander("\U0001f517 LangChain \u96c6\u6210", expanded=False):
        st.code("""from langchain_core.tools import tool
from src.clawra import Clawra

agent = Clawra(enable_memory=False)

@tool
def learn_knowledge(text: str) -> str:
    result = agent.learn(text)
    facts = result.get("extracted_facts", [])
    return "\\n".join(f"({f['subject']})-[{f['predicate']}]->({f['object']})" for f in facts)

@tool
def reason_about(topic: str) -> str:
    agent.add_fact(topic, "relates_to", "known")
    return "\\n".join(str(c.conclusion) for c in agent.reason(max_depth=2))""", language="python")

    with st.expander("\U0001f310 FastAPI \u540e\u7aef", expanded=False):
        st.code("""# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from src.clawra import Clawra

app = FastAPI(title="Clawra API")
agent = Clawra(enable_memory=False)

class LearnReq(BaseModel):
    text: str
    domain_hint: str | None = None

@app.post("/api/v1/learn")
def learn(req: LearnReq):
    return agent.learn(req.text, domain_hint=req.domain_hint)

@app.post("/api/v1/reason")
def reason():
    return {"conclusions": [str(c.conclusion) for c in agent.reason(max_depth=3)]}

# Run: uvicorn main:app --reload --port 8000""", language="python")

    with st.expander("\U0001f3a8 Streamlit \u524d\u7aef", expanded=False):
        st.code("""# streamlit_app.py
import streamlit as st
from src.clawra import Clawra

if "agent" not in st.session_state:
    st.session_state.agent = Clawra(enable_memory=False)

q = st.chat_input("Ask me anything...")
if q:
    with st.chat_message("user"): st.markdown(q)
    with st.chat_message("assistant"):
        result = st.session_state.agent.learn(q)
        for f in result.get("extracted_facts", []):
            st.markdown(f"- ({f['subject']}) -[{f['predicate']}]-> ({f['object']})")

# Run: streamlit run streamlit_app.py --server.port 8501""", language="python")

    with st.expander("\U0001f4ac \u5d4c\u5165\u5df2\u6709 Chatbot", expanded=False):
        st.code("""# Embed Clawra as a capability module
from src.clawra import Clawra

class ClawraAgent:
    def __init__(self):
        self.agent = Clawra(enable_memory=True)

    def chat(self, msg: str) -> str:
        self.agent.learn(msg)
        resp = self.agent.retrieve_knowledge(msg, top_k=3)
        return f"Learned {len(resp.results)} relevant facts"

agent = ClawraAgent()
print(agent.chat("Gas regulators need regular maintenance"))""", language="python")

    st.markdown("---")
    st.markdown("### \U0001f527 \u73af\u5883\u53d8\u91cf")
    st.code("""# .env
MINIMAX_API_KEY=your_key_here
MINIMAX_API_BASE=https://api.minimaxi.com/v1
NEO4J_URI=bolt://localhost:7687
CLAWRA_API_KEY=your_api_key
API_RATE_LIMIT=100""", language="bash")
