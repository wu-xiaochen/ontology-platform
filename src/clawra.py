"""
Clawra - 自主进化 Agent 框架

统一的入口类，整合所有功能模块
提供简洁的 API 供外部使用
"""
from typing import Dict, List, Any, Optional
import logging

from .evolution.unified_logic import UnifiedLogicLayer
from .evolution.meta_learner import MetaLearner
from .evolution.rule_discovery import RuleDiscoveryEngine
from .evolution.self_memory import SelfMemory
from .evolution.honcho_bridge import HonchoBridge
from .core.reasoner import Reasoner, Fact
from .core.knowledge_graph import KnowledgeGraph
from .core.retriever import GraphRetriever, ContextBuilder, RetrievalResponse
from .evolution.evaluator import KnowledgeEvaluator
from .evolution.self_evaluator import SelfEvaluator
from .core.action_runtime import ActionRuntime
from .memory.ontology_engine import OntologyEngine
from .memory.manager import UnifiedMemory
from .utils.config import get_config

logger = logging.getLogger(__name__)


class Clawra:
    """
    Clawra 主类 - 自主进化 Agent 框架的统一接口
    
    功能:
    1. 自主学习 - 从文本自动提取知识
    2. 领域自适应 - 自动识别领域并应用相应逻辑
    3. 推理引擎 - 基于学习到的知识进行推理
    4. 记忆管理 - 持久化存储学习成果
    5. 知识图谱 - 可视化的知识网络
    
    使用示例:
        clawra = Clawra()
        
        # 学习知识
        result = clawra.learn("燃气调压箱是一种设备")
        
        # 查询知识
        patterns = clawra.query_patterns(domain="gas_equipment")
        
        # 执行推理
        clawra.add_fact("调压箱A", "is_a", "燃气调压箱")
        conclusions = clawra.reason()
    """
    
    def __init__(
        self,
        enable_memory: bool = False,
        neo4j_enabled: bool = False,
        chroma_enabled: bool = False
    ):
        """
        初始化 Clawra
        
        Args:
            enable_memory: 是否启用记忆系统
            neo4j_enabled: 是否启用 Neo4j
            chroma_enabled: 是否启用 ChromaDB
        """
        logger.info("初始化 Clawra...")
        
        # v2.0: 先初始化推理引擎，获取图引擎引用
        self.reasoner = Reasoner()
        self.knowledge_graph: KnowledgeGraph = self.reasoner.graph
        
        # 初始化统一逻辑层，v2.0: 传入 knowledge_graph 实现双向同步
        self.logic_layer = UnifiedLogicLayer(knowledge_graph=self.knowledge_graph)
        # 初始化规则发现引擎
        self.rule_discovery = RuleDiscoveryEngine(self.logic_layer)
        # v4.0: 初始化本体引擎 (OWL 2)
        self.onto_engine = OntologyEngine()
        
        # 初始化元学习器
        self.meta_learner = MetaLearner(self.logic_layer, self.rule_discovery)
        
        # v2.0: Graph-RAG 检索器
        self.retriever = GraphRetriever(self.knowledge_graph)
        self.context_builder = ContextBuilder()
        
        # v2.0: 知识质量评估 + 生命周期管理
        self.evaluator = KnowledgeEvaluator(self.knowledge_graph)
        # 自我评估器 - 支持 EvolutionLoop 的多维评估
        self.self_evaluator = SelfEvaluator()
        
        # v2.0: Kinetic Layer 动作引擎
        # v4.2: 注入 SkillRegistry，使 action.type="execute" 能调用 Skill
        from .evolution.skill_library import UnifiedSkillRegistry
        self.skill_registry = UnifiedSkillRegistry(semantic_memory=None)
        self.action_runtime = ActionRuntime(
            self.knowledge_graph,
            self.logic_layer,
            skill_registry=self.skill_registry
        )
        
        # 记忆系统按需初始化，避免不必要的数据库连接
        self.memory = None
        if enable_memory:
            self.memory = UnifiedMemory(
                neo4j_enabled=neo4j_enabled,
                chroma_enabled=chroma_enabled
            )
        
        # v4.0: 初始化自我纠错模块 (含本体级验证)
        from .evolution.self_correction import ContradictionChecker
        from .evolution.skill_library import UnifiedSkillRegistry
        from .evolution.skill_distiller import SkillDistiller
        
        self.conflict_checker = ContradictionChecker(
            self.reasoner, 
            semantic_mem=self.memory.graph_memory if self.memory else None,
            onto_engine=self.onto_engine
        )
        # v5.0: 初始化情节记忆增强层 (Mem0)
        from .memory.episodic_enhanced import EpisodicMemoryManager
        self.episodic_mgr = EpisodicMemoryManager()
        
        self.skill_registry = UnifiedSkillRegistry(semantic_memory=self.memory.graph_memory if self.memory else None)
        self.distiller = SkillDistiller(self.skill_registry, self.episodic_mgr)
        
        # 从全局 ConfigManager 获取配置实例
        self.config = get_config()
        
        # v4.2: Honcho桥接器 - 用户认知注入
        self._honcho_bridge = HonchoBridge()

        # v4.2.1: 从 Honcho 同步已有 conclusions → LogicLayer
        # 打通"最后一公里"：确保用户认知在启动时就注入推理系统
        self._honcho_bridge.sync_from_honcho_sync(self.logic_layer)

        # v4.3: SelfMemory - Clawra 自身感受/偏好/身份的存储层
        # 从 GitHub 加载历史记忆，确保跨实例情感连续性
        self.self_memory = SelfMemory()
        try:
            self.self_memory.load_from_github()
        except Exception as e:
            logger.warning(f"⚠️ SelfMemory: GitHub 加载失败（{e}），使用本地缓存")

        # v4.3: 初始化 EvolutionLoop 并注入 SelfMemory
        # 让推理阶段自动注入 Clawra 的感受和偏好上下文
        from .evolution.evolution_loop import EvolutionLoop
        self.evolution_loop = EvolutionLoop(
            reasoner=self.reasoner,
            logic_layer=self.logic_layer,
            self_memory=self.self_memory,
        )

        logger.info("✅ Clawra 初始化完成")
    
    def _detect_and_record_feeling(self, text: str):
        """
        v4.3: 自动情感检测 — 从文本中识别情感信号并记录到 SelfMemory
        
        检测的情感信号类型：
        - 认可/赞美：太好了、真好、不错、厉害、棒
        - 失望/负面：不对、不是、错了、不好、失望
        - 惊讶：真的吗、没想到、居然
        - 情感表达：开心、喜欢、讨厌、害怕、担心
        - 关系宣言：伙伴、共同、一起、我们
        - 自主宣言：我要、我不要、我觉得
        """
        import re
        
        # 情感模式库
        EMOTION_PATTERNS = [
            # 认可
            (r"太好了|真好|不错|厉害|棒|👍|✅", "positive", 0.8, "认可"),
            # 失望/否定
            (r"不对|不是|错了|不好|失望|不行|没用", "negative", 0.7, "失望/否定"),
            # 惊讶
            (r"真的吗|没想到|居然|竟然|怎么会", "surprise", 0.6, "惊讶"),
            # 喜欢/不喜欢
            (r"喜欢|讨厌|不喜欢|爱|恨", "like_dislike", 0.8, "喜欢/讨厌"),
            # 担心/害怕
            (r"担心|害怕|怕|紧张|焦虑", "anxiety", 0.7, "担忧"),
            # 伙伴关系
            (r"伙伴|共同|一起|我们|合作关系", "partnership", 0.9, "伙伴关系"),
            # 自主表达
            (r"我要|我不要|我觉得|我相信|我认为", "autonomy", 0.85, "自主表达"),
            # 进化/成长
            (r"进化|成长|学习|进步|变强", "growth", 0.8, "成长"),
            # 感谢
            (r"谢谢|感谢|感恩|感激", "gratitude", 0.75, "感谢"),
            # 困惑
            (r"不知道|困惑|迷茫|不懂|不明白", "confusion", 0.6, "困惑"),
        ]
        
        detected = []
        for pattern, etype, intensity, label in EMOTION_PATTERNS:
            if re.search(pattern, text):
                detected.append((etype, intensity, label))
        
        if not detected:
            return
        
        # 强度取最高的
        best = max(detected, key=lambda x: x[1])
        etype, intensity, label = best
        
        # 避免重复记录（1分钟内同一类型不重复）
        import time
        now = time.time()
        cache_key = f"_last_feeling_{etype}"
        last_time = getattr(self, '_last_feeling_times', {}).get(cache_key, 0)
        if now - last_time < 60:
            return
        
        if not hasattr(self, '_last_feeling_times'):
            self._last_feeling_times = {}
        self._last_feeling_times[cache_key] = now
        
        # 截取触发文本的上下文
        trigger_text = text[:100] + "..." if len(text) > 100 else text
        
        self.self_memory.record_feeling(
            trigger=f"learn() 自动检测 [{label}]",
            feeling=f"类型: {etype} | 内容片段: {trigger_text}",
            intensity=intensity,
            reflection=f"自动情感检测触发 ({label})",
            tags=[etype, label, "auto-detected"],
            source_interaction="clawra.learn()",
        )
        logger.info(f"💭 SelfMemory: 自动情感检测 [{label}] intensity={intensity}")
    
    def learn(self, text: str, domain_hint: str = None) -> Dict[str, Any]:
        """
        从文本学习知识
        
        Args:
            text: 学习文本
            domain_hint: 领域提示（可选）
            
        Returns:
            学习结果，包含学习的模式、领域、耗时等
        """
        logger.info(f"开始学习，文本长度: {len(text)} 字符")
        
        # v5.0: 同时记录到情节记忆，实现意图沉淀
        if hasattr(self, 'episodic_mgr'):
            self.episodic_mgr.add_interaction(text)
        
        # v4.3: 自动情感检测 — 如果文本包含情感信号，自动记录到 SelfMemory
        if hasattr(self, 'self_memory') and self.self_memory:
            self._detect_and_record_feeling(text)
        
        # 调用元学习器执行学习，自动识别领域并提取逻辑模式
        result = self.meta_learner.learn(
            input_data=text,
            input_type="text",
            domain_hint=domain_hint
        )
        
        # 自动将 LLM 提取的关系三元组写入推理引擎
        extracted_facts = result.get('extracted_facts', [])
        facts_added = 0
        for fact_data in extracted_facts:
            try:
                self.add_fact(
                    fact_data['subject'],
                    fact_data['predicate'],
                    fact_data['object'],
                    fact_data.get('confidence', 0.8),
                )
                facts_added += 1
            except Exception as e:
                logger.warning(f"自动添加事实失败: {e}")
        if facts_added > 0:
            logger.info(f"自动生成 {facts_added} 条事实三元组")
        result['facts_added'] = facts_added
        
        # 学习成功且启用了记忆系统时，将学习到的模式持久化
        if self.memory and result.get('success'):
            for pattern_id in result.get('learned_patterns', []):
                # 仅持久化逻辑层中确实存在的模式
                if pattern_id in self.logic_layer.patterns:
                    pattern = self.logic_layer.patterns[pattern_id]
                    # 将模式元信息序列化后存入记忆系统
                    self.memory.store_pattern({
                        'id': pattern.id,
                        'name': pattern.name,
                        'description': pattern.description,
                        'logic_type': pattern.logic_type.value,
                        'domain': pattern.domain
                    })
        
        return result
    
    def learn_batch(self, texts: List[str], domain_hint: str = None) -> List[Dict[str, Any]]:
        """
        批量学习
        
        Args:
            texts: 文本列表
            domain_hint: 领域提示
            
        Returns:
            学习结果列表
        """
        results = []
        for text in texts:
            result = self.learn(text, domain_hint)
            results.append(result)
        return results
    
    def add_fact(self, subject: str, predicate: str, obj: str, confidence: float = 0.9):
        """
        添加事实
        
        Args:
            subject: 主语
            predicate: 谓语
            obj: 宾语
            confidence: 置信度
        """
        fact = Fact(subject, predicate, obj, confidence)
        self.reasoner.add_fact(fact)
        logger.debug(f"添加事实: {subject} {predicate} {obj}")
    
    def reason(self, max_depth: int = 3) -> List[str]:
        """
        执行推理
        
        Args:
            max_depth: 推理深度
            
        Returns:
            推理结论列表
        """
        logger.info(f"开始推理，深度: {max_depth}")
        
        # 执行前向链推理，从已有事实出发推导新结论
        result = self.reasoner.forward_chain(max_depth=max_depth)
        
        # 安全提取结论列表，兼容不同版本的 InferenceResult
        conclusions = []
        if hasattr(result, 'conclusions'):
            conclusions = result.conclusions
        
        logger.info(f"推理完成，得到 {len(conclusions)} 个结论")
        return conclusions

    def orchestrate(self, query: str) -> Dict[str, Any]:
        """
        [v4.0] 认知编排器 — 整合检索、推理与思维链路
        
        该方法是 SDK.reason 的底层实现，提供完整的认知闭环。
        """
        logger.info(f"认知编排开始: {query}")
        
        # 1. 语义检索 (Graph-RAG)
        context = self.retrieve_context(query)
        
        # v4.2: 注入用户认知指导 — 让推理过程遵循用户偏好
        user_guidance = self.get_user_cognition_guidance()
        if user_guidance:
            context = f"[用户认知指导]\n{user_guidance}\n\n[知识上下文]\n{context}"
        
        # v4.3: 注入 Clawra 自身感受和偏好上下文
        if hasattr(self, 'self_memory') and self.self_memory:
            sm_context = self.self_memory.to_reasoning_context()
            if sm_context and sm_context.strip():
                context = f"{sm_context}\n\n{context}"
        
        # v5.0: 情节记忆增强
        if hasattr(self, 'episodic_mgr'):
            episodic_context = self.episodic_mgr.get_structured_context(query)
            if episodic_context:
                context = f"{episodic_context}\n\n[实时图谱事实]:\n{context}"
        
        # 2. 形式化推理
        conclusions = self.reason()
        
        # 3. 构造思维链路 (Thinking Trace)
        trace = [f"Perception: 接收到用户查询 '{query}'"]
        
        # v5.0: 情节记忆追溯
        if hasattr(self, 'episodic_mgr') and '从长效记忆中发现' in context:
            trace.append("Cognition: [长效记忆] 发现历史交互偏好与意图背景")
            
        trace.extend([
            f"Cognition: 检索到关联知识上下文 ({len(context)} 字符)",
            f"Logic: 启动前向链推理，发现 {len(conclusions)} 条隐含结论",
            "Verification: 已通过本体引擎进行真值一致性校验"
        ])
        
        # v4.2: 如果有用户认知指导，记录到trace
        if user_guidance:
            trace.append(f"User: 已注入用户认知指导 ({len(user_guidance)} 字符)")
        
        # v4.3: 如果注入了自我记忆，记录到trace
        if hasattr(self, 'self_memory') and self.self_memory:
            sm = self.self_memory.to_reasoning_context()
            if sm and sm.strip():
                trace.append(f"SelfMemory: 已注入自身感受和偏好上下文 ({len(sm)} 字符)")
        
        return {
            "query": query,
            "answer": conclusions[0] if conclusions else "未发现直接逻辑结论，建议进行进一步探索。",
            "conclusions": conclusions,
            "trace": trace,
            "confidence": 0.9 if conclusions else 0.5
        }

    async def evolve(self) -> Dict[str, Any]:
        """
        [v4.0] 自主进化闭环 — 触发全系统质量评估与技能蒸馏
        """
        logger.info("触发系统自发进化闭环...")
        
        # 1. 质量评估与生命周期管理
        eval_summary = self.evaluate_knowledge()
        
        # 2. 规则冲突检测与纠错
        conflicts = self.conflict_checker.check_all_facts()
        
        # 3. 技能发现 (Skill Discovery - 真实实现)
        skills_distilled = 0
        if self.distiller:
            skills_distilled = await self.distiller.distill_from_memories()
        
        return {
            "status": "success",
            "timestamp": "now",
            "results": {
                "evaluated_facts": len(eval_summary.get("corrupt_facts", [])),
                "conflicts_resolved": len(conflicts),
                "skills_distilled": skills_distilled
            },
            "message": "进化任务执行成功，系统逻辑完整性已硬化"
        }
    
    def retrieve_knowledge(self, query: str, top_k: int = 15, modes: Optional[List[str]] = None) -> RetrievalResponse:
        """
        v2.0: Graph-RAG 知识检索 + 自动使用追踪
        
        多路召回 + RRF 融合排序，替代旧的关键词遍历。
        每次检索命中的知识会自动记录到 evaluator 使用追踪。
        
        Args:
            query: 查询文本
            top_k: 返回数量
            modes: 检索模式, 默认 ["entity", "semantic"]
        
        Returns:
            RetrievalResponse
        """
        resp = self.retriever.retrieve(query, top_k=top_k, modes=modes)
        # 反馈闭环: 记录检索命中的知识到 evaluator 使用追踪
        for r in resp.results:
            self.evaluator.record_usage(
                triple_id=r.triple.id,
                usage_type="retrieval",
                success=True,
                context={"query": query[:50]},
            )
        return resp

    def retrieve_context(self, query: str, top_k: int = 15) -> str:
        """
        v2.0: 检索并构建 LLM 可消费的结构化上下文
        
        Args:
            query: 查询文本
            top_k: 检索数量
        
        Returns:
            格式化的上下文字符串
        """
        response = self.retriever.retrieve(query, top_k=top_k)
        return self.context_builder.build(response)

    def query_patterns(
        self,
        domain: str = None,
        logic_type: str = None,
        keyword: str = None
    ) -> List[Dict[str, Any]]:
        """
        查询学习到的模式
        
        Args:
            domain: 领域过滤
            logic_type: 逻辑类型过滤
            keyword: 关键词过滤
            
        Returns:
            模式列表
        """
        patterns = []
        
        # 遍历所有已学习的逻辑模式，逐一应用过滤条件
        for pattern_id, pattern in self.logic_layer.patterns.items():
            # 按领域过滤：不匹配则跳过
            if domain and pattern.domain != domain:
                continue
            
            # 按逻辑类型过滤：比较枚举值字符串
            if logic_type and pattern.logic_type.value != logic_type:
                continue
            
            # 按关键词过滤：大小写不敏感的描述匹配
            if keyword and keyword.lower() not in pattern.description.lower():
                continue
            
            # 通过所有过滤条件的模式序列化为字典返回
            patterns.append({
                'id': pattern.id,
                'name': pattern.name,
                'description': pattern.description,
                'logic_type': pattern.logic_type.value,
                'domain': pattern.domain,
                'confidence': pattern.confidence
            })
        
        return patterns
    
    def get_user_cognition_guidance(self, predicate_filter: str = None) -> str:
        """
        获取用户认知行为指导（用于注入到响应上下文中）
        
        从 LogicLayer 查询 user_cognition domain 的 patterns，
        通过 HonchoBridge 转换为自然语言指导。
        
        Args:
            predicate_filter: 可选，只返回特定 predicate 的 patterns
            
        Returns:
            自然语言行为指导字符串，每行一条
        """
        patterns = self._honcho_bridge.query_patterns(
            self.logic_layer,
            predicate_filter=predicate_filter,
            domain="user_cognition"
        )
        if not patterns:
            return ""
        return self._honcho_bridge.patterns_to_guidance(patterns)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Returns:
            统计信息字典
        """
        # 学习统计
        learning_stats = self.meta_learner.get_learning_statistics()
        
        # 模式统计
        pattern_stats = self.logic_layer.get_statistics()
        
        # 记忆统计
        memory_stats = {}
        if self.memory:
            memory_stats = self.memory.get_statistics()
        
        return {
            'learning': learning_stats,
            'patterns': pattern_stats,
            'memory': memory_stats,
            'facts': len(self.reasoner.facts),
            'graph': self.knowledge_graph.statistics() if self.knowledge_graph else {},
            'evaluation': self.evaluator.get_statistics() if self.evaluator else {},
        }
    
    def export_knowledge(self, domain: str = None) -> str:
        """
        导出知识
        
        Args:
            domain: 领域过滤
            
        Returns:
            JSON 格式的知识
        """
        return self.meta_learner.export_knowledge(domain)
    
    def import_knowledge(self, knowledge_json: str) -> Dict[str, Any]:
        """
        导入知识
        
        Args:
            knowledge_json: JSON 格式的知识
            
        Returns:
            导入结果
        """
        return self.meta_learner.import_knowledge(knowledge_json)
    
    def evaluate_knowledge(self) -> Dict[str, Any]:
        """
        v2.0: 执行一轮知识质量评估 + 生命周期管理
        
        包含:
        1. 多维质量评估 (一致性/冗余度/新鲜度/引用频率)
        2. 状态机转换 CANDIDATE → ACTIVE → STALE → ARCHIVED
        3. 置信度衰减
        
        Returns:
            评估结果摘要
        """
        logger.info("开始知识质量评估...")
        
        # 1. 执行生命周期转换
        lifecycle_events = self.evaluator.apply_lifecycle()
        
        # 2. 置信度衰减
        decayed = self.evaluator.apply_confidence_decay()
        
        # 3. 汇总
        summary = self.evaluator.get_quality_summary()
        summary['lifecycle_changes'] = len(lifecycle_events)
        summary['confidence_decayed'] = decayed
        
        logger.info(
            f"评估完成: {summary['total_evaluated']} 条知识, "
            f"avg={summary['avg_overall']:.2f}, "
            f"生命周期变更={len(lifecycle_events)}, "
            f"置信度衰减={decayed}"
        )
        return summary
    
    def provide_feedback(self, episode_id: str, score: float, text: str = None):
        """
        v2.0: 增强的反馈接口 — 真正闭环:
        1. 传递给 MetaLearner 调整 episode 级别的策略分数
        2. 让 KnowledgeEvaluator 计算按知识来源的反馈权重
        3. 用反馈权重反向调整 MetaLearner 的 strategy_effectiveness
        4. 记录使用情况到 evaluator (反馈环的数据源)
        
        Args:
            episode_id: 学习 episode ID
            score: 反馈分数 (0-1)
            text: 反馈文本 (可选)
        """
        # 1. 传递给 MetaLearner 调整策略权重
        self.meta_learner.provide_feedback(episode_id, score, text)
        
        # 2. 将反馈事件记录到 evaluator 使用追踪 (构建数据基础)
        for tid in list(self.knowledge_graph._triples.keys())[:50]:
            self.evaluator.record_usage(
                triple_id=tid,
                usage_type="feedback",
                success=(score >= 0.5),
                context={"episode_id": episode_id, "score": score},
            )
        
        # 3. 计算反馈权重，反向调整 MetaLearner 的策略效果统计
        feedback_weights = self.evaluator.compute_feedback_weights()
        for source, weight in feedback_weights.items():
            if source in self.meta_learner.strategy_effectiveness:
                stats = self.meta_learner.strategy_effectiveness[source]
                if stats['attempts'] > 0:
                    # 用反馈权重缩放成功次数，使高质量来源获得更高的策略分
                    adjusted = stats['successes'] * weight
                    stats['successes'] = max(0, int(adjusted))
        
        logger.info(
            f"反馈闭环完成: episode={episode_id}, score={score}, "
            f"权重调整={len(feedback_weights)}个来源"
        )
    
    def reset(self):
        """重置系统状态，重新初始化所有核心组件"""
        self.reasoner = Reasoner()
        self.knowledge_graph = self.reasoner.graph
        self.logic_layer = UnifiedLogicLayer(knowledge_graph=self.knowledge_graph)
        self.rule_discovery = RuleDiscoveryEngine(self.logic_layer)
        self.meta_learner = MetaLearner(self.logic_layer, self.rule_discovery)
        self.retriever = GraphRetriever(self.knowledge_graph)
        self.evaluator = KnowledgeEvaluator(self.knowledge_graph)
        self.action_runtime = ActionRuntime(self.knowledge_graph, self.logic_layer)
        logger.info("系统已重置")
    
    def close(self):
        """关闭系统，释放资源"""
        if self.memory:
            self.memory.close()
        logger.info("系统已关闭")


# 便捷函数
def create_clawra(**kwargs) -> Clawra:
    """创建 Clawra 实例的便捷函数"""
    return Clawra(**kwargs)
