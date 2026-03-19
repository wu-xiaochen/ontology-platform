# 贡献指南

感谢您对 ontology-platform 的兴趣！我们欢迎各种形式的贡献。

## 如何贡献

### 1. 报告问题
- 在 GitHub Issues 中创建新 issue
- 清晰描述问题或功能需求
- 提供复现步骤（如果是 bug）

### 2. 提交代码
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. Push 到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 3. 代码规范
- 遵循 PEP 8 Python 代码规范
- 为新功能添加测试
- 更新相关文档

### 4. 本体贡献
- 新增领域本体需包含完整定义
- 遵循 `domain_expert/` 目录结构
- 提供中英文双语描述

## 项目结构

```
ontology-platform/
├── domain_expert/     # 领域本体库
├── src/               # 核心源代码
├── scripts/           # 脚本工具
├── skills/            # AI Agent技能
├── docs/              # 文档
└── tests/             # 测试
```

## 许可

通过贡献代码，您同意您的贡献将按照 MIT 许可证授权。
