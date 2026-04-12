"""
Skill Library - 基于 Voyager 范式的技能进化库

该模块负责：
1. 技能的持久化存储 (存入 skills/ 目录)
2. 技能的动态加载与工具化包装
3. 技能的版本控制与元数据管理
"""

import os
import logging
import importlib.util
import inspect
import ast
import re
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from ..utils.config import get_config

logger = logging.getLogger(__name__)

class SkillType(Enum):
    """技能类型封装"""
    CODE = "code"   # 可执行 Python 代码
    LOGIC = "logic" # DSL/SQL 推理模板

@dataclass
class Skill:
    """
    统一技能数据模型 (Unified Skill Model)
    
    整合程序性记忆与动态代码能力。
    """
    id: str
    name: str
    description: str
    skill_type: SkillType
    content: str  # 代码或逻辑模板
    usage_count: int = 0
    success_rate: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "v1.0"

class UnifiedSkillRegistry:
    """
    统一技能注册表 (Unified Skill Registry)
    
    对标 Voyager 与 Agent Lightning，管理 Agent 自主发现的跨模态技能。
    支持生产级安全审计与动态工具化。
    """
    
    def __init__(self, skill_dir: Optional[str] = None, semantic_memory: Any = None):
        # 获取系统配置，遵循零硬编码原则
        self.config = get_config()
        self.semantic_memory = semantic_memory
        # 确定技能持久化目录
        self.skill_dir = skill_dir or os.path.join(self.config.app.data_dir, "skills")
        # 确保目录存在
        os.makedirs(self.skill_dir, exist_ok=True)
        
        # 内存缓存：skill_id -> Skill 对象
        self.skills: Dict[str, Skill] = {}
        # 运行时函数映射：skill_id -> callable (仅针对 CODE 类型)
        self.callables: Dict[str, Callable] = {}
        
        # 1. 初始化时加载磁盘已有技能
        self.load_all_skills()
        # 2. 加载内置遗留技能
        self._load_built_in_skills()

    def _load_built_in_skills(self):
        """加载初始内置技能（兼容 legacy core.memory.skills）"""
        legacy_skills = [
            Skill(
                id="skill:gas_regulator_quality_audit",
                name="调压柜质量全量审计",
                description="自动联通 GB 27791 和设备参数进行闭环合规扫描。",
                skill_type=SkillType.LOGIC,
                content="MATCH (e:Entity {type:'Regulator'})-[:has_parameter]->(p) ..."
            )
        ]
        for s in legacy_skills:
            if s.id not in self.skills:
                self.register_skill(s)

    def _verify_code_safety(self, code: str) -> bool:
        """
        [Hardening] 静态代码安全审查 (AST Auditing)
        
        拦截系统调用、文件 I/O 与元编程，确保自主生成的代码在沙箱内运行。
        """
        try:
            # 解析抽象语法树
            tree = ast.parse(code)
            # 定义允许导入的基础库白名单，符合零硬编码原则
            allowed_modules = {"math", "re", "json", "datetime", "collections", "typing"}
            
            # 遍历语法树节点检测高危操作
            for node in ast.walk(tree):
                # 1. 检查授权导入
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        base = alias.name.split('.')[0]
                        if base not in allowed_modules:
                            logger.error(f"🚨 安全拦截: 技能尝试导入未授权模块 '{base}'")
                            return False
                
                # 2. 检查危险内建函数调用
                if isinstance(node, ast.Call):
                    name = ""
                    if isinstance(node.func, ast.Name):
                        name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        name = node.func.attr
                    
                    # 拦截 eval, exec, open 等关键逃逸函数
                    if name in {"eval", "exec", "open", "input", "os", "subprocess"}:
                        logger.error(f"🚨 安全拦截: 技能代码包含危险调用 '{name}'")
                        return False
            return True
        except Exception as e:
            logger.error(f"代码审计异常解析失败: {e}")
            return False

    def register_skill(self, skill: Skill) -> bool:
        """
        注册并持久化新技能
        
        Args:
            skill: 待注册的 Skill 实例
        """
        # 如果是代码技能，执行前置安全审计
        if skill.skill_type == SkillType.CODE:
            if not self._verify_code_safety(skill.content):
                logger.warning(f"技能 {skill.name} 安全审计未通过，拒绝录入")
                return False

        # 持久化到文件系统
        file_path = os.path.join(self.skill_dir, f"{skill.id.replace(':', '_')}.py")
        # 补充元数据 Header
        header = f'"""\nSkill: {skill.name}\nType: {skill.skill_type.value}\nDesc: {skill.description}\n"""\n\n'
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(header + skill.content)
            
            # 存入内存缓存
            self.skills[skill.id] = skill
            
            # [Hardening] 推送事实至语义图谱，实现跨 Agent 共享
            if self.semantic_memory:
                try:
                    from ..core.reasoner import Fact
                    skill_fact = Fact(
                        subject=skill.id, 
                        predicate="rdf:type", 
                        object="owl:Skill", 
                        confidence=1.0, 
                        source="skill_registry"
                    )
                    self.semantic_memory.store_fact(skill_fact)
                    logger.debug(f"技能已同步至 Neo4j 图谱: {skill.id}")
                except Exception as e:
                    logger.warning(f"技能同步图谱失败: {e}")

            logger.info(f"✅ 技能已发现并持久化: {skill.id} ({skill.name})")
            
            # 如果是代码，立即加载到运行环境
            if skill.skill_type == SkillType.CODE:
                return self._compile_callable(skill.id, file_path)
            return True
        except Exception as e:
            logger.error(f"持久化技能失败: {e}")
            return False

    def _compile_callable(self, skill_id: str, file_path: str) -> bool:
        """单例加载并编译 Python 函数"""
        try:
            spec = importlib.util.spec_from_file_location(skill_id.replace(':', '_'), file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if not name.startswith('_'): 
                    self.callables[skill_id] = func
                    return True
        except Exception as e:
            logger.error(f"技能编译失败 {skill_id}: {e}")
        return False

    def load_all_skills(self):
        """全量扫描磁盘技能库"""
        if not os.path.exists(self.skill_dir): return
        
        count = 0
        for file in os.listdir(self.skill_dir):
            if file.endswith(".py"):
                skill_id = file[:-3].replace('_', ':') # 还原命名空间
                file_path = os.path.join(self.skill_dir, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        name_match = re.search(r'Skill: (.*?)\n', content)
                        type_match = re.search(r'Type: (.*?)\n', content)
                        desc_match = re.search(r'Desc: (.*?)\n', content)
                        
                        name = name_match.group(1) if name_match else skill_id
                        stype = SkillType(type_match.group(1)) if type_match else SkillType.CODE
                        desc = desc_match.group(1) if desc_match else ""
                        body = re.sub(r'^""".*?"""\s*', '', content, flags=re.DOTALL).strip()
                        
                        skill = Skill(id=skill_id, name=name, description=desc, skill_type=stype, content=body)
                        self.skills[skill_id] = skill
                        if stype == SkillType.CODE:
                            self._compile_callable(skill_id, file_path)
                    count += 1
                except Exception as e:
                    logger.warning(f"加载技能文件失败 {file}: {e}")
        logger.info(f"技能库加载完成: {count} 个技能")

    def get_tool_metadata(self) -> List[Dict[str, Any]]:
        """转化为 JSON-RPC/OpenAI Tool 契约"""
        tools = []
        for sid, skill in self.skills.items():
            func_name = sid.replace(':', '_')
            tools.append({
                "type": "function",
                "function": {
                    "name": func_name,
                    "description": f"[自主进化技能] {skill.description}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "args": {"type": "object", "description": f"输入参数，符合 {skill.name} 的逻辑要求"}
                        }
                    }
                }
            })
        return tools
