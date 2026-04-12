"""
LLM 驱动的知识提取器

用 LLM Structured Output 从任意领域文本中提取结构化知识：
  - 实体 (entities)
  - 关系/事实三元组 (relations)
  - 条件规则 (rules)
  - 领域识别 (domain)

三级降级策略: LLM JSON -> LLM 纯文本解析 -> 正则 fallback
"""
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..utils.config import get_config

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 提取结果数据结构
# ─────────────────────────────────────────────

@dataclass
class ExtractedEntity:
    """提取到的实体"""
    name: str
    type: str  # e.g. "设备", "疾病", "药物", "人物"
    description: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExtractedRelation:
    """提取到的关系 / 事实三元组"""
    subject: str
    predicate: str
    object: str
    confidence: float = 0.8


@dataclass
class ExtractedRule:
    """提取到的条件规则"""
    condition: str
    action: str
    description: str = ""
    confidence: float = 0.8


@dataclass
class ExtractionResult:
    """LLM 提取的完整结果"""
    entities: List[ExtractedEntity] = field(default_factory=list)
    relations: List[ExtractedRelation] = field(default_factory=list)
    rules: List[ExtractedRule] = field(default_factory=list)
    domain: str = "generic"
    summary: str = ""
    source: str = "llm"  # "llm" | "regex_fallback"


# ─────────────────────────────────────────────
# 切块与分布处理
# ─────────────────────────────────────────────

class SemanticChunker:
    """文本语义切分器，用于将超长文本切分为适合 LLM 抽取的片段"""
    @staticmethod
    def chunk_text(text: str, max_chunk_size: int = 3000) -> List[str]:
        if len(text) <= max_chunk_size:
            return [text]
            
        chunks = []
        # 以句号为主要分割点，尽量保持句子完整
        sentences = [s + '。' for s in text.split('。') if s.strip()]
        current_chunk = ""
        for s in sentences:
            if len(current_chunk) + len(s) > max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = s
            else:
                current_chunk += s
        if current_chunk:
            chunks.append(current_chunk)
        return chunks


# ─────────────────────────────────────────────
# LLM 知识提取器
# ─────────────────────────────────────────────

