"""ontology-platform - Agent Growth SDK with Metacognition"""

__version__ = "0.9.0-alpha"

from ontology_platform.loader import OntologyLoader
from ontology_platform.reasoner import OntologyReasoner
from ontology_platform.confidence import ConfidenceEngine

__all__ = [
    "OntologyLoader",
    "OntologyReasoner", 
    "ConfidenceEngine",
    "__version__",
]
