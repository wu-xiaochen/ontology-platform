"""
Skill Distiller - 认知进化核心
分析情节记忆中的成功路径，并将其蒸馏为可重用技能。
支持可执行技能模板生成与安全审计。
"""

import logging
import json
import asyncio
import re
import ast
from typing import List, Dict, Any, Optional, Tuple
from ..utils.config import get_config
from .skill_library import UnifiedSkillRegistry, Skill, SkillType

logger = logging.getLogger(__name__)


class SkillDistiller:
    """
    技能蒸馏引擎

    从情节记忆中自动发现、提取并生成可执行技能。
    支持三种技能类型:
    - LOGIC: DSL/SQL 推理模板
    - CODE: 可执行 Python 代码（通过 importlib 动态加载）
    - EXECUTABLE: 可执行结构化指令（通过 AST 安全执行）
    """

    def __init__(self, skill_registry: UnifiedSkillRegistry, episodic_memory: Any):
        self.registry = skill_registry
        self.memory = episodic_memory
        self.config = get_config()
        self.skill_config = self.config.skill

    async def distill_from_memories(self) -> int:
        """
        核心进化逻辑：从近期记忆中发现并生成可执行技能

        Returns:
            本次蒸馏成功创建的技能数量
        """
        logger.info("开始扫描情节记忆以提取潜在技能...")

        # 1. 检索近期的成功交互记录
        recent_memories = self.memory.search_memories("Task Trace Result", limit=20)

        if not recent_memories:
            logger.info("未发现足够的情节记忆进行蒸馏。")
            return 0

        # 2. 分析记忆并提取技能模式
        discovered_skills = self._analyze_memories_for_skills(recent_memories)

        if not discovered_skills:
            logger.info("未从记忆中提取到有效的技能模式。")
            return 0

        # 3. 过滤并验证技能
        valid_skills = []
        for skill_data in discovered_skills:
            if self._validate_skill_content(skill_data):
                valid_skills.append(skill_data)
            if len(valid_skills) >= self.skill_config.max_distill_per_batch:
                break

        # 4. 注册有效技能
        registered_count = 0
        for skill_data in valid_skills:
            skill = self._create_skill_from_data(skill_data)
            if skill and self.registry.register_skill(skill):
                registered_count += 1
                logger.info(f"✅ 技能蒸馏成功: {skill.name} (type={skill.skill_type.value})")

        logger.info(f"技能蒸馏完成: 共发现 {len(discovered_skills)} 个模式, 验证通过 {len(valid_skills)}, 成功注册 {registered_count}")
        return registered_count

    def _analyze_memories_for_skills(self, memories: List[Dict]) -> List[Dict]:
        """
        从记忆列表中分析并提取技能数据

        Args:
            memories: 记忆字典列表

        Returns:
            技能数据字典列表
        """
        discovered = []

        for mem in memories:
            text = mem.get("text", mem.get("memory", ""))

            # 跳过无效记忆
            if not text or len(text) < self.skill_config.min_content_length:
                continue

            # 检查是否为成功案例
            is_success = "status: success" in text.lower() or "result:" in text.lower()

            # 提取技能模式
            patterns = self._extract_patterns(text, is_success)
            discovered.extend(patterns)

        # 去重：基于技能名和内容哈希
        seen = set()
        unique_skills = []
        for skill_data in discovered:
            key = (skill_data.get("name", ""), hash(skill_data.get("content", "")) % 100000)
            if key not in seen:
                seen.add(key)
                unique_skills.append(skill_data)

        return unique_skills

    def _extract_patterns(self, text: str, is_success: bool) -> List[Dict]:
        """
        从文本中提取技能模式

        Args:
            text: 记忆文本
            is_success: 是否为成功案例

        Returns:
            提取的技能数据列表
        """
        patterns = []

        # 尝试提取任务目标作为技能名
        task_section = text.split("Trace:")[0] if "Trace:" in text else text
        goal = task_section.replace("Task:", "").strip()

        if not goal or len(goal) < 5:
            return patterns

        # 如果是成功案例，生成可执行技能
        if is_success:
            # 尝试从文本中提取可执行的代码片段或逻辑
            code_snippet = self._extract_code_snippet(text)

            if code_snippet:
                # 生成 EXECUTABLE 类型技能
                patterns.append({
                    "id": f"skill:auto_{hash(goal) % 100000}",
                    "name": f"AutoPattern: {goal[:30]}...",
                    "description": f"从成功案例中自动蒸馏的可执行技能: {goal}",
                    "skill_type": SkillType.EXECUTABLE,
                    "content": code_snippet,
                    "source_memory": goal
                })
            else:
                # 生成 LOGIC 类型技能（推理模板）
                patterns.append({
                    "id": f"skill:auto_{hash(goal) % 100000}",
                    "name": f"LogicPattern: {goal[:30]}...",
                    "description": f"从成功案例中蒸馏的逻辑模板: {goal}",
                    "skill_type": SkillType.LOGIC,
                    "content": self._generate_logic_template(text),
                    "source_memory": goal
                })

        return patterns

    def _extract_code_snippet(self, text: str) -> Optional[str]:
        """
        从文本中提取代码片段

        Args:
            text: 输入文本

        Returns:
            提取的代码片段，如果无则返回 None
        """
        # 尝试提取 markdown 代码块
        code_block_pattern = r'```(?:python)?\s*(.*?)```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)

        for match in matches:
            code = match.strip()
            # 验证代码片段是否有意义（非空且长度合理）
            if len(code) >= self.skill_config.min_content_length and len(code) <= self.skill_config.max_content_length:
                return code

        # 尝试提取 "Result:" 或 "Output:" 后面的内容
        result_pattern = r'(?:Result|Output|结果):\s*([^\n]+(?:\n(?!\w+:)[^\n]+)*)'
        result_matches = re.findall(result_pattern, text)

        for result in result_matches:
            result = result.strip()
            if self._looks_like_code(result):
                return result

        return None

    def _looks_like_code(self, text: str) -> bool:
        """
        判断文本是否看起来像代码

        Args:
            text: 待检测文本

        Returns:
            是否像代码
        """
        code_indicators = [
            r'\bdef\s+\w+\s*\(',
            r'\breturn\s+',
            r'\bif\s+\w+\s*:',
            r'\bfor\s+\w+\s+in\s+',
            r'\bwhile\s+',
            r'\bprint\s*\(',
            r'=>',
            r'->',
            r'\{.*:.*\}',
        ]

        for pattern in code_indicators:
            if re.search(pattern, text):
                return True

        return False

    def _generate_logic_template(self, text: str) -> str:
        """
        从文本生成逻辑模板

        Args:
            text: 输入文本

        Returns:
            逻辑模板字符串
        """
        # 提取关键信息
        task_section = text.split("Trace:")[0] if "Trace:" in text else text
        task = task_section.replace("Task:", "").strip()

        # 生成结构化模板
        template = f"""# 逻辑模板: {task}

# 输入参数
params = {{}}

# 业务逻辑
# 1. 解析任务目标: {task}

# 2. 执行推理步骤
result = {{}}

# 3. 返回结果
return result
"""
        return template

    def _validate_skill_content(self, skill_data: Dict) -> bool:
        """
        验证技能内容是否有效

        Args:
            skill_data: 技能数据字典

        Returns:
            是否有效
        """
        content = skill_data.get("content", "")

        # 检查长度
        if len(content) < self.skill_config.min_content_length:
            logger.debug(f"技能内容过短: {len(content)} < {self.skill_config.min_content_length}")
            return False

        if len(content) > self.skill_config.max_content_length:
            logger.debug(f"技能内容过长: {len(content)} > {self.skill_config.max_content_length}")
            return False

        # 对 EXECUTABLE 类型进行 AST 安全检查
        if skill_data.get("skill_type") == SkillType.EXECUTABLE:
            return self._validate_executable_safety(content)

        return True

    def _validate_executable_safety(self, code: str) -> bool:
        """
        验证可执行代码的安全性

        Args:
            code: Python 代码字符串

        Returns:
            是否安全
        """
        try:
            tree = ast.parse(code)

            allowed_modules = self.skill_config.get_allowed_modules()
            forbidden_calls = self.skill_config.get_forbidden_calls()

            for node in ast.walk(tree):
                # 检查导入
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        base = alias.name.split('.')[0]
                        if base not in allowed_modules:
                            logger.warning(f"禁止导入未授权模块: {base}")
                            return False

                # 检查函数调用
                if isinstance(node, ast.Call):
                    name = ""
                    if isinstance(node.func, ast.Name):
                        name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        name = node.func.attr

                    if name in forbidden_calls:
                        logger.warning(f"禁止调用危险函数: {name}")
                        return False

            return True
        except SyntaxError as e:
            logger.warning(f"技能代码语法错误: {e}")
            return False
        except Exception as e:
            logger.warning(f"技能安全验证异常: {e}")
            return False

    def _create_skill_from_data(self, skill_data: Dict) -> Optional[Skill]:
        """
        从技能数据创建 Skill 实例

        Args:
            skill_data: 技能数据字典

        Returns:
            Skill 实例或 None
        """
        try:
            skill = Skill(
                id=skill_data["id"],
                name=skill_data["name"],
                description=skill_data["description"],
                skill_type=skill_data["skill_type"],
                content=skill_data["content"]
            )
            return skill
        except Exception as e:
            logger.error(f"创建技能实例失败: {e}")
            return None

    def distill_skill_from_text(self, text: str, name: str, description: str) -> Optional[Skill]:
        """
        从给定文本直接蒸馏技能（用于手动触发）

        Args:
            text: 包含技能内容的文本
            name: 技能名称
            description: 技能描述

        Returns:
            创建的 Skill 实例或 None
        """
        code_snippet = self._extract_code_snippet(text)

        if code_snippet and self._validate_executable_safety(code_snippet):
            skill_type = SkillType.EXECUTABLE
            content = code_snippet
        else:
            skill_type = SkillType.LOGIC
            content = self._generate_logic_template(text)

        skill = Skill(
            id=f"skill:manual_{hash(name) % 100000}",
            name=name,
            description=description,
            skill_type=skill_type,
            content=content
        )

        if self.registry.register_skill(skill):
            return skill

        return None

    def distill_code_skill(self, code: str, name: str, description: str) -> Tuple[bool, str]:
        """
        手动创建代码技能（带安全验证）

        Args:
            code: Python 代码
            name: 技能名称
            description: 技能描述

        Returns:
            (是否成功, 消息)
        """
        # 安全验证
        if not self._validate_executable_safety(code):
            return False, "代码安全验证未通过"

        # 长度验证
        if len(code) > self.skill_config.max_content_length:
            return False, f"代码过长 (最大 {self.skill_config.max_content_length} 字符)"

        skill = Skill(
            id=f"skill:code_{hash(name) % 100000}",
            name=name,
            description=description,
            skill_type=SkillType.EXECUTABLE,
            content=code
        )

        if self.registry.register_skill(skill):
            return True, f"技能创建成功: {skill.id}"
        else:
            return False, "技能注册失败"

    def list_executable_skills(self) -> List[Dict[str, Any]]:
        """
        列出所有可执行的 EXECUTABLE 类型技能

        Returns:
            技能信息列表
        """
        result = []
        for skill_id, skill in self.registry.skills.items():
            if skill.skill_type == SkillType.EXECUTABLE:
                result.append({
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "content_preview": skill.content[:100] + "..." if len(skill.content) > 100 else skill.content,
                    "usage_count": skill.usage_count,
                    "success_rate": skill.success_rate
                })
        return result
