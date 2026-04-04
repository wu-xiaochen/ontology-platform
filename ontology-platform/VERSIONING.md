# 版本管理策略 (Version Management Strategy)

本文档定义了 ontology-platform 项目的版本控制规范，确保版本发布的一致性和可追溯性。

---

## 1. 语义化版本 (Semantic Versioning)

### 版本格式

```
MAJOR.MINOR.PATCH[-预发布版本][+构建元数据]
```

| 组件 | 说明 | 示例 |
|------|------|------|
| MAJOR | 主版本号 | 不兼容的 API 变更 |
| MINOR | 次版本号 | 向后兼容的新功能 |
| PATCH | 补丁版本号 | 向后兼容的 bug 修复 |
| 预发布版本 | 测试版/候选版 | alpha.1, beta.2, rc.1 |
| 构建元数据 | 构建信息 | build.20240316, git.abc123 |

### 版本号递增规则

```
1. MAJOR 版本号递增：当存在不兼容的 API 变更
2. MINOR 版本号递增：新增向后兼容的功能
3. PATCH 版本号递增：向后兼容的 bug 修复

预发布版本优先级低于正式版本：
1.0.0-alpha.1 < 1.0.0-alpha.2 < 1.0.0-beta.1 < 1.0.0-rc.1 < 1.0.0
```

### 版本兼容性承诺

- **MAJOR 版本**：不保证兼容性，需要迁移指南
- **MINOR 版本**：完全向后兼容
- **PATCH 版本**：完全向后兼容

---

## 2. 发布流程 (Release Process)

### 分支策略

```
main          → 生产环境稳定代码
develop       → 开发主分支
release/*     → 发布准备分支
hotfix/*      → 紧急修复分支
feature/*     → 功能开发分支
```

### 发布流程图

```
develop 分支
    ↓
创建 release/* 分支 (版本号确定)
    ↓
预发布测试 (Pre-release Testing)
    ↓
更新版本号 & CHANGELOG
    ↓
合并到 main 分支 & 打标签 (vX.Y.Z)
    ↓
合并回 develop 分支
    ↓
发布 (构建 & 部署)
```

### 发布步骤

#### 步骤 1: 准备发布

```bash
# 从 develop 创建发布分支
git checkout -b release/v1.2.0 develop

# 更新版本号
npm version 1.2.0
# 或手动修改 package.json version 字段
```

#### 步骤 2: 预发布测试

- 运行完整测试套件
- 更新 CHANGELOG.md
- 确认所有功能完整

#### 步骤 3: 正式发布

```bash
# 合并到 main
git checkout main
git merge --no-ff release/v1.2.0

# 打标签
git tag -a v1.2.0 -m "Release v1.2.0"

# 推送到远程
git push origin main --tags

# 合并回 develop
git checkout develop
git merge --no-ff release/v1.2.0
git push origin develop

# 删除发布分支
git branch -d release/v1.2.0
```

#### 步骤 4: 紧急修复 (Hotfix)

```bash
# 从 main 创建 hotfix 分支
git checkout -b hotfix/v1.2.1 main

# 修复后更新版本号
npm version 1.2.1

# 合并到 main 和 develop
git checkout main
git merge --no-ff hotfix/v1.2.1
git tag -a v1.2.1 -m "Hotfix v1.2.1"

git checkout develop
git merge --no-ff hotfix/v1.2.1
```

---

## 3. 版本兼容性 (Version Compatibility)

### 兼容性类型

| 类型 | 说明 | 范围 |
|------|------|------|
| **API 兼容性** | REST API 接口的向后兼容性 | MINOR 版本内保证 |
| **数据兼容性** | 数据库 schema、存储格式变化 | MINOR 版本内保证 |
| **协议兼容性** | 客户端-服务器通信协议 | MAJOR 版本内保证 |
| **功能兼容性** | 命令行参数、环境变量 | MINOR 版本内保证 |

### API 兼容性规则

```python
# ✅ 兼容的变更 (MINOR/PATCH)
- 新增可选参数
- 新增 API 端点
- 扩展返回字段（不删除现有字段）
- 修改非关键错误信息

# ❌ 不兼容的变更 (MAJOR)
- 删除或重命名端点
- 删除或重命名参数
- 修改参数类型
- 改变响应格式结构
- 修改必需/可选状态
```

### 数据迁移策略

