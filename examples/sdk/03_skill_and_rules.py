#!/usr/bin/env python3
"""
Clawra SDK Example 03 — 技能库 + 规则引擎
展示如何注册自定义技能和业务规则

Run: PYTHONPATH=. python examples/sdk/03_skill_and_rules.py
"""

from src.clawra import Clawra
from src.evolution.skill_library import Skill, SkillType
from src.core.ontology.rule_engine import RuleEngine, OntologyRule, SafeMathSandbox

agent = Clawra(enable_memory=False)

# ── 技能库 ───────────────────────────────────────────────────────────────────
print("=" * 60)
print("⚙️  技能库 — 注册并执行自定义技能")
print("=" * 60)

# 注册一个压力安全检查技能
skill = Skill(
    id="skill:pressure_check",
    name="压力安全检查",
    description="检查燃气设备压力是否在安全范围内，返回检查结果。",
    skill_type=SkillType.CODE,
    content='''
def check_pressure(inlet, outlet):
    """
    检查压力是否在安全范围内
    安全范围: inlet <= 0.4 MPa, outlet between 0.002-0.4 MPa
    """
    if inlet > 0.4:
        return {"safe": False, "reason": f"进气压力 {inlet}MPa 超出安全上限 0.4MPa"}
    if outlet < 0.002 or outlet > 0.4:
        return {"safe": False, "reason": f"出气压力 {outlet}MPa 超出安全范围 0.002~0.4MPa"}
    return {"safe": True, "reason": "压力参数正常"}
'''
)

success = agent.skill_registry.register_skill(skill)
print(f"技能注册: {'✅ 成功' if success else '❌ 失败'}")
print(f"当前技能数: {len(agent.skill_registry.skills)}")

# 执行技能
print("\n执行压力检查:")
test_cases = [
    (0.3, 0.05),   # 正常
    (0.5, 0.05),   # 进气超限
    (0.3, 0.5),    # 出气超限
]

for inlet, outlet in test_cases:
    if "skill:pressure_check" in agent.skill_registry.callables:
        fn = agent.skill_registry.callables["skill:pressure_check"]
        result = fn(inlet, outlet)
        status = "✅" if result["safe"] else "🚫"
        print(f"  {status} inlet={inlet}MPa, outlet={outlet}MPa → {result['reason']}")

# ── 规则引擎 ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("🛡️  规则引擎 — 业务约束评估 + SafeMath 防 DoS")
print("=" * 60)

engine = RuleEngine()

# 注册安全规则
rules = [
    OntologyRule(
        id="rule:outlet_pressure_range",
        target_object_class="GasRegulator",
        expression="outlet_pressure >= 0.002 and outlet_pressure <= 0.4",
        description="出口压力必须在 2kPa~400kPa 安全范围内"
    ),
    OntologyRule(
        id="rule:inlet_pressure_limit",
        target_object_class="GasRegulator",
        expression="inlet_pressure <= 0.4",
        description="进气压力不能大于0.4MPa"
    ),
    OntologyRule(
        id="rule:maintenance_cycle",
        target_object_class="GasRegulator",
        expression="maintenance_interval_months <= 12",
        description="维护周期不能超过12个月"
    ),
]

for rule in rules:
    engine.register_rule(rule)
    print(f"  ✅ 注册规则: {rule.description}")

print(f"\n当前规则总数: {len(engine.rules)}")

# 评估测试用例
print("\n测试用例评估:")
test_params = [
    {"name": "✅ 正常参数", "params": {"outlet_pressure": 0.05, "inlet_pressure": 0.3, "maintenance_interval_months": 6}},
    {"name": "🚫 出气超限", "params": {"outlet_pressure": 0.8, "inlet_pressure": 0.3, "maintenance_interval_months": 6}},
    {"name": "🚫 进气超限", "params": {"outlet_pressure": 0.05, "inlet_pressure": 0.5, "maintenance_interval_months": 6}},
    {"name": "🚫 维护过期", "params": {"outlet_pressure": 0.05, "inlet_pressure": 0.3, "maintenance_interval_months": 18}},
]

for tc in test_params:
    results = engine.evaluate_action_preconditions("action:configure", "GasRegulator", tc["params"])
    passed = sum(1 for r in results if r.get("status") == "PASS")
    total = len(results)
    status = f"✅ 通过({passed}/{total})" if passed == total else f"🚫 拒绝({total-passed}条违规)"
    print(f"\n  {tc['name']}: {status}")
    for r in results:
        icon = "✅" if r.get("status") == "PASS" else "🚫"
        print(f"    {icon} {r.get('rule_name', 'rule')}: {r.get('message', '')}")

# SafeMath 防 DoS
print("\n🛡️ SafeMath 防 DoS 测试:")
dangerous_exprs = [
    "99999 ** 9999",        # 指数爆炸
    "sum(range(10**10))",   # 内存耗尽
    "eval('__import__(\"os\").system(\"ls\")')",  # 代码注入
]

for expr in dangerous_exprs:
    try:
        SafeMathSandbox.evaluate(expr, {})
        print(f"  ❌ 应该被拦截: {expr[:40]}")
    except ValueError as e:
        print(f"  ✅ 拦截成功: {expr[:40]} → {e}")
