import logging
from typing import List, Dict, Any
from ..utils.config import get_config

logger = logging.getLogger(__name__)

class MemoryGovernor:
    """
    本体记忆治理引擎 (Ontology Memory Governance)
    
    企业级知识库会随着时间膨胀，产生相互冲突的陈旧条款。
    本模块负责实现类脑的“神经突触修剪 (Synaptic Pruning)”与“置信度衰减 (Confidence Decay)”。
    """
    def __init__(self, semantic_memory, reasoner):
        self.semantic_memory = semantic_memory
        self.reasoner = reasoner
        # 从 ConfigManager 读取记忆治理参数，避免硬编码
        _mem_cfg = get_config().memory
        self.decay_rate = _mem_cfg.decay_rate           # 每次衰减扣除的置信度
        self.reinforce_rate = _mem_cfg.reinforce_rate   # 每次强化增加的置信度
        self.prune_threshold = _mem_cfg.prune_threshold # 置信度低于此值将被遗忘 (剪枝)

    def reinforce_path(self, facts_used: List[Any]):
        """正向强化: 某条推理路径被成功采纳后，强化途径的神经元"""
        count = 0
        for fact in facts_used:
            # 修改内存中事实的置信度
            fact.confidence = min(1.0, fact.confidence + self.reinforce_rate)
            count += 1
        if count > 0:
            logger.info(f"[Governance] 强化了 {count} 个热频神经元路径。")

    def penalize_conflict(self, bad_facts: List[Any]):
        """负面惩罚: 某条路径导致了审计拦截或数学冲突"""
        count = 0
        for fact in bad_facts:
            fact.confidence = max(0.0, fact.confidence - self.decay_rate)
            count += 1
            if fact.confidence < self.prune_threshold:
                self._prune_fact(fact)
        if count > 0:
            logger.info(f"[Governance] 降权了 {count} 个冲突特征。")

    def _prune_fact(self, fact: Any):
        """神经元剪枝: 从运行时图谱中抹除该陈旧知识"""
        if fact in self.reasoner.facts:
            self.reasoner.facts.remove(fact)
            logger.warning(f"✂️ [Synaptic Pruning] 遗忘陈旧知识: ({fact.subject} -> {fact.predicate} -> {fact.object})")

    def run_garbage_collection(self) -> Dict[str, Any]:
        """定期运行垃圾回收，扫描并清除所有低迷节点"""
        initial_count = len(self.reasoner.facts)
        dead_neurons = [f for f in self.reasoner.facts if f.confidence < self.prune_threshold]
        
        for dead in dead_neurons:
            self._prune_fact(dead)
            
        return {
            "status": "SUCCESS",
            "metrics": {
                "initial_facts": initial_count,
                "pruned_facts": len(dead_neurons),
                "active_facts": len(self.reasoner.facts)
            }
        }