"""
配置管理模块

提供统一的配置加载、验证和管理功能
支持环境变量、配置文件和默认值

配置加载优先级：
1. 环境变量（最高优先级）
2. .env 文件
3. 代码默认值（最低优先级）
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

# 配置模块日志记录器
logger = logging.getLogger(__name__)

# 尝试加载 python-dotenv 以支持 .env 文件
try:
    from dotenv import load_dotenv
    # 查找项目根目录的 .env 文件
    _env_path = Path(__file__).parent.parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
        logger.debug(f"已加载 .env 文件: {_env_path}")
except ImportError:
    # python-dotenv 未安装时跳过，直接使用环境变量
    logger.debug("python-dotenv 未安装，跳过 .env 文件加载")


@dataclass
class LLMConfig:
    """LLM 配置"""
    # 主 LLM 配置
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4"))
    temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.7")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "2000")))
    timeout: int = field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT", "30")))
    # Embedding 配置
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "doubao-embedding-v1"))
    embedding_base_url: str = field(default_factory=lambda: os.getenv("EMBEDDING_BASE_URL", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")))
    
    # 重试配置
    max_retries: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "3")))
    retry_delay: float = field(default_factory=lambda: float(os.getenv("LLM_RETRY_DELAY", "1.0")))
    
    # 是否跳过 LLM 调用（完全离线模式）
    # 设置为 true 时，系统将只使用正则表达式和规则进行知识提取，不依赖外部 LLM 服务
    skip_llm: bool = field(default_factory=lambda: os.getenv("SKIP_LLM", "false").lower() == "true")
    
    def is_configured(self) -> bool:
        """
        检查是否已配置且未禁用 LLM
        
        如果设置了 skip_llm=true，即使有 API key 也返回 False，
        这允许用户在无需 LLM 的情况下运行系统（完全离线模式）。
        """
        # 如果设置了 skip_llm，即使有 API key 也返回 False
        if self.skip_llm:
            return False
        return bool(self.api_key) and self.api_key not in ("mock", "your_api_key_here")


@dataclass
class DatabaseConfig:
    """数据库配置"""
    neo4j_uri: str = field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_user: str = field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    neo4j_password: str = field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", "password"))
    chroma_path: str = field(default_factory=lambda: os.getenv("CHROMA_PATH", "./data/chroma_db"))
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return all([self.neo4j_uri, self.neo4j_user, self.neo4j_password])


@dataclass
class ReasoningConfig:
    """推理引擎配置"""
    max_inference_depth: int = int(os.getenv("REASONING_MAX_DEPTH", "5"))  # 最大推理深度
    timeout_seconds: float = float(os.getenv("REASONING_TIMEOUT", "5.0"))  # 推理超时时间（秒）
    min_confidence: float = float(os.getenv("REASONING_MIN_CONFIDENCE", "0.0"))  # 最低置信度阈值


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    decay_rate: float = float(os.getenv("MEMORY_DECAY_RATE", "0.05"))  # 置信度衰减率
    reinforce_rate: float = float(os.getenv("MEMORY_REINFORCE_RATE", "0.10"))  # 置信度强化率
    prune_threshold: float = float(os.getenv("MEMORY_PRUNE_THRESHOLD", "0.20"))  # 剪枝阈值
    sample_limit: int = int(os.getenv("MEMORY_SAMPLE_LIMIT", "50"))  # 样本数量限制
    search_top_k: int = int(os.getenv("MEMORY_SEARCH_TOP_K", "5"))  # 语义搜索 Top-K


@dataclass
class EvolutionConfig:
    """演化模块配置"""
    max_text_length: int = int(os.getenv("EVOLUTION_MAX_TEXT_LENGTH", "5000"))  # 文本处理最大长度
    min_support: int = int(os.getenv("EVOLUTION_MIN_SUPPORT", "2"))  # 规则发现最小支持度
    min_confidence: float = float(os.getenv("EVOLUTION_MIN_CONFIDENCE", "0.6"))  # 规则发现最小置信度
    confidence_high: float = float(os.getenv("CONFIDENCE_HIGH", "0.85"))  # 高置信度阈值
    confidence_medium: float = float(os.getenv("CONFIDENCE_MEDIUM", "0.60"))  # 中置信度阈值
    confidence_low: float = float(os.getenv("CONFIDENCE_LOW", "0.40"))  # 低置信度阈值
    # 知识评估器参数
    decay_interval: float = float(os.getenv("EVAL_DECAY_INTERVAL", "86400.0"))  # 置信度衰减周期(秒)
    decay_factor: float = float(os.getenv("EVAL_DECAY_FACTOR", "0.95"))  # 置信度衰减因子
    promote_threshold: float = float(os.getenv("EVAL_PROMOTE_THRESHOLD", "0.5"))  # CANDIDATE→ACTIVE最低分
    stale_threshold: float = float(os.getenv("EVAL_STALE_THRESHOLD", "0.3"))  # ACTIVE→STALE最低分
    archive_confidence: float = float(os.getenv("EVAL_ARCHIVE_CONFIDENCE", "0.15"))  # 归档置信度阈值
    redundancy_max_duplicates: int = int(os.getenv("EVAL_REDUNDANCY_MAX", "3"))  # 冗余检测上限
    quality_w_consistency: float = float(os.getenv("EVAL_W_CONSISTENCY", "0.3"))  # 一致性权重
    quality_w_redundancy: float = float(os.getenv("EVAL_W_REDUNDANCY", "0.2"))  # 冗余度权重
    quality_w_freshness: float = float(os.getenv("EVAL_W_FRESHNESS", "0.25"))  # 新鲜度权重
    quality_w_citation: float = float(os.getenv("EVAL_W_CITATION", "0.25"))  # 引用频率权重
    
    # 元逻辑引导配置：控制是否启用基础元规则引导
    # 这些元规则是系统推理的基础，但在某些场景（如纯自定义规则系统）可能需要禁用
    enable_bootstrap_rules: bool = field(default_factory=lambda: os.getenv("EVOLUTION_ENABLE_BOOTSTRAP", "true").lower() == "true")
    
    # 抽取 Prompt 和 fallback Regex（去硬编码）
    extraction_prompt: str = field(default_factory=lambda: os.getenv("EVOLUTION_EXTRACTION_PROMPT", "你是一个专业的知识工程师。请从以下文本中提取结构化知识，输出严格的 JSON。\n\n要求：\n1. **entities**: 提取所有有意义的实体（名词性概念），包含名称、类型、描述、关键属性\n2. **relations**: 提取实体之间的关系，形成三元组 (subject, predicate, object)。关系类型包括但不限于: is_a(属于), has(拥有), requires(需要), causes(导致), part_of(组成部分), produces(产生), located_in(位于), treats(治疗)等\n3. **rules**: 提取条件规则（如果...那么...、当...时...、...必须...）\n4. **domain**: 识别文本所属领域（如 gas_equipment, medical, legal, finance, engineering, 或具体的领域名称）\n5. **summary**: 用一句话概括文本的核心知识\n\n输出 JSON 格式（不要输出任何其他内容）：\n```json\n{{\n  \"entities\": [\n    {{\"name\": \"实体名\", \"type\": \"类型\", \"description\": \"描述\", \"attributes\": {{\"属性名\": \"属性值\"}}}}\n  ],\n  \"relations\": [\n    {{\"subject\": \"主语\", \"predicate\": \"谓语\", \"object\": \"宾语\", \"confidence\": 0.9}}\n  ],\n  \"rules\": [\n    {{\"condition\": \"条件\", \"action\": \"动作/结果\", \"description\": \"规则描述\", \"confidence\": 0.85}}\n  ],\n  \"domain\": \"领域名\",\n  \"summary\": \"核心知识概括\"\n}}\n```\n\n文本内容：\n{text}"))
    regex_rule_if_then: str = field(default_factory=lambda: os.getenv("EVOLUTION_REGEX_IF_THEN", r"如果\s*([^，。\n]+)[，。]?\s*那么\s*([^。\n]+)"))
    regex_rule_when: str = field(default_factory=lambda: os.getenv("EVOLUTION_REGEX_WHEN", r"当\s*([^，。\n]+)[，。]?\s*时[，。]?\s*([^。\n]+)"))
    # 元逻辑规则配置：基础传递性规则配置
    # 这些配置允许自定义元规则的核心参数，但规则结构是元逻辑层面的固定定义
    meta_transitivity_id: str = field(default_factory=lambda: os.getenv("META_TRANSITIVITY_ID", "meta:transitivity"))
    meta_transitivity_name: str = field(default_factory=lambda: os.getenv("META_TRANSITIVITY_NAME", "传递性规则"))
    meta_transitivity_confidence: float = field(default_factory=lambda: float(os.getenv("META_TRANSITIVITY_CONFIDENCE", "1.0")))
    
    # 元逻辑规则配置：分类继承规则配置
    meta_classification_id: str = field(default_factory=lambda: os.getenv("META_CLASSIFICATION_ID", "meta:classification"))
    meta_classification_name: str = field(default_factory=lambda: os.getenv("META_CLASSIFICATION_NAME", "分类继承规则"))
    meta_classification_confidence: float = field(default_factory=lambda: float(os.getenv("META_CLASSIFICATION_CONFIDENCE", "1.0")))
    
    # 元逻辑规则通用配置
    meta_rule_source: str = field(default_factory=lambda: os.getenv("META_RULE_SOURCE", "bootstrap"))


@dataclass
class ActionRuntimeConfig:
    """动作引擎配置"""
    max_chain_depth: int = int(os.getenv("ACTION_MAX_CHAIN_DEPTH", "5"))  # 规则链最大深度
    max_exec_time: float = float(os.getenv("ACTION_MAX_EXEC_TIME", "5.0"))  # 单个 execute 动作最大秒数


@dataclass
class ToolConfig:
    """
    工具系统配置
    
    配置 LLM 可调用的工具相关参数，包括工具名称、描述等。
    所有配置项均可通过环境变量覆盖，符合零硬编码原则。
    """
    # 核心工具配置：工具名称（唯一标识符）
    tool_ingest_name: str = os.getenv("TOOL_INGEST_NAME", "ingest_knowledge")
    tool_ingest_desc: str = os.getenv(
        "TOOL_INGEST_DESC",
        "将用户提供的原始文本直接送入知识抽取管道。你必须将用户的原文原文原封不动、一字不改地传入text参数。"
    )
    
    tool_query_name: str = os.getenv("TOOL_QUERY_NAME", "query_graph")
    tool_query_desc: str = os.getenv(
        "TOOL_QUERY_DESC",
        "连通 ChromaDB 和 Reasoner 双引擎进行推理查询。当用户提出溯源判定或逻辑推导时使用。YOU MUST USE THIS FOR QUESTIONS."
    )
    
    tool_action_name: str = os.getenv("TOOL_ACTION_NAME", "execute_action")
    tool_action_desc: str = os.getenv(
        "TOOL_ACTION_DESC",
        "执行本体动力学操作。当需要进行特定业务逻辑校验或驱动本体演进时使用。"
    )
    
    tool_evaluate_name: str = os.getenv("TOOL_EVALUATE_NAME", "evaluate_knowledge")
    tool_evaluate_desc: str = os.getenv(
        "TOOL_EVALUATE_DESC",
        "评估知识条目的质量和置信度。用于验证和打分已有知识。"
    )
    
    tool_feedback_name: str = os.getenv("TOOL_FEEDBACK_NAME", "provide_feedback")
    tool_feedback_desc: str = os.getenv(
        "TOOL_FEEDBACK_DESC",
        "提供反馈信息，用于持续优化知识库和推理能力。"
    )
    
    # 工具调用参数配置
    thought_process_required: bool = os.getenv("TOOL_THOUGHT_PROCESS_REQUIRED", "true").lower() == "true"
    default_top_k: int = int(os.getenv("TOOL_DEFAULT_TOP_K", "5"))  # 默认检索 Top-K
    max_query_depth: int = int(os.getenv("TOOL_MAX_QUERY_DEPTH", "5"))  # 查询最大深度


@dataclass
class GraphRAGConfig:
    """GraphRAG 检索增强配置"""
    # 社区检测参数
    community_algorithm: str = field(default_factory=lambda: os.getenv("GRAPHRAG_COMMUNITY_ALGORITHM", "louvain"))
    # Louvain 算法分辨率参数，值越大社区越细粒度
    louvain_resolution: float = field(default_factory=lambda: float(os.getenv("GRAPHRAG_LOUVAIN_RESOLUTION", "1.0")))
    # Girvan-Newman 最大迭代次数
    girvan_newman_max_iter: int = field(default_factory=lambda: int(os.getenv("GRAPHRAG_GN_MAX_ITER", "100")))
    # 最小社区规模，小于此值的社区将被合并
    min_community_size: int = field(default_factory=lambda: int(os.getenv("GRAPHRAG_MIN_COMMUNITY_SIZE", "3")))
    # 社区检测超时时间（秒），防止大规模图导致无限等待
    community_detection_timeout: float = field(default_factory=lambda: float(os.getenv("GRAPHRAG_COMMUNITY_TIMEOUT", "300.0")))
    
    # 检索策略参数
    # Local Search: 实体邻居扩展深度
    local_search_depth: int = field(default_factory=lambda: int(os.getenv("GRAPHRAG_LOCAL_DEPTH", "2")))
    # Local Search: 返回结果数量上限
    local_search_top_k: int = field(default_factory=lambda: int(os.getenv("GRAPHRAG_LOCAL_TOP_K", "20")))
    # Global Search: 检索社区数量
    global_search_communities: int = field(default_factory=lambda: int(os.getenv("GRAPHRAG_GLOBAL_COMMUNITIES", "5")))
    # Global Search: 每个社区返回结果数量
    global_search_per_community: int = field(default_factory=lambda: int(os.getenv("GRAPHRAG_GLOBAL_PER_COMMUNITY", "10")))
    
    # 混合检索策略选择
    # auto: 自动根据查询类型选择，local: 仅 Local Search，global: 仅 Global Search，hybrid: 混合模式
    hybrid_strategy: str = field(default_factory=lambda: os.getenv("GRAPHRAG_HYBRID_STRATEGY", "auto"))
    # Local Search 权重（混合模式下）
    hybrid_local_weight: float = field(default_factory=lambda: float(os.getenv("GRAPHRAG_HYBRID_LOCAL_WEIGHT", "0.6")))
    # Global Search 权重（混合模式下）
    hybrid_global_weight: float = field(default_factory=lambda: float(os.getenv("GRAPHRAG_HYBRID_GLOBAL_WEIGHT", "0.4")))
    
    # 置信度加权排序参数
    # 相关性分数权重
    weight_relevance: float = field(default_factory=lambda: float(os.getenv("GRAPHRAG_WEIGHT_RELEVANCE", "0.4")))
    # 置信度分数权重
    weight_confidence: float = field(default_factory=lambda: float(os.getenv("GRAPHRAG_WEIGHT_CONFIDENCE", "0.3")))
    # 新鲜度分数权重
    weight_freshness: float = field(default_factory=lambda: float(os.getenv("GRAPHRAG_WEIGHT_FRESHNESS", "0.15")))
    # 访问频率权重
    weight_access: float = field(default_factory=lambda: float(os.getenv("GRAPHRAG_WEIGHT_ACCESS", "0.15")))
    
    # 新鲜度衰减周期（秒），默认 7 天
    freshness_decay_seconds: float = field(default_factory=lambda: float(os.getenv("GRAPHRAG_FRESHNESS_DECAY", "604800.0")))
    
    # 自动检测查询类型的阈值
    # 查询包含实体数量低于此值时使用 Local Search
    auto_local_threshold: int = field(default_factory=lambda: int(os.getenv("GRAPHRAG_AUTO_LOCAL_THRESHOLD", "3")))
    # 查询关键词数量高于此值时使用 Global Search
    auto_global_threshold: int = field(default_factory=lambda: int(os.getenv("GRAPHRAG_AUTO_GLOBAL_THRESHOLD", "5")))


@dataclass
class AgentToolConfig:
    """Agent 工具注册配置"""
    # 是否启用工具注册
    enabled: bool = field(default_factory=lambda: os.getenv("AGENT_TOOLS_ENABLED", "true").lower() == "true")
    # 工具注册表路径（可选，用于自定义工具）
    registry_path: str = field(default_factory=lambda: os.getenv("AGENT_TOOLS_REGISTRY_PATH", ""))
    # 内置工具列表（逗号分隔）
    builtin_tools: str = field(default_factory=lambda: os.getenv("AGENT_BUILTIN_TOOLS", "retriever,reasoner,executor"))
    # 工具执行超时时间（秒）
    tool_timeout: float = field(default_factory=lambda: float(os.getenv("AGENT_TOOL_TIMEOUT", "30.0")))
    # 最大并行工具调用数
    max_parallel_calls: int = field(default_factory=lambda: int(os.getenv("AGENT_MAX_PARALLEL_CALLS", "5")))
    # 工具调用重试次数
    tool_retries: int = field(default_factory=lambda: int(os.getenv("AGENT_TOOL_RETRIES", "2")))
    
    def get_builtin_tools_list(self) -> List[str]:
        """获取内置工具列表"""
        if not self.builtin_tools:
            return []
        return [t.strip() for t in self.builtin_tools.split(",") if t.strip()]


@dataclass
class LLMFallbackConfig:
    """LLM Fallback 配置"""
    # 是否启用 Fallback 机制
    enabled: bool = field(default_factory=lambda: os.getenv("LLM_FALLBACK_ENABLED", "true").lower() == "true")
    # Fallback 模型列表（逗号分隔，按优先级排序）
    fallback_models: str = field(default_factory=lambda: os.getenv("LLM_FALLBACK_MODELS", "gpt-4,gpt-3.5-turbo"))
    # 主模型失败后等待时间（秒）再尝试 Fallback
    fallback_delay: float = field(default_factory=lambda: float(os.getenv("LLM_FALLBACK_DELAY", "1.0")))
    # 单个模型最大连续失败次数，超过后跳过该模型
    max_consecutive_failures: int = field(default_factory=lambda: int(os.getenv("LLM_FALLBACK_MAX_FAILURES", "3")))
    # 失败模型冷却时间（秒），冷却期内跳过该模型
    failure_cooldown_seconds: float = field(default_factory=lambda: float(os.getenv("LLM_FALLBACK_COOLDOWN", "300.0")))
    # 降级策略："strict" 严格模式（全部失败才报错），"lenient" 宽松模式（部分成功即返回）
    degradation_policy: str = field(default_factory=lambda: os.getenv("LLM_FALLBACK_DEGRADATION", "strict"))
    
    def get_fallback_models_list(self) -> List[str]:
        """获取 Fallback 模型列表"""
        if not self.fallback_models:
            return []
        return [m.strip() for m in self.fallback_models.split(",") if m.strip()]


@dataclass
class RetrieverConfig:
    """检索器配置"""
    rrf_k: int = field(default_factory=lambda: int(os.getenv("RETRIEVER_RRF_K", "60")))  # RRF 平滑常数
    context_max_tokens: int = field(default_factory=lambda: int(os.getenv("RETRIEVER_MAX_TOKENS", "2000")))  # 上下文最大 token 数
    # 默认检索 Top-K
    default_top_k: int = field(default_factory=lambda: int(os.getenv("RETRIEVER_DEFAULT_TOP_K", "20")))
    # 实体检索深度
    entity_depth: int = field(default_factory=lambda: int(os.getenv("RETRIEVER_ENTITY_DEPTH", "1")))
    # 模糊匹配阈值（0-1）
    fuzzy_match_threshold: float = field(default_factory=lambda: float(os.getenv("RETRIEVER_FUZZY_THRESHOLD", "0.8")))


@dataclass
class PerformanceConfig:
    """性能优化配置"""
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 缓存过期时间（秒）
    cache_max_size: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))  # 缓存最大条目数
    pool_min_size: int = int(os.getenv("POOL_MIN_SIZE", "2"))  # 连接池最小连接数
    pool_max_size: int = int(os.getenv("POOL_MAX_SIZE", "20"))  # 连接池最大连接数
    query_cache_ttl: int = int(os.getenv("QUERY_CACHE_TTL", "600"))  # 查询缓存过期时间
    batch_size: int = int(os.getenv("BATCH_SIZE", "10"))  # 批处理大小


@dataclass
class PermissionConfig:
    """
    权限系统配置
    
    配置角色层级、权限定义和访问控制策略。
    所有配置项均可通过环境变量覆盖，符合零硬编码原则。
    """
    # 角色层级定义：层级越高权限越大，格式为 "角色名:层级数值"
    # admin=100 > editor=50 > viewer=10
    role_hierarchy: str = field(default_factory=lambda: os.getenv(
        "PERMISSION_ROLE_HIERARCHY",
        "admin:100,editor:50,viewer:10,api_user:30,export_user:20"
    ))
    # 默认角色配置文件路径（JSON格式）
    # 如果未设置，使用代码内置的默认角色定义
    roles_config_path: str = field(default_factory=lambda: os.getenv("PERMISSION_ROLES_CONFIG", ""))
    # 权限检查失败时的默认行为："raise" 抛出异常，"log" 仅记录日志
    denial_action: str = field(default_factory=lambda: os.getenv("PERMISSION_DENIAL_ACTION", "raise"))
    # 审计日志保留天数
    audit_log_retention_days: int = field(default_factory=lambda: int(os.getenv("PERMISSION_AUDIT_RETENTION", "90")))
    # 是否启用权限缓存（提升性能）
    enable_permission_cache: bool = field(default_factory=lambda: os.getenv("PERMISSION_ENABLE_CACHE", "true").lower() == "true")
    # 权限缓存 TTL（秒）
    permission_cache_ttl: int = field(default_factory=lambda: int(os.getenv("PERMISSION_CACHE_TTL", "300")))
    # 超级管理员角色名（该角色拥有所有权限）
    super_admin_role: str = field(default_factory=lambda: os.getenv("PERMISSION_SUPER_ADMIN", "admin"))
    
    def get_role_hierarchy(self) -> Dict[str, int]:
        """
        解析角色层级配置为字典
        
        返回格式：{"admin": 100, "editor": 50, ...}
        """
        hierarchy = {}
        if self.role_hierarchy:
            for item in self.role_hierarchy.split(","):
                item = item.strip()
                if ":" in item:
                    role, level = item.split(":", 1)
                    hierarchy[role.strip()] = int(level.strip())
        return hierarchy


@dataclass
class AuditConfig:
    """
    审计系统配置
    
    配置审计日志的存储、查询和保留策略。
    """
    # 审计日志存储类型："sqlite" 或 "file"
    storage_type: str = field(default_factory=lambda: os.getenv("AUDIT_STORAGE_TYPE", "sqlite"))
    # SQLite 数据库路径
    sqlite_path: str = field(default_factory=lambda: os.getenv("AUDIT_SQLITE_PATH", "./data/audit.db"))
    # 文件日志路径（当 storage_type="file" 时使用）
    file_path: str = field(default_factory=lambda: os.getenv("AUDIT_FILE_PATH", "./data/audit.log"))
    # 日志保留天数
    retention_days: int = field(default_factory=lambda: int(os.getenv("AUDIT_RETENTION_DAYS", "90")))
    # 是否启用异步写入（提升性能，但可能丢失最近几秒的日志）
    async_write: bool = field(default_factory=lambda: os.getenv("AUDIT_ASYNC_WRITE", "true").lower() == "true")
    # 异步写入批量大小
    async_batch_size: int = field(default_factory=lambda: int(os.getenv("AUDIT_ASYNC_BATCH_SIZE", "100")))
    # 审计日志最大大小（MB）
    max_log_size_mb: int = field(default_factory=lambda: int(os.getenv("AUDIT_MAX_SIZE_MB", "500")))
    # SQLite 连接超时时间（秒）—— 避免硬编码，高并发场景下可适当增大
    sqlite_timeout: float = field(default_factory=lambda: float(os.getenv("AUDIT_SQLITE_TIMEOUT", "5.0")))


@dataclass
class SelfCorrectionConfig:
    """
    自我纠错模块配置
    
    控制冲突检测和反思回路的行为参数。
    反义词映射从外部 JSON 文件加载，符合零硬编码原则。
    """
    # 反义词映射文件路径 —— 当 Neo4j 不可用时使用本地 JSON 作为降级方案
    antonym_mapping_path: str = field(default_factory=lambda: os.getenv(
        "ANTONYM_MAPPING_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "antonym_defaults.json")
    ))
    # 冲突检测是否阻断写入 —— True: 发现冲突立即拒绝; False: 仅记录警告
    block_on_conflict: bool = field(default_factory=lambda: os.getenv("SELF_CORRECTION_BLOCK_ON_CONFLICT", "true").lower() == "true")
    # 反思回路最大迭代次数 —— 防止无限递归
    max_reflection_iterations: int = field(default_factory=lambda: int(os.getenv("SELF_CORRECTION_MAX_ITERATIONS", "3")))


@dataclass
class BehaviorLearnerConfig:
    """
    行为学习器配置
    
    控制从交互历史中学习行为模式的参数。
    """
    # 最小出现频率 —— 低于此频率的行为模式视为噪声，不会被注册
    min_frequency: int = field(default_factory=lambda: int(os.getenv("BEHAVIOR_MIN_FREQUENCY", "3")))
    # 最小成功率 —— 成功率低于此阈值的行为模式不会被推荐
    min_success_rate: float = field(default_factory=lambda: float(os.getenv("BEHAVIOR_MIN_SUCCESS_RATE", "0.5")))
    # 交互历史最大保留条数 —— 超过此数量时使用 FIFO 淘汰旧记录
    max_history_size: int = field(default_factory=lambda: int(os.getenv("BEHAVIOR_MAX_HISTORY_SIZE", "10000")))


@dataclass
class ObservabilityConfig:
    """
    可观测性配置
    
    配置结构化日志、指标采集和链路追踪。
    """
    # 是否启用结构化日志（JSON格式）
    structured_logging: bool = field(default_factory=lambda: os.getenv("OBS_STRUCTURED_LOGGING", "true").lower() == "true")
    # 日志输出格式："json" 或 "text"
    log_format: str = field(default_factory=lambda: os.getenv("OBS_LOG_FORMAT", "json"))
    # 是否启用推理链路追踪
    enable_inference_tracing: bool = field(default_factory=lambda: os.getenv("OBS_INFERENCE_TRACING", "true").lower() == "true")
    # 追踪数据保留时间（秒）
    trace_retention_seconds: int = field(default_factory=lambda: int(os.getenv("OBS_TRACE_RETENTION", "86400")))
    # 采样率（0.0-1.0，用于降低追踪数据量）
    trace_sample_rate: float = field(default_factory=lambda: float(os.getenv("OBS_TRACE_SAMPLE_RATE", "1.0")))
    # 是否记录敏感数据
    log_sensitive_data: bool = field(default_factory=lambda: os.getenv("OBS_LOG_SENSITIVE", "false").lower() == "true")
    # 慢查询阈值（秒）
    slow_query_threshold: float = field(default_factory=lambda: float(os.getenv("OBS_SLOW_QUERY_THRESHOLD", "1.0")))
    # 慢推理阈值（秒）
    slow_inference_threshold: float = field(default_factory=lambda: float(os.getenv("OBS_SLOW_INFERENCE_THRESHOLD", "5.0")))


@dataclass
class AppConfig:
    """应用配置"""
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    data_dir: str = field(default_factory=lambda: os.getenv("DATA_DIR", "./data"))
    max_learning_episodes: int = 10000
    auto_save_interval: int = 300  # 秒


class ConfigManager:
    """
    配置管理器（单例模式）
    
    配置加载优先级：
    1. 环境变量（最高优先级）- 直接通过 os.getenv 获取
    2. .env 文件 - 通过 python-dotenv 加载到环境变量
    3. 代码默认值（最低优先级）- dataclass 默认值
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 基础配置
        self.llm = LLMConfig()
        self.database = DatabaseConfig()
        self.app = AppConfig()
        
        # 功能模块配置
        self.reasoning = ReasoningConfig()
        self.memory = MemoryConfig()
        self.evolution = EvolutionConfig()
        self.performance = PerformanceConfig()
        self.action_runtime = ActionRuntimeConfig()
        self.retriever = RetrieverConfig()
        
        # 新增配置模块
        self.graphrag = GraphRAGConfig()  # GraphRAG 检索增强配置
        self.agent_tools = AgentToolConfig()  # Agent 工具注册配置
        self.llm_fallback = LLMFallbackConfig()  # LLM Fallback 配置
        self.tool = ToolConfig()  # 工具系统配置
        
        # 企业级安全治理与可观测性配置
        self.permission = PermissionConfig()  # 权限系统配置
        self.audit = AuditConfig()  # 审计系统配置
        self.observability = ObservabilityConfig()  # 可观测性配置
        
        # 演化层增强配置
        self.self_correction = SelfCorrectionConfig()  # 自我纠错配置
        self.behavior_learner = BehaviorLearnerConfig()  # 行为学习器配置
        
        self._initialized = True
        logger.debug("ConfigManager 初始化完成")
    
    def validate(self) -> Dict[str, Any]:
        """
        验证配置
        
        检查必要配置是否存在，以及配置值是否合法
        
        Returns:
            验证结果，包含是否有效、错误信息和警告
        """
        errors = []
        warnings = []
        
        # 验证 LLM 配置
        if not self.llm.is_configured():
            errors.append("LLM API Key 未配置 (OPENAI_API_KEY)")
        
        
        # 验证数据库配置
        if not self.database.is_configured():
            warnings.append("数据库配置不完整，部分功能可能受限")
        
        
        # 验证日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.app.log_level.upper() not in valid_levels:
            warnings.append(f"未知的日志级别: {self.app.log_level}")
        
        
        # 验证 GraphRAG 配置
        valid_algorithms = ["louvain", "girvan_newman", "label_propagation"]
        if self.graphrag.community_algorithm not in valid_algorithms:
            warnings.append(f"GraphRAG 社区检测算法 '{self.graphrag.community_algorithm}' 可能不被支持，建议使用: {valid_algorithms}")
        
        # 验证 GraphRAG 权重配置（增强验证）
        weight_sum = (
            self.graphrag.weight_relevance +
            self.graphrag.weight_confidence +
            self.graphrag.weight_freshness +
            self.graphrag.weight_access
        )
        
        # 验证权重和是否接近 1.0（允许 0.01 的浮点误差）
        if abs(weight_sum - 1.0) > 0.01:
            errors.append(f"GraphRAG 排序权重之和必须等于 1.0，当前为: {weight_sum:.4f}，请调整权重配置")
        
        # 验证各权重是否在合理范围 [0, 1]
        weight_fields = [
            ("weight_relevance", self.graphrag.weight_relevance),
            ("weight_confidence", self.graphrag.weight_confidence),
            ("weight_freshness", self.graphrag.weight_freshness),
            ("weight_access", self.graphrag.weight_access),
        ]
        for field_name, weight in weight_fields:
            if weight < 0.0 or weight > 1.0:
                errors.append(f"GraphRAG {field_name} 权重必须在 [0, 1] 范围内，当前为: {weight}")
        
        # 验证混合检索权重（如果启用混合模式）
        if self.graphrag.hybrid_strategy == "hybrid":
            hybrid_sum = self.graphrag.hybrid_local_weight + self.graphrag.hybrid_global_weight
            if abs(hybrid_sum - 1.0) > 0.01:
                warnings.append(f"GraphRAG 混合检索权重之和应为 1.0，当前为: {hybrid_sum:.4f}")
        
        # 验证混合检索策略
        valid_strategies = ["auto", "local", "global", "hybrid"]
        if self.graphrag.hybrid_strategy not in valid_strategies:
            warnings.append(f"GraphRAG 混合策略 '{self.graphrag.hybrid_strategy}' 无效，建议使用: {valid_strategies}")
        
        # 验证 LLM Fallback 降级策略
        valid_policies = ["strict", "lenient"]
        if self.llm_fallback.degradation_policy not in valid_policies:
            warnings.append(f"LLM Fallback 降级策略 '{self.llm_fallback.degradation_policy}' 无效，建议使用: {valid_policies}")
        
        # 验证 LLM Fallback 计数逻辑配置
        if self.llm_fallback.max_consecutive_failures < 1:
            errors.append(f"LLM Fallback 最大连续失败次数必须 >= 1，当前为: {self.llm_fallback.max_consecutive_failures}")
        
        if self.llm_fallback.failure_cooldown_seconds < 0:
            errors.append(f"LLM Fallback 失败冷却时间必须 >= 0，当前为: {self.llm_fallback.failure_cooldown_seconds}")
        
        # 验证 Fallback 模型列表非空（如果启用 fallback）
        if self.llm_fallback.enabled and not self.llm_fallback.get_fallback_models_list():
            warnings.append("LLM Fallback 已启用但未配置任何 fallback 模型")
        
        # 验证 Agent 工具配置
        if self.agent_tools.enabled and not self.agent_tools.get_builtin_tools_list():
            warnings.append("Agent 工具已启用但未配置任何内置工具")
        
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典（隐藏敏感信息）"""
        return {
            "llm": {
                "base_url": self.llm.base_url,
                "model": self.llm.model,
                "configured": self.llm.is_configured()
            },
            "database": {
                "neo4j_uri": self.database.neo4j_uri,
                "configured": self.database.is_configured()
            },
            "app": asdict(self.app),
            "graphrag": {
                "community_algorithm": self.graphrag.community_algorithm,
                "hybrid_strategy": self.graphrag.hybrid_strategy
            },
            "agent_tools": {
                "enabled": self.agent_tools.enabled,
                "builtin_tools": self.agent_tools.get_builtin_tools_list()
            },
            "llm_fallback": {
                "enabled": self.llm_fallback.enabled,
                "fallback_models": self.llm_fallback.get_fallback_models_list()
            },
            "tool": {
                "ingest_name": self.tool.tool_ingest_name,
                "query_name": self.tool.tool_query_name,
                "action_name": self.tool.tool_action_name,
                "evaluate_name": self.tool.tool_evaluate_name,
                "feedback_name": self.tool.tool_feedback_name
            }
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证当前配置（别名方法，便于外部调用）
        
        Returns:
            验证结果字典，包含 valid、errors、warnings 字段
        """
        return self.validate()
    
    def save_to_file(self, filepath: str):
        """保存配置到文件（不包含敏感信息）"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "ConfigManager":
        """从文件加载配置"""
        config = cls()
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 这里可以添加从文件加载的逻辑
        
        return config


# 全局配置实例
config = ConfigManager()


def get_config() -> ConfigManager:
    """获取配置管理器实例"""
    return config


def validate_config() -> Dict[str, Any]:
    """验证当前配置"""
    return config.validate()
