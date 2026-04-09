"""
推理引擎 (Reasoner)
基于规则的推理引擎，支持前向链和后向链推理

⚠️ OWL 语义注意事项：
本引擎基于开放世界假设 (OWA) 运行。
- 约束 (constraints) 不等同于数据库的外键约束
- owl:someValuesFrom/owl:allValuesFrom 表达存在性/全称量化， 非闭路校验
- 基数限制 (min/max) 不等同于唯一性约束
详见: OWL_SEMANTICS.md
"""

import re
import logging
import time as _time
from dataclasses import dataclass, field
from typing import Any, Optional, List
from collections import defaultdict
from enum import Enum

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 降级 Stub 类定义 - 当依赖不可用时提供有意义的错误
# ─────────────────────────────────────────────

class _UnavailableModuleStub:
    """
    模块不可用时的占位符基类
    
    通过 __getattr__ 拦截所有属性访问，抛出有意义的错误信息，
    避免在降级模式下出现难以调试的 AttributeError 或 NoneType 错误
    """
    
    def __init__(self, module_name: str, install_hint: str = ""):
        self._module_name = module_name
        self._install_hint = install_hint or f"请检查 {module_name} 模块是否正确安装"
    
    def __getattr__(self, name: str) -> Any:
        # 拦截所有属性访问，抛出包含模块名和安装提示的错误
        raise ImportError(
            f"'{self._module_name}' 模块不可用，无法访问属性 '{name}'。"
            f"{self._install_hint}"
        )
    
    def __call__(self, *args, **kwargs) -> Any:
        # 拦截直接调用（如 KnowledgeGraph()）
        raise ImportError(
            f"'{self._module_name}' 模块不可用，无法实例化。"
            f"{self._install_hint}"
        )
    
    def __bool__(self) -> bool:
        # 在 if 语句中表现为 False，支持降级检查
        return False


# KnowledgeGraph 降级 Stub
class _KnowledgeGraphStub(_UnavailableModuleStub):
    """KnowledgeGraph 模块不可用的占位符"""
    
    def __init__(self):
        super().__init__(
            module_name="KnowledgeGraph",
            install_hint="请安装 networkx 或检查 src/core/knowledge_graph.py 是否存在"
        )


# TypedTriple 降级 Stub
class _TypedTripleStub(_UnavailableModuleStub):
    """TypedTriple 模块不可用的占位符"""
    
    def __init__(self):
        super().__init__(
            module_name="TypedTriple",
            install_hint="请检查 src/core/knowledge_graph.py 是否存在"
        )


# OntologyLoader 降级 Stub
class _OntologyLoaderStub(_UnavailableModuleStub):
    """OntologyLoader 模块不可用的占位符"""
    
    def __init__(self):
        super().__init__(
            module_name="OntologyLoader",
            install_hint="请检查 src/core/loader.py 是否存在"
        )


# OntologyClass 降级 Stub
class _OntologyClassStub(_UnavailableModuleStub):
    """OntologyClass 模块不可用的占位符"""
    
    def __init__(self):
        super().__init__(
            module_name="OntologyClass",
            install_hint="请检查 src/core/loader.py 是否存在"
        )


# OntologyProperty 降级 Stub
class _OntologyPropertyStub(_UnavailableModuleStub):
    """OntologyProperty 模块不可用的占位符"""
    
    def __init__(self):
        super().__init__(
            module_name="OntologyProperty",
            install_hint="请检查 src/core/loader.py 是否存在"
        )


# OntologyIndividual 降级 Stub
class _OntologyIndividualStub(_UnavailableModuleStub):
    """OntologyIndividual 模块不可用的占位符"""
    
    def __init__(self):
        super().__init__(
            module_name="OntologyIndividual",
            install_hint="请检查 src/core/loader.py 是否存在"
        )


# ─────────────────────────────────────────────
# 导入链处理 - 使用统一的降级策略
# ─────────────────────────────────────────────