class LLMKnowledgeExtractor:
    """
    LLM 驱动的知识提取器

    三级降级:
      1. LLM + JSON 响应 → 结构化提取
      2. LLM + 纯文本 → 解析 JSON 块
      3. 正则 fallback → 基础模式匹配
    """

    def __init__(self):
        cfg = get_config()
        llm_cfg = cfg.llm
        perf_cfg = getattr(cfg, 'performance', None)
        
        self.api_key = llm_cfg.api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = llm_cfg.base_url or os.getenv(
            "OPENAI_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
        )
        self.model = llm_cfg.model or os.getenv("OPENAI_MODEL", "doubao-seed-2-0-pro-260215")

        # 如果 api_key 是默认的空串、mock 或明显的占位符，尝试使用环境变量
        if not self.api_key or self.api_key in ("mock", "sk-secret", "sk-test", "test"):
            self.api_key = os.getenv("OPENAI_API_KEY", "")

        self.client: Optional[OpenAI] = None
        if self.api_key and self.api_key not in ("mock", "sk-secret", "sk-test", "test"):
            try:
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception as e:
                logger.warning(f"LLM 客户端初始化失败: {e}")

        # 提取缓存 (text_hash -> ExtractionResult)
        # 从配置读取缓存大小限制，避免无限制增长导致内存泄漏
        # 默认最大缓存 1000 条，可通过 CACHE_MAX_SIZE 环境变量配置
        self._max_cache_size: int = getattr(perf_cfg, 'cache_max_size', 1000) if perf_cfg else 1000
        self._cache: Dict[str, ExtractionResult] = {}
        # LLM 连续失败计数，超过阈值自动降级到正则
        self._consecutive_failures = 0
        self._max_failures = cfg.llm_fallback.max_consecutive_failures  # 从配置读取最大连续失败次数

    @property
    def is_available(self) -> bool:
        """LLM 是否可用"""
        return self.client is not None and self._consecutive_failures < self._max_failures

    def extract(self, text: str, domain_hint: str = None) -> ExtractionResult:
        """
        从文本提取结构化知识（同步方法）

        Args:
            text: 输入文本
            domain_hint: 领域提示

        Returns:
            ExtractionResult
        """
        # 缓存检查
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self._cache:
            logger.info("LLM 提取: 命中缓存")
            return self._cache[text_hash]

        cfg = get_config()
        max_len = getattr(cfg.evolution, "max_text_length", 3000)
        chunks = SemanticChunker.chunk_text(text, max_len)
        
        merged_result = ExtractionResult(
            entities=[], relations=[], rules=[], domain=domain_hint or "generic", summary="", source="llm"
        )
        
        for chunk in chunks:
            chunk_res = self._extract_with_fallback(chunk, domain_hint)
            
            # 合并实体 (按名字去重)
            entity_names = {e.name for e in merged_result.entities}
            for e in chunk_res.entities:
                if e.name not in entity_names:
                    merged_result.entities.append(e)
                    entity_names.add(e.name)
                    
            # 合并关系 (按主谓宾去重)
            relation_keys = {f"{r.subject}_{r.predicate}_{r.object}" for r in merged_result.relations}
            for r in chunk_res.relations:
                k = f"{r.subject}_{r.predicate}_{r.object}"
                if k not in relation_keys:
                    merged_result.relations.append(r)
                    relation_keys.add(k)
                    
            # 合并规则 (按条件与结果去重)
            rule_keys = {f"{r.condition}_{r.action}" for r in merged_result.rules}
            for r in chunk_res.rules:
                k = f"{r.condition}_{r.action}"
                if k not in rule_keys:
                    merged_result.rules.append(r)
                    rule_keys.add(k)
                    
            if chunk_res.source == "regex_fallback":
                merged_result.source = "regex_fallback"

        # 缓存结果前检查缓存大小，避免无限制增长
        # 如果缓存已满，清除最旧的 20% 条目（简单 LRU 策略）
        if len(self._cache) >= self._max_cache_size:
            keys_to_remove = list(self._cache.keys())[:int(self._max_cache_size * 0.2)]
            for key in keys_to_remove:
                del self._cache[key]
            logger.warning(f"缓存已满，已清除 {len(keys_to_remove)} 条旧缓存")
        
        self._cache[text_hash] = merged_result
        return merged_result
    
    def clear_cache(self) -> None:
        """
        清除提取缓存
        
        用于：
        1. 内存管理：释放不再需要的缓存数据
        2. 数据一致性：当底层知识库发生变更时
        3. 测试场景：重置提取器状态
        """
        self._cache.clear()
        logger.info("LLMKnowledgeExtractor 缓存已清除")

    def _extract_with_fallback(self, text: str, domain_hint: str = None) -> ExtractionResult:
        """三级降级提取"""
        if not self.client or self._consecutive_failures >= self._max_failures:
            logger.info("LLM 不可用，使用正则 fallback")
            return self._regex_fallback(text, domain_hint)

        cfg = get_config()
        prompt_template = getattr(cfg.evolution, "extraction_prompt", "")
        # 如果由于任何原因配置没拿到，还是提供基础保底
        if not prompt_template:
            prompt_template = "提取知识: \n{text}"
            
        prompt = prompt_template.format(text=text[:3000])
        prompt += "\n\n请直接输出 JSON 格式数据，严禁包含 Markdown 代码块标记符词汇，也不要包含任何额外解释。"

        # 策略 1: LLM + json_object
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
            )
            content = resp.choices[0].message.content or ""
            # 去除思维链标签（推理模型如 MiniMax-M2.7 会输出 <think>...</think>）
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            data = json.loads(content)
            result = self._parse_llm_output(data, domain_hint)
            result.source = "llm"
            self._consecutive_failures = 0  # 成功后重置计数
            logger.info(
                f"LLM JSON 提取成功: {len(result.entities)} 实体, "
                f"{len(result.relations)} 关系, {len(result.rules)} 规则"
            )
            return result
        except Exception as e:
            self._consecutive_failures += 1
            logger.warning(f"LLM json_object 模式失败: {e}")

        # 策略 2: 如果已达到失败阈值，直接 fallback
        if self._consecutive_failures >= self._max_failures:
            return self._regex_fallback(text, domain_hint)

        # LLM 纯文本，解析 JSON 块
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
            )
            content = resp.choices[0].message.content or ""
            # 去除思维链标签
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            # 查找 JSON 块
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                result = self._parse_llm_output(data, domain_hint)
                result.source = "llm"
                self._consecutive_failures = 0  # 成功后重置计数
                logger.info(
                    f"LLM 文本解析成功: {len(result.entities)} 实体, "
                    f"{len(result.relations)} 关系, {len(result.rules)} 规则"
                )
                return result
        except Exception as e:
            self._consecutive_failures += 1
            logger.warning(f"LLM 纯文本模式失败: {e}")

        # 策略 3: 正则 fallback
        logger.info("LLM 全部失败，使用正则 fallback")
        return self._regex_fallback(text, domain_hint)

    def _parse_llm_output(self, data: Dict, domain_hint: str = None) -> ExtractionResult:
        """解析 LLM 输出的 JSON 为 ExtractionResult"""
        entities = []
        for e in data.get("entities", []):
            if isinstance(e, dict) and e.get("name"):
                entities.append(ExtractedEntity(
                    name=e["name"],
                    type=e.get("type", "概念"),
                    description=e.get("description", ""),
                    attributes=e.get("attributes", {}),
                ))

        relations = []
        for r in data.get("relations", []):
            if isinstance(r, dict) and r.get("subject") and r.get("object"):
                relations.append(ExtractedRelation(
                    subject=r["subject"],
                    predicate=r.get("predicate", "related_to"),
                    object=r["object"],
                    confidence=float(r.get("confidence", 0.8)),
                ))

        rules = []
        for r in data.get("rules", []):
            if isinstance(r, dict) and (r.get("condition") or r.get("action")):
                rules.append(ExtractedRule(
                    condition=r.get("condition", ""),
                    action=r.get("action", ""),
                    description=r.get("description", ""),
                    confidence=float(r.get("confidence", 0.8)),
                ))

        domain = domain_hint or data.get("domain", "generic")
        summary = data.get("summary", "")

        return ExtractionResult(
            entities=entities,
            relations=relations,
            rules=rules,
            domain=domain,
            summary=summary,
        )

    def _regex_fallback(self, text: str, domain_hint: str = None) -> ExtractionResult:
        """正则 fallback — 基础模式匹配提取"""
        entities = []
        relations = []
        rules = []

        cfg = get_config()

        # 提取 "如果...那么..." 规则
        for m in re.finditer(getattr(cfg.evolution, "regex_rule_if_then", r'如果\s*([^，。\n]+)[，。]?\s*那么\s*([^。\n]+)'), text):
            rules.append(ExtractedRule(
                condition=m.group(1).strip(),
                action=m.group(2).strip(),
                description=f"如果 {m.group(1).strip()} 那么 {m.group(2).strip()}",
                confidence=0.7,
            ))

        # 提取 "X是Y" 定义 → 生成实体 + 关系
        for m in re.finditer(r'(?:^|(?<=。))\s*([^是。\n]{2,20})是(?:一种)?([^。\n]{2,80})', text):
            subj = m.group(1).strip()
            obj_desc = m.group(2).strip()
            entities.append(ExtractedEntity(name=subj, type="概念", description=obj_desc))
            relations.append(ExtractedRelation(
                subject=subj, predicate="is_a", object=obj_desc[:30],
                confidence=0.7,
            ))

        # 提取 "X属于Y" → 关系
        for m in re.finditer(r'([^。\n]{2,20})属于([^。\n]{2,30})', text):
            relations.append(ExtractedRelation(
                subject=m.group(1).strip(), predicate="is_a",
                object=m.group(2).strip(), confidence=0.7,
            ))

        # 简单领域检测
        domain = domain_hint or "generic"
        if not domain_hint:
            kw_map = {
                "gas_equipment": ["燃气", "调压", "压力", "阀门"],
                "medical": ["患者", "诊断", "治疗", "血糖", "药物"],
                "finance": ["投资", "收益", "风险"],
                "legal": ["合同", "违约", "赔偿"],
            }
            for d, kws in kw_map.items():
                if any(k in text for k in kws):
                    domain = d
                    break

        return ExtractionResult(
            entities=entities,
            relations=relations,
            rules=rules,
            domain=domain,
            summary="",
            source="regex_fallback",
        )


