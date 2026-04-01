import logging
from typing import Dict, Any

from core.reasoner import Reasoner
from memory.base import SemanticMemory, EpisodicMemory
from perception.extractor import KnowledgeExtractor
from evolution.self_correction import ContradictionChecker
from agents.metacognition import MetacognitiveAgent

logger = logging.getLogger(__name__)

class CognitiveOrchestrator:
    """
    多智能体大脑中枢 (Multi-Agent Orchestrator)
    
    分析用户输入意图，将任务分发给不同的专门模块：
    - 领域知识录入 -> Perception (KnowledgeExtractor) -> Sentinel -> Memory
    - 逻辑推理请求 -> MetacognitiveAgent -> Core Reasoner -> Response
    """
    
    def __init__(self, reasoner: Reasoner, semantic_mem: SemanticMemory, episodic_mem: EpisodicMemory):
        self.reasoner = reasoner
        self.semantic_memory = semantic_mem
        self.episodic_memory = episodic_mem
        
        self.extractor = KnowledgeExtractor(use_mock_llm=True)
        self.sentinel = ContradictionChecker(self.reasoner)
        self.reasoning_agent = MetacognitiveAgent(name="Clawra_Thinker", reasoner=self.reasoner)

    def _determine_intent(self, text: str) -> str:
        """
        极简意图识别。真实企业环境应调用极小参数量 LLM (如 Llama3-8B) 或 BERT 进行 Intent Classification。
        """
        query_words = ["?", "what", "is", "how", "evaluate", "assess", "check", "查询", "是否", "怎么"]
        text_lower = text.lower()
        if any(qw in text_lower for qw in query_words) and not ("add" in text_lower or "录入" in text_lower):
            return "QUERY"
        return "INGEST"

    async def execute_task(self, user_input: str) -> Dict[str, Any]:
        """执行总调度"""
        logger.info(f"Orchestrator received task: {user_input[:50]}...")
        intent = self._determine_intent(user_input)
        
        response_data = {"intent": intent, "status": "success", "message": ""}
        
        if intent == "INGEST":
            logger.info("Routing to Perception Layer (Ingestion)...")
            extracted_facts = self.extractor.extract_from_text(user_input)
            accepted_facts = []
            
            for fact in extracted_facts:
                if self.sentinel.check_fact(fact):
                    self.reasoner.add_fact(fact)
                    self.semantic_memory.store_fact(fact)
                    accepted_facts.append(fact.to_tuple())
                else:
                    logger.warning(f"Fact blocked by Sentinel: {fact.to_tuple()}")
            
            response_data["message"] = f"Ingested {len(accepted_facts)} verified facts."
            response_data["facts"] = accepted_facts
            
        elif intent == "QUERY":
            logger.info("Routing to Metacognitive Agent (Reasoning)...")
            # 引入 Hybrid GraphRAG 构建上下文
            vector_context = self.semantic_memory.semantic_search(user_input, top_k=2)
            context_str = " | ".join([doc.content for doc in vector_context])
            
            logger.info(f"Retrieved GraphRAG Context: {context_str}")
            
            agent_response = await self.reasoning_agent.run(f"Context: {context_str}. Query: {user_input}")
            response_data["message"] = agent_response
        
        # 统一记录情理性经历
        self.episodic_memory.store_episode({
            "task_id": f"orch_{hash(user_input) % 10000}",
            "input": user_input,
            "intent": intent,
            "response": response_data["message"]
        })
        
        return response_data
