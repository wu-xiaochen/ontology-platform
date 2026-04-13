# ── Page Config ────────────────────────────────────────────────────────────────
import streamlit as st
st.set_page_config(page_title="Capabilities - Clawra", page_icon="🔬", layout="wide")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.markdown("## 🔬 能力演示")
st.markdown("*每个能力模块均提供 Python SDK 调用示例，即学即用*")
st.divider()

# ── Helper: code block ─────────────────────────────────────────────────────────
def show_code(title, code):
    with st.expander(f"📄 {title}", expanded=False):
        st.code(code, language="python")

# ── Init ─────────────────────────────────────────────────────────────────────
if "clawra" not in st.session_state:
    st.session_state.clawra = None
    st.session_state.clawra_ready = False

# ── Learn ─────────────────────────────────────────────────────────────────────
with st.expander("### 1️⃣ learn() — 从文本提取知识", expanded=True):
    col_demo, col_code = st.columns([1, 1])
    
    with col_demo:
        st.markdown("**演示**")
        text_input = st.text_area(
            "输入文本",
            value="燃气调压箱的作用是把高压燃气降低为恒定压力的低压或中压。使用规范要求：进气压力不能大于0.4MPa，否则存在泄漏爆炸风险。调压箱通常配备安全阀和监控系统。",
            height=100, key="learn_text"
        )
        if st.button("🔍 执行学习", key="btn_learn", use_container_width=True):
            if "clawra" not in st.session_state or st.session_state.clawra is None:
                st.warning("请先在侧边栏初始化")
            else:
                with st.spinner("调用 LLM 提取中 (~20s)..."):
                    result = st.session_state.clawra.learn(text_input)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("✅ 成功", "是" if result.get("success") else "否")
                c2.metric("📂 领域", result.get("domain","—"))
                c3.metric("🔢 模式", len(result.get("learned_patterns",[])))
                c4.metric("📝 事实", result.get("facts_added", 0))
                facts = result.get("extracted_facts", [])
                for i, f in enumerate(facts[:6], 1):
                    st.markdown(
                        f"<div style='background:#0d1117;border-left:3px solid #22d3ee;padding:6px 12px;margin:3px 0;border-radius:4px;font-family:monospace;font-size:0.82rem'>"
                        f"{i}. ({f.get('subject','')}) <b>-[{f.get('predicate','')}]-></b> ({f.get('object','')})"
                        f"</div>", unsafe_allow_html=True
                    )
    
    with col_code:
        st.markdown("**SDK 调用**")
        show_code("初始化 + learn()", '''from src.clawra import Clawra

clawra = Clawra(enable_memory=False)

result = clawra.learn(
    "燃气调压箱的作用是把高压燃气降低为恒定压力的低压或中压。"
    "使用规范要求：进气压力不能大于0.4MPa，否则存在泄漏爆炸风险。"
)

print(result)
# {'success': True, 'domain': 'gas_equipment',
#  'learned_patterns': [...], 'facts_added': 7,
#  'extracted_facts': [
#    {'subject': '燃气调压箱', 'predicate': '功能是',
#     'object': '降低燃气压力'}, ...
#  ]}''')
        show_code("learn() 参数详解", '''result = clawra.learn(
    text="...",           # 待学习的文本 (str)
    domain_hint=None,     # 领域提示，如 "medical"/"legal" (str|None)
    confidence=0.9,        # 置信度阈值 (float, 0~1)
)

# 返回值:
# - success: bool, 是否成功
# - domain: str, 检测到的领域
# - learned_patterns: List[LogicPattern]
# - facts_added: int, 新增事实数
# - extracted_facts: List[Dict], 三元组列表
#   - subject/predicate/object: str''')

