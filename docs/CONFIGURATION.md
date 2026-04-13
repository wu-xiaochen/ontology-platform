# Clawra 配置参考文档

> 详细说明 Clawra 的所有配置项、默认值、配置方式。

---

## 1. 配置架构

### 1.1 配置来源优先级

Clawra 的配置来自多个来源，优先级从高到低：

```
1. 环境变量 (.env)
2. 配置文件 (config.yaml)
3. 代码默认值
```

### 1.2 配置管理方式

```python
from src.utils.config import get_config

config = get_config()

# 读取配置
value = config.evolution.min_support

# 运行时修改（仅影响当前进程）
config.evolution.min_support = 3
```

---

## 2. 环境变量配置

### 2.1 必需的环境变量

```bash
# .env 文件

# LLM 配置
MINIMAX_API_KEY=your_api_key_here          # MiniMax API Key
OPENAI_API_KEY=your_openai_key_here        # OpenAI API Key (可选)

# Neo4j 配置 (可选，用于完整功能)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# ChromaDB 配置 (可选)
CHROMA_DB_PATH=./data/chroma_db

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8501
LOG_LEVEL=INFO
```

### 2.2 可选的环境变量

```bash
# 性能配置
MAX_WORKERS=4
REQUEST_TIMEOUT=30
CACHE_SIZE=1000

# 安全配置
API_KEY_REQUIRED=true
RATE_LIMIT_PER_MINUTE=60

# 调试配置
DEBUG=false
SKIP_LLM=false
```

---

## 3. config.yaml 配置

### 3.1 完整配置示例

```yaml
# config.yaml
app:
  name: "Clawra"
  version: "4.0.0"
  environment: "development"  # development / production
  debug: false

server:
  host: "0.0.0.0"
  port: 8501
  reload: true

llm:
  provider: "minimax"  # minimax / openai / local
  skip_llm: false
  model: "MiniMax-M2.7"
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
  retry:
    max_attempts: 3
    backoff_factor: 2

database:
  knowledge_graph:
    provider: "sqlite"  # sqlite / neo4j
    path: "./data/knowledge_graph.db"
    # neo4j 配置 (当 provider=neo4j 时)
    neo4j:
      uri: "bolt://localhost:7687"
      user: "neo4j"
      password: ""
      database: "neo4j"
  
  episodic_memory:
    provider: "sqlite"
    path: "./data/episodic_memory.db"
  
  vector_store:
    provider: "chroma"  # chroma / qdrant
    path: "./data/chroma_db"
    collection_name: "clawra_vectors"
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

reasoning:
  max_depth: 10
  timeout_seconds: 5
  enable_forward_chain: true
  enable_backward_chain: true
  confidence_threshold: 0.5
  enable_conflict_check: true
  max_inference_steps: 1000

memory:
  episodic:
    max_episodes: 10000
    retention_days: 90
    enable_compression: true
  semantic:
    enable_cache: true
    cache_ttl: 3600
    max_neighbors: 50

evolution:
  min_support: 2              # 最小支持度 (规则发现)
  min_confidence: 0.6         # 最小置信度
  confidence_high: 0.8        # 高置信度阈值
  confidence_medium: 0.6      # 中置信度阈值
  confidence_low: 0.4         # 低置信度阈值
  promote_threshold: 0.7      # 规则提升阈值
  max_learning_episodes: 1000 # 最大学习记录数
  
self_correction:
  block_on_conflict: true     # 冲突时是否阻断
  antonym_mapping_path: "./src/data/antonyms.json"
  
self_evaluator:
  enable_periodic: true
  evaluation_interval_hours: 24
  quality_threshold: 0.7
  accuracy_threshold: 0.9

performance:
  enable_cache: true
  cache_size: 1000
  enable_connection_pool: true
  connection_pool_size: 10
  enable_async: true
  max_workers: 4

security:
  enable_api_key: false
  api_key: ""
  enable_rate_limit: true
  rate_limit_per_minute: 60
  enable_cors: true
  cors_origins:
    - "http://localhost:8501"
    - "http://localhost:3000"

logging:
  level: "INFO"  # DEBUG / INFO / WARNING / ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./logs/clawra.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

---

## 4. 各模块配置详解

### 4.1 LLM 配置

```python
# 配置结构
class LLMConfig:
    provider: str          # "minimax" / "openai" / "local"
    skip_llm: bool        # 是否跳过 LLM（用于测试）
    model: str            # 模型名称
    temperature: float    # 生成温度 [0.0, 1.0]
    max_tokens: int       # 最大生成 token 数
    timeout: int          # 请求超时（秒）
    retry: Dict           # 重试配置
