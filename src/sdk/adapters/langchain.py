"""
Clawra SDK - LangChain Adapter

提供针对 LangChain 框架的标准化适配。
将 Clawra 的推理能力封装为 LangChain Tool，支持在 AgentExecutor 中直接调度。
"""

try:
    from langchain.tools import BaseTool
except ImportError:
    # 如果未安装 langchain，提供 Mock 类或抛出友好提示
    class BaseTool: pass
    
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from .. import ClawraSDK

class ClawraQueryInput(BaseModel):
    query: str = Field(description="需要通过认知引擎进行逻辑验证的问题或指令")

class ClawraReasoningTool(BaseTool):
    """
    Clawra 认知推理工具
    
    描述: 用于需要严谨逻辑推导、本体验证、以及防止 AI 幻觉的复杂查询。
    该工具连接到 Clawra 的神经符号引擎，返回基于事实图谱的确定性结论。
    """
    name: str = "clawra_reasoning"
    description: str = "用于逻辑严谨的推理与本体知识验证。当常规 LLM 可能产生幻觉或需要基于特定领域知识库回答时使用。"
    args_schema: Type[BaseModel] = ClawraQueryInput
    sdk: Optional[ClawraSDK] = None

    def __init__(self, sdk: Optional[ClawraSDK] = None, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk or ClawraSDK()

    def _run(self, query: str) -> str:
        """同步执行推理"""
        result = self.sdk.reason(query)
        # 组装格式化的推理响应
        trace = result.get("reasoning_trace", [])
        conclusion = result.get("conclusion", "未能得出有效结论")
        confidence = result.get("confidence", 0.0)
        
        response = f"【Clawra 推理结论】: {conclusion}\n"
        response += f"【置信度】: {confidence:.2f}\n"
        if trace:
            response += f"【推理链路】: {' -> '.join(trace[:5])} ..."
        
        return response

    async def _arun(self, query: str) -> str:
        """异步执行推理"""
        # 简单封装，未来可接入真异步接口
        return self._run(query)

def get_langchain_tools(sdk: Optional[ClawraSDK] = None) -> list:
    """快速获取所有 Clawra 适配工具"""
    return [ClawraReasoningTool(sdk=sdk)]
