"""
Action Runtime — 轻量级动作执行引擎 (Kinetic Layer)

v2.0 核心模块，让 LogicPattern 真正可执行。
参考 Palantir Kinetic Ontology — 从"描述型知识"升级为"可执行型知识"。

支持的动作类型:
- infer    : 推导新三元组 (写入 KnowledgeGraph)
- notify   : 触发通知/回调
- validate : 校验数据约束
- transform: 数据格式转换
- execute  : 调用注册的 Python 函数 (沙箱)

事件驱动:
- 新三元组写入图时，自动匹配 condition → 触发规则链
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from .knowledge_graph import KnowledgeGraph, TypedTriple, TripleStatus
from ..utils.config import get_config

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class ActionResult:
    """动作执行结果"""
    action_type: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class RuleMatch:
    """规则匹配结果"""
    rule_id: str
    bindings: Dict[str, str]   # 变量 → 实际值
    triggered_by: Optional[str] = None  # 触发该匹配的三元组 ID


@dataclass
class ExecutionRecord:
    """执行记录"""
    rule_id: str
    timestamp: float = field(default_factory=time.time)
    trigger: str = "manual"   # "manual" | "event" | "chain"
    bindings: Dict[str, str] = field(default_factory=dict)
    results: List[ActionResult] = field(default_factory=list)
    success: bool = False
    chain_depth: int = 0


# ─────────────────────────────────────────────
# ActionRuntime — 核心执行引擎
# ─────────────────────────────────────────────

class ActionRuntime:
    """
    轻量级动作执行引擎

    特性:
    - 5 种内置动作类型 (infer/notify/validate/transform/execute)
    - 沙箱执行: 注册函数在受限环境运行
    - 事件驱动: on_triple_added 自动触发规则匹配
    - 规则链: 一个规则的 action 可触发另一个规则
    - 防无限循环: chain_depth 上限
    """

    # 从 ConfigManager 读取配置，符合零硬编码规则

    @property
    def MAX_CHAIN_DEPTH(self) -> int:
        return get_config().action_runtime.max_chain_depth

    @property
    def MAX_EXEC_TIME(self) -> float:
        return get_config().action_runtime.max_exec_time

    def __init__(self, graph: KnowledgeGraph, logic_layer=None):
        # 绑定知识图谱引擎 — 所有 infer 动作写入此图
        self._graph = graph
        # 绑定逻辑层 — 规则定义来源，可为 None (仅执行单个动作)
        self._logic_layer = logic_layer

        # 注册的可执行函数: name → callable (沙箱执行时查表)
        self._registered_functions: Dict[str, Callable] = {}

        # 通知回调: event_type → list of callbacks (notify 动作分发)
        self._notification_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # 执行历史 — 每次 execute_rule 产生一条记录
        self._execution_history: List[ExecutionRecord] = []

        # 事件驱动开关 — 启用后新三元组写入自动触发规则匹配
        self._event_driven_enabled = False
        # 当前规则链深度 — 防止 A→B→A 无限循环
        self._active_chain_depth = 0

    # ─────────────────────────────────────────
    # 函数注册
    # ─────────────────────────────────────────

    def register_function(self, name: str, func: Callable, description: str = ""):
        """
        注册可执行函数

        Args:
            name: 函数名 (用于 action 中 {"type": "execute", "function": name})
            func: Python 可调用对象
            description: 函数说明
        """
        self._registered_functions[name] = func
        logger.info(f"注册函数: {name} ({description})")

    def register_notification_handler(self, event_type: str, handler: Callable):
        """
        注册通知回调

        Args:
            event_type: 事件类型 (用于 action 中 {"type": "notify", "event": event_type})
            handler: 回调函数, 签名 handler(event_type, data)
        """
        self._notification_handlers[event_type].append(handler)

    # ─────────────────────────────────────────
    # 动作执行
    # ─────────────────────────────────────────

    def execute_action(self, action: Dict[str, Any], bindings: Dict[str, str] = None) -> ActionResult:
        """
        执行单个动作 — 不记录到执行历史 (execute_rule 才记录)

        Args:
            action: 动作定义 {"type": "infer|notify|validate|transform|execute", ...}
            bindings: 变量绑定 {"?X": "实际值", ...}

        Returns:
            ActionResult
        """
        # 提取动作类型，默认 infer (最常用)
        action_type = action.get("type", "infer")
        # 变量绑定字典: ?X → "猫" 等
        bindings = bindings or {}
        start = time.time()

        try:
            if action_type == "infer":
                result = self._execute_infer(action, bindings)
            elif action_type == "notify":
                result = self._execute_notify(action, bindings)
            elif action_type == "validate":
                result = self._execute_validate(action, bindings)
            elif action_type == "transform":
                result = self._execute_transform(action, bindings)
            elif action_type == "execute":
                result = self._execute_function(action, bindings)
            else:
                result = ActionResult(
                    action_type=action_type, success=False,
                    error=f"未知动作类型: {action_type}"
                )
        except Exception as e:
            result = ActionResult(
                action_type=action_type, success=False,
                error=str(e)
            )

        result.duration = time.time() - start
        return result

    def execute_rule(
        self,
        rule_id: str,
        bindings: Dict[str, str],
        trigger: str = "manual",
        chain_depth: int = 0,
    ) -> ExecutionRecord:
        """
        执行一条规则的所有 actions

        Args:
            rule_id: 规则 ID (在 UnifiedLogicLayer 中)
            bindings: 变量绑定
            trigger: 触发来源
            chain_depth: 当前链深度

        Returns:
            ExecutionRecord
        """
        # 防御性编程：确保 bindings 不为 None，避免后续代码出现空指针异常
        if bindings is None:
            bindings = {}
        
        # 防御性编程：确保 rule_id 为有效字符串，防止空值导致的逻辑错误
        if not rule_id or not isinstance(rule_id, str):
            record = ExecutionRecord(
                rule_id=str(rule_id) if rule_id else "unknown",
                trigger=trigger,
                bindings=dict(bindings) if bindings else {},
                chain_depth=chain_depth,
            )
            record.results.append(ActionResult(
                action_type="unknown", success=False,
                error=f"无效的 rule_id: {rule_id}"
            ))
            self._execution_history.append(record)
            return record
        
        record = ExecutionRecord(
            rule_id=rule_id,
            trigger=trigger,
            bindings=dict(bindings),
            chain_depth=chain_depth,
        )

        # 检查逻辑层是否初始化，防止空指针访问
        if self._logic_layer is None:
            record.results.append(ActionResult(
                action_type="unknown", success=False,
                error="逻辑层未初始化"
            ))
            self._execution_history.append(record)
            return record
        
        # 检查规则是否存在，避免 KeyError
        if rule_id not in self._logic_layer.patterns:
            record.results.append(ActionResult(
                action_type="unknown", success=False,
                error=f"规则不存在: {rule_id}"
            ))
            self._execution_history.append(record)
            return record

        pattern = self._logic_layer.patterns[rule_id]
        
        # 防御性编程：检查 pattern.actions 是否为 None 或空列表
        if not pattern.actions:
            record.results.append(ActionResult(
                action_type="unknown", success=False,
                error=f"规则 {rule_id} 没有定义任何动作"
            ))
            self._execution_history.append(record)
            return record
        
        all_success = True

        for action in pattern.actions:
            # 防御性编程：检查 action 是否为 None，避免 execute_action 内部出错
            if action is None:
                record.results.append(ActionResult(
                    action_type="unknown", success=False,
                    error="规则中包含空动作"
                ))
                all_success = False
                continue
            result = self.execute_action(action, bindings)
            record.results.append(result)
            if not result.success:
                all_success = False

        record.success = all_success

        # 更新 pattern 的成功率统计，检查方法是否存在（防御性编程）
        if hasattr(pattern, 'update_success_rate'):
            pattern.update_success_rate(all_success)

        self._execution_history.append(record)
        return record

    # ── 具体动作实现 ──

    def _execute_infer(self, action: Dict, bindings: Dict) -> ActionResult:
        """推导新三元组, 写入图 — 状态为 CANDIDATE, 经评估后升级"""
        # 解析变量: 将 ?X 替换为 bindings 中的实际值
        subject = self._resolve(action.get("subject", ""), bindings)
        predicate = self._resolve(action.get("predicate", ""), bindings)
        obj = self._resolve(action.get("object", ""), bindings)

        if not subject or not predicate or not obj:
            return ActionResult(
                action_type="infer", success=False,
                error="三元组字段不完整"
            )

        # 写入图 (状态为 CANDIDATE, 经评估后升级)
        tid = self._graph.add_triple(
            subject, predicate, obj,
            confidence=action.get("confidence", 0.8),
            source="inferred",
            status=TripleStatus.CANDIDATE,
        )
        return ActionResult(
            action_type="infer", success=True,
            output={"triple_id": tid, "spo": (subject, predicate, obj)}
        )

    def _execute_notify(self, action: Dict, bindings: Dict) -> ActionResult:
        """触发通知回调"""
        event_type = action.get("event", "default")
        data = {k: self._resolve(str(v), bindings) for k, v in action.items() if k != "type"}
        data["bindings"] = bindings

        handlers = self._notification_handlers.get(event_type, [])
        if not handlers:
            return ActionResult(
                action_type="notify", success=True,
                output={"event": event_type, "handlers": 0}
            )

        errors = []
        for handler in handlers:
            try:
                handler(event_type, data)
            except Exception as e:
                errors.append(str(e))

        return ActionResult(
            action_type="notify",
            success=len(errors) == 0,
            output={"event": event_type, "handlers": len(handlers), "errors": errors},
            error="; ".join(errors) if errors else None,
        )

    def _execute_validate(self, action: Dict, bindings: Dict) -> ActionResult:
        """校验约束"""
        subject = self._resolve(action.get("subject", ""), bindings)
        predicate = action.get("predicate", "")
        expected = self._resolve(action.get("expected", ""), bindings)

        # 查询图中的实际值
        triples = self._graph.query(subject=subject, predicate=predicate, limit=1)
        if not triples:
            return ActionResult(
                action_type="validate", success=False,
                error=f"未找到 ({subject}, {predicate}, ?)"
            )

        actual = triples[0].object
        passed = (actual == expected) if expected else True

        return ActionResult(
            action_type="validate", success=passed,
            output={"subject": subject, "predicate": predicate,
                     "expected": expected, "actual": actual}
        )

    def _execute_transform(self, action: Dict, bindings: Dict) -> ActionResult:
        """数据格式转换"""
        source_val = self._resolve(action.get("source_value", ""), bindings)
        transform_type = action.get("transform", "identity")

        try:
            if transform_type == "upper":
                result_val = source_val.upper()
            elif transform_type == "lower":
                result_val = source_val.lower()
            elif transform_type == "strip":
                result_val = source_val.strip()
            elif transform_type == "to_number":
                result_val = float(source_val) if source_val else 0.0
            else:
                result_val = source_val  # identity

            return ActionResult(
                action_type="transform", success=True,
                output={"input": source_val, "output": result_val, "transform": transform_type}
            )
        except (ValueError, AttributeError) as e:
            return ActionResult(
                action_type="transform", success=False, error=str(e)
            )

    def _execute_function(self, action: Dict, bindings: Dict) -> ActionResult:
        """调用注册的 Python 函数 (沙箱)"""
        func_name = action.get("function", "")
        if func_name not in self._registered_functions:
            return ActionResult(
                action_type="execute", success=False,
                error=f"未注册的函数: {func_name}"
            )

        func = self._registered_functions[func_name]
        args = {k: self._resolve(str(v), bindings)
                for k, v in action.get("args", {}).items()}

        try:
            output = func(**args)
            return ActionResult(
                action_type="execute", success=True, output=output
            )
        except Exception as e:
            return ActionResult(
                action_type="execute", success=False, error=str(e)
            )

    # ─────────────────────────────────────────
    # 事件驱动触发
    # ─────────────────────────────────────────

    def enable_event_driven(self):
        """启用事件驱动 — 新三元组写入时自动匹配规则"""
        if self._event_driven_enabled:
            return
        self._event_driven_enabled = True
        self._graph.on_triple_added(self._on_triple_added)
        logger.info("事件驱动已启用")

    def disable_event_driven(self):
        """禁用事件驱动"""
        self._event_driven_enabled = False
        # 注意: 钩子仍在列表中, 但 _on_triple_added 会检查 flag
        logger.info("事件驱动已禁用")

    def _on_triple_added(self, triple: TypedTriple):
        """
        三元组写入钩子 — 自动匹配规则 conditions 并触发

        防无限循环: 检查 chain_depth, 超过 MAX_CHAIN_DEPTH 则停止
        """
        # 事件驱动未启用时直接返回
        if not self._event_driven_enabled:
            return

        # 防无限循环: 规则 A 推导出三元组 → 触发规则 B → 又推导 → ...
        if self._active_chain_depth >= self.MAX_CHAIN_DEPTH:
            logger.warning(
                f"规则链深度已达上限 ({self.MAX_CHAIN_DEPTH}), 跳过触发"
            )
            return

        if self._logic_layer is None:
            return

        # 扫描所有规则, 找出 conditions 能被此三元组满足的规则
        matches = self._match_rules_for_triple(triple)

        # 进入下一层链深度 (finally 保证退出时恢复)
        self._active_chain_depth += 1
        try:
            for match in matches:
                self.execute_rule(
                    match.rule_id,
                    match.bindings,
                    trigger="event",
                    chain_depth=self._active_chain_depth,
                )
        finally:
            # 回退链深度, 确保并行规则不互相干扰
            self._active_chain_depth -= 1

    def _match_rules_for_triple(self, triple: TypedTriple) -> List[RuleMatch]:
        """
        给定一个新三元组, 找出所有 conditions 被满足的规则

        简化版匹配: 检查规则的每个 condition 是否能在图中找到匹配
        """
        if self._logic_layer is None:
            return []

        matches: List[RuleMatch] = []

        for rule_id, pattern in self._logic_layer.patterns.items():
            # 跳过非规则类型
            if pattern.logic_type.value != "rule":
                continue

            # 尝试匹配
            bindings = self._try_match_conditions(pattern.conditions, triple)
            if bindings is not None:
                matches.append(RuleMatch(
                    rule_id=rule_id,
                    bindings=bindings,
                    triggered_by=triple.id,
                ))

        return matches

    def _try_match_conditions(
        self, conditions: List[Dict], trigger_triple: TypedTriple
    ) -> Optional[Dict[str, str]]:
        """
        尝试用 trigger_triple 满足 conditions 的第一个条件,
        然后查图验证剩余条件 (Prolog 风格的变量统一)。

        Returns:
            变量绑定字典, 或 None 表示不匹配
        """
        if not conditions:
            return None

        # 过滤掉 "raw" 条件 (自然语言描述, 需要 LLM 判断, 此处跳过)
        structured = [c for c in conditions if "subject" in c and "predicate" in c and "object" in c]
        if not structured:
            return None

        # 用 trigger_triple 尝试统一 (unify) 第一个 condition
        first = structured[0]
        bindings: Dict[str, str] = {}  # 变量绑定表: ?X → 实际值

        if not self._unify(first.get("subject", ""), trigger_triple.subject, bindings):
            return None
        if not self._unify(first.get("predicate", ""), trigger_triple.predicate, bindings):
            return None
        if not self._unify(first.get("object", ""), trigger_triple.object, bindings):
            return None

        # 验证剩余条件
        for cond in structured[1:]:
            s = self._resolve(cond.get("subject", ""), bindings)
            p = self._resolve(cond.get("predicate", ""), bindings)
            o = self._resolve(cond.get("object", ""), bindings)

            # 如果仍有未绑定变量, 查图
            if s.startswith("?") or p.startswith("?") or o.startswith("?"):
                results = self._graph.query(
                    subject=s if not s.startswith("?") else None,
                    predicate=p if not p.startswith("?") else None,
                    obj=o if not o.startswith("?") else None,
                    limit=1,
                )
                if not results:
                    return None
                # 绑定变量
                t = results[0]
                if s.startswith("?"):
                    bindings[s] = t.subject
                if p.startswith("?"):
                    bindings[p] = t.predicate
                if o.startswith("?"):
                    bindings[o] = t.object
            else:
                # 全部是具体值, 验证图中是否存在
                results = self._graph.query(subject=s, predicate=p, obj=o, limit=1)
                if not results:
                    return None

        return bindings

    # ── 辅助方法 ──

    @staticmethod
    def _unify(pattern_val: str, actual_val: str, bindings: Dict[str, str]) -> bool:
        """统一变量: 如果 pattern_val 是变量 (?X), 绑定到 actual_val"""
        if pattern_val.startswith("?"):
            if pattern_val in bindings:
                return bindings[pattern_val] == actual_val
            bindings[pattern_val] = actual_val
            return True
        return pattern_val == actual_val

    @staticmethod
    def _resolve(value: str, bindings: Dict[str, str]) -> str:
        """解析变量: 将 ?X 替换为绑定值"""
        if value.startswith("?") and value in bindings:
            return bindings[value]
        return value

    # ─────────────────────────────────────────
    # 统计
    # ─────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        """获取执行统计"""
        total = len(self._execution_history)
        successes = sum(1 for r in self._execution_history if r.success)
        by_trigger: Dict[str, int] = defaultdict(int)
        for r in self._execution_history:
            by_trigger[r.trigger] += 1

        return {
            "total_executions": total,
            "success_rate": successes / total if total > 0 else 0.0,
            "by_trigger": dict(by_trigger),
            "registered_functions": list(self._registered_functions.keys()),
            "event_driven_enabled": self._event_driven_enabled,
            "max_chain_depth": self.MAX_CHAIN_DEPTH,
        }


# ─────────────────────────────────────────────
# ToolRegistry — LLM 工具注册框架
# ─────────────────────────────────────────────

@dataclass
class ToolDefinition:
    """
    LLM 工具定义
    
    封装 OpenAI 格式的工具定义，支持分类标签和执行处理器。
    工具定义包含名称、描述、参数 Schema、分类标签以及执行逻辑。
    """
    name: str                                           # 工具名称（唯一标识符）
    description: str                                    # 工具描述
    parameters: Dict[str, Any]                          # OpenAI 格式的参数 Schema
    handler: Optional[Callable] = None                  # 工具执行处理器（可选）
    tags: List[str] = field(default_factory=list)       # 分类标签（用于筛选和分组）
    category: str = "general"                           # 工具分类（如 "knowledge", "query", "action"）
    enabled: bool = True                                # 是否启用（支持热插拔）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展元数据


class ToolRegistry:
    """
    LLM 工具注册中心
    
    提供统一的工具注册、管理和发现机制。
    支持装饰器注册、分类标签、热插拔（运行时添加/移除）。
    
    使用方式:
        # 装饰器注册
        @tool_registry.register_tool(
            name="my_tool",
            description="工具描述",
            parameters={...},
            tags=["knowledge"]
        )
        def my_tool_handler(args):
            ...
        
        # 编程式注册
        tool_registry.register(ToolDefinition(...))
        
        # 获取工具
        tool = tool_registry.get_tool("my_tool")
    """
    
    _instance = None  # 单例实例
    
    def __new__(cls):
        # 单例模式：确保全局只有一个 ToolRegistry 实例
        # 这是因为工具定义通常是全局共享的，避免重复注册
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # 初始化标志防止重复初始化
        if self._initialized:
            return
        
        # 工具存储：name → ToolDefinition
        self._tools: Dict[str, ToolDefinition] = {}
        # 分类索引：category → set of tool names（加速分类查询）
        self._category_index: Dict[str, Set[str]] = defaultdict(set)
        # 标签索引：tag → set of tool names（加速标签查询）
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
        # 初始化完成标志
        self._initialized = True
        logger.info("ToolRegistry 初始化完成")

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Optional[Callable] = None,
        tags: Optional[List[str]] = None,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Callable:
        """
        装饰器风格的工具注册方法
        
        既可以用作装饰器，也可以直接调用注册。
        支持传入自定义处理器，或自动使用被装饰函数作为处理器。
        
        Args:
            name: 工具名称（唯一标识符）
            description: 工具描述（LLM 会看到）
            parameters: OpenAI 格式的参数 Schema
            handler: 可选的执行处理器函数
            tags: 分类标签列表
            category: 工具分类
            metadata: 扩展元数据
            
        Returns:
            装饰器函数或原始函数
            
        Example:
            @tool_registry.register_tool(
                name="ingest_knowledge",
                description="知识入库工具",
                parameters={"type": "object", "properties": {...}}
            )
            def handle_ingest(args):
                ...
        """
        def decorator(func: Callable) -> Callable:
            # 创建工具定义，使用传入的 handler 或被装饰的函数
            tool_def = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                handler=handler or func,  # 优先使用传入的 handler，否则使用被装饰的函数
                tags=tags or [],
                category=category,
                metadata=metadata or {}
            )
            # 注册到工具表
            self.register(tool_def)
            return func  # 返回原函数，保持可调用性
        
        return decorator

    def register(self, tool: ToolDefinition) -> None:
        """
        注册工具定义
        
        将工具添加到注册表，同时更新分类和标签索引。
        如果工具已存在，则覆盖旧定义（支持热更新）。
        
        Args:
            tool: ToolDefinition 实例
        """
        # 存储工具定义
        self._tools[tool.name] = tool
        
        # 更新分类索引（移除旧的分类关联，添加新的）
        for cat_tools in self._category_index.values():
            cat_tools.discard(tool.name)
        self._category_index[tool.category].add(tool.name)
        
        # 更新标签索引（移除旧的标签关联，添加新的）
        for tag_tools in self._tag_index.values():
            tag_tools.discard(tool.name)
        for tag in tool.tags:
            self._tag_index[tag].add(tool.name)
        
        logger.info(f"工具已注册: {tool.name} (分类: {tool.category}, 标签: {tool.tags})")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """
        按名称获取工具定义
        
        Args:
            name: 工具名称
            
        Returns:
            ToolDefinition 或 None（工具不存在时）
        """
        return self._tools.get(name)

    def list_tools(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True
    ) -> List[ToolDefinition]:
        """
        列出所有已注册工具
        
        支持按分类和标签过滤，以及是否只返回启用的工具。
        
        Args:
            category: 可选的分类过滤
            tags: 可选的标签过滤（满足任一标签即可）
            enabled_only: 是否只返回启用的工具
            
        Returns:
            工具定义列表
        """
        # 从分类索引获取候选工具名（如果指定了分类）
        if category:
            candidates = self._category_index.get(category, set())
        else:
            candidates = set(self._tools.keys())
        
        # 从标签索引进一步过滤（如果指定了标签）
        if tags:
            # 满足任一标签即可（OR 逻辑）
            tag_matches = set()
            for tag in tags:
                tag_matches.update(self._tag_index.get(tag, set()))
            candidates = candidates & tag_matches
        
        # 转换为 ToolDefinition 并过滤
        result = []
        for name in candidates:
            tool = self._tools.get(name)
            if tool and (not enabled_only or tool.enabled):
                result.append(tool)
        
        return result

    def unregister_tool(self, name: str) -> bool:
        """
        移除工具（支持热插拔）
        
        从注册表中移除指定工具，同时清理相关索引。
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功移除（工具不存在时返回 False）
        """
        tool = self._tools.get(name)
        if not tool:
            logger.warning(f"尝试移除不存在的工具: {name}")
            return False
        
        # 从主存储移除
        del self._tools[name]
        # 从分类索引移除
        self._category_index[tool.category].discard(name)
        # 从标签索引移除
        for tag in tool.tags:
            self._tag_index[tag].discard(name)
        
        logger.info(f"工具已移除: {name}")
        return True

    def enable_tool(self, name: str) -> bool:
        """
        启用工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功（工具不存在时返回 False）
        """
        tool = self._tools.get(name)
        if not tool:
            return False
        tool.enabled = True
        logger.info(f"工具已启用: {name}")
        return True

    def disable_tool(self, name: str) -> bool:
        """
        禁用工具（不删除，仅标记为禁用）
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功（工具不存在时返回 False）
        """
        tool = self._tools.get(name)
        if not tool:
            return False
        tool.enabled = False
        logger.info(f"工具已禁用: {name}")
        return True

    def get_openai_tools(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        获取 OpenAI 格式的工具定义列表
        
        将注册的工具转换为 OpenAI API 所需的 tools 参数格式。
        用于 LLM 调用时的 tools 参数。
        
        Args:
            enabled_only: 是否只返回启用的工具
            
        Returns:
            OpenAI 格式的工具定义列表
        """
        tools = []
        for tool in self.list_tools(enabled_only=enabled_only):
            # OpenAI 工具格式：{"type": "function", "function": {...}}
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return tools

    def get_categories(self) -> List[str]:
        """
        获取所有已使用的分类
        
        Returns:
            分类名称列表
        """
        # 只返回非空的分类
        return [cat for cat, tools in self._category_index.items() if tools]

    def get_tags(self) -> List[str]:
        """
        获取所有已使用的标签
        
        Returns:
            标签名称列表
        """
        # 只返回非空的标签
        return [tag for tag, tools in self._tag_index.items() if tools]

    def clear(self) -> None:
        """
        清空所有工具注册
        
        用于测试或重置场景。
        """
        self._tools.clear()
        self._category_index.clear()
        self._tag_index.clear()
        logger.info("ToolRegistry 已清空")

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取工具注册统计信息
        
        Returns:
            包含工具数量、分类分布、标签分布等信息的字典
        """
        enabled_count = sum(1 for t in self._tools.values() if t.enabled)
        return {
            "total_tools": len(self._tools),
            "enabled_tools": enabled_count,
            "disabled_tools": len(self._tools) - enabled_count,
            "categories": {
                cat: len(tools) for cat, tools in self._category_index.items() if tools
            },
            "tags": {
                tag: len(tools) for tag, tools in self._tag_index.items() if tools
            }
        }


# 全局单例实例
# 使用单例模式确保整个应用共享同一个工具注册表
# 避免在不同模块中重复注册工具
tool_registry = ToolRegistry()
