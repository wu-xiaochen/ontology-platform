"""
Clawra SDK - LangChain Adapter (Enhanced)

提供针对 LangChain 框架的完整工具集适配。
将 Clawra 的核心能力封装为 LangChain Tools，支持在 AgentExecutor 中直接调度。

使用示例:
    from langchain.agents import AgentType, initialize_agent
    from clawra.sdk.adapters.langchain import get_clawra_tools

    tools = get_clawra_tools()
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
"""

try:
    from langchain.tools import BaseTool
    from langchain.callbacks.manager import CallbackManagerForToolRun
except ImportError:
    # 提供 Mock 以支持未安装 langchain 的环境
    class BaseTool:
        name: str = ""
        description: str = ""
        def __init__(self, **kwargs): pass

    class MockCallbackManager:
        pass

    CallbackManagerForToolRun = MockCallbackManager

from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.sdk import ClawraSDK


# ─────────────────────────────────────────────────────────────
# Tool Input Schemas
# ─────────────────────────────────────────────────────────────

class ClawraLearnInput(BaseModel):
    """Clawra Learn Tool 输入参数"""
    text: str = Field(description="要学习的自然语言文本内容")
    domain: Optional[str] = Field(None, description="领域提示（可选），帮助更准确地提取知识")


class ClawraQueryInput(BaseModel):
    """Clawra Query Tool 输入参数"""
    query: str = Field(description="需要通过认知引擎进行逻辑验证的问题或指令")


class ClawraRetrieveInput(BaseModel):
    """Clawra Retrieve Tool 输入参数"""
    query: str = Field(description="检索查询")
    top_k: int = Field(5, description="返回结果数量")


class ClawraEvolveInput(BaseModel):
    """Clawra Evolve Tool 输入参数"""
    trigger: str = Field("manual", description="触发类型：manual（手动）或 automatic（自动）")


class ClawraStatsInput(BaseModel):
    """Clawra Stats Tool 输入参数"""
    pass


# ─────────────────────────────────────────────────────────────
# Tool Implementations
# ─────────────────────────────────────────────────────────────

