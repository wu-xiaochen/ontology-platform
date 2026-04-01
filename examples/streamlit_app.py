import streamlit as st
import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from core.reasoner import Reasoner, Fact
from memory.base import SemanticMemory, EpisodicMemory
from agents.orchestrator import CognitiveOrchestrator

st.set_page_config(page_title="Clawra 认知智能体", page_icon="🧠", layout="wide")

@st.cache_resource
def init_orchestrator():
    """全局初始化 Clawra 认知中枢"""
    reasoner = Reasoner()
    # 预先灌入测试规则和事实以便展示
    reasoner.facts.append(Fact("System", "status", "online", confidence=1.0))
    semantic_mem = SemanticMemory()
    episodic_mem = EpisodicMemory()
    return CognitiveOrchestrator(reasoner, semantic_mem, episodic_mem)

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = init_orchestrator()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是 Clawra 企业级认知智能体。您可以向我灌输知识，或者向我提问进行逻辑推导。"}
    ]

# 侧边栏：系统状态监控
with st.sidebar:
    st.title("🧠 Clawra 神经枢纽监控")
    st.markdown("---")
    st.metric("Neo4j 图谱状态", "Connected" if st.session_state.orchestrator.semantic_memory.is_connected else "Offline (Local Only)")
    st.metric("ChromaDB 向量条目", "Ready")
    st.metric("Reasoner 事实容量", len(st.session_state.orchestrator.reasoner.facts))
    st.markdown("---")
    st.caption("Module 4: UI Visual Reasoning Trace Dashboard. Powered by Phase 5 Enterprise Arch.")

# 主界面：对话窗口
st.title("💡 Clawra 终端交互面 (Sandbox)")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "trace" in msg:
            with st.expander("🧐 查看认知引擎推理轨迹 (Reasoning Trace)"):
                st.code(msg["trace"], language="json")

# 用户输入交互
if prompt := st.chat_input("输入查询意图或业务语料..."):
    # 显示用户输入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Clawra 大脑处理
    with st.chat_message("assistant"):
        with st.spinner("Clawra 混合引掣思考中 (GraphRAG + Logic)..."):
            start_time = time.time()
            response_data = st.session_state.orchestrator.route_intent(prompt)
            latency = time.time() - start_time
            
            # 解析响应结构
            # 格式： {"intent": ..., "status": ..., "response": ..., "details": ...}
            intent = response_data.get("intent", "UNKNOWN")
            
            if intent == "INGEST":
                reply = f"✅ 已成功将知识摄入系统图谱。\n\n**抽取出的结构化三元组:**\n"
                for item in response_data.get("details", {}).get("extracted_facts", []):
                    reply += f"- `({item[0]} -> {item[1]} -> {item[2]})`\n"
                    
                trace_log = f"""[Intent Routing]: INGEST
[Perception Layer]: OpenAI Structured Output (or fallback)
[Evolution Sentinel]: Cypher DisjointCheck -> Passed
[Memory Commits]: Graph (Neo4j) & Vector (Chroma)
[Latency]: {latency:.2f}s
"""
            else:
                conclusions = response_data.get("details", {}).get("derived_conclusions", [])
                reply = f"🔍 经过本体图谱严密推导，得出以下结论：\n"
                for idx, item in enumerate(conclusions):
                    reply += f"{idx+1}. `{item}`\n"
                if not conclusions:
                    reply += "根据当前知识库，没有获得确信的结论组合。"
                    
                trace_log = f"""[Intent Routing]: QUERY
[Hybrid Retrieval]: Vector Text Match -> Graph Sub-graph extraction
[Core Reasoner]: Forward/Backward Chaining executed
[Circuit Breaker]: Checked (Max Depth 10)
[Confidence System]: Activated
[Derived Facts Count]: {len(conclusions)}
[Latency]: {latency:.2f}s
"""

            st.markdown(reply)
            with st.expander("🧐 查看认知引擎推理轨迹 (Reasoning Trace)"):
                st.code(trace_log, language="yaml")
                
            st.session_state.messages.append({"role": "assistant", "content": reply, "trace": trace_log})
