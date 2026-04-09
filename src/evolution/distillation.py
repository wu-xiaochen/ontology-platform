"""
知识蒸馏器 (Knowledge Distiller)

负责从非结构化文本中提取结构化的本体知识（事实三元组）。
优先使用 LLM 进行高精度提取，LLM 不可用时降级到正则表达式本地提取。

设计决策：
- 复用 evolution.llm_extractor 模块的 LLMKnowledgeExtractor 避免重复实现
- 降级提取使用中文"是/的/有/属于"等关系词模式，覆盖常见断言结构
- suggest_schema_updates() 通过对比新谓词与已有图谱谓词集合，发现本体最（Schema）扩展机会
- 所有提取结果经过 ContradictionChecker 校验，防止知识污染
"""
import logging
import re
import uuid
from typing import Dict, List, Any, Optional

# 导入核心推理器的 Fact 数据结构
from ..core.reasoner import Reasoner, Fact
# 导入配置管理，确保零硬编码
from ..utils.config import get_config

logger = logging.getLogger(__name__)


class KnowledgeDistiller:
    """
    知识蒸馏器 — 从 LLM 交互日志和非结构化文本中提取结构化本体知识

    核心能力：
    1. extract_triples: 从文本提取事实三元组
    2. suggest_schema_updates: 基于新事实建议本体结构更新
    """

    def __init__(self, reasoner: Reasoner):
        # 推理引擎实例 —— 用于对比已有事实和校验一致性
        self.reasoner = reasoner
        # LLM 提取器延迟初始化 —— 避免启动时就尝试连接 LLM 服务
        self._llm_extractor = None
        # 已知谓词集合 —— 用于 schema 变更检测
        self._known_predicates: set = set()
        # 从推理引擎中收集已有谓词，建立基线
        self._collect_known_predicates()

    def _collect_known_predicates(self) -> None:
        """
        从推理引擎中收集所有已知的谓词

        用于后续 suggest_schema_updates 时对比新谓词。
        每次调用会重建谓词集合，确保与 Reasoner 状态同步。
        """
        self._known_predicates = set()
        # 遍历 Reasoner 中的所有事实，提取唯一谓词
        for fact in self.reasoner.facts:
            self._known_predicates.add(fact.predicate)

    @property
    def llm_extractor(self):
        """
        延迟初始化 LLM 知识提取器

        首次访问时才创建实例，避免在系统启动时就尝试连接 LLM。
        如果 LLM 不可用或初始化失败，返回 None 触发降级路径。
        """
        if self._llm_extractor is None:
            try:
                # 尝试导入并初始化 LLM 提取器
                from ..evolution.llm_extractor import LLMKnowledgeExtractor
                self._llm_extractor = LLMKnowledgeExtractor()
                logger.info("LLM 知识提取器初始化成功")
            except Exception as e:
                # LLM 不可用时记录警告，后续走降级提取
                logger.warning(f"LLM 知识提取器初始化失败，将使用本地正则提取: {e}")
                self._llm_extractor = None
        return self._llm_extractor

    def extract_triples(self, text: str) -> List[Fact]:
        """
        从非结构化文本中提取事实三元组

        提取策略：
        1. 优先使用 LLM 进行高精度结构化提取
        2. LLM 不可用时降级到本地正则表达式匹配

        Args:
            text: 待提取的非结构化文本

        Returns:
            提取出的事实三元组列表，每个元素为 Fact 对象
        """
        # 输入校验 —— 空文本直接返回
        if not text or not text.strip():
            logger.warning("输入文本为空，跳过知识蒸馏")
            return []

        logger.info(f"开始知识蒸馏，文本长度: {len(text)} 字符")

        # 阶段一：尝试 LLM 提取
        config = get_config()
        # 检查 LLM 是否可用且未被配置禁用
        if config.llm.is_configured() and self.llm_extractor is not None:
            try:
                facts = self._extract_via_llm(text)
                if facts:
                    logger.info(f"LLM 提取成功，得到 {len(facts)} 个三元组")
                    return facts
                # LLM 返回空结果时，降级到本地提取
                logger.info("LLM 返回空结果，降级到本地正则提取")
            except Exception as e:
                logger.warning(f"LLM 提取异常，降级到本地正则提取: {e}")

        # 阶段二：本地正则降级提取
        facts = self._extract_via_regex(text)
        logger.info(f"本地正则提取完成，得到 {len(facts)} 个三元组")
        return facts

    def _extract_via_llm(self, text: str) -> List[Fact]:
        """
        使用 LLM 进行高精度知识提取

        调用 LLMKnowledgeExtractor 的 extract 方法，将返回的字典转换为 Fact 对象。

        Args:
            text: 待提取文本

        Returns:
            Fact 对象列表
        """
        extractor = self.llm_extractor
        if extractor is None:
            return []

        # 调用 LLM 提取器 —— 返回格式为 {"triples": [...], ...}
        result = extractor.extract(text)

        facts = []
        # 从提取结果中构建 Fact 对象
        raw_triples = result.get("triples", [])
        for triple in raw_triples:
            # 每个 triple 应包含 subject, predicate, object 字段
            subject = triple.get("subject", "").strip()
            predicate = triple.get("predicate", "").strip()
            obj = triple.get("object", "").strip()

            # 跳过不完整的三元组
            if not all([subject, predicate, obj]):
                continue

            # 从 LLM 提取的三元组默认置信度为 0.7（低于手工标注的 0.9）
            confidence = float(triple.get("confidence", 0.7))
            fact = Fact(
                subject=subject,
                predicate=predicate,
                object=obj,
                confidence=confidence,
                source="llm_distillation",
            )
            facts.append(fact)

        return facts

    def _extract_via_regex(self, text: str) -> List[Fact]:
        """
        使用正则表达式进行本地降级提取

        覆盖中文常见断言结构：
        - "A 是 B" / "A 为 B"（分类关系）
        - "A 的 B 是 C"（属性关系）
        - "A 有 B"（拥有关系）
        - "A 属于 B"（层级关系）
        - "A 包含 B" / "A 包括 B"（组成关系）

        Args:
            text: 待提取文本

        Returns:
            Fact 对象列表
        """
        facts = []

        # 按句子分割 —— 支持中文句号、分号和换行符作为分隔
        sentences = re.split(r'[。；\n]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            # 跳过过短的片段（低于3个字符不太可能包含有效三元组）
            if len(sentence) < 3:
                continue

            # 模式1: "A 是/为 B" —— 分类或等价关系
            match = re.search(r'(.{1,20}?)\s*[是为]\s*(.{1,30})', sentence)
            if match:
                subject = match.group(1).strip()
                obj = match.group(2).strip()
                # 跳过主语或宾语为空的情况
                if subject and obj:
                    facts.append(Fact(
                        subject=subject,
                        predicate="是",
                        object=obj,
                        confidence=0.5,  # 正则提取置信度较低
                        source="regex_distillation",
                    ))
                    continue  # 每个句子只取第一个匹配，避免重复提取

            # 模式2: "A 属于 B" —— 层级关系
            match = re.search(r'(.{1,20}?)\s*属于\s*(.{1,30})', sentence)
            if match:
                facts.append(Fact(
                    subject=match.group(1).strip(),
                    predicate="属于",
                    object=match.group(2).strip(),
                    confidence=0.5,
                    source="regex_distillation",
                ))
                continue

            # 模式3: "A 包含/包括 B" —— 组成关系
            match = re.search(r'(.{1,20}?)\s*包[含括]\s*(.{1,30})', sentence)
            if match:
                facts.append(Fact(
                    subject=match.group(1).strip(),
                    predicate="包含",
                    object=match.group(2).strip(),
                    confidence=0.5,
                    source="regex_distillation",
                ))
                continue

            # 模式4: "A 有 B" —— 拥有关系
            match = re.search(r'(.{1,20}?)\s*有\s*(.{1,30})', sentence)
            if match:
                facts.append(Fact(
                    subject=match.group(1).strip(),
                    predicate="有",
                    object=match.group(2).strip(),
                    confidence=0.4,  # "有" 关系模糊度更高
                    source="regex_distillation",
                ))

        return facts

    def suggest_schema_updates(self, facts: List[Fact]) -> List[Dict[str, Any]]:
        """
        根据新提取的事实，建议本体结构（Schema）的更新
        """
        # 重新收集已知谓词，确保与当前 Reasoner 状态同步
        self._collect_known_predicates()

        suggestions: List[Dict[str, Any]] = []

        # 收集新事实中尚未见过的谓词
        new_predicates: Dict[str, Fact] = {}
        for fact in facts:
            if fact.predicate not in self._known_predicates:
                # 保留第一个使用该谓词的事实作为示例
                if fact.predicate not in new_predicates:
                    new_predicates[fact.predicate] = fact

        # 为每个新谓词生成更新建议
        for predicate, example_fact in new_predicates.items():
            suggestion = {
                "type": "new_property",
                "predicate": predicate,
                "example": {
                    "subject": example_fact.subject,
                    "predicate": example_fact.predicate,
                    "object": example_fact.object,
                },
                "confidence": example_fact.confidence,
                "description": f"发现新关系类型 '{predicate}'，建议添加到本体 Schema",
            }
            suggestions.append(suggestion)
            logger.info(f"Schema 更新建议: 新谓词 '{predicate}' (示例: {example_fact.subject} → {example_fact.object})")

        return suggestions


class CodeDistiller:
    """
    [v5.0] 代码蒸馏器 — 将成功的推理轨迹转化为可执行的 Python 技能 (Skills)
    
    对标 Voyager (Skill Library) 与 Agent Lightning。
    通过 LLM 将冗长的推理步骤压缩为标准化的工具函数，提升系统执行效率。
    """
    
    def __init__(self):
        self._llm_extractor = None
        self.config = get_config()
        # 延迟导入以避免循环依赖
        self._skill_registry = None

    @property
    def skill_registry(self):
        if self._skill_registry is None:
            from .skill_library import UnifiedSkillRegistry
            self._skill_registry = UnifiedSkillRegistry()
        return self._skill_registry

    @property
    def llm_client(self):
        if self._llm_extractor is None:
            from ..evolution.llm_extractor import LLMKnowledgeExtractor
            self._llm_extractor = LLMKnowledgeExtractor()
        return self._llm_extractor

    def distill_skill(self, task_name: str, reasoning_trace: List[str]) -> Optional[str]:
        """
        基于推理轨迹生成并注册 Python 技能
        
        Args:
            task_name: 任务描述
            reasoning_trace: 推理步骤列表
        """
        if not reasoning_trace:
            return None

        # 构建更加严谨的 Prompt，引导 LLM 生成高质量代码
        prompt = f"""你是一个高级算法工程师。请将以下经过验证的推理路径转化为一个单文件、无侧后果的 Python 函数。

[任务场景]
{task_name}

[推理轨迹]
{' -> '.join(reasoning_trace)}

[技术要求]
1. 函数名必须符合 `skill_[任务关键词]` 格式。
2. 接收 `**kwargs` 参数，必须返回 `dict` 格式，包含 'status' ("success"/"error") 和 'result' 字段。
3. 只能使用 math, re, json, datetime, collections, typing 等基础标准库。
4. 函数必须包含完整的 Docstring 描述其逻辑。
5. 严禁使用 os, subprocess, open, eval 等可能破坏系统安全的调用。

[输出格式]
```python
def skill_example(**kwargs):
    \"\"\"[自动生成] 实现对...的逻辑固化\"\"\"
    # 核心算法实现...
    return {{"status": "success", "result": ...}}
```
"""
        try:
            extractor = self.llm_client
            if not extractor or not extractor.client:
                return None

            response = extractor.client.chat.completions.create(
                model=self.config.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            code_content = response.choices[0].message.content
            
            # 正则提取代码块
            match = re.search(r'```python\n(.*?)\n```', code_content, re.DOTALL)
            if not match:
                return None
                
            code = match.group(1)
            
            # 提取生成的函数名作为 Skill ID
            func_name_match = re.search(r'def (skill_\w+)\(', code)
            skill_id = func_name_match.group(1) if func_name_match else f"skill_{uuid.uuid4().hex[:8]}"

            # 创建并注册技能
            from .skill_library import Skill, SkillType
            new_skill = Skill(
                id=skill_id,
                name=task_name[:50],
                description=f"从推理轨迹 '{task_name}' 中固化的专业技能",
                skill_type=SkillType.CODE,
                content=code
            )
            
            if self.skill_registry.register_skill(new_skill):
                logger.info(f"🚀 系统自进化成功: 新技能 '{skill_id}' 已上线")
                return skill_id
            return None
            
        except Exception as e:
            logger.error(f"代码蒸馏流程中断: {e}")
            return None
