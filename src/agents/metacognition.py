from .base import BaseAgent
from typing import Any, Dict, List, Optional
from ..utils.config import get_config
import logging
import re

logger = logging.getLogger(__name__)

class MetacognitiveAgent(BaseAgent):
    """
    Metacognitive Agent with self-assessment capabilities
    
    Implements:
    - Confidence calibration based on evidence quality
    - Knowledge boundary detection
    - Self-reflection with reasoning validation
    """
    
    # 从 ConfigManager 读取置信度阈值，避免硬编码
    _evolution_cfg = get_config().evolution
    CONFIDENCE_HIGH = _evolution_cfg.confidence_high
    CONFIDENCE_MEDIUM = _evolution_cfg.confidence_medium
    CONFIDENCE_LOW = _evolution_cfg.confidence_low
    
    async def reflect(self, thought: str, reasoning_steps: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Self-reflection: Validate reasoning against ontology logic
        
        Args:
            thought: The thought or conclusion to reflect upon
            reasoning_steps: The reasoning steps that led to this thought
            
        Returns:
            Reflection result with validity assessment
        """
        logger.info(f"{self.name} reflecting on: {thought[:100]}...")
        
        reflection_result = {
            "valid": True,        # 推理是否有效
            "confidence": 0.0,    # 推理置信度
            "issues": [],         # 发现的问题列表
            "suggestions": []     # 改进建议
        }
        
        # 检查推理链是否有充分的证据支撑
        if reasoning_steps:
            # 计算所有步骤的平均置信度
            total_confidence = sum(step.get("confidence", 0.5) for step in reasoning_steps)
            avg_confidence = total_confidence / len(reasoning_steps) if reasoning_steps else 0.0
            reflection_result["confidence"] = avg_confidence
            
            # 识别置信度低于中等阈值的步骤，标记为潜在问题
            low_confidence_steps = [
                i for i, step in enumerate(reasoning_steps) 
                if step.get("confidence", 1.0) < self.CONFIDENCE_MEDIUM
            ]
            
            if low_confidence_steps:
                reflection_result["issues"].append(
                    f"Low confidence in reasoning steps: {low_confidence_steps}"
                )
                reflection_result["suggestions"].append(
                    "Consider gathering more evidence for uncertain conclusions"
                )
        
        
        # Validate logical consistency
        if self._detect_contradictions(thought):
            reflection_result["valid"] = False
            reflection_result["issues"].append("Potential contradiction detected in reasoning")
        
        
        return reflection_result
    
    
    def _detect_contradictions(self, text: str) -> bool:
        """
        Simple contradiction detection
        In production, this would use the reasoner for logical validation
        """
        # Simple pattern-based contradiction detection
        contradiction_patterns = [
            r'is not.*is',
            r'cannot.*can',
            r'impossible.*possible',
            r'false.*true'
        ]
        
        for pattern in contradiction_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
        
    async def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute task loop: Think -> Reflect -> Act -> Learn
        
        Args:
            task: The task to execute
            context: Additional context for the task
            
        Returns:
            Execution result with confidence assessment
        """
        logger.info(f"Starting metacognitive task: {task[:100]}...")
        
        # Execute forward chain reasoning
        inference = self.reasoner.forward_chain(max_depth=5)
        explanation = self.reasoner.explain(inference)
        
        # Build structured reasoning steps
        steps = []
        for step in inference.conclusions:
            steps.append({
                "rule": step.rule.name,
                "premise": f"({step.matched_facts[0].subject} → {step.matched_facts[0].predicate} → {step.matched_facts[0].object})",
                "conclusion": f"({step.conclusion.subject} → {step.conclusion.predicate} → {step.conclusion.object})",
                "confidence": round(step.confidence.value, 4)
            })
        
        # Perform self-reflection
        reflection = await self.reflect(explanation, steps)
        
        # Assess knowledge boundary
        boundary_check = self.check_knowledge_boundary(task, inference.total_confidence.value)
        
        return {
            "status": "success",
            "result": explanation,
            "inference_steps": steps,
            "facts_used_count": len(inference.facts_used),
            "total_confidence": round(inference.total_confidence.value, 4),
            "reflection": reflection,
            "knowledge_boundary": boundary_check
        }
    
    
    def check_knowledge_boundary(self, query: str, confidence: float) -> Dict[str, Any]:
        """
        Check if the query is within the knowledge boundary
        
        Args:
            query: The user's query
            confidence: Current confidence level
            
        Returns:
            Boundary assessment with recommendations
        """
        boundary_result = {
            "within_boundary": True,
            "confidence_level": "high",
            "message": "",
            "recommendation": None
        }
        
        # 判定置信度层级，从高到低逐级判断
        if confidence >= self.CONFIDENCE_HIGH:
            # 高置信度：推理结果可信
            boundary_result["confidence_level"] = "high"
            boundary_result["message"] = "High confidence in the reasoning result"
        elif confidence >= self.CONFIDENCE_MEDIUM:
            # 中等置信度：建议验证关键事实
            boundary_result["confidence_level"] = "medium"
            boundary_result["message"] = "Moderate confidence - consider verifying critical facts"
        elif confidence > self.CONFIDENCE_LOW:
            # 低置信度：接近知识边界，建议咨询专家
            boundary_result["confidence_level"] = "low"
            boundary_result["message"] = "Low confidence - knowledge boundary approaching"
            boundary_result["recommendation"] = "Consider consulting external sources or human expert"
        else:
            # 极低置信度 (<= CONFIDENCE_LOW)：超出知识边界，无法给出可靠答案
            boundary_result["within_boundary"] = False
            boundary_result["confidence_level"] = "unknown"
            boundary_result["message"] = "Query appears to be outside knowledge boundary"
            boundary_result["recommendation"] = "Unable to provide reliable answer - please consult domain expert"
        
        
        return boundary_result
    
    
    def calibrate_confidence(self, evidence_count: int, evidence_quality: float = 0.8) -> float:
        """
        Calibrate confidence based on evidence quantity and quality
        
        Uses Bayesian-inspired calibration:
        - More evidence increases confidence
        - Lower quality evidence reduces confidence boost
        
        Args:
            evidence_count: Number of evidence pieces
            evidence_quality: Average quality of evidence (0-1)
            
        Returns:
            Calibrated confidence score
        """
        if evidence_count == 0:
            return 0.0  # 无证据时置信度为零
        
        # 证据数量缩放：超过 5 个证据后收益递减
        evidence_factor = min(evidence_count / 5.0, 1.0)
        
        # 证据质量调整：高质量证据提升置信度
        quality_factor = evidence_quality
        
        # 贝叶斯风格的置信度校准：保留基础不确定性
        base_uncertainty = 0.1  # 最小不确定性 10%
        calibrated = (evidence_factor * quality_factor * (1 - base_uncertainty)) + base_uncertainty
        
        return min(calibrated, 0.99)  # 封顶 0.99，保持谦逊原则
