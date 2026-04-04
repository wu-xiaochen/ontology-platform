"""
主动学习引擎 (Active Learning Engine)
基于ontology-clawra v3.3的主动学习能力

功能：
- 用户确认后自动抽取到本体
- 高频实体自动识别
- 推理失败时主动建议补充
- 置信度升级机制
"""

import logging
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """置信度级别"""
    CONFIRMED = "CONFIRMED"     # 🟢 本体数据
    ASSUMED = "ASSUMED"        # 🟡 合理假设
    SPECULATIVE = "SPECULATIVE" # 🔴 推测
    UNKNOWN = "UNKNOWN"         # ⚪ 未知


class EntityType(Enum):
    """实体类型"""
    PERSON = "Person"
    CONCEPT = "Concept"
    LAW = "Law"
    RULE = "Rule"
    PROJECT = "Project"
    TASK = "Task"
    DECISION = "Decision"
    OBJECTIVE = "Objective"


@dataclass
class ExtractedEntity:
    """抽取的实体"""
    entity_type: EntityType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: ConfidenceLevel = ConfidenceLevel.ASSUMED
    source: str = "interactive_extraction"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExtractedRelation:
    """抽取的关系"""
    relation_type: str
    subject: str
    object: str
    confidence: ConfidenceLevel = ConfidenceLevel.ASSUMED
    source: str = "interactive_extraction"


@dataclass
class LearningEvent:
    """学习事件"""
    event_type: str  # user_confirms, entity_mentioned, ontology_failed, user_correction
    timestamp: str
    content: Dict[str, Any]
    action_taken: str = ""
    result: str = ""


