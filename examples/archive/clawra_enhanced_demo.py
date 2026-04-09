"""
Clawra Enhanced Demo - 增强版自主进化演示
===========================================

Phase 1 改进:
1. 知识图谱可视化 (PyVis + NetworkX)
2. 实时学习过程动画
3. 学习效果对比
4. 交互式规则编辑
"""
import streamlit as st
import sys
import os
import json
import time
from typing import List, Dict
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.evolution.unified_logic import UnifiedLogicLayer, LogicType, LogicPattern
from src.evolution.rule_discovery import RuleDiscoveryEngine
from src.evolution.meta_learner import MetaLearner

# 页面配置
st.set_page_config(
    page_title="Clawra 自主进化引擎 - 增强版",
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
        font-size: 1.2rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
    }
    .learning-step {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3b82f6;
        background: #f8fafc;
        border-radius: 0 0.25rem 0.25rem 0;
    }
    .pattern-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# 初始化系统
@st.cache_resource
def init_system():
    logic_layer = UnifiedLogicLayer()
    discovery_engine = RuleDiscoveryEngine(logic_layer)
    meta_learner = MetaLearner(logic_layer, discovery_engine)
    return logic_layer, discovery_engine, meta_learner

logic_layer, discovery_engine, meta_learner = init_system()

# 初始化会话状态
if 'learning_history' not in st.session_state:
    st.session_state.learning_history = []
if 'patterns' not in st.session_state:
    st.session_state.patterns = []

# ==================== 头部 ====================
st.markdown('<div class="main-header">🧠 Clawra 自主进化引擎</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">零硬编码 · 领域自适应 · 自我进化</div>', unsafe_allow_html=True)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("📊 系统仪表盘")
    
    # 实时统计
    stats = logic_layer.get_statistics()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("逻辑模式", stats["total_patterns"], delta="+" + str(len(st.session_state.patterns)))
    with col2:
        st.metric("学习次数", len(st.session_state.learning_history))
    
    # 类型分布
    st.subheader("📈 类型分布")
    for logic_type, count in stats["by_type"].items():
        if count > 0:
            st.progress(count / max(stats["total_patterns"], 1), text=f"{logic_type}: {count}")
    
    # 领域分布
    st.subheader("🌍 领域覆盖")
    for domain, count in stats.get("by_domain", {}).items():
        st.markdown(f"<span style='color: #3b82f6'>●</span> **{domain}**: {count} 模式", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 学习历史
    st.subheader("📚 学习历史")
    for i, record in enumerate(reversed(st.session_state.learning_history[-5:])):
        with st.expander(f"📝 {record['timestamp']}", expanded=False):
            st.markdown(f"**领域**: {record['domain']}")
            st.markdown(f"**策略**: {record['strategy']}")
            st.markdown(f"**发现**: {len(record['patterns'])} 个模式")

# ==================== 主界面 ====================

# 标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 实时学习", 
    "🔍 规则发现", 
    "🕸️ 知识图谱",
    "⚙️ 系统配置"
])

