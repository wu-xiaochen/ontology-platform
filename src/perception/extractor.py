import logging
from typing import List
from pydantic import BaseModel, Field
from core.reasoner import Fact

logger = logging.getLogger(__name__)

class FactSchema(BaseModel):
    """
    FactSchema (Pydantic Model)
    用于约束大模型输出严格符合 RDF 三元组格式。这种结构化输出从源头阻断了 LLM 的发散和幻觉。
    """
    subject: str = Field(..., description="主体名称，如 '公司A', '设备B', '人物C'")
    predicate: str = Field(..., description="谓词（关系或属性），强烈建议使用下划线命名法，如 'has_certification', 'operates_at'")
    object: str = Field(..., description="客体（属性值或关联目标），如 'ISO9001', 'true', '公司D'")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="对该事实提取准确度的置信度 (0.0 到 1.0)")
    source: str = Field(default="llm_extraction", description="信息来源")

class KnowledgeExtractionResult(BaseModel):
    """
    包含提取出的多条事实三元组的集合。
    """
    facts: List[FactSchema] = Field(default_factory=list, description="提取出的事实列表")


class KnowledgeExtractor:
    """
    知识提取器 (Knowledge Extractor)
    
    使用 Pydantic 结构化输出约束，将非结构化文本通过 LLM 转换为明确且合法的本体事实。
    """
    def __init__(self, use_mock_llm: bool = True):
        self.use_mock_llm = use_mock_llm

    def _call_mock_llm(self, text: str) -> KnowledgeExtractionResult:
        """
        模拟大模型的 JSON 结构化输出调用。
        在真实环境中，这里对接 openai.beta.chat.completions.parse(..., response_format=KnowledgeExtractionResult)
        """
        logger.info("[Mock LLM] Processing text for extraction...")
        # 简单模拟：如果文本包含 safe 等关键词，尝试提取
        mock_facts = []
        if "Supplier 'SafeGas_Corp' has ISO9001" in text:
            mock_facts.append(FactSchema(
                subject="SafeGas_Corp",
                predicate="has_iso9001_cert",
                object="true",
                confidence=0.98,
                source="doc_parsing"
            ))
            mock_facts.append(FactSchema(
                subject="SafeGas_Corp",
                predicate="operates_above_10bar",
                object="true",
                confidence=0.95,
                source="doc_parsing"
            ))
        elif "risk" in text.lower():
             mock_facts.append(FactSchema(
                subject="SupplierA",
                predicate="status",
                object="high_risk",
                confidence=0.7,
                source="doc_parsing"
            ))
        
        return KnowledgeExtractionResult(facts=mock_facts)

    def extract_from_text(self, text: str) -> List[Fact]:
        """
        从文本中提取知识三元组
        
        Args:
            text: 非结构化的输入文本（文档段落、聊天记录）
            
        Returns:
            List[Fact]: 转换后的标准本体事实对象列表
        """
        logger.info(f"KnowledgeExtractor 开始提取知识 (长度: {len(text)})")
        
        try:
            if self.use_mock_llm:
                extraction_result = self._call_mock_llm(text)
            else:
                try:
                    import os
                    from openai import OpenAI
                    
                    api_key = os.getenv("OPENAI_API_KEY", "sk-zueyelhrtzsngjdnqfnwfbsboockestuzwwhujpqrjmjmxyy")
                    base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
                    model_id = os.getenv("OPENAI_MODEL", "Pro/MiniMaxAI/MiniMax-M2.5")
                    
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    completion = client.beta.chat.completions.parse(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": "You are a precise ontological extraction bot. Extract formal RDF triples from unformatted text."},
                            {"role": "user", "content": f"Extract formal triples from: {text}"}
                        ],
                        response_format=KnowledgeExtractionResult,
                    )
                    extraction_result = completion.choices[0].message.parsed
                except ImportError:
                    logger.error("OpenAI package not installed. run `pip install openai`.")
                    return []
                except Exception as e:
                    logger.error(f"OpenAI (SiliconFlow) API error: {e}")
                    # Fallback to empty if API fails in production
                    return []

            # 将 Pydantic Models 转换为系统的 Fact Core Objects
            core_facts = []
            for item in extraction_result.facts:
                core_facts.append(Fact(
                    subject=item.subject,
                    predicate=item.predicate,
                    object=item.object,
                    confidence=item.confidence,
                    source=item.source
                ))
            
            logger.info(f"成功提取 {len(core_facts)} 条结构化事实")
            return core_facts
            
        except Exception as e:
            logger.error(f"提取过程失败: {str(e)}")
            return []
