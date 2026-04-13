# Clawra 部署指南

> 从开发环境到生产环境的完整部署方案。

---

## 1. 环境要求

### 1.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 8 核+ |
| 内存 | 4 GB | 16 GB+ |
| 磁盘 | 10 GB | 50 GB+ SSD |
| OS | Ubuntu 20.04+ / macOS 12+ / Windows 10+ | Ubuntu 22.04 LTS |

### 1.2 依赖服务

| 服务 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 运行环境 |
| Neo4j | 5.x | 知识图谱存储 |
| ChromaDB | 0.4+ | 向量检索 |
| Redis | 7.x | 缓存（可选） |

### 1.3 Python 环境

```bash
# 推荐使用 pyenv 管理 Python 版本
pyenv install 3.11.6
pyenv virtualenv 3.11.6 clawra

# 或使用 conda
conda create -n clawra python=3.11
conda activate clawra
```

---

## 2. 开发环境部署

### 2.1 克隆项目

```bash
git clone https://github.com/wu-xiaochen/ontology-platform.git
cd ontology-platform
```

### 2.2 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate   # Windows
```

### 2.3 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.4 配置环境变量

```bash
cp .env.example .env

# 编辑 .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxx

LOG_LEVEL=DEBUG
```

### 2.5 启动本地服务

```bash
# Neo4j（macOS）
brew services start neo4j

# 或 Docker
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5

# ChromaDB
docker run -d --name chromadb \
  -p 8000:8000 \
  chromadb/chroma:latest

# 验证服务
curl http://localhost:7474
curl http://localhost:8000
```

### 2.6 验证安装

```bash
python -c "
from src.clawra import Clawra
agent = Clawra(enable_memory=False)
result = agent.learn('测试数据')
print('✅ 安装成功' if result['success'] else '❌ 安装失败')
"
```

---

## 3. Docker 部署

### 3.1 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/
COPY .env .

# 创建非 root 用户
RUN useradd -m -u 1000 clawra && \
    chown -R clawra:clawra /app
USER clawra

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 docker-compose.yml（完整栈）

```yaml
# docker-compose.yml
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
      - LLM_PROVIDER=${LLM_PROVIDER}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      neo4j:
        condition: service_healthy
      chromadb:
        condition: service_started
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 5

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chromadb_data:/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  neo4j_data:
  neo4j_logs:
  chromadb_data:
  redis_data:
```

### 3.3 启动

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f clawra-api

# 检查健康状态
docker-compose ps

# 停止
docker-compose down
```

### 3.4 生产环境启动

```bash
# 使用生产配置文件
docker-compose -f docker-compose.prod.yml up -d

# 扩缩容
docker-compose up -d --scale clawra-api=3
```

---

## 4. Kubernetes 部署

### 4.1 命名空间

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: clawra
  labels:
    name: clawra
```

### 4.2 ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: clawra-config
  namespace: clawra
data:
  LOG_LEVEL: "INFO"
  LLM_PROVIDER: "openai"
  NEO4J_URI: "bolt://neo4j-svc:7687"
---
apiVersion: v1
kind: Secret
metadata:
  name: clawra-secrets
  namespace: clawra
type: Opaque
stringData:
  NEO4J_PASSWORD: "your_secure_password"
  OPENAI_API_KEY: "sk-xxxx"
```

### 4.3 Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clawra-api
  namespace: clawra
spec:
  replicas: 3
  selector:
    matchLabels:
      app: clawra-api
  template:
    metadata:
      labels:
        app: clawra-api
    spec:
      containers:
        - name: clawra-api
          image: clawra/api:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: clawra-config
            - secretRef:
                name: clawra-secrets
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: clawra-api-svc
  namespace: clawra
spec:
  selector:
    app: clawra-api
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: clawra-ingress
  namespace: clawra
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
    - host: api.clawra.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: clawra-api-svc
                port:
                  number: 80
```

### 4.4 部署命令

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml

# 查看状态
kubectl get pods -n clawra
kubectl logs -f deployment/clawra-api -n clawra
```

---

## 5. 生产环境检查清单

### 5.1 安全

- [ ] 所有密钥使用环境变量或 Kubernetes Secret
- [ ] Neo4j 启用认证
- [ ] API 使用 HTTPS
- [ ] 限制容器运行权限（不使用 root）
- [ ] 定期更新基础镜像

### 5.2 性能

- [ ] 配置资源限制（CPU/内存）
- [ ] 启用缓存
- [ ] 配置连接池
- [ ] 启用压缩（gzip）

### 5.3 监控

- [ ] 配置日志聚合（ELK/Loki）
- [ ] 配置指标采集（Prometheus）
- [ ] 配置告警规则
- [ ] 健康检查端点

### 5.4 备份

- [ ] Neo4j 定期备份
- [ ] ChromaDB 数据备份
- [ ] 配置文件的版本控制

---

## 6. 环境变量参考

```bash
# ========== LLM 配置 ==========
LLM_PROVIDER=openai           # openai | anthropic | ollama | minimax
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
OLLAMA_BASE_URL=http://localhost:11434
MINIMAX_API_KEY=xxx
MINIMAX_GROUP_ID=xxx

# ========== Neo4j 配置 ==========
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=xxx

# ========== ChromaDB 配置 ==========
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# ========== Redis 配置 ==========
REDIS_HOST=localhost
REDIS_PORT=6379

# ========== 应用配置 ==========
LOG_LEVEL=INFO
DEBUG=false
ENABLE_MEMORY=true
CACHE_SIZE=1000
CONNECTION_POOL_SIZE=10

# ========== 服务器配置 ==========
HOST=0.0.0.0
PORT=8000
WORKERS=4
TIMEOUT=30
```

---

## 7. 健康检查

### 7.1 API 健康检查

```bash
curl http://localhost:8000/health

# 响应
{
  "status": "healthy",
  "version": "3.5.0",
  "services": {
    "neo4j": "connected",
    "chromadb": "connected"
  }
}
```

### 7.2 Docker 健康检查

```bash
# 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' clawra-api

# 检查日志中的健康检查结果
docker inspect --format='{{range .State.Health.Log}} {{.Output}} {{end}}' clawra-api
```

---

## 8. 故障恢复

### 8.1 Neo4j 数据恢复

```bash
# 停止服务
docker-compose stop clawra-api

# 从备份恢复
docker-compose exec neo4j bash -c "neo4j-admin database restore --from=/backups/neo4j-$(date +%Y%m%d)"

# 重启
docker-compose start clawra-api
```

### 8.2 服务重启

```bash
# Docker
docker-compose restart clawra-api

# Kubernetes
kubectl rollout restart deployment/clawra-api -n clawra
kubectl rollout status deployment/clawra-api -n clawra
```

---

**最后更新**: 2026-04-13