# ==================== Tab 1: 实时学习 ====================
with tab1:
    st.header("🎯 实时规则学习")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 输入区域
        st.subheader("输入学习文本")
        
        # 预设示例
        examples = {
            "燃气设备维护": "如果设备是燃气调压箱，那么需要定期维护。维护周期是6个月。",
            "医疗诊断": "如果患者血糖高于7.0mmol/L，那么诊断为糖尿病。需要定期监测。",
            "合同违约": "如果合同一方未按期付款，那么构成违约。需要支付违约金。",
            "自定义": ""
        }
        
        selected_example = st.selectbox("选择示例或自定义", list(examples.keys()))
        
        if selected_example == "自定义":
            learn_text = st.text_area(
                "输入包含逻辑关系的文本：",
                height=120,
                placeholder="例如：如果A是B，那么C是D。"
            )
        else:
            learn_text = st.text_area(
                "输入包含逻辑关系的文本：",
                value=examples[selected_example],
                height=120
            )
        
        # 高级选项
        with st.expander("高级选项"):
            domain_hint = st.selectbox(
                "领域提示（可选）",
                ["自动检测", "medical", "legal", "gas_equipment", "finance", "engineering"]
            )
            domain_hint = None if domain_hint == "自动检测" else domain_hint
        
        # 学习按钮
        if st.button("🚀 开始自主学习", type="primary", use_container_width=True):
            if learn_text.strip():
                # 创建占位符用于实时更新
                progress_placeholder = st.empty()
                result_placeholder = st.empty()
                
                with progress_placeholder.container():
                    st.info("🔍 步骤 1/4: 识别领域...")
                    time.sleep(0.3)
                    
                    # 执行学习
                    result = meta_learner.learn(learn_text, input_type="text", domain_hint=domain_hint)
                    
                    st.info("🔍 步骤 2/4: 提取逻辑模式...")
                    time.sleep(0.3)
                    
                    st.info("🔍 步骤 3/4: 验证模式...")
                    time.sleep(0.3)
                    
                    st.info("🔍 步骤 4/4: 集成到知识库...")
                    time.sleep(0.3)
                
                progress_placeholder.empty()
                
                # 记录学习历史
                st.session_state.learning_history.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "domain": result["domain"],
                    "strategy": result["strategy"],
                    "patterns": result["learned_patterns"],
                    "text": learn_text[:50] + "..." if len(learn_text) > 50 else learn_text
                })
                
                # 显示结果
                with result_placeholder.container():
                    st.success(f"✅ 学习完成！发现 {len(result['learned_patterns'])} 个逻辑模式")
                    
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("识别领域", result["domain"])
                    with cols[1]:
                        st.metric("学习策略", result["strategy"])
                    with cols[2]:
                        st.metric("耗时", f"{result['learning_time']:.3f}s")
                    
                    # 显示发现的模式
                    if result["learned_patterns"]:
                        st.subheader("📋 发现的模式")
                        for pattern_id in result["learned_patterns"]:
                            if pattern_id in logic_layer.patterns:
                                pattern = logic_layer.patterns[pattern_id]
                                with st.container():
                                    st.markdown(f"<div class='pattern-card'>", unsafe_allow_html=True)
                                    st.markdown(f"**{pattern.name}** ({pattern.logic_type.value})")
                                    st.markdown(f"_{pattern.description}_")
                                    st.markdown(f"<span style='color: #3b82f6'>置信度: {pattern.confidence:.0%}</span>", unsafe_allow_html=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("⚠️ 请输入学习文本")
    
    with col2:
        st.subheader("📊 学习统计")
        
        # 实时统计
        stats = meta_learner.get_learning_statistics()
        
        st.metric("总学习次数", stats["total_episodes"])
        st.metric("成功率", f"{stats['success_rate']:.0%}")
        st.metric("平均耗时", f"{stats['avg_learning_time']:.3f}s")
        
        # 策略效果
        st.markdown("---")
        st.subheader("🎯 策略效果")
        for strategy, effectiveness in stats.get("strategy_effectiveness", {}).items():
            if effectiveness["attempts"] > 0:
                success_rate = effectiveness["successes"] / effectiveness["attempts"]
                st.progress(success_rate, text=f"{strategy}: {success_rate:.0%}")

# ==================== Tab 2: 规则发现 ====================
with tab2:
    st.header("🔍 从数据中归纳规则")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("输入事实数据")
        
        # 预设数据
        data_examples = {
            "设备分类": '''[
  {"subject": "调压箱A", "predicate": "is_a", "object": "燃气调压箱"},
  {"subject": "调压箱B", "predicate": "is_a", "object": "燃气调压箱"},
  {"subject": "调压箱C", "predicate": "is_a", "object": "燃气调压箱"},
  {"subject": "燃气调压箱", "predicate": "is_a", "object": "燃气设备"},
  {"subject": "燃气设备", "predicate": "requires", "object": "定期维护"}
]''',
            "传递关系": '''[
  {"subject": "A", "predicate": "part_of", "object": "B"},
  {"subject": "B", "predicate": "part_of", "object": "C"},
  {"subject": "C", "predicate": "part_of", "object": "D"},
  {"subject": "X", "predicate": "part_of", "object": "Y"},
  {"subject": "Y", "predicate": "part_of", "object": "Z"}
]''',
            "自定义": "[]"
        }
        
        selected_data = st.selectbox("选择示例数据", list(data_examples.keys()))
        
        fact_data = st.text_area(
            "JSON 格式事实数据：",
            value=data_examples[selected_data],
            height=200
        )
        
        if st.button("🔍 发现规则", type="primary"):
            try:
                facts = json.loads(fact_data)
                if facts:
                    with st.spinner("分析数据模式..."):
                        discovered = discovery_engine.discover_from_facts(facts)
                    
                    st.session_state.discovered_rules = discovered
                    
                    if discovered:
                        st.success(f"✅ 发现 {len(discovered)} 条潜在规则")
                    else:
                        st.info("ℹ️ 未发现明显规则模式")
                else:
                    st.warning("⚠️ 请输入事实数据")
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON 格式错误: {e}")
    
    with col2:
        st.subheader("📋 发现的规则")
        
        if "discovered_rules" in st.session_state:
            for rule in st.session_state.discovered_rules:
                with st.container():
                    st.markdown(f"<div class='pattern-card'>", unsafe_allow_html=True)
                    
                    # 规则头部
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"**{rule['name']}**")
                    with cols[1]:
                        st.markdown(f"<span style='background: #dbeafe; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;'>{rule['type']}</span>", unsafe_allow_html=True)
                    
                    st.markdown(f"_{rule['description']}_")
                    
                    # 置信度和支持度
                    cols = st.columns(2)
                    with cols[0]:
                        st.progress(rule['confidence'], text=f"置信度: {rule['confidence']:.0%}")
                    with cols[1]:
                        st.markdown(f"支持度: {rule['support']} 实例")
                    
                    # 条件和结论
                    with st.expander("查看详情"):
                        st.markdown("**条件:**")
                        for cond in rule['conditions']:
                            st.markdown(f"  - `{cond}`")
                        st.markdown("**结论:**")
                        for action in rule['actions']:
                            st.markdown(f"  - `{action}`")
                    
                    st.markdown("</div>", unsafe_allow_html=True)