# 尝试导入 KnowledgeGraph，失败时使用 Stub 类
try:
    from .knowledge_graph import KnowledgeGraph, TypedTriple
except ImportError as e:
    logger.warning(f"KnowledgeGraph 模块不可用: {e}，将使用降级模式")
    # 使用 Stub 类替代 None，提供有意义的错误信息
    KnowledgeGraph = _KnowledgeGraphStub()
    TypedTriple = _TypedTripleStub()

# 尝试导入 OntologyLoader，失败时使用 Stub 类
try:
    from .loader import OntologyLoader, OntologyClass, OntologyProperty, OntologyIndividual
except ImportError as e:
    logger.warning(f"OntologyLoader 模块不可用: {e}，本体功能将受限")
    # 使用 Stub 类替代 None，提供有意义的错误信息
    OntologyLoader = _OntologyLoaderStub()
    OntologyClass = _OntologyClassStub()
    OntologyProperty = _OntologyPropertyStub()
    OntologyIndividual = _OntologyIndividualStub()

# ─────────────────────────────────────────────
# 延迟导入置信度模块，避免循环导入
# ConfidenceCalculator 在 __init__ 和推理方法中延迟导入
# ConfidenceResult 和 Evidence 在此定义 fallback，避免类型注解问题
# ─────────────────────────────────────────────

# 延迟导入的模块引用，初始为 None
_ConfidenceCalculator = None
_confidence_module_loaded = False


def _get_confidence_calculator():
    """
    延迟导入 ConfidenceCalculator，避免循环导入
    
    在第一次调用时才导入 confidence 模块，打破 reasoner <-> confidence 的循环依赖。
    使用模块级缓存避免重复导入。
    
    Returns:
        ConfidenceCalculator 类（导入成功）或 None（导入失败时返回 fallback）
    """
    global _ConfidenceCalculator, _confidence_module_loaded
    
    # 如果已经尝试过导入，直接返回缓存结果
    if _confidence_module_loaded:
        return _ConfidenceCalculator
    
    _confidence_module_loaded = True
    try:
        # 延迟导入：在函数内部执行 import，避免模块顶层循环依赖
        from ..eval.confidence import ConfidenceCalculator
        _ConfidenceCalculator = ConfidenceCalculator
        return _ConfidenceCalculator
    except ImportError as e:
        # 导入失败时返回 fallback 类，避免程序崩溃
        logger.warning(f"Confidence 模块不可用: {e}，使用简化置信度计算")
        return None


@dataclass
class ConfidenceResult:
    """
    置信度结果数据结构
    
    作为 fallback 类定义，当 confidence 模块不可用时使用。
    同时用于类型注解，避免运行时导入问题。
    """
    value: float  # 置信度值，范围 [0.0, 1.0]
    method: str   # 计算方法名称
    evidence_count: int = 0  # 证据数量


@dataclass
class Evidence:
    """
    证据数据结构
    
    作为 fallback 类定义，当 confidence 模块不可用时使用。
    用于表示推理过程中的单个证据源。
    """
    source: str           # 证据来源标识
    reliability: float    # 证据可靠性 [0.0, 1.0]
    content: Any          # 证据内容
    timestamp: Optional[str] = None  # 时间戳（可选）


