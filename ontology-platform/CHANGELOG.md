# Changelog

本文档按照 [Keep a Changelog](https://keepachangelog.com/) 规范维护。

---

## [未发布] (Unreleased)

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
