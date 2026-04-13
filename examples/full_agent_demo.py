import streamlit as st
import os
import time
import asyncio
import base64

# ==========================================
# 页面配置与顶级全局状态
# ==========================================
st.set_page_config(
    page_title="Clawra Full Agent | 全能力动态智能体",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 动态配置加载路径
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.reasoner import Reasoner
from src.memory.base import SemanticMemory, EpisodicMemory
from src.agents.orchestrator import Orchestrator

# ==========================================
# 高端拟态化 CSS (Neon & Glass)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');
    
    .chat-user {
        border-right: 2px solid #58a6ff;
        background: transparent;
        padding: 1rem;
        margin-bottom: 15px;
        color: #A1A1AA;
    }
    .chat-assistant {
        border-left: 3px solid #00FF66;
        background: rgba(0, 255, 102, 0.03);
        padding: 1rem;
        margin-bottom: 15px;
        color: #FFFFFF;
        box-shadow: -10px 0 20px -10px rgba(0,255,102,0.2) inset;
    }
    
    .stMetric {
        background: #09090b;
        border: 1px solid #27272a;
        border-radius: 6px;
        padding: 15px;
        transition: all 0.2s ease;
    }
    
    .stMetric:hover {
        border-color: #00FF66;
        box-shadow: 0 0 10px rgba(0,255,102,0.1);
    }
    
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 初始化 Agent 核心依赖 (跨会话缓存)
# ==========================================
@st.cache_resource
def get_cognitive_architecture():
    reasoner = Reasoner()
    semantic_mem = SemanticMemory()
    semantic_mem.connect()
    episodic_mem = EpisodicMemory()
    orchestrator = Orchestrator(reasoner, semantic_mem, episodic_mem)
    return orchestrator

orchestrator = get_cognitive_architecture()

# ==========================================
# 工具函数：渲染推理轨迹节点
# ==========================================
def render_trace_node(node):
    tool = node.get("tool", "Unknown")
    latency = node.get("latency", "0s")
    result = node.get("result", {})
    
    with st.container():
        st.markdown(f"**🔧 {tool}** `({latency})`")
        if isinstance(result, dict):
            status_code = result.get("status", "UNKNOWN")
            
            if status_code == "BLOCKED":
                st.error(f"🚫 **安全拦截**: {result.get('summary', '被策略阻断')}")
                for risk in result.get("risks", []):
                    st.caption(f"⚠️ {risk}")
            elif status_code == "ERROR":
                st.error(f"❌ **执行错误**: {result.get('msg', '未知故障')}")
            else:
                if "summary" in result:
                    st.info(result["summary"])
                    
                # 针对不同工具的美化：
                if tool == "ingest_knowledge" and "accepted_triples" in result:
                    triples = [t.get("triple", "") for t in result["accepted_triples"]]
                    if triples:
                        st.code("\n".join(triples), language="text")
                elif tool == "query_graph":
                    if "reasoning_chain" in result and result["reasoning_chain"]:
                        st.write("**🧠 符号推导规则链:**")
                        for s in result["reasoning_chain"]:
                            st.caption(f"- {s.get('conclusion', '')}")
                    meta = result.get("metacognition", {})
                    if meta.get('total_confidence', 0) > 0:
                        st.success(f"💡 {meta.get('result', '')}")
        else:
            st.caption(str(result))

# ==========================================
# 侧边栏：模块监控与动态知识图谱
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/nolan/256/brain.png", width=80)
    st.title("Clawra Agent Hub")
    
    st.markdown("### ⚙️ 神经状态监测")
    col1, col2 = st.columns(2)
    col1.metric("推理机事实数", len(orchestrator.reasoner.facts))
    # 尝试获取Neo4j的实际数量，如果没有连接则显示 Local
    graph_count = orchestrator.semantic_memory.get_total_facts_count() if orchestrator.semantic_memory.is_connected else 0
    col2.metric("Neo4j 图谱数", graph_count)
    
    if orchestrator.semantic_memory.is_connected:
        st.success("🟢 Neo4j: Active")
    else:
        st.warning("🟡 Graph: Local Fallback")

    st.markdown("---")
    st.markdown("### 🕸️ 知识图谱引擎可视化")
    def render_graph_html(height="400px"):
        try:
            from pyvis.network import Network
            net = Network(height=height, width="100%", bgcolor="#0b0f19", font_color="#e6edf3", directed=True)
            net.toggle_physics(False) 
            
            display_facts = list(orchestrator.reasoner.facts)
            if len(display_facts) < 5 and orchestrator.semantic_memory.is_connected:
                samples = orchestrator.semantic_memory.get_sample_triples(limit=30)
                display_facts.extend(samples)
                
            for fact in display_facts:
                # 若来自图样本，则高亮区分
                is_sample = getattr(fact, "source", "") == "neo4j_sample"
                node_color = "#FF6B6B" if is_sample else "#00D4FF"
                size = 15 if is_sample else 20
                net.add_node(fact.subject, label=fact.subject, color=node_color, size=size)
                net.add_node(fact.object, label=fact.object, color="#FFCC00", size=15)
                net.add_edge(fact.subject, fact.object, label=fact.predicate, color="#FFFFFF", width=1)
                
            path = "temp_agent_graph.html"
            net.save_graph(path)
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
            if os.path.exists(path):
                os.remove(path)
            return html
        except Exception as e:
            return f"图谱渲染失败 (请确保已安装 pyvis): {e}"

    import streamlit.components.v1 as components
    # 即使数量为0，也可以根据连通性展示空网格
    html = render_graph_html()
    components.html(html, height=450)
    
    if st.button("🗑️ 清空对话记忆 (Clear)", use_container_width=True):
        st.session_state.messages = []
        if hasattr(st, 'rerun'):
            st.rerun()
        else:
            st.experimental_rerun()

# ==========================================
# 主界面构建：基于对话的超级 Agent
# ==========================================
st.markdown("### 💬 全能力交互式 Agent")
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好，我是搭载了 Clawra 编排器的全能力智能体。侧边栏已挂载了互动图谱。\n您可以输入技术文档让我学习提取，也可以直接使用自然语言询问逻辑推演结果！", "trace": []}
    ]

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-user'><b>👤 您:</b><br/>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-assistant'><b>🤖 Agent 回应:</b><br/>{msg['content']}</div>", unsafe_allow_html=True)
        if msg.get("trace"):
            with st.expander("✨ 展开引擎推导轨迹追踪 (Reasoning Trace)"):
                for t in msg["trace"]:
                    render_trace_node(t)

