"""
Clawra SDK - 极致简化的认知 Agent 集成套件

Clawra SDK 旨在为第三方 Agent 框架（如 LangChain, CrewAI, AutoGen）提供极致简化的
接入体验。通过该 SDK，开发者可以使用 3 行代码为现有 Agent 注入「自主进化」和「逻辑闭环」能力。

示例：
    from clawra.sdk import ClawraSDK
    sdk = ClawraSDK()
    sdk.learn("供应商 A 提供轴承部件。轴承部件属于核心零组件。")
    result = sdk.reason("供应商 A 提供核心零组件吗？")
"""

import logging
from typing import Dict, List, Any, Optional

from ..clawra import Clawra
from ..core.reasoner import Fact

logger = logging.getLogger(__name__)

class ClawraSDK:
    """
    Clawra SDK 核心入口
    
    封装了复杂的本体层与认知层逻辑，暴露简洁的生产级 API。
    """
    
    def __init__(self, **kwargs):
        """
        初始化 SDK 实例
        
        Args:
            **kwargs: 透传给 Clawra 核心类的参数 (e.g., enable_memory=True)
        """
        self._core = Clawra(**kwargs)
        logger.info("🚀 Clawra SDK 已初始化，认知能力就绪")

    def learn(self, content: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        自主知识提取与本体同步
        
        Args:
            content: 非结构化文本内容
            domain: 可选的领域提示
            
        Returns:
            Dict 包含提取出的三元组、实体和领域摘要
        """
        return self._core.learn(content, domain_hint=domain)

    def reason(self, query: str, context: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        神经符号混合推理
        
        基于当前本体知识图谱进行严格的逻辑推导，有效阻断 LLM 幻觉。
        
        Args:
            query: 用户提问
            context: 额外的上下文（可选）
            
        Returns:
            Dict 包含推理结论、置信度、以及完整的推理轨迹 (Thinking Trace)
        """
        # 内部调用推理驱动器
        return self._core.orchestrate(query)

    async def evolve(self) -> Dict[str, Any]:
        """
        手动触发系统进化闭环
        
        执行：策略评估 -> 规则发现 -> 知识冗余清理 -> 技能蒸馏
        
        Returns:
            评估摘要与进化日志
        """
        # 调用核心进化闭环
        return await self._core.evolve()

    def get_graph_data(self) -> Dict[str, Any]:
        """
        获取知识图谱可视化数据
        
        Returns:
            符合 D3/Three.js 格式的节点和边数据
        """
        return self._core.knowledge_graph.export_d3()

    @property
    def core(self) -> Clawra:
        """访问底层核心实例（高级开发者使用）"""
        return self._core
