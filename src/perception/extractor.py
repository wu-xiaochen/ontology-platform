import os
import json
import logging
import re
from typing import List, Optional

from pydantic import BaseModel, Field
from ..core.reasoner import Fact
from ..chunking.hierarchical import HierarchicalChunker

logger = logging.getLogger(__name__)


# ========================================
# Pydantic Schema（约束LLM输出格式）
# ========================================

class FactSchema(BaseModel):
    """
    单条事实三元组的结构化模型。
    用于约束大模型输出严格符合 RDF 三元组格式。
    """
    subject: str = Field(..., description="主体实体名称")
    predicate: str = Field(..., description="谓词（关系）")
    object: str = Field(..., description="客体（目标实体或属性值）")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="置信度")
    source: str = Field(default="llm_extraction", description="来源标识")


class KnowledgeExtractionResult(BaseModel):
    """提取的事实三元组集合"""
    facts: List[FactSchema] = Field(default_factory=list, description="提取的事实列表")


# ========================================
# 本体引导定义（Domain Ontology Schema）
# ========================================

CORE_DOMAIN_ONTOLOGY = """
[核心领域本体定义]
1. 核心类 (Classes):
   - 产品/设备: 燃气调压箱, 楼栋调压箱, 落地调压柜, 调压站设备
   - 核心部件: 调压器 (核心), 切断阀, 放散阀, 过滤器, 压力表, 流量计
   - 技术参数: 进口压力(P1), 出口压力(P2), 额定流量(Q), 稳压精度(AC), 关闭压力(SG)
   - 质量指标/检验: 气密性测试, 强度测试, 无损检测, 漆膜厚度, 响应时间
   - 业务场景: 居民小区, 工商业(餐饮/综合体), 工业园区, 老旧管网改造
   - 标准规范: GB 27791, GB 50028, GB 27790
   - 供应商/品牌: 费希尔, 特瑞斯, 春晖, 永良

2. 核心谓词 (Predicates):
   - 包含组件 (has_component)
   - 具备参数/规格 (has_parameter)
   - 适用场景 (applicable_to)
   - 符合/依据标准 (complies_with)
   - 属于分类 (subClassOf)
   - 质量要求/红线 (quality_requirement)
   - 工艺特性 (technical_feature)
"""

EXTRACTION_SYSTEM_PROMPT = f"""你是一个高精度的工业级本体知识抽取引擎。你的任务是从燃气设备相关的技术文档中提取结构化的知识三元组(Subject, Predicate, Object)。

{CORE_DOMAIN_ONTOLOGY}

输出规则：
1. 必须使用上述[核心领域本体定义]中的类名和谓词进行对齐。不要创造重复的同义词。
2. 提取密度：请尽可能全面提取所有技术细节，包括具体的数值范围（如 0.4-4.0 MPa）、标准号（如 GB 27791）和业务红线。
3. 如果文档提到"严禁"、"红线"或"故障原因"，请务必将其提取为 (Subject, quality_requirement, "...")。
4. 只输出一个合法的 JSON 对象，格式如下：
{{"facts": [{{"subject": "...", "predicate": "...", "object": "...", "confidence": 0.9}}]}}
5. 每次最多提取 30 条三元组以保证知识不遗漏。
6. 不要解释，不要加markdown格式，只输出纯JSON。"""

EXTRACTION_USER_PROMPT = """请从以下文本中提取知识三元组。只输出JSON，不要解释。

文本段落：
{text}"""


# ========================================
# 核心抽取器
# ========================================

