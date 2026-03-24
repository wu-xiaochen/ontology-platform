#!/usr/bin/env python3
"""
ontology-platform Agent Growth Demo
====================================
展示Agent三大成长能力：
1. 学习特性：运行时学习新规则
2. 推理能力：因果推理 + 逻辑推理
3. 元认知：置信度自知 + 知识边界识别

运行方式:
    cd /path/to/ontology-platform
    python examples/agent_growth_demo.py

输出: 完整的Agent成长演示，包含推理链追踪和置信度标注
"""

import sys
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Literal
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from confidence import ConfidenceCalculator
from reasoner import RuleType, Rule
from src.ontology.auto_learn import AutoLearnEngine


# ─────────────────────────────────────────────────────────────
# 1. Meta-Cognition Layer: Agent Self-Awareness
# ─────────────────────────────────────────────────────────────

class KnowledgeBoundary:
    """
    知识边界识别器
    让Agent能说"我不知道"
    """
    
    CONFIDENCE_HIGH = 0.75
    CONFIDENCE_LOW = 0.40
    
    # 领域关键词映射（支持同义词、近义词、上下位词）
    DOMAIN_KEYWORDS = {
        "供应链管理": ["供应链", "采购", "供应商", "库存", "物流", "交付", "成本"],
        "采购风险": ["风险", "供应商风险", "采购风险", "质量", "延误", "违约"],
        "跨境电商供应商": ["跨境", "电商", "清关", "进出口", "外贸"],
    }
    
    def __init__(self):
        self.known_domains: set[str] = set()
        self.learned_facts: dict[str, float] = {}
    
    def register_knowledge(self, domain: str, confidence: float, keywords: list[str] = None):
        """注册已知知识（可指定关联关键词）"""
        self.known_domains.add(domain)
        self.learned_facts[domain] = max(
            self.learned_facts.get(domain, 0), confidence
        )
        # 同时注册关键词
        if keywords:
            if domain not in self.DOMAIN_KEYWORDS:
                self.DOMAIN_KEYWORDS[domain] = []
            self.DOMAIN_KEYWORDS[domain].extend(keywords)
    
    def assess_confidence(self, query: str) -> tuple[float, str]:
        """
        评估查询的置信度
        
        Returns:
            (confidence, response)
        """
        query_lower = query.lower()
        best_confidence = 0.0
        
        # 检查所有领域关键词
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if domain in self.known_domains:
                if any(kw in query_lower for kw in keywords):
                    conf = self.learned_facts.get(domain, 0.3)
                    if conf > best_confidence:
                        best_confidence = conf
        
        if best_confidence > 0:
            return best_confidence, self._make_response(query, best_confidence)
        
        # 未知领域
        return 0.2, (
            "❓ 我对这个领域不确定（置信度: 20%）。"
            "我可以尝试从本体库中搜索，或者请提供更多背景信息。"
        )
    
    def _make_response(self, query: str, confidence: float) -> str:
        if confidence >= self.CONFIDENCE_HIGH:
            return f"✅ 我对这个领域有较高置信度（{confidence:.0%}）：{query}"
        elif confidence >= self.CONFIDENCE_LOW:
            return f"⚠️ 我对这个领域有一定了解但不确定（{confidence:.0%}）：{query}"
        else:
            return f"❓ 我对这个领域了解有限（{confidence:.0%}）：{query}"


# ─────────────────────────────────────────────────────────────
# 2. Memory Layer: Ontology-backed Knowledge Store
# ─────────────────────────────────────────────────────────────

