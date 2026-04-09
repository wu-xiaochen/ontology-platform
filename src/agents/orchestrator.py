import os
import json
import logging
import time
import re
import asyncio
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

# 延迟导入核心模块，避免循环导入问题
# orchestrator 和 reasoner 之间存在潜在的循环导入风险
# 因为 reasoner 可能会通过其他模块间接引用 orchestrator
# 使用局部导入确保在方法执行时才加载模块，打破循环
from ..utils.config import get_config

# 类型检查导入（TYPE_CHECKING 模式下不会实际执行导入）
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..core.reasoner import Reasoner, Fact
    from ..memory.base import SemanticMemory, EpisodicMemory

# 延迟导入：这些模块在 __init__ 中才实际使用
# 避免模块加载时的循环依赖问题
def _get_reasoner():
    from ..core.reasoner import Reasoner
    return Reasoner

def _get_fact():
    from ..core.reasoner import Fact
    return Fact

def _get_semantic_memory():
    from ..memory.base import SemanticMemory
    return SemanticMemory

def _get_episodic_memory():
    from ..memory.base import EpisodicMemory
    return EpisodicMemory

# 在类定义后导入其他依赖
# 这些导入放在文件底部或使用局部导入

# 保持向后兼容 - CognitiveOrchestrator 是 Orchestrator 的别名
# 实际的 Orchestrator 类定义在下面