# ==================== Tab 3: 知识图谱 ====================
with tab3:
    st.header("🕸️ 知识图谱可视化")
    
    try:
        from pyvis.network import Network
        import networkx as nx
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            st.subheader("图谱控制")
            
            # 过滤选项
            show_rules = st.checkbox("显示规则节点", value=True)
            show_facts = st.checkbox("显示事实节点", value=True)
            
            st.markdown("---")
            
            # 添加新事实
            st.subheader("➕ 添加事实")
            subject = st.text_input("主语 (Subject)", placeholder="例如: 燃气调压箱")
            predicate = st.text_input("谓词 (Predicate)", placeholder="例如: is_a")
            obj = st.text_input("宾语 (Object)", placeholder="例如: 燃气设备")
            
            if st.button("添加到图谱"):
                if subject and predicate and obj:
                    if 'custom_facts' not in st.session_state:
                        st.session_state.custom_facts = []
                    st.session_state.custom_facts.append({
                        "subject": subject,
                        "predicate": predicate,
                        "object": obj
                    })
                    st.success("✅ 已添加")
                    st.rerun()
        
        with col1:
            # 构建图谱
            G = nx.DiGraph()
            
            # 添加模式节点
            for pattern_id, pattern in logic_layer.patterns.items():
                if show_rules:
                    G.add_node(pattern_id, 
                              label=pattern.name, 
                              color="#3b82f6" if pattern.source == "bootstrap" else "#10b981",
                              size=20 if pattern.source == "bootstrap" else 15)
            
            # 添加事实节点
            if show_facts:
                # 从学习历史中提取事实
                for record in st.session_state.learning_history:
                    text = record.get("text", "")
                    # 简单解析主谓宾
                    if "是" in text:
                        parts = text.split("是")
                        if len(parts) == 2:
                            subj = parts[0].replace("如果", "").strip()
                            obj = parts[1].split("。")[0].strip()
                            G.add_node(subj, label=subj, color="#f59e0b", size=10)
                            G.add_node(obj, label=obj, color="#ef4444", size=10)
                            G.add_edge(subj, obj, label="is_a")
                
                # 添加自定义事实
                for fact in st.session_state.get("custom_facts", []):
                    G.add_node(fact["subject"], label=fact["subject"], color="#f59e0b", size=10)
                    G.add_node(fact["object"], label=fact["object"], color="#ef4444", size=10)
                    G.add_edge(fact["subject"], fact["object"], label=fact["predicate"])
            
            # 创建 PyVis 网络
            net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="#1e293b")
            net.from_nx(G)
            
            # 配置物理引擎
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
            net.save_graph("/tmp/knowledge_graph.html")
            with open("/tmp/knowledge_graph.html", "r", encoding="utf-8") as f:
                html = f.read()
            st.components.v1.html(html, height=520)
            
            # 图例
            cols = st.columns(4)
            with cols[0]:
                st.markdown("<span style='color: #3b82f6'>●</span> 元规则", unsafe_allow_html=True)
            with cols[1]:
                st.markdown("<span style='color: #10b981'>●</span> 学习规则", unsafe_allow_html=True)
            with cols[2]:
                st.markdown("<span style='color: #f59e0b'>●</span> 实体", unsafe_allow_html=True)
            with cols[3]:
                st.markdown("<span style='color: #ef4444'>●</span> 概念", unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"图谱渲染失败: {e}")
        st.info("请确保已安装 pyvis: pip install pyvis")