```yaml
# 版本升级数据迁移
migration_policy:
  # 自动迁移 (Minor 版本)
  auto_migrate:
    - 索引优化
    - 缓存结构调整
    - 元数据更新
  
  # 手动迁移 (Major 版本)
  manual_migration:
    - schema 变更
    - 数据格式转换
    - 迁移脚本执行
    - 回滚方案准备

# 兼容性保证
backward_compatibility:
  # 数据保留期限
  data_retention: "3个版本"
  
  # 配置兼容
  config_compat: "自动合并旧配置"
```

### 弃用策略 (Deprecation)

```markdown
## 弃用周期

| 弃用类型 | 通知时机 | 移除时机 |
|----------|----------|----------|
| API 端点 | 首次发布弃用时 | 下一个 MAJOR 版本 |
| 参数/字段 | 首次发布弃用时 | 2个 MINOR 版本后 |
| 功能特性 | 首次发布弃用时 | 下一个 MAJOR 版本 |

## 弃用标记示例

```python
# Python 弃用警告
import warnings

def legacy_api():
    warnings.warn(
        "legacy_api() 将在 2.0.0 版本移除，请使用 new_api()",
        DeprecationWarning,
        stacklevel=2
    )
```

### 向后兼容性测试

```yaml
# .github/workflows/compatibility-test.yml
name: Compatibility Tests

on:
  pull_request:
    branches: [develop, main]

jobs:
  compatibility:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        # 测试最近 3 个版本
        version: [current, current-1, current-2]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run API Compatibility Tests
        run: |
          # 测试 API 向后兼容
          pytest tests/api_compat/
          
      - name: Run Schema Compatibility Tests
        run: |
          # 测试数据库 schema 兼容
          pytest tests/schema_compat/
```

### 客户端版本匹配

```markdown
## 客户端兼容性矩阵

| 服务器版本 | 支持的客户端版本 |
|------------|-------------------|
| 2.x | 2.x, 1.x (部分) |
| 1.x | 1.x |
| 0.x | 0.x |

## 版本探测

```bash
# 客户端版本检查
curl -s https://api.example.com/v1/version
# 返回: {"version": "1.2.0", "min_client_version": "1.0.0"}
```

### 版本降级策略

```markdown
## 不支持降级

⚠️ **重要**: 不支持从高版本降级到低版本。
如需降级，请重新安装对应版本并恢复备份数据。

## 降级场景处理

| 场景 | 推荐方案 |
|------|----------|
| 新版本有严重 bug | 等待 patch 版本或使用 hotfix |
| 需要回滚功能 | 使用版本控制恢复代码 |
| 数据兼容问题 | 恢复数据库备份 |
```

---

## 4. CHANGELOG (变更日志)

### CHANGELOG 格式

采用 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范：

```markdown
# Changelog

本文档按照 [Keep a Changelog](https://keepachangelog.com/) 规范维护。

## [1.2.0] - 2024-03-20

### Added
- 新增知识图谱可视化组件
- 支持 OWL 2.0 语法解析
- 新增 REST API 端点: /api/v1/ontology/validate

### Changed
- 优化图数据库查询性能 (提升 40%)
- 更新依赖包版本

### Deprecated
- 弃用 /api/legacy/ endpoint (将于 2.0.0 移除)

### Removed
- 移除已废弃的 XML 导出功能

### Fixed
- 修复本体推理引擎内存泄漏问题
- 修复并发写入冲突问题

### Security
- 修复 XSS 漏洞 (CVE-2024-XXXX)
```

### 版本历史结构

```markdown
## [未发布] (Unreleased)

### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [1.1.0] - 2024-02-15

...
```

### 变更类型说明

| 类型 | 说明 |
|------|------|
| **Added** | 新增功能 |
| **Changed** | 现有功能变更 |
| **Deprecated** | 即将移除的功能 |
| **Removed** | 已移除的功能 |
| **Fixed** | Bug 修复 |
| **Security** | 安全修复 |

### 自动化工具

推荐使用以下工具自动生成 CHANGELOG：

- **standard-version**: 基于 Git commits 自动生成
- **release-it**: 完整的发布自动化工具
- **changesets**: 管理多包变更集

```bash
# 使用 standard-version
npx standard-version

# 使用 release-it
npx release-it
```

---

## 版本号参考示例

```
v1.0.0       - 初始正式版本
v1.0.1       - Bug 修复
v1.1.0       - 新功能添加
v1.1.0-beta.1 - 测试版
v1.1.0-rc.1   - 候选发布版
v2.0.0       - 重大更新 (breaking changes)
v2.0.1       - 2.0.0 的 bug 修复
```

---

## 相关文件

- `package.json` - 项目版本定义
- `CHANGELOG.md` - 变更日志
- `.github/workflows/release.yml` - 自动发布工作流
