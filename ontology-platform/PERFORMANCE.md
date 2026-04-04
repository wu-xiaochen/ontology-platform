# 性能优化文档

本文档定义了 ontology-platform 的性能指标、优化策略和基准测试规范。

---

## 1. 性能指标

### 1.1 API 响应时间

| 指标 | 目标值 | 告警阈值 |
|------|--------|----------|
| P50 延迟 | < 200ms | > 500ms |
| P90 延迟 | < 500ms | > 1s |
| P99 延迟 | < 1s | > 2s |

### 1.2 吞吐量

| 指标 | 目标值 |
|------|--------|
| QPS (每秒请求数) | > 100 |
| 并发连接数 | > 50 |

### 1.3 推理引擎

| 指标 | 目标值 |
|------|--------|
| 单次推理耗时 | < 300ms |
| 批量推理 (100条) | < 5s |
| 本体加载时间 | < 2s |

### 1.4 资源利用率

| 指标 | 目标范围 |
|------|----------|
| CPU 使用率 | 40% - 70% |
| 内存使用率 | < 80% |
| GPU 利用率 | > 60% |

---

## 2. 优化策略

### 2.1 缓存策略

- **推理结果缓存**: 对相同输入的推理结果进行缓存，TTL 设置为 1 小时
- **本体数据缓存**: 本体数据加载后缓存在内存中，避免重复读取
- **热点数据**: 使用 Redis 缓存热点知识库数据

```python
# 缓存示例
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_inference(query: str, context: dict) -> Result:
    return reasoner.inference(query, context)
```

### 2.2 数据库优化

- **索引优化**: 为高频查询字段创建复合索引
- **连接池**: 使用数据库连接池，配置最小 5 个连接
- **查询优化**: 避免 SELECT *，只查询必要字段
- **分页查询**: 大数据集使用游标分页而非 OFFSET

### 2.3 算法优化

- **批量处理**: 合并多个独立推理请求为批量处理
- **剪枝策略**: 推理过程中跳过不必要的路径
- **近似算法**: 对准确度要求不高的场景使用近似算法

### 2.4 并发优化

- **异步IO**: 使用 asyncio 处理 IO 密集型任务
- **多进程**: CPU 密集型任务使用 multiprocessing
- **协程池**: 配置合理的协程池大小

### 2.5 资源配置

- **Gunicorn Workers**: 配置 `workers = (2 * CPU_CORES) + 1`
- **Uvicorn Workers**: 使用 `workers = CPU_CORES`
- **超时设置**: 推理超时设置为 30s

---

## 3. 基准测试

### 3.1 测试环境

- **服务器**: 8 核 CPU, 16GB 内存
- **数据库**: PostgreSQL 14, Redis 7
- **Python**: 3.10+
- **依赖**: 见 requirements.txt

### 3.2 测试工具

```bash
# 安装测试工具
pip install locust pytest-benchmark

# 运行 API 基准测试
locust -f tests/locustfile.py --host=http://localhost:8000

# 运行推理引擎基准测试
pytest tests/benchmark_reasoner.py --benchmark-only
```

### 3.3 测试场景

#### 3.3.1 API 响应时间测试

```python
# tests/benchmark_api.py
import time
import requests

def test_api_latency():
    """测试 API 响应时间"""
    times = []
    for _ in range(100):
        start = time.time()
        response = requests.post(
            "http://localhost:8000/api/v1/reason",
            json={"query": "测试查询", "domain": "gas"}
        )
        times.append(time.time() - start)
    
    # 计算 P50, P90, P99
    times.sort()
    p50 = times[50]
    p90 = times[90]
    p99 = times[99]
    
    assert p50 < 0.2, f"P50 延迟 {p50}s 超过目标 200ms"
    assert p90 < 0.5, f"P90 延迟 {p90}s 超过目标 500ms"
    assert p99 < 1.0, f"P99 延迟 {p99}s 超过目标 1s"
```

#### 3.3.2 吞吐量测试

```python
# tests/benchmark_throughput.py
import concurrent.futures
import requests

def test_throughput():
    """测试系统吞吐量"""
    def make_request():
        return requests.post(
            "http://localhost:8000/api/v1/reason",
            json={"query": "测试查询", "domain": "gas"}
        )
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        start = time.time()
        results = list(executor.map(lambda _: make_request(), range(1000)))
        duration = time.time() - start
    
    qps = 1000 / duration
    assert qps > 100, f"QPS {qps} 未达到目标 100"
```

#### 3.3.3 推理引擎基准测试

```python
# tests/benchmark_reasoner.py
import pytest
from src.reasoner import Reasoner

reasoner = Reasoner()

@pytest.mark.benchmark
def test_reasoner_single(benchmark):
    """单次推理基准测试"""
    result = benchmark(
        reasoner.inference,
        "燃气管道泄漏如何处理",
        {"domain": "gas", "context": {}}
    )
    assert result is not None

@pytest.mark.benchmark
def test_reasoner_batch(benchmark):
    """批量推理基准测试"""
    queries = [
        ("燃气管道泄漏如何处理", {"domain": "gas", "context": {}}),
        ("采购流程是什么", {"domain": "procurement", "context": {}}),
        # ... 更多查询
    ]
    
    def batch_inference():
        return [reasoner.inference(q, c) for q, c in queries]
    
    result = benchmark(batch_inference)
    assert len(result) == len(queries)
```

### 3.4 性能回归检测

```bash
# 在 CI/CD 中运行基准测试
pytest tests/benchmark_reasoner.py \
    --benchmark-compare=main \
    --benchmark-json=benchmark.json

# 性能下降超过 20% 时失败
```

---

## 4. 监控与告警

### 4.1 关键指标监控

使用 Prometheus + Grafana 监控以下指标：

- `api_request_duration_seconds` - API 请求延迟
- `api_requests_total` - API 请求总数
- `reasoner_inference_duration_seconds` - 推理耗时
- `reasoner_cache_hit_total` - 缓存命中率

### 4.2 告警规则

| 指标 | 条件 | 级别 |
|------|------|------|
| P99 延迟 | > 2s | Warning |
| P99 延迟 | > 5s | Critical |
| QPS | < 50 | Warning |
| 缓存命中率 | < 60% | Warning |

---

## 5. 持续优化

1. **每日监控**: 每日检查性能指标趋势
2. **周优化**: 每周分析慢请求，优化热点路径
3. **月度复盘**: 每月评估优化效果，调整目标

---

*最后更新: 2026-03-16*
