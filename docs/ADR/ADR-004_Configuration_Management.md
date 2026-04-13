# ADR-004: Configuration Management

> 状态: **已通过** | 日期: 2026-04-12

---

## 背景

Clawra 需要支持多种环境（开发、测试、生产）和多种部署方式（本地、Docker、K8s），配置管理需要：
- **零硬编码**：所有魔法值必须外置
- **分层配置**：环境变量 > 命令行 > 配置文件
- **环境隔离**：不同环境配置分离
- **运行时更新**：无需重启即可更新部分配置

---

## 决策

### 配置分层

```
优先级（高 → 低）：
┌─────────────────────────────────────────┐
│ 1. 环境变量 (ENV)     ← 最高优先级       │
│ 2. 命令行参数 (ARG)                      │
│ 3. config.yaml      ← 项目级配置        │
│ 4. .env             ← 本地开发配置      │
│ 5. defaults.yaml    ← 系统默认          │
└─────────────────────────────────────────┘
```

### 配置文件结构

```yaml
# config.yaml
app:
  name: "Clawra"
  version: "3.5.0"
  debug: false
  log_level: "${LOG_LEVEL:-INFO}"

server:
  host: "${HOST:-0.0.0.0}"
  port: "${PORT:-8000}"
  workers: "${WORKERS:-4}"
  timeout: "${TIMEOUT:-30}"

llm:
  provider: "${LLM_PROVIDER:-openai}"
  model: "${LLM_MODEL:-gpt-4}"
  temperature: 0.7
  max_retries: 3
  timeout: 30
  # Provider 特定配置
  openai:
    api_key: "${OPENAI_API_KEY}"
    base_url: "${OPENAI_BASE_URL:-https://api.openai.com/v1}"
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    base_url: "${ANTHROPIC_BASE_URL:-https://api.anthropic.com}"
  ollama:
    base_url: "${OLLAMA_BASE_URL:-http://localhost:11434}"
    model: "${OLLAMA_MODEL:-llama3}"
  minimax:
    api_key: "${MINIMAX_API_KEY}"
    group_id: "${MINIMAX_GROUP_ID}"
    base_url: "${MINIMAX_BASE_URL:-https://api.minimax.chat/v1}"

neo4j:
  uri: "${NEO4J_URI:-bolt://localhost:7687}"
  user: "${NEO4J_USER:-neo4j}"
  password: "${NEO4J_PASSWORD}"
  database: "${NEO4J_DATABASE:-neo4j}"
  max_connection_lifetime: 3600
  max_connection_pool_size: 50

chromadb:
  host: "${CHROMADB_HOST:-localhost}"
  port: "${CHROMADB_PORT:-8000}"
  collection_name: "clawra_entities"
  persist_directory: "${CHROMADB_PERSIST_DIR:-./data/chromadb}"

redis:
  host: "${REDIS_HOST:-localhost}"
  port: "${REDIS_PORT:-6379}"
  db: 0
  password: "${REDIS_PASSWORD}"
  pool_size: 10

memory:
  enable: "${ENABLE_MEMORY:-true}"
  cache_size: "${CACHE_SIZE:-1000}"
  history_window: 10
  ttl: 3600

evolution:
  enable_meta_learner: "${ENABLE_META_LEARNER:-true}"
  enable_rule_discovery: "${ENABLE_RULE_DISCOVERY:-true}"
  enable_self_evaluation: "${ENABLE_SELF_EVALUATION:-true}"
  max_iterations: 100
  convergence_threshold: 0.01

features:
  enable_graphrag: "${ENABLE_GRAPHRAG:-true}"
  enable_skill_distiller: "${ENABLE_SKILL_DISTILLER:-true}"
  enable_pattern_versioning: "${ENABLE_PATTERN_VERSIONING:-true}"
```

### .env 示例

```bash
# .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password

LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=https://api.openai.com/v1

LOG_LEVEL=DEBUG
DEBUG=true

ENABLE_MEMORY=true
ENABLE_GRAPHRAG=true
ENABLE_META_LEARNER=true
ENABLE_PATTERN_VERSIONING=true
```

### 配置加载器

```python
# src/config/loader.py
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config()
        self._config: Dict[str, Any] = {}
        self._load()

    def _find_config(self) -> str:
        """查找配置文件"""
        search_paths = [
            Path.cwd() / "config.yaml",
            Path.cwd() / "config" / "default.yaml",
            Path(__file__).parent.parent.parent / "config.yaml",
        ]
        for path in search_paths:
            if path.exists():
                return str(path)
        return str(search_paths[0])  # 返回默认路径

    def _load(self):
        """加载配置"""
        # 1. 加载 defaults.yaml
        defaults = self._load_yaml("defaults.yaml")

        # 2. 加载 config.yaml
        if Path(self.config_path).exists():
            config = self._load_yaml(self.config_path)
            self._config = self._merge(defaults, config)
        else:
            self._config = defaults

        # 3. 环境变量覆盖
        self._override_from_env()

    def _override_from_env(self):
        """从环境变量覆盖"""
        for key, value in os.environ.items():
            if key.isupper() and key.startswith(("NEO4J_", "LLM_", "REDIS_", "APP_")):
                self._set_nested(key.lower(), value)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def _set_nested(self, key: str, value: Any):
        """设置嵌套配置"""
        keys = key.split("_")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
```

### 配置验证

```python
# src/config/validator.py
from pydantic import BaseModel, validator
from typing import Optional

class LLMConfig(BaseModel):
    provider: str
    model: str
    timeout: int = 30
    max_retries: int = 3

    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['openai', 'anthropic', 'ollama', 'minimax']
        if v not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v

class Neo4jConfig(BaseModel):
    uri: str
    user: str
    password: str
    max_connection_pool_size: int = 50

class Config(BaseModel):
    llm: LLMConfig
    neo4j: Neo4jConfig
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    class Config:
        extra = 'allow'  # 允许额外字段
```

---

## 后果

### 正面

- ✅ **零硬编码**：所有配置外置
- ✅ **环境隔离**：dev/staging/prod 完全分离
- ✅ **运行时更新**：部分配置可热更新
- ✅ **配置验证**：启动时检查必填项
- ✅ **文档完整**：每个配置项有说明

### 负面

- ❌ 配置项较多，学习成本稍高
- ❌ 需要维护多个配置文件

### 风险

- ⚠️ 敏感信息（API Key）需要通过环境变量传入，不要提交到 Git

---

## 实现清单

- [x] `src/config/loader.py` - 配置加载器
- [x] `src/config/validator.py` - 配置验证
- [x] `src/config/defaults.yaml` - 默认配置
- [x] `.env.example` - 环境变量示例
- [x] `config.yaml` - 项目默认配置

---

## 相关 ADR

- [ADR-001](./ADR-001_LLM_Provider_Abstraction.md) - LLM Provider 配置方式
- [ADR-003](./ADR-003_Evolution_Loop_Architecture.md) - Evolution Loop 参数配置
