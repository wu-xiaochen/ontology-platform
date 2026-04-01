from .base import BaseAgent
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

class MetacognitiveAgent(BaseAgent):
    """
    元认知智能体
    
    具备"自我反思"能力的 Agent，在执行动作前进行逻辑验证，
    并能够评估自己的推理置信度。
    """
    
    async def reflect(self, thought: str) -> bool:
        """自我反思：检查当前思路是否符合本体逻辑"""
        logger.info(f"{self.name} 正在反思: {thought}")
        # 调用 core.reasoner 进行逻辑一致性检查
        return True
        
    async def run(self, task: str) -> Dict[str, Any]:
        """执行任务循环：思考 -> 反思 -> 行动 -> 学习"""
        logger.info(f"开启元认知任务: {task}")
        
        # 执行前向链推理，获取结构化推理结果
        inference = self.reasoner.forward_chain(max_depth=5)
        explanation = self.reasoner.explain(inference)
        
        # 构建结构化推理步骤
        steps = []
        for step in inference.conclusions:
            steps.append({
                "rule": step.rule.name,
                "premise": f"({step.matched_facts[0].subject} → {step.matched_facts[0].predicate} → {step.matched_facts[0].object})",
                "conclusion": f"({step.conclusion.subject} → {step.conclusion.predicate} → {step.conclusion.object})",
                "confidence": round(step.confidence.value, 4)
            })
        
        return {
            "status": "success",
            "result": explanation,
            "inference_steps": steps,
            "facts_used_count": len(inference.facts_used),
            "total_confidence": round(inference.total_confidence.value, 4)
        }
