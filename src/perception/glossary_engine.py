import os
import re
import json
import logging
from typing import Dict, List, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

class GlossaryEngine:
    """
    业务语义词典引擎 (Glossary Engine)
    
    自动扫描数据库物理字典（Comment/DDL），利用 LLM 自动生成 Business Glossary。
    解决物理字段名（如 P1_MIN）与本体业务术语（如 进口压力最小值）之间的断裂。
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key or self.api_key == "mock":
            self.api_key = "e2e894dc-4ce5-4a7e-87d5-a7da2c12135a"
            
        self.base_url = os.getenv("OPENAI_BASE_URL") or "https://ark.cn-beijing.volces.com/api/v3"
        self.model = os.getenv("OPENAI_MODEL") or "doubao-seed-2-0-pro-260215"
        
        if self.api_key and self.api_key != "mock":
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

    def discover_glossary(self, ddl_text: str) -> Dict[str, str]:
        """
        根据 DDL 或元数据文本发现映射关系。
        策略：LLM json_object → LLM 纯文本解析 → 正则 DDL 注释提取
        """
        if not self.client:
            logger.warning("GlossaryEngine: No API key found, returning empty mock.")
            return {"P1_MAX": "出口压力最大值", "P2_MIN": "进口压力最小值"}

        prompt = (
            "你是一个资深数据建模专家。请分析以下数据库 DDL 或注释字段，"
            "提取物理字段名与其对应的中文业务语义，并以 JSON 格式返回 (Key: 物理名, Value: 业务名)。\n\n"
            f"DDL 内容:\n{ddl_text}\n\n"
            "注意：只返回 JSON，不要任何解释。"
        )
        
        # 策略1: 尝试 json_object 响应格式
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            mapping = json.loads(response.choices[0].message.content)
            return mapping
        except Exception as e:
            logger.warning(f"Glossary json_object mode failed, falling back to text mode: {e}")
        
        # 策略2: 不指定 response_format，从纯文本中解析 JSON
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content
            # 提取 JSON 块（可能被 ```json ... ``` 包裹）
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                mapping = json.loads(json_match.group())
                return mapping
        except Exception as e:
            logger.warning(f"Glossary text mode failed, falling back to regex: {e}")
        
        # 策略3: 正则从 DDL 注释中直接提取 (离线兜底)
        return self._extract_from_comments(ddl_text)
    
    def _extract_from_comments(self, ddl_text: str) -> Dict[str, str]:
        """从 DDL 注释中用正则提取物理名→业务名映射"""
        mapping = {}
        # 模式: -- FIELD_NAME 是/为/指 中文描述
        for m in re.finditer(r'--\s*([A-Z_][A-Z0-9_]*)\s*(?:是|为|指|→|->|:)\s*([\u4e00-\u9fff]+)', ddl_text):
            mapping[m.group(1)] = m.group(2)
        # 模式: COMMENT ON COLUMN ... IS '...' 或 DDL 内联注释
        for m in re.finditer(r'\b([A-Z_][A-Z0-9_]*)\s+\w+.*?--\s*([\u4e00-\u9fff]+)', ddl_text):
            if m.group(1) not in mapping:
                mapping[m.group(1)] = m.group(2)
        return mapping

    def enrich_extractor_context(self, current_context: str, ddl_source: str) -> str:
        """
        将新发现的业务词典注入到 KnowledgeExtractor 的 Prompt 上下文中
        """
        mapping = self.discover_glossary(ddl_source)
        glossary_str = "\n".join([f"- {k} -> {v}" for k, v in mapping.items()])
        
        enriched = (
            f"{current_context}\n\n"
            "### [Physical-to-Business Glossary Override]\n"
            "在处理以下特殊物理字段时，请务必映射到对应业务术语：\n"
            f"{glossary_str}"
        )
        return enriched