class ClawraLearnTool(BaseTool):
    """
    Clawra 知识学习工具

    描述: 从自然语言文本中自动提取结构化知识（实体、关系、约束），
    存入 Clawra 的知识图谱。与传统的 prompt engineering 不同，
    Clawra 会将知识编码为形式化规则，供后续推理使用。

    使用场景:
    - 构建领域知识库
    - 从文档中自动提取规则和约束
    - 将非结构化文本转化为可推理的知识
    """
    name: str = "clawra_learn"
    description: str = (
        "从自然语言文本中学习知识。将文本中的实体、关系和约束提取出来，"
        "存入知识图谱供后续推理使用。当需要构建领域知识库或从文档中提取规则时使用。"
    )
    args_schema: Type[BaseModel] = ClawraLearnInput
    sdk: Optional[ClawraSDK] = None

    def __init__(self, sdk: Optional[ClawraSDK] = None, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk or ClawraSDK()

    def _run(self, text: str, domain: Optional[str] = None) -> str:
        """同步执行知识学习"""
        result = self.sdk.learn(text, domain=domain)

        extracted = result.get("extracted_triples", [])
        patterns = result.get("patterns_discovered", 0)

        response = f"✅ 学习完成！\n"
        response += f"📊 提取三元组: {len(extracted)} 条\n"
        response += f"🧠 发现模式: {patterns} 个\n"

        if extracted:
            response += f"\n【已学习知识】\n"
            for triple in extracted[:5]:
                if isinstance(triple, dict):
                    response += f"  • {triple.get('subject', '?')} — {triple.get('predicate', '?')} — {triple.get('object', '?')}\n"
                else:
                    response += f"  • {triple}\n"
            if len(extracted) > 5:
                response += f"  ... 还有 {len(extracted) - 5} 条\n"

        return response

    async def _arun(
        self,
        text: str,
        domain: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步执行知识学习"""
        return self._run(text, domain)


class ClawraReasoningTool(BaseTool):
    """
    Clawra 逻辑推理工具

    描述: 基于知识图谱进行严格的神经符号混合推理。
    通过前向链和后向链逻辑推导出确定性结论，有效阻断 LLM 幻觉。

    使用场景:
    - 需要严谨逻辑推导的查询
    - 本体验证（检查答案是否符合已知事实）
    - 防止 LLM 产生幻觉的关键决策
    """
    name: str = "clawra_reasoning"
    description: str = (
        "进行严格的神经符号混合推理。当需要严谨的逻辑推导、"
        "本体验证、或者防止 AI 幻觉的关键决策时使用。"
        "输入是一个自然语言问题或指令。"
    )
    args_schema: Type[BaseModel] = ClawraQueryInput
    sdk: Optional[ClawraSDK] = None

    def __init__(self, sdk: Optional[ClawraSDK] = None, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk or ClawraSDK()

    def _run(self, query: str) -> str:
        """同步执行推理"""
        result = self.sdk.reason(query)

        conclusion = result.get("conclusion", result.get("message", "未能得出有效结论"))
        confidence = result.get("confidence", 0.0)
        trace = result.get("reasoning_trace", [])

        response = f"🧠 推理结论: {conclusion}\n"
        response += f"📊 置信度: {confidence:.2f}\n"

        if trace:
            response += f"🔗 推理链路:\n"
            for i, step in enumerate(trace[:7], 1):
                response += f"  {i}. {step}\n"
            if len(trace) > 7:
                response += f"  ... 共 {len(trace)} 步\n"

        return response

    async def _arun(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步执行推理"""
        return self._run(query)


class ClawraRetrieveTool(BaseTool):
    """
    Clawra 知识检索工具

    描述: 使用 GraphRAG 混合检索（向量 + 知识图谱）从知识库中检索相关内容。
    比纯向量 RAG 检索质量更高，上下文相关性更强。

    使用场景:
    - RAG 知识问答
    - 检索与查询相关的文档和事实
    - 增强 LLM 的上下文理解
    """
    name: str = "clawra_retrieve"
    description: str = (
        "使用 GraphRAG 混合检索从知识库中检索相关内容。适用于 RAG 问答、"
        "文档检索、和增强 LLM 上下文。返回最相关的 top_k 条知识。"
    )
    args_schema: Type[BaseModel] = ClawraRetrieveInput
    sdk: Optional[ClawraSDK] = None

    def __init__(self, sdk: Optional[ClawraSDK] = None, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk or ClawraSDK()

    def _run(self, query: str, top_k: int = 5) -> str:
        """同步执行知识检索"""
        try:
            context = self.sdk.core.retrieve_context(query=query, top_k=top_k)
        except AttributeError:
            # fallback if retrieve_context doesn't exist
            context = []

        if not context:
            return f"🔍 检索「{query}」: 未找到相关内容\n💡 建议：先使用 clawra_learn 学习相关知识"

        response = f"🔍 检索「{query}」（top {top_k}）:\n\n"
        for i, item in enumerate(context[:5], 1):
            if isinstance(item, dict):
                content = item.get("content", str(item))
                score = item.get("score", item.get("distance", "N/A"))
                response += f"  {i}. {content[:200]}"
                if score != "N/A":
                    response += f" [相关度: {score:.2f}]"
                response += "\n\n"
            else:
                response += f"  {i}. {str(item)[:200]}\n\n"

        return response

    async def _arun(
        self,
        query: str,
        top_k: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步执行知识检索"""
        return self._run(query, top_k)


class ClawraEvolveTool(BaseTool):
    """
    Clawra 自主进化工具

    描述: 触发 Clawra 的 8 阶段自主进化闭环。
    系统会自动评估知识质量、检测冲突、蒸馏技能、更新规则。

    8 阶段: 感知 → 学习 → 推理 → 执行 → 评估 → 漂移检测 → 规则修订 → 知识更新

    使用场景:
    - 定期触发系统自我优化
    - 在批量知识注入后触发知识整理
    - 检测并修复知识库中的冲突
    """
    name: str = "clawra_evolve"
    description: str = (
        "触发 Clawra 的 8 阶段自主进化闭环。"
        "系统会自动评估知识质量、检测冲突、蒸馏技能、更新规则。"
        "适用于定期优化或在批量知识注入后触发。"
    )
    args_schema: Type[BaseModel] = ClawraEvolveInput
    sdk: Optional[ClawraSDK] = None

    def __init__(self, sdk: Optional[ClawraSDK] = None, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk or ClawraSDK()

    def _run(self, trigger: str = "manual") -> str:
        """同步执行进化（会触发 async evolve）"""
        import asyncio

        async def _do_evolve():
            return await self.sdk.evolve()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_do_evolve())
        loop.close()

        stages = result.get("stages", {})
        quality = result.get("knowledge_quality", {})
        conflicts = result.get("conflicts_resolved", 0)

        response = f"🔄 进化闭环完成！\n"
        response += f"🔧 冲突解决: {conflicts} 个\n"
        response += f"📊 知识质量评估:\n"
        for key, val in quality.items():
            response += f"  • {key}: {val}\n"

        if stages:
            response += f"\n🧬 8 阶段状态:\n"
            for stage, status in list(stages.items())[:8]:
                emoji = "✅" if status in ("completed", "success", True) else "⏳"
                response += f"  {emoji} {stage}\n"

        return response

    async def _arun(
        self,
        trigger: str = "manual",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步执行进化"""
        return self._run(trigger)


class ClawraStatsTool(BaseTool):
    """
    Clawra 系统状态工具

    描述: 获取 Clawra 系统的实时统计信息，包括事实数量、
    模式数量、实体数量、记忆统计等。

    使用场景:
    - 查看系统当前知识储备
    - 监控知识图谱状态
    - 调试和诊断
    """
    name: str = "clawra_stats"
    description: str = "获取 Clawra 系统的实时统计信息：事实数量、模式数量、实体数量等。"
    args_schema: Type[BaseModel] = ClawraStatsInput
    sdk: Optional[ClawraSDK] = None

    def __init__(self, sdk: Optional[ClawraSDK] = None, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk or ClawraSDK()

    def _run(self) -> str:
        """获取系统统计"""
        try:
            stats = self.sdk.core.get_statistics()
        except AttributeError:
            return "❌ 系统统计不可用，请确保 Clawra 已正确初始化"

        response = f"📊 Clawra 系统状态\n"
        response += f"{'='*30}\n"

        facts = stats.get("facts", 0)
        response += f"🧠 事实总数: {facts}\n"

        patterns = stats.get("patterns", {})
        if isinstance(patterns, dict):
            response += f"🔮 模式数量: {patterns.get('total', 'N/A')}\n"
        else:
            response += f"🔮 模式数量: {patterns}\n"

        entities = stats.get("entities", 0)
        response += f"🏷️ 实体数量: {entities}\n"

        domain = stats.get("domain", "未设置")
        response += f"🎯 当前领域: {domain}\n"

        return response

    async def _arun(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步获取统计"""
        return self._run()


# ─────────────────────────────────────────────────────────────
# Factory Function
# ─────────────────────────────────────────────────────────────

def get_clawra_tools(sdk: Optional[ClawraSDK] = None) -> List[BaseTool]:
    """
    快速获取所有 Clawra LangChain Tools

    返回完整的工具集，可以直接传给 LangChain Agent。

    示例:
        from langchain.agents import AgentType, initialize_agent

        tools = get_clawra_tools()
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        agent.run("用 clawra 学习天然气管道安全规范，然后回答：最大允许压力是多少？")

    Args:
        sdk: 可选的 ClawraSDK 实例。默认为新实例。

    Returns:
        List[BaseTool]: Clawra 工具列表
    """
    _sdk = sdk or ClawraSDK()
    return [
        ClawraLearnTool(sdk=_sdk),
        ClawraReasoningTool(sdk=_sdk),
        ClawraRetrieveTool(sdk=_sdk),
        ClawraEvolveTool(sdk=_sdk),
        ClawraStatsTool(sdk=_sdk),
    ]


def get_clawra_tools_dict(sdk: Optional[ClawraSDK] = None) -> Dict[str, BaseTool]:
    """
    获取 Clawra Tools 的字典格式（name -> tool）

    适用于需要按名称访问工具的场景。
    """
    tools = get_clawra_tools(sdk)
    return {tool.name: tool for tool in tools}
