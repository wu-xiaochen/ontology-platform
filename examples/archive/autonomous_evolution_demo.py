"""
Autonomous Evolution Demo - 自主进化能力验证
=============================================

展示真正的自主学习能力：
1. 从文本动态提取规则（零硬编码）
2. 自动领域识别与适应
3. 规则发现与归纳
4. 学习效果验证
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.evolution.unified_logic import UnifiedLogicLayer, LogicType
from src.evolution.rule_discovery import RuleDiscoveryEngine
from src.evolution.meta_learner import MetaLearner

st.set_page_config(page_title="Autonomous Evolution Demo", layout="wide")

st.title("🧠 自主进化 Agent 验证")
st.markdown("### 零硬编码 · 动态学习 · 自我进化")

# 初始化系统
@st.cache_resource
def init_system():
    logic_layer = UnifiedLogicLayer()
    discovery_engine = RuleDiscoveryEngine(logic_layer)
    meta_learner = MetaLearner(logic_layer, discovery_engine)
    return logic_layer, discovery_engine, meta_learner

logic_layer, discovery_engine, meta_learner = init_system()

# 侧边栏：系统状态
with st.sidebar:
    st.header("📊 系统状态")
    stats = logic_layer.get_statistics()
    st.metric("总逻辑模式", stats["total_patterns"])
    st.metric("规则类", stats["by_type"].get("rule", 0))
    st.metric("行为类", stats["by_type"].get("behavior", 0))
    st.metric("策略类", stats["by_type"].get("policy", 0))
    
    st.markdown("---")
    st.header("🔍 已学习领域")
    for domain, count in stats.get("by_domain", {}).items():
        st.markdown(f"- **{domain}**: {count} 个模式")

# 主界面
st.markdown("---")

# 功能1：动态规则学习
st.header("1️⃣ 动态规则学习（零硬编码）")

col1, col2 = st.columns(2)

with col1:
    st.subheader("输入学习文本")
    learn_text = st.text_area(
        "输入包含逻辑关系的文本：",
        height=150,
        placeholder="例如：如果设备是燃气调压箱，那么需要定期维护。维护周期是6个月。"
    )
    
    if st.button("🚀 开始学习", type="primary"):
        if learn_text.strip():
            with st.spinner("正在自主学习..."):
                result = meta_learner.learn(learn_text, input_type="text")
                
                st.session_state.last_learn_result = result
                st.success(f"✅ 学习完成！发现 {len(result['learned_patterns'])} 个逻辑模式")
        else:
            st.warning("请输入学习文本")

with col2:
    st.subheader("学习结果")
    if "last_learn_result" in st.session_state:
        result = st.session_state.last_learn_result
        
        st.markdown(f"**识别领域**: {result['domain']}")
        st.markdown(f"**学习策略**: {result['strategy']}")
        st.markdown(f"**学习耗时**: {result['learning_time']:.2f}s")
        
        st.markdown("**发现的模式**:")
        for pattern_id in result['learned_patterns']:
            if pattern_id in logic_layer.patterns:
                pattern = logic_layer.patterns[pattern_id]
                with st.expander(f"📌 {pattern.name}"):
                    st.markdown(f"**类型**: {pattern.logic_type.value}")
                    st.markdown(f"**描述**: {pattern.description}")
                    st.markdown(f"**条件**:")
                    for cond in pattern.conditions:
                        st.markdown(f"  - {cond}")
                    st.markdown(f"**动作**:")
                    for action in pattern.actions:
                        st.markdown(f"  - {action}")

st.markdown("---")

# 功能2：规则发现
st.header("2️⃣ 从数据中归纳规则")

st.markdown("输入结构化事实数据，系统自动发现规则：")

fact_data = st.text_area(
    "输入事实（JSON格式）：",
    height=120,
    value='''[
  {"subject": "燃气调压箱A", "predicate": "is_a", "object": "燃气设备"},
  {"subject": "燃气调压箱B", "predicate": "is_a", "object": "燃气设备"},
  {"subject": "燃气调压箱C", "predicate": "is_a", "object": "燃气设备"},
  {"subject": "燃气设备", "predicate": "requires", "object": "定期维护"}
]'''
)

if st.button("🔍 发现规则"):
    try:
        facts = json.loads(fact_data)
        with st.spinner("分析数据模式..."):
            discovered = discovery_engine.discover_from_facts(facts)
            
            st.session_state.discovered_rules = discovered
            st.success(f"发现 {len(discovered)} 条潜在规则")
    except Exception as e:
        st.error(f"解析错误: {e}")

if "discovered_rules" in st.session_state:
    st.subheader("发现的规则")
    for rule in st.session_state.discovered_rules:
        with st.expander(f"📏 {rule['name']} (置信度: {rule['confidence']:.0%})"):
            st.markdown(f"**描述**: {rule['description']}")
            st.markdown(f"**类型**: {rule['type']}")
            st.markdown(f"**支持度**: {rule['support']} 个实例")
            st.markdown(f"**条件**:")
            for cond in rule['conditions']:
                st.markdown(f"  - {cond}")
            st.markdown(f"**结论**:")
            for action in rule['actions']:
                st.markdown(f"  - {action}")

st.markdown("---")

# 功能3：领域自适应
st.header("3️⃣ 领域自适应验证")

domain_text = st.text_input("输入任意领域文本，检测系统自动识别：", 
                            placeholder="例如：患者需要定期服用胰岛素控制血糖...")

if domain_text:
    scores = meta_learner.detect_domain(domain_text)
    
    st.subheader("领域识别结果")
    for domain, score in list(scores.items())[:3]:
        st.progress(score, text=f"{domain}: {score:.0%}")

st.markdown("---")

# 功能4：学习统计
st.header("4️⃣ 学习过程统计")

if st.button("📈 查看完整统计"):
    stats = meta_learner.get_learning_statistics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总学习次数", stats["total_episodes"])
    with col2:
        st.metric("成功率", f"{stats['success_rate']:.0%}")
    with col3:
        st.metric("平均学习耗时", f"{stats['avg_learning_time']:.2f}s")
    
    st.subheader("领域分布")
    for domain, count in stats["domain_distribution"].items():
        st.markdown(f"- **{domain}**: {count} 次学习")
    
    st.subheader("策略效果")
    for strategy, effectiveness in stats["strategy_effectiveness"].items():
        if effectiveness["attempts"] > 0:
            success_rate = effectiveness["successes"] / effectiveness["attempts"]
            st.markdown(f"- **{strategy}**: {success_rate:.0%} 成功率 ({effectiveness['attempts']} 次尝试)")

st.markdown("---")
st.caption("🧠 Autonomous Evolution System | Zero Hardcoding | Self-Learning | Domain Adaptive")
