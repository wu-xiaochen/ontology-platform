# OWL 语义增强指南

本文档说明 ontology-platform 中 OWL 约束的正确使用方式。

## ⚠️ 关键概念：开放世界假设 (OWA)

ontology-platform 基于 **OWL** 构建，遵循 **开放世界假设 (Open World Assumption, OWA)**。

### OWA vs CWA（封闭世界假设）

| 特性 | OWA (OWL) | CWA (传统数据库) |
|------|-----------|------------------|
| 未知事实 | 视为"未知"而非"假" | 视为"假" |
| 约束 | 不满足才报错 | 满足才存在 |
| 推理 | 允许推理新知识 | 仅验证已知 |

### 示例

```turtle
# OWA 视角：除非另有说明，否则类可能还有其他属性
:Supplier rdf:type owl:Class .
# 没有说 Supplier 只能有一个地址，所以可以有多个

# CWA 视角：表的外键约束
# 只有明确存在的记录才能关联
```

## 约束 vs OWL 属性限制

### ❌ 错误理解
```python
# 错误：将 OWL 限制当作数据库约束
# 这在 OWA 下不会阻止额外值的出现
product :hasPart [a :Part] .
```

### ✅ 正确理解
```python
# OWL 限制表达的是"最小/最大基数"，不是"恰好"
# :Product rdf:type owl:Class ;
#     rdfs:subClassOf [
#         a owl:Restriction ;
#         owl:onProperty :hasPart ;
#         owl:minCardinality 1   # 至少1个，但可以有更多
#     ] .
```

## 在 Prompt 中区分

当使用 LLM 进行本体校验时，请明确指示：

```
你正在基于 OWL 的开放世界假设进行推理。
- 除非明确用 owl:allValuesFrom 限制，否则属性可以接受任何值
- 未声明的类/属性不等于不存在
- 基数限制 (min/max) 不等同于唯一性约束
```

## 参考文献

- OWL 2 Web Ontology Language Primer
- Description Logic Handbook
- Ontology Development 101: A Guide to Creating Your First Ontology

---
*本文档对应战略报告第 6.2 节*
