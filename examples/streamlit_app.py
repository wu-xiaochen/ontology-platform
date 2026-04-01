import streamlit as st
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.reasoner import Reasoner, Fact
from memory.base import SemanticMemory, EpisodicMemory
from agents.orchestrator import CognitiveOrchestrator

st.set_page_config(page_title="Clawra 认知智能体", page_icon="🧠", layout="wide")

@st.cache_resource
def init_orchestrator():
    """全局初始化 Clawra 认知中枢"""
    reasoner = Reasoner()
    reasoner.facts.append(Fact("System", "status", "online", confidence=1.0))
    
    # Neo4j 连接凭据（从环境变量读取，默认本地 Docker）
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "clawra2026")
    
    semantic_mem = SemanticMemory(uri=neo4j_uri, user=neo4j_user, password=neo4j_pass)
    semantic_mem.connect()  # 主动尝试连接 Neo4j
    
    episodic_mem = EpisodicMemory()
    return CognitiveOrchestrator(reasoner, semantic_mem, episodic_mem)

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = init_orchestrator()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是 Clawra 企业级认知智能体。您可以向我灌输知识，或者向我提问进行逻辑推导。"}
    ]

# =========================================
# 左侧栏：系统状态 + 实时本体图谱
# =========================================
with st.sidebar:
    st.title("🧠 Clawra 神经枢纽")
    st.markdown("---")

    # 引擎状态面板
    reasoner = st.session_state.orchestrator.reasoner
    fact_count = len(reasoner.facts)
    
    col1, col2 = st.columns(2)
    col1.metric("Reasoner 事实", fact_count)
    col2.metric("ChromaDB", "✅ Active")

    neo4j_connected = st.session_state.orchestrator.semantic_memory.is_connected
    if neo4j_connected:
        st.success("🟢 Neo4j: Connected")
        st.link_button("🔗 打开 Neo4j Browser", "http://localhost:7474")
    else:
        st.warning("🟡 Neo4j: 未连接 (仅本地推理)")
    st.markdown("---")

    # ================================
    # 实时本体知识图谱可视化
    # ================================
    st.subheader("🕸️ 本体知识图谱")
    
    if fact_count > 0:
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
            import networkx as nx

            # F4 修复：配置中文字体（macOS 系统自带）
            chinese_fonts = ['PingFang SC', 'STHeiti', 'Heiti TC', 'Arial Unicode MS', 'SimHei']
            font_set = False
            for font_name in chinese_fonts:
                matches = [f for f in fm.fontManager.ttflist if font_name in f.name]
                if matches:
                    plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
                    plt.rcParams['axes.unicode_minus'] = False
                    font_set = True
                    break
            if not font_set:
                plt.rcParams['axes.unicode_minus'] = False

            G = nx.DiGraph()
            for fact in reasoner.facts:
                G.add_node(fact.subject, node_type="entity")
                G.add_node(fact.object, node_type="entity")
                G.add_edge(fact.subject, fact.object, label=fact.predicate, weight=fact.confidence)

            # 布局优化：增加 k 值使节点更分散
            pos = nx.spring_layout(G, k=3.0, iterations=50, seed=42)
            
            # 创建高清画布
            fig, ax = plt.subplots(figsize=(8, 6), dpi=200)
            fig.patch.set_facecolor('#0E1117')
            ax.set_facecolor('#0E1117')

            # 节点：增大尺寸，使用更明亮的边框
            nx.draw_networkx_nodes(G, pos, ax=ax,
                node_color='#00D4FF', node_size=1000, alpha=0.95, edgecolors='#FFFFFF', linewidths=2)
            
            # 边：增加宽度和箭头大小
            nx.draw_networkx_edges(G, pos, ax=ax,
                edge_color='#FF6B6B', arrows=True, arrowsize=20,
                width=2, alpha=0.8, connectionstyle="arc3,rad=0.1")
            
            # 节点标签：增大字体，增加描边背景
            nx.draw_networkx_labels(G, pos, ax=ax,
                font_size=9, font_color='white', font_weight='bold',
                bbox=dict(facecolor='#0E1117', alpha=0.6, edgecolor='none', pad=1))
            
            # 边标签：增大字体
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos, edge_labels, ax=ax,
                font_size=7, font_color='#FFD93D', alpha=1.0, rotate=False,
                bbox=dict(facecolor='#0E1117', alpha=0.8, edgecolor='none'))

            ax.set_title(f"Ontology Knowledge Graph ({G.number_of_nodes()} nodes)",
                         color='white', fontsize=12, pad=15)
            ax.axis('off')
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        except ImportError:
            st.info("请安装 `networkx` 和 `matplotlib` 以启用图谱可视化。")
    else:
        st.caption("暂无知识，请向 Agent 灌输领域事实。")
    
    # 事实明细表
    if fact_count > 0:
        st.markdown("---")
        st.subheader("📋 事实明细")
        fact_data = []
        for f in reasoner.facts:
            fact_data.append({"主体": f.subject, "谓词": f.predicate, "客体": f.object, "置信": f"{f.confidence:.0%}"})
        st.dataframe(fact_data, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption("Module 4: Visual Reasoning Trace Dashboard")

# =========================================
# 右侧主界面：对话窗口
# =========================================
st.title("💡 Clawra 终端交互面 (Sandbox)")

def render_structured_trace(trace_data):
    """渲染结构化推理轨迹"""
    if isinstance(trace_data, str):
        # 兼容旧格式（如果是字符串，直接显示）
        st.code(trace_data, language="text")
        return
    
    # 归一化数据格式：兼容 List (orchestrator 原生) 和 Dict (UI 包装)
    nodes = []
    if isinstance(trace_data, list):
        nodes = trace_data
    elif isinstance(trace_data, dict):
        nodes = trace_data.get("trace_nodes") or trace_data.get("trace") or []
    
    for t in nodes:
        tool_name = t.get("tool", "")
        result = t.get("result", {})
        
        st.markdown(f"**🔌 工具调用:** `{tool_name}`")
        
        if isinstance(result, str):
            st.code(result, language="text")
            continue

        if isinstance(result, dict):
            # 摘要
            if "summary" in result:
                st.info(f"📋 {result['summary']}")
            
            # 已接受的三元组
            if "accepted_triples" in result and result["accepted_triples"]:
                st.markdown("**✅ 经哨兵验证通过的公理:**")
                triple_data = []
                for ref in result["accepted_triples"]:
                    triple_data.append({
                        "三元组": ref.get("triple", ""),
                        "置信度": f"{ref.get('confidence', 0):.2%}",
                        "来源": ref.get("source", "")
                    })
                st.dataframe(triple_data, use_container_width=True, hide_index=True)
            
            # 被拒绝的三元组
            if "rejected_triples" in result and result["rejected_triples"]:
                st.markdown("**❌ 被哨兵拒绝的公理:**")
                for ref in result["rejected_triples"]:
                    st.warning(f"{ref.get('triple', '')} — {ref.get('reason', '')}")
            
            # 向量检索上下文
            if "vector_context" in result and result["vector_context"]:
                st.markdown("**🔍 向量检索上下文 (ChromaDB):**")
                for i, ctx in enumerate(result["vector_context"], 1):
                    st.caption(f"  {i}. {ctx}")
            
            # 推理链
            if "reasoning_chain" in result and result["reasoning_chain"]:
                st.markdown("**🧠 前向链推理步骤:**")
                for i, step in enumerate(result["reasoning_chain"], 1):
                    rule_info = step.get("rule", {})
                    st.markdown(
                        f"  **Step {i}:** 规则 `{rule_info.get('name', '')}` (`{rule_info.get('id', '')}`)\n"
                        f"  - 前提: `{step.get('premise', '')}`\n"
                        f"  - 结论: `{step.get('conclusion', '')}`\n"
                        f"  - 置信度: **{step.get('confidence', 0):.2%}**"
                    )
            
            # 使用的事实
            if "facts_used" in result and result["facts_used"]:
                st.markdown("**📚 推理依据事实:**")
                for ref in result["facts_used"]:
                    st.caption(f"  • {ref}")
            
            # 整体置信度
            if "total_confidence" in result:
                conf = result["total_confidence"]
                st.metric("推理链整体置信度", f"{conf:.2%}")
            
            # Agent 结论
            if "agent_conclusion" in result:
                st.markdown(f"**💡 元认知结论:** {result['agent_conclusion']}")

            # Action 执行详情
            if "action_details" in result:
                st.markdown(f"**⚡ 行动详情:** {result['action_details']}")
            if "parameters" in result:
                st.json(result["parameters"])
        else:
            st.code(str(result), language="text")
        
        st.markdown("---")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "trace" in msg:
            with st.expander("🧐 查看认知引擎推理轨迹 (Reasoning Trace)"):
                render_structured_trace(msg["trace"])

# 用户输入交互
if prompt := st.chat_input("输入查询意图或业务语料..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Clawra 混合引擎思考中 (ReAct Agent Loop)..."):
            import asyncio
            start_time = time.time()
            response_data = asyncio.run(st.session_state.orchestrator.execute_task(st.session_state.messages))
            latency = time.time() - start_time
            
            intent = response_data.get("intent", "UNKNOWN")
            reply = response_data.get("message", "")
            
            if intent == "INGEST":
                facts = response_data.get("facts", [])
                if facts:
                    reply += f"\n\n**抽取出的结构化三元组:**\n"
                    for item in facts:
                        reply += f"- `({item[0]} -> {item[1]} -> {item[2]})`\n"

            # 构建结构化 trace 数据
            trace_logs = response_data.get("trace", [])
            structured_trace = {
                "intent": intent,
                "latency": f"{latency:.2f}s",
                "trace_nodes": trace_logs
            }

            st.markdown(reply)
            with st.expander("🧐 查看认知引擎推理轨迹 (Reasoning Trace)"):
                st.markdown(f"**意图路由:** `{intent}` | **延迟:** `{latency:.2f}s`")
                st.markdown("---")
                render_structured_trace(structured_trace)
                
            st.session_state.messages.append({"role": "assistant", "content": reply, "trace": structured_trace})
            
            # 触发侧边栏图谱刷新
            st.rerun()