# ==================== Tab 4: 系统配置 ====================
with tab4:
    st.header("⚙️ 系统配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 系统统计")
        
        stats = logic_layer.get_statistics()
        
        st.markdown("**逻辑模式统计**")
        st.markdown(f"- 总模式数: {stats['total_patterns']}")
        st.markdown(f"- 总执行次数: {stats['total_executions']}")
        st.markdown(f"- 平均置信度: {stats['avg_confidence']:.2f}")
        
        st.markdown("---")
        
        st.markdown("**类型分布**")
        for logic_type, count in stats["by_type"].items():
            st.markdown(f"- {logic_type}: {count}")
    
    with col2:
        st.subheader("💾 数据管理")
        
        # 导出知识
        if st.button("📤 导出知识"):
            export_data = meta_learner.export_knowledge()
            st.download_button(
                label="下载 JSON",
                data=export_data,
                file_name=f"clawra_knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        # 导入知识
        uploaded_file = st.file_uploader("📥 导入知识", type=["json"])
        if uploaded_file is not None:
            content = uploaded_file.read().decode("utf-8")
            result = meta_learner.import_knowledge(content)
            if result["success"]:
                st.success(f"✅ 成功导入 {result['imported']} 个模式")
            else:
                st.error(f"❌ 导入失败: {result.get('error', '未知错误')}")
        
        st.markdown("---")
        
        # 重置系统
        if st.button("🔄 重置系统", type="secondary"):
            st.session_state.learning_history = []
            st.session_state.patterns = []
            st.session_state.discovered_rules = []
            st.session_state.custom_facts = []
            st.success("✅ 系统已重置")
            st.rerun()

# ==================== 底部 ====================
st.markdown("---")
st.caption("🧠 Clawra Autonomous Evolution Engine v2.0 | Built with Streamlit & PyVis")
