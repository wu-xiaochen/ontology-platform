"""
Clawra Cognitive Framework (神经符号智能引擎) 完整演示程序

本示例旨在为您呈现 Clawra 的真正价值：
1. 元学习 (Meta Learning): 自动从非结构化文本中汲取领域知识，转为知识图谱结构
2. 数学沙盒保障 (Neuro-Symbolic Gatekeeper): 防止 LLM 关于数值产生的幻觉，阻断 OOM/CPU 高危漏洞
3. 规则前向校验 (Rule Engine Enforcement): 依据硬性规则进行物理拦截，无需依赖概率模型
"""
import logging
from src.clawra import Clawra
from src.core.ontology.rule_engine import RuleEngine, OntologyRule, SafeMathSandbox

# 关闭过于嘈杂的日志输出方便演示
logging.getLogger("src").setLevel(logging.CRITICAL)

def main():
    print("=" * 70)
    print("🤖 欢迎来到 Clawra 自主进化智能体框架 - 核心能力演示")
    print("=" * 70)
    
    # ---------------------------------------------------------
    # 能力一：自主提取与领域知识固化
    # ---------------------------------------------------------
    print("\n[核心优势 1] 非结构化知识自动转化为数学事实 (Meta Learning)")
    print("正在拉起 Clawra 核心引擎...")
    agent = Clawra(enable_memory=False) # Demo 纯内存运行
    
    text = (
        "燃气调压箱的作用是把高压燃气降低为恒定压力的低压或者中压。"
        "使用规范要求：进气压力不能大于0.4MPa，否则存在泄漏爆炸风险。"
        "通常一个园区只需部署一台。"
    )
    print(f"▶ 注入领域业务规范文本: '{text}'")
    print("▶ 引擎底层正在分析文本规律...")
    
    result = agent.learn(text)
    
    print(f"  ✓ 框架自动判别其归属业务域: [{result.get('domain', 'generic')}]")
    print("  ✓ Clawra 内置大模型感知器自动归纳出了以下图谱结构:")
    facts = result.get('extracted_facts', [])
    if facts:
        for idx, f in enumerate(facts[:3]):
            print(f"     => ({f.get('subject')})  -[{f.get('predicate')}]->  ({f.get('object')})")
    else:
        print("     => (未提取出结构化事实，如果你正处于纯离线模式，则回退为正则提取)")
        
    # ---------------------------------------------------------
    # 能力二：绝对的算力资源保护沙盒
    # ---------------------------------------------------------
    print("\n[核心优势 2] 坚固的物理边界 (SafeMathSandbox) 预防 DoS 瘫痪")
    print("▶ 测试场景：如果 LLM 由于幻觉生成了一个破坏性的指数公式 '99999 ** 9999'")
    print("▶ 如果不由沙盒接管，Python的进程会瞬间因 CPU 和 RAM 被打满而锁死。")
    try:
        SafeMathSandbox.evaluate("99999 ** 9999", {}) 
        print("  ❌ 沙盒未生效，不应出现在此。")
    except ValueError as e:
        print(f"  🛡️ 沙盒强力拦截成功: {e}")
        print("  ✓ 这意味着不管外部恶意输入或大模型如何崩溃，您的服务底层永远不会死锁。")

    # ---------------------------------------------------------
    # 能力三：完全可靠的神经符号逻辑前置守卫
    # ---------------------------------------------------------
    print("\n[核心优势 3] 结合符号规则引擎 (Rule Engine) 实现完美的事实验证")
    engine = RuleEngine()
    
    # 制定硬性数学纪律（哪怕大模型觉得没问题，系统也不允许的情况）
    rule = OntologyRule(
        id="rule:demo_gas_pressure",
        target_object_class="GasRegulator",
        expression="outlet_pressure >= 0.002 and outlet_pressure <= 0.4",
        description="出口压力必须在安全的 2kPa 到 400kPa 的工程合理范围内！"
    )
    engine.register_rule(rule)
    print(f"▶ 已将企业规范注册为不可动摇的底线: `{rule.expression}`")
    
    mock_llm_suggestion = {"outlet_pressure": 0.8} # 大模型给出 0.8 MPa
    print(f"▶ 场景：大模型经过思考，认为压力推荐为 {mock_llm_suggestion['outlet_pressure']} MPa 比较有效。")
    
    eval_result = engine.evaluate_action_preconditions(
         action_id="action:configure", 
         object_class="GasRegulator", 
         context=mock_llm_suggestion
    )
    
    for res in eval_result:
        stat = res.get('status')
        print(f"  => 底层校验结果: [{stat}]！校验依据: {res.get('rule_name')}")
        if stat == "FAIL":
            print("  🚫 框架最终裁决: LLM 存在致命工程幻觉！该动作被物理阻断执行。")
            
    print("\n" + "="*70)
    print("🎉 演示结束")
    print("经过本轮架构的全面审查和加固改造后，Clawra已具备：")
    print(" - 真正的大陆线防护能力（资源锁死、线程阻塞不再发生）")
    print(" - 高效准确地进行企业级决策执行流约束的能力")
    print("现在，它绝非只是一层套着 OpenAI 接口的壳子，而是严肃可控的智能中枢。")
    print("=" * 70)

if __name__ == "__main__":
    main()
