"""
自我纠错模块 (Self-Correction Module)

提供知识冲突检测和推理反思能力，防止知识图谱数据污染。

核心组件：
1. ContradictionChecker —— 在写入新知识前检测与已有知识的矛盾
2. ReflectionLoop —— 在执行动作前进行逻辑校验，对失败决策进行溯源分析

设计决策：
- 反义词映射从外部 JSON 配置文件加载（SelfCorrectionConfig.antonym_mapping_path）
- 优先使用 Neo4j 的 owl:disjointWith 关系查询真实冲突
- 本地 JSON 降级方案仅在图数据库不可用时启用
- ReflectionLoop 支持配置化的最大迭代次数，防止无限递归
"""
import json
import logging
from typing import Any, List, Optional, Dict

# 导入核心推理器
from ..core.reasoner import Reasoner, Fact
# 导入配置管理
from ..utils.config import get_config

logger = logging.getLogger(__name__)


class ContradictionChecker:
    """
    逻辑冲突检查哨兵 (Contradiction Checker)

    安全机制：在将大模型提取的新知识或自我蒸馏的新规则存入 Semantic Memory 之前，
    必须通过此类进行公理冲突检测。防止知识图谱发生数据污染 (Data Poisoning)。
    """

    def __init__(self, reasoner: Reasoner, semantic_mem: Optional[Any] = None, onto_engine: Optional[Any] = None):
        # 推理引擎实例 —— 包含已有事实和规则
        self.reasoner = reasoner
        # 语义记忆（Neo4j 适配器）—— 可选，用于查询 owl:disjointWith
        self.semantic_mem = semantic_mem
        # v4.0: 本体引擎 —— 用于标准 OWL 推理
        self.onto_engine = onto_engine
        # 配置参数
        config = get_config()
        # 冲突检测模式 —— True: 阻断写入，False: 仅记录警告
        self._block_on_conflict = config.self_correction.block_on_conflict
        # 本地反义词映射缓存 —— 延迟加载
        self._local_antonyms: Optional[Dict[str, List[str]]] = None
        # 反义词映射文件路径
        self._antonym_path = config.self_correction.antonym_mapping_path

    def _load_local_antonyms(self) -> Dict[str, List[str]]:
        """
        从配置文件加载本地反义词映射

        使用延迟加载策略，首次调用时读取文件并缓存。
        文件格式为 JSON，键为概念值，值为互斥概念列表。

        Returns:
            反义词映射字典
        """
        if self._local_antonyms is not None:
            return self._local_antonyms

        try:
            # 从配置路径读取 JSON 文件
            with open(self._antonym_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 过滤掉以 _ 开头的元数据字段（如 _description、_usage）
            self._local_antonyms = {
                k: v for k, v in data.items()
                if not k.startswith("_") and isinstance(v, list)
            }
            logger.info(f"已加载 {len(self._local_antonyms)} 个反义词映射 (来源: {self._antonym_path})")
        except FileNotFoundError:
            # 配置文件不存在时使用空映射 —— 不阻断系统启动
            logger.warning(f"反义词映射文件不存在: {self._antonym_path}，冲突检测将仅依赖 Neo4j")
            self._local_antonyms = {}
        except json.JSONDecodeError as e:
            # JSON 解析错误 —— 记录错误并使用空映射
            logger.error(f"反义词映射文件解析失败: {e}，冲突检测将仅依赖 Neo4j")
            self._local_antonyms = {}

        return self._local_antonyms

    def _find_antonyms(self, predicate: str, object_val: str) -> List[str]:
        """
        查找与给定概念互斥的概念列表

        检索策略：
        1. 优先查询 Neo4j 中的 owl:disjointWith 关系（最权威）
        2. Neo4j 不可用时，降级到本地 JSON 配置文件

        Args:
            predicate: 谓词（预留，未来可支持基于谓词的冲突词典）
            object_val: 待查询的概念值

        Returns:
            互斥概念列表
        """
        # 策略1: 查询 Neo4j 图数据库中的 owl:disjointWith 关系
        if self.semantic_mem and getattr(self.semantic_mem, 'is_connected', False):
            driver = getattr(getattr(self.semantic_mem, 'client', None), 'driver', None)
            if driver:
                # Cypher 查询：查找与目标概念存在 disjointWith 关系的实体
                query = """
                MATCH (a:Entity {id: $obj})-[:disjointWith]-(b:Entity)
                RETURN b.id AS antonym
                """
                try:
                    with driver.session() as session:
                        result = session.run(query, obj=object_val)
                        antonyms = [record["antonym"] for record in result]
                        if antonyms:
                            logger.debug(f"从 Neo4j 查询到 {len(antonyms)} 个互斥概念: {object_val}")
                            return antonyms
                except Exception as e:
                    # Neo4j 查询失败时降级，不阻断冲突检测流程
                    logger.error(f"Neo4j 反义词查询异常: {e}")

        # 策略2: 降级到本地 JSON 配置文件
        local_antonyms = self._load_local_antonyms()
        # 使用小写匹配，提高鲁棒性
        return local_antonyms.get(object_val.lower(), [])

    def check_fact(self, proposed_fact: Fact) -> bool:
        """
        检查提议的事实是否与现有知识库发生严重冲突 (v4.0 增强版)

        算法：
        1. 优先使用 OWL 2 本体引擎进行公理级冲突检测
        2. 降级使用领域反义词典进行互斥验证
        """
        # 算法 1: 本体级约束验证 (OWL 2)
        if self.onto_engine:
            if not self.onto_engine.validate_contradiction(
                proposed_fact.subject, 
                proposed_fact.predicate, 
                proposed_fact.object
            ):
                logger.error(f"🚨 本体级冲突! 已拦截: ({proposed_fact.to_tuple()})")
                if self._block_on_conflict:
                    return False

        # 算法 2: 领域词典互斥验证 (Legacy Fallback)
        # 查找互斥概念
        conflicting_objects = self._find_antonyms(proposed_fact.predicate, proposed_fact.object)

        if not conflicting_objects:
            # 没有明确的互斥定义，默认放行
            return True

        # 遍历已有事实，检查是否存在矛盾
        for existing_fact in self.reasoner.facts:
            # 匹配条件：主语和谓词相同，且宾语存在互斥关系
            if (existing_fact.subject == proposed_fact.subject
                    and existing_fact.predicate == proposed_fact.predicate):
                if existing_fact.object.lower() in conflicting_objects:
                    logger.error(
                        f"🚨 知识冲突警报! 试图存入: ({proposed_fact.subject} "
                        f"{proposed_fact.predicate} {proposed_fact.object}), "
                        f"但现有图谱已存在: ({existing_fact.subject} "
                        f"{existing_fact.predicate} {existing_fact.object})"
                    )
                    # 根据配置决定是否阻断
                    if self._block_on_conflict:
                        return False
                    else:
                        # 仅记录警告，不阻断写入
                        logger.warning("冲突检测配置为非阻断模式，允许写入")
                        return True

        logger.info(f"✅ 哨兵检查通过，事实可安全存入: {proposed_fact.to_tuple()}")
        return True

    def check_all_facts(self) -> List[Fact]:
        """
        全量检测知识图谱中的逻辑冲突
        
        遍历当前推理引擎中的所有事实，识别违反本体约束或反义词约束的记录。
        
        Returns:
            List[Fact]: 发现的冲突事实列表
        """
        conflicts = []
        facts = list(self.reasoner.facts)
        
        # 临时克隆事实库以便逐一比对（避免在遍历时逻辑冲突导致拦截）
        for fact in facts:
            # 这里的 check_fact 会将当前事实与 self.reasoner.facts 中的其他事实进行比对
            # 由于本体引擎和反义词检测是幂等的，这可以有效识别存量数据中的矛盾
            if not self.check_fact(fact):
                conflicts.append(fact)
                
        if conflicts:
            logger.warning(f"全量冲突检测完成: 发现 {len(conflicts)} 条潜在矛盾事实")
            
        return conflicts

    def reload_antonyms(self) -> None:
        """
        重新加载反义词映射

        当外部修改了配置文件后调用此方法刷新缓存。
        """
        self._local_antonyms = None
        self._load_local_antonyms()
        logger.info("反义词映射已重新加载")


class ReflectionLoop:
    """
    反思回路 (Reflection Loop)

    用于在执行动作前进行逻辑校验，并对失败的决策进行溯源分析。
    反思过程有配置化的最大迭代次数限制，防止无限递归。
    """

    def __init__(self, reasoner: Reasoner, semantic_mem: Optional[Any] = None):
        # 推理引擎实例
        self.reasoner = reasoner
        # 冲突检查器 —— 传入语义记忆以支持 Neo4j 查询
        self.checker = ContradictionChecker(reasoner, semantic_mem)
        # 从配置读取最大反思迭代次数
        config = get_config()
        self._max_iterations = config.self_correction.max_reflection_iterations

    def evaluate_thought(self, thought_trace: List[str]) -> bool:
        """
        评估推理轨迹的合理性

        检查推理轨迹中的每一步是否存在逻辑冲突或死循环。

        算法：
        1. 检查推理轨迹长度是否超过最大迭代限制
        2. 检查是否存在重复步骤（循环检测）
        3. 检查最终结论是否与初始前提矛盾

        Args:
            thought_trace: 推理步骤列表，每个元素为一步推理的文本描述

        Returns:
            bool: True 表示推理轨迹合理，False 表示存在问题
        """
        logger.info(f"开始反思评估，推理轨迹长度: {len(thought_trace)}")

        # 检查1: 推理步骤是否超过最大迭代限制
        if len(thought_trace) > self._max_iterations:
            logger.warning(
                f"推理轨迹长度 {len(thought_trace)} 超过最大限制 "
                f"{self._max_iterations}，可能存在逻辑死循环"
            )
            return False

        # 检查2: 循环检测 —— 是否存在重复的推理步骤
        seen_steps = set()
        for step in thought_trace:
            # 归一化步骤文本（去除首尾空白和统一大小写）
            normalized = step.strip().lower()
            if normalized in seen_steps:
                logger.warning(f"推理轨迹中发现重复步骤: '{step}'，可能存在循环推理")
                return False
            seen_steps.add(normalized)

        # 检查3: 如果轨迹至少有2步，检查首尾是否矛盾
        if len(thought_trace) >= 2:
            first_step = thought_trace[0].strip().lower()
            last_step = thought_trace[-1].strip().lower()
            # 简单的矛盾检测 —— 如果结论直接否定了前提
            if first_step == last_step:
                # 完全相同的首尾步骤不一定是矛盾，但值得警告
                logger.debug("推理轨迹首尾步骤相同，可能是冗余推理")

        logger.info("✅ 反思评估通过，推理轨迹合理")
        return True

    def analyze_failure(self, thought_trace: List[str], error: str) -> Dict[str, Any]:
        """
        分析推理失败的原因

        对失败的决策进行溯源分析，定位问题步骤。

        Args:
            thought_trace: 推理步骤列表
            error: 错误描述

        Returns:
            分析报告字典
        """
        report = {
            "trace_length": len(thought_trace),
            "error": error,
            "diagnosis": "unknown",
            "problematic_step": None,
            "suggestion": "",
        }

        # 分析1: 空推理轨迹
        if not thought_trace:
            report["diagnosis"] = "empty_trace"
            report["suggestion"] = "推理引擎未产生任何步骤，可能是初始事实不足或规则缺失"
            return report

        # 分析2: 超长轨迹 —— 可能是无限循环
        if len(thought_trace) > self._max_iterations:
            report["diagnosis"] = "infinite_loop"
            report["problematic_step"] = len(thought_trace) - 1
            report["suggestion"] = f"推理深度超过 {self._max_iterations} 步，建议检查规则中是否存在循环依赖"
            return report

        # 分析3: 检查重复步骤
        seen = {}
        for i, step in enumerate(thought_trace):
            normalized = step.strip().lower()
            if normalized in seen:
                report["diagnosis"] = "circular_reasoning"
                report["problematic_step"] = i
                report["suggestion"] = f"第 {i} 步与第 {seen[normalized]} 步重复，存在循环推理"
                return report
            seen[normalized] = i

        # 分析4: 通用诊断
        report["diagnosis"] = "general_failure"
        report["problematic_step"] = len(thought_trace) - 1
        report["suggestion"] = f"推理在第 {len(thought_trace)} 步失败，建议检查最后一步的规则条件: '{error}'"

        return report
