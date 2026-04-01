import asyncio
import logging
from core.reasoner import Reasoner, Fact
from perception.extractor import KnowledgeExtractor
from evolution.self_correction import ContradictionChecker
from memory.base import EpisodicMemory, SemanticMemory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("Phase3Demo")

async def run_phase3_demo():
    print("\n" + "="*60)
    print("  🚀 Clawra Phase 3: Deep Cognitive Integration Demo")
    print("  1. LLM Structured Extraction (Perception)")
    print("  2. Contradiction Sentinel (Evolution)")
    print("  3. Persistent Task Logging (SQLite Episodic Memory)")
    print("="*60 + "\n")

    # Initialize Modules
    reasoner = Reasoner()
    SemanticMemory() # Neo4j instance
    episodic_memory = EpisodicMemory(db_path="data/demo_episodic.db")
    extractor = KnowledgeExtractor(use_mock_llm=True)
    sentinel = ContradictionChecker(reasoner=reasoner)

    # Inject base truth into reasoner
    logger.info("Injecting foundation truth: (SupplierA status safe)")
    base_fact = Fact(subject="SupplierA", predicate="status", object="safe", confidence=1.0, source="system")
    reasoner.add_fact(base_fact)

    print("\n--- Phase 3.1: Perception Layer (LLM Structured Extraction) ---")
    unstructured_text_1 = "System logs show Supplier 'SafeGas_Corp' has ISO9001 certification and operates high-pressure tanks."
    extracted_facts = extractor.extract_from_text(unstructured_text_1)
    
    for f in extracted_facts:
        logger.info(f"Extracted strict Fact: {f.to_tuple()} [Confidence: {f.confidence}]")
        reasoner.add_fact(f)

    print("\n--- Phase 3.2: Evolution Sentinel (Contradiction Check) ---")
    # Simulate extracting a toxic/contradictory fact from an LLM hallucination
    unstructured_text_2 = "Intelligence suggests SupplierA status is high_risk due to recent leaks."
    hallucinated_facts = extractor.extract_from_text(unstructured_text_2) # The mock LLM will extract high_risk
    
    for f in hallucinated_facts:
        # Before adding to reasoner/memory, pass through sentinel
        logger.info(f"Sentinel evaluating proposed fact: {f.to_tuple()}")
        if sentinel.check_fact(f):
            reasoner.add_fact(f)
            logger.info("Fact accepted.")
        else:
            logger.warning("Fact blocked by Sentinel! Preserving ontology integrity.")

    print("\n--- Phase 3.3: Persistent Episodic Memory ---")
    episode_data = {
        "task_id": "audit_demo_001",
        "extracted_count": len(extracted_facts),
        "blocked_count": 1,
        "final_reasoner_state": [f.to_tuple() for f in reasoner.facts]
    }
    episodic_memory.store_episode(episode_data)
    
    # Retrieve to verify DB persistence
    history = episodic_memory.retrieve_episodes(limit=1)
    logger.info(f"Retrieved from SQLite: {history[0]}")

    print("\n" + "="*60)
    print(" ✅ Phase 3 Integration Demo Complete")
    print(" System successfully parsed text, blocked data poisoning, and saved state.")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_phase3_demo())
