import logging
from abc import ABC, abstractmethod
from typing import Any, Dict
from core.reasoner import Reasoner

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    基础智能体类
    """
    def __init__(self, name: str, reasoner: Reasoner):
        self.name = name
        self.reasoner = reasoner
        
    @abstractmethod
    async def run(self, task: str) -> Dict[str, Any]:
        """运行任务的主入口"""
        pass
