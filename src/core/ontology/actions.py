import logging
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ActionType:
    """
    Palantir-style Action Type
    
    不仅描述事实，还定义了对本体数据的"动力学"操作。
    包含验证规则、执行逻辑和副作用。
    """
    id: str
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    validation_logic: Optional[Callable] = None
    execution_logic: Optional[Callable] = None

class ActionRegistry:
    """管理所有可用 Actions 的注册中心"""
    def __init__(self):
        self.actions: Dict[str, ActionType] = {}
        self._register_default_actions()

    def _register_default_actions(self):
        """注册初始内置行动"""
        # 1. 质量合规校验 Action
        self.register(ActionType(
            id="action:validate_compliance",
            name="合规性智能校验",
            description="针对特定调压箱型号，对照国家安全标准（GB）进行自动闭环校验。",
            parameters={"target_entity": "string", "standard_id": "string"}
        ))
        
        # 2. 知识演进 Action
        self.register(ActionType(
            id="action:evolve_ontology",
            name="本体自我演进",
            description="基于最近的冲突检测结果，自动修正并优化本体模式约束。",
            parameters={"feedback_loop_id": "string"}
        ))

    def register(self, action: ActionType):
        self.actions[action.id] = action
        logger.info(f"Registered Action Type: {action.name} ({action.id})")

    def get_action(self, action_id: str) -> Optional[ActionType]:
        return self.actions.get(action_id)

    def list_actions(self) -> List[Dict]:
        return [
            {"id": a.id, "name": a.name, "description": a.description}
            for a in self.actions.values()
        ]
