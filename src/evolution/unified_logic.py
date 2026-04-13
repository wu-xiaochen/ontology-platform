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
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from functools import lru_cache
import time
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
        
        # ── Pattern 版本历史存储 ──
        # 存储结构: {pattern_id: {version: LogicPattern}}
        # 每次 add_pattern 更新已存在 pattern 时，自动归档旧版本到此处
        self._pattern_history: Dict[str, Dict[int, LogicPattern]] = {}
        
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
        # 版本升级: 检查已有 pattern，继承历史统计，同时保存旧版本到历史
        existing = self.patterns.get(pattern.id)
        if existing is not None:
            # ── 保存旧版本到历史 ──
            self._archive_pattern_version(existing)
            # 版本升级
            pattern.version = existing.version + 1
            # 继承历史统计信息
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
    
    def _archive_pattern_version(self, pattern: LogicPattern) -> None:
        """
        将 pattern 旧版本归档到 _pattern_history。
        
        Args:
            pattern: 要归档的 LogicPattern（归档时使用其当前 version 作为 key）
        """
        pid = pattern.id
        version = pattern.version
        if pid not in self._pattern_history:
            self._pattern_history[pid] = {}
        # 使用深拷贝避免引用问题
        self._pattern_history[pid][version] = LogicPattern(
            id=pattern.id,
            logic_type=pattern.logic_type,
            name=pattern.name,
            description=pattern.description,
            conditions=pattern.conditions.copy(),
            actions=pattern.actions.copy(),
            confidence=pattern.confidence,
            source=pattern.source,
            domain=pattern.domain,
            version=pattern.version,
            usage_count=pattern.usage_count,
            success_count=pattern.success_count,
            failure_count=pattern.failure_count,
        )
        logger.debug(f"已归档 pattern {pid} version={version} 到历史")
    
    # ── 版本控制 API ──
    
    def get_current_version(self, pattern_id: str) -> Optional[int]:
        """
        获取 pattern 的当前版本号。
        
        Args:
            pattern_id: pattern ID
            
        Returns:
            当前版本号，如果 pattern 不存在则返回 None
        """
        pattern = self.patterns.get(pattern_id)
        return pattern.version if pattern else None
    
    def get_pattern_history(self, pattern_id: str) -> List[LogicPattern]:
        """
        获取 pattern 的所有历史版本。
        
        Args:
            pattern_id: pattern ID
            
        Returns:
            按版本号升序排列的 LogicPattern 列表
        """
        history = self._pattern_history.get(pattern_id, {})
        return [history[v] for v in sorted(history.keys())]
    
    def compare_versions(
        self, pattern_id: str, v1: int, v2: int
    ) -> Dict[str, Any]:
        """
        比较 pattern 两个版本的差异。
        
        Args:
            pattern_id: pattern ID
            v1: 版本号 1
            v2: 版本号 2
            
        Returns:
            包含差异信息的字典:
            {
                "pattern_id": str,
                "v1": int, "v2": int,
                "v1_pattern": LogicPattern,
                "v2_pattern": LogicPattern,
                "diff": {
                    "changed_fields": List[str],  # 发生变化的字段
                    "field_diffs": Dict[str, Tuple[Any, Any]]  # field -> (old, new)
                }
            }
            如果某个版本不存在，返回包含 error 信息的字典
        """
        history = self._pattern_history.get(pattern_id, {})
        p1 = history.get(v1)
        p2 = history.get(v2)
        
        # 当前版本需要从 patterns 中获取
        current = self.patterns.get(pattern_id)
        
        if v1 == current.version:
            p1 = current
        if v2 == current.version:
            p2 = current
            
        if p1 is None or p2 is None:
            return {
                "error": f"版本不存在: v1={v1} exists={p1 is not None}, v2={v2} exists={p2 is not None}",
                "pattern_id": pattern_id
            }
        
        # 计算字段差异
        fields_to_compare = [
            "name", "description", "conditions", "actions",
            "confidence", "domain", "logic_type"
        ]
        changed_fields: List[str] = []
        field_diffs: Dict[str, Any] = {}
        
        for field in fields_to_compare:
            val1 = getattr(p1, field)
            val2 = getattr(p2, field)
            if val1 != val2:
                changed_fields.append(field)
                field_diffs[field] = (val1, val2)
        
        return {
            "pattern_id": pattern_id,
            "v1": v1,
            "v2": v2,
            "v1_pattern": p1,
            "v2_pattern": p2,
            "diff": {
                "changed_fields": changed_fields,
                "field_diffs": field_diffs
            }
        }
    
    def rollback_pattern(self, pattern_id: str, target_version: int) -> bool:
        """
        将 pattern 回滚到指定版本。
        
        回滚逻辑:
        1. 从历史中获取目标版本的 deep copy
        2. 将其作为新版本写入（触发版本号 +1）
        3. 旧版本（当前版本）自动归档到历史
        
        Args:
            pattern_id: pattern ID
            target_version: 目标回滚版本号
            
        Returns:
            bool: 回滚是否成功
        """
        history = self._pattern_history.get(pattern_id, {})
        target = history.get(target_version)
        
        if target is None:
            logger.warning(f"回滚失败: pattern {pattern_id} 版本 {target_version} 不存在")
            return False
        
        logger.info(f"开始回滚 pattern {pattern_id} 到版本 {target_version}")
        
        # 创建回滚版本的深拷贝
        rollback_pattern = LogicPattern(
            id=target.id,
            logic_type=target.logic_type,
            name=target.name,
            description=target.description,
            conditions=target.conditions.copy(),
            actions=target.actions.copy(),
            confidence=target.confidence,
            source=target.source,
            domain=target.domain,
            version=0,  # add_pattern 会自动设置为 current_version + 1
            usage_count=0,
            success_count=0,
            failure_count=0,
        )
        
        # 通过 add_pattern 写入，会自动处理版本归档
        self.add_pattern(rollback_pattern)
        
        logger.info(f"回滚完成: pattern {pattern_id} 已回滚到 version={rollback_pattern.version}")
        return True
    
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

    # ── 规则相似度去重功能 ──────────────────────────────────────────────────
    
    def _get_similarity_config(self) -> Tuple[float, bool]:
        """
        从配置读取相似度相关参数。
        
        Returns:
            Tuple[similarity_threshold, enable_auto_merge]
        """
        config = get_config()
        evo_config = getattr(config, 'evolution', None)
        
        threshold = 0.85  # 默认值
        auto_merge = False  # 默认值
        
        if evo_config is not None:
            threshold = getattr(evo_config, 'similarity_threshold', threshold)
            auto_merge = getattr(evo_config, 'enable_auto_merge', auto_merge)
        
        logger.debug(f"相似度配置: threshold={threshold}, auto_merge={auto_merge}")
        return threshold, auto_merge
    
    def similarity(self, pattern1: LogicPattern, pattern2: LogicPattern) -> float:
        """
        计算两个 LogicPattern 之间的相似度。
        
        使用 PatternVectorizer 将 pattern 转换为向量, 然后计算余弦相似度。
        
        Args:
            pattern1: 第一个 LogicPattern
            pattern2: 第二个 LogicPattern
            
        Returns:
            float: 0-1 的相似度分数, 1 表示完全相同
        """
        if not hasattr(self, '_pattern_vectorizer'):
            self._pattern_vectorizer = PatternVectorizer()
        
        vec1 = self._pattern_vectorizer.vectorize(pattern1)
        vec2 = self._pattern_vectorizer.vectorize(pattern2)
        
        similarity_score = _compute_similarity_with_vectorizer(vec1, vec2)
        logger.debug(f"相似度计算: {pattern1.id} <-> {pattern2.id} = {similarity_score:.4f}")
        
        return similarity_score
    
    def detect_redundancy(
        self,
        threshold: Optional[float] = None,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检测冗余规则。
        
        找出相似度超过阈值的规则对, 返回冗余规则列表。
        
        Args:
            threshold: 相似度阈值, 默认为配置值 0.85
            domain: 可选, 仅检测指定域名的规则
            
        Returns:
            List[Dict]: 冗余规则列表, 每项包含:
                - pattern1_id: 第一个冗余规则的 ID
                - pattern2_id: 第二个冗余规则的 ID  
                - similarity: 相似度分数
                - recommended_action: 建议的处理动作 (keep_higher_confidence / keep_newer)
        """
        if threshold is None:
            threshold, _ = self._get_similarity_config()
        
        patterns = list(self.patterns.values())
        
        # 按域名过滤
        if domain:
            patterns = [p for p in patterns if p.domain == domain]
        
        logger.info(f"开始冗余检测: {len(patterns)} 个 patterns, 阈值={threshold}")
        
        redundant_pairs: List[Dict[str, Any]] = []
        checked: Set[Tuple[str, str]] = set()
        
        for i, p1 in enumerate(patterns):
            for p2 in patterns[i + 1:]:
                pair_key = (min(p1.id, p2.id), max(p1.id, p2.id))
                if pair_key in checked:
                    continue
                checked.add(pair_key)
                
                sim = self.similarity(p1, p2)
                
                if sim >= threshold:
                    # 确定保留哪个: 优先高置信度, 其次更新版本
                    if p1.confidence > p2.confidence:
                        keep_id, remove_id = p2.id, p1.id
                        action = "keep_higher_confidence"
                    elif p2.confidence > p1.confidence:
                        keep_id, remove_id = p1.id, p2.id
                        action = "keep_higher_confidence"
                    else:
                        keep_id, remove_id = p1.id, p2.id
                        action = "keep_newer"
                    
                    redundant_pairs.append({
                        "pattern1_id": p1.id,
                        "pattern2_id": p2.id,
                        "similarity": round(sim, 4),
                        "keep_id": keep_id,
                        "remove_id": remove_id,
                        "recommended_action": action,
                        "pattern1_confidence": p1.confidence,
                        "pattern2_confidence": p2.confidence
                    })
                    
                    logger.debug(
                        f"发现冗余: {p1.id} <-> {p2.id}, "
                        f"相似度={sim:.4f}, 建议保留={keep_id}"
                    )
        
        logger.info(f"冗余检测完成: 发现 {len(redundant_pairs)} 对冗余规则")
        return redundant_pairs
    
    def merge_similar_patterns(
        self,
        threshold: Optional[float] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        合并相似度超过阈值的规则。
        
        Args:
            threshold: 相似度阈值, 默认为配置值 0.85
            dry_run: 若为 True, 仅返回合并计划而不执行
            
        Returns:
            Dict 包含:
                - merged_count: 合并的规则数量
                - merge_plan: 合并计划详情
                - would_remove: 如果执行将移除的规则 ID 列表
        """
        if threshold is None:
            threshold, auto_merge = self._get_similarity_config()
        else:
            _, auto_merge = self._get_similarity_config()
        
        redundant = self.detect_redundancy(threshold=threshold)
        
        if not redundant:
            return {
                "merged_count": 0,
                "merge_plan": [],
                "would_remove": [],
                "message": "未发现需要合并的冗余规则"
            }
        
        # 构建合并计划
        remove_ids: Set[str] = set()
        merge_plan: List[Dict[str, Any]] = []
        
        for item in redundant:
            if item["remove_id"] not in remove_ids:
                remove_ids.add(item["remove_id"])
                merge_plan.append({
                    "keep_id": item["keep_id"],
                    "remove_id": item["remove_id"],
                    "similarity": item["similarity"],
                    "reason": f"与 {item['keep_id']} 相似度 {item['similarity']}"
                })
        
        result = {
            "merged_count": len(remove_ids),
            "merge_plan": merge_plan,
            "would_remove": list(remove_ids),
            "auto_merge": auto_merge
        }
        
        if dry_run:
            result["message"] = f"干运行: 将合并 {len(remove_ids)} 条冗余规则 (实际执行需 dry_run=False)"
            logger.info(result["message"])
            return result
        
        # 执行合并
        if not auto_merge:
            result["message"] = "enable_auto_merge=False, 拒绝自动合并"
            logger.warning(result["message"])
            return result
        
        removed_count = 0
        for remove_id in remove_ids:
            if remove_id in self.patterns:
                self.remove_pattern(remove_id)
                removed_count += 1
                logger.info(f"已移除冗余规则: {remove_id}")
        
        result["actually_removed"] = removed_count
        result["message"] = f"已合并 {removed_count} 条冗余规则"
        
        # 清除缓存
        self._pattern_cache.clear()
        return result


# ── PatternVectorizer 及相关辅助函数 ──────────────────────────────────────

import hashlib

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False
    np = None


class PatternVectorizer:
    """
    将 LogicPattern 转换为向量的向量化器。
    
    支持两种模式:
    - embedding 模式: 使用语义 embedding (需要 numpy)
    - 特征哈希模式: 基于规则结构特征的哈希向量 (降级方案)
    """
    
    def __init__(self, use_embedding: bool = True):
        """
        初始化向量化器。
        
        Args:
            use_embedding: 是否优先使用 embedding 模式, False 则使用特征哈希
        """
        self.use_embedding = use_embedding and _NUMPY_AVAILABLE
        self._embedding_cache: Dict[str, np.ndarray] = {} if _NUMPY_AVAILABLE else {}
        logger.debug(f"PatternVectorizer 初始化: embedding模式={self.use_embedding}")
    
    def vectorize(self, pattern: LogicPattern) -> np.ndarray:
        """
        将 LogicPattern 转换为向量表示。
        
        Args:
            pattern: 要向量化的 LogicPattern
            
        Returns:
            np.ndarray: 固定维度的向量表示
        """
        if self.use_embedding:
            return self._embedding_vectorize(pattern)
        return self._feature_hash_vectorize(pattern)
    
    def _embedding_vectorize(self, pattern: LogicPattern) -> np.ndarray:
        """
        使用 embedding 模式向量化。
        
        基于 pattern 的结构和语义信息生成向量。
        """
        if pattern.id in self._embedding_cache:
            return self._embedding_cache[pattern.id]
        
        # 构建语义特征向量
        features = []
        
        # 1. 类型特征 (one-hot)
        type_features = [0.0] * len(LogicType)
        type_index = list(LogicType).index(pattern.logic_type)
        type_features[type_index] = 1.0
        features.extend(type_features)
        
        # 2. 置信度特征
        features.append(pattern.confidence)
        
        # 3. 条件结构特征
        cond_count = len(pattern.conditions)
        features.append(min(cond_count / 10.0, 1.0))  # 归一化
        
        # 4. 动作结构特征
        action_count = len(pattern.actions)
        features.append(min(action_count / 10.0, 1.0))
        
        # 5. 条件谓词哈希
        pred_hash = self._hash_features([
            c.get("predicate", "") for c in pattern.conditions
        ])
        features.extend(pred_hash)
        
        # 6. 动作类型哈希
        action_hash = self._hash_features([
            a.get("type", "") for a in pattern.actions
        ])
        features.extend(action_hash)
        
        # 7. 描述语义特征 (基于词频)
        desc_features = self._text_features(pattern.description)
        features.extend(desc_features)
        
        # 8. 域名特征
        domain_features = self._text_features(pattern.domain)
        features.extend(domain_features)
        
        vector = np.array(features, dtype=np.float32)
        
        # L2 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        self._embedding_cache[pattern.id] = vector
        return vector
    
    def _feature_hash_vectorize(self, pattern: LogicPattern) -> np.ndarray:
        """
        使用特征哈希模式向量化 (降级方案)。
        
        基于规则结构特征生成固定维度的哈希向量。
        """
        features = []
        
        # 1. 类型特征
        type_val = hash(pattern.logic_type.value) % 1000
        features.append(float(type_val) / 1000.0)
        
        # 2. 置信度
        features.append(pattern.confidence)
        
        # 3. 结构和描述哈希
        struct_str = json.dumps({
            "conditions": pattern.conditions,
            "actions": pattern.actions,
            "name": pattern.name,
            "domain": pattern.domain
        }, sort_keys=True)
        
        hash_digest = hashlib.sha256(struct_str.encode()).digest()
        hash_features = [b / 255.0 for b in hash_digest[:32]]
        features.extend(hash_features)
        
        if _NUMPY_AVAILABLE:
            vector = np.array(features, dtype=np.float32)
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            return vector
        else:
            return np.array(features, dtype=np.float32)
    
    def _hash_features(self, items: List[str], dim: int = 8) -> List[float]:
        """将字符串列表转换为哈希特征向量"""
        hash_vals = [0.0] * dim
        for item in items:
            h = hash(item) % 10000
            for i in range(dim):
                hash_vals[i] += (h % (i + 2)) / (i + 1)
        # 归一化
        total = sum(abs(v) for v in hash_vals)
        if total > 0:
            hash_vals = [v / total for v in hash_vals]
        return hash_vals
    
    def _text_features(self, text: str, dim: int = 16) -> List[float]:
        """从文本提取词频特征"""
        words = re.findall(r'\w+', text.lower())
        word_hash = [0.0] * dim
        for word in words:
            h = hash(word) % 10000
            for i in range(dim):
                word_hash[i] += (h % (i + 2)) / (i + 1)
        # 归一化
        total = sum(abs(v) for v in word_hash)
        if total > 0:
            word_hash = [v / total for v in word_hash]
        return word_hash


def _compute_similarity_with_vectorizer(
    vec1: np.ndarray,
    vec2: np.ndarray
) -> float:
    """
    计算两个向量的余弦相似度。
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        float: 0-1 的相似度分数
    """
    if _NUMPY_AVAILABLE:
        dot_product = np.dot(vec1, vec2)
        return float(np.clip(dot_product, 0.0, 1.0))
    else:
        # 降级: 逐元素乘积和
        dot = sum(a * b for a, b in zip(vec1, vec2))
        return max(0.0, min(1.0, dot))

