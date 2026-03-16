# 贡献指南

感谢您对 ontology-platform 项目的兴趣！我们欢迎任何形式的贡献，包括但不限于代码改进、文档完善、问题反馈和功能建议。

## 如何贡献

### 1. 报告问题

如果您发现了 bug 或有功能建议，请通过 GitHub Issues 报告。请包含以下信息：

- 清晰的问题描述
- 复现步骤（如果是 bug）
- 环境信息（操作系统、Python 版本等）
- 相关的日志或截图

### 2. 提交代码

#### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/wu-xiaochen/ontology-platform.git
cd ontology-platform

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 代码规范

- **Python**: 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 风格指南
- **注释**: 使用中文注释，确保代码可读性
- **命名**: 使用清晰的英文变量/函数命名
- **提交信息**: 使用清晰简洁的提交信息，格式如下：
  ```
  <type>(<scope>): <description>
  
  [可选的详细描述]
  
  [可选的关联 Issue]
  ```

#### Type 说明

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

#### Pull Request 流程

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/your-feature`)
3. 进行开发并提交更改
4. 推送分支 (`git push origin feature/your-feature`)
5. 打开 Pull Request
6. 等待代码 review 和合并

### 3. 完善文档

文档是项目的重要组成部分，欢迎：

- 修正错别字或语法错误
- 补充缺失的文档
- 翻译文档为其他语言
- 提供使用示例

## 项目结构

```
ontology-platform/
├── src/              # 源代码
├── examples/         # 示例代码
├── domain_expert/    # 领域专家文档
├── cto/              # 技术架构文档
├── pm/               # 产品管理文档
├── reasoner/         # 推理引擎相关
├── consultant/       # 顾问相关
├── monitoring/       # 监控相关
└── docs/             # 文档目录
```

## 行为准则

请保持友善和专业的交流态度。我们期待一个包容、开放的社区环境。

## 联系方式

- GitHub: https://github.com/wu-xiaochen/ontology-platform
- 问题反馈: 通过 GitHub Issues

感谢您的贡献！🎉
