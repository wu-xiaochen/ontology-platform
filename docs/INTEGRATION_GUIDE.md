# Clawra 集成指南

> 如何将 Clawra 与 LangChain、LlamaIndex、外部系统集成。

---

## 1. LangChain 集成

### 1.1 安装依赖

```bash
pip install langchain langchain-community
```

### 1.2 作为 Tool 使用

```python
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from langchain.tools import Tool

from src.clawra import Clawra

# 初始化 Clawra
agent = Clawra(enable_memory=False)

# 定义工具
clawra_tool = Tool(
    name="OntologyReasoner",
    func=agent.reason,
    description="用于知识图谱推理。根据输入执行前向链推理，返回推理结论。"
)

clawra_learn_tool = Tool(
    name="KnowledgeLearner",
    func=agent.learn,
    description="用于学习新知识。输入文本，提取实体、关系和规则，加入知识图谱。"
)

# 创建 Agent
llm = OpenAI(temperature=0)
tools = [clawra_tool, clawra_learn_tool]

chain = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# 使用
result = chain.run(
    "学习：燃气调压箱出口压力不得超0.4MPa。然后检查调压箱A（出口压力0.5MPa）是否安全。"
)
```

### 1.3 作为 Memory 记忆层

```python
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType

from src.clawra import Clawra
from src.clawra.memory import ClawraMemory

# Clawra 记忆层
clawra_memory = ClawraMemory(
    agent=Clawra(enable_memory=True)
)

# LangChain 对话记忆
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# 合并记忆
chat_history = clawra_memory.load_memory_variables({})
memory.chat_memory.add_user_message(chat_history["history"])
```

---

## 2. LlamaIndex 集成

### 2.1 安装依赖

```bash
pip install llama-index
```

### 2.2 作为 Query Engine

```python
import llama_index

from src.clawra import Clawra
from src.clawra.retrieval import ClawraGraphVectorIndex

# 初始化
clawra = Clawra(enable_memory=False)

# 获取 Clawra 的检索接口
retriever = clawra.retriever  # ClawraGraphVectorIndex

# 转为 LlamaIndex 查询引擎
query_engine = retriever.as_query_engine()

# 使用
response = query_engine.query("燃气调压箱的安全规范是什么？")
print(response)
```

### 2.3 Clawra + LlamaIndex 混合检索

```python
from llama_index import VectorStoreIndex, KnowledgeGraphIndex
from llama_index.storage import StorageContext

from src.clawra import Clawra

clawra = Clawra(enable_memory=True)

# 知识图谱索引
kg_index = KnowledgeGraphIndex(
    kg_logger=clawra.kg_logger,
    storage_context=StorageContext.from_defaults()
)

# 向量索引
vector_index = VectorStoreIndex.from_documents(documents)

# 合并
from llama_index.query_engine import RetrieverQueryEngine

combined_engine = RetrieverQueryEngine.from_args(
    [kg_index.as_retriever(), vector_index.as_retriever()],
    node_postprocessors=[...]
)
```

---

## 3. 外部知识图谱导入/导出

### 3.1 从 Neo4j 导入

```python
from neo4j import GraphDatabase

from src.clawra import Clawra

# Neo4j 连接
neo4j_driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

clawra = Clawra(enable_memory=True)

# 导出 Neo4j 数据到 Clawra
with neo4j_driver.session() as session:
    result = session.run("MATCH (a)-[r]->(b) RETURN a, r, b")
    for record in result:
        subject = record["a"]["name"]
        predicate = record["r"].type
        obj = record["b"]["name"]
        clawra.add_fact(subject, predicate, obj)

neo4j_driver.close()
```

### 3.2 导出到 RDF

```python
# 导出为 RDF Turtle 格式
rdf_output = clawra.export_knowledge(format="rdf")

with open("knowledge.rdf", "w") as f:
    f.write(rdf_output)
```

### 3.3 批量导入 CSV

```python
import csv

from src.clawra import Clawra

clawra = Clawra()

# CSV 格式：subject, predicate, object, confidence
with open("facts.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        clawra.add_fact(
            row["subject"],
            row["predicate"],
            row["object"],
            confidence=float(row.get("confidence", 0.9))
        )
```

