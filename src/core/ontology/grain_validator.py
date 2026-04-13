import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GrainDefinition:
    entity: str
    grain_key: str  # e.g., 'order_id', 'user_id'
    cardinality: str # '1', 'N'

class GrainValidator:
    """
    粒度理论 (Grain Theory) 校验引擎 (V2 - Graph-Backed)
    
    不再依赖硬编码字典，而是动态从 SemanticMemory (Neo4j) 中下钻粒度定义。
    专门用于拦截 SQL/逻辑聚合中的 "Fan-trap" (扇形陷阱) 问题。
    """
    
    def __init__(self, semantic_memory: Any):
        self.semantic_memory = semantic_memory

    def validate_query_logic(self, entities_involved: List[str], aggregate_func: Optional[str] = None) -> Dict[str, Any]:
        """
        校验查询逻辑是否存在粒度不一致风险
        """
        if not aggregate_func:
            return {"status": "SAFE", "reason": "No aggregation detected"}
            
        risk_detected = False
        findings = []
        
        # 核心逻辑：从图谱动态获取每一类实体的粒度 (Grain)
        n_end_entities = []
        for entity in entities_involved:
            cardinality = self.semantic_memory.get_grain_cardinality(entity)
            if cardinality == "N":
                n_end_entities.append(entity)
        
        # 判定：如果在 1:N 关系链上直接对 '1' 端进行 'SUM' 等聚合，存在 Fan-trap 风险
        if len(n_end_entities) > 0 and aggregate_func.upper() in ["SUM", "AVG", "COUNT"]:
            risk_detected = True
            findings.append(f"检测到在 1:N 关系链中对 {entities_involved} 进行 {aggregate_func} 聚合，存在【扇形陷阱】风险。")
            
        if risk_detected:
            return {
                "status": "RISK",
                "risk_level": "CRITICAL",
                "message": "⚠️ 语义拦截：粒度冲突！",
                "details": findings,
                "suggestion": "请检查 SQL 中的 JOIN 逻辑，建议使用子查询预聚合或 DISTINCT 处理。"
            }
            
        return {"status": "SAFE", "reason": "Grain consistency verified"}

def check_fan_trap(query_entities: List[str], agg: str, semantic_memory: Any) -> bool:
    validator = GrainValidator(semantic_memory)
    result = validator.validate_query_logic(query_entities, agg)
    return result["status"] == "SAFE"
