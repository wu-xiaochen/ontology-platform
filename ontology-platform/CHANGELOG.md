# Changelog

本文档按照 [Keep a Changelog](https://keepachangelog.com/) 规范维护。

---

## [未发布] (Unreleased)

### Added
- **数据导出模块** (`src/export.py`):
  - 多格式导出支持 (JSON, CSV, Turtle, JSON-LD)
  - 三元组导出
  - 实体导出
  - Schema导出
  - 元数据包含选项

- **权限管理模块** (`src/permissions.py`):
  - 细粒度RBAC权限控制
  - 角色管理 (创建、更新、删除)
  - 用户-角色映射
  - 权限继承
  - 资源级别访问控制

- **增强缓存模块** (`src/caching.py`):
  - LRU缓存 (带TTL和标签)
  - 两级缓存 (L1 + L2)
  - 监控缓存 (带访问日志)
  - 缓存失效策略
  - 缓存工厂函数

- **API 新增端点**:
  - `POST /api/v1/export/triples` - 导出三元组
  - `POST /api/v1/export/entities` - 导出实体
  - `POST /api/v1/export/schema` - 导出Schema
  - `GET /api/v1/permissions/roles` - 列出角色
  - `POST /api/v1/permissions/roles` - 创建角色
  - `PUT /api/v1/permissions/roles/{name}` - 更新角色
  - `DELETE /api/v1/permissions/roles/{name}` - 删除角色
  - `GET /api/v1/permissions/users/{id}/roles` - 获取用户角色
  - `POST /api/v1/permissions/users/roles` - 分配角色
  - `GET /api/v1/permissions/users/{id}/permissions` - 获取用户权限
  - `GET /api/v1/permissions/check` - 检查权限
  - `GET /api/v1/performance/cache/two-level` - 两级缓存统计
  - `GET /api/v1/performance/cache/debug` - 调试缓存统计
  - `GET /api/v1/performance/cache/debug/log` - 缓存访问日志
  - `POST /api/v1/performance/cache/clear-all` - 清除所有缓存
  - `POST /api/v1/performance/cache/invalidate` - 标签失效

## [3.4.0] - 2026-03-17

### Added
- **监控模块** (`src/monitoring.py`):
  - Prometheus 指标收集器
  - 请求/响应时间追踪
  - 健康检查端点 (`/health/detailed`)
  - 性能快照生成器
  - 关联ID (correlation ID) 支持

- **安全模块** (`src/security.py`):
  - API 密钥管理 (生成、验证、撤销)
  - 速率限制 (Token Bucket 算法)
  - IP 阻止机制
  - 安全头部中间件
  - 输入验证和清洗
  - 审计日志

- **性能优化模块** (`src/performance.py`):
  - LRU 缓存实现
  - 通用连接池
  - 异步批处理器
  - 查询优化器
  - 性能分析器
  - 资源管理器

- **API 新增端点**:
  - `GET /metrics` - Prometheus 指标
  - `GET /health/detailed` - 详细健康检查
  - `POST /api/v1/auth/api-keys` - 创建API密钥
  - `GET /api/v1/auth/api-keys` - 列出API密钥
  - `GET /api/v1/performance/cache` - 缓存统计
  - `POST /api/v1/performance/cache/clear` - 清除缓存
  - `GET /api/v1/performance/profiler` - 性能分析

- **Docker Compose 更新**:
  - 添加 Prometheus 服务
  - 添加 Grafana 服务
  - 健康检查优化

### Changed
- API 版本升级到 3.4.0
- 配置文件 (`config.yaml`) 添加监控、安全、性能配置节
- 重构 API 主文件，集成新模块
- CORS 中间件配置化

### Security
- 添加请求速率限制
- 添加 IP 阻止机制
- 添加 API 密钥认证
- 添加安全头部 (HSTS, CSP, X-Frame-Options 等)
- 输入验证和清洗

### Performance
- 添加推理结果缓存
- 添加查询优化
- 添加性能分析支持
- 添加连接池管理

---

### Added
- 基础项目框架搭建 (Python + Node.js)
- 本体论推理引擎核心模块
- 知识图谱可视化组件
- 基础 RESTful API 服务
- 多领域支持：燃气工程、采购供应链、安全生产、金融风控

### Changed
- 优化图数据库查询性能
- 更新依赖包版本

### Deprecated
- /api/legacy/ endpoint (将于 2.0.0 移除)

### Removed
- 移除已废弃的 XML 导出功能

### Fixed
- 修复本体推理引擎内存泄漏问题
- 修复并发写入冲突问题

### Security
- 修复 XSS 漏洞 (CVE-2024-XXXX)

---

## [0.9.0] - 2026-03-16

### Added
- **核心推理引擎**: 实现基于置信度的推理机制 (`confidence.py`)
- **本体加载器**: OWL 本体文件解析与加载 (`loader.py`)
- **知识图谱API**: 提供 RESTful 接口进行本体查询和推理
- **监控模块**: 基础系统监控能力
- **Docker 支持**: 提供 Dockerfile 和 docker-compose.yml
- **安全模块**: 基础安全策略文档

### Changed
- 重构项目目录结构，清晰划分模块
- 更新依赖版本至稳定版本
- 优化 API 响应格式

### Fixed
- 修复首次加载大型本体时的超时问题
- 修复 API 并发请求处理

### Security
- 添加基础认证中间件
- 实现请求速率限制

---

## [0.5.0] - 2026-02-01

### Added
- 项目初始化
- 基础目录结构创建
- README.md 和版本管理策略文档
- 基础 Makefile 构建脚本

### Changed
- 确定技术栈选型

### Fixed
- 修复 Git 仓库初始化问题

---

## 版本历史

| 版本 | 日期 | 状态 | 说明 |
|------|------|------|------|
| [0.9.0] | 2026-03-16 | ✅ | 核心功能开发完成 |
| [0.5.0] | 2026-02-01 | ✅ | 项目初始化 |
| [0.1.0] | 2026-01-15 | ✅ | 概念验证 |

---

## 即将发布

### [1.0.0] - 计划 2026年6月 (V1.0 MVP)

#### 核心功能
- 供应商管理模块 (查询、详情页)
- 智能推荐供应商
- 供应链拓扑图可视化
- 风险警报系统

#### 技术交付物
- React + Ant Design 前端应用
- 基础本体论模型 (OWL)
- RESTful API (20+ endpoints)
- 基础AI推荐模型

#### 里程碑
- M1.1 - 基础框架 (4月15日)
- M1.2 - 数据模型 (4月30日)
- M1.3 - 核心API (5月20日)
- M1.4 - 前端MVP (6月10日)
- M1.5 - 集成测试 (6月25日)
- V1.0 发布 (6月30日)

---

## 变更类型说明

| 类型 | 说明 |
|------|------|
| **Added** | 新增功能 |
| **Changed** | 现有功能变更 |
| **Deprecated** | 即将移除的功能 |
| **Removed** | 已移除的功能 |
| **Fixed** | Bug 修复 |
| **Security** | 安全修复 |

---

## 更新日志

- **standard-version**: 基于 Git commits 自动生成
- **release-it**: 完整的发布自动化工具

```bash
# 使用 standard-version
npx standard-version

# 使用 release-it
npx release-it
```

---

*本文档将根据项目进展定期更新*