class OntologyMemory:
    """
    本体记忆层
    基于JSONL的轻量级本体存储
    """
    
    def __init__(self, storage_path: str = "memory/ontology/graph.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._entities: dict[str, dict] = {}
        self._load()
    
    def _load(self):
        """从文件加载本体"""
        if self.storage_path.exists():
            with open(self.storage_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    if record.get("op") == "create":
                        entity = record["entity"]
                        self._entities[entity["id"]] = entity
    
    def add_entity(self, entity_type: str, name: str, properties: dict) -> str:
        """添加实体到本体"""
        import uuid
        entity_id = f"{entity_type.lower()[:4]}_{uuid.uuid4().hex[:8]}"
        entity = {
            "id": entity_id,
            "type": entity_type,
            "properties": {"name": name, **properties},
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }
        self._entities[entity_id] = entity
        
        # 追加到文件
        with open(self.storage_path, "a") as f:
            f.write(json.dumps({"op": "create", "entity": entity}, ensure_ascii=False) + "\n")
        
        return entity_id
    
    def query_by_type(self, entity_type: str) -> list[dict]:
        """按类型查询实体"""
        return [
            e for e in self._entities.values()
            if e.get("type") == entity_type
        ]
    
    def get_stats(self) -> dict:
        """获取记忆统计"""
        types = {}
        for e in self._entities.values():
            t = e.get("type", "Unknown")
            types[t] = types.get(t, 0) + 1
        return {"total": len(self._entities), "by_type": types}


# ─────────────────────────────────────────────────────────────
# 3. Reasoning Layer: Causal + Logical Inference
# ─────────────────────────────────────────────────────────────

@dataclass
class ReasoningResult:
    """推理结果"""
    conclusion: str
    reasoning_type: Literal["causal", "logical"]
    confidence: float
    chain: list[dict]
    facts_used: list[str]
    
    def display(self):
        """打印推理链"""
        print(f"\n🔍 推理类型: {'因果推理' if self.reasoning_type == 'causal' else '逻辑推理'}")
        print(f"📊 置信度: {self.confidence:.0%}")
        print(f"📋 推理链 ({len(self.chain)} 步):")
        for i, step in enumerate(self.chain, 1):
            print(f"   [{i}] {step['description']}")
            if "confidence" in step:
                print(f"       └─ 置信度: {step['confidence']:.0%}")
        print(f"\n💡 结论: {self.conclusion}")
        return self


class CausalReasoner:
    """
    因果推理引擎
    支持链追溯和干预分析（简化版）
    """
    
    def __init__(self, memory: OntologyMemory):
        self.memory = memory
        self.causal_graph: dict[str, list[tuple[str, float]]] = {}
        self.rules: list[Rule] = []
    
    def add_causal_relation(self, cause: str, effect: str, strength: float = 0.8):
        """添加因果关系"""
        if cause not in self.causal_graph:
            self.causal_graph[cause] = []
        self.causal_graph[cause].append((effect, strength))
    
    def learn_rule(self, rule: Rule):
        """学习规则"""
        self.rules.append(rule)
    
    def reason(self, query: str, reasoning_type: str = "causal") -> ReasoningResult:
        """执行推理"""
        if reasoning_type == "causal":
            return self._causal_reason(query)
        else:
            return self._logical_reason(query)
    
    def _causal_reason(self, query: str) -> ReasoningResult:
        """因果推理"""
        chain = []
        facts_used = []
        query_lower = query.lower()
        
        # 搜索因果链
        for cause, effects in self.causal_graph.items():
            if cause.lower() in query_lower:
                for effect, strength in effects:
                    chain.append({
                        "description": f"原因 '{cause}' → 结果 '{effect}'",
                        "confidence": strength,
                        "type": "causal_edge"
                    })
                    facts_used.append(cause)
        
        # 如果没有找到因果链，进行假阳性分析
        if not chain:
            # 尝试从OntologyMemory中推断
            entities = self.memory.query_by_type("Concept")
            for e in entities:
                name = e["properties"].get("name", "")
                if name and name.lower() in query_lower:
                    chain.append({
                        "description": f"从本体中找到概念: '{name}'",
                        "confidence": 0.6,
                        "type": "ontology_lookup"
                    })
                    facts_used.append(name)
        
        if not chain:
            # 假阳性分析失败
            chain.append({
                "description": "因果链分析：未找到明确的因果关系",
                "confidence": 0.2,
                "type": "no_causal_chain"
            })
            confidence = 0.2
            conclusion = "无法确定因果关系，需要更多信息"
        else:
            # 传播置信度
            confidences = [s["confidence"] for s in chain]
            confidence = min(confidences) if confidences else 0.3
            conclusion = f"基于 {len(chain)} 条因果链的分析，结论置信度 {confidence:.0%}"
        
        return ReasoningResult(
            conclusion=conclusion,
            reasoning_type="causal",
            confidence=confidence,
            chain=chain,
            facts_used=facts_used
        )
    
    def _logical_reason(self, query: str) -> ReasoningResult:
        """逻辑推理（使用规则引擎）"""
        chain = []
        facts_used = []
        
        for rule in self.rules:
            if any(kw in query.lower() for kw in rule.condition.lower().split()):
                chain.append({
                    "description": f"规则匹配: IF {rule.condition} THEN {rule.conclusion}",
                    "confidence": rule.confidence,
                    "type": "logical_rule",
                    "rule_id": rule.name
                })
                facts_used.append(rule.condition)
        
        if chain:
            confidences = [s["confidence"] for s in chain]
            confidence = sum(confidences) / len(confidences)
            conclusion = f"应用 {len(chain)} 条逻辑规则，推理置信度 {confidence:.0%}"
        else:
            chain.append({
                "description": "逻辑推理：未找到匹配规则",
                "confidence": 0.2,
                "type": "no_rule_matched"
            })
            confidence = 0.2
            conclusion = "未找到匹配的逻辑规则"
        
        return ReasoningResult(
            conclusion=conclusion,
            reasoning_type="logical",
            confidence=confidence,
            chain=chain,
            facts_used=facts_used
        )


# ─────────────────────────────────────────────────────────────
# 4. Agent: Integrating All Layers
# ─────────────────────────────────────────────────────────────

class GrowingAgent:
    """
    可成长的Agent
    集成记忆、推理、元认知能力
    """
    
    def __init__(self, name: str = "Agent"):
        self.name = name
        self.memory = OntologyMemory()
        self.reasoner = CausalReasoner(self.memory)
        self.meta_cognition = KnowledgeBoundary()
        self.learn_engine = AutoLearnEngine()
        
        # 内置初始知识
        self._init_knowledge()
        
        print(f"\n🌱 {self.name} 已初始化（ontology-platform v1.0）")
        print(f"   记忆层: {len(self.memory._entities)} 个实体")
        print(f"   推理规则: {len(self.reasoner.rules)} 条")
    
    def _init_knowledge(self):
        """初始化内置知识"""
        # 添加初始概念
        self.memory.add_entity("Concept", "供应商风险", {
            "definition": "供应商无法按时交付或质量不达标的风险",
            "severity": "high"
        })
        self.memory.add_entity("Rule", "高风险供应商处理规则", {
            "condition": "供应商评级 < 3 且 交付准时率 < 80%",
            "action": "增加备选供应商"
        })
        
        # 添加因果关系
        self.reasoner.add_causal_relation("原材料涨价", "供应商成本上升", 0.85)
        self.reasoner.add_causal_relation("供应商成本上升", "供应商风险增加", 0.75)
        self.reasoner.add_causal_relation("供应商风险增加", "采购失败概率上升", 0.80)
        
        # 注册知识边界
        self.meta_cognition.register_knowledge(
            "供应链管理", 0.8,
            keywords=["供应链", "采购", "供应商", "库存", "物流", "交付", "成本", "采购成本", "供应商稳定"]
        )
        self.meta_cognition.register_knowledge(
            "采购风险", 0.75,
            keywords=["风险", "供应商风险", "采购风险", "质量", "延误", "违约"]
        )
        
        # 添加规则
        from reasoner import Rule
        self.reasoner.learn_rule(Rule(
            id="risk_rule_1",
            name="风险处理规则",
            rule_type=RuleType.IF_THEN,
            condition="供应商风险",
            conclusion="增加备选供应商",
            confidence=0.85
        ))
    
    def learn(self, concept: str, rule: str = None, confidence: float = 0.8, 
              properties: dict = None):
        """
        学习新知识
        
        Example:
            agent.learn("新能源供应商", 
                       rule="新能源供应商 → 优先考虑",
                       confidence=0.85,
                       properties={"type": "emerging", "region": "中国"})
        """
        entity_id = self.memory.add_entity(
            entity_type="Learning",
            name=concept,
            properties=properties or {"rule": rule, "confidence": confidence}
        )
        
        if rule:
            self.reasoner.learn_rule(Rule(
                id=f"learned_{entity_id}",
                name=f"learned_rule_{entity_id}",
                rule_type=RuleType.IF_THEN,
                condition=concept,
                conclusion=rule,
                confidence=confidence
            ))
        
        self.meta_cognition.register_knowledge(concept, confidence)
        
        print(f"\n📚 {self.name} 学习了新知识:")
        print(f"   概念: {concept}")
        if rule:
            print(f"   规则: {rule}")
        print(f"   置信度: {confidence:.0%}")
        
        return entity_id
    
    def reason(self, query: str, reasoning_type: str = "causal", 
               trace: bool = True) -> ReasoningResult:
        """
        执行推理
        
        Example:
            result = agent.reason("为什么采购失败？", reasoning_type="causal")
            result.display()
        """
        # 先检查置信度
        conf, meta_response = self.meta_cognition.assess_confidence(query)
        
        print(f"\n🤔 {self.name} 收到查询: \"{query}\"")
        print(f"   元认知评估: 置信度 {conf:.0%}")
        
        if conf < 0.4:
            print(f"   {meta_response}")
            return ReasoningResult(
                conclusion=meta_response,
                reasoning_type=reasoning_type,
                confidence=conf,
                chain=[],
                facts_used=[]
            )
        
        # 执行推理
        result = self.reasoner.reason(query, reasoning_type)
        
        if trace:
            result.display()
        
        return result
    
    def ask(self, question: str) -> str:
        """
        提问接口（带元认知）
        Agent会诚实表达不确定性
        
        Example:
            response = agent.ask("量子计算的未来")
            print(response)
        """
        conf, meta_response = self.meta_cognition.assess_confidence(question)
        
        print(f"\n💬 {self.name} 收到问题: \"{question}\"")
        
        if conf < 0.4:
            return f"⚠️ {meta_response}\n   建议: 请提供更多背景信息，或查阅专业资料。"
        
        result = self.reasoner.reason(question, "logical")
        result.display()
        
        return f"\n💡 我的回答（置信度 {conf:.0%}）: {result.conclusion}"
    
    def status(self):
        """打印Agent当前状态"""
        mem_stats = self.memory.get_stats()
        print(f"\n📊 {self.name} 状态:")
        print(f"   记忆实体: {mem_stats['total']} 个")
        for t, c in mem_stats["by_type"].items():
            print(f"     - {t}: {c}")
        print(f"   推理规则: {len(self.reasoner.rules)} 条")
        print(f"   已知领域: {', '.join(self.meta_cognition.known_domains)}")
        print(f"   因果关系: {len(self.reasoner.causal_graph)} 条")


# ─────────────────────────────────────────────────────────────
# 5. Demo Runner
# ─────────────────────────────────────────────────────────────

def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main():
    """运行完整Demo"""
    print_header("🌱 ontology-platform Agent Growth Demo")
    print("展示Agent三大成长能力：学习、推理、元认知")
    
    # 创建Agent
    agent = GrowingAgent("Clawra")
    agent.status()
    
    # ── Demo 1: 学习新知识 ──
    print_header("📚 Demo 1: Agent学习新知识")
    
    # 学习新概念
    entity_id = agent.learn(
        concept="跨境电商供应商",
        rule="跨境电商供应商 → 需核查清关资质",
        confidence=0.82,
        properties={
            "industry": "e-commerce",
            "compliance": "customs_clearance"
        }
    )
    print(f"   新增实体ID: {entity_id}")
    
    # 从用户反馈中学习（模拟）
    print("\n   [模拟用户确认] '是的，这个规则正确'")
    entities = agent.learn_engine.extract_from_text("跨境电商供应商需核查清关资质")
    relations = agent.learn_engine.extract_relations(
        "跨境电商供应商需核查清关资质", 
        entities
    )
    result = agent.learn_engine.save_to_ontology(entities, relations)
    print(f"   自动学习结果: 添加了 {result['entities_added']} 个实体")
    
    agent.status()
    
    # ── Demo 2: 因果推理 ──
    print_header("🔗 Demo 2: 因果推理")
    
    # 添加新的因果关系
    agent.reasoner.add_causal_relation("地缘政治冲突", "原材料供应中断", 0.90)
    agent.reasoner.add_causal_relation("原材料供应中断", "价格波动", 0.85)
    agent.reasoner.add_causal_relation("价格波动", "采购成本上升", 0.88)
    
    result = agent.reason(
        "为什么采购成本可能上升？",
        reasoning_type="causal"
    )
    
    print("\n   追加原因链分析:")
    agent.reasoner.add_causal_relation("地缘政治冲突", "采购成本上升", 0.78)
    agent.reason("地缘政治冲突如何影响采购？", reasoning_type="causal")
    
    # ── Demo 3: 逻辑推理 ──
    print_header("🧠 Demo 3: 逻辑推理")
    
    # 添加逻辑规则
    from reasoner import Rule
    agent.reasoner.learn_rule(Rule(
        id="cost_rule",
        name="成本评估规则",
        rule_type=RuleType.IF_THEN,
        condition="成本上升",
        conclusion="重新评估供应商",
        confidence=0.9
    ))
    
    result = agent.reason(
        "成本上升时应该如何处理？",
        reasoning_type="logical"
    )
    
    # ── Demo 4: 元认知 - 置信度自知 ──
    print_header("🎯 Demo 4: 元认知 - 置信度自知")
    
    print("\n   场景A: 已知领域")
    response = agent.ask("供应商风险如何管理？")
    print(f"   {response}")
    
    print("\n   场景B: 未知领域")
    response = agent.ask("量子计算的最新进展？")
    print(f"   {response}")
    
    # ── Demo 5: 组合推理 + 元认知 ──
    print_header("🔄 Demo 5: 完整推理流程")
    
    print("""
    查询: "我们应该担心今年的供应商稳定性吗？"
    
    完整推理流程:
    1️⃣ 元认知预检 → 置信度 80%（供应链管理是已知领域）
    2️⃣ 因果推理 → 发现多条因果链指向"风险增加"
    3️⃣ 逻辑推理 → 应用"高风险 → 增加备选"规则
    4️⃣ 置信度计算 → min(0.85, 0.75, 0.80, 0.90) = 75%
    """)
    
    result = agent.reason(
        "我们应该担心今年的供应商稳定性吗？",
        reasoning_type="causal"
    )
    
    print("\n   最终响应:")
    print("   基于因果链和逻辑规则的综合分析，")
    print(f"   我对这个判断的置信度为 {result.confidence:.0%}。")
    print(f"   {result.conclusion}")
    
    # ── Demo 6: 置信度传播链 ──
    print_header("📈 Demo 6: 推理链置信度传播")
    
    calc = ConfidenceCalculator()
    chain = [0.85, 0.78, 0.92, 0.65]
    
    print(f"\n   推理链各步置信度: {chain}")
    print(f"   min传播: {calc.propagate_confidence(chain, 'min'):.0%}")
    print(f"   算术平均: {calc.propagate_confidence(chain, 'arithmetic'):.0%}")
    print(f"   乘法传播: {calc.propagate_confidence(chain, 'multiplicative'):.0%}")
    
    agent.status()
    
    print_header("✅ Demo完成")
    print("""
    总结: ontology-platform 赋能Agent三大成长能力:
    
    1️⃣ 学习特性: Agent运行时学习新规则，并持久化到本体
    2️⃣ 推理能力: 因果推理 + 逻辑推理，可追溯推理链
    3️⃣ 元认知: 置信度自知 + 知识边界识别，诚实表达不确定
    
    下一步: 将此Demo集成到你的Agent中，
    让你的Agent真正具备成长能力！
    """)


if __name__ == "__main__":
    main()
