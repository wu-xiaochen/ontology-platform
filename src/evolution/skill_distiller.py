"""
Skill Distiller - 认知进化核心
分析情节记忆中的成功路径，并将其蒸馏为可重用技能。
"""

import logging
import json
import asyncio
from typing import List, Dict, Any
from ..utils.config import get_config
from .skill_library import UnifiedSkillRegistry, Skill, SkillType

logger = logging.getLogger(__name__)

class SkillDistiller:
    """技能蒸馏引擎"""
    
    def __init__(self, skill_registry: UnifiedSkillRegistry, episodic_memory: Any):
        self.registry = skill_registry
        self.memory = episodic_memory
        self.config = get_config()

    async def distill_from_memories(self) -> int:
        """
        核心进化逻辑：从近期记忆中发现潜在技能
        """
        logger.info("开始扫描情节记忆以提取潜在技能...")
        
        # 1. 检索近期的成功交互 (通过 status: success 过滤)
        # 注意: search_memories 如果底层是 Mem0，通常返回的是语义搜索结果
        # 我们搜索关键词 "Task" 来获取交互记录
        recent_memories = self.memory.search_memories("Task Trace Result", limit=20)
        
        if not recent_memories:
            logger.info("未发现足够的情节记忆进行蒸馏。")
            return 0

        # 2. 这里的实现应该调用 LLM 来分析这些记忆并发现模式
        # 为了演示真正的“逻辑实现”而非 Mock，我们先实现一个基于规则的提取，
        # 并在 v4.5 中引入 LLM 深度蒸馏。
        
        discovered_count = 0
        for mem in recent_memories:
            text = mem.get("text", mem.get("memory", ""))
            
            # 简单的模式发现：如果记录中包含典型的成功推理链条
            if "status: success" in text.lower() or "result:" in text.lower():
                # 尝试提取任务目标作为技能名
                try:
                    # 假设格式: Task: <Goal> Trace: <Tools>
                    task_section = text.split("Trace:")[0] if "Trace:" in text else ""
                    goal = task_section.replace("Task:", "").strip()
                    
                    if goal and len(goal) > 5:
                        skill_id = f"skill:auto_{hash(goal) % 10000}"
                        
                        if skill_id not in self.registry.skills:
                            new_skill = Skill(
                                id=skill_id,
                                name=f"AutoPattern: {goal[:20]}...",
                                description=f"从成功案例中蒸馏出的自动化逻辑: {goal}",
                                skill_type=SkillType.LOGIC,
                                content=text # 暂时将原始轨迹作为逻辑模板
                            )
                            self.registry.register_skill(new_skill)
                            discovered_count += 1
                except Exception as e:
                    logger.debug(f"跳过不符合格式的记忆条目: {e}")

        return discovered_count