class _SimpleConfidenceCalculator:
    """
    简化版置信度计算器 (Fallback)
    
    当 eval.confidence 模块不可用时使用此简化实现。
    提供基本的置信度计算和传播功能，确保推理引擎可正常工作。
    """
    
    def __init__(self, default_reliability: float = 0.5):
        # 默认可靠性阈值，用于无证据时的回退计算
        self.default_reliability = default_reliability
    
    def calculate(self, evidence: List[Evidence], method: str = "weighted", **kwargs) -> ConfidenceResult:
        """
        计算证据的加权置信度
        
        Args:
            evidence: 证据列表
            method: 计算方法（支持 weighted, multiplicative）
            
        Returns:
            置信度结果
        """
        if not evidence:
            # 无证据时返回零置信度，避免除以零错误
            return ConfidenceResult(value=0.0, method=method)
        
        # 提取所有证据的可靠性值
        values = [e.reliability for e in evidence]
        
        if method == "multiplicative":
            # 乘法融合：所有证据可靠性相乘
            result = 1.0
            for v in values:
                result *= v
            return ConfidenceResult(value=result, method=method, evidence_count=len(evidence))
        
        # 默认使用加权平均
        return ConfidenceResult(
            value=sum(values) / len(values),
            method=method,
            evidence_count=len(evidence)
        )
    
    def propagate_confidence(self, confidences: List[float], method: str = "min") -> float:
        """
        传播置信度（链式推理时使用）
        
        Args:
            confidences: 置信度列表
            method: 传播策略（min 保守, average 融合）
            
        Returns:
            传播后的置信度
        """
        if not confidences:
            return 0.0
        if method == "min":
            # 保守策略：取最小值，确保链式推理的可靠性
            return min(confidences)
        # 平均策略：适用于并行证据的融合
        return sum(confidences) / len(confidences)


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
        # 解析条件中的变量 (支持 ?var 格式)
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
        # v2.0: 使用 KnowledgeGraph 替代 list[Fact]，提供 O(1) 索引查询
        if KnowledgeGraph is not None:
            self._graph = KnowledgeGraph()
        else:
            self._graph = None
        self._facts_legacy: list[Fact] = []  # fallback when KnowledgeGraph unavailable
        self.inference_cache: dict[str, list[Fact]] = defaultdict(list)
        
        # 延迟导入 ConfidenceCalculator，避免循环导入
        # 使用 getter 函数获取类，在首次使用时才真正导入
        _calculator_class = _get_confidence_calculator()
        if _calculator_class is not None:
            # 导入成功：使用真实的 ConfidenceCalculator
            self.confidence_calculator = _calculator_class()
        else:
            # 导入失败：使用 fallback 简化计算器
            self.confidence_calculator = _SimpleConfidenceCalculator()
        
        # 规则索引 (按谓词索引)
        self.predicate_index: dict[str, list[str]] = defaultdict(list)
        
        # 注册内置规则
        self._register_builtin_rules()

    @property
    def graph(self) -> 'KnowledgeGraph':
        """访问底层知识图谱引擎"""
        return self._graph

    @property
    def facts(self) -> list['Fact']:
        """兼容属性: 返回所有事实 (Fact 对象列表)"""
        if self._graph is not None:
            return [
                Fact(
                    subject=t.subject,
                    predicate=t.predicate,
                    object=t.object,
                    confidence=t.confidence,
                    source=t.source,
                    timestamp=None,
                )
                for t in self._graph
            ]
        return self._facts_legacy

    @facts.setter
    def facts(self, value):
        """兼容 setter: 支持 self.facts = [] 等操作"""
        if self._graph is not None:
            self._graph.clear()
            if value:
                for f in value:
                    self._graph.add_triple(
                        f.subject, f.predicate, f.object,
                        confidence=f.confidence,
                        source=f.source or "unknown",
                    )
        else:
            self._facts_legacy = value
    
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
        """添加事实 (自动去重)"""
        if self._graph is not None:
            self._graph.add_triple(
                fact.subject, fact.predicate, fact.object,
                confidence=fact.confidence,
                source=fact.source or "unknown",
            )
        else:
            existing = self._find_fact(fact.subject, fact.predicate, fact.object)
            if existing is None:
                self._facts_legacy.append(fact)
        logger.debug(f"添加事实: {fact.subject} {fact.predicate} {fact.object}")

    def _find_fact(self, subject: str, predicate: str, obj: str) -> Optional[Fact]:
        """查找事实"""
        if self._graph is not None:
            if self._graph.has_triple(subject, predicate, obj):
                results = self._graph.query(subject=subject, predicate=predicate, obj=obj, limit=1)
                if results:
                    t = results[0]
                    return Fact(t.subject, t.predicate, t.object, t.confidence, t.source)
            return None
        for f in self._facts_legacy:
            if f.subject == subject and f.predicate == predicate and f.object == obj:
                return f
        return None

    def clear_facts(self):
        """清空事实库"""
        if self._graph is not None:
            self._graph.clear()
        else:
            self._facts_legacy.clear()
    
    def forward_chain(
        self,
        initial_facts: Optional[list[Fact]] = None,
        max_depth: int = 10,
        timeout_seconds: float = 5.0,
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
        # 初始化事实库：将外部传入的初始事实加入工作记忆
        if initial_facts:
            for f in initial_facts:
                self.add_fact(f)
        
        derived_facts: list[InferenceStep] = []  # 累计的推理步骤
        used_facts: list[Fact] = []  # 参与推理的事实
        
        # 工作记忆：拷贝当前事实库作为推理的工作集
        working_facts = list(self.facts)
        # 已见三元组集合，防止推导出重复结论
        seen_triples = {(f.subject, f.predicate, f.object) for f in working_facts}
        
        start_time = _time.time()
        # 逐层迭代推理，每层尝试将规则应用于所有工作事实
        for depth in range(max_depth):
            # 熔断器机制：超时则强制终止推理循环
            if _time.time() - start_time > timeout_seconds:
                logger.error(f"⚠️ Circuit Breaker Triggered (Forward Chain): Exceeded {timeout_seconds}s limit at depth {depth}.")
                break
            
            new_facts = []  # 本层新推导出的事实
            
            for fact in working_facts:
                # 尝试将每个事实与所有规则进行匹配
                matched_rules = self._match_rules(fact, direction)
                
                for rule, substitutions in matched_rules:
                    # 应用规则生成新的结论事实
                    conclusion_fact = self._apply_rule(rule, fact, substitutions)
                    
                    # 查重：避免重复推导相同的三元组
                    triple = (conclusion_fact.subject, conclusion_fact.predicate, conclusion_fact.object)
                    if triple in seen_triples:
                        continue
                    
                    # 基于证据计算结论的置信度（事实可靠性 × 规则置信度）
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
                    base_confidence = min(fact.confidence, rule.confidence)
                    conclusion_confidence = min(conf_result.value, base_confidence)
                    conclusion_fact.confidence = conclusion_confidence
                    
                    # 记录推理步骤：包含规则、前提、结论、置信度
                    step = InferenceStep(
                        rule=rule,
                        matched_facts=[fact],
                        substitutions=substitutions,
                        conclusion=conclusion_fact,
                        confidence=conf_result
                    )
                    
                    derived_facts.append(step)
                    new_facts.append(conclusion_fact)
                    seen_triples.add(triple)  # 标记为已见避免重复
                    # 记录参与推理的原始事实（去重）
                    if fact.to_tuple() not in {f.to_tuple() for f in used_facts}:
                        used_facts.append(fact)
            
            # 本层无新事实产生，推理已收敛，提前结束
            if not new_facts:
                break
            
            # 将新推导的事实加入工作集，供下一层推理使用
            working_facts.extend(new_facts)
        
        # 计算推理链的整体置信度（取最小值，保守策略）
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
        max_depth: int = 10,
        timeout_seconds: float = 5.0
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
        # BFS 后向推理：从目标往回搜索可能的前提条件
        conclusions: list[InferenceStep] = []  # 累计的推理步骤
        used_facts: set = set()  # 存储事实元组（而非 Fact 对象）以支持哈希去重
        
        # BFS 队列：每个元素包含 (目标事实, 当前深度, 推理路径)
        queue = [(goal, 0, [])]
        
        start_time = _time.time()
        
        while queue:
            # 熔断器：超时则强制终止后向推理
            if _time.time() - start_time > timeout_seconds:
                logger.error(f"⚠️ Circuit Breaker Triggered (Backward Chain): Exceeded {timeout_seconds}s limit.")
                break
            # 从队列头部取出当前目标
            current_goal, depth, path = queue.pop(0)
            
            # 深度限制：超过最大深度则跳过该分支
            if depth >= max_depth:
                continue
            
            # 在事实库中搜索是否已有匹配的事实
            matching = self._find_matching_facts(current_goal)
            if matching:
                # 找到匹配事实，记录为推理结果
                for fact in matching:
                    used_facts.add(fact.to_tuple())  # 存储元组而非 Fact 对象
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
                # 未找到匹配事实，查找可推出此目标的规则
                relevant_rules = self._find_rules_for_conclusion(current_goal)
                
                for rule in relevant_rules:
                    # 反向应用规则：从结论反推前提条件
                    preconditions = self._backward_apply(rule, current_goal)
                    
                    # 将前提条件加入 BFS 队列继续反向搜索
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
        
        # Convert tuples back to Fact objects for return
        used_facts_list = [Fact(t[0], t[1], t[2]) for t in used_facts]
        
        return InferenceResult(
            conclusions=conclusions,
            facts_used=used_facts_list,
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
                # 传递规则特殊处理 (v2.0: 索引加速)
                # 查找 (X, P, Y) 和 (Y, P, Z) => (X, P, Z)
                if self._graph is not None:
                    # 使用索引: 查找 predicate 相同且 object == fact.subject 的三元组
                    candidates = self._graph.query(
                        predicate=fact.predicate, obj=fact.subject
                    )
                    other_facts = [
                        Fact(t.subject, t.predicate, t.object, t.confidence, t.source)
                        for t in candidates
                    ]
                else:
                    other_facts = [
                        f for f in self._facts_legacy
                        if f.predicate == fact.predicate and f.object == fact.subject
                    ]
                for other_fact in other_facts:
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
        """
        模式匹配
        支持格式: (?x predicate object) 或 (?x predicate ?y)
        """
        # 提取模式中的变量
        pattern = pattern.strip('()')
        parts = pattern.split()
        if len(parts) < 3:
            return None
            
        p_subj, p_pred, p_obj = parts
        
        # 检查谓词是否匹配 (核心逻辑)
        if p_pred != fact.predicate:
            return None
            
        substitutions = {}
        
        # 匹配主体
        if p_subj.startswith('?'):
            substitutions[p_subj] = fact.subject
        elif p_subj != fact.subject:
            return None
            
        # 匹配客体
        if p_obj.startswith('?'):
            substitutions[p_obj] = fact.object
        elif p_obj != fact.object:
            return None
            
        return substitutions
    
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
        """查找匹配的事实 (v2.0: 索引加速)"""
        if self._graph is not None:
            # 使用图索引查询，将通配符 '?' 转为 None
            s = pattern.subject if pattern.subject != '?' else None
            p = pattern.predicate if pattern.predicate != '?' else None
            o = pattern.object if pattern.object != '?' else None
            results = self._graph.query(subject=s, predicate=p, obj=o)
            return [
                Fact(t.subject, t.predicate, t.object, t.confidence, t.source)
                for t in results
            ]
        matches = []
        for fact in self._facts_legacy:
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
        lines.append("推理完成:")
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
        查询事实库 (v2.0: 索引加速)
        
        Args:
            subject: 主体 (None 表示任意)
            predicate: 谓词 (None 表示任意)
            obj: 客体 (None 表示任意)
            min_confidence: 最小置信度
        
        Returns:
            匹配的事实列表
        """
        if self._graph is not None:
            triples = self._graph.query(
                subject=subject or None,
                predicate=predicate or None,
                obj=obj or None,
                min_confidence=min_confidence,
            )
            return [
                Fact(t.subject, t.predicate, t.object, t.confidence, t.source)
                for t in triples
            ]
        results = []
        for fact in self._facts_legacy:
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
from .loader import create_sample_ontology


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
    
    # 解释
    print("\n--- 推理解释 ---")
    print(reasoner.explain(result))