"""ontology-platform - Agent Growth SDK with Metacognition"""

__version__ = "0.9.0-alpha"

# 从现有模块导入核心组件
from src.core.loader import OntologyLoader
from src.ontology.reasoner import OntologyReasoner
from src.eval.confidence import ConfidenceCalculator

__all__ = [
    "OntologyLoader",
    "OntologyReasoner", 
    "ConfidenceCalculator",
    "__version__",
]