# ── Reason ─────────────────────────────────────────────────────────────────────
with st.expander("### 2️⃣ reason() — 前向链推理", expanded=False):
    col_demo, col_code = st.columns([1, 1])
    
    with col_demo:
        st.markdown("**添加事实 + 推理**")
        if st.button("➕ 添加预设事实", key="btn_add_facts", use_container_width=True):
            if st.session_state.clawra:
                st.session_state.clawra.add_fact("调压箱A", "is_a", "燃气调压箱", confidence=0.95)
                st.session_state.clawra.add_fact("调压箱A", "has_component", "安全阀", confidence=0.9)
                st.session_state.clawra.add_fact("安全阀", "is_a", "安全装置", confidence=0.95)
                st.session_state.clawra.add_fact("燃气调压箱", "is_a", "压力设备", confidence=0.9)
                st.success("已添加 4 条事实")
        
        if st.button("🧠 执行推理 (深度=3)", key="btn_reason", use_container_width=True):
            if not st.session_state.clawra:
                st.warning("请先初始化")
            else:
                with st.spinner("推理中..."):
                    conclusions = st.session_state.clawra.reason(max_depth=3)
                st.success(f"推导出 {len(conclusions)} 条结论")
                for i, c in enumerate(conclusions[:5], 1):
                    conc = c.conclusion if hasattr(c, 'conclusion') else c
                    st.markdown(
                        f"<div style='background:#0d1117;border-left:3px solid #a78bfa;padding:6px 12px;margin:3px 0;border-radius:4px;font-size:0.82rem'>"
                        f"🧠 {i}. {str(conc)[:80]}"
                        f"</div>", unsafe_allow_html=True
                    )
    
    with col_code:
        st.markdown("**SDK 调用**")
        show_code("添加事实 + 推理", '''# 添加事实
clawra.add_fact(
    subject="调压箱A",
    predicate="is_a",
    object="燃气调压箱",
    confidence=0.95      # 置信度 0~1
)

# 执行前向链推理
conclusions = clawra.reason(max_depth=3)

for c in conclusions:
    print(c.conclusion)
    # Fact(subject='调压箱A', predicate='is_a',
    #      object='设备', confidence=0.85, ...)''')
        show_code("add_fact / reason 参数", '''# add_fact()
clawra.add_fact(
    subject: str,        # 主体
    predicate: str,       # 谓词
    object: str,          # 客体
    confidence: float,    # 置信度 (0~1)
    source: str           # 来源 (可选)
)

# reason()
clawra.reason(
    max_depth: int = 3,  # 推理深度
    rules: List[Rule]     # 可选，自定义规则
) -> List[InferenceStep]''')

# ── Domain Adaptive ─────────────────────────────────────────────────────────────
with st.expander("### 3️⃣ 领域自适应", expanded=False):
    col_demo, col_code = st.columns([1, 1])
    
    with col_demo:
        domains = {
            "🏥 医疗": "患者诊断需要根据症状和检查结果进行。药物治疗方案需要考虑患者的过敏史和副作用。",
            "⚖️ 法律": "合同违约需要承担赔偿责任。依据合同条款确定违约责任范围。",
            "🔥 燃气": "燃气调压箱的维护周期为每半年一次。需要检查密封性能和压力参数。",
        }
        for name, text in domains.items():
            if st.button(f"学习: {name}", key=f"domain_{name[:2]}", use_container_width=True):
                if not st.session_state.clawra:
                    st.warning("请先初始化")
                else:
                    hint = name.split()[1].lower()
                    with st.spinner(f"学习{name}中..."):
                        result = st.session_state.clawra.learn(text, domain_hint=hint)
                    st.metric("检测领域", result.get("domain", "—"))
                    st.metric("模式数", len(result.get("learned_patterns", [])))
    
    with col_code:
        st.markdown("**SDK 调用**")
        show_code("learn() + domain_hint", '''# 指定领域提示
result = clawra.learn(
    text="患者诊断需要根据症状和检查结果...",
    domain_hint="medical"    # 强制指定领域
)
print(result["domain"])  # "medical"

# 自动领域检测 (不指定 hint)
result = clawra.learn(
    text="燃气调压箱的维护周期为每半年一次..."
)
print(result["domain"])  # "gas_equipment"''')

# ── GraphRAG ───────────────────────────────────────────────────────────────────
with st.expander("### 4️⃣ GraphRAG 检索", expanded=False):
    col_demo, col_code = st.columns([1, 1])
    
    with col_demo:
        query = st.text_input("🔍 检索 query", value="燃气调压箱的安全规范", key="rag_query")
        top_k = st.selectbox("Top-K", [3, 5, 10], index=1, key="rag_k")
        
        if st.button("🚀 检索", key="btn_rag", use_container_width=True):
            if not st.session_state.clawra:
                st.warning("请先初始化")
            else:
                with st.spinner("检索中..."):
                    st.session_state.clawra.retriever.build_index()
                    resp = st.session_state.clawra.retrieve_knowledge(
                        query, top_k=top_k, modes=["entity", "semantic"]
                    )
                st.success(f"找到 {len(resp.results)} 条结果")
                for i, r in enumerate(resp.results[:5], 1):
                    col = "#dcfce7" if r.score > 0.5 else "#fef9c3"
                    st.markdown(
                        f"<div style='background:{col};padding:6px 12px;border-radius:6px;margin:3px 0;font-size:0.82rem'>"
                        f"<b>#{i}</b> ({r.triple.subject}) <b>-[{r.triple.predicate}]-></b> ({r.triple.object})"
                        f"<br><small>得分: {r.score:.3f} | {r.source}</small>"
                        f"</div>", unsafe_allow_html=True
                    )
    
    with col_code:
        st.markdown("**SDK 调用**")
        show_code("GraphRAG 检索", '''# 构建索引
clawra.retriever.build_index()

# 检索
resp = clawra.retrieve_knowledge(
    query="燃气调压箱的安全规范",
    top_k=5,
    modes=["entity", "semantic"]  # 混合模式
)

for r in resp.results:
    print(f"({r.triple.subject}) -[{r.triple.predicate}]-> ({r.triple.object})")
    print(f"  score={r.score:.3f}, source={r.source}")''')

