"""
Evolution Layer - 自主进化核心层

提供动态学习、自我进化、领域自适应能力
"""
from .meta_learner import MetaLearner
from .rule_discovery import RuleDiscoveryEngine
from .behavior_learner import BehaviorLearner
from .self_evaluator import SelfEvaluator
from .unified_logic import UnifiedLogicLayer
from .evolution_loop import (
    EvolutionLoop,
    EvolutionPhase,
    FailureType,
    FeedbackSignal,
    PhaseResult,
    EvolutionLoopState,
)
from .pattern_versioning import (
    PatternVersion,
    PatternHistory,
    PatternBranching,
    PatternRollback,
    SimilarityDeduplication,
)
from .episodic_memory import (
    EpisodicMemory,
    Episode,
    OutcomeType,
)
from .case_based_reasoner import (
    CaseBasedReasoner,
    Case,
    CaseBase,
    CaseOutcome,
    MetaStrategy,
    AdaptationResult,
)
from .honcho_bridge import (
    HonchoBridge,
    HonchoConclusion,
    CognitiveFact,
    conclusions_to_facts,
    create_bridge,
)

__all__ = [
    'MetaLearner',
    'RuleDiscoveryEngine',
    'BehaviorLearner',
    'SelfEvaluator',
    'UnifiedLogicLayer',
    'EvolutionLoop',
    'EvolutionPhase',
    'FailureType',
    'FeedbackSignal',
    'PhaseResult',
    'EvolutionLoopState',
    'PatternVersion',
    'PatternHistory',
    'PatternBranching',
    'PatternRollback',
    'SimilarityDeduplication',
    'EpisodicMemory',
    'Episode',
    'OutcomeType',
    'CaseBasedReasoner',
    'Case',
    'CaseBase',
    'CaseOutcome',
    'MetaStrategy',
    'AdaptationResult',
    'HonchoBridge',
    'HonchoConclusion',
    'CognitiveFact',
    'conclusions_to_facts',
]
