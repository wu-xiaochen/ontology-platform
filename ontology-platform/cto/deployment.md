# 本体推理平台部署文档

**版本**: V1.0  
**制定人**: CTO  
**日期**: 2026-03-16  
**密级**: 内部

---

## 目录

1. [概述](#1-概述)
2. [Docker部署](#2-docker部署)
3. [Kubernetes部署](#3-kubernetes部署)
4. [环境变量配置](#4-环境变量配置)
5. [监控告警](#5-监控告警)
6. [部署检查清单](#6-部署检查清单)

---

## 1. 概述

### 1.1 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 20GB | 50GB+ |
| Docker | 20.10+ | 24.0+ |
| Kubernetes | 1.24+ | 1.28+ |

### 1.2 组件架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   API服务   │────▶│    Redis    │────▶│  推理引擎   │
│  (FastAPI)  │     │   (缓存)    │     │  (Python)   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       ▼                                       ▼
┌─────────────┐                         ┌─────────────┐
│   Nginx     │                         │ SQLite/PG   │
│  (反向代理) │                         │  (数据库)   │
└─────────────┘                         └─────────────┘
```

---

## 2. Docker部署

### 2.1 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.2 Docker Compose 本地开发

```yaml
# docker-compose.yml
version: '3.8'

services:
  # API服务
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ontology-api
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DB_URL=sqlite:///data/ontology.db
      - LOG_LEVEL=info
      - API_WORKERS=4
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: ontology-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: ontology-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped

volumes:
  redis-data:
```

### 2.3 Docker Compose 生产部署

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    image: ontology-platform/api:${VERSION:-latest}
    container_name: ontology-api-prod
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DB_URL=postgresql://user:password@db:5432/ontology
      - LOG_LEVEL=warning
      - API_WORKERS=8
      - JWT_SECRET=${JWT_SECRET}
      - JWT_ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy
    restart: always
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 20s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    container_name: ontology-redis-prod
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 20s
      timeout: 5s
      retries: 3

  # PostgreSQL数据库
  db:
    image: postgres:15-alpine
    container_name: ontology-db-prod
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=ontology
    volumes:
      - pg-data:/var/lib/postgresql/data
      - ./backup:/backup
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  nginx:
    image: nginx:alpine
    container_name: ontology-nginx-prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - api
    restart: always

volumes:
  redis-data:
  pg-data:
```

### 2.4 快速启动命令

```bash
# 克隆项目
git clone <repository-url>
cd ontology-platform

# 开发环境启动
docker-compose up -d

# 生产环境启动
VERSION=v1.0.0 docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

---

## 3. Kubernetes部署

### 3.1 Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ontology-platform
  labels:
    name: ontology-platform
    environment: production
```

### 3.2 ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ontology-config
  namespace: ontology-platform
data:
  LOG_LEVEL: "info"
  API_WORKERS: "4"
  REDIS_URL: "redis://redis-service:6379/0"
  DB_TYPE: "postgresql"
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  DB_NAME: "ontology"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  JWT_ALGORITHM: "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: "30"
---
apiVersion: v1
kind: Secret
metadata:
  name: ontology-secrets
  namespace: ontology-platform
type: Opaque
stringData:
  DB_USER: "ontology_user"
  DB_PASSWORD: "${DB_PASSWORD}"
  REDIS_PASSWORD: "${REDIS_PASSWORD}"
  JWT_SECRET: "${JWT_SECRET}"
```

### 3.3 Redis部署

```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-deployment
  namespace: ontology-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
          - redis-server
          - "--appendonly"
          - "yes"
          - "--requirepass"
          - "$(REDIS_PASSWORD)"
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        livenessProbe:
          exec:
            command: ["redis-cli", "-a", "$(REDIS_PASSWORD)", "ping"]
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command: ["redis-cli", "-a", "$(REDIS_PASSWORD)", "ping"]
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: ontology-platform
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: ontology-platform
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### 3.4 PostgreSQL部署

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-deployment
  namespace: ontology-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: ontology-secrets
              key: DB_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ontology-secrets
              key: DB_PASSWORD
        - name: POSTGRES_DB
          value: ontology
        ports:
        - containerPort: 5432
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command: ["pg_isready", "-U", "ontology_user"]
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command: ["pg_isready", "-U", "ontology_user"]
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: ontology-platform
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: ontology-platform
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
```

### 3.5 API服务部署

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ontology-api
  namespace: ontology-platform
  labels:
    app: ontology-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ontology-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: ontology-api
    spec:
      containers:
      - name: api
        image: ontology-platform/api:${VERSION:-latest}
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: ontology-config
        - secretRef:
            name: ontology-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 5
          failureThreshold: 3
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - ontology-api
              topologyKey: kubernetes.io/hostname
---
apiVersion: v1
kind: Service
metadata:
  name: ontology-api-service
  namespace: ontology-platform
spec:
  selector:
    app: ontology-api
  ports:
  - port: 80
    targetPort: 8000
    name: http
  type: ClusterIP
```

### 3.6 HPA自动扩缩容

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ontology-api-hpa
  namespace: ontology-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ontology-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### 3.7 Ingress配置

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ontology-ingress
  namespace: ontology-platform
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.ontology.example.com
    secretName: ontology-tls-secret
  rules:
  - host: api.ontology.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ontology-api-service
            port:
              number: 80
```

### 3.8 部署清单

```bash
# 创建所有K8s资源
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml

# 查看部署状态
kubectl get pods -n ontology-platform
kubectl get svc -n ontology-platform
kubectl get hpa -n ontology-platform

# 查看日志
kubectl logs -f deployment/ontology-api -n ontology-platform

# 扩缩容
kubectl scale deployment ontology-api --replicas=10 -n ontology-platform
```

---

## 4. 环境变量配置

### 4.1 必需变量

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `REDIS_URL` | string | `redis://localhost:6379/0` | Redis连接地址 |
| `DB_TYPE` | string | `sqlite` | 数据库类型 (sqlite/postgresql) |
| `DB_URL` | string | `sqlite:///ontology.db` | 数据库连接URL |
| `JWT_SECRET` | string | - | JWT签名密钥 (必需) |
| `JWT_ALGORITHM` | string | `HS256` | JWT算法 |
| `API_HOST` | string | `0.0.0.0` | API监听地址 |
| `API_PORT` | string | `8000` | API监听端口 |

### 4.2 可选变量

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `LOG_LEVEL` | string | `info` | 日志级别 (debug/info/warning/error) |
| `API_WORKERS` | int | `4` | Uvicorn工作进程数 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `30` | 访问令牌过期时间 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | `7` | 刷新令牌过期时间 |
| `ONTOLOGY_DIR` | string | `./ontology` | 本体文件目录 |
| `CACHE_TTL` | int | `3600` | 缓存TTL(秒) |
| `MAX_CONCURRENT_REQUESTS` | int | `100` | 最大并发请求数 |
| `REQUEST_TIMEOUT` | int | `30` | 请求超时时间(秒) |

### 4.3 生产环境示例

```bash
# .env.production
# 数据库
DB_TYPE=postgresql
DB_USER=ontology_user
DB_PASSWORD=your_secure_password_here
DB_HOST=postgres-service
DB_PORT=5432
DB_NAME=ontology
DB_URL=postgresql://ontology_user:your_secure_password_here@postgres-service:5432/ontology

# Redis
REDIS_PASSWORD=your_redis_password_here
REDIS_URL=redis://:your_redis_password_here@redis-service:6379/0

# 安全
JWT_SECRET=your_very_long_and_secure_jwt_secret_key_here_at_least_32_chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=8
LOG_LEVEL=warning

# 业务
ONTOLOGY_DIR=/app/ontology
CACHE_TTL=3600
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
```

---

## 5. 监控告警

### 5.1 Prometheus指标配置

```python
# src/monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# 请求计数器
request_counter = Counter(
    'ontology_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

# 请求延迟
request_latency = Histogram(
    'ontology_api_request_duration_seconds',
    'API request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
)

# 活跃连接数
active_connections = Gauge(
    'ontology_active_connections',
    'Number of active connections'
)

# 推理次数
reasoning_total = Counter(
    'ontology_reasoning_total',
    'Total reasoning operations',
    ['domain', 'status']
)

# 推理延迟
reasoning_duration = Histogram(
    'ontology_reasoning_duration_seconds',
    'Reasoning operation duration',
    ['domain']
)

# 缓存命中率
cache_hit_rate = Gauge(
    'ontology_cache_hit_rate',
    'Cache hit rate'
)
```

### 5.2 Prometheus配置

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ontology-api'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: ontology-api
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: pod
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: namespace
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### 5.3 Grafana仪表盘

```json
{
  "dashboard": {
    "title": "Ontology Platform",
    "panels": [
      {
        "title": "API请求率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ontology_api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "API延迟P99",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(ontology_api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "推理成功率",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(ontology_reasoning_total{status=\"success\"}[5m])) / sum(rate(ontology_reasoning_total[5m]))",
            "legendFormat": "成功率"
          }
        ]
      },
      {
        "title": "CPU使用率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(process_cpu_seconds_total{job=\"ontology-api\"}[5m]) * 100",
            "legendFormat": "CPU %"
          }
        ]
      },
      {
        "title": "内存使用",
        "type": "graph",
        "targets": [
          {
            "expr": "process_resident_memory_bytes{job=\"ontology-api\"} / 1024 / 1024",
            "legendFormat": "Memory MB"
          }
        ]
      },
      {
        "title": "缓存命中率",
        "type": "gauge",
        "targets": [
          {
            "expr": "ontology_cache_hit_rate",
            "legendFormat": "Hit Rate"
          }
        ]
      }
    ]
  }
}
```

### 5.4 告警规则

```yaml
# prometheus/alerts.yml
groups:
  - name: ontology-alerts
    rules:
      # API不可用
      - alert: APIUnavailable
        expr: up{job="ontology-api"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "API服务不可用"
          description: "API服务已经停止响应超过2分钟"

      # 高错误率
      - alert: HighErrorRate
        expr: rate(ontology_api_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API错误率过高"
          description: "API 5xx错误率超过5%，当前值: {{ $value }}"

      # 高延迟
      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(ontology_api_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API延迟过高"
          description: "API P99延迟超过5秒，当前值: {{ $value }}s"

      # 推理失败
      - alert: ReasoningFailures
        expr: rate(ontology_reasoning_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "推理失败率过高"
          description: "推理失败率超过10%，当前值: {{ $value }}"

      # 内存不足
      - alert: HighMemoryUsage
        expr: (process_resident_memory_bytes{job="ontology-api"} / process_max_memory_bytes{job="ontology-api"}) > 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率超过90%，当前值: {{ $value }}"

      # CPU过载
      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total{job="ontology-api"}[5m]) > 0.95
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "CPU使用率超过95%，当前值: {{ $value }}"

      # Redis不可用
      - alert: RedisUnavailable
        expr: up{job="redis"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Redis服务不可用"
          description: "Redis服务已经停止响应超过2分钟"

      # 数据库不可用
      - alert: DatabaseUnavailable
        expr: up{job="postgres"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "数据库服务不可用"
          description: "PostgreSQL服务已经停止响应超过2分钟"

      # Pod重启
      - alert: PodRestarting
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pod频繁重启"
          description: "Pod {{ $labels.pod }} 重启频率过高"

      # HPA扩容
      - alert: HPAScalingUp
        expr: kube_horizontalpodautoscaler_status_desired_replicas > kube_horizontalpodautoscaler_status_current_replicas
        for: 1m
        labels:
          severity: info
        annotations:
          summary: "HPA正在扩容"
          description: "HPA正在扩容，当前副本数: {{ $labels.current_replicas }}，目标: {{ $labels.desired_replicas }}"
```

### 5.5 告警通知配置

```yaml
# alertmanager/config.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-notifications'
    continue: true
  - match:
      severity: warning
    receiver: 'warning-notifications'

receivers:
  - name: 'default'
    webhook_configs:
    - url: 'http://notification-service:9090/webhook'

  - name: 'critical-notifications'
    webhook_configs:
    - url: 'http://notification-service:9090/webhook/critical'
    - url: 'http://pagerduty:9090/pagerduty'

  - name: 'warning-notifications'
    webhook_configs:
    - url: 'http://notification-service:9090/webhook/warning'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'namespace']
```

---

## 6. 部署检查清单

### 6.1 部署前检查

- [ ] 服务器资源满足要求
- [ ] 所有环境变量已配置
- [ ] 基础镜像已准备
- [ ] 数据库已初始化
- [ ] SSL证书已准备
- [ ] 监控告警已配置
- [ ] 备份策略已制定

### 6.2 部署验证

- [ ] 所有Pod正常运行
- [ ] API健康检查通过
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] 日志正常输出
- [ ] 监控指标正常采集
- [ ] 告警规则生效

### 6.3 功能验证

- [ ] 用户认证正常
- [ ] 推理接口正常
- [ ] 本体加载正常
- [ ] 缓存正常工作
- [ ] 日志记录正常

---

**文档状态**: 已完成  
**下次更新**: 根据实际部署经验补充
