"""
Meta Learner - 元学习层

核心职责：
1. 学习如何学习（学习策略优化）
2. 领域自适应（自动识别领域并加载相关逻辑）
3. 学习效果评估与反馈
4. 知识蒸馏与迁移

改进:
- 添加结构化日志记录
- 完善错误处理和边界检查
"""
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
import json
import time
import logging

from ..utils.config import get_config
from .llm_extractor import LLMKnowledgeExtractor, ExtractionResult, BaseFallbackExtractor
from .skill_library import UnifiedSkillRegistry

# 类型检查导入，避免循环导入问题
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from evolution.unified_logic import LogicPattern
    from evolution.rule_discovery import RuleDiscoveryEngine

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class LearningEpisode:
    """
    学习过程记录
    
    记录单次学习会话的完整信息，用于后续分析和策略优化
    """
    episode_id: str
    timestamp: float
    domain: str
    input_type: str  # text, interaction, feedback
    input_data: Any
    learned_patterns: List[str]
    learning_time: float
    success: bool
    feedback_score: Optional[float] = None


class MetaLearner:
    """
    元学习器 - 系统的"学习中枢"
    
    实现功能：
    1. 领域识别与自适应
    2. 学习策略选择
    3. 学习效果追踪
    4. 跨领域知识迁移
    """
    
    def __init__(
        self,
        unified_logic_layer: Any,  # UnifiedLogicLayer 实例，用于模式管理
        rule_discovery_engine: Any  # RuleDiscoveryEngine 实例，用于从数据中发现规则
    ) -> None:
        """
        初始化元学习器
            
        Args:
            unified_logic_layer: 统一逻辑层实例，用于模式管理
            rule_discovery_engine: 规则发现引擎，用于从数据中发现规则
            
        """
        # 保存逻辑层引用，用于模式管理和检索
        self.logic_layer: Any = unified_logic_layer
        # 保存规则发现引擎引用，用于从结构化数据中发现规则
        self.discovery_engine: Any = rule_discovery_engine
            
        # ── LLM 依赖解耦：延迟初始化 ──
        # 不在 __init__ 中立即创建 LLM 客户端，避免启动时的外部依赖问题
        # _llm_extractor 在首次访问时才初始化
        self._llm_extractor: Optional[LLMKnowledgeExtractor] = None
        # fallback 提取器始终可用（不依赖 LLM），用于降级场景
        self._fallback_extractor: BaseFallbackExtractor = BaseFallbackExtractor()
        # 从配置读取 skip_llm 设置，支持完全离线模式
        self._skip_llm: bool = get_config().llm.skip_llm
            
        # 学习历史：记录所有学习会话，用于后续分析和策略优化
        self.episodes: List[LearningEpisode] = []
            
        # 领域模型：存储各领域的学习状态和模式索引
        self.domain_models: Dict[str, Dict[str, Any]] = {}
            
        # 学习策略效果统计：用于策略选择和优化
        self.strategy_effectiveness: Dict[str, Dict[str, Union[int, float]]] = defaultdict(lambda: {
            "attempts": 0,
            "successes": 0,
            "avg_learning_time": 0.0
        })
        
        # v5.0: 技能库集成
        self.skill_registry = UnifiedSkillRegistry()
    
        # 领域关键词库 - 用于自动领域识别
        # 涵盖系统支持的主要业务领域及其关键词
        self.domain_keywords: Dict[str, List[str]] = {
            "medical": ["患者", "诊断", "治疗", "症状", "药物", "patient", "diagnosis", "treatment"],
            "legal": ["合同", "违约", "赔偿", "法律", "条款", "contract", "breach", "liability"],
            "gas_equipment": ["燃气", "调压", "压力", "设备", "维护", "gas", "regulator", "pressure"],
            "finance": ["投资", "收益", "风险", "市场", "stock", "investment", "return", "risk"],
            "engineering": ["系统", "组件", "参数", "规格", "system", "component", "parameter"]
        }
        
    @property
    def llm_extractor(self) -> LLMKnowledgeExtractor:
        """
        获取 LLM 知识提取器（延迟初始化）
            
        首次访问时才创建 LLMKnowledgeExtractor 实例，
        这样可以避免在系统启动时就尝试连接 LLM 服务。
        """
        if self._llm_extractor is None:
            self._llm_extractor = LLMKnowledgeExtractor()
        return self._llm_extractor
        
    @property
    def is_llm_available(self) -> bool:
        """
        检查 LLM 服务是否可用
            
        返回 False 的情况：
        1. 用户设置了 SKIP_LLM=true（完全离线模式）
        2. LLM 客户端初始化失败
        3. LLM 连续调用失败次数超过阈值
            
        Returns:
            bool: LLM 是否可用于知识提取
        """
        # 如果用户明确禁用了 LLM，直接返回 False
        if self._skip_llm:
            return False
        # 检查 LLM 提取器的可用性
        return self.llm_extractor.is_available
    
    def detect_domain(self, text: str) -> Dict[str, float]:
        """
        自动检测文本所属领域
        
        基于关键词匹配计算各领域置信度分数，
        如果没有明显匹配则返回 generic 领域。
        
        Args:
            text: 待分析的文本
            
        Returns:
            {"domain": score, ...} 按置信度降序排列
        """
        text_lower = text.lower()
        scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            # 提高匹配权重，确保单关键词也能高置信度
            scores[domain] = min(matches / max(len(keywords) * 0.3, 1.0), 1.0)
        
        # 如果没有明显匹配，标记为generic
        if max(scores.values()) < 0.2:
            scores["generic"] = 0.8
        
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
    
    def clear_cache(self) -> None:
        """
        清除所有缓存数据
        
        在以下场景调用：
        1. 学习大量新模式后，释放内存
        2. 数据变更后，确保缓存一致性
        3. 测试场景，重置状态
        
        清除范围：
        - LLM 提取器缓存
        - Fallback 提取器缓存
        - 领域模型缓存（可选）
        """
        # 清除 LLM 提取器缓存（如果已初始化）
        if self._llm_extractor is not None:
            self._llm_extractor.clear_cache()
        
        # 清除 fallback 提取器缓存
        self._fallback_extractor.clear_cache()
        
        logger.info("MetaLearner 缓存已清除")
    
    def _invalidate_domain_cache(self, domain: str) -> None:
        """
        使指定领域的缓存失效
        
        当领域相关数据发生变更时调用，确保缓存一致性。
        
        Args:
            domain: 领域名称
        """
        if domain in self.domain_models:
            # 清除该领域的模式缓存，下次访问时重新加载
            self.domain_models[domain]["patterns"] = []
            logger.debug(f"领域 '{domain}' 的缓存已失效")
    
    def learn(
        self,
        input_data: Any,
        input_type: str = "text",
        domain_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行学习过程
        
        这是核心入口方法，实现完整的自主学习流程：
        1. 输入验证
        2. 领域识别
        3. 策略选择
        4. 执行学习
        5. 记录结果
        
        Args:
            input_data: 输入数据（文本、结构化数据或交互记录）
            input_type: 输入类型（"text", "structured", "interaction"）
            domain_hint: 可选的领域提示，用于跳过自动领域识别
            
        Returns:
            包含学习结果的字典，包括 episode_id、domain、learned_patterns 等
        """
        start_time = time.time()
        episode_id = f"ep_{int(start_time * 1000)}"
        
        # 输入验证
        if input_type == "text" and (not input_data or not str(input_data).strip()):
            logger.warning(f"[{episode_id}] 学习失败: 输入文本为空")
            return {
                "episode_id": episode_id,
                "domain": domain_hint or "generic",
                "strategy": "none",
                "learned_patterns": [],
                "learning_time": 0,
                "success": False,
                "error": "输入文本为空"
            }
        
        logger.info(f"[{episode_id}] 开始学习: type={input_type}, domain_hint={domain_hint}")
        
        # Step 1: 领域识别
        if not domain_hint and input_type == "text":
            domain_scores = self.detect_domain(input_data)
            domain = list(domain_scores.keys())[0]
            logger.info(f"[{episode_id}] 识别领域: {domain} (置信度: {domain_scores[domain]:.2f})")
        else:
            domain = domain_hint or "generic"
            logger.info(f"[{episode_id}] 使用指定领域: {domain}")
        
        # Step 2: 加载领域相关逻辑
        self._adapt_to_domain(domain)
        
        # Step 3: 选择学习策略
        strategy = self._select_learning_strategy(input_type, domain)
        logger.info(f"[{episode_id}] 选择策略: {strategy}")
        
        # Step 4: 执行学习
        learned_patterns = []
        success = False
        error_msg = None
        
        extracted_facts = []  # 自动生成的事实三元组
        
        try:
            if strategy == "llm_extraction":
                # 选择合适的提取器：LLM 优先，不可用时降级到 fallback
                if self.is_llm_available:
                    extraction = self.llm_extractor.extract(input_data, domain_hint=domain)
                    logger.info(f"[{episode_id}] 使用 LLM 提取器")
                else:
                    # LLM 不可用，使用 fallback 提取器（纯正则表达式，无外部依赖）
                    extraction = self._fallback_extractor.extract(input_data, domain_hint=domain)
                    logger.info(f"[{episode_id}] LLM 不可用，降级到 fallback 提取器")
                
                domain = extraction.domain or domain  # 提取器自动识别的领域
                
                # 1) 关系 -> 事实三元组 (由 Clawra SDK 写入 Reasoner)
                for rel in extraction.relations:
                    extracted_facts.append({
                        "subject": rel.subject,
                        "predicate": rel.predicate,
                        "object": rel.object,
                        "confidence": rel.confidence,
                    })
                
                # 2) 规则 -> LogicPattern (type=RULE)
                from .unified_logic import LogicPattern, LogicType
                for i, rule in enumerate(extraction.rules):
                    pattern = LogicPattern(
                        id=f"learned:llm_rule:{domain}:{episode_id}:{i}",
                        logic_type=LogicType.RULE,
                        name=f"规则: {rule.condition[:30]}",
                        description=f"如果 {rule.condition} 那么 {rule.action}",
                        conditions=[{"raw": rule.condition}],
                        actions=[{"type": "infer", "raw": rule.action}],
                        confidence=rule.confidence,
                        source="learned",
                        domain=domain,
                    )
                    self.logic_layer.add_pattern(pattern)
                    learned_patterns.append(pattern.id)
                
                # 3) 实体 -> LogicPattern (type=BEHAVIOR/定义)
                for i, entity in enumerate(extraction.entities):
                    desc = entity.description or entity.name
                    attr_str = ", ".join(f"{k}={v}" for k, v in entity.attributes.items())
                    if attr_str:
                        desc = f"{desc} ({attr_str})"
                    pattern = LogicPattern(
                        id=f"learned:llm_entity:{domain}:{episode_id}:{i}",
                        logic_type=LogicType.BEHAVIOR,
                        name=f"定义: {entity.name[:30]}",
                        description=f"{entity.name} [{entity.type}]: {desc[:100]}",
                        conditions=[{"subject": entity.name, "predicate": "exists", "object": "true"}],
                        actions=[{"type": "assign", "subject": entity.name, "predicate": "is_a", "object": entity.type}],
                        confidence=0.85,
                        source="learned",
                        domain=domain,
                    )
                    self.logic_layer.add_pattern(pattern)
                    learned_patterns.append(pattern.id)
                
                # 4) 正则补充提取 (捕获 LLM 可能遗漏的格式化内容)
                regex_patterns = self.logic_layer.extract_logic_from_text(input_data, domain)
                for rp in regex_patterns:
                    # 去重: 如果描述已经被 LLM 覆盖，跳过
                    if not any(rp.description[:20] in lp_id for lp_id in learned_patterns):
                        # 简单去重: 检查 name 是否类似
                        existing_names = {self.logic_layer.patterns[pid].name
                                          for pid in learned_patterns
                                          if pid in self.logic_layer.patterns}
                        if rp.name not in existing_names:
                            self.logic_layer.add_pattern(rp)
                            learned_patterns.append(rp.id)
                
                success = len(learned_patterns) > 0 or len(extracted_facts) > 0
                logger.info(
                    f"[{episode_id}] LLM 提取: {len(extraction.entities)} 实体, "
                    f"{len(extraction.relations)} 关系, {len(extraction.rules)} 规则, "
                    f"来源={extraction.source}"
                )
            
            elif strategy == "pattern_extraction":
                patterns = self.logic_layer.extract_logic_from_text(input_data, domain)
                logger.info(f"[{episode_id}] 提取到 {len(patterns)} 个模式")
                for pattern in patterns:
                    self.logic_layer.add_pattern(pattern)
                    logger.debug(f"[{episode_id}] 添加模式: {pattern.id}")
                    learned_patterns.append(pattern.id)
                success = len(patterns) > 0
            
            elif strategy == "rule_discovery":
                # 需要结构化数据
                if isinstance(input_data, list):
                    rules = self.discovery_engine.discover_from_facts(input_data)
                    for rule in rules:
                        # 转换为LogicPattern并添加
                        pattern = self._convert_rule_to_pattern(rule, domain)
                        self.logic_layer.add_pattern(pattern)
                        learned_patterns.append(pattern.id)
                    # 即使没有发现新规则，只要输入有效就算成功
                    success = len(input_data) > 0
            
            elif strategy == "interaction_learning":
                if isinstance(input_data, list):
                    rules = self.discovery_engine.discover_from_interactions(input_data)
                    for rule in rules:
                        pattern = self._convert_rule_to_pattern(rule, domain)
                        self.logic_layer.add_pattern(pattern)
                        learned_patterns.append(pattern.id)
                    success = len(rules) > 0
            
            # 更新策略效果统计
            self._update_strategy_stats(strategy, success, time.time() - start_time)
            
            # 如果学习成功且有新模式，使该领域的缓存失效以保持数据一致性
            if success and learned_patterns:
                self._invalidate_domain_cache(domain)
            
        except Exception as e:
            success = False
            error_msg = str(e)
            logger.error(f"[{episode_id}] 学习过程错误: {e}", exc_info=True)
        
        # 计算学习耗时
        learning_time = time.time() - start_time
        
        # 记录学习过程
        episode = LearningEpisode(
            episode_id=episode_id,
            timestamp=start_time,
            domain=domain,
            input_type=input_type,
            input_data=input_data if isinstance(input_data, str) else str(input_data)[:200],
            learned_patterns=learned_patterns,
            learning_time=learning_time,
            success=success
        )
        self.episodes.append(episode)
        
        # 记录结果日志
        if success:
            logger.info(f"[{episode_id}] 学习成功: 发现 {len(learned_patterns)} 个模式, 耗时 {learning_time:.3f}s")
        else:
            logger.warning(f"[{episode_id}] 学习失败: {error_msg or '未提取到有效模式'}, 耗时 {learning_time:.3f}s")
        
        result = {
            "episode_id": episode_id,
            "domain": domain,
            "strategy": strategy,
            "learned_patterns": learned_patterns,
            "extracted_facts": extracted_facts,
            "learning_time": episode.learning_time,
            "success": success
        }
        if error_msg:
            result["error"] = error_msg
        return result
    
    def _adapt_to_domain(self, domain: str) -> None:
        """
        根据领域自适应调整
        
        加载领域相关的已有逻辑模式，初始化领域模型。
        
        Args:
            domain: 目标领域名称
        """
        if domain not in self.domain_models:
            # 初始化领域模型
            self.domain_models[domain] = {
                "patterns": [],
                "keywords": self.domain_keywords.get(domain, []),
                "learned_count": 0
            }
        
        # 加载领域相关的已有逻辑
        domain_patterns = self.logic_layer.get_patterns_by_domain(domain)
        self.domain_models[domain]["patterns"] = [p.id for p in domain_patterns]
    
    def _select_learning_strategy(self, input_type: str, domain: str) -> str:
        """
        根据输入类型和领域选择最佳学习策略
        
        基于历史成功率选择效果最好的策略，
        优先使用 LLM 提取（如果可用）。
        
        Args:
            input_type: 输入数据类型
            domain: 目标领域
            
        Returns:
            选定的策略名称
        """
        if input_type == "text":
            # LLM 提取优先，可用时始终使用
            # 使用 is_llm_available 属性（已考虑 skip_llm 配置和 LLM 连接状态）
            if self.is_llm_available:
                return "llm_extraction"
            # LLM 不可用时 fallback 到正则
            strategies = ["pattern_extraction", "rule_discovery"]
        elif input_type == "structured":
            strategies = ["rule_discovery", "pattern_extraction"]
        elif input_type == "interaction":
            strategies = ["interaction_learning"]
        else:
            strategies = ["pattern_extraction"]
        
        # 选择效果最好的策略
        best_strategy = strategies[0]
        best_score = 0
        
        for strategy in strategies:
            stats = self.strategy_effectiveness[strategy]
            if stats["attempts"] > 0:
                score = stats["successes"] / stats["attempts"]
                if score > best_score:
                    best_score = score
                    best_strategy = strategy
        
        return best_strategy
    
    def _update_strategy_stats(self, strategy: str, success: bool, learning_time: float) -> None:
        """
        更新策略效果统计
        
        记录策略使用次数、成功次数和平均学习耗时，
        用于后续策略选择优化。
        
        Args:
            strategy: 策略名称
            success: 学习是否成功
            learning_time: 学习耗时（秒）
        """
        stats = self.strategy_effectiveness[strategy]
        stats["attempts"] += 1
        if success:
            stats["successes"] += 1
        
        # 更新平均学习时间
        old_avg = stats["avg_learning_time"]
        stats["avg_learning_time"] = (old_avg * (stats["attempts"] - 1) + learning_time) / stats["attempts"]
    
    def _convert_rule_to_pattern(self, rule: Dict[str, Any], domain: str) -> Any:
        """
        将发现的规则转换为 LogicPattern
        
        根据规则类型映射到对应的逻辑类型，
        构建完整的 LogicPattern 对象。
        
        Args:
            rule: 规则字典
            domain: 所属领域
            
        Returns:
            LogicPattern 对象
        """
        from .unified_logic import LogicPattern, LogicType
        
        type_mapping = {
            "transitive": LogicType.RULE,
            "classification": LogicType.RULE,
            "inheritance": LogicType.RULE,
            "policy": LogicType.POLICY,
            "constraint": LogicType.CONSTRAINT
        }
        
        return LogicPattern(
            id=rule["id"],
            logic_type=type_mapping.get(rule["type"], LogicType.RULE),
            name=rule["name"],
            description=rule["description"],
            conditions=rule["conditions"],
            actions=rule["actions"],
            confidence=rule.get("confidence", 0.7),
            source="discovered",
            domain=domain
        )
    
    def provide_feedback(
        self,
        episode_id: str,
        feedback_score: float,
        feedback_text: Optional[str] = None
    ) -> None:
        """
        接收学习反馈，用于改进学习策略
        
        根据反馈分数调整策略权重，低分反馈会降低对应策略的优先级。
        
        Args:
            episode_id: 学习会话 ID
            feedback_score: 0-1，越高表示学习效果越好
            feedback_text: 可选的文本反馈
        """
        for episode in self.episodes:
            if episode.episode_id == episode_id:
                episode.feedback_score = feedback_score
                
                # 根据反馈调整策略权重
                if feedback_score < 0.5:
                    # 学习效果差，降低该策略权重
                    strategy = self._select_learning_strategy(episode.input_type, episode.domain)
                    self.strategy_effectiveness[strategy]["successes"] = max(0, 
                        self.strategy_effectiveness[strategy]["successes"] - 1)
                
                break
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """
        获取学习统计信息
        
        汇总学习历史、成功率、领域分布和策略效果。
        
        Returns:
            包含各项统计指标的字典
        """
        total_episodes = len(self.episodes)
        successful_episodes = len([e for e in self.episodes if e.success])
        
        domain_distribution = defaultdict(int)
        for episode in self.episodes:
            domain_distribution[episode.domain] += 1
        
        return {
            "total_episodes": total_episodes,
            "success_rate": successful_episodes / total_episodes if total_episodes > 0 else 0,
            "domain_distribution": dict(domain_distribution),
            "strategy_effectiveness": dict(self.strategy_effectiveness),
            "avg_learning_time": sum(e.learning_time for e in self.episodes) / total_episodes if total_episodes > 0 else 0
        }
    
    def export_knowledge(self, domain: Optional[str] = None) -> str:
        """
        导出学习到的知识
        
        将指定领域或全部领域的模式导出为 JSON 字符串。
        
        Args:
            domain: 可选的领域过滤，为 None 时导出所有领域
            
        Returns:
            JSON 格式的知识导出字符串
        """
        if domain:
            patterns = self.logic_layer.get_patterns_by_domain(domain)
        else:
            patterns = list(self.logic_layer.patterns.values())
        
        export_data = {
            "patterns": [p.to_dict() for p in patterns],
            "statistics": self.get_learning_statistics(),
            "export_time": time.time()
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def import_knowledge(self, knowledge_json: str) -> Dict[str, Any]:
        """
        导入外部知识
        
        从 JSON 字符串解析并导入模式到逻辑层。
        
        Args:
            knowledge_json: JSON 格式的知识字符串
            
        Returns:
            包含导入结果的字典（success, imported_count 或 error）
        """
        try:
            data = json.loads(knowledge_json)
            patterns_data = data.get("patterns", [])
            
            imported = 0
            for p_data in patterns_data:
                from .unified_logic import LogicPattern
                pattern = LogicPattern.from_dict(p_data)
                self.logic_layer.add_pattern(pattern)
                imported += 1
            
            return {"success": True, "imported": imported}
        except Exception as e:
            return {"success": False, "error": str(e)}
    def distill_skill(self, task_name: str, successful_trace: List[str], generated_code: str):
        """
        [v5.0] 将成功轨迹蒸馏为技能
        
        基于成功的推理路径和生成的代码片段，将其收录进技能库。
        
        Args:
            task_name: 任务名称
            successful_trace: 成功的推理步骤描述列表
            generated_code: 对应的 Python 实现代码
        """
        description = f"Autonomous skill for task: {task_name}. Distilled from successful reasoning path."
        return self.skill_registry.add_skill(task_name, generated_code, description)
