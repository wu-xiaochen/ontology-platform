import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..core.reasoner import Reasoner

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    基础智能体类
    
    定义所有智能体的通用接口和基础行为，
    子类必须实现 run 方法以提供具体的任务执行逻辑。
    """
    
    def __init__(self, name: str, reasoner: Reasoner) -> None:
        """
        初始化基础智能体
        
        Args:
            name: 智能体名称，用于日志和识别
            reasoner: 推理引擎实例，提供逻辑推理能力
        """
        self.name: str = name
        self.reasoner: Reasoner = reasoner
        
    @abstractmethod
    async def run(self, task: str) -> Dict[str, Any]:
        """
        运行任务的主入口
        
        子类必须实现此方法以执行具体的智能体任务。
        
        Args:
            task: 任务描述文本
            
        Returns:
            包含执行结果的字典，具体结构由子类定义
        """
        pass
    
    def log_action(self, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        记录智能体动作日志
        
        提供统一的日志记录接口，便于追踪智能体行为。
        
        Args:
            action: 动作名称
            details: 可选的详细参数
        """
        log_msg = f"[{self.name}] {action}"
        if details:
            log_msg += f": {details}"
        logger.info(log_msg)