class AutoLearnEngine:
    """
    主动学习引擎
    
    实现基于ontology-clawra v3.3的自动学习能力：
    - 用户确认推理结果后自动抽取
    - 高频实体自动识别
    - 推理失败主动建议
    - 用户纠正自动更新
    """
    
    # 实体抽取模式
    EXTRACT_PATTERNS = {
        "Person": [
            r"我叫(.*)", r"我是(.*)", r"用户是(.*)",
            r"他(?:叫|是)(.*)", r"她(?:叫|是)(.*)",
            r"创业者", r"工程师", r"开发者"
        ],
        "Concept": [
            r"(.*)是一种", r"(.*)是(?:一种|一类)",
            r"所谓的(.*)", r"(.*)本体",
            r"知识图谱", r"Agent", r"本体论"
        ],
        "Law": [
            r"当(.*)时", r"如果(.*)那么(.*)",
            r"(?:规律|法则|原则)"
        ],
        "Rule": [
            r"应该(?:.*)", r"必须(?:.*)",
            r"建议(?:.*)", r"推荐(?:.*)"
        ],
        "Project": [
            r"项目(?:.*)", r"在做(?:.*)",
            r"目标(?:.*)"
        ],
        "Task": [
            r"任务(?:.*)", r"需要做(?:.*)",
            r"要做(?:.*)"
        ]
    }
    
    # 关系抽取模式
    RELATION_PATTERNS = {
        "is_a": [r"(.*)是一种(.*)", r"(.*)属于(.*)类型"],
        "relates_to": [r"(.*)和(.*)相关", r"(.*)与(.*)有关"],
        "triggers": [r"(.*)导致(.*)", r"(.*)引发(.*)"],
        "supports": [r"(.*)支持(.*)", r"(.*)基于(.*)"],
        "contradicts": [r"(.*)与(.*)矛盾", r"(.*)不同于(.*)"]
    }
    
    def __init__(self, ontology_path: str = "data/ontology.jsonl"):
        self.ontology_path = Path(ontology_path)
        self.ontology_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 实体提及计数
        self.entity_mentions: Dict[str, int] = defaultdict(int)
        
        # 抽取日志
        self.extraction_log: List[LearningEvent] = []
        
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            "on_entity_extracted": [],
            "on_confidence_upgraded": [],
            "on_suggestion": []
        }
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调函数"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    # ==================== 触发条件检测 ====================
    
    def check_user_confirms(self, user_input: str) -> bool:
        """检查用户是否确认了推理结果"""
        confirm_patterns = [
            r"确认", r"是的", r"正确", r"对",
            r"同意", r"可以", r"采纳", r"好的",
            r"👍", r"✅", r"收到"
        ]
        return any(re.search(p, user_input) for p in confirm_patterns)
    
    def check_entity_mention(self, text: str) -> List[str]:
        """检测文本中的实体提及"""
        mentioned = []
        for entity_type, patterns in self.EXTRACT_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                mentioned.extend(matches)
        return mentioned
    
    def check_ontology_failed(self, query: str, results: Any) -> bool:
        """检查本体查询是否失败"""
        return results is None or (isinstance(results, list) and len(results) == 0)
    
    def check_user_correction(self, user_input: str) -> Optional[Dict]:
        """检查用户是否纠正了错误"""
        correction_patterns = [
            r"不是(?:.*)", r"错误", r"不对",
            r"应该是(?:.*)", r"纠正"
        ]
        for pattern in correction_patterns:
            match = re.search(pattern, user_input)
            if match:
                return {
                    "type": "correction",
                    "content": user_input,
                    "matched": match.group(0)
                }
        return None
    
    # ==================== 核心功能 ====================
    
    def extract_from_text(self, text: str) -> List[ExtractedEntity]:
        """从文本中抽取实体"""
        entities = []
        
        # 实体检测
        for entity_type_str, patterns in self.EXTRACT_PATTERNS.items():
            entity_type = EntityType(entity_type_str)
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    name = match if isinstance(match, str) else match
                    if name and len(name) > 1:
                        entities.append(ExtractedEntity(
                            entity_type=entity_type,
                            name=name.strip()
                        ))
        
        # 更新提及计数
        for entity in entities:
            self.entity_mentions[entity.name] += 1
        
        return entities
    
    def extract_relations(
        self,
        text: str,
        entities: List[ExtractedEntity]
    ) -> List[ExtractedRelation]:
        """从文本中抽取关系"""
        relations = []
        entity_names = [e.name for e in entities]
        
        for rel_type, patterns in self.RELATION_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match) >= 2:
                        subj, obj = match[0], match[1]
                        # 检查是否涉及已知实体
                        if any(e in subj or e in obj for e in entity_names):
                            relations.append(ExtractedRelation(
                                relation_type=rel_type,
                                subject=subj.strip(),
                                object=obj.strip()
                            ))
        
        return relations
    
    def check_high_frequency(self, threshold: int = 3) -> List[str]:
        """检查高频实体"""
        return [
            name for name, count in self.entity_mentions.items()
            if count >= threshold
        ]
    
    def upgrade_confidence(
        self,
        from_level: ConfidenceLevel,
        to_level: ConfidenceLevel
    ) -> bool:
        """置信度升级"""
        if from_level == ConfidenceLevel.ASSUMED and to_level == ConfidenceLevel.CONFIRMED:
            return True
        if from_level == ConfidenceLevel.SPECULATIVE and to_level == ConfidenceLevel.ASSUMED:
            return True
        return False
    
    # ==================== 写入本体 ====================
    
    def save_to_ontology(
        self,
        entities: List[ExtractedEntity],
        relations: List[ExtractedRelation]
    ) -> Dict[str, Any]:
        """保存到本体（增量更新）"""
        # 加载现有本体
        existing = self._load_ontology()
        
        # 检查去重
        new_entities = []
        for entity in entities:
            is_duplicate = False
            for obj in existing.get("objects", []):
                if obj.get("name") == entity.name:
                    is_duplicate = True
                    break
            if not is_duplicate:
                new_entities.append({
                    "type": entity.entity_type.value,
                    "name": entity.name,
                    "properties": entity.properties,
                    "confidence": entity.confidence.value,
                    "source": entity.source,
                    "created_at": entity.created_at
                })
        
        # 合并实体
        if "objects" not in existing:
            existing["objects"] = []
        existing["objects"].extend(new_entities)
        
        # 合并关系
        new_relations = []
        for rel in relations:
            new_relations.append({
                "type": rel.relation_type,
                "subject": rel.subject,
                "object": rel.object,
                "confidence": rel.confidence.value,
                "source": rel.source
            })
        
        if "links" not in existing:
            existing["links"] = []
        existing["links"].extend(new_relations)
        
        # 保存
        self._save_ontology(existing)
        
        # 记录日志
        event = LearningEvent(
            event_type="extraction",
            timestamp=datetime.now().isoformat(),
            content={
                "entities_extracted": len(new_entities),
                "relations_extracted": len(new_relations)
            },
            action_taken="save_to_ontology",
            result="success"
        )
        self.extraction_log.append(event)
        
        return {
            "entities_added": len(new_entities),
            "relations_added": len(new_relations),
            "total_entities": len(existing.get("objects", [])),
            "total_relations": len(existing.get("links", []))
        }
    
    def _load_ontology(self) -> Dict:
        """加载本体"""
        if self.ontology_path.exists():
            try:
                with open(self.ontology_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"objects": [], "links": []}
        return {"objects": [], "links": []}
    
    def _save_ontology(self, ontology: Dict):
        """保存本体"""
        with open(self.ontology_path, 'w', encoding='utf-8') as f:
            json.dump(ontology, f, ensure_ascii=False, indent=2)
    
    # ==================== 建议系统 ====================
    
    def suggest_supplement(self, query: str, failed_concepts: List[str]) -> List[str]:
        """建议补充本体"""
        suggestions = []
        
        for concept in failed_concepts:
            suggestions.append(f"建议补充 '{concept}' 相关的本体数据")
        
        # 通用建议
        if not suggestions:
            suggestions.append("本体中无相关数据，建议提供更多背景信息")
        
        # 记录日志
        event = LearningEvent(
            event_type="ontology_failed",
            timestamp=datetime.now().isoformat(),
            content={
                "query": query,
                "failed_concepts": failed_concepts
            },
            action_taken="suggest_supplement",
            result="\n".join(suggestions)
        )
        self.extraction_log.append(event)
        
        # 触发回调
        for callback in self.callbacks.get("on_suggestion", []):
            callback(suggestions)
        
        return suggestions
    
    # ==================== 统计 ====================
    
    def get_stats(self) -> Dict:
        """获取学习引擎统计"""
        return {
            "total_entities_extracted": sum(self.entity_mentions.values()),
            "unique_entities": len(self.entity_mentions),
            "high_frequency_entities": self.check_high_frequency(),
            "extraction_events": len(self.extraction_log),
            "callbacks_registered": sum(len(cbs) for cbs in self.callbacks.values())
        }
    
    def get_extraction_log(self, limit: int = 100) -> List[Dict]:
        """获取抽取日志"""
        return [
            {
                "event_type": e.event_type,
                "timestamp": e.timestamp,
                "content": e.content,
                "action_taken": e.action_taken,
                "result": e.result
            }
            for e in self.extraction_log[-limit:]
        ]


# 全局实例
auto_learn_engine = AutoLearnEngine()
