"""
Behavior Learner - 行为学习模块

从交互历史中自动发现行为模式，基于频率统计和成功率过滤噪声。
发现的行为模式可注册到 UnifiedLogicLayer 作为 LogicType.BEHAVIOR 类型的逻辑。

设计决策：
- 使用 (context_type, action) 二元组作为模式聚合键，确保同类场景下的行为归一
- 频率和成功率两重过滤，由 BehaviorLearnerConfig 控制阈值
- 交互历史使用 FIFO 淘汰策略，防止内存无限增长
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import uuid
import time
import logging

# 导入配置管理，获取行为学习器阈值参数
from ..utils.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class BehaviorPattern:
    """
    行为模式数据结构
    
    表示从交互历史中发现的一种行为模式。
    每个模式由 context_type + action 唯一标识。
    """
    # 模式唯一标识符
    id: str
    # 触发上下文类型（如 "query"、"ingest"、"reasoning" 等）
    context_type: str
    # 执行的动作名称
    action: str
    # 最近一次执行的结果描述
    outcome: str
    # 统计成功率 (0.0 ~ 1.0)
    success_rate: float
    # 出现频率（总次数）
    frequency: int
    # 成功次数 —— 用于增量更新 success_rate
    success_count: int = 0
    # 创建时间戳
    created_at: float = field(default_factory=time.time)
    # 最后更新时间戳
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典格式，用于存储和传输"""
        return {
            "id": self.id,
            "context_type": self.context_type,
            "action": self.action,
            "outcome": self.outcome,
            "success_rate": self.success_rate,
            "frequency": self.frequency,
            "success_count": self.success_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class BehaviorLearner:
    """
    行为学习器 — 从交互历史中发现行为模式
    
    核心算法：
    1. 按 (context_type, action) 聚合交互记录
    2. 统计每种组合的出现频率和成功率
    3. 使用配置化阈值过滤噪声模式
    4. 返回通过过滤的有效行为模式列表
    """
    
    def __init__(self):
        # 从配置管理器读取阈值参数，确保零硬编码
        config = get_config()
        # 已发现的行为模式字典，键为 pattern.id
        self.behaviors: Dict[str, BehaviorPattern] = {}
        # 交互历史记录列表
        self.interaction_history: List[Dict[str, Any]] = []
        # 最小频率阈值 —— 低于此频率的组合视为偶发事件，不提取为模式
        self._min_frequency: int = config.behavior_learner.min_frequency
        # 最小成功率阈值 —— 成功率过低的模式说明该行为不可靠
        self._min_success_rate: float = config.behavior_learner.min_success_rate
        # 历史记录最大容量 —— 超出时 FIFO 淘汰最旧记录
        self._max_history_size: int = config.behavior_learner.max_history_size
    
    def record_interaction(
        self,
        context: Dict[str, Any],
        action: str,
        outcome: str,
        success: bool
    ) -> None:
        """
        记录一次交互事件
        
        Args:
            context: 交互发生时的上下文信息，必须包含 "type" 字段标识场景类型
            action: 执行的动作名称
            outcome: 动作执行的结果描述
            success: 动作是否成功
        """
        # 构建交互记录，包含时间戳用于后续时序分析
        record = {
            "context": context,
            "action": action,
            "outcome": outcome,
            "success": success,
            "timestamp": time.time(),
        }
        self.interaction_history.append(record)
        
        # 当历史记录超过最大容量时，淘汰最旧的记录（FIFO）
        if len(self.interaction_history) > self._max_history_size:
            # 计算需要淘汰的数量 —— 批量淘汰 10% 以减少频繁缩减开销
            trim_count = max(1, self._max_history_size // 10)
            self.interaction_history = self.interaction_history[trim_count:]
            logger.debug(f"交互历史超过上限 {self._max_history_size}，已淘汰 {trim_count} 条旧记录")
    
    def learn_from_history(self) -> List[BehaviorPattern]:
        """
        从交互历史中学习行为模式
        
        算法步骤：
        1. 按 (context_type, action) 聚合所有历史记录
        2. 统计每种组合的频率和成功率
        3. 过滤低频和低成功率的噪声模式
        4. 更新 self.behaviors 字典并返回新发现的模式
        
        Returns:
            本次学习新发现的行为模式列表
        """
        # 如果历史为空，直接返回空列表
        if not self.interaction_history:
            logger.info("交互历史为空，跳过行为学习")
            return []
        
        # 第一步：按 (context_type, action) 聚合统计
        # 使用 defaultdict 自动初始化统计容器
        aggregated: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total": 0,
            "success": 0,
            "last_outcome": "",
        })
        
        for record in self.interaction_history:
            # 从 context 中提取场景类型，默认为 "unknown"
            context_type = record.get("context", {}).get("type", "unknown")
            action = record.get("action", "")
            # 聚合键由场景类型和动作名称组成
            key = f"{context_type}::{action}"
            aggregated[key]["total"] += 1
            if record.get("success", False):
                aggregated[key]["success"] += 1
            # 记录最新的 outcome 作为模式描述
            aggregated[key]["last_outcome"] = record.get("outcome", "")
        
        # 第二步：过滤并构建行为模式
        new_patterns: List[BehaviorPattern] = []
        
        for key, stats in aggregated.items():
            # 解析聚合键
            parts = key.split("::", 1)
            context_type = parts[0]
            action = parts[1] if len(parts) > 1 else ""
            
            frequency = stats["total"]
            success_count = stats["success"]
            # 计算成功率，频率为 0 时默认 0（防御性编程）
            success_rate = success_count / frequency if frequency > 0 else 0.0
            
            # 频率过滤 —— 低于阈值的组合视为偶发事件
            if frequency < self._min_frequency:
                continue
            
            # 成功率过滤 —— 成功率过低说明该行为模式不可靠
            if success_rate < self._min_success_rate:
                logger.debug(
                    f"行为模式 ({context_type}, {action}) 成功率 {success_rate:.2f} "
                    f"低于阈值 {self._min_success_rate}，跳过"
                )
                continue
            
            # 检查是否已存在相同模式 —— 使用 context_type + action 去重
            existing_id = None
            for pid, p in self.behaviors.items():
                if p.context_type == context_type and p.action == action:
                    existing_id = pid
                    break
            
            if existing_id:
                # 更新已有模式的统计数据
                existing = self.behaviors[existing_id]
                existing.frequency = frequency
                existing.success_count = success_count
                existing.success_rate = success_rate
                existing.outcome = stats["last_outcome"]
                existing.updated_at = time.time()
            else:
                # 创建新的行为模式
                pattern = BehaviorPattern(
                    id=f"behavior:{uuid.uuid4().hex[:8]}",
                    context_type=context_type,
                    action=action,
                    outcome=stats["last_outcome"],
                    success_rate=success_rate,
                    frequency=frequency,
                    success_count=success_count,
                )
                self.behaviors[pattern.id] = pattern
                new_patterns.append(pattern)
                logger.info(
                    f"发现新行为模式: ({context_type}, {action}) "
                    f"频率={frequency}, 成功率={success_rate:.2f}"
                )
        
        logger.info(f"行为学习完成: 本次新发现 {len(new_patterns)} 个模式，累计 {len(self.behaviors)} 个")
        return new_patterns
    
    def get_patterns_by_context(self, context_type: str) -> List[BehaviorPattern]:
        """
        按上下文类型查询已学习的行为模式
        
        Args:
            context_type: 场景类型标识（如 "query"、"reasoning"）
            
        Returns:
            该场景下的所有行为模式，按成功率降序排列
        """
        # 过滤匹配的模式并按成功率排序 —— 优先推荐高成功率的行为
        matched = [
            p for p in self.behaviors.values()
            if p.context_type == context_type
        ]
        return sorted(matched, key=lambda p: p.success_rate, reverse=True)
    
    def get_all_patterns(self) -> List[BehaviorPattern]:
        """
        获取所有已学习的行为模式
        
        Returns:
            全部行为模式列表，按频率降序排列
        """
        return sorted(self.behaviors.values(), key=lambda p: p.frequency, reverse=True)
    
    def clear(self) -> None:
        """
        重置行为学习器状态
        
        清空所有已学习的模式和交互历史。
        用于测试场景或系统重置。
        """
        self.behaviors.clear()
        self.interaction_history.clear()
        logger.info("行为学习器已重置")
