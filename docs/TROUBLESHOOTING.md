# Clawra 故障排查指南

> 常见问题及解决方案。

---

## 1. 安装问题

### 1.1 pip 安装失败

**症状**: `pip install clawra` 报错

**解决方案**:

```bash
# 使用国内镜像
pip install clawra -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或先升级 pip
pip install --upgrade pip
pip install clawra
```

### 1.2 依赖版本冲突

**症状**: ImportError 或版本不兼容

**解决方案**:

```bash
# 创建独立虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

---

## 2. 启动问题

### 2.1 Neo4j 连接失败

**症状**: `ConnectionError: Unable to connect to Neo4j`

**排查步骤**:

1. 检查 Neo4j 是否运行：

```bash
# macOS
brew services list | grep neo4j

# 或手动检查
curl http://localhost:7474
```

2. 检查连接参数（.env）：

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

3. 如未设置密码，先设置：

```bash
# 启动 Neo4j Browser（http://localhost:7474）
# 首次登录用 neo4j/neo4j，系统会要求设置新密码
```

4. 确认 Aura 实例（云端）：

```bash
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=aursxxxxxxxxx
```

### 2.2 ChromaDB 连接问题

**症状**: `ImportError: Cannot find ChromaDB` 或启动报错

**解决方案**:

```bash
pip install chromadb
```

如遇持久化问题：

```python
import chromadb

# 使用持久化存储
client = chromadb.PersistentClient(path="./data/chromadb")

# 或使用临时内存
client = chromadb.EphemeralClient()
```

### 2.3 LLM API 调用失败

**症状**: `APITimeoutError` 或 `APIError`

**排查**:

1. 检查 API Key 配置：

```bash
# .env 文件
OPENAI_API_KEY=sk-xxxx
# 或
ANTHROPIC_API_KEY=sk-ant-xxxx
# 或
MINIMAX_API_KEY=xxxxxxxx
```

2. 检查网络代理（如需）：

```bash
# 设置代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

3. 检查模型名称是否正确：

```python
agent = Clawra(llm_model="gpt-4")  # 正确
agent = Clawra(llm_model="gpt-5")  # 错误！不存在
```

4. 检查 API 额度：

```bash
# OpenAI
https://platform.openai.com/usage

# MiniMax
https://www.minimax.chat/center
```

### 2.4 MiniMax 403/401 错误

**症状**: MiniMax API 返回 403 或 401

**常见原因**:

1. **API Key 填错位置**：确保 `.env` 中 `MINIMAX_API_KEY` 填在 MiniMax 的密钥位置，不是 OpenAI 位置

2. **端点地址错误**：

```bash
# 中国区正确端点
MINIMAX_BASE_URL=https://api.minimax.chat/v1

# 错误的常用地址（已被拦截）
# https://api.tiktok.com/xxx  ❌
# https://ark.cn-beijing.volces.com/  ❌
```

3. **模型名称错误**：

```python
# MiniMax 中国区可用模型
MiniMax-Text-01     # 文本模型
MiniMax-V01         # 视觉模型
abab6.5s-chat       # 对话模型
```

---

## 3. 运行时问题

### 3.1 学习（learn）无响应或超时

**症状**: `agent.learn()` 调用后长时间无返回

**原因**: LLM 调用阻塞或超时

**解决方案**:

1. 检查 LLM 可用性：

```python
from src.llm.client import LLMClient

client = LLMClient()
response = client.chat("你好")
print(response)
```

2. 启用异步模式：

```python
import asyncio

async def learn_async():
    agent = await Clawra.create()
    result = await agent.learn_async("文本")
    return result

result = asyncio.run(learn_async())
```

3. 设置超时：

```python
agent = Clawra(
    timeout=30,  # 30 秒超时
    enable_retry=True,
    max_retries=3
)
```

### 3.2 推理结果为空

**症状**: `agent.reason()` 返回空列表

**排查**:

1. 确认知识图谱有数据：

```python
facts = agent.query()
print(f"事实数量: {len(facts)}")

if len(facts) == 0:
    print("知识图谱为空，请先添加事实或学习")
    agent.learn("燃气调压箱出口压力不得超0.4MPa")
```

2. 检查事实格式：

```python
# 错误格式
agent.add_fact("调压箱A", "is a", "燃气调压箱")  # ❌ 空格

# 正确格式
agent.add_fact("调压箱A", "is_a", "燃气调压箱")  # ✅ 下划线
```

3. 调整置信度阈值：

```python
# 查询低置信度事实
facts = agent.query(min_confidence=0.1)
```

### 3.3 Meta-Learner 报错

**症状**: `MetaLearnerError` 或 `LearningLoopError`

**解决方案**:

1. 检查 LLM 配置：

```python
from src.evolution.meta_learner import MetaLearner

ml = MetaLearner(llm_config={"provider": "openai", "model": "gpt-4"})
```

2. 禁用 Meta-Learner（调试用）：

```python
agent = Clawra(
    enable_meta_learner=False  # 跳过 Meta-Learner
)
```

3. 查看详细日志：

```python
import logging

logging.basicConfig(level=logging.DEBUG)
agent = Clawra()
agent.learn("文本")  # 查看 DEBUG 日志
```

### 3.4 GraphRAG 检索质量差

**症状**: `retrieve_knowledge()` 返回不相关内容

