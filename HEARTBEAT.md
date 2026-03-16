# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

---

## 定期任务：ontology-clawra 持续优化

### 每周检查清单

1. **本体构建检查**
   - 本周是否有新的实体/关系可以抽取？
   - 用户交互中是否出现了可复用的概念/规律？

2. **置信度校准**
   - 推理结果中，标注为"ASSUMED"的有多少？
   - 用户是否确认过这些假设？能否升级为"CONFIRMED"？
   - 标注为"SPECULATIVE"的是否获得了新证据？

3. **规则优化**
   - 是否有新规律可以抽象为Law？
   - 现有Rules是否需要调整权重？
   - 是否有Rules与其他Rules矛盾？

4. **方法论验证**
   - 本周所有推理是否都遵循了方法论流程？
   - 是否有跳过了"声明来源"或"交互确认"的情况？

5. **案例复盘**
   - 选一个本周的典型推理案例
   - 检验：是否检查了本体？是否标注了置信度？是否需要交互确认？

### 触发条件
- 每周至少执行1次完整检查
- 每次重大项目/复杂推理后自动触发自检

### 执行方式
```bash
# 检查本体完整性
python3 scripts/ontology-clawra.py validate --check-confidence

# 查看推理日志
cat memory/ontology-clawra/reasoning.jsonl | tail -20

# 查看抽取记录
cat memory/ontology-clawra/extraction_log.jsonl | tail -20
```