class KnowledgeExtractor:
    """
    知识提取器 (Knowledge Extractor)
    
    工业级管道：长文档 → 分块 → 逐块LLM抽取 → JSON修复 → 合并去重 → 输出Fact列表
    
    架构特性：
    - 自动对长文档调用 HierarchicalChunker 分块
    - 每块独立调用 LLM，限制输出 ≤15 条三元组
    - 内置 JSON 修复逻辑（处理截断的输出）
    - 支持 Mock 模式用于单元测试
    """
    
    # 单块最大字符数（超过此值将触发分块）
    CHUNK_THRESHOLD = 1500
    # 每个LLM调用最大返回三元组数
    MAX_TRIPLES_PER_CALL = 30
    
    def __init__(self, use_mock_llm: bool = True):
        self.use_mock_llm = use_mock_llm
        self.chunker = HierarchicalChunker(max_tokens=2048, overlap_tokens=128)
        
        # LLM 客户端（延迟初始化）
        self._client = None
        self._model_id = None
    
    def _get_llm_client(self):
        """获取或创建 LLM 客户端（单例模式，避免重复创建）"""
        if self._client is None:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "mock":
                api_key = "e2e894dc-4ce5-4a7e-87d5-a7da2c12135a"
                
            base_url = os.getenv("OPENAI_BASE_URL") or "https://ark.cn-beijing.volces.com/api/v3"
            self._model_id = os.getenv("OPENAI_MODEL") or "doubao-seed-2-0-pro-260215"
            self._client = OpenAI(api_key=api_key, base_url=base_url)
        return self._client, self._model_id
    
    def _repair_json(self, raw: str) -> Optional[dict]:
        """
        修复可能被截断或包含多余字符的 JSON 输出。
        
        策略：
        1. 先尝试直接解析
        2. 去除 markdown code fence
        3. 查找最外层 { } 边界
        4. 补全被截断的 JSON 数组
        """
        if not raw or not raw.strip():
            return None
        
        text = raw.strip()
        
        # 去除 markdown 代码块标记
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()
        
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 查找 JSON 对象边界
        start = text.find('{')
        if start == -1:
            return None
        
        # 尝试找到匹配的结束括号
        depth = 0
        end = -1
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        
        if end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        
        # 最后手段：截断JSON修复（在最后一个完整的 } 后补全数组和对象）
        truncated = text[start:]
        # 找到最后一个}的位置
        last_complete = truncated.rfind('}')
        if last_complete > 0:
            candidate = truncated[:last_complete + 1]
            # 补全可能缺失的 ] 和 }
            open_brackets = candidate.count('[') - candidate.count(']')
            open_braces = candidate.count('{') - candidate.count('}')
            candidate += ']' * max(0, open_brackets)
            candidate += '}' * max(0, open_braces)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"JSON修复失败，原始输出长度: {len(raw)}")
        return None
    
    def _extract_chunk(self, text: str, extra_prompt: Optional[str] = None) -> List[FactSchema]:
        """
        对单个文本块调用LLM进行三元组抽取。
        
        Args:
            text: 待抽取的文本块
            extra_prompt: 额外的 Prompt 指示（如 Glossary 映射）
        """
        if not text.strip():
            return []
        
        system_prompt = EXTRACTION_SYSTEM_PROMPT
        if extra_prompt:
            system_prompt = f"{system_prompt}\n\n[ADDITIONAL CONTEXT]\n{extra_prompt}"

        try:
            client, model_id = self._get_llm_client()
            
            import time
            max_retries = 3
            backoff = 2
            
            for attempt in range(max_retries):
                try:
                    completion = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": EXTRACTION_USER_PROMPT.format(text=text[:3000])}
                        ],
                        temperature=0.1,
                        max_tokens=2048
                    )
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        wait_time = backoff ** (attempt + 1)
                        logger.warning(f"触发频率限制 (429)，{wait_time}s 后重试 (第 {attempt+1} 次)...")
                        time.sleep(wait_time)
                        continue
                    raise e
            
            raw_output = completion.choices[0].message.content
            parsed = self._repair_json(raw_output)
            
            if not parsed or "facts" not in parsed:
                logger.warning(f"LLM抽取返回无法解析的内容 (长度: {len(raw_output or '')})")
                return []
            
            # 手动验证并转换为 Pydantic 模型
            facts = []
            for item in parsed["facts"][:self.MAX_TRIPLES_PER_CALL]:
                try:
                    fact = FactSchema(
                        subject=str(item.get("subject", "")).strip(),
                        predicate=str(item.get("predicate", "")).strip(),
                        object=str(item.get("object", "")).strip(),
                        confidence=float(item.get("confidence", 0.9)),
                        source=str(item.get("source", "llm_extraction"))
                    )
                    # 过滤空值
                    if fact.subject and fact.predicate and fact.object:
                        facts.append(fact)
                except Exception as e:
                    logger.debug(f"跳过无效三元组: {item}, 原因: {e}")
            
            return facts
            
        except Exception as e:
            logger.error(f"LLM抽取调用失败: {e}")
            return []
    
    def _call_mock_llm(self, text: str) -> KnowledgeExtractionResult:
        """模拟LLM抽取（用于单元测试和离线开发）"""
        logger.info("[Mock LLM] Processing text for extraction...")
        mock_facts = []
        if "Supplier 'SafeGas_Corp' has ISO9001" in text:
            mock_facts.append(FactSchema(
                subject="SafeGas_Corp", predicate="has_iso9001_cert",
                object="true", confidence=0.98, source="doc_parsing"
            ))
        elif "risk" in text.lower():
            mock_facts.append(FactSchema(
                subject="SupplierA", predicate="status",
                object="high_risk", confidence=0.7, source="doc_parsing"
            ))
        return KnowledgeExtractionResult(facts=mock_facts)

    def extract_from_text(self, text: str, extra_prompt: Optional[str] = None) -> List[Fact]:
        """
        从文本中提取知识三元组。
        
        Args:
            text: 非结构化的输入文本
            extra_prompt: 额外的 Prompt 引导（如业务词典映射）
            
        Returns:
            List[Fact]: 去重后的标准本体事实对象列表
        """
        logger.info(f"KnowledgeExtractor 开始提取知识 (长度: {len(text)})")
        
        try:
            if self.use_mock_llm:
                extraction_result = self._call_mock_llm(text)
                all_fact_schemas = extraction_result.facts
            else:
                # 判断是否需要分块
                if len(text) > self.CHUNK_THRESHOLD:
                    chunks = self.chunker.chunk(text)
                    if not chunks:
                        # chunker 可能因文本格式无法识别标题而返回空
                        # 降级为简单按段落分块
                        chunks = self.chunker.chunk_by_paragraphs(text, min_tokens=50)
                    
                    if not chunks:
                        # 最后降级：直接按字符数切分
                        chunk_texts = [text[i:i+self.CHUNK_THRESHOLD] 
                                      for i in range(0, len(text), self.CHUNK_THRESHOLD)]
                    else:
                        chunk_texts = [c.text for c in chunks]
                    
                    logger.info(f"长文档分块: {len(chunk_texts)} 个块")
                else:
                    chunk_texts = [text]
                
                # 逐块抽取
                all_fact_schemas = []
                for i, chunk_text in enumerate(chunk_texts):
                    logger.info(f"正在抽取第 {i+1}/{len(chunk_texts)} 块 (长度: {len(chunk_text)})")
                    chunk_facts = self._extract_chunk(chunk_text, extra_prompt=extra_prompt)
                    all_fact_schemas.extend(chunk_facts)
                    logger.info(f"  → 本块抽取出 {len(chunk_facts)} 条三元组")
            
            # 去重（基于 subject+predicate+object 的唯一键）
            seen = set()
            unique_facts = []
            for item in all_fact_schemas:
                key = (item.subject, item.predicate, item.object)
                if key not in seen:
                    seen.add(key)
                    unique_facts.append(item)
            
            # 转换为系统核心 Fact 对象
            core_facts = [
                Fact(
                    subject=item.subject,
                    predicate=item.predicate,
                    object=item.object,
                    confidence=item.confidence,
                    source=item.source
                )
                for item in unique_facts
            ]
            
            logger.info(f"成功提取 {len(core_facts)} 条去重后的结构化事实 (原始: {len(all_fact_schemas)})")
            return core_facts
            
        except Exception as e:
            logger.error(f"提取过程失败: {str(e)}")
            return []