**解决方案**:

1. 调整检索模式：

```python
# 智能模式（组合多种检索）
result = agent.retrieve_knowledge(
    query="查询内容",
    top_k=5,
    modes=["smart"]
)

# 指定单一模式
result = agent.retrieve_knowledge(
    query="查询内容",
    top_k=5,
    modes=["entity"]  # 只用实体检索
)
```

2. 调整 `top_k`：

```python
result = agent.retrieve_knowledge(
    query="查询内容",
    top_k=10  # 增加返回数量
)
```

3. 检查向量数据库连接：

```python
# 验证 ChromaDB
import chromadb
client = chromadb.PersistentClient(path="./data/chromadb")
print(client.list_collections())
```

---

## 4. 测试问题

### 4.1 pytest 超时

**症状**: 测试运行 120 秒后超时

**原因**: LLM 调用阻塞，测试未 mock

**解决方案**:

1. 使用 mock：

```python
from unittest.mock import patch

@patch('src.evolution.meta_learner.MetaLearner._call_llm')
def test_learn(mock_llm):
    mock_llm.return_value = {"pattern": "测试规则"}
    result = agent.learn("测试文本")
    assert result['success']
```

2. 设置短超时：

```python
# conftest.py
import pytest

@pytest.fixture
def quick_agent():
    return Clawra(timeout=5)  # 5 秒超时
```

3. 跳过慢速测试：

```bash
pytest -m "not slow"
```

### 4.2 Neo4j 测试连接错误

**症状**: `ServiceUnavailable` 或 `ConnectionRequired`

**解决方案**:

1. 使用测试容器：

```bash
docker run -d \
    --name neo4j-test \
    -p 7477:7474 -p 7688:7687 \
    -e NEO4J_AUTH=neo4j/test \
    neo4j:5
```

2. 或使用 mock：

```python
from unittest.mock import MagicMock

@pytest.fixture
def mock_neo4j():
    mock_driver = MagicMock()
    return mock_driver
```

---

## 5. 性能问题

### 5.1 内存占用高

**症状**: 内存持续增长

**解决方案**:

1. 限制缓存大小：

```python
agent = Clawra(
    cache_size=1000,      # 限制缓存
    enable_cache=True
)
```

2. 定期清理：

```python
agent.clear_cache()      # 清理缓存
agent.gc_collect()       # 触发垃圾回收
```

3. 使用流式处理：

```python
# 大批量数据用生成器
def learn_batch(texts):
    for text in texts:
        yield agent.learn(text)
```

### 5.2 推理速度慢

**症状**: `reason()` 执行很慢

**解决方案**:

1. 限制推理深度：

```python
conclusions = agent.reason(max_depth=3)  # 减少深度
```

2. 使用索引：

```python
# 确保知识图谱有索引
agent.create_indexes()
```

3. 减少事实数量：

```python
# 分批处理
batch1 = agent.query(domain="gas_equipment")
batch2 = agent.query(domain="safety")
```

---

## 6. 环境问题

### 6.1 .env 文件不生效

**症状**: 配置的变量没有生效

**排查**:

1. 确认文件位置：

```bash
# 项目根目录
ls -la .env

# 或确认文件内容
cat .env
```

2. 检查变量名：

```bash
# 错误名称
NEO4J_URL=bolt://localhost:7687     # ❌ 不是 URL

# 正确名称（根据代码）
NEO4J_URI=bolt://localhost:7687     # ✅ URI
```

3. 重启应用：

```bash
# 修改 .env 后必须重启
pkill -f "python.*clawra"
python main.py
```

### 6.2 工作目录问题

**症状**: 找不到 config 或 .env

**解决方案**:

```bash
# 确认工作目录
pwd

# 或指定配置路径
agent = Clawra(config_path="/path/to/config.yaml")
```

---

## 7. 错误代码速查

| 错误代码 | 含义 | 快速解决 |
|---------|------|---------|
| `E1001` | Neo4j 连接失败 | 检查 Neo4j 是否运行、密码是否正确 |
| `E1002` | ChromaDB 初始化失败 | 重建数据目录 `rm -rf ./data/chromadb` |
| `E2001` | LLM API 超时 | 检查网络、代理设置、增加 timeout |
| `E2002` | LLM API 认证失败 | 检查 API Key 是否正确、是否有额度 |
| `E3001` | 学习失败 | 检查输入文本是否为空、LLM 是否可用 |
| `E3002` | 推理失败 | 确认知识图谱有数据、增加 max_depth |
| `E4001` | 元学习器错误 | 禁用 meta_learner 逐阶段排查 |
| `E5001` | 配置文件错误 | 检查 config.yaml 格式、必填字段 |

---

## 8. 获取帮助

### 8.1 诊断信息收集

```python
# 打印完整诊断信息
from src.utils.diagnostics import print_diagnostics

print_diagnostics()
```

### 8.2 日志分析

```bash
# 查看最近日志
tail -n 100 logs/clawra.log

# 搜索错误
grep -i "error" logs/clawra.log

# 实时监控
tail -f logs/clawra.log
```

### 8.3 GitHub Issues

如遇到无法解决的问题，请提交 Issue 并附上：
- 完整的错误堆栈
- 复现步骤
- 环境信息（OS、Python 版本、依赖版本）

---

**最后更新**: 2026-04-13