# ── Skill Library ──────────────────────────────────────────────────────────────
with st.expander("### 5️⃣ 技能库", expanded=False):
    col_demo, col_code = st.columns([1, 1])
    
    with col_demo:
        st.markdown("**注册并执行技能**")
        if st.button("⚙️ 执行压力检查技能", key="btn_skill_exec", use_container_width=True):
            if not st.session_state.clawra:
                st.warning("请先初始化")
            else:
                # Find a pressure-related skill
                found = False
                for k, fn in st.session_state.clawra.skill_registry.callables.items():
                    if "pressure" in k.lower():
                        result = fn(0.3, 0.01)
                        st.json(result)
                        found = True
                        break
                if not found:
                    st.info("暂无压力检查技能，请先注册")
    
    with col_code:
        st.markdown("**SDK 调用**")
        show_code("注册 + 执行技能", '''from src.evolution.skill_library import (
    Skill, SkillType
)

skill = Skill(
    id="skill:pressure_check",
    name="压力安全检查",
    description="检查压力是否在安全范围",
    skill_type=SkillType.CODE,
    content="""
def check_pressure(inlet, outlet):
    if inlet > 0.4:
        return {"safe": False, "reason": "进气超限"}
    return {"safe": True, "reason": "正常"}
"""
)
clawra.skill_registry.register_skill(skill)

# 执行
if "skill:pressure_check" in clawra.skill_registry.callables:
    fn = clawra.skill_registry.callables["skill:pressure_check"]
    result = fn(0.3, 0.01)
    print(result)  # {"safe": True, "reason": "正常"}''')

# ── Rule Engine ────────────────────────────────────────────────────────────────
with st.expander("### 6️⃣ 规则引擎", expanded=False):
    col_demo, col_code = st.columns([1, 1])
    
    with col_demo:
        from src.core.ontology.rule_engine import RuleEngine, OntologyRule, SafeMathSandbox
        _re = RuleEngine()
        
        t_out = st.number_input("出口压力 (MPa)", value=0.05, format="%.3f", key="re_out")
        t_in = st.number_input("进气压力 (MPa)", value=0.3, format="%.3f", key="re_in")
        t_maint = st.number_input("维护周期 (月)", value=6, key="re_maint")
        
        if st.button("🛡️ 评估约束", key="btn_rule_eval", use_container_width=True):
            params = {
                "outlet_pressure": t_out,
                "inlet_pressure": t_in,
                "maintenance_interval_months": t_maint
            }
            results = _re.evaluate_action_preconditions("action:configure", "GasRegulator", params)
            passed = sum(1 for r in results if r.get("status") == "PASS")
            total = len(results)
            if passed == total:
                st.success(f"✅ 全部通过 ({passed}/{total})")
            else:
                st.error(f"❌ {total-passed} 条规则失败")
            for r in results:
                icon = "✅" if r.get("status") == "PASS" else "🚫"
                col = "#dcfce7" if r.get("status") == "PASS" else "#fee2e2"
                st.markdown(
                    f"<div style='background:{col};padding:5px 10px;border-radius:5px;margin:2px 0;font-size:0.82rem'>"
                    f"{icon} {r.get('rule_name','')}: {r.get('message','')}"
                    f"</div>", unsafe_allow_html=True
                )
        
        # SafeMath
        if st.button("🛡️ SafeMath 防DoS测试", key="btn_safemath", use_container_width=True):
            try:
                SafeMathSandbox.evaluate("99999 ** 9999", {})
                st.error("应该被拦截!")
            except ValueError as e:
                st.success(f"已拦截: {e}")
    
    with col_code:
        st.markdown("**SDK 调用**")
        show_code("注册规则 + 评估", '''from src.core.ontology.rule_engine import (
    RuleEngine, OntologyRule, SafeMathSandbox
)

engine = RuleEngine()

# 注册业务约束
rule = OntologyRule(
    id="rule:gas_pressure_safety",
    target_object_class="GasRegulator",
    expression="outlet_pressure >= 0.002 and outlet_pressure <= 0.4",
    description="出口压力安全范围 2kPa~400kPa"
)
engine.register_rule(rule)

# 评估
results = engine.evaluate_action_preconditions(
    "action:configure",
    "GasRegulator",
    {"outlet_pressure": 0.05, "inlet_pressure": 0.3}
)

for r in results:
    print(r["status"], r["rule_name"])''')
        show_code("SafeMathSandbox", '''# 防止恶意表达式耗尽 CPU
try:
    SafeMathSandbox.evaluate("99999 ** 9999", {})
except ValueError as e:
    print(f"已拦截: {e}")
# 输出: Exponent too large, preventing CPU DoS''')
