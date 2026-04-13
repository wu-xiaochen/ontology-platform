"""
Clawra 完整功能 Demo

展示所有核心功能：
- 自主学习
- 领域自适应
- 批量处理
- 推理查询
- 知识图谱
- 统计分析
"""
import streamlit as st
import sys
import os
import json
import time
from typing import Dict, List, Any

# 修复导入路径：将项目根目录加入 sys.path，使用 src. 前缀导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入 Clawra 核心组件（使用 src. 前缀）
from src.clawra import Clawra, create_clawra

# 页面配置
st.set_page_config(
    page_title="Clawra 完整功能演示",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# st.rerun() 兼容处理：旧版 Streamlit 使用 experimental_rerun
# ─────────────────────────────────────────────
def safe_rerun():
    """兼容新旧版本的 rerun 函数"""
    if hasattr(st, 'rerun'):
        st.rerun()
    elif hasattr(st, 'experimental_rerun'):
        st.experimental_rerun()

# 自定义样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .success-box {
        background: #dcfce7;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 1rem;
        color: #166534;
    }
    .info-box {
        background: #dbeafe;
        border: 1px solid #93c5fd;
        border-radius: 8px;
        padding: 1rem;
        color: #1e40af;
    }
</style>
""", unsafe_allow_html=True)


# 初始化 session state
if 'clawra' not in st.session_state:
    st.session_state.clawra = create_clawra()
    st.session_state.logs = []
    st.session_state.patterns_learned = 0


def add_log(message: str):
    """添加日志"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")
    st.session_state.logs = st.session_state.logs[-50:]


# 侧边栏
with st.sidebar:
    st.markdown("## 🎛️ 控制面板")
    
    # 系统统计
    st.markdown("### 系统统计")
    stats = st.session_state.clawra.get_statistics()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("学习次数", stats['learning'].get('total_episodes', 0))
    with col2:
        st.metric("模式数量", stats['patterns'].get('total_patterns', 0))
    
    col3, col4 = st.columns(2)
    with col3:
        st.metric("事实数量", stats.get('facts', 0))
    with col4:
        st.metric("成功率", f"{stats['learning'].get('success_rate', 0)*100:.1f}%")
    
    # 日志
    st.markdown("### 系统日志")
    log_container = st.container(height=250)
    with log_container:
        for log in reversed(st.session_state.logs[-15:]):
            st.text(log)
    
    if st.button("🗑️ 清除日志"):
        st.session_state.logs = []
        safe_rerun()
    
    if st.button("🔄 重置系统"):
        st.session_state.clawra.reset()
        st.session_state.logs = []
        add_log("系统已重置")
        safe_rerun()


# 主页面
st.markdown('<div class="main-header">🧠 Clawra 完整功能演示</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">零硬编码 · 领域自适应 · 自主学习 · 统一接口</div>', unsafe_allow_html=True)

# 标签页
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 自主学习", "📚 批量学习", "🔍 推理查询", "📊 知识管理", "🌐 知识图谱"
])

