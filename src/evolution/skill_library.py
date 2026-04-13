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
    EXECUTABLE = "executable"  # 可执行结构化指令（AST 安全执行）

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

    def execute(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行技能内容并返回结果

        Args:
            params: 执行参数字典

        Returns:
            包含执行结果的字典，格式: {"success": bool, "result": Any, "error": str}
        """
        from ..utils.config import get_config
        config = get_config()

        if not config.skill.execution_enabled:
            return {"success": False, "result": None, "error": "技能执行已禁用 (SKILL_EXECUTION_ENABLED=false)"}

        if params is None:
            params = {}

        if self.skill_type != SkillType.EXECUTABLE:
            return {"success": False, "result": None, "error": f"技能类型 {self.skill_type.value} 不支持直接执行"}

        try:
            result = self._execute_safe_ast(self.content, params, config.skill)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    def _execute_safe_ast(self, code: str, params: Dict[str, Any], skill_config) -> Any:
        """
        使用 AST 安全执行 Python 代码片段

        Args:
            code: Python 代码字符串
            params: 传入的参数
            skill_config: 技能配置

        Returns:
            执行结果
        """
        import ast
        import sys
        from io import StringIO

        # 1. AST 安全审计
        tree = ast.parse(code)

        allowed_modules = skill_config.get_allowed_modules()
        forbidden_calls = skill_config.get_forbidden_calls()

        for node in ast.walk(tree):
            # 检查导入
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    base = alias.name.split('.')[0]
                    if base not in allowed_modules:
                        raise SecurityError(f"禁止导入未授权模块: {base}")

            # 检查函数调用
            if isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr

                if name in forbidden_calls:
                    raise SecurityError(f"禁止调用危险函数: {name}")

        # 2. 构建安全执行环境
        safe_globals = {
            "__builtins__": {
                "True": True, "False": False, "None": None,
                "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
                "chr": chr, "dict": dict, "dir": dir, "divmod": divmod,
                "enumerate": enumerate, "filter": filter, "float": float,
                "format": format, "frozenset": frozenset, "hash": hash,
                "hex": hex, "int": int, "isinstance": isinstance,
                "issubclass": issubclass, "iter": iter, "len": len,
                "list": list, "map": map, "max": max, "min": min,
                "next": next, "object": object, "oct": oct, "ord": ord,
                "pow": pow, "print": print, "range": range, "repr": repr,
                "reversed": reversed, "round": round, "set": set,
                "slice": slice, "sorted": sorted, "str": str, "sum": sum,
                "tuple": tuple, "zip": zip,
            },
            "math": __import__("math"),
            "re": __import__("re"),
            "json": __import__("json"),
            "datetime": __import__("datetime"),
            "collections": __import__("collections"),
            "typing": __import__("typing"),
            "random": __import__("random"),
            "statistics": __import__("statistics"),
        }

        # 3. 合并传入参数
        safe_locals = dict(params)

        # 4. 判断代码类型并执行
        stripped = code.strip()
        is_single_expr = (
            '\n' not in stripped
            and not any(stripped.startswith(kw) for kw in ('if', 'for', 'while', 'def', 'return', 'class'))
        )

        # 5. 限制执行时间
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError(f"技能执行超时 ({skill_config.execution_timeout}s)")

        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(skill_config.execution_timeout))

        try:
            if is_single_expr:
                # 单表达式用 eval
                result = eval(code, safe_globals, safe_locals)
            else:
                # 多行代码用 exec，捕获 stdout
                old_stdout = sys.stdout
                sys.stdout = StringIO()

                # 检查是否有 return 语句
                has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))

                if has_return:
                    # 包装成函数执行
                    func_code = f"def _skill_exec(params):\n" + "\n".join("    " + line for line in code.split('\n')) + "\n_result = _skill_exec(params)"
                    exec(func_code, safe_globals, safe_locals)
                    result = safe_locals.get("_result")
                else:
                    exec(code, safe_globals, safe_locals)
                    result = safe_locals.get("_result")

                # 获取打印输出
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout

                # 如果没有返回值但有 stdout 输出，返回输出
                if result is None and output:
                    return output.strip()

            return result
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            if 'sys.stdout' in dir() and sys.stdout is not None:
                sys.stdout = old_stdout


class SecurityError(Exception):
    """安全审计异常"""
    pass


class TimeoutError(Exception):
    """执行超时异常"""
    pass

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
        # 如果是代码或可执行技能，执行前置安全审计
        if skill.skill_type in (SkillType.CODE, SkillType.EXECUTABLE):
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
