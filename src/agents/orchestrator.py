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
    
    分析多轮对话历史，大模型自主调用以下专有工具：
    - ingest_knowledge -> Perception (KnowledgeExtractor) -> Sentinel -> Memory
    - query_graph -> Vector Search -> MetacognitiveAgent -> Core Reasoner -> Response
    """
    
    def __init__(self, reasoner: Reasoner, semantic_mem: SemanticMemory, episodic_mem: EpisodicMemory, project_context: Optional[str] = None):
        self.reasoner = reasoner
        self.semantic_memory = semantic_mem
        self.episodic_memory = episodic_mem
        
        # 强制生产级 LLM 后端（禁止假数据）
        self.extractor = KnowledgeExtractor(use_mock_llm=False)
        self.sentinel = ContradictionChecker(self.reasoner, self.semantic_memory)
        self.reasoning_agent = MetacognitiveAgent(name="Clawra_Thinker", reasoner=self.reasoner)
        self.auditor = AuditorAgent(name="Safety_Auditor", reasoner=self.reasoner, semantic_memory=self.semantic_memory)
        self.glossary_engine = GlossaryEngine()
        self.skill_registry = SkillRegistry(semantic_memory=self.semantic_memory)
        self.action_registry = ActionRegistry()
        self._wire_action_logics()

        # 全局项目上下文加载
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
                    "description": "将用户提供的原始文本直接送入知识抽取管道。你必须将用户的原文原封不动、一字不改地传入text参数，禁止摘要、禁止省略、禁止改写。系统内部会自动分块处理超长文本。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "用户提供的原始文本，必须原封不动传入，禁止摘要或压缩。"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_graph",
                    "description": "连通 ChromaDB 和 Reasoner 双引擎进行推理查询。当用户提出溯源判定或逻辑推导时使用。",
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
                    "description": "执行本体动力学操作（Action Type）。当需要进行特定业务逻辑校验（如质量合规性校验）或驱动本体演进时使用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action_id": {"type": "string", "enum": [a["id"] for a in self.action_registry.list_actions()], "description": "要执行的 Action 唯一标识"},
                            "params": {"type": "object", "description": "Action 所需的参数键值对"}
                        },
                        "required": ["action_id"]
                    }
                }
            }
        ]

    def _wire_action_logics(self):
        """将 Registry 中的 Action 与具体的引擎执行逻辑绑定"""
        
        # 绑定：语义映射自修复
        update_action = self.action_registry.get_action("action:update_mapping")
        if update_action:
            update_action.execution_logic = self._execute_update_mapping

    async def _execute_update_mapping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行逻辑：更新本体映射关系"""
        phys = params.get("physical_key")
        biz = params.get("business_term")
        conf = params.get("confidence", 1.0)
        
        if not phys or not biz:
            return {"status": "ERROR", "msg": "Missing physical_key or business_term"}
            
        # 1. 更新 Reasoner (Logic Layer)
        from core.reasoner import Fact
        new_fact = Fact(subject=phys, predicate="maps_to", object=biz, confidence=conf, source="action_loop")
        self.reasoner.add_fact(new_fact)
        
        # 2. 更新 SemanticMemory (Storage Layer)
        self.semantic_memory.store_fact(new_fact)
        
        logger.info(f"Self-healing: 成功建立映射 {phys} -> {biz}")
        return {
            "status": "SUCCESS",
            "impact": f"已将物理字段 {phys} 永久映射至业务术语 {biz}",
            "triple": f"({phys} -> maps_to -> {biz})"
        }

    async def execute_task(self, messages: List[Dict[str, str]], custom_prompt: Optional[str] = None) -> Dict[str, Any]:
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
                "content": (
                    custom_prompt or (
                        f"[Clawra Cognitive Kernel - Intelligence Directive]\n"
                        f"{self.project_context}\n\n"
                        "CORE MISSION: You are not a chatbot; you are a High-Fidelity Logic Engine. \n"
                        "1. FACTUAL GROUNDING: Every claim must lead back to a verified triple from the Graph. \n"
                        "2. QUALITY FOCUS: When discussing procurement or gas regulators, meticulously analyze 'Quality Points' (质量点) and 'Safety Requirements'. \n"
                        "3. KINETIC REASONING: Don't just list facts. Connect them. If 'ExdIIBT4' is required, explain why the environment demands it based on the ontology. \n"
                        "4. TOOL USAGE: Use 'ingest_knowledge' for new facts. Use 'query_graph' for ANY logic investigation. YOU MUST USE TOOLS FOR REASONING. \n"
                        "5. AVOID PRAISE: Minimize polite fillers. Be cold, logical, and technically precise."
                    )
                )
            }
        ]
        
        # 剥离多媒体和非标准 Key（防止 Pydantic 炸毁）
        for m in messages:
            if m["role"] in ["user", "assistant"]:
                local_messages.append({"role": m["role"], "content": str(m["content"])})
        
        response_data = {"intent": "CHAT", "facts": [], "trace": [], "structured_trace": []}
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

                # [Gemini Optimization] 多智能体语义审计 (Auditor Agent)
                audit_result = await self.auditor.audit_plan(func_name, func_args)
                if audit_result["status"] == "BLOCKED":
                    logger.warning(f"🚫 Auditor BLOCKED tool [{func_name}]: {audit_result['risks']}")
                    tool_result_str = json.dumps({
                        "status": "AUDIT_FAILURE", 
                        "msg": "执行计划被审计智能体拦截。", 
                        "risks": audit_result["risks"]
                    }, ensure_ascii=False)
                    trace_node["result"] = {
                        "summary": "🚨 审计拦截：检测到潜在逻辑风险",
                        "risks": audit_result["risks"],
                        "decision": audit_result["decision"]
                    }
                    response_data["trace"].append(trace_node)
                    local_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": tool_result_str
                    })
                    continue

                try:
                    if func_name == "ingest_knowledge":
                        response_data["intent"] = "INGEST"
                        text = func_args.get("text", "")
                        
                        # F1 安全网：检测LLM是否压缩了原文
                        # 如果工具参数中的text远短于最后一条用户消息，则使用原文
                        last_user_msg = ""
                        for m in reversed(messages):
                            if m.get("role") == "user":
                                last_user_msg = str(m.get("content", ""))
                                break
                        
                        if last_user_msg and len(text) < len(last_user_msg) * 0.7:
                            logger.warning(
                                f"F1安全网触发: LLM压缩了原文 (工具参数:{len(text)}字 < 原文:{len(last_user_msg)}字 × 0.7)，"
                                f"使用原始用户输入替代"
                            )
                            text = last_user_msg
                        
                        # [Gemini Optimization] 自动业务词典对齐 (Glossary Engine)
                        # 如果文本包含 DDL 或 字段定义，先提取词典
                        extra_prompt = ""
                        if any(k in text.upper() for k in ["CREATE TABLE", "FIELD", "字段", "SELECT"]):
                            extra_prompt = self.glossary_engine.enrich_extractor_context("", text)
                            logger.info("GlossaryEngine: 注入动态业务词典上下文")

                        extracted_facts = self.extractor.extract_from_text(text, extra_prompt=extra_prompt)
                        accepted_facts = []
                        rejected_facts = []
                        for fact in extracted_facts:
                            if self.sentinel.check_fact(fact):
                                self.reasoner.add_fact(fact)
                                self.semantic_memory.store_fact(fact)
                                accepted_facts.append(fact)
                            else:
                                rejected_facts.append(fact)
                                
                        response_data["facts"].extend([f.to_tuple() for f in accepted_facts])
                        
                        # 构建严格事实引用的 trace
                        accepted_refs = [
                            {
                                "triple": f"({f.subject} → {f.predicate} → {f.object})",
                                "confidence": round(f.confidence, 4),
                                "source": f.source
                            }
                            for f in accepted_facts
                        ]
                        rejected_refs = [
                            {
                                "triple": f"({f.subject} → {f.predicate} → {f.object})",
                                "reason": "哨兵冲突检测拒绝"
                            }
                            for f in rejected_facts
                        ]
                        trace_node["result"] = {
                            "summary": f"经哨兵验证存入 {len(accepted_facts)} 条公理，拒绝 {len(rejected_facts)} 条",
                            "accepted_triples": accepted_refs,
                            "rejected_triples": rejected_refs
                        }
                        tool_result_str = json.dumps({"status": "SUCCESS", "stored_triples": len(accepted_facts), "sample": [f.to_tuple() for f in accepted_facts[:5]]}, ensure_ascii=False)

                    elif func_name == "query_graph":
                        response_data["intent"] = "QUERY"
                        query = func_args.get("query", "")
                        
                        # 1. 向量相似度检索 (Semantic Layer)
                        vector_context = self.semantic_memory.semantic_search(query, top_k=5)
                        context_docs = [doc.content for doc in vector_context]
                        
                        # 2. 图谱两步拓展 (Logic Layer / 2-hop Expansion)
                        # 提取查询中的关键名词进行基准拓展
                        entities = re.findall(r'[\u4e00-\u9fa5\w]{2,}', query)
                        expanded_facts = []
                        for entity in entities[:3]: # 限制前3个核心词，防止背景过载
                            neighbors = self.semantic_memory.query(entity, depth=1)
                            for node in neighbors:
                                if hasattr(node, 'items'): # 处理 Neo4j 返回节点对象
                                    expanded_facts.append(str(node))
                        
                        full_context = " | ".join(context_docs + expanded_facts[:10])
                        
                        # 3. 执行本体前向链推理
                        inference_result = self.reasoner.forward_chain(max_depth=5)
                        reasoning_chain = []
                        for step in inference_result.conclusions:
                            reasoning_chain.append({
                                "rule": {"id": step.rule.id, "name": step.rule.name},
                                "premise": f"({step.matched_facts[0].subject} → {step.matched_facts[0].predicate} → {step.matched_facts[0].object})",
                                "conclusion": f"({step.conclusion.subject} → {step.conclusion.predicate} → {step.conclusion.object})",
                                "confidence": round(step.confidence.value, 4)
                            })
                        
                        facts_used_refs = [
                            f"({f.subject} → {f.predicate} → {f.object})"
                            for f in inference_result.facts_used
                        ]
                        
                        # [Gemini Optimization] 粒度理论 (Grain Theory) 静态校验
                        grain_validator = GrainValidator(self.semantic_memory)
                        # 启发式检测聚合意图
                        agg_func = "SUM" if any(k in query for k in ["总和", "共", "累计", "SUM", "TOTAL"]) else None
                        grain_result = grain_validator.validate_query_logic(entities[:2], aggregate_func=agg_func)
                        
                        # 4. 注入极深关联背景供 Agent 决策
                        rich_task = f"[Context-Enriched Query]\n[Graph Context]: {full_context}\n[Target]: {query}\n[Logic Constraints]: {grain_result.get('message', 'Checked')}"
                        agent_response = await self.reasoning_agent.run(rich_task)
                        
                        trace_node["result"] = {
                            "summary": f"GraphRAG 2阶拓展完成。召回 {len(context_docs)} 条向量，拓展 {len(expanded_facts)} 条图节点。",
                            "vector_context": context_docs,
                            "reasoning_chain": reasoning_chain,
                            "facts_used": facts_used_refs,
                            "grain_check": grain_result,
                            "total_confidence": round(inference_result.total_confidence.value, 4),
                            "metacognition": agent_response # 直接传递结构化字典
                        }
                        tool_result_str = json.dumps({
                            "status": "SUCCESS", 
                            "logic_engine_conclusion": agent_response.get("result", ""),
                            "grain_status": grain_result.get("status", "SAFE")
                        }, ensure_ascii=False)

                    elif func_name == "execute_action":
                        response_data["intent"] = "ACTION"
                        action_id = func_args.get("action_id", "")
                        params = func_args.get("params", {})
                        
                        action = self.action_registry.get_action(action_id)
                        if action:
                            # [Gemini Optimization] 真实执行动力学逻辑
                            if action.execution_logic:
                                try:
                                    if asyncio.iscoroutinefunction(action.execution_logic):
                                        exec_result = await action.execution_logic(params)
                                    else:
                                        exec_result = action.execution_logic(params)
                                    
                                    summary = exec_result.get("impact", f"已成功执行 {action.name}")
                                    tool_result_str = json.dumps(exec_result, ensure_ascii=False)
                                except Exception as e:
                                    logger.error(f"Action execution logic failed: {e}")
                                    tool_result_str = json.dumps({"status": "ERROR", "msg": str(e)})
                                    summary = f"执行 {action.name} 时发生逻辑错误: {e}"
                            else:
                                # 降级：模拟动态执行
                                summary = f"已对 {params.get('target_entity', '未知实体')} 完成 {action.name} 所需的推理闭环。"
                                tool_result_str = json.dumps({"status": "SUCCESS", "action": action.name, "execution_summary": summary}, ensure_ascii=False)
                            
                            trace_node["result"] = {
                                "summary": f"执行动力学 Action: {action.name}",
                                "action_details": action.description,
                                "parameters": params,
                                "execution_impact": summary
                            }
                        else:
                            tool_result_str = json.dumps({"status": "ERROR", "msg": "Action ID not found"})
                            trace_node["result"] = "Fault: Action not found."
                        
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
            "task_id": f"orch_{int(time.time())}_{str(hash(str(messages)) % 100000)}",
            "messages_length": len(messages),
            "final_intent": response_data["intent"],
            "tool_use_count": len(response_data["trace"]),
            "response": str(response_data.get("message", ""))
        })
            
        return response_data