# ─────────────────────────────────────────────
# 基础提取器（无 LLM 依赖）
# ─────────────────────────────────────────────

class BaseFallbackExtractor:
    """
    基础知识提取器 - 不依赖 LLM，仅使用正则表达式和规则
    
    用途：
    1. 当 LLM 服务不可用时的降级方案
    2. 完全离线模式下的知识提取
    3. 作为 LLM 提取的补充（捕获格式化的结构化内容）
    
    特点：
    - 零外部依赖，纯正则表达式实现
    - 支持常见的中文知识表达格式
    - 轻量级，响应快速
    """
    
    # 领域关键词映射表，用于自动检测文本所属领域
    # 涵盖系统支持的主要业务领域
    DOMAIN_KEYWORDS: Dict[str, List[str]] = {
        "gas_equipment": ["燃气", "调压", "压力", "阀门", "设备", "维护", "检修", "安全"],
        "medical": ["患者", "诊断", "治疗", "血糖", "药物", "症状", "疾病", "医院"],
        "finance": ["投资", "收益", "风险", "市场", "股票", "基金", "利率"],
        "legal": ["合同", "违约", "赔偿", "法律", "条款", "诉讼", "责任"],
        "engineering": ["系统", "组件", "参数", "规格", "设计", "工程", "技术"],
    }
    
    def __init__(self):
        """初始化基础提取器，无需任何外部依赖"""
        # 从配置读取缓存大小限制，避免无限制增长导致内存泄漏
        cfg = get_config()
        perf_cfg = getattr(cfg, 'performance', None)
        # 默认最大缓存 500 条，可通过 CACHE_MAX_SIZE 环境变量配置
        self._max_cache_size: int = getattr(perf_cfg, 'cache_max_size', 500) if perf_cfg else 500
        # 提取缓存 (text_hash -> ExtractionResult)，避免重复处理相同文本
        self._cache: Dict[str, ExtractionResult] = {}
    
    @property
    def is_available(self) -> bool:
        """
        检查提取器是否可用
        
        基础提取器始终可用，因为它不依赖任何外部服务。
        这与 LLMKnowledgeExtractor 的接口保持一致。
        """
        return True
    
    
    def extract(self, text: str, domain_hint: str = None) -> ExtractionResult:
        """
        从文本中提取结构化知识（纯正则表达式实现）
        
        Args:
            text: 输入文本
            domain_hint: 可选的领域提示，用于跳过自动领域检测
            
        Returns:
            ExtractionResult 包含提取的实体、关系和规则
        """
        # 缓存检查：如果已处理过相同文本，直接返回缓存结果
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self._cache:
            logger.info("Fallback 提取器: 命中缓存")
            return self._cache[text_hash]
        
        # 执行提取
        result = self._extract_with_regex(text, domain_hint)
        
        # 缓存结果前检查缓存大小，避免无限制增长
        # 如果缓存已满，清除最旧的 20% 条目（简单 LRU 策略）
        if len(self._cache) >= self._max_cache_size:
            keys_to_remove = list(self._cache.keys())[:int(self._max_cache_size * 0.2)]
            for key in keys_to_remove:
                del self._cache[key]
            logger.warning(f"Fallback 提取器缓存已满，已清除 {len(keys_to_remove)} 条旧缓存")
        
        self._cache[text_hash] = result
        return result
    
    def clear_cache(self) -> None:
        """
        清除提取缓存
        
        用于：
        1. 内存管理：释放不再需要的缓存数据
        2. 数据一致性：当底层知识库发生变更时
        3. 测试场景：重置提取器状态
        """
        self._cache.clear()
        logger.info("BaseFallbackExtractor 缓存已清除")
    
    
    def _extract_with_regex(self, text: str, domain_hint: str = None) -> ExtractionResult:
        """
        使用正则表达式提取知识
        
        支持的格式：
        1. 条件规则：如果...那么...
        2. 定义：X是Y、X是一种Y
        3. 关系：X属于Y、X包含Y
        4. 属性：X的Y是Z
        """
        entities: List[ExtractedEntity] = []
        relations: List[ExtractedRelation] = []
        rules: List[ExtractedRule] = []
        
        cfg = get_config()
        # ── 规则提取 ──
        # 提取 "如果...那么..." 规则
        # 这是最常见的条件规则表达方式
        for m in re.finditer(getattr(cfg.evolution, "regex_rule_if_then", r'如果\s*([^，。\n]+)[，。]?\s*那么\s*([^。\n]+)'), text):
            rules.append(ExtractedRule(
                condition=m.group(1).strip(),
                action=m.group(2).strip(),
                description=f"如果 {m.group(1).strip()} 那么 {m.group(2).strip()}",
                confidence=0.75,  # 正则匹配的置信度略低于 LLM
            ))
        
        
        # 提取 "当...时，..." 规则（另一种条件规则表达）
        for m in re.finditer(getattr(cfg.evolution, "regex_rule_when", r'当\s*([^，。\n]+)[，。]?\s*时[，。]?\s*([^。\n]+)'), text):
            rules.append(ExtractedRule(
                condition=m.group(1).strip(),
                action=m.group(2).strip(),
                description=f"当 {m.group(1).strip()} 时，{m.group(2).strip()}",
                confidence=0.75,
            ))
        
        
        # ── 实体和关系提取 ──
        # 提取 "X是Y" 定义 → 生成实体 + 关系
        # 使用句子边界确保匹配的是完整句子
        for m in re.finditer(r'(?:^|(?<=[。！？]))\s*([^是。\n]{2,20})是(?:一种)?([^。\n]{2,80})', text):
            subj = m.group(1).strip()
            obj_desc = m.group(2).strip()
            # 过滤太短或太长的匹配
            if len(subj) >= 2 and len(obj_desc) >= 2:
                entities.append(ExtractedEntity(name=subj, type="概念", description=obj_desc))
                relations.append(ExtractedRelation(
                    subject=subj, predicate="is_a", object=obj_desc[:50],
                    confidence=0.7,
                ))
        
        
        # 提取 "X属于Y" → 分类关系
        for m in re.finditer(r'([^。\n]{2,20})属于([^。\n]{2,30})', text):
            subj = m.group(1).strip()
            obj = m.group(2).strip()
            if len(subj) >= 2 and len(obj) >= 2:
                relations.append(ExtractedRelation(
                    subject=subj, predicate="is_a",
                    object=obj, confidence=0.7,
                ))
        
        
        # 提取 "X包含Y" 或 "X包括Y" → 组成关系
        for m in re.finditer(r'([^。\n]{2,20})(?:包含|包括)([^。\n]{2,50})', text):
            subj = m.group(1).strip()
            obj = m.group(2).strip()
            if len(subj) >= 2 and len(obj) >= 2:
                relations.append(ExtractedRelation(
                    subject=subj, predicate="contains",
                    object=obj, confidence=0.7,
                ))
        
        
        # 提取 "X的Y是Z" → 属性关系
        for m in re.finditer(r'([^。\n]{2,20})的([^。\n]{2,15})是([^，。\n]{1,30})', text):
            subj = m.group(1).strip()
            attr = m.group(2).strip()
            value = m.group(3).strip()
            if len(subj) >= 2 and len(attr) >= 1:
                relations.append(ExtractedRelation(
                    subject=subj, predicate=f"has_{attr}",
                    object=value, confidence=0.65,
                ))
        
        
        # ── 领域检测 ──
        domain = domain_hint or "generic"
        if not domain_hint:
            # 基于关键词统计进行领域检测
            domain_scores = {}
            for d, kws in self.DOMAIN_KEYWORDS.items():
                # 计算关键词匹配数量
                matches = sum(1 for k in kws if k in text)
                if matches > 0:
                    domain_scores[d] = matches
            
            # 选择匹配最多的领域
            if domain_scores:
                domain = max(domain_scores.keys(), key=lambda x: domain_scores[x])
        
        
        logger.info(
            f"Fallback 提取完成: {len(entities)} 实体, "
            f"{len(relations)} 关系, {len(rules)} 规则, 领域={domain}"
        )
        
        return ExtractionResult(
            entities=entities,
            relations=relations,
            rules=rules,
            domain=domain,
            summary="",  # 基础提取器不生成摘要
            source="regex_fallback",
        )