class Orchestrator:
    """
    Next-Gen Agentic Orchestrator (ReAct Tool-Calling Loop)
    """

    def __init__(
        self,
        reasoner: Any,  # 使用 Any 避免循环导入，实际为 Reasoner
        semantic_mem: Any,  # 实际为 SemanticMemory
        episodic_mem: Any,  # 实际为 EpisodicMemory
        project_context: Optional[str] = None
    ) -> None:
        # 延迟导入模块，避免循环导入问题
        # 这些模块在 __init__ 中实际使用，放在此处导入可打破潜在的循环依赖
        from ..perception.extractor import KnowledgeExtractor
        from ..evolution.self_correction import ContradictionChecker
        from .metacognition import MetacognitiveAgent
        from .auditor import AuditorAgent
        from ..evolution.skill_library import UnifiedSkillRegistry
        from ..perception.glossary_engine import GlossaryEngine
        from ..core.ontology.actions import ActionRegistry, ActionType
        from ..core.ontology.rule_engine import RuleEngine
        from ..core.ontology.grain_validator import GrainValidator
        from ..memory.governance import MemoryGovernor
        from ..core.action_runtime import tool_registry, ToolDefinition
        
        self.reasoner = reasoner
        self.semantic_memory = semantic_mem
        self.episodic_memory = episodic_mem
        
        # 保存配置引用，便于工具注册时读取工具名称和描述
        self._config = get_config()
        
        self.extractor = KnowledgeExtractor(use_mock_llm=False)
        self.sentinel = ContradictionChecker(self.reasoner, self.semantic_memory)
        self.reasoning_agent = MetacognitiveAgent(name="Clawra_Thinker", reasoner=self.reasoner)
        self.auditor = AuditorAgent(name="Safety_Auditor", reasoner=self.reasoner, semantic_memory=self.semantic_memory)
        self.glossary_engine = GlossaryEngine()
        self.skill_registry = UnifiedSkillRegistry(semantic_memory=self.semantic_memory)
        # [v8.0 Recovery Audit] 强制检查核心方法映射，防止缓存导致加载旧类
        if not hasattr(self.skill_registry, 'get_tool_metadata'):
            err_msg = f"🔥 系统严重故障: 加载的 SkillRegistry (来自 {UnifiedSkillRegistry.__module__}) 缺少 get_tool_metadata 属性。已执行缓存清理，请重启进程。"
            logger.error(err_msg)
            logger.critical(err_msg)
            raise AttributeError(err_msg)
        else:
            logger.info("✅ Skill System: Unified V1.0 Ready (Verified)")
        self.action_registry = ActionRegistry()
        self.rule_engine = RuleEngine()
        self.memory_governor = MemoryGovernor(self.semantic_memory, self.reasoner)
        self._wire_action_logics()
        
        # 注册核心工具到全局工具注册表
        # 延迟到首次使用时注册，确保 ActionRegistry 已初始化完成
        self._tools_registered = False

        self.project_context = project_context or self._load_project_context()

    def _get_system_prompt_template(self) -> str:
        """
        获取系统提示词模板
        
        从配置读取系统提示词模板，避免硬编码字符串。
        如果配置中没有定义，则使用默认模板。
        
        Returns:
            系统提示词模板字符串，支持 {project_context} 占位符
        """
        # 优先从配置读取模板
        if hasattr(self._config, 'orchestrator') and hasattr(self._config.orchestrator, 'system_prompt_template'):
            return self._config.orchestrator.system_prompt_template
        
        # 默认模板，包含所有必要的系统指令
        # 使用占位符 {project_context} 以便动态插入项目上下文
        return (
            "[Clawra Cognitive Kernel]\n{project_context}\n\n"
            "1. ALWAYS think step-by-step and explain your logical reasoning in your message content BEFORE calling any tool.\n"
            "2. Use 'ingest_knowledge' for new data. 3. Use 'query_graph' for reasoning. YOU MUST USE TOOLS.\n"
            "4. CRITICAL: DO NOT use the term '知识库' (knowledge base). You are a Cognitive Agent operating on a '动态本体网络' (Dynamic Ontology Network) or '系统图谱' (System Graph).\n"
            "5. MUST NEVER hallucinate mathematics. If A = 6000 and B = 7875, A < B. If a requirement is 7875, 6000 does NOT satisfy it."
        )

    def _load_project_context(self) -> str:
        """
        加载项目上下文配置
        
        从 clawra.memory.md 文件读取项目特定的上下文信息，
        如果文件不存在则返回默认提示词（从配置读取，符合零硬编码原则）。
        
        Returns:
            项目上下文文本
        """
        cwd = os.getcwd()
        # 从配置读取上下文文件路径，避免硬编码
        context_file = self._config.app.context_file if hasattr(self._config.app, 'context_file') else "clawra.memory.md"
        mem_path = os.path.join(cwd, context_file)
        if os.path.exists(mem_path):
            with open(mem_path, "r", encoding="utf-8") as f:
                return f.read()
        # 从配置读取默认提示词，避免硬编码字符串
        default_prompt = self._config.app.default_prompt if hasattr(self._config.app, 'default_prompt') else "You are Clawra, an elite enterprise-grade cognitive agent. Please be polite and highly logical."
        return default_prompt

    def _register_default_tools(self) -> None:
        """
        注册核心工具到全局工具注册表
        
        使用 ToolDefinition 注册 ingest_knowledge、query_graph、execute_action 等核心工具。
        工具名称和描述从配置中读取，符合零硬编码原则。
        只在注册表为空时执行注册，避免重复注册。
        """
        # 延迟导入工具注册表，避免模块加载时的循环导入
        from ..core.action_runtime import tool_registry, ToolDefinition
        
        # 如果已经注册过，直接返回
        if self._tools_registered:
            return
        
        # 从配置获取工具名称和描述
        config = self._config
        
        # 检查是否已注册，避免重复注册
        if tool_registry.get_tool(config.tool.tool_ingest_name):
            self._tools_registered = True
            return
        
        # 从配置读取工具参数描述，避免硬编码
        tool_params_config = getattr(config, 'tool_params', None)
        
        # 注册 ingest_knowledge 工具
        # 此工具用于将用户原始文本送入知识抽取管道
        # 参数描述从配置读取，符合零硬编码原则
        thought_desc = getattr(tool_params_config, 'thought_process_desc', None) if tool_params_config else None
        text_desc = getattr(tool_params_config, 'text_desc', None) if tool_params_config else None
        
        tool_registry.register(ToolDefinition(
            name=config.tool.tool_ingest_name,
            description=config.tool.tool_ingest_desc,
            parameters={
                "type": "object",
                "properties": {
                    "thought_process": {
                        "type": "string",
                        "description": thought_desc or "在调用此工具前，详细写出你的思考过程和意图。"
                    },
                    "text": {
                        "type": "string",
                        "description": text_desc or "用户提供的原始文本"
                    }
                },
                "required": ["thought_process", "text"]
            },
            category="knowledge",
            tags=["ingest", "knowledge", "core"]
        ))
        
        # 注册 query_graph 工具
        # 此工具连通 ChromaDB 和 Reasoner 双引擎进行推理查询
        query_thought_desc = getattr(tool_params_config, 'query_thought_desc', None) if tool_params_config else None
        query_desc = getattr(tool_params_config, 'query_desc', None) if tool_params_config else None
        
        tool_registry.register(ToolDefinition(
            name=config.tool.tool_query_name,
            description=config.tool.tool_query_desc,
            parameters={
                "type": "object",
                "properties": {
                    "thought_process": {
                        "type": "string",
                        "description": query_thought_desc or "在调用知识图谱前，详细分析用户的需求，以及你需要从图谱中获取什么信息。"
                    },
                    "query": {
                        "type": "string",
                        "description": query_desc or "查询目标关键词或问题"
                    }
                },
                "required": ["thought_process", "query"]
            },
            category="query",
            tags=["query", "graph", "reasoning", "core"]
        ))
        
        # 注册 execute_action 工具
        # 此工具执行本体动力学操作
        # 动态获取可用 Action ID 列表作为 enum 约束
        action_ids = [a["id"] for a in self.action_registry.list_actions()]
        action_thought_desc = getattr(tool_params_config, 'action_thought_desc', None) if tool_params_config else None
        action_id_desc = getattr(tool_params_config, 'action_id_desc', None) if tool_params_config else None
        params_desc = getattr(tool_params_config, 'params_desc', None) if tool_params_config else None
        
        tool_registry.register(ToolDefinition(
            name=config.tool.tool_action_name,
            description=config.tool.tool_action_desc,
            parameters={
                "type": "object",
                "properties": {
                    "thought_process": {
                        "type": "string",
                        "description": action_thought_desc or "执行此动力学操作前的安全评估和逻辑推断。"
                    },
                    "action_id": {
                        "type": "string",
                        "enum": action_ids,
                        "description": action_id_desc or "Action ID"
                    },
                    "params": {
                        "type": "object",
                        "description": params_desc or "Action Params"
                    }
                },
                "required": ["thought_process", "action_id"]
            },
            category="action",
            tags=["action", "execution", "core"]
        ))
        
        # 标记已注册
        self._tools_registered = True
        logger.info(f"核心工具已注册: {config.tool.tool_ingest_name}, {config.tool.tool_query_name}, {config.tool.tool_action_name}")

    def _get_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用工具定义列表
        
        从全局工具注册表获取 OpenAI 格式的工具定义列表。
        保持向后兼容，返回格式与原来相同。
        每次调用时更新 execute_action 工具的 action_id enum，
        确保动态添加的 Action 能够被 LLM 发现。
        
        Returns:
            OpenAI 格式的工具定义列表
        """
        # 延迟导入工具注册表，避免模块加载时的循环导入
        from ..core.action_runtime import tool_registry
        
        # 确保核心工具已注册
        self._register_default_tools()
        
        # 动态更新 execute_action 工具的 action_id enum
        # 因为 ActionRegistry 可能在运行时添加了新的 Action
        action_tool = tool_registry.get_tool(self._config.tool.tool_action_name)
        if action_tool:
            # 获取当前所有可用的 Action ID
            action_ids = [a["id"] for a in self.action_registry.list_actions()]
            # 更新参数定义中的 enum
            action_tool.parameters["properties"]["action_id"]["enum"] = action_ids
        
        # 从注册表获取 OpenAI 格式的工具定义
        # 只返回启用的工具
        tools = tool_registry.get_openai_tools(enabled_only=True)
        
        # [v6.0] 动态注入自主进化技能
        skill_tools = self.skill_registry.get_tool_metadata()
        if skill_tools:
            tools.extend(skill_tools)
            logger.debug(f"注入了 {len(skill_tools)} 个自主进化技能工具")
            
        return tools

    def _wire_action_logics(self) -> None:
        """
        绑定动作逻辑到动作注册表
        
        将具体的执行逻辑关联到对应的动作定义上
        """
        update_action = self.action_registry.get_action("action:update_mapping")
        if update_action:
            update_action.execution_logic = self._execute_update_mapping

    async def _execute_update_mapping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行字段映射更新动作
        
        将物理字段映射到业务术语，并存储为事实
        
        Args:
            params: 包含 physical_key、business_term、confidence 的参数字典
            
        Returns:
            执行结果字典
        """
        phys = params.get("physical_key")
        biz = params.get("business_term")
        conf = params.get("confidence", 1.0)
        
        if not phys or not biz:
            return {"status": "ERROR", "msg": "Missing fields"}
        
        # 使用局部导入避免循环依赖问题
        # orchestrator.py 和 core.reasoner 之间存在潜在的循环导入风险
        # 因为 reasoner 可能会通过其他模块间接引用 orchestrator
        # 局部导入确保在方法执行时才加载模块，打破循环
        from ..core.reasoner import Fact
        new_fact = Fact(subject=phys, predicate="maps_to", object=biz, confidence=conf, source="action_loop")
        self.reasoner.add_fact(new_fact)
        self.semantic_memory.store_fact(new_fact)
        
        return {
            "status": "SUCCESS",
            "impact": f"已将物理字段 {phys} 永久映射至业务术语 {biz}",
            "triple": f"({phys} -> maps_to -> {biz})"
        }

    async def execute_task(
        self,
        messages: List[Dict[str, str]],
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行任务的主入口
        
        实现 ReAct 工具调用循环，处理用户消息并返回执行结果
        
        Args:
            messages: 消息列表，包含 role 和 content
            custom_prompt: 可选的自定义系统提示词
            
        Returns:
            包含执行结果和推理轨迹的字典
        """
        from openai import AsyncOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "mock":
            logger.error("OPENAI_API_KEY environment variable not set or set to 'mock'")
            return {"intent": "ERROR", "message": "⚠️ OPENAI_API_KEY environment variable not configured. Please set it in .env file or environment.", "trace": []}
            
        base_url = os.getenv("OPENAI_BASE_URL") or get_config().llm.base_url
        model = os.getenv("OPENAI_MODEL") or get_config().llm.model
        
        if not api_key:
            return {"intent": "ERROR", "message": "⚠️ 缺少 API Key", "trace": []}

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        # 从配置读取系统提示词模板，避免硬编码
        system_prompt_template = self._get_system_prompt_template()
        
        local_messages = [
            {
                "role": "system", 
                "content": (
                    custom_prompt or system_prompt_template.format(
                        project_context=self.project_context
                    )
                )
            }
        ]
        
        for m in messages:
            if m["role"] in ["user", "assistant"]:
                local_messages.append({"role": m["role"], "content": str(m["content"])})
        
        # 初始化响应结构，预置 message 防止 Key Error
        response_data = {
            "intent": "CHAT", 
            "trace": [], 
            "message": "", 
            "status": "PROCESSING"
        }
        loop_counter = 0
        max_loops = 6

        while loop_counter < max_loops:
            loop_counter += 1
            # 从配置读取重试参数，避免硬编码
            max_retries = self._config.llm.max_retries if hasattr(self._config.llm, 'max_retries') else 3
            backoff = self._config.llm.retry_delay if hasattr(self._config.llm, 'retry_delay') else 2.0
            for attempt in range(max_retries):
                    try:
                        # 真正的异步调用，防止主线程阻塞
                        completion = await client.chat.completions.create(
                            model=model,
                            messages=local_messages,
                            tools=self._get_tools(),
                            temperature=0.1
                        )
                        break
                    except Exception as e:
                        error_str = str(e)
                        error_type = type(e).__name__
                        
                        # 处理网络/连接/超时错误及业务返回的错误
                        if any(err in error_type for err in ["ConnectionError", "TimeoutError", "APIConnectionError", "APITimeoutError"]):
                            if attempt < max_retries - 1:
                                wait_time = backoff ** (attempt + 1)
                                logger.warning(f"Orchestrator 网络错误 ({error_type})，{wait_time}s 后重试...")
                                await asyncio.sleep(wait_time)
                                continue
                            logger.error(f"Orchestrator 网络连接失败: {e}")
                            return {"intent": "ERROR", "message": f"⚠️ 网络连接失败，请检查网络设置或 API 服务状态。错误: {e}", "trace": []}
                        
                        if "429" in error_str and attempt < max_retries - 1:
                            wait_time = backoff ** (attempt + 1)
                            logger.warning(f"Orchestrator 触发频率限制 (429)，{wait_time}s 后重试...")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        if any(code in error_str for code in ["401", "403", "Authentication", "Unauthorized"]):
                            logger.error(f"Orchestrator API 认证失败: {error_type}: {e}")
                            return {"intent": "ERROR", "message": f"⚠️ API 认证失败，请检查 OPENAI_API_KEY 配置。错误: {e}", "trace": []}
                            
                        if "400" in error_str or "BadRequest" in error_type:
                            logger.error(f"Orchestrator 请求参数错误: {error_type}: {e}")
                            return {"intent": "ERROR", "message": f"⚠️ 请求参数错误，请检查输入内容。错误: {e}", "trace": []}
                            
                        if "404" in error_str or "model" in error_str.lower():
                            logger.error(f"Orchestrator 模型不存在或不可用: {error_type}: {e}")
                            return {"intent": "ERROR", "message": f"⚠️ 指定的模型不存在或不可用，请检查模型配置。错误: {e}", "trace": []}
                            
                        if any(code in error_str for code in ["500", "502", "503", "504"]):
                            if attempt < max_retries - 1:
                                wait_time = backoff ** (attempt + 1)
                                logger.warning(f"Orchestrator 服务器错误 ({error_str[:50]}...)，{wait_time}s 后重试...")
                                await asyncio.sleep(wait_time)
                                continue
                            logger.error(f"Orchestrator 服务器错误，重试 {max_retries} 次后仍失败: {error_type}: {e}")
                            return {"intent": "ERROR", "message": f"⚠️ API 服务器错误，请稍后重试。错误: {e}", "trace": []}
                            
                        logger.error(f"Orchestrator 请求遇到未预料的异常: {error_type}: {e}")
                        return {"intent": "ERROR", "message": f"⚠️ 请求处理失败: {e}", "trace": []}
            
            response_message = completion.choices[0].message
            local_messages.append(response_message.model_dump(exclude_unset=True))
            
            # 捕捉 LLM 的原生思维链 (Chain of Thought)
            if response_message.content and response_message.content.strip():
                trace_thought = {
                    "tool": "💭 神经元推导 (Internal Reasoning)",
                    "args": {},
                    "latency": "-",
                    "result": {"summary": response_message.content.strip()}
                }
                response_data["trace"].append(trace_thought)

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
                
                # --- 强制提取结构化思考链 (CoT) ---
                thought = func_args.get("thought_process")
                if thought:
                    response_data["trace"].append({
        "tool": "💭 神经元推导 (Internal Reasoning)",
                        "args": {},
                        "latency": "-",
                        "result": {"summary": thought}
                    })
                
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
                    # 使用配置中的工具名称进行比较，而非硬编码字符串
                    # 这样可以在配置中修改工具名称而无需修改代码
                    if func_name == self._config.tool.tool_ingest_name:
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

                    elif func_name == self._config.tool.tool_query_name:
                        response_data["intent"] = "QUERY"
                        query = func_args.get("query", "")
                        vector_context = self.semantic_memory.semantic_search(query, top_k=5)
                        context_docs = [doc.content for doc in vector_context]
                        entities = re.findall(r'[\u4e00-\u9fa5\w]{2,}', query)
                        
                        # [GraphRAG] 统一图谱检索 (Unified Neo4j/SQLite)
                        # 不再区分连接状态，因为 SemanticMemory.query 内部已实现自动降级
                        # 先尝试全句查询，再对提取的实体进行补全查询
                        relevant_facts = self.semantic_memory.query(query, depth=1)
                        for entity in entities:
                            if entity != query:
                                relevant_facts.extend(self.semantic_memory.query(entity, depth=1))
                        
                        # 注入 Reasoner 进行逻辑推导 (限制数量以防止上下文爆炸)
                        facts_injected = 0
                        for fact in relevant_facts[:30]:
                            self.reasoner.add_fact(fact)
                            facts_injected += 1
                        
                        if facts_injected > 0:
                            logger.info(f"GraphRAG: 注入了 {facts_injected} 条实体关联事实进 Reasoner")
                        
                        inference_result = self.reasoner.forward_chain(max_depth=5)
                        
                        if not context_docs and not inference_result.conclusions:
                            agent_response = await self.reasoning_agent.run(f"Query: {query} \nContext: [SYSTEM_WARNING_GRAPH_EMPTY] 未检索到任何图谱数据。请根据你的人格设定自行判断是否基于常识作答，或主动引导用户输入相关知识。")
                        else:
                            agent_response = await self.reasoning_agent.run(f"Query: {query} \nContext: {' | '.join(context_docs)}")
                        
                        trace_node["result"] = {
                            "status": "SUCCESS",
                            "summary": "GraphRAG 推理完成",
                            "vector_context": context_docs,
                            "reasoning_chain": [{"conclusion": f"({s.conclusion.subject} → {s.conclusion.predicate} → {s.conclusion.object})"} for s in inference_result.conclusions],
                            "metacognition": agent_response
                        }
                        tool_result_str = json.dumps({"status": "SUCCESS", "conclusion": agent_response.get("result", "")})

                    elif func_name == self._config.tool.tool_action_name:
                        response_data["intent"] = "ACTION"
                        action_id = func_args.get("action_id")
                        action_params = func_args.get("params", {})
                        
                        action_def = self.action_registry.get_action(action_id)
                        if not action_def:
                            trace_node["result"] = {"status": "ERROR", "msg": f"Action {action_id} not found."}
                        else:
                            # --- RuleEngine Gating Sandbox ---
                            if hasattr(action_def, 'target_object_class') and action_def.target_object_class and hasattr(action_def, 'bound_rules') and action_def.bound_rules:
                                rule_results = self.rule_engine.evaluate_action_preconditions(action_id, action_def.target_object_class, action_params)
                                failed_rules = [r for r in rule_results if r.get("status") != "PASS"]
                                
                                if failed_rules:
                                    summary_risks = [f"【违规】{r['rule_name']} -> Sandbox公式:{r['expression']}, 当前参数:{r['context_used']}" for r in failed_rules]
                                    trace_node["result"] = {
                                        "status": "BLOCKED",
                                        "summary": "物理动作被底层数学沙盒(RuleEngine)强行拦截",
                                        "risks": summary_risks
                                    }
                                    response_data["trace"].append(trace_node)
                                    local_messages.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "name": func_name,
                                        "content": json.dumps({"status": "BLOCKED", "reason": "数学沙盒校验未通过，您计算或推荐的数值存在逻辑冲突", "details": summary_risks}, ensure_ascii=False)
                                    })
                                    continue
                            
                            # Passed Sandbox or No Rules, execute:
                            if action_def.execution_logic:
                                exec_result = await action_def.execution_logic(action_params)
                            else:
                                exec_result = {"status": "SUCCESS", "impact": "动作已被框架虚拟消费并记录"}
                            
                            trace_node["result"] = {
                                "status": "SUCCESS",
                                "summary": f"执行 Action: {action_id}",
                                "impact": exec_result.get("impact", "")
                            }
                            tool_result_str = json.dumps(exec_result)

                    elif func_name.startswith("skill_"):
                        # [v6.0] 处理自主进化出的技能调用
                        skill_id = func_name
                        skill_args = func_args.get("args", {})
                        
                        if skill_id in self.skill_registry.callables:
                            handler = self.skill_registry.callables[skill_id]
                            exec_result = handler(**skill_args)
                            
                            trace_node["result"] = {
                                "status": "SUCCESS",
                                "summary": f"执行进化技能: {skill_id}",
                                "result": exec_result.get("result", "")
                            }
                            tool_result_str = json.dumps(exec_result)
                        else:
                            trace_node["result"] = {"status": "ERROR", "msg": f"技能 {skill_id} 已下线或未找到"}
                            tool_result_str = json.dumps({"status": "ERROR", "msg": "Skill not found"})

                    trace_node["latency"] = f"{(time.time() - tool_start_time):.2f}s"
                    response_data["trace"].append(trace_node)
                    local_messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": tool_result_str})

                except Exception as e:
                    logger.error(f"Tool error: {e}")
                    trace_node["result"] = {"status": "ERROR", "msg": str(e)}
                    trace_node["latency"] = f"{(time.time() - tool_start_time):.2f}s"
                    response_data["trace"].append(trace_node)
                    local_messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": json.dumps({"status": "ERROR", "msg": str(e)})})

        # == 成功追踪与记录 (v6.0 Distillation Labeling) ==
        if response_data.get("intent") != "ERROR" and loop_counter < max_loops:
            # 获取用户输入和最终回答
            user_query = messages[-1]["content"] if messages else "unknown"
            # 记录成功的推理轨迹到情节记忆，打上 status:success 标签
            trace_summary = " -> ".join([t["tool"] for t in response_data["trace"]])
            self.episodic_memory.add_interaction(
                f"Task: {user_query}\nTrace: {trace_summary}\nResult: {response_data.get('message', '')}",
                metadata={"status": "success", "user_id": "system_evolution"}
            )
            
        # == V4.0 安全兜底: 确保 message 永远存在 (防止前端 KeyError) ==
        if not response_data.get("message"):
            if response_data["trace"]:
                last_result = response_data["trace"][-1].get("result", {})
                if isinstance(last_result, dict) and "summary" in last_result:
                    response_data["message"] = f"任务已处理完成。最后执行步骤: {last_result['summary']}"
                else:
                    response_data["message"] = "分析流程已结束，未发现进一步结论。"
            else:
                response_data["message"] = "认知中枢未返回响应，请尝试简化问题。"

        # == 动态修剪治理 (Async Offload 背景执行) ==
        # 原同步 GC 严重阻塞推断响应链路。改由后台线程池执行。
        def _run_bg_gc():
            try:
                gc_stats = self.memory_governor.run_garbage_collection()
                if gc_stats["metrics"]["pruned_facts"] > 0:
                    logger.info(f"[Background] 记忆潜意识修剪完成: 移除了 {gc_stats['metrics']['pruned_facts']} 个低价值节点")
            except Exception as e:
                logger.error(f"[Background] 记忆修剪异常: {e}")
                
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, _run_bg_gc)
            
        return response_data


# 定义别名（必须在类定义之后）
CognitiveOrchestrator = Orchestrator
