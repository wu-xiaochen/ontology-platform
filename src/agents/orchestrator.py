import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

from core.reasoner import Reasoner, Fact
from memory.base import SemanticMemory, EpisodicMemory
from perception.extractor import KnowledgeExtractor
from evolution.self_correction import ContradictionChecker
from agents.agent import MetacognitiveAgent

class CognitiveOrchestrator:
    """
    Next-Gen Agentic Orchestrator (ReAct Tool-Calling Loop)
    
    分析多轮对话历史，大模型自主调用以下专有工具：
    - ingest_knowledge -> Perception (KnowledgeExtractor) -> Sentinel -> Memory
    - query_graph -> Vector Search -> MetacognitiveAgent -> Core Reasoner -> Response
    """
    
    def __init__(self, reasoner: Reasoner, semantic_mem: SemanticMemory, episodic_mem: EpisodicMemory):
        self.reasoner = reasoner
        self.semantic_memory = semantic_mem
        self.episodic_memory = episodic_mem
        
        # 强制生产级 LLM 后端（禁止假数据）
        self.extractor = KnowledgeExtractor(use_mock_llm=False)
        self.sentinel = ContradictionChecker(self.reasoner, self.semantic_memory)
        self.reasoning_agent = MetacognitiveAgent(name="Clawra_Thinker", reasoner=self.reasoner)

        # 全局项目上下文加载（类似 claude.md）
        self.project_context = self._load_project_context()

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
                    "description": "严格用于抽取事实逻辑。调用感知层(Perception)将用户输入的业务文本剥离为三元组，送入进化哨兵(Sentinel)验证防冲突，最后永久钉入Neo4j图谱。当用户传授经验、定义新规时调用此武器。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "需要解构入库的陈述句片段。"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_graph",
                    "description": "严格用于逻辑推理与追查。连通 ChromaDB 和 Reasoner 双引擎进行高维跨步推导（传递性/对称性等事实发酵）。当用户提出严谨审查、溯源判定或逻辑深究时触发此核按钮。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "高度概括的目标追问词条"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    async def execute_task(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """执行基于 Tool-Calling 的无极状态机大循环"""
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not api_key:
            return {"intent": "ERROR", "message": "⚠️ 认知中枢因缺失 OPENAI_API_KEY 而遭受物理级熔断！", "trace": []}

        client = OpenAI(api_key=api_key, base_url=base_url)
        
        # 1. 安全隔离组装 Context
        local_messages = [
            {
                "role": "system", 
                "content": f"[System Core Instruct]\n{self.project_context}\n[Important] You have access to ontology-modifying tools. Use 'ingest_knowledge' strictly for memorizing facts. Use 'query_graph' strictly for logical tracedowns. For casual chat, DO NOT use any tools, reply directly."
            }
        ]
        
        # 剥离多媒体和非标准 Key（防止 Pydantic 炸毁）
        for m in messages:
            if m["role"] in ["user", "assistant"]:
                local_messages.append({"role": m["role"], "content": str(m["content"])})
        
        response_data = {"intent": "CHAT", "facts": [], "trace": []}
        loop_counter = 0
        max_loops = 6 # 极限多轮对话熔断深度（模仿 Claude Code）

        while loop_counter < max_loops:
            loop_counter += 1
            logger.info(f"Orchestrator LLM Request (Agent Loop -> {loop_counter}/{max_loops})")
            
            completion = client.chat.completions.create(
                model=model,
                messages=local_messages,
                tools=self._get_tools(),
                temperature=0.1 # 压低温度，确保调用行为极致稳定不发疯
            )
            
            response_message = completion.choices[0].message
            # Append model reasoning to history
            local_messages.append(response_message.model_dump(exclude_unset=True))
            
            if not response_message.tool_calls:
                # 没有任何 Tool Calls，模型认为思考与行动已完结，直接抛出内容作为最终回响
                response_data["message"] = response_message.content
                break
                
            # 执行 Tool Chains (The 'Act' phase of ReAct)
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                func_args_str = tool_call.function.arguments
                
                try:
                    func_args = json.loads(func_args_str)
                except json.JSONDecodeError:
                    func_args = {}
                    
                tool_result_str = ""
                trace_node = {"tool": func_name, "args": func_args, "result": ""}
                
                logger.info(f"🔨 Agent triggered tool: [{func_name}] with {func_args}")

                try:
                    if func_name == "ingest_knowledge":
                        response_data["intent"] = "INGEST"
                        text = func_args.get("text", "")
                        extracted_facts = self.extractor.extract_from_text(text)
                        accepted_facts = []
                        for fact in extracted_facts:
                            # 动态图谱防爆验证
                            if self.sentinel.check_fact(fact):
                                self.reasoner.add_fact(fact)
                                self.semantic_memory.store_fact(fact)
                                accepted_facts.append(fact.to_tuple())
                                
                        response_data["facts"].extend(accepted_facts)
                        tool_result_str = json.dumps({"status": "SUCCESS", "stored_triples": accepted_facts}, ensure_ascii=False)
                        trace_node["result"] = f"Ingested {len(accepted_facts)} verified axioms."

                    elif func_name == "query_graph":
                        response_data["intent"] = "QUERY"
                        query = func_args.get("query", "")
                        # 融合 Chroma 和 Reasoner
                        vector_context = self.semantic_memory.semantic_search(query, top_k=3)
                        context_str = " | ".join([doc.content for doc in vector_context])
                        
                        agent_response = await self.reasoning_agent.run(f"[Hybrid GraphRAG Context: {context_str}] Target Query: {query}")
                        tool_result_str = json.dumps({"status": "SUCCESS", "logic_engine_conclusion": agent_response}, ensure_ascii=False)
                        trace_node["result"] = "Deep reasoning generated."
                        
                    else:
                        tool_result_str = json.dumps({"status": "ERROR", "msg": f"Unrecognized Tool {func_name}"})
                        trace_node["result"] = "Crash: Missing tool module."
                        
                except Exception as e:
                    logger.error(f"Tool execution catastrophic failure: {e}")
                    tool_result_str = json.dumps({"status": "SYSTEM_FAULT", "traceback": str(e)})
                    trace_node["result"] = f"Fault: {str(e)}"

                # 把物理执行层的客观结果强行塞回给 Agent 脑部，供其开启下一次 Loop 反刍
                local_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": tool_result_str
                })
                response_data["trace"].append(trace_node)

        # 兜底：强行打断无解死循环
        if loop_counter >= max_loops:
            logger.warning("🚨 Orchestrator hit absolute Max Recursion Limit.")
            response_data["message"] = "🧠 (极危断路器熔断：由于图谱环境过于深层，神经枢纽提前被物理切断，以防资源枯竭。)"

        # 落基岩：写入人类反馈和情景记忆，以便未来重放
        self.episodic_memory.store_episode({
            "task_id": f"orch_{str(hash(str(messages)) % 100000)}",
            "messages_length": len(messages),
            "final_intent": response_data["intent"],
            "tool_use_count": len(response_data["trace"]),
            "response": response_data["message"]
        })
            
        return response_data
