# SDK 使用

## 初始化

```python
from clawra import Clawra

clawra = Clawra()
```

## learn() - 学习知识

```python
result = clawra.learn(
    text="燃气调压箱出口压力不得超过 0.4MPa",
    domain="industrial_safety"  # 可选
)

print(result)
# {'extracted_triples': [...], 'patterns_discovered': 3}
```

## reason() - 推理

```python
result = clawra.reason(
    query="调压箱最大安全压力是多少？"
)

print(result)
# {'conclusion': '0.4 MPa', 'confidence': 0.95, 'reasoning_trace': [...]}
```

## retrieve() - 检索

```python
result = clawra.retrieve(
    query="燃气安全规范",
    top_k=5
)

for item in result:
    print(item['content'])
```

## evolve() - 触发进化

```python
# 异步调用
result = await clawra.evolve(trigger="automatic")

print(result)
# {'stages': {...}, 'conflicts_resolved': 2}
```

## 完整示例

```python
from clawra import Clawra

async def main():
    clawra = Clawra()

    # 学习领域知识
    await clawra.learn("""
    天然气管道最大允许压力: 0.4MPa
    管道检测周期: 每季度一次
    紧急情况: 压力超过 0.35MPa 触发截断
    """)

    # 推理验证
    result = await clawra.reason(
        "如果管道压力是 0.5MPa，安全吗？"
    )
    print(result['conclusion'])  # → 不安全

    # 触发进化优化
    await clawra.evolve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```