---

## 4. Webhook 外部触发

### 4.1 接收外部事件

```python
from flask import Flask, request
from src.clawra import Clawra

app = Flask(__name__)
clawra = Clawra(enable_memory=True)

@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.json
    
    if event["type"] == "fact_added":
        # 新增事实触发学习
        clawra.add_fact(
            event["subject"],
            event["predicate"],
            event["object"],
            event.get("confidence", 0.9)
        )
        
    elif event["type"] == "document":
        # 文档触发学习
        clawra.learn(event["content"])
    
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(port=5000)
```

### 4.2 Clawra 事件回调

```python
from src.clawra.events import EventEmitter

# 定义事件处理
def on_pattern_discovered(pattern):
    print(f"发现新模式: {pattern.name}")
    # 发送通知、触发其他系统等

def on_inference_complete(conclusions):
    if any("危险" in c.conclusion for c in conclusions):
        # 发送告警
        send_alert(conclusions)

# 注册监听器
emitter = EventEmitter()
emitter.on("pattern_discovered", on_pattern_discovered)
emitter.on("inference_complete", on_inference_complete)
```

---

## 5. API Server 部署

### 5.1 FastAPI 服务

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from src.clawra import Clawra

app = FastAPI(title="Clawra API")
agent = Clawra(enable_memory=True)

class LearnRequest(BaseModel):
    text: str
    domain_hint: Optional[str] = None

class FactRequest(BaseModel):
    subject: str
    predicate: str
    object: str
    confidence: float = 0.9

@app.post("/learn")
def learn(req: LearnRequest):
    result = agent.learn(req.text, domain_hint=req.domain_hint)
    return result

@app.post("/fact")
def add_fact(req: FactRequest):
    success = agent.add_fact(req.subject, req.predicate, req.object, req.confidence)
    return {"success": success}

@app.get("/query")
def query(subject: Optional[str] = None, predicate: Optional[str] = None, object: Optional[str] = None):
    results = agent.query(subject, predicate, object)
    return {"results": [{"subject": r.subject, "predicate": r.predicate, "object": r.object} for r in results]}

@app.post("/reason")
def reason(max_depth: int = 10):
    conclusions = agent.reason(max_depth=max_depth)
    return {"conclusions": [{"premise": c.premise, "conclusion": c.conclusion, "rule_id": c.rule_id} for c in conclusions]}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 5.2 启动服务

```bash
# 开发环境
uvicorn src.api.server:app --reload --port 8000

# 生产环境
uvicorn src.api.server:app --workers 4 --host 0.0.0.0 --port 8000
```

---

## 6. Docker 部署

### 6.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY .env .

EXPOSE 8000

CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 docker-compose.yml

```yaml
version: '3.8'

services:
  clawra-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
    depends_on:
      - neo4j
    volumes:
      - ./data:/app/data

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data

volumes:
  neo4j_data:
```

### 6.3 启动

```bash
docker-compose up -d
docker-compose logs -f clawra-api
```

---

## 7. 外部 LLM 切换

### 7.1 使用 OpenAI

```python
import os
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = "your-key"

agent = Clawra(llm_provider="openai", llm_model="gpt-4")
```

### 7.2 使用 Claude

```python
import os
os.environ["LLM_PROVIDER"] = "anthropic"
os.environ["ANTHROPIC_API_KEY"] = "your-key"

agent = Clawra(llm_provider="anthropic", llm_model="claude-3-opus")
```

### 7.3 使用本地 Ollama

```python
agent = Clawra(
    llm_provider="ollama",
    llm_model="llama3",
    llm_base_url="http://localhost:11434"
)
```

### 7.4 使用 MiniMax

```python
import os
os.environ["MINIMAX_API_KEY"] = "your-key"

agent = Clawra(
    llm_provider="minimax",
    llm_model="MiniMax-M2.7",
    llm_base_url="https://api.minimax.chat/v1"
)
```

---

**最后更新**: 2026-04-13