```

### 4.2 推理配置

```python
# 配置结构
class ReasoningConfig:
    max_depth: int           # 最大推理深度
    timeout_seconds: float    # 推理超时（秒）
    enable_forward_chain: bool   # 启用前向链
    enable_backward_chain: bool  # 启用后向链
    confidence_threshold: float # 置信度阈值
    enable_conflict_check: bool  # 启用冲突检测
    max_inference_steps: int     # 最大推理步数
```

### 4.3 Evolution 配置

```python
# 配置结构
class EvolutionConfig:
    min_support: int          # 最小支持度
    min_confidence: float     # 最小置信度
    confidence_high: float    # 高置信度阈值
    confidence_medium: float  # 中置信度阈值
    confidence_low: float     # 低置信度阈值
    promote_threshold: float   # 规则提升阈值
    max_learning_episodes: int # 最大学习记录数
```

### 4.4 Self-Correction 配置

```python
# 配置结构
class SelfCorrectionConfig:
    block_on_conflict: bool   # 冲突时是否阻断（True=阻断写入，False=仅警告）
    antonym_mapping_path: str # 反义词映射文件路径
```

### 4.5 安全配置

```python
# 配置结构
class SecurityConfig:
    enable_api_key: bool     # 是否启用 API Key
    api_key: str            # API Key（生产环境应使用环境变量）
    enable_rate_limit: bool  # 是否启用限流
    rate_limit_per_minute: int # 每分钟请求数限制
    enable_cors: bool       # 是否启用 CORS
    cors_origins: List[str] # 允许的来源
```

---

## 5. 配置验证

### 5.1 配置验证规则

```python
# 配置验证在启动时自动执行
VALIDATION_RULES = {
    "llm.temperature": {"min": 0.0, "max": 2.0},
    "reasoning.max_depth": {"min": 1, "max": 100},
    "evolution.min_confidence": {"min": 0.0, "max": 1.0},
    "security.rate_limit_per_minute": {"min": 1, "max": 10000},
}
```

### 5.2 验证失败处理

```python
# 验证失败时的行为
# 1. 如果是必需配置项 → 抛出异常，阻止启动
# 2. 如果是可选配置项 → 使用默认值，记录警告

# 示例
try:
    config.validate()
except ConfigValidationError as e:
    print(f"配置验证失败: {e}")
    sys.exit(1)
```

---

## 6. 生产环境配置

### 6.1 生产环境推荐配置

```yaml
# config.prod.yaml
app:
  environment: "production"
  debug: false

llm:
  timeout: 60
  retry:
    max_attempts: 5
    backoff_factor: 3

database:
  knowledge_graph:
    provider: "neo4j"  # 生产环境推荐使用 Neo4j
    neo4j:
      uri: "${NEO4J_URI}"
      user: "${NEO4J_USER}"
      password: "${NEO4J_PASSWORD}"

performance:
  enable_cache: true
  cache_size: 10000
  enable_connection_pool: true
  connection_pool_size: 50

security:
  enable_api_key: true
  enable_rate_limit: true
  rate_limit_per_minute: 100

logging:
  level: "WARNING"
```

### 6.2 敏感信息管理

```bash
# 生产环境使用环境变量或密钥管理服务
# 不要将敏感信息硬编码在配置文件中

# 示例: 使用环境变量
NEO4J_PASSWORD=${SECRET_MANAGER_PASSWORD}

# 示例: 使用 Kubernetes Secret
# 通过 volume mount 注入
```

---

## 7. 配置调试

### 7.1 查看当前配置

```python
from src.utils.config import get_config

config = get_config()

# 打印所有配置
print(config.to_dict())

# 打印特定模块配置
print(config.evolution.to_dict())
```

### 7.2 配置热重载

```python
# 在开发环境中，支持配置热重载
config.reload()

# 验证新配置
config.validate()
```

---

**最后更新**: 2026-04-13