# Tab 1: 自主学习
with tab1:
    st.markdown("### 自主学习")
    st.info("输入文本，Clawra 将自动识别领域、提取模式并学习")
    
    # 示例
    examples = [
        ("定义示例", "燃气调压箱：是一种将燃气调压器集成在金属箱体内的成套设备。"),
        ("功能示例", "功能：主要用于将上游管网的高压燃气降至下游用户所需的低压标准。"),
        ("属性示例", "额定流量：50, 100, 150，200, 300 m³/h"),
        ("规则示例", "如果设备是燃气调压箱，那么需要定期维护。"),
    ]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        input_text = st.text_area(
            "输入学习文本",
            height=150,
            placeholder="输入包含定义、功能、属性或规则的文本..."
        )
    with col2:
        st.markdown("**快速示例**")
        for name, text in examples:
            if st.button(name, key=f"ex_{name}"):
                st.session_state.input_text = text
                safe_rerun()
    
    if 'input_text' in st.session_state:
        input_text = st.session_state.input_text
        del st.session_state.input_text
    
    if st.button("🚀 开始学习", type="primary", use_container_width=True):
        if not input_text.strip():
            st.error("请输入学习文本")
        else:
            with st.spinner("正在学习..."):
                add_log(f"开始学习: {input_text[:30]}...")
                
                start_time = time.time()
                result = st.session_state.clawra.learn(input_text)
                elapsed = time.time() - start_time
                
                if result['success']:
                    st.session_state.patterns_learned += len(result['learned_patterns'])
                    add_log(f"学习成功: {len(result['learned_patterns'])} 个模式")
                    
                    st.success(f"✅ 学习成功！耗时 {elapsed:.3f}s")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("识别领域", result['domain'])
                    with col2:
                        st.metric("学习策略", result['strategy'])
                    with col3:
                        st.metric("模式数量", len(result['learned_patterns']))
                    with col4:
                        st.metric("学习耗时", f"{result['learning_time']:.3f}s")
                    
                    # 显示学习的模式
                    if result['learned_patterns']:
                        st.markdown("**学习的模式:**")
                        for pid in result['learned_patterns'][:5]:
                            patterns = st.session_state.clawra.query_patterns()
                            for p in patterns:
                                if p['id'] == pid:
                                    with st.expander(f"📌 {p['name']}"):
                                        st.text(f"类型: {p['logic_type']}")
                                        st.text(f"描述: {p['description']}")
                                        st.text(f"置信度: {p['confidence']}")
                                    break
                else:
                    error_msg = result.get('error', '未知错误')
                    add_log(f"学习失败: {error_msg}")
                    st.error(f"❌ 学习失败: {error_msg}")

# Tab 2: 批量学习
with tab2:
    st.markdown("### 批量学习")
    st.info("输入多条文本，一次性批量学习")
    
    batch_text = st.text_area(
        "输入多条文本（每行一条）",
        height=200,
        placeholder="燃气调压箱是一种设备。\n额定流量：50-100 m³/h\n功能：降压稳压"
    )
    
    if st.button("📚 批量学习", type="primary", use_container_width=True):
        if not batch_text.strip():
            st.error("请输入学习文本")
        else:
            texts = [t.strip() for t in batch_text.split('\n') if t.strip()]
            
            with st.spinner(f"正在批量学习 {len(texts)} 条文本..."):
                add_log(f"开始批量学习: {len(texts)} 条文本")
                
                progress_bar = st.progress(0)
                results = []
                
                for i, text in enumerate(texts):
                    result = st.session_state.clawra.learn(text)
                    results.append(result)
                    progress_bar.progress((i + 1) / len(texts))
                
                total_patterns = sum(len(r['learned_patterns']) for r in results)
                success_count = sum(1 for r in results if r['success'])
                
                add_log(f"批量学习完成: {success_count}/{len(texts)} 成功, {total_patterns} 模式")
                
                st.success(f"✅ 批量学习完成！")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("成功/总数", f"{success_count}/{len(texts)}")
                with col2:
                    st.metric("总模式数", total_patterns)
                with col3:
                    avg_patterns = total_patterns / len(texts) if texts else 0
                    st.metric("平均模式/条", f"{avg_patterns:.1f}")

