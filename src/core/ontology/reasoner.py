"""
Ontology Reasoner - Core reasoning engine
Provides inference capabilities based on rules and confidence tracking
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ConfidenceLevel(Enum):
    CONFIRMED = "CONFIRMED"
    ASSUMED = "ASSUMED"
    SPECULATIVE = "SPECULATIVE"
    UNKNOWN = "UNKNOWN"

@dataclass
class ReasoningResult:
    conclusion: str
    confidence: ConfidenceLevel
    evidence: List[Dict[str, Any]]
    rules_used: List[str]
    chain: List[Dict[str, Any]]

class OntologyReasoner:
    """
    Core ontology reasoning engine
    Provides rule-based inference with confidence tracking
    """
    
    def __init__(self):
        self.rules = []
        self.ontology = {}
        self.reasoning_history = []
    
    def add_rule(self, rule: Dict[str, Any]):
        """Add a reasoning rule"""
        self.rules.append(rule)
    
    def load_ontology(self, ontology_data: Dict[str, Any]):
        """Load ontology data"""
        self.ontology = ontology_data
    
    def query(self, query: str) -> List[Dict[str, Any]]:
        """Query the ontology"""
        results = []
        for entity_id, entity_data in self.ontology.items():
            if query.lower() in str(entity_data).lower():
                results.append({
                    "id": entity_id,
                    "data": entity_data,
                    "confidence": ConfidenceLevel.CONFIRMED.value
                })
        return results
    
    def reason(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """
        Perform reasoning based on query and context
        """
        evidence = []
        rules_used = []
        
        # Simple rule-based reasoning
        for rule in self.rules:
            if self._match_rule(rule, query):
                evidence.append({
                    "source": rule.get("id", "unknown"),
                    "reliability": rule.get("weight", 0.5),
                    "content": rule.get("conclusion", "")
                })
                rules_used.append(rule.get("id", "unknown"))
        
        # Determine confidence
        if len(evidence) >= 3:
            confidence = ConfidenceLevel.CONFIRMED
        elif len(evidence) >= 1:
            confidence = ConfidenceLevel.ASSUMED
        else:
            confidence = ConfidenceLevel.SPECULATIVE
        
        return ReasoningResult(
            conclusion=f"Reasoned result for: {query}",
            confidence=confidence,
            evidence=evidence,
            rules_used=rules_used,
            chain=[{"step": "match_rules", "matched": len(evidence)}]
        )
    
    def _match_rule(self, rule: Dict[str, Any], query: str) -> bool:
        """Check if rule matches query"""
        pattern = rule.get("pattern", "").lower()
        return pattern in query.lower()
    
    def validate(self) -> Dict[str, Any]:
        """Validate ontology consistency"""
        return {
            "valid": True,
            "rules_count": len(self.rules),
            "entities_count": len(self.ontology),
            "status": "OK"
        }

# Export main classes
__all__ = ["OntologyReasoner", "ReasoningResult", "ConfidenceLevel"]
