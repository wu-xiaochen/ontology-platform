"""
推理引擎 (Reasoner)
基于规则的推理引擎，支持前向链和后向链推理
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from collections import defaultdict
from enum import Enum

from loader import OntologyLoader, OntologyClass, OntologyProperty, OntologyIndividual
from confidence import ConfidenceCalculator, ConfidenceResult, Evidence

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuleType(Enum):
    """规则类型"""
    IF_THEN = "if_then"           # 产生式规则
    EQUIVALENCE = "equivalence"   # 等价关系
    TRANSITIVE = "transitive"    # 传递规则
    SYMMETRIC = "symmetric"       # 对称规则
    INVERSE = "inverse"           # 逆规则


class InferenceDirection(Enum):
    """推理方向"""
    FORWARD = "forward"           # 前向链
    BACKWARD = "backward"         # 后向链
    BIDIRECTIONAL = "bidirectional"  # 双向


@dataclass
class Rule:
    """推理规则"""
    id: str
    name: str
    rule_type: RuleType
    condition: str                # 条件模式 (支持变量)
    conclusion: str               # 结论模式
    confidence: float = 1.0       # 规则置信度
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # 解析条件中的变量
        self.condition_vars = set(re.findall(r'\?(\w+)', self.condition))
        self.conclusion_vars = set(re.findall(r'\?(\w+)', self.conclusion))


@dataclass
class Fact:
    """事实/断言"""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source: str = "unknown"
    timestamp: Optional[str] = None
    
    def to_tuple(self) -> tuple:
        """转换为元组用于比较"""
        return (self.subject, self.predicate, self.object)


@dataclass
class InferenceStep:
    """推理步骤"""
    rule: Rule
    matched_facts: list[Fact]     # 匹配的事实
    substitutions: dict[str, str] # 变量替换
    conclusion: Fact               # 推出的结论
    confidence: ConfidenceResult  # 推理置信度


@dataclass
class InferenceResult:
    """推理结果"""
    conclusions: list[InferenceStep]  # 推理步骤
    facts_used: list[Fact]             # 使用的事实
    depth: int                        # 推理深度
    total_confidence: ConfidenceResult  # 整体置信度


class Reasoner:
    """
    推理引擎
    
    支持:
    - 前向链推理 (从事实推导结论)
    - 后向链推理 (从目标反向推导)
    - 混合推理策略
    - 置信度传播
    
    示例:
        reasoner = Reasoner(ontology)
        reasoner.load_rules_from_file("rules.json")
        result = reasoner.forward_chain(initial_facts)
        print(f"推导出 {len(result.conclusions)} 个结论")
    """
    
    def __init__(self, ontology: Optional[OntologyLoader] = None):
        """
        初始化推理引擎
        
        Args:
            ontology: 本体加载器 (可选)
        """
        self.ontology = ontology
        self.rules: dict[str, Rule] = {}
        self.facts: list[Fact] = []
        self.inference_cache: dict[str, list[Fact]] = defaultdict(list)
        self.confidence_calculator = ConfidenceCalculator()
        
        # 规则索引 (按谓词索引)
        self.predicate_index: dict[str, list[str]] = defaultdict(list)
        
        # 注册内置规则
        self._register_builtin_rules()
    
    def _register_builtin_rules(self):
        """注册内置规则"""
        # 传递规则: A -> B, B -> C => A -> C
        transitivity = Rule(
            id="builtin:transitivity",
            name="传递性规则",
            rule_type=RuleType.TRANSITIVE,
            condition="(?x ?p ?y) AND (?y ?p ?z)",
            conclusion="(?x ?p ?z)",
            confidence=0.95,
            description="传递属性推导"
        )
        self.add_rule(transitivity)
        
        # 对称规则: A knows B => B knows A
        symmetry = Rule(
            id="builtin:symmetry",
            name="对称性规则",
            rule_type=RuleType.SYMMETRIC,
            condition="(?x ?p ?y)",
            conclusion="(?y ?p ?x)",
            confidence=0.9,
            description="对称属性推导"
        )
        self.add_rule(symmetry)
    
    def add_rule(self, rule: Rule):
        """
        添加推理规则
        
        Args:
            rule: 推理规则
        """
        self.rules[rule.id] = rule
        
        # 索引规则
        # 从条件中提取谓词
        pred_match = re.search(r'\?(\w+)', rule.condition)
        if pred_match:
            self.predicate_index[pred_match.group(1)].append(rule.id)
        
        logger.info(f"添加规则: {rule.name} ({rule.id})")
    
    def add_fact(self, fact: Fact):
        """添加事实"""
        # 检查是否已存在
        existing = self._find_fact(fact.subject, fact.predicate, fact.object)
        if existing is None:
            self.facts.append(fact)
            logger.debug(f"添加事实: {fact.subject} {fact.predicate} {fact.object}")
    
    def _find_fact(self, subject: str, predicate: str, obj: str) -> Optional[Fact]:
        """查找事实"""
        for f in self.facts:
            if f.subject == subject and f.predicate == predicate and f.object == obj:
                return f
        return None
    
    def clear_facts(self):
        """清空事实库"""
        self.facts.clear()
    
    def forward_chain(
        self,
        initial_facts: Optional[list[Fact]] = None,
        max_depth: int = 10,
        direction: InferenceDirection = InferenceDirection.FORWARD
    ) -> InferenceResult:
        """
        前向链推理
        
        Args:
            initial_facts: 初始事实列表
            max_depth: 最大推理深度
            direction: 推理方向
        
        Returns:
            推理结果
        """
        # 初始化事实库
        if initial_facts:
            self.facts.extend(initial_facts)
        
        derived_facts: list[InferenceStep] = []
        used_facts: list[Fact] = []
        
        # 工作记忆
        working_facts = list(self.facts)
        seen_triples = {(f.subject, f.predicate, f.object) for f in working_facts}
        
        for depth in range(max_depth):
            new_facts = []
            
            for fact in working_facts:
                # 匹配规则
                matched_rules = self._match_rules(fact, direction)
                
                for rule, substitutions in matched_rules:
                    # 应用规则
                    conclusion_fact = self._apply_rule(rule, fact, substitutions)
                    
                    # 检查是否已存在
                    triple = (conclusion_fact.subject, conclusion_fact.predicate, conclusion_fact.object)
                    if triple in seen_triples:
                        continue
                    
                    # 计算置信度
                    evidence = [
                        Evidence(source=f.source, reliability=f.confidence, content=f)
                        for f in [fact]
                    ]
                    evidence.append(Evidence(
                        source="rule",
                        reliability=rule.confidence,
                        content=rule.id
                    ))
                    
                    conf_result = self.confidence_calculator.calculate(
                        evidence, method="multiplicative"
                    )
                    conclusion_fact.confidence = conf_result.value
                    
                    # 记录推理步骤
                    step = InferenceStep(
                        rule=rule,
                        matched_facts=[fact],
                        substitutions=substitutions,
                        conclusion=conclusion_fact,
                        confidence=conf_result
                    )
                    
                    derived_facts.append(step)
                    new_facts.append(conclusion_fact)
                    seen_triples.add(triple)
                    # 避免重复添加同一事实
                    if fact.to_tuple() not in {f.to_tuple() for f in used_facts}:
                        used_facts.append(fact)
            
            if not new_facts:
                break
            
            working_facts.extend(new_facts)
        
        # 计算整体置信度
        if derived_facts:
            chain_confidences = [step.confidence.value for step in derived_facts]
            overall_conf_value = self.confidence_calculator.propagate_confidence(
                chain_confidences, method="min"
            )
            overall_conf = ConfidenceResult(
                value=overall_conf_value,
                method="forward_chain"
            )
        else:
            overall_conf = ConfidenceResult(value=0.0, method="forward_chain")
        
        return InferenceResult(
            conclusions=derived_facts,
            facts_used=used_facts,
            depth=max_depth,
            total_confidence=overall_conf
        )
    
    def backward_chain(
        self,
        goal: Fact,
        max_depth: int = 10
    ) -> InferenceResult:
        """
        后向链推理
        
        从目标反向推导前提
        
        Args:
            goal: 目标事实
            max_depth: 最大推理深度
        
        Returns:
            推理结果
        """
        # BFS 后向推理
        conclusions: list[InferenceStep] = []
        used_facts: list[Fact] = []
        
        # 队列: (目标事实, 深度, 路径)
        queue = [(goal, 0, [])]
        
        while queue:
            current_goal, depth, path = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            # 检查事实库中是否已有
            matching = self._find_matching_facts(current_goal)
            if matching:
                for fact in matching:
                    used_facts.add(fact)
                    conclusions.append(InferenceStep(
                        rule=Rule(
                            id="fact",
                            name="事实匹配",
                            rule_type=RuleType.IF_THEN,
                            condition="",
                            conclusion=""
                        ),
                        matched_facts=[fact],
                        substitutions={},
                        conclusion=current_goal,
                        confidence=ConfidenceResult(
                            value=fact.confidence,
                            method="fact_match"
                        )
                    ))
            else:
                # 查找可推出此目标的规则
                relevant_rules = self._find_rules_for_conclusion(current_goal)
                
                for rule in relevant_rules:
                    # 反向应用规则
                    preconditions = self._backward_apply(rule, current_goal)
                    
                    for precond in preconditions:
                        queue.append((precond, depth + 1, path + [rule]))
        
        # 计算置信度
        if conclusions:
            chain_confidences = [c.confidence.value for c in conclusions]
            overall_conf_value = self.confidence_calculator.propagate_confidence(
                chain_confidences, method="min"
            )
            overall_conf = ConfidenceResult(
                value=overall_conf_value,
                method="backward_chain"
            )
        else:
            overall_conf = ConfidenceResult(value=0.0, method="backward_chain")
        
        return InferenceResult(
            conclusions=conclusions,
            facts_used=used_facts,
            depth=max_depth,
            total_confidence=overall_conf
        )
    
    def _match_rules(
        self,
        fact: Fact,
        direction: InferenceDirection
    ) -> list[tuple[Rule, dict[str, str]]]:
        """匹配事实与规则"""
        matched = []
        
        for rule in self.rules.values():
            if rule.rule_type == RuleType.TRANSITIVE:
                # 传递规则特殊处理
                # 查找 (X, P, Y) 和 (Y, P, Z) => (X, P, Z)
                for other_fact in self.facts:
                    if other_fact.predicate == fact.predicate and other_fact.object == fact.subject:
                        substitutions = {
                            '?x': other_fact.subject,
                            '?y': fact.subject,
                            '?z': fact.object
                        }
                        matched.append((rule, substitutions))
            
            elif rule.rule_type == RuleType.SYMMETRIC:
                # 对称规则: (?x ?p ?y) => (?y ?p ?x)
                if fact.predicate in rule.metadata.get('symmetric_properties', []):
                    substitutions = {
                        '?x': fact.subject,
                        '?y': fact.object
                    }
                    matched.append((rule, substitutions))
            
            elif rule.rule_type == RuleType.IF_THEN:
                # 产生式规则匹配
                match = self._pattern_match(rule.condition, fact)
                if match:
                    matched.append((rule, match))
        
        return matched
    
    def _pattern_match(self, pattern: str, fact: Fact) -> Optional[dict[str, str]]:
        """模式匹配"""
        # 简化: 检查主体和谓词是否匹配
        # 实际应支持更复杂的模式匹配
        
        # 提取模式中的变量
        vars_in_pattern = re.findall(r'\?(\w+)', pattern)
        if not vars_in_pattern:
            return None
        
        # 简单匹配: pattern 中第一个变量匹配 subject
        substitutions = {}
        
        # 检查 pattern 是否包含这个三元组
        # 格式: (?x ?p ?y) 或 (?s ?p ?o)
        if '?x' in pattern and '?y' in pattern:
            # (?x ?p ?y) 匹配当前事实
            # 需要规则本身定义了 predicate
            pass
        
        # 简化实现: 如果 pattern 是空的或包含相同谓词
        return {} if vars_in_pattern else None
    
    def _apply_rule(
        self,
        rule: Rule,
        matched_fact: Fact,
        substitutions: dict[str, str]
    ) -> Fact:
        """应用规则生成新事实"""
        # 提取结论中的变量
        if rule.rule_type == RuleType.TRANSITIVE:
            return Fact(
                subject=substitutions.get('?x', ''),
                predicate=matched_fact.predicate,
                object=substitutions.get('?z', ''),
                confidence=rule.confidence,
                source=f"inferred:{rule.id}"
            )
        elif rule.rule_type == RuleType.SYMMETRIC:
            return Fact(
                subject=matched_fact.object,
                predicate=matched_fact.predicate,
                object=matched_fact.subject,
                confidence=rule.confidence,
                source=f"inferred:{rule.id}"
            )
        else:
            # 通用规则应用
            # 替换变量
            conclusion = rule.conclusion
            for var, value in substitutions.items():
                conclusion = conclusion.replace(var, value)
            
            # 解析三元组
            parts = conclusion.strip('()').split()
            if len(parts) >= 3:
                return Fact(
                    subject=parts[0],
                    predicate=parts[1],
                    object=parts[2],
                    confidence=rule.confidence,
                    source=f"inferred:{rule.id}"
                )
        
        # 默认返回
        return Fact(
            subject="unknown",
            predicate="unknown",
            object="unknown",
            confidence=0.0
        )
    
    def _find_matching_facts(self, pattern: Fact) -> list[Fact]:
        """查找匹配的事实"""
        matches = []
        for fact in self.facts:
            if self._fact_matches(fact, pattern):
                matches.append(fact)
        return matches
    
    def _fact_matches(self, fact: Fact, pattern: Fact) -> bool:
        """检查事实是否匹配模式"""
        # 支持变量
        if pattern.subject != '?' and pattern.subject != fact.subject:
            return False
        if pattern.predicate != '?' and pattern.predicate != fact.predicate:
            return False
        if pattern.object != '?' and pattern.object != fact.object:
            return False
        return True
    
    def _find_rules_for_conclusion(self, goal: Fact) -> list[Rule]:
        """查找可以推出目标结论的规则"""
        relevant = []
        
        for rule in self.rules.values():
            if rule.rule_type == RuleType.IF_THEN:
                # 检查规则结论是否能匹配目标
                conclusion_parts = rule.conclusion.strip('()').split()
                if len(conclusion_parts) >= 3:
                    # 简化: 检查谓词是否匹配
                    if conclusion_parts[1] == goal.predicate:
                        relevant.append(rule)
        
        return relevant
    
    def _backward_apply(self, rule: Rule, goal: Fact) -> list[Fact]:
        """反向应用规则"""
        # 简化实现
        preconditions = []
        
        # 从条件中提取前置事实
        # 格式: (?x ?p ?y) AND (?y ?p ?z)
        if 'AND' in rule.condition:
            parts = rule.condition.split('AND')
            for part in parts:
                part = part.strip()
                vars = re.findall(r'\?(\w+)', part)
                if len(vars) >= 3:
                    # 创建前置条件
                    preconditions.append(Fact(
                        subject=vars[0],
                        predicate='?p',
                        object=vars[2]
                    ))
        
        return preconditions
    
    def explain(self, result: InferenceResult) -> str:
        """
        解释推理过程
        
        Args:
            result: 推理结果
        
        Returns:
            可读的解释
        """
        lines = []
        lines.append(f"推理完成:")
        lines.append(f"  推导出 {len(result.conclusions)} 个结论")
        lines.append(f"  使用了 {len(result.facts_used)} 个事实")
        lines.append(f"  推理深度: {result.depth}")
        lines.append(f"  整体置信度: {result.total_confidence.value:.3f}")
        lines.append("")
        
        lines.append("推理过程:")
        for i, step in enumerate(result.conclusions, 1):
            lines.append(f"  {i}. {step.rule.name}")
            lines.append(f"     前提: {step.matched_facts[0].subject} {step.matched_facts[0].predicate} {step.matched_facts[0].object}")
            lines.append(f"     结论: {step.conclusion.subject} {step.conclusion.predicate} {step.conclusion.object}")
            lines.append(f"     置信度: {step.confidence.value:.3f}")
        
        return "\n".join(lines)
    
    def add_rule_from_dict(self, rule_dict: dict) -> Rule:
        """
        从字典创建规则
        
        Args:
            rule_dict: 规则字典
        
        Returns:
            创建的规则
        """
        rule = Rule(
            id=rule_dict.get('id', f"rule_{len(self.rules)}"),
            name=rule_dict.get('name', 'Unnamed Rule'),
            rule_type=RuleType(rule_dict.get('type', 'if_then')),
            condition=rule_dict.get('condition', ''),
            conclusion=rule_dict.get('conclusion', ''),
            confidence=rule_dict.get('confidence', 1.0),
            description=rule_dict.get('description', ''),
            metadata=rule_dict.get('metadata', {})
        )
        
        self.add_rule(rule)
        return rule
    
    def load_rules_from_list(self, rules: list[dict]):
        """从字典列表加载规则"""
        for rule_dict in rules:
            self.add_rule_from_dict(rule_dict)
    
    def query(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> list[Fact]:
        """
        查询事实库
        
        Args:
            subject: 主体 (None 表示任意)
            predicate: 谓词 (None 表示任意)
            obj: 客体 (None 表示任意)
            min_confidence: 最小置信度
        
        Returns:
            匹配的事实列表
        """
        results = []
        for fact in self.facts:
            if subject and fact.subject != subject:
                continue
            if predicate and fact.predicate != predicate:
                continue
            if obj and fact.object != obj:
                continue
            if fact.confidence < min_confidence:
                continue
            results.append(fact)
        return results


# 便捷函数
def create_sample_reasoner() -> Reasoner:
    """
    创建示例推理引擎
    
    包含一些测试规则和事实
    """
    # 创建本体
    ontology = create_sample_ontology()
    
    # 创建推理引擎
    reasoner = Reasoner(ontology)
    
    # 添加自定义规则
    # 规则1: 老师教学生 => 老师是教育者
    reasoner.add_rule_from_dict({
        'id': 'rule:teacher_student',
        'name': '师生关系推导',
        'type': 'if_then',
        'condition': '(?teacher http://example.org/teaches ?student)',
        'conclusion': '(?teacher http://example.org/isEducator true)',
        'confidence': 0.85,
        'description': '教学生的老师是教育者'
    })
    
    # 规则2: 知道某人 => 被知道
    reasoner.add_rule_from_dict({
        'id': 'rule:knows_symmetric',
        'name': '认识关系对称',
        'type': 'symmetric',
        'condition': '(?x http://example.org/knows ?y)',
        'conclusion': '(?y http://example.org/knows ?x)',
        'confidence': 0.9,
        'description': '认识关系是对称的',
        'metadata': {'symmetric_properties': ['http://example.org/knows']}
    })
    
    # 规则3: 人类 => 是生物
    reasoner.add_rule_from_dict({
        'id': 'rule:person_animal',
        'name': '人是动物',
        'type': 'if_then',
        'condition': '(?x rdf:type http://example.org/Person)',
        'conclusion': '(?x rdf:type http://example.org/Animal)',
        'confidence': 0.95,
        'description': '人属于动物类'
    })
    
    # 添加初始事实
    reasoner.add_fact(Fact(
        subject='http://example.org/Alice',
        predicate='http://example.org/knows',
        object='http://example.org/Bob',
        confidence=0.9,
        source='user_input'
    ))
    
    reasoner.add_fact(Fact(
        subject='http://example.org/Bob',
        predicate='http://example.org/teaches',
        object='http://example.org/Alice',
        confidence=0.85,
        source='user_input'
    ))
    
    return reasoner


# 导入需要的函数
from loader import create_sample_ontology


# 测试代码
if __name__ == '__main__':
    print("=== 推理引擎测试 ===\n")
    
    # 创建推理引擎
    reasoner = create_sample_reasoner()
    
    print(f"加载了 {len(reasoner.rules)} 个规则")
    print(f"加载了 {len(reasoner.facts)} 个事实\n")
    
    # 测试前向链推理
    print("--- 前向链推理 ---")
    result = reasoner.forward_chain(max_depth=5)
    print(f"推导出 {len(result.conclusions)} 个新结论")
    print(f"使用事实: {len(result.facts_used)} 个")
    print(f"整体置信度: {result.total_confidence.value:.3f}")
    
    print("\n--- 详细结果 ---")
    for i, step in enumerate(result.conclusions, 1):
        print(f"{i}. {step.rule.name}")
        print(f"   结论: {step.conclusion.subject} {step.conclusion.predicate} {step.conclusion.object}")
        print(f"   置信度: {step.confidence.value:.3f}")
    
    # 测试查询
    print("\n--- 查询事实 ---")
    knows_facts = reasoner.query(predicate='http://example.org/knows')
    for f in knows_facts:
        print(f"  {f.subject} knows {f.object} (conf: {f.confidence})")
    
    # 测试后向链
    print("\n--- 后向链推理 ---")
    goal = Fact(
        subject='?x',
        predicate='http://example.org/isEducator',
        object='true'
    )
    result2 = reasoner.backward_chain(goal, max_depth=3)
    print(f"找到 {len(result2.conclusions)} 条推理路径")
    
    # 解释
    print("\n--- 推理解释 ---")
    print(reasoner.explain(result))