# Tab 3: 推理查询
with tab3:
    st.markdown("### 推理查询")
    st.info("添加事实并执行推理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**添加事实**")
        subject = st.text_input("主语", placeholder="例如: 调压箱A")
        predicate = st.selectbox(
            "谓语",
            ["is_a", "has_property", "requires", "belongs_to", "located_at"]
        )
        obj = st.text_input("宾语", placeholder="例如: 燃气调压箱")
        confidence = st.slider("置信度", 0.0, 1.0, 0.9)
        
        if st.button("➕ 添加事实"):
            if subject and obj:
                st.session_state.clawra.add_fact(subject, predicate, obj, confidence)
                add_log(f"添加事实: {subject} {predicate} {obj}")
                st.success(f"已添加: {subject} {predicate} {obj}")
            else:
                st.error("请填写完整的事实信息")
    
    with col2:
        st.markdown("**执行推理**")
        max_depth = st.slider("推理深度", 1, 5, 2)
        
        if st.button("🧠 执行推理", type="primary"):
            with st.spinner("正在推理..."):
                add_log(f"执行推理: 深度={max_depth}")
                
                conclusions = st.session_state.clawra.reason(max_depth=max_depth)
                
                if conclusions:
                    st.success(f"✅ 推理完成！推导出 {len(conclusions)} 个结论")
                    for i, conclusion in enumerate(conclusions[:10]):
                        st.text(f"{i+1}. {conclusion}")
                    if len(conclusions) > 10:
                        st.text(f"... 还有 {len(conclusions) - 10} 个结论")
                else:
                    st.info("ℹ️ 没有新的推理结论")

# Tab 4: 知识管理
with tab4:
    st.markdown("### 知识管理")
    
    # 查询过滤
    col1, col2, col3 = st.columns(3)
    with col1:
        domain_filter = st.selectbox(
            "领域过滤",
            ["全部", "gas_equipment", "generic", "medical", "legal"]
        )
    with col2:
        type_filter = st.selectbox(
            "类型过滤",
            ["全部", "rule", "behavior", "constraint", "policy"]
        )
    with col3:
        keyword = st.text_input("关键词搜索")
    
    # 查询
    domain = None if domain_filter == "全部" else domain_filter
    logic_type = None if type_filter == "全部" else type_filter
    
    patterns = st.session_state.clawra.query_patterns(
        domain=domain,
        logic_type=logic_type,
        keyword=keyword if keyword else None
    )
    
    st.markdown(f"**查询结果: {len(patterns)} 个模式**")
    
    # 显示模式
    for p in patterns:
        with st.expander(f"📌 {p['name']} ({p['logic_type']})"):
            col1, col2 = st.columns(2)
            with col1:
                st.text(f"ID: {p['id']}")
                st.text(f"领域: {p['domain']}")
            with col2:
                st.text(f"置信度: {p['confidence']}")
            st.text(f"描述: {p['description']}")

# Tab 5: 知识图谱
with tab5:
    st.markdown("### 知识图谱可视化")
    
    try:
        from pyvis.network import Network as PyVisNetwork
        
        # 创建网络图
        net = PyVisNetwork(height="500px", bgcolor="#ffffff", font_color="#1e293b")
        
        # 获取所有模式
        patterns = st.session_state.clawra.query_patterns()
        
        # 添加节点
        nodes_added = set()
        for p in patterns:
            node_id = p['id']
            if node_id not in nodes_added:
                color = {
                    'rule': '#3b82f6',
                    'behavior': '#10b981',
                    'constraint': '#f59e0b',
                    'policy': '#8b5cf6'
                }.get(p['logic_type'], '#6b7280')
                
                net.add_node(
                    node_id,
                    label=p['name'][:20],
                    title=p['description'],
                    color=color,
                    size=20
                )
                nodes_added.add(node_id)
        
        # 设置布局
        net.set_options("""
        {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 100
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 150}
          }
        }
        """)
        
        # 保存并显示
        graph_path = "/tmp/clawra_graph.html"
        net.save_graph(graph_path)
        
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph_html = f.read()
        
        st.components.v1.html(graph_html, height=550)
        
        st.info(f"📊 图谱包含 {len(nodes_added)} 个节点")
        
    except Exception as e:
        st.error(f"图谱渲染失败: {e}")
        st.info("请确保已安装 pyvis: pip install pyvis")

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b;'>"
    "Clawra 自主进化 Agent Framework v2.0 | 完整功能版本"
    "</div>",
    unsafe_allow_html=True
)
