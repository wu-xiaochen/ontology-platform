import os
import json
import logging
import time
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

from core.reasoner import Reasoner
from memory.base import SemanticMemory, EpisodicMemory
from perception.extractor import KnowledgeExtractor
from evolution.self_correction import ContradictionChecker
from agents.metacognition import MetacognitiveAgent
from agents.auditor import AuditorAgent
from core.memory.skills import SkillRegistry
from perception.glossary_engine import GlossaryEngine
from core.ontology.actions import ActionRegistry, ActionType
from core.ontology.grain_validator import GrainValidator

class CognitiveOrchestrator:
    """
    Next-Gen Agentic Orchestrator (ReAct Tool-Calling Loop)
    """

    def __init__(self, reasoner: Reasoner, semantic_mem: SemanticMemory, episodic_mem: EpisodicMemory, project_context: Optional[str] = None):
        self.reasoner = reasoner
        self.semantic_memory = semantic_mem
        self.episodic_memory = episodic_mem
        
        self.extractor = KnowledgeExtractor(use_mock_llm=False)
        self.sentinel = ContradictionChecker(self.reasoner, self.semantic_memory)
        self.reasoning_agent = MetacognitiveAgent(name="Clawra_Thinker", reasoner=self.reasoner)
        self.auditor = AuditorAgent(name="Safety_Auditor", reasoner=self.reasoner, semantic_memory=self.semantic_memory)
        self.glossary_engine = GlossaryEngine()
        self.skill_registry = SkillRegistry(semantic_memory=self.semantic_memory)
        self.action_registry = ActionRegistry()
        self._wire_action_logics()

        self.project_context = project_context or self._load_project_context()

    def _load_project_context(self) -> str:
        cwd = os.getcwd()
        mem_path = os.path.join(cwd, "clawra.memory.md")
        if os.path.exists(mem_path):
            with open(mem_path, "r", encoding="utf-8") as f:
                return f.read()
        return "You are Clawra, an elite enterprise-grade cognitive agent. Please be polite and highly logical."

    def _get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "ingest_knowledge",
                    "description": "将用户提供的原始文本直接送入知识抽取管道。你必须将用户的原文原文原封不动、一字不改地传入text参数。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "用户提供的原始文本"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_graph",
                    "description": "连通 ChromaDB 和 Reasoner 双引擎进行推理查询。当用户提出溯源判定或逻辑推导时使用。YOU MUST USE THIS FOR QUESTIONS.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "查询目标关键词或问题"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_action",
                    "description": "执行本体动力学操作。当需要进行特定业务逻辑校验或驱动本体演进时使用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action_id": {"type": "string", "enum": [a["id"] for a in self.action_registry.list_actions()], "description": "Action ID"},
                            "params": {"type": "object", "description": "Action Params"}
                        },
                        "required": ["action_id"]
                    }
                }
            }
        ]

    def _wire_action_logics(self):
        update_action = self.action_registry.get_action("action:update_mapping")
        if update_action:
            update_action.execution_logic = self._execute_update_mapping

    async def _execute_update_mapping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        phys = params.get("physical_key")
        biz = params.get("business_term")
        conf = params.get("confidence", 1.0)
        
        if not phys or not biz:
            return {"status": "ERROR", "msg": "Missing fields"}
            
        from core.reasoner import Fact
        new_fact = Fact(subject=phys, predicate="maps_to", object=biz, confidence=conf, source="action_loop")
        self.reasoner.add_fact(new_fact)
        self.semantic_memory.store_fact(new_fact)
        
        return {
            "status": "SUCCESS",
            "impact": f"已将物理字段 {phys} 永久映射至业务术语 {biz}",
            "triple": f"({phys} -> maps_to -> {biz})"
        }

    async def execute_task(self, messages: List[Dict[str, str]], custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not api_key:
            return {"intent": "ERROR", "message": "⚠️ 缺少 API Key", "trace": []}

        client = OpenAI(api_key=api_key, base_url=base_url)
        
        local_messages = [
            {
                "role": "system", 
                "content": (
                    custom_prompt or (
                        f"[Clawra Cognitive Kernel]\n{self.project_context}\n\n"
                        "1. Use 'ingest_knowledge' for new data. 2. Use 'query_graph' for reasoning. YOU MUST USE TOOLS."
                    )
                )
            }
        ]
        
        for m in messages:
            if m["role"] in ["user", "assistant"]:
                local_messages.append({"role": m["role"], "content": str(m["content"])})
        
        response_data = {"intent": "CHAT", "trace": []}
        loop_counter = 0
        max_loops = 6

        while loop_counter < max_loops:
            loop_counter += 1
            completion = client.chat.completions.create(
                model=model,
                messages=local_messages,
                tools=self._get_tools(),
                temperature=0.1
            )
            
            response_message = completion.choices[0].message
            local_messages.append(response_message.model_dump(exclude_unset=True))
            
            if not response_message.tool_calls:
                response_data["message"] = response_message.content
                break
                
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                func_args_str = tool_call.function.arguments
                
                try:
                    func_args = json.loads(func_args_str)
                except json.JSONDecodeError:
                    func_args = {}
                    
                tool_start_time = time.time()
                trace_node = {"tool": func_name, "args": func_args, "result": ""}
                
                # 审计
                audit_result = await self.auditor.audit_plan(func_name, func_args)
                if audit_result["status"] == "BLOCKED":
                    tool_result_str = json.dumps({"status": "AUDIT_FAILURE", "risks": audit_result["risks"]}, ensure_ascii=False)
                    trace_node["result"] = {
                        "status": "BLOCKED",
                        "summary": "🚨 审计拦截：检测到潜在逻辑风险",
                        "risks": audit_result["risks"],
                        "decision": audit_result["decision"]
                    }
                    trace_node["latency"] = f"{(time.time() - tool_start_time):.2f}s"
                    response_data["trace"].append(trace_node)
                    local_messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": tool_result_str})
                    continue

                try:
                    if func_name == "ingest_knowledge":
                        response_data["intent"] = "INGEST"
                        text = func_args.get("text", "")
                        extracted_facts = self.extractor.extract_from_text(text)
                        accepted = []
                        for fact in extracted_facts:
                            if self.sentinel.check_fact(fact):
                                self.reasoner.add_fact(fact)
                                self.semantic_memory.store_fact(fact)
                                accepted.append(fact)
                        
                        trace_node["result"] = {
                            "status": "SUCCESS",
                            "summary": f"存入 {len(accepted)} 条公理",
                            "accepted_triples": [{"triple": f"({f.subject} → {f.predicate} → {f.object})"} for f in accepted]
                        }
                        tool_result_str = json.dumps({"status": "SUCCESS", "stored": len(accepted)})

                    elif func_name == "query_graph":
                        response_data["intent"] = "QUERY"
                        query = func_args.get("query", "")
                        vector_context = self.semantic_memory.semantic_search(query, top_k=5)
                        context_docs = [doc.content for doc in vector_context]
                        entities = re.findall(r'[\u4e00-\u9fa5\w]{2,}', query)
                        
                        inference_result = self.reasoner.forward_chain(max_depth=5)
                        agent_response = await self.reasoning_agent.run(f"Query: {query} \nContext: {' | '.join(context_docs)}")
                        
                        trace_node["result"] = {
                            "status": "SUCCESS",
                            "summary": "GraphRAG 推理完成",
                            "vector_context": context_docs,
                            "reasoning_chain": [{"conclusion": f"({s.conclusion.subject} → {s.conclusion.predicate} → {s.conclusion.object})"} for s in inference_result.conclusions],
                            "metacognition": agent_response
                        }
                        tool_result_str = json.dumps({"status": "SUCCESS", "conclusion": agent_response.get("result", "")})

                    elif func_name == "execute_action":
                        response_data["intent"] = "ACTION"
                        action_id = func_args.get("action_id", "")
                        exec_result = await self.action_registry.get_action(action_id).execution_logic(func_args.get("params", {}))
                        trace_node["result"] = {
                            "status": "SUCCESS",
                            "summary": f"执行 Action: {action_id}",
                            "impact": exec_result.get("impact", "")
                        }
                        tool_result_str = json.dumps(exec_result)

                    trace_node["latency"] = f"{(time.time() - tool_start_time):.2f}s"
                    response_data["trace"].append(trace_node)
                    local_messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": tool_result_str})

                except Exception as e:
                    logger.error(f"Tool error: {e}")
                    trace_node["result"] = {"status": "ERROR", "msg": str(e)}
                    trace_node["latency"] = f"{(time.time() - tool_start_time):.2f}s"
                    response_data["trace"].append(trace_node)
                    local_messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": json.dumps({"status": "ERROR", "msg": str(e)})})

        return response_data
