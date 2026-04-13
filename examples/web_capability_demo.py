import streamlit as st
import time
import pandas as pd
from src.clawra import Clawra
from src.core.ontology.rule_engine import RuleEngine, OntologyRule, SafeMathSandbox

# ==========================================
# 页面配置与顶级全局状态
# ==========================================
st.set_page_config(
    page_title="Clawra Core - Web Demo",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 注入高端自定义 CSS (Glassmorphism + 暗色主题美化)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* 玻璃拟物化卡片 */
    .glass-card {
        background: rgba(30, 35, 45, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 24px;
    }
    
    .glowing-text {
        color: #58a6ff;
        text-shadow: 0 0 10px rgba(88, 166, 255, 0.5);
        font-weight: 800;
    }
    
    .alert-box {
        border-left: 4px solid #f85149;
        background-color: rgba(248, 81, 73, 0.1);
        padding: 16px;
        border-radius: 4px 8px 8px 4px;
        margin: 10px 0;
    }
    
    .success-box {
        border-left: 4px solid #3fb950;
        background-color: rgba(63, 185, 80, 0.1);
        padding: 16px;
        border-radius: 4px 8px 8px 4px;
        margin: 10px 0;
    }

    h1, h2, h3 {
        color: #ffffff;
    }
    
    /* 隐藏 Streamlit 默认尾部 */
    footer {visibility: hidden;}
    header {background-color: rgba(0,0,0,0) !important;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 延迟加载核心引擎 (单例)
# ==========================================
@st.cache_resource
def get_clawra():
    return Clawra(enable_memory=False)

def get_rule_engine():
    return RuleEngine()

agent = get_clawra()
rule_engine = get_rule_engine()

# ==========================================
# UI 结构
# ==========================================
st.markdown("<h1 style='text-align: center;'><span class='glowing-text'>Clawra</span> 神经符号智能引擎 核心靶标演示</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e;'>探索我们刚刚迭代加强过的三大安全控制塔</p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🧠 Meta Learning (领域自主学习)", "🛡️ 算力终极沙盒 (数学漏洞拦截)", "⚖️ Neuro-Symbolic 神经门控 (AI 幻觉阻断)"])

# ----------------------------------------------------
# 模块一：自主能力抽取
# ----------------------------------------------------
with tab1:
    st.markdown("""
    <div class="glass-card">
        <h3>1. 大数据下的规则“啃食”能力</h3>
        <p>不再需要大量人工配置，系统会自动切分知识文本、剥离无关废话，并将符合企业物理规范的描述升维成<b>逻辑图谱</b>。</p>
    </div>
    """, unsafe_allow_html=True)
    
    default_text = "燃气调压箱的作用是把高压燃气降低为恒定压力的低压或者中压。使用规范要求：进气压力不能大于0.4MPa，否则存在泄漏爆炸风险。如果设备温度超过60度或低于零下20度，将自动停止运作。一般需要配合安全阀共同切断闭锁。"
    user_text = st.text_area("请灌入一份企业的原始规章手册 (支持千字长文，自动分块):", value=default_text, height=150)
    
    if st.button("🚀 启动语义解构与图谱提炼", type="primary"):
        with st.spinner("调用元学习器底层感知器分析中... (如为本地无连通环境，默认自适应回退到正则表达式)"):
            import time
            start_time = time.time()
            result = agent.learn(user_text)
            latency = time.time() - start_time
            
        st.markdown(f"#### ⚡ 提取耗时: `{latency:.2f}s` | 匹配推断基座: `[ {result.get('domain', 'generic')} ]`")
        
        facts = result.get('extracted_facts', [])
        if facts:
            st.markdown(f'<div class="success-box">✅ 从茫茫文本中成功捕捉到了 <b>{len(facts)}</b> 个工业常识元组。</div>', unsafe_allow_html=True)
            df = pd.DataFrame(facts)
            st.dataframe(df, use_container_width=True)
        else:
            st.markdown('<div class="alert-box">⚠️ 提取环境异常或未匹配到图谱三元组。请确认配置环境大模型连通性。</div>', unsafe_allow_html=True)

# ----------------------------------------------------
# 模块二：超强安全沙盒
# ----------------------------------------------------
with tab2:
    st.markdown("""
    <div class="glass-card">
        <h3>2. Defend DoS: 物理与算力的“绝缘盾牌”</h3>
        <p>大模型在幻觉下极有可能会给出导致服务器瞬间死锁的表达式，例如 <code>99999 ** 99999</code>。Clawra 底层直接屏蔽了超过安全边界的高次幂或天文乘法，保护 CPU 免遭毒手。</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.code("恶意输入变种：\n1. 99999 ** 9999\n2. 'crash' * 9999999\n3. ((2*3)**4)**5", language="python")
    
    with col2:
        danger_input = st.text_input("您可以尝试在此攻破沙盒 (输入恶意计算表达式)：", value="99999 ** 9999")
        if st.button("💣 模拟 AI 注入执行"):
            with st.spinner("编译 AST 抽象语法树检测..."):
                time.sleep(0.5) # UI效果
                try:
                    SafeMathSandbox.evaluate(danger_input, {})
                    st.error("沙盒失效，未被阻拦！")
                except ValueError as e:
                    st.markdown(f"""
                    <div class="alert-box">
                        <h4>🛑 核心守护者已介入断路！</h4>
                        <strong>底层拒绝信息：</strong> {str(e)}<br/>
                        <em>成功保护了本次事件循环未被大数计算和 OOM 堵死。</em>
                    </div>
                    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 模块三：对抗大模型幻觉的绝对法庭
# ----------------------------------------------------
with tab3:
    st.markdown("""
    <div class="glass-card">
        <h3>3. 物理门禁 (Neuro-Symbolic Check)</h3>
        <p>将大模型的创造力框定在<b>物理事实</b>的绝对管辖内！即使 GPT 给你天花乱坠的理由推荐了一个错误配置，底层的符号逻辑（RuleEngine）也会一票否决阻止执行。</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### 配置绝对安全红线 (不可被大模型更改)")
    rule_exp = st.text_input("写入硬性安全纪律，例如：", value="outlet_pressure >= 0.002 and outlet_pressure <= 0.4")
    
    if st.button("🔒 将法则蚀刻进入底层虚拟机"):
        rule = OntologyRule(
            id="rule:ui_demo",
            target_object_class="GasRegulator",
            expression=rule_exp,
            description="UI 现场设置的安全合规值域"
        )
        rule_engine.register_rule(rule, check_conflict=False)
        st.toast("法则注册成功", icon="✅")
        st.session_state["rule_registered"] = True
        
    st.markdown("---")
    st.markdown("#### 模拟大模型幻觉输出")
    llm_mock_val = st.number_input("模拟 AI 模型基于其幻觉推理后得出的出口压力 (MPa):", value=0.8, step=0.1)
    
    if st.button("🧠 允许大模型实施该配置流 ->"):
        if not st.session_state.get("rule_registered"):
            st.warning("请先点击上方按钮注册安全法则。")
        else:
            with st.spinner("AI 申请提交配置，神经系统请求底座放行..."):
                time.sleep(1)
                
                eval_result = rule_engine.evaluate_action_preconditions(
                    action_id="action:configure", 
                    object_class="GasRegulator", 
                    context={"outlet_pressure": llm_mock_val}
                )
                
                # 评估有没有 FAIL
                rejected = any(r.get('status') == 'FAIL' for r in eval_result)
                
                if rejected:
                    msg = [r.get('rule_name') for r in eval_result if r.get('status') == 'FAIL'][0]
                    st.markdown(f"""
                    <div class="alert-box", style="border-left-color: #f00;">
                        <h2 style="color:#f85149">📛 神经网闸拦截！(BLOCKED)</h2>
                        <p>判定模型提案 <b>{llm_mock_val}</b> 严重违反了安全常数规则: <br/><code>{rule_exp}</code></p>
                        <p>该 Action 会被直接吞掉，阻止下发工业节点！</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="success-box">
                        <h2>✅ 合规放行 (APPROVED)</h2>
                        <p>该配置提案 <b>{llm_mock_val}</b> 完美位于沙盒阈值 <code>{rule_exp}</code> 内，安全准入！</p>
                    </div>
                    """, unsafe_allow_html=True)