if prompt := st.chat_input("帮我提取一下这篇采购规范的知识..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<div class='chat-user'><b>👤 您:</b><br/>{prompt}</div>", unsafe_allow_html=True)

    async def run_agent_task(orch, history):
        return await orch.execute_task(messages=history[-6:])

    # ====== 新版流程展示 (st.status 动态追踪流) ======
    status = st.status("🤖 Orchestrator Agent 突触激活中...", expanded=True)
    with status:
        st.markdown("*正在调度底层工具集...*")
        
        try:
            start_time = time.time()
            response = asyncio.run(run_agent_task(orchestrator, st.session_state.messages))
            latency = time.time() - start_time
            
            trace_logs = response.get("trace", [])
            reply_text = response.get("message", "抱歉，系统返回为空。")
            
            status.update(label=f"✨ 推理完成 (耗时 {latency:.2f}s)", state="complete", expanded=False)
            
            # 保存到状态
            st.session_state.messages.append({
                "role": "assistant",
                "content": reply_text,
                "trace": trace_logs
            })
            
            # 在外层立刻渲染助手回答
            if hasattr(st, 'rerun'):
                st.rerun()
            else:
                st.experimental_rerun()
                
        except Exception as e:
            import traceback
            status.update(label="❌ Agent 后台核心链路执行崩溃", state="error", expanded=True)
            st.error(f"出现错误：{str(e)}")
            st.code(traceback.format_exc())
