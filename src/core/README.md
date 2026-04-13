# Core Module

核心基础模块，提供平台的基础设施和通用功能。

## 核心组件

### errors.py
错误处理系统：
- 统一的异常类型定义
- 错误码规范
- 错误上下文记录

### loader.py
数据加载器：
- 多格式文件支持（PDF, DOCX, TXT, MD）
- 文本分块（Chunking）
- 元数据提取

### permissions.py
权限管理：
- RBAC（基于角色的访问控制）
- 细粒度权限控制
- 权限继承

### security.py
安全模块：
- 输入验证
- 输出过滤
- 敏感信息保护

### reasoner.py
通用推理器：
- 逻辑推理
- 矛盾检测
- 知识融合

### ontology/ 子目录
核心本体定义：
- 基础概念模型
- 关系类型定义
- 约束规则

## 使用示例

```python
from src.core.loader import DocumentLoader
from src.core.permissions import PermissionChecker

# 加载文档
loader = DocumentLoader()
docs = loader.load("path/to/document.pdf")

# 权限检查
checker = PermissionChecker()
if checker.can_access(user, resource, "read"):
    # 执行操作
    pass
```

## 错误码规范

| 错误码范围 | 类型 | 说明 |
|-----------|------|------|
| 1000-1999 | 系统错误 | 内部错误 |
| 2000-2999 | 验证错误 | 输入验证失败 |
| 3000-3999 | 权限错误 | 权限不足 |
| 4000-4999 | 业务错误 | 业务逻辑错误 |

## 支持的文档格式

- PDF
- DOCX / DOC
- TXT
- Markdown
- HTML
- CSV / Excel

## 分块策略

### 固定大小分块
- 按字符数分块
- 重叠区域（overlap）

### 语义分块
- 按段落/章节
- 保持语义完整性

### 自适应分块
- 根据内容类型自动选择
- 最优分块大小

## 依赖

- PyPDF2 >= 3.0.0
- python-docx >= 0.8.0
- beautifulsoup4 >= 4.11.0
- pandas >= 2.0.0
