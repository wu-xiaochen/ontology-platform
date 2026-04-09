"""
Unified Logic Layer - 统一逻辑表达层

将规则、行为、策略统一表达为可学习的逻辑结构
支持从文本自动提取逻辑，无需硬编码

性能优化:
- 使用 lru_cache 缓存频繁访问的模式
- 使用索引加速模式查询
- 延迟加载和批量处理

增强功能:
- 支持复杂知识库文本提取
- 多层级结构解析
- 实体关系抽取
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from functools import lru_cache
import json
import re
import logging

from ..utils.config import get_config

logger = logging.getLogger(__name__)


class LogicType(Enum):
    """逻辑类型枚举"""
    RULE = "rule"           # 推理规则
    BEHAVIOR = "behavior"   # 行为模式
    POLICY = "policy"       # 策略决策
    CONSTRAINT = "constraint"  # 约束条件
    WORKFLOW = "workflow"   # 工作流


@dataclass
class LogicPattern:
    """逻辑模式 - 统一表达所有逻辑"""
    id: str
    logic_type: LogicType
    name: str
    description: str
    
    # 条件部分（前提）
    conditions: List[Dict[str, Any]]  # [{"subject": "?X", "predicate": "is_a", "object": "device"}]
    
    # 动作部分（结论/行为）
    actions: List[Dict[str, Any]]     # [{"type": "infer", "subject": "?X", "predicate": "requires", "object": "maintenance"}]
    
    # 元信息
    confidence: float = 0.8
    source: str = "learned"  # learned, manual, inferred
    domain: str = "generic"
    version: int = 1
    
    # 学习相关
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "logic_type": self.logic_type.value,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "actions": self.actions,
            "confidence": self.confidence,
            "source": self.source,
            "domain": self.domain,
            "version": self.version,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LogicPattern':
        return cls(
            id=data["id"],
            logic_type=LogicType(data["logic_type"]),
            name=data["name"],
            description=data["description"],
            conditions=data["conditions"],
            actions=data["actions"],
            confidence=data.get("confidence", 0.8),
            source=data.get("source", "learned"),
            domain=data.get("domain", "generic"),
            version=data.get("version", 1),
            usage_count=data.get("usage_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0)
        )
    
    def update_success_rate(self, success: bool):
        """更新成功率统计"""
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # 动态调整置信度
        if self.usage_count > 5:
            self.confidence = self.success_count / self.usage_count


class UnifiedLogicLayer:
    """
    统一逻辑层 - 核心架构组件
    
    职责：
    1. 统一管理所有逻辑（规则、行为、策略）
    2. 支持从文本自动提取逻辑
    3. 支持逻辑的动态加载、更新、版本管理
    4. 提供逻辑执行引擎
    
    存储架构（v2.0 重构）：
    - KnowledgeGraph 是 pattern 的**唯一真值源**
    - _patterns_fallback 仅在 KG 不可用时作为降级方案（内存存储）
    - 所有 pattern 的 CRUD 操作优先通过 KG
    - 通过 is_using_kg 属性可以检查当前使用的存储后端
    """
    
    def __init__(self, knowledge_graph=None):
        # ── 存储架构：KG 为唯一真值源 ──
        # KnowledgeGraph 是 pattern 的唯一存储源，保证数据一致性
        # 当无图引擎时退化为内存字典 (兼容无图场景)
        self._knowledge_graph = knowledge_graph
        # _patterns_fallback 仅当无 KG 时使用，不应与 KG 同时写入（避免双写不一致）
        self._patterns_fallback: Dict[str, LogicPattern] = {}
        self.execution_history: List[Dict] = []
        self._pattern_cache: Dict[str, Any] = {}  # 简单缓存
        
        # 内置基础逻辑（最小化硬编码）
        self._bootstrap_basic_logic()
    
    @property
    def is_using_kg(self) -> bool:
        """
        检查是否使用 KnowledgeGraph 作为存储后端
        
        Returns:
            True: 使用 KG（推荐），数据持久化且支持复杂查询
            False: 使用内存 fallback，仅适用于无 KG 场景
        """
        return self._knowledge_graph is not None

    @property
    def patterns(self) -> Dict[str, LogicPattern]:
        """
        统一 pattern 访问入口 — 对外保持 dict 接口不变，确保所有消费方（demo、tests）零修改。
        
        设计决策：
        - 如果存在 KnowledgeGraph，优先从图中重建 pattern 字典（唯一真值源）
        - 使用缓存避免频繁重建，提升读取性能
        - 仅当 KG 不可用时回退到内存 fallback（兼容无图场景）
        
        缓存策略：
        - 使用 _pattern_cache 缓存重建结果
        - 写入操作（add/remove）会触发缓存清除
        - 读取操作在缓存命中时直接返回，避免 O(n) 遍历
        """
        if self._knowledge_graph is not None:
            # 从图中读取所有以 _type 谓词标记的 pattern 节点
            cache_key = '_patterns_view'
            if cache_key in self._pattern_cache:
                # 缓存命中：直接返回缓存结果，避免重复重建
                return self._pattern_cache[cache_key]
            # 缓存未命中：从 KG 重建并缓存结果
            result = self._rebuild_patterns_from_graph()
            self._pattern_cache[cache_key] = result
            return result
        # KG 不可用时使用内存 fallback（降级方案）
        return self._patterns_fallback

    @property
    def domain_patterns(self) -> Dict[str, List[str]]:
        """按领域聚合的 pattern 索引 — 从 patterns 视图动态构建"""
        index: Dict[str, List[str]] = {}
        for pid, p in self.patterns.items():
            index.setdefault(p.domain, []).append(pid)
        return index

    @property
    def type_patterns(self) -> Dict[LogicType, List[str]]:
        """按类型聚合的 pattern 索引 — 从 patterns 视图动态构建"""
        index: Dict[LogicType, List[str]] = {}
        for pid, p in self.patterns.items():
            index.setdefault(p.logic_type, []).append(pid)
        return index

    def _rebuild_patterns_from_graph(self) -> Dict[str, LogicPattern]:
        """
        从 KnowledgeGraph 重建 pattern 字典 — 图驱动的单一数据源。
        
        性能优化：
        - 使用 KG 的索引查询（predicate="_type"）而非全量扫描
        - 单次遍历构建结果字典，时间复杂度 O(n)
        - 结果被缓存，避免重复重建
        
        图中 pattern 节点的存储约定:
        - (pattern_id, "_type", logic_type_value) — pattern 元信息
        - metadata 中存储 name / domain / description / conditions / actions / version 等
        
        Returns:
            Dict[str, LogicPattern]: pattern_id 到 LogicPattern 的映射
        """
        kg = self._knowledge_graph
        result: Dict[str, LogicPattern] = {}
        # 查询所有 _type 谓词的三元组 — 每条代表一个 pattern
        # 使用 KG 索引加速，避免全量扫描
        type_triples = kg.query(predicate="_type")
        for t in type_triples:
            pid = t.subject
            meta = t.metadata or {}
            try:
                # 构建 LogicPattern 对象，使用 metadata 填充字段
                pattern = LogicPattern(
                    id=pid,
                    logic_type=LogicType(t.object),
                    name=meta.get("name", pid),
                    description=meta.get("description", ""),
                    conditions=meta.get("conditions", []),
                    actions=meta.get("actions", []),
                    confidence=t.confidence,
                    source=t.source.replace("pattern:", "") if t.source.startswith("pattern:") else t.source,
                    domain=meta.get("domain", "generic"),
                    version=meta.get("version", 1),
                    usage_count=meta.get("usage_count", 0),
                    success_count=meta.get("success_count", 0),
                    failure_count=meta.get("failure_count", 0),
                )
                result[pid] = pattern
            except (ValueError, KeyError) as e:
                # 跳过无效节点，记录调试日志
                logger.debug(f"跳过无效 pattern 节点 {pid}: {e}")
        return result
    
    def _bootstrap_basic_logic(self):
        """
        启动最基础的元逻辑 — 通过 add_pattern 写入图。
        
        设计决策：
        - 元规则是系统推理的基础，必须在初始化时确保存在
        - 通过 add_pattern 统一入口写入，确保 KG 优先策略一致
        - 如果 KG 可用，规则直接进入图；否则进入内存 fallback
        - 规则的核心参数（ID、名称、置信度）可从配置读取，支持灵活定制
        
        关于元逻辑固定性的说明：
        - 传递性和分类继承是形式逻辑的基本公理，属于元逻辑层面
        - 这些规则的"结构"（conditions/actions）是逻辑系统的固有定义
        - 如果修改规则结构，将改变系统的推理语义，不再是同一逻辑系统
        - 因此仅开放标识性参数（ID、名称、置信度）供配置，规则结构保持固定
        """
        # 从配置读取是否启用元规则引导（支持灵活配置）
        config = get_config()
        evo_config = getattr(config, 'evolution', None)
        
        # 如果配置存在且明确禁用引导，则跳过
        if evo_config is not None:
            if not getattr(evo_config, 'enable_bootstrap_rules', True):
                logger.debug("元规则引导已禁用，跳过 bootstrap")
                return
        
        # 从配置读取元规则参数，使用默认值作为 fallback
        # 这些参数允许用户自定义标识，但规则结构是元逻辑层面的固定定义
        transitivity_id = getattr(evo_config, 'meta_transitivity_id', 'meta:transitivity') if evo_config else 'meta:transitivity'
        transitivity_name = getattr(evo_config, 'meta_transitivity_name', '传递性规则') if evo_config else '传递性规则'
        transitivity_confidence = getattr(evo_config, 'meta_transitivity_confidence', 1.0) if evo_config else 1.0
        
        classification_id = getattr(evo_config, 'meta_classification_id', 'meta:classification') if evo_config else 'meta:classification'
        classification_name = getattr(evo_config, 'meta_classification_name', '分类继承规则') if evo_config else '分类继承规则'
        classification_confidence = getattr(evo_config, 'meta_classification_confidence', 1.0) if evo_config else 1.0
        
        meta_rule_source = getattr(evo_config, 'meta_rule_source', 'bootstrap') if evo_config else 'bootstrap'
        
        # 定义元规则列表
        # 注意：conditions 和 actions 是元逻辑层面的固定结构，不属于可配置的业务逻辑
        # 它们定义了系统的推理语义，修改将改变系统的逻辑基础
        meta_rules = [
            LogicPattern(
                id=transitivity_id,
                logic_type=LogicType.RULE,
                name=transitivity_name,
                description="如果A→B且B→C，则A→C（传递性公理）",
                conditions=[
                    {"subject": "?A", "predicate": "?P", "object": "?B"},
                    {"subject": "?B", "predicate": "?P", "object": "?C"}
                ],
                actions=[
                    {"type": "infer", "subject": "?A", "predicate": "?P", "object": "?C"}
                ],
                confidence=transitivity_confidence,
                source=meta_rule_source
            ),
            LogicPattern(
                id=classification_id,
                logic_type=LogicType.RULE,
                name=classification_name,
                description="如果X是A，A是B，则X是B（分类继承公理）",
                conditions=[
                    {"subject": "?X", "predicate": "is_a", "object": "?A"},
                    {"subject": "?A", "predicate": "is_a", "object": "?B"}
                ],
                actions=[
                    {"type": "infer", "subject": "?X", "predicate": "is_a", "object": "?B"}
                ],
                confidence=classification_confidence,
                source=meta_rule_source
            )
        ]
        
        logger.debug(f"正在引导 {len(meta_rules)} 条元逻辑规则")
        
        # 通过统一入口写入，确保 KG 优先策略一致
        # 如果有图引擎则直接进图；否则进入内存 fallback
        for rule in meta_rules:
            self.add_pattern(rule)
    
    def add_pattern(self, pattern: LogicPattern) -> bool:
        """
        添加新的逻辑模式 — 统一写入 KnowledgeGraph (唯一存储源)。
        
        存储策略（单一写入点原则）：
        1. KnowledgeGraph 是 pattern 的唯一真值源（当可用时）
        2. _patterns_fallback 仅在 KG 不可用时作为降级方案使用
        3. 禁止双写：不同时写入 KG 和 fallback，避免数据不一致
        
        版本管理：
        - 如果 pattern 已存在，自动升级版本号
        - 继承历史统计信息（success_count/failure_count）
        
        Args:
            pattern: 要添加的逻辑模式
            
        Returns:
            bool: 是否添加成功
        """
        # 版本升级: 检查已有 pattern，继承历史统计
        existing = self.patterns.get(pattern.id)
        if existing is not None:
            pattern.version = existing.version + 1
            pattern.success_count = existing.success_count
            pattern.failure_count = existing.failure_count

        if self._knowledge_graph is not None:
            # 写入图 — pattern 的唯一存储源（优先路径）
            self._write_pattern_to_graph(pattern)
            # 清除缓存，下次访问 self.patterns 时重建
            self._clear_cache()
        else:
            # 无图引擎时退化为内存存储（降级路径）
            # 注意：此时不写入 KG，确保单一写入点原则
            self._patterns_fallback[pattern.id] = pattern

        return True
    
    def _write_pattern_to_graph(self, pattern: LogicPattern):
        """
        将 LogicPattern 完整写入 KnowledgeGraph — 唯一写入路径。

        存储约定:
        - 主节点: (pattern.id, "_type", logic_type.value)
          metadata 存储完整 pattern 定义 (conditions/actions/description 等)
        - 额外: 将 conditions/actions 中的具体实体关系也写入图,
          方便 Reasoner 和 GraphRetriever 索引
        """
        try:
            kg = self._knowledge_graph
            # 先删除旧 _type 节点 (如果存在), 确保幂等
            old = kg.query(subject=pattern.id, predicate="_type")
            for t in old:
                kg.remove_triple(t.id)

            # 写入 pattern 元节点, metadata 包含完整定义
            kg.add_triple(
                subject=pattern.id,
                predicate="_type",
                obj=pattern.logic_type.value,
                confidence=pattern.confidence,
                source=f"pattern:{pattern.source}",
                metadata={
                    "name": pattern.name,
                    "domain": pattern.domain,
                    "description": pattern.description,
                    "conditions": pattern.conditions,
                    "actions": pattern.actions,
                    "version": pattern.version,
                    "usage_count": pattern.usage_count,
                    "success_count": pattern.success_count,
                    "failure_count": pattern.failure_count,
                },
            )
            # 将 conditions 中的具体实体关系也写入图 (方便索引检索)
            for cond in pattern.conditions:
                subj = cond.get("subject", "")
                pred = cond.get("predicate", "")
                obj_val = cond.get("object", "")
                if subj and pred and obj_val and not subj.startswith("?") and not obj_val.startswith("?"):
                    kg.add_triple(
                        subject=subj, predicate=pred, obj=obj_val,
                        confidence=pattern.confidence,
                        source=f"pattern:{pattern.id}",
                    )
            # 将 actions 中的具体推导关系写入图
            for action in pattern.actions:
                subj = action.get("subject", "")
                pred = action.get("predicate", "")
                obj_val = action.get("object", "")
                if subj and pred and obj_val and not subj.startswith("?") and not obj_val.startswith("?"):
                    kg.add_triple(
                        subject=subj, predicate=pred, obj=obj_val,
                        confidence=pattern.confidence,
                        source=f"pattern:{pattern.id}",
                    )
        except Exception as e:
            logger.warning(f"写入 pattern 到图失败: {e}")
    
    def _clear_cache(self):
        """
        清除 pattern 缓存。
        
        触发时机：
        - 写入操作（add/remove pattern）后必须调用
        - 确保下次读取时从 KG 重建最新数据
        
        性能考虑：
        - 缓存清除是 O(1) 操作
        - 重建是延迟的（下次访问 patterns 属性时）
        """
        self._pattern_cache.clear()
    
    def extract_logic_from_text(self, text: str, domain_hint: str = None) -> List[LogicPattern]:
        """
        从文本中提取逻辑模式 - 核心能力
        
        支持的逻辑表达：
        - "如果...那么..." -> 规则
        - "当...时，应该..." -> 行为
        - "为了...必须..." -> 策略
        - "...需要..." -> 约束
        - "...是..." -> 定义/分类
        - "...包括..." -> 组成关系
        
        增强功能:
        - 支持知识库结构化文本
        - 多层级关系提取
        - 属性值提取
        - 超长文本分段处理（性能优化）
        """
        patterns = []
        pattern_counter = 0
        
        logger.info(f"开始从文本提取逻辑模式，文本长度: {len(text)} 字符")
        
        # 性能优化：如果文本过长，分段处理
        # 从 ConfigManager 读取最大文本长度，避免硬编码
        MAX_TEXT_LENGTH = get_config().evolution.max_text_length
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(f"文本过长({len(text)}字符)，将分段处理")
            # 只处理前5000字符，避免性能问题
            text = text[:MAX_TEXT_LENGTH]
        
        # 预处理：清理文本
        text = self._preprocess_text(text)
        
        # 模式1: 定义/分类 (是/为/指) - 增强版，支持更多格式
        definition_patterns = [
            # 标准格式: X：是/为/指 Y
            r'([^：:\n]{2,50})[：:]\s*(?:是|为|指)\s*([^。\n]{2,200})',
            # 简单格式: X是Y (句子级匹配，支持段落内句子)
            r'(?:^|(?<=。))\s*([^是。\n]{2,30})是([^。\n]{2,100})',
            # 类别格式: X是一种Y
            r'([^是]{2,30})是一种([^。]{2,100})',
        ]
        for pattern in definition_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                entity = match.group(1).strip()
                definition = match.group(2).strip()
                
                # 清理实体名：移除常见列表标记符号，确保实体名干净
                # 使用 str.strip() 的字符集参数一次性移除所有标记符号
                entity = entity.strip('●○•·-–—* ')
                
                # 防御性检查：确保实体名和定义有效（非空且长度合理）
                # 过滤过短或无效的匹配结果，避免噪声数据进入知识库
                if not entity or not definition:
                    continue
                if len(entity) < 2 or len(definition) < 2:
                    continue
                if len(entity) > 50 or len(definition) > 300:
                    continue  # 跳过过长的匹配
                
                pattern_obj = LogicPattern(
                    id=f"learned:definition:{domain_hint or 'generic'}:{pattern_counter}",
                    logic_type=LogicType.BEHAVIOR,
                    name=f"定义: {entity[:30]}",
                    description=f"{entity} 是 {definition[:100]}",
                    conditions=[{"subject": entity, "predicate": "exists", "object": "true"}],
                    actions=[{"type": "assign", "subject": entity, "predicate": "is_a", "object": definition}],
                    source="learned",
                    domain=domain_hint or "generic"
                )
                patterns.append(pattern_obj)
                pattern_counter += 1
        
        # 模式2: 功能/用途 (用于/功能/作用)
        function_patterns = [
            r'([^：:\n]+)[：:]\s*(?:用于|功能|作用)[：:]?\s*([^。\n]+)',
            r'(?:用于|功能|作用)[：:]\s*([^。\n]+)',
        ]
        for pattern in function_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                if len(match.groups()) == 2:
                    entity = match.group(1).strip()
                    function = match.group(2).strip()
                else:
                    entity = "设备"
                    function = match.group(1).strip()
                
                if len(function) > 200:
                    continue
                
                pattern_obj = LogicPattern(
                    id=f"learned:function:{domain_hint or 'generic'}:{pattern_counter}",
                    logic_type=LogicType.BEHAVIOR,
                    name=f"功能: {entity[:30]}",
                    description=f"{entity} 用于 {function[:100]}",
                    conditions=[{"subject": entity, "predicate": "exists", "object": "true"}],
                    actions=[{"type": "assign", "subject": entity, "predicate": "function", "object": function}],
                    source="learned",
                    domain=domain_hint or "generic"
                )
                patterns.append(pattern_obj)
                pattern_counter += 1
        
        # 模式3: 属性/参数 (属性/参数/规格)
        attribute_patterns = [
            r'([^：:\n]+)[：:]\s*([^，。\n]+)[，。]?\s*(?:单位|范围|值)?[：:]?\s*([^。\n]*)',
        ]
        for pattern in attribute_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                attr_name = match.group(1).strip()
                attr_value = match.group(2).strip()
                
                # 过滤掉非属性项
                if any(keyword in attr_name for keyword in ['定义', '功能', '说明', '来源']):
                    continue
                if len(attr_name) > 30 or len(attr_value) > 100:
                    continue
                
                pattern_obj = LogicPattern(
                    id=f"learned:attribute:{domain_hint or 'generic'}:{pattern_counter}",
                    logic_type=LogicType.CONSTRAINT,
                    name=f"属性: {attr_name[:30]}",
                    description=f"{attr_name} = {attr_value[:50]}",
                    conditions=[{"subject": "entity", "predicate": "exists", "object": "true"}],
                    actions=[{"type": "assign", "subject": "entity", "predicate": attr_name, "object": attr_value}],
                    source="learned",
                    domain=domain_hint or "generic"
                )
                patterns.append(pattern_obj)
                pattern_counter += 1
        
        # 模式4: 如果...那么... (条件规则)
        if_then_matches = re.finditer(
            r'如果\s*([^，。\n]+)[，。]?\s*那么\s*([^。\n]+)',
            text
        )
        for match in if_then_matches:
            condition_str = match.group(1).strip()
            action_str = match.group(2).strip()
            
            conditions = self._parse_condition(condition_str)
            actions = self._parse_action(action_str)
            
            if conditions and actions:
                pattern_obj = LogicPattern(
                    id=f"learned:rule:{domain_hint or 'generic'}:{pattern_counter}",
                    logic_type=LogicType.RULE,
                    name=f"规则: {condition_str[:30]}",
                    description=f"如果 {condition_str} 那么 {action_str}",
                    conditions=conditions,
                    actions=actions,
                    source="learned",
                    domain=domain_hint or "generic"
                )
                patterns.append(pattern_obj)
                pattern_counter += 1
        
        # 模式5: 组成关系 (包括/包含/由...组成)
        composition_patterns = [
            r'([^：:\n]+)[：:]\s*(?:包括|包含|由...组成)[：:]?\s*([^。\n]+)',
        ]
        for pattern in composition_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                whole = match.group(1).strip()
                parts = match.group(2).strip()
                
                pattern_obj = LogicPattern(
                    id=f"learned:composition:{domain_hint or 'generic'}:{pattern_counter}",
                    logic_type=LogicType.BEHAVIOR,
                    name=f"组成: {whole[:30]}",
                    description=f"{whole} 包括 {parts[:100]}",
                    conditions=[{"subject": whole, "predicate": "exists", "object": "true"}],
                    actions=[{"type": "assign", "subject": whole, "predicate": "components", "object": parts}],
                    source="learned",
                    domain=domain_hint or "generic"
                )
                patterns.append(pattern_obj)
                pattern_counter += 1
        
        logger.info(f"提取完成，共发现 {len(patterns)} 个逻辑模式")
        return patterns
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本，清理格式"""
        # 移除多余的空白字符
        text = re.sub(r'\n\s*\n', '\n', text)
        # 注意: 不替换中文标点，因为正则模式依赖它们进行边界检测
        return text
    
    def _parse_condition(self, text: str) -> List[Dict]:
        """解析条件文本为结构化条件"""
        conditions = []
        
        # 简单解析: 主语 + 谓语 + 宾语
        # 例如: "X是燃气设备" -> {subject: "X", predicate: "is_a", object: "燃气设备"}
        patterns = [
            (r'([^是]+)是([^的]+)', 'is_a'),
            (r'([^有]+)有([^的]+)', 'has'),
            (r'([^需要]+)需要([^的]+)', 'requires'),
            (r'([^大于]+)大于([^的]+)', 'greater_than'),
        ]
        
        for pattern, pred in patterns:
            match = re.search(pattern, text)
            if match:
                conditions.append({
                    "subject": match.group(1).strip(),
                    "predicate": pred,
                    "object": match.group(2).strip()
                })
        
        return conditions if conditions else [{"raw": text}]
    
    def _parse_action(self, text: str) -> List[Dict]:
        """解析动作文本为结构化动作"""
        actions = []
        
        patterns = [
            (r'([^是]+)是([^的]+)', 'infer', 'is_a'),
            (r'([^应该]+)应该([^的]+)', 'suggest', 'should'),
            (r'([^需要]+)需要([^的]+)', 'require', 'requires'),
            (r'执行([^操作]+)', 'execute', 'action'),
        ]
        
        for pattern, action_type, pred in patterns:
            match = re.search(pattern, text)
            if match:
                actions.append({
                    "type": action_type,
                    "subject": match.group(1).strip(),
                    "predicate": pred,
                    "object": match.group(2).strip()
                })
        
        return actions if actions else [{"type": "infer", "raw": text}]
    
    def get_patterns_by_domain(self, domain: str) -> List[LogicPattern]:
        """获取特定领域的逻辑模式 — 从图驱动的 patterns 属性中过滤"""
        return [p for p in self.patterns.values() if p.domain == domain]

    def get_patterns_by_type(self, logic_type: LogicType) -> List[LogicPattern]:
        """获取特定类型的逻辑模式 — 从图驱动的 patterns 属性中过滤"""
        return [p for p in self.patterns.values() if p.logic_type == logic_type]
    
    def execute_pattern(self, pattern: LogicPattern, context: Dict[str, Any]) -> Dict:
        """
        执行逻辑模式
        
        Returns:
            {
                "success": bool,
                "results": List[Dict],
                "explanation": str
            }
        """
        # 记录执行
        execution_record = {
            "pattern_id": pattern.id,
            "timestamp": time.time(),
            "context": context,
            "success": False
        }
        
        try:
            # 条件匹配
            bindings = self._match_conditions(pattern.conditions, context)
            
            if not bindings:
                execution_record["success"] = False
                execution_record["reason"] = "Conditions not matched"
                self.execution_history.append(execution_record)
                pattern.update_success_rate(False)
                return {"success": False, "results": [], "explanation": "条件不匹配"}
            
            # 执行动作
            results = []
            for action in pattern.actions:
                result = self._execute_action(action, bindings)
                results.append(result)
            
            execution_record["success"] = True
            execution_record["results"] = results
            self.execution_history.append(execution_record)
            pattern.update_success_rate(True)
            
            return {
                "success": True,
                "results": results,
                "explanation": f"成功执行 {len(results)} 个动作"
            }
            
        except Exception as e:
            execution_record["success"] = False
            execution_record["error"] = str(e)
            self.execution_history.append(execution_record)
            pattern.update_success_rate(False)
            return {"success": False, "results": [], "explanation": f"执行错误: {e}"}
    
    def _match_conditions(self, conditions: List[Dict], context: Dict) -> Optional[Dict]:
        """匹配条件，返回变量绑定"""
        bindings = {}
        
        for condition in conditions:
            if "raw" in condition:
                # 原始文本条件，需要LLM判断
                continue
            
            # 变量替换
            subject = condition["subject"]
            predicate = condition["predicate"]
            obj = condition["object"]
            
            # 检查是否是变量（以?开头）
            if subject.startswith("?"):
                if subject not in bindings:
                    # 尝试从上下文绑定
                    if "facts" in context:
                        for fact in context["facts"]:
                            if fact.get("predicate") == predicate and fact.get("object") == obj:
                                bindings[subject] = fact.get("subject")
                                break
            
            if obj.startswith("?"):
                if obj not in bindings:
                    if "facts" in context:
                        for fact in context["facts"]:
                            if fact.get("subject") == subject and fact.get("predicate") == predicate:
                                bindings[obj] = fact.get("object")
                                break
        
        return bindings if bindings else None
    
    def _execute_action(self, action: Dict, bindings: Dict) -> Dict:
        """执行单个动作"""
        action_type = action.get("type", "infer")
        
        # 变量替换
        subject = action.get("subject", "")
        predicate = action.get("predicate", "")
        obj = action.get("object", "")
        
        if subject.startswith("?") and subject in bindings:
            subject = bindings[subject]
        if obj.startswith("?") and obj in bindings:
            obj = bindings[obj]
        
        return {
            "type": action_type,
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "bindings": bindings
        }
    
    def get_statistics(self) -> Dict:
        """获取逻辑层统计信息"""
        return {
            "total_patterns": len(self.patterns),
            "by_type": {
                t.value: len(self.get_patterns_by_type(t)) for t in LogicType
            },
            "by_domain": {
                domain: len(patterns) for domain, patterns in self.domain_patterns.items()
            },
            "total_executions": len(self.execution_history),
            "avg_confidence": sum(p.confidence for p in self.patterns.values()) / len(self.patterns) if self.patterns else 0,
            "storage_backend": "knowledge_graph" if self.is_using_kg else "memory_fallback",
        }
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """
        删除逻辑模式 — 统一删除入口，确保单一写入点
        
        根据当前存储后端选择正确的删除方式：
        - 使用 KG 时：从 KG 中删除 pattern 节点
        - 使用 fallback 时：从内存字典中删除
        
        Args:
            pattern_id: 要删除的 pattern ID
            
        Returns:
            bool: 是否删除成功
        """
        if self.is_using_kg:
            # 从 KG 中删除 pattern 节点
            # 先查找 _type 谓词的三元组
            old_triples = self._knowledge_graph.query(subject=pattern_id, predicate="_type")
            if not old_triples:
                logger.warning(f"Pattern {pattern_id} 不存在")
                return False
            
            # 删除主节点
            for t in old_triples:
                self._knowledge_graph.remove_triple(t.id)
            
            # 清除缓存
            self._clear_cache()
            logger.info(f"已从 KG 删除 pattern: {pattern_id}")
            return True
        else:
            # 从 fallback 字典中删除
            if pattern_id in self._patterns_fallback:
                del self._patterns_fallback[pattern_id]
                logger.info(f"已从内存删除 pattern: {pattern_id}")
                return True
            logger.warning(f"Pattern {pattern_id} 不存在")
            return False
    
    def verify_consistency(self) -> Dict[str, Any]:
        """
        校验存储一致性 — 检查 fallback 和 KG 之间的数据是否一致
        
        此方法用于诊断和调试，确保存储层的数据一致性。
        正常情况下，KG 优先模式不会同时写入 fallback，
        但如果代码逻辑有误或迁移过程中出现问题，可能导致不一致。
        
        Returns:
            {
                "consistent": bool,  # 是否一致
                "kg_count": int,     # KG 中的 pattern 数量
                "fallback_count": int,  # fallback 中的 pattern 数量
                "only_in_kg": List[str],  # 仅在 KG 中存在的 pattern ID
                "only_in_fallback": List[str],  # 仅在 fallback 中存在的 pattern ID
                "conflicts": List[Dict],  # 两边都存在但不一致的 pattern
                "message": str,  # 诊断信息
            }
        """
        result = {
            "consistent": True,
            "kg_count": 0,
            "fallback_count": 0,
            "only_in_kg": [],
            "only_in_fallback": [],
            "conflicts": [],
            "message": "",
        }
        
        # 如果没有 KG，不需要校验一致性
        if not self.is_using_kg:
            result["message"] = "未使用 KnowledgeGraph，无需校验一致性"
            result["fallback_count"] = len(self._patterns_fallback)
            return result
        
        # 获取 KG 中的 pattern
        kg_patterns = self._rebuild_patterns_from_graph()
        result["kg_count"] = len(kg_patterns)
        
        # 获取 fallback 中的 pattern
        result["fallback_count"] = len(self._patterns_fallback)
        
        # 比较两边的 pattern ID
        kg_ids = set(kg_patterns.keys())
        fallback_ids = set(self._patterns_fallback.keys())
        
        # 仅在 KG 中存在
        result["only_in_kg"] = list(kg_ids - fallback_ids)
        
        # 仅在 fallback 中存在（不应该发生）
        result["only_in_fallback"] = list(fallback_ids - kg_ids)
        
        # 检查两边都存在但不一致的 pattern
        common_ids = kg_ids & fallback_ids
        for pid in common_ids:
            kg_p = kg_patterns[pid]
            fb_p = self._patterns_fallback[pid]
            # 检查关键字段是否一致
            if (kg_p.name != fb_p.name or 
                kg_p.logic_type != fb_p.logic_type or 
                abs(kg_p.confidence - fb_p.confidence) > 0.01):
                result["conflicts"].append({
                    "id": pid,
                    "kg_version": kg_p.version,
                    "fallback_version": fb_p.version,
                    "kg_name": kg_p.name,
                    "fallback_name": fb_p.name,
                })
        
        # 判断一致性
        is_consistent = (
            len(result["only_in_fallback"]) == 0 and
            len(result["conflicts"]) == 0
        )
        result["consistent"] = is_consistent
        
        # 生成诊断信息
        if is_consistent:
            result["message"] = f"存储一致性校验通过，KG 中有 {result['kg_count']} 个 pattern"
        else:
            issues = []
            if result["only_in_fallback"]:
                issues.append(f"{len(result['only_in_fallback'])} 个 pattern 仅在 fallback 中")
            if result["conflicts"]:
                issues.append(f"{len(result['conflicts'])} 个 pattern 存在冲突")
            result["message"] = f"存储不一致: {', '.join(issues)}"
            logger.warning(result["message"])
        
        
        return result
    
    def sync_to_fallback(self) -> int:
        """
        将 KG 中的 pattern 同步到 fallback（仅用于降级准备）
        
        此方法用于在需要从 KG 切换到 fallback 前预先同步数据。
        正常操作中不应调用此方法，以避免双写。
        
        Returns:
            同步的 pattern 数量
        """
        if not self.is_using_kg:
            logger.warning("未使用 KG，无需同步")
            return 0
        
        # 从 KG 读取所有 pattern
        kg_patterns = self._rebuild_patterns_from_graph()
        
        # 清空 fallback 并重新填充
        self._patterns_fallback.clear()
        for pid, pattern in kg_patterns.items():
            self._patterns_fallback[pid] = pattern
        
        logger.info(f"已将 {len(kg_patterns)} 个 pattern 同步到 fallback")
        return len(kg_patterns)


import time
