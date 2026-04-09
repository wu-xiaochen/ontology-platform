"""
Clawra 生产级 Demo

功能验证:
- 配置管理 ✅
- 自主学习 ✅  
- 领域自适应 ✅
- 推理引擎 ✅
- 知识图谱可视化 ✅
- 日志系统 ✅

使用方法:
streamlit run examples/clawra_production_demo.py
"""
import streamlit as st
import sys
import os
import json
import time
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入核心模块
from src.evolution.unified_logic import UnifiedLogicLayer, LogicType
from src.evolution.meta_learner import MetaLearner
from src.evolution.rule_discovery import RuleDiscoveryEngine
from src.core.reasoner import Reasoner, Fact
from src.utils.config import get_config, validate_config

# 页面配置
st.set_page_config(
    page_title="Clawra 自主进化 Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #0f172a;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #64748b;
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
    .warning-box {
        background: #fef3c7;
        border: 1px solid #fcd34d;
        border-radius: 8px;
        padding: 1rem;
        color: #92400e;
    }
    .log-entry {
        font-family: monospace;
        font-size: 0.8rem;
        padding: 0.25rem 0;
        border-bottom: 1px solid #e2e8f0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# 初始化 session state
if 'logic_layer' not in st.session_state:
    st.session_state.logic_layer = UnifiedLogicLayer()
    st.session_state.discovery = RuleDiscoveryEngine(st.session_state.logic_layer)
    st.session_state.meta = MetaLearner(st.session_state.logic_layer, st.session_state.discovery)
    st.session_state.reasoner = Reasoner()
    st.session_state.logs = []
    st.session_state.learned_count = 0
    st.session_state.inference_count = 0


def add_log(message: str, level: str = "info"):
    """添加日志"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.logs.append({
        "time": timestamp,
        "message": message,
        "level": level
    })
    # 只保留最近50条日志
    st.session_state.logs = st.session_state.logs[-50:]


# 侧边栏
with st.sidebar:
    st.markdown("## 🎛️ 控制面板")
    
    # 配置状态
    st.markdown("### 系统状态")
    config = get_config()
    validation = validate_config()
    
    if validation["valid"]:
        st.success("✅ 配置正常")
    else:
        st.warning("⚠️ 配置不完整")
        for error in validation["errors"]:
            st.text(f"• {error}")
    
    # 统计信息
    st.markdown("### 统计信息")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("学习次数", st.session_state.learned_count)
    with col2:
        st.metric("推理次数", st.session_state.inference_count)
    
    # 日志显示
    st.markdown("### 系统日志")
    log_container = st.container(height=300)
    with log_container:
        for log in reversed(st.session_state.logs[-20:]):
            color = {"info": "🔵", "success": "🟢", "warning": "🟡", "error": "🔴"}.get(log["level"], "⚪")
            st.text(f"{color} [{log['time']}] {log['message']}")
    
    # 清除日志按钮
    if st.button("🗑️ 清除日志"):
        st.session_state.logs = []
        st.rerun()


# 主页面
st.markdown('<div class="main-header">🧠 Clawra 自主进化 Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">零硬编码 · 领域自适应 · 自主学习</div>', unsafe_allow_html=True)

# 标签页
tab1, tab2, tab3, tab4 = st.tabs(["📝 自主学习", "🔍 推理查询", "🌐 知识图谱", "⚙️ 系统配置"])

# Tab 1: 自主学习
with tab1:
    st.markdown("### 自主学习")
    st.info("输入文本，Agent 将自动识别领域并学习其中的逻辑模式")
    
    # 示例文本
    examples = [
        "如果设备是燃气调压箱，那么需要定期维护。",
        "患者血糖高于7.0需要服用胰岛素。",
        "合同违约需要支付违约金。"
    ]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        input_text = st.text_area(
            "输入学习文本",
            height=150,
            placeholder="输入包含逻辑关系的文本，例如：如果A是B，那么C需要D..."
        )
    with col2:
        st.markdown("**示例文本**")
        for i, ex in enumerate(examples):
            if st.button(f"示例 {i+1}", key=f"ex_{i}"):
                st.session_state.input_text = ex
                st.rerun()
    
    # 使用 session state 中的值
    if 'input_text' in st.session_state:
        input_text = st.session_state.input_text
        del st.session_state.input_text
    
    # 学习按钮
    if st.button("🚀 开始学习", type="primary", use_container_width=True):
        if not input_text.strip():
            st.error("请输入学习文本")
        else:
            with st.spinner("正在学习..."):
                add_log(f"开始学习内容: {input_text[:30]}...", "info")
                
                # 执行学习
                result = st.session_state.meta.learn(input_text, input_type="text")
                
                if result["success"]:
                    st.session_state.learned_count += len(result["learned_patterns"])
                    add_log(f"学习成功: 发现 {len(result['learned_patterns'])} 个模式", "success")
                    
                    # 显示结果
                    st.success(f"✅ 学习成功！")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("识别领域", result["domain"])
                    with col2:
                        st.metric("学习模式", len(result["learned_patterns"]))
                    with col3:
                        st.metric("学习耗时", f"{result['learning_time']:.3f}s")
                    
                    # 显示学习的模式
                    if result["learned_patterns"]:
                        st.markdown("**学习的模式:**")
                        for pid in result["learned_patterns"]:
                            if pid in st.session_state.logic_layer.patterns:
                                pattern = st.session_state.logic_layer.patterns[pid]
                                st.text(f"• {pattern.name}: {pattern.description}")
                else:
                    error_msg = result.get("error", "未知错误")
                    add_log(f"学习失败: {error_msg}", "error")
                    st.error(f"❌ 学习失败: {error_msg}")

# Tab 2: 推理查询
with tab2:
    st.markdown("### 推理查询")
    st.info("添加事实并执行推理，查看推导出的新知识")
    
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
                fact = Fact(subject, predicate, obj, confidence)
                st.session_state.reasoner.add_fact(fact)
                add_log(f"添加事实: {subject} {predicate} {obj}", "info")
                st.success(f"已添加: {subject} {predicate} {obj}")
            else:
                st.error("请填写完整的事实信息")
    
    with col2:
        st.markdown("**执行推理**")
        max_depth = st.slider("推理深度", 1, 5, 2)
        
        if st.button("🧠 执行推理", type="primary"):
            with st.spinner("正在推理..."):
                result = st.session_state.reasoner.forward_chain(max_depth=max_depth)
                st.session_state.inference_count += 1
                add_log(f"执行推理: 深度={max_depth}", "info")
                
                # 显示推理结果
                if hasattr(result, 'conclusions') and result.conclusions:
                    st.success(f"✅ 推理完成！推导出 {len(result.conclusions)} 个结论")
                    
                    for i, conclusion in enumerate(result.conclusions[:10]):
                        st.text(f"{i+1}. {conclusion}")
                    
                    if len(result.conclusions) > 10:
                        st.text(f"... 还有 {len(result.conclusions) - 10} 个结论")
                else:
                    st.info("ℹ️ 没有新的推理结论")

# Tab 3: 知识图谱
with tab3:
    st.markdown("### 知识图谱可视化")
    
    try:
        from pyvis.network import Network as PyVisNetwork
        
        # 创建网络图
        net = PyVisNetwork(height="500px", bgcolor="#ffffff", font_color="#1e293b")
        
        # 添加节点和边
        nodes_added = set()
        
        # 从逻辑层添加模式
        for pid, pattern in st.session_state.logic_layer.patterns.items():
            if pattern.logic_type == LogicType.RULE and pattern.conditions:
                # 简化显示规则
                node_label = pattern.name[:20] if pattern.name else pid[:15]
                if pid not in nodes_added:
                    net.add_node(pid, label=node_label, color="#3b82f6", size=20)
                    nodes_added.add(pid)
        
        # 从推理引擎添加事实
        for fact in st.session_state.reasoner.facts:
            if fact.subject not in nodes_added:
                net.add_node(fact.subject, label=fact.subject, color="#10b981", size=15)
                nodes_added.add(fact.subject)
            if fact.object not in nodes_added:
                net.add_node(fact.object, label=fact.object, color="#10b981", size=15)
                nodes_added.add(fact.object)
            
            net.add_edge(fact.subject, fact.object, label=fact.predicate, color="#94a3b8")
        
        # 设置物理布局
        net.set_options("""
        {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 100,
              "springConstant": 0.08
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
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

# Tab 4: 系统配置
with tab4:
    st.markdown("### 系统配置")
    
    config = get_config()
    validation = validate_config()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**LLM 配置**")
        st.json({
            "base_url": config.llm.base_url,
            "model": config.llm.model,
            "configured": config.llm.is_configured()
        })
    
    with col2:
        st.markdown("**数据库配置**")
        st.json({
            "neo4j_uri": config.database.neo4j_uri,
            "configured": config.database.is_configured()
        })
    
    st.markdown("**应用配置**")
    st.json({
        "debug": config.app.debug,
        "log_level": config.app.log_level,
        "data_dir": config.app.data_dir
    })
    
    # 验证结果
    st.markdown("**验证结果**")
    if validation["valid"]:
        st.success("✅ 所有配置正常")
    else:
        st.error("❌ 配置验证失败")
        for error in validation["errors"]:
            st.text(f"错误: {error}")
    
    if validation["warnings"]:
        st.warning("⚠️ 警告")
        for warning in validation["warnings"]:
            st.text(f"警告: {warning}")

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b;'>"
    "Clawra 自主进化 Agent Framework | 生产就绪版本"
    "</div>",
    unsafe_allow_html=True
)
