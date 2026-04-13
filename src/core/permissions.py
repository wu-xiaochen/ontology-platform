"""
Permission Management Module - 企业级 RBAC 权限管理系统

提供细粒度的基于角色的访问控制 (Role-Based Access Control)

v2.0.0 - 企业级增强版本
- 角色层级管理（admin > editor > viewer）
- 资源级别权限控制（知识图谱、推理引擎、Agent 系统等）
- 权限继承机制（子角色继承父角色权限）
- 权限检查装饰器 @require_permission(resource, action)
- 配置化角色和权限定义（零硬编码原则）
- 权限缓存优化（提升性能）
"""

import json
import logging
import functools
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from threading import Lock
from functools import lru_cache

# 导入配置管理器，实现配置化权限定义
from ..utils.config import get_config

logger = logging.getLogger(__name__)


# ==================== 权限和资源定义 ====================

class Permission(Enum):
    """
    系统权限枚举
    
    按照功能模块划分权限类别：
    - read:* 读取权限
    - write:* 写入权限
    - admin:* 管理权限
    - execute:* 执行权限
    - special:* 特殊权限
    """
    # 读取权限 - 基础查询操作
    READ_SCHEMA = "read:schema"           # 读取本体模式
    READ_ENTITIES = "read:entities"       # 读取实体
    READ_RELATIONSHIPS = "read:relationships"  # 读取关系
    READ_TRIPLES = "read:triples"         # 读取三元组
    READ_INFERENCES = "read:inferences"   # 读取推理结果
    READ_STATS = "read:stats"             # 读取统计信息
    READ_LINEAGE = "read:lineage"         # 读取数据血缘
    READ_AUDIT_LOG = "audit:view"         # 查看审计日志
    
    # 写入权限 - 数据修改操作
    WRITE_SCHEMA = "write:schema"         # 修改本体模式
    WRITE_ENTITIES = "write:entities"     # 创建/修改实体
    WRITE_RELATIONSHIPS = "write:relationships"  # 创建/修改关系
    WRITE_TRIPLES = "write:triples"       # 创建/修改三元组
    WRITE_INFERENCES = "write:inferences"  # 创建/修改推理结果
    
    # 管理权限 - 系统管理操作
    ADMIN_USERS = "admin:users"           # 用户管理
    ADMIN_ROLES = "admin:roles"           # 角色管理
    ADMIN_API_KEYS = "admin:api_keys"     # API密钥管理
    ADMIN_EXPORT = "admin:export"         # 数据导出管理
    ADMIN_SETTINGS = "admin:settings"     # 系统设置管理
    ADMIN_SECURITY = "admin:security"     # 安全设置管理
    
    # 执行权限 - 功能调用操作
    EXECUTE_REASONING = "execute:reasoning"  # 执行推理
    EXECUTE_LEARNING = "execute:learning"    # 执行学习
    EXECUTE_AGENT = "execute:agent"          # 执行Agent操作
    
    # 特殊权限
    EXPORT_DATA = "export:data"           # 导出数据
    IMPORT_DATA = "import:data"           # 导入数据
    BULK_OPERATIONS = "bulk:operations"   # 批量操作


class ResourceType(Enum):
    """
    资源类型枚举
    
    定义系统中所有可访问的资源类型，
    用于资源级别的权限控制。
    """
    # 知识图谱资源
    SCHEMA = "schema"           # 本体模式
    ENTITY = "entity"           # 实体
    RELATIONSHIP = "relationship"  # 关系
    TRIPLE = "triple"           # 三元组
    
    # 推理引擎资源
    INFERENCE = "inference"     # 推理结果
    RULE = "rule"               # 推理规则
    
    # Agent 系统资源
    AGENT = "agent"             # Agent实例
    TOOL = "tool"               # 工具
    
    # 系统管理资源
    USER = "user"               # 用户
    ROLE = "role"               # 角色
    API_KEY = "api_key"         # API密钥
    EXPORT = "export"           # 导出任务
    
    # 审计和监控资源
    AUDIT_LOG = "audit_log"     # 审计日志
    METRICS = "metrics"         # 监控指标
    TRACE = "trace"             # 链路追踪


class Action(Enum):
    """
    操作类型枚举
    
    定义对资源可执行的操作类型。
    """
    CREATE = "create"    # 创建
    READ = "read"        # 读取
    UPDATE = "update"    # 更新
    DELETE = "delete"    # 删除
    EXECUTE = "execute"  # 执行
    EXPORT = "export"    # 导出
    IMPORT = "import"    # 导入
    ADMIN = "admin"      # 管理


# ==================== 资源和访问规则定义 ====================

@dataclass
class Resource:
    """
    资源定义
    
    表示系统中需要权限控制的资源实例。
    """
    type: ResourceType              # 资源类型
    id: str                          # 资源唯一标识
    owner: str = ""                  # 资源所有者ID
    attributes: Dict[str, Any] = field(default_factory=dict)  # 资源属性
    
    def __hash__(self):
        # 使用类型和ID作为哈希依据，确保资源唯一性
        return hash((self.type, self.id))


@dataclass
class AccessRule:
    """
    访问控制规则
    
    定义权限、资源类型和访问条件之间的映射关系。
    """
    permission: Permission           # 所需权限
    resource_type: ResourceType      # 资源类型
    resource_id: Optional[str] = None  # 特定资源ID（None表示任意资源）
    owner_only: bool = False         # 是否仅限所有者访问


# ==================== 角色定义 ====================

@dataclass
class Role:
    """
    角色定义
    
    包含角色的完整定义信息，支持权限继承和层级管理。
    """
    name: str                        # 角色名称（唯一标识）
    description: str                 # 角色描述
    permissions: Set[Permission] = field(default_factory=set)  # 直接权限
    inherits_from: List[str] = field(default_factory=list)  # 继承的父角色
    level: int = 0                   # 角色层级（数值越大权限越高）
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(self, permission: Permission) -> bool:
        """检查角色是否拥有指定权限"""
        return permission in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于序列化"""
        return {
            "name": self.name,
            "description": self.description,
            "permissions": [p.value for p in self.permissions],
            "inherits_from": self.inherits_from,
            "level": self.level,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Role":
        """从字典创建角色实例"""
        # 解析权限列表
        permissions = set()
        for p in data.get("permissions", []):
            try:
                permissions.add(Permission(p))
            except ValueError:
                logger.warning(f"未知权限: {p}，已跳过")
        
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            permissions=permissions,
            inherits_from=data.get("inherits_from", []),
            level=data.get("level", 0),
        )


def _build_default_roles() -> Dict[str, Role]:
    """
    构建默认角色定义
    
    从配置文件读取角色定义，如果配置文件不存在则使用内置默认值。
    符合零硬编码原则：所有角色定义均可通过配置覆盖。
    """
    config = get_config().permission
    
    # 尝试从配置文件加载角色定义
    roles_config_path = config.roles_config_path
    if roles_config_path and Path(roles_config_path).exists():
        try:
            with open(roles_config_path, "r", encoding="utf-8") as f:
                roles_data = json.load(f)
            roles = {}
            for role_data in roles_data.get("roles", []):
                role = Role.from_dict(role_data)
                roles[role.name] = role
            logger.info(f"从配置文件加载了 {len(roles)} 个角色: {roles_config_path}")
            return roles
        except Exception as e:
            logger.warning(f"加载角色配置文件失败: {e}，使用默认配置")
    
    # 使用内置默认角色定义
    # 注意：这些是代码中的后备默认值，应优先使用配置文件
    role_hierarchy = config.get_role_hierarchy()
    
    default_roles = {
        "admin": Role(
            name="admin",
            description="系统管理员 - 拥有所有权限",
            permissions={
                # 所有读取权限
                Permission.READ_SCHEMA, Permission.READ_ENTITIES,
                Permission.READ_RELATIONSHIPS, Permission.READ_TRIPLES,
                Permission.READ_INFERENCES, Permission.READ_STATS,
                Permission.READ_LINEAGE, Permission.READ_AUDIT_LOG,
                # 所有写入权限
                Permission.WRITE_SCHEMA, Permission.WRITE_ENTITIES,
                Permission.WRITE_RELATIONSHIPS, Permission.WRITE_TRIPLES,
                Permission.WRITE_INFERENCES,
                # 所有管理权限
                Permission.ADMIN_USERS, Permission.ADMIN_ROLES,
                Permission.ADMIN_API_KEYS, Permission.ADMIN_EXPORT,
                Permission.ADMIN_SETTINGS, Permission.ADMIN_SECURITY,
                # 所有执行权限
                Permission.EXECUTE_REASONING, Permission.EXECUTE_LEARNING,
                Permission.EXECUTE_AGENT,
                # 特殊权限
                Permission.EXPORT_DATA, Permission.IMPORT_DATA,
                Permission.BULK_OPERATIONS,
            },
            level=role_hierarchy.get("admin", 100),
        ),
        "editor": Role(
            name="editor",
            description="编辑者 - 可以读写本体数据和执行推理",
            permissions={
                # 读取权限
                Permission.READ_SCHEMA, Permission.READ_ENTITIES,
                Permission.READ_RELATIONSHIPS, Permission.READ_TRIPLES,
                Permission.READ_INFERENCES, Permission.READ_STATS,
                Permission.READ_LINEAGE,
                # 写入权限
                Permission.WRITE_SCHEMA, Permission.WRITE_ENTITIES,
                Permission.WRITE_RELATIONSHIPS, Permission.WRITE_TRIPLES,
                Permission.WRITE_INFERENCES,
                # 执行权限
                Permission.EXECUTE_REASONING, Permission.EXECUTE_LEARNING,
            },
            level=role_hierarchy.get("editor", 50),
        ),
        "viewer": Role(
            name="viewer",
            description="查看者 - 只读访问权限",
            permissions={
                # 仅读取权限
                Permission.READ_SCHEMA, Permission.READ_ENTITIES,
                Permission.READ_RELATIONSHIPS, Permission.READ_TRIPLES,
                Permission.READ_INFERENCES, Permission.READ_STATS,
            },
            level=role_hierarchy.get("viewer", 10),
        ),
        "api_user": Role(
            name="api_user",
            description="API用户 - 程序化访问权限",
            permissions={
                # API访问常用的读取权限
                Permission.READ_SCHEMA, Permission.READ_ENTITIES,
                Permission.READ_RELATIONSHIPS, Permission.READ_TRIPLES,
                Permission.READ_INFERENCES,
                # 执行推理权限
                Permission.EXECUTE_REASONING,
            },
            level=role_hierarchy.get("api_user", 30),
        ),
        "export_user": Role(
            name="export_user",
            description="导出用户 - 可以读取和导出数据",
            permissions={
                # 读取权限
                Permission.READ_SCHEMA, Permission.READ_ENTITIES,
                Permission.READ_RELATIONSHIPS, Permission.READ_TRIPLES,
                # 导出权限
                Permission.EXPORT_DATA,
            },
            inherits_from=["viewer"],  # 继承viewer的权限
            level=role_hierarchy.get("export_user", 20),
        ),
    }
    
    # 应用权限继承（使用循环检测避免循环引用）
    for role_name, role in default_roles.items():
        inherited_perms = set()
        # 使用 visited 集合检测循环继承
        visited = {role_name}  # 记录已处理的角色链，防止 A->B->A 的循环
        
        def resolve_inheritance(parent_name: str, inheritance_chain: List[str]) -> None:
            """
            递归解析权限继承，检测循环引用
            
            Args:
                parent_name: 父角色名称
                inheritance_chain: 当前继承链，用于错误报告
            """
            if parent_name in visited:
                # 检测到循环继承，记录 WARNING 并跳过
                cycle_path = " -> ".join(inheritance_chain + [parent_name])
                logger.warning(f"检测到角色循环继承，已跳过: {cycle_path}")
                return
            
            if parent_name not in default_roles:
                return
            
            visited.add(parent_name)
            parent_role = default_roles[parent_name]
            
            # 添加父角色的权限
            inherited_perms.update(parent_role.permissions)
            
            # 递归处理父角色的继承
            for grandparent in parent_role.inherits_from:
                resolve_inheritance(grandparent, inheritance_chain + [parent_name])
        
        # 解析每个父角色的继承
        for parent_name in role.inherits_from:
            resolve_inheritance(parent_name, [role_name])
        
        role.permissions.update(inherited_perms)
    
    return default_roles


# ==================== 权限管理器 ====================

class PermissionManager:
    """
    权限管理器 - 核心权限控制类
    
    职责：
    - 管理角色定义和角色层级
    - 管理用户-角色映射
    - 执行权限检查
    - 缓存权限计算结果以提升性能
    
    设计原则：
    - 单例模式：全局唯一的权限管理器
    - 配置驱动：所有配置从 ConfigManager 读取
    - 线程安全：使用锁保护并发访问
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        # 单例模式：确保全局只有一个权限管理器实例
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # 避免重复初始化
        if self._initialized:
            return
        
        self._initialized = True
        
        # 从配置获取设置
        config = get_config().permission
        
        # 角色存储
        self._roles: Dict[str, Role] = {}
        # 用户-角色映射：user_id -> Set[role_name]
        self._user_roles: Dict[str, Set[str]] = {}
        # 用户权限缓存：user_id -> Set[Permission]
        self._user_permissions: Dict[str, Set[Permission]] = {}
        # 角色权限缓存：role_name -> Set[Permission]
        self._role_permissions: Dict[str, Set[Permission]] = {}
        # 权限缓存过期时间
        self._cache_timestamp: Dict[str, datetime] = {}
        
        # 初始化默认角色
        default_roles = _build_default_roles()
        for name, role in default_roles.items():
            self._roles[name] = role
            self._role_permissions[name] = role.permissions.copy()
        
        # 存储角色层级信息
        self._role_hierarchy = config.get_role_hierarchy()
        
        # 超级管理员角色名
        self._super_admin_role = config.super_admin_role
        
        # 是否启用权限缓存
        self._enable_cache = config.enable_permission_cache
        self._cache_ttl = config.permission_cache_ttl
        
        # 权限拒绝时的行为
        self._denial_action = config.denial_action
        
        logger.info(f"PermissionManager 初始化完成: {len(self._roles)} 个角色, 缓存={'启用' if self._enable_cache else '禁用'}")
    
    # ==================== 角色层级管理 ====================
    
    def get_role_level(self, role_name: str) -> int:
        """
        获取角色层级
        
        层级越高权限越大，用于角色比较和权限继承。
        """
        role = self._roles.get(role_name)
        return role.level if role else 0
    
    def compare_roles(self, role1: str, role2: str) -> int:
        """
        比较两个角色的层级
        
        返回值：
        - 正数：role1 层级高于 role2
        - 负数：role1 层级低于 role2
        - 0：层级相同
        """
        level1 = self.get_role_level(role1)
        level2 = self.get_role_level(role2)
        return level1 - level2
    
    def get_higher_roles(self, role_name: str) -> List[str]:
        """
        获取所有层级高于指定角色的角色列表
        
        用于权限继承和提升判断。
        """
        target_level = self.get_role_level(role_name)
        return [
            name for name, role in self._roles.items()
            if role.level > target_level
        ]
    
    def get_lower_roles(self, role_name: str) -> List[str]:
        """
        获取所有层级低于指定角色的角色列表
        
        用于权限降级判断。
        """
        target_level = self.get_role_level(role_name)
        return [
            name for name, role in self._roles.items()
            if role.level < target_level
        ]
    
    # ==================== 角色管理 ====================
    
    def create_role(
        self,
        name: str,
        description: str,
        permissions: Set[Permission] = None,
        inherits_from: List[str] = None,
        level: int = 0,
    ) -> Role:
        """
        创建新角色
        
        支持权限继承：新角色自动获得父角色的所有权限。
        """
        with self._lock:
            # 检查角色是否已存在
            if name in self._roles:
                raise ValueError(f"角色已存在: {name}")
            
            # 创建角色实例
            role = Role(
                name=name,
                description=description,
                permissions=permissions or set(),
                inherits_from=inherits_from or [],
                level=level,
            )
            
            # 解析继承的权限（带循环检测）
            all_perms = set(permissions or [])
            visited = {name}  # 记录已访问角色，防止循环继承
            
            def resolve_with_cycle_check(parent_name: str, chain: List[str]) -> Set[Permission]:
                """
                递归解析权限继承，检测循环引用
                
                Args:
                    parent_name: 父角色名称
                    chain: 当前继承链
                    
                Returns:
                    继承的权限集合
                """
                if parent_name in visited:
                    cycle = " -> ".join(chain + [parent_name])
                    logger.warning(f"检测到角色循环继承，已跳过: {cycle}")
                    return set()
                
                if parent_name not in self._roles:
                    logger.warning(f"父角色不存在: {parent_name}")
                    return set()
                
                visited.add(parent_name)
                parent = self._roles[parent_name]
                perms = set(parent.permissions)
                
                # 递归解析祖父角色
                for grandparent in parent.inherits_from:
                    perms.update(resolve_with_cycle_check(grandparent, chain + [parent_name]))
                
                return perms
            
            for parent_name in role.inherits_from:
                all_perms.update(resolve_with_cycle_check(parent_name, [name]))
            
            role.permissions = all_perms
            self._roles[name] = role
            self._role_permissions[name] = all_perms
            
            # 清除用户权限缓存
            self._invalidate_user_cache()
            
            logger.info(f"创建角色: {name}, 权限数={len(all_perms)}, 层级={level}")
            return role
    
    def update_role(
        self,
        name: str,
        description: str = None,
        permissions: Set[Permission] = None,
        inherits_from: List[str] = None,
        level: int = None,
    ) -> Role:
        """
        更新现有角色
        
        更新后会重新计算权限继承关系。
        """
        with self._lock:
            if name not in self._roles:
                raise ValueError(f"角色不存在: {name}")
            
            role = self._roles[name]
            
            # 更新各字段
            if description is not None:
                role.description = description
            if permissions is not None:
                role.permissions = permissions
            if inherits_from is not None:
                role.inherits_from = inherits_from
            if level is not None:
                role.level = level
            
            # 重新计算权限继承（带循环检测）
            all_perms = set(role.permissions)
            visited = {name}  # 记录已访问角色，防止循环继承
            
            def resolve_with_cycle_check_update(parent_name: str, chain: list) -> set:
                """
                递归解析权限继承，检测循环引用
                
                Args:
                    parent_name: 父角色名称
                    chain: 当前继承链
                    
                Returns:
                    继承的权限集合
                """
                if parent_name in visited:
                    cycle = " -> ".join(chain + [parent_name])
                    logger.warning(f"检测到角色循环继承，已跳过: {cycle}")
                    return set()
                
                if parent_name not in self._roles:
                    return set()
                
                visited.add(parent_name)
                parent = self._roles[parent_name]
                perms = set(parent.permissions)
                
                # 递归解析祖父角色
                for grandparent in parent.inherits_from:
                    perms.update(resolve_with_cycle_check_update(grandparent, chain + [parent_name]))
                
                return perms
            
            for parent_name in role.inherits_from:
                all_perms.update(resolve_with_cycle_check_update(parent_name, [name]))
            
            role.permissions = all_perms
            role.updated_at = datetime.now()
            self._role_permissions[name] = all_perms
            
            # 清除用户权限缓存
            self._invalidate_user_cache()
            
            logger.info(f"更新角色: {name}, 权限数={len(all_perms)}")
            return role
    
    def delete_role(self, name: str) -> bool:
        """
        删除角色
        
        注意：默认角色不可删除。
        """
        with self._lock:
            if name not in self._roles:
                return False
            
            # 检查是否为默认角色
            if name in _build_default_roles():
                raise ValueError(f"不能删除默认角色: {name}")
            
            # 从所有用户中移除该角色
            for user_id in self._user_roles:
                self._user_roles[user_id].discard(name)
            
            del self._roles[name]
            self._role_permissions.pop(name, None)
            
            # 清除用户权限缓存
            self._invalidate_user_cache()
            
            logger.info(f"删除角色: {name}")
            return True
    
    def get_role(self, name: str) -> Optional[Role]:
        """获取角色定义"""
        return self._roles.get(name)
    
    def list_roles(self) -> List[Dict[str, Any]]:
        """
        列出所有角色
        
        返回角色的详细信息列表。
        """
        with self._lock:
            return [
                {
                    "name": r.name,
                    "description": r.description,
                    "permissions": [p.value for p in r.permissions],
                    "inherits_from": r.inherits_from,
                    "level": r.level,
                    "created_at": r.created_at.isoformat(),
                    "updated_at": r.updated_at.isoformat(),
                }
                for r in sorted(self._roles.values(), key=lambda x: x.level, reverse=True)
            ]
    
    # ==================== 用户-角色管理 ====================
    
    def assign_role(self, user_id: str, role_name: str) -> bool:
        """
        为用户分配角色
        
        用户可拥有多个角色，权限取并集。
        """
        with self._lock:
            # 验证角色存在
            if role_name not in self._roles:
                raise ValueError(f"角色不存在: {role_name}")
            
            # 初始化用户角色集合
            if user_id not in self._user_roles:
                self._user_roles[user_id] = set()
            
            self._user_roles[user_id].add(role_name)
            
            # 清除该用户的权限缓存
            self._user_permissions.pop(user_id, None)
            self._cache_timestamp.pop(user_id, None)
            
            logger.info(f"为用户 {user_id} 分配角色: {role_name}")
            return True
    
    def remove_role(self, user_id: str, role_name: str) -> bool:
        """
        移除用户的角色
        """
        with self._lock:
            if user_id in self._user_roles:
                self._user_roles[user_id].discard(role_name)
                # 清除该用户的权限缓存
                self._user_permissions.pop(user_id, None)
                self._cache_timestamp.pop(user_id, None)
                logger.info(f"移除用户 {user_id} 的角色: {role_name}")
                return True
            return False
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """获取用户的所有角色"""
        with self._lock:
            return list(self._user_roles.get(user_id, set()))
    
    def get_user_highest_role(self, user_id: str) -> Optional[str]:
        """
        获取用户层级最高的角色
        
        用于快速判断用户权限等级。
        """
        roles = self.get_user_roles(user_id)
        if not roles:
            return None
        return max(roles, key=lambda r: self.get_role_level(r))
    
    # ==================== 权限检查 ====================
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        获取用户的所有权限
        
        合并用户所有角色的权限，使用缓存优化性能。
        在检查缓存时顺便清理过期条目，避免内存泄漏。
        """
        with self._lock:
            # 在检查缓存时顺便清理过期条目（每 100 次调用执行一次清理）
            if self._enable_cache and hasattr(self, '_cache_check_count'):
                self._cache_check_count = getattr(self, '_cache_check_count', 0) + 1
                if self._cache_check_count % 100 == 0:
                    self._cleanup_expired_cache()
            
            # 检查缓存是否有效
            if self._enable_cache and user_id in self._user_permissions:
                cache_time = self._cache_timestamp.get(user_id)
                if cache_time:
                    elapsed = (datetime.now() - cache_time).total_seconds()
                    if elapsed < self._cache_ttl:
                        return self._user_permissions[user_id].copy()
            
            # 计算用户权限
            perms = set()
            roles = self._user_roles.get(user_id, set())
            
            for role_name in roles:
                if role_name in self._role_permissions:
                    perms.update(self._role_permissions[role_name])
            
            # 更新缓存
            if self._enable_cache:
                self._user_permissions[user_id] = perms.copy()
                self._cache_timestamp[user_id] = datetime.now()
            
            return perms
    
    def _cleanup_expired_cache(self) -> int:
        """
        清理过期的权限缓存条目
        
        遍历所有缓存条目，删除已过期的记录。
        在 get_user_permissions 中定期自动调用。
        
        Returns:
            清理的过期条目数量
        """
        if not self._enable_cache:
            return 0
        
        expired_users = []
        now = datetime.now()
        
        for user_id, cache_time in list(self._cache_timestamp.items()):
            elapsed = (now - cache_time).total_seconds()
            if elapsed >= self._cache_ttl:
                expired_users.append(user_id)
        
        # 删除过期条目
        for user_id in expired_users:
            self._user_permissions.pop(user_id, None)
            self._cache_timestamp.pop(user_id, None)
        
        if expired_users:
            logger.debug(f"清理了 {len(expired_users)} 个过期权限缓存条目")
        
        return len(expired_users)
    
    def cleanup_expired_cache(self) -> int:
        """
        公共方法：手动清理过期的权限缓存
        
        供外部调用，用于强制清理过期缓存。
        
        Returns:
            清理的过期条目数量
        """
        with self._lock:
            return self._cleanup_expired_cache()
    
    def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource: Resource = None,
    ) -> bool:
        """
        检查用户是否拥有指定权限
        
        检查逻辑：
        1. 超级管理员拥有所有权限
        2. 检查用户是否拥有该权限
        3. 如果指定了资源，检查资源级别的访问控制
        """
        # 超级管理员拥有所有权限
        user_roles = self._user_roles.get(user_id, set())
        if self._super_admin_role in user_roles:
            return True
        
        # 获取用户权限
        user_perms = self.get_user_permissions(user_id)
        
        # 检查直接权限
        if permission in user_perms:
            # 如果指定了资源，检查资源级别权限
            if resource:
                return self._check_resource_access(user_id, permission, resource)
            return True
        
        return False
    
    def _check_resource_access(
        self,
        user_id: str,
        permission: Permission,
        resource: Resource,
    ) -> bool:
        """
        检查资源级别的访问控制
        
        资源访问规则：
        - 如果资源有所有者，只有所有者可以修改
        - 读取操作允许所有有权限的用户
        - 管理操作由角色层级决定
        - 如果资源所有者不存在（如用户已删除），视为无主资源按默认策略处理
        """
        # 如果资源没有所有者，允许访问
        if not resource.owner:
            return True
        
        # 检查资源所有者是否仍然存在（防止引用已删除用户）
        # 如果所有者不在用户角色系统中，视为无主资源
        if resource.owner not in self._user_roles:
            # 无主资源按默认策略处理：读取允许，写入需要管理权限
            if permission.value.startswith("read:"):
                return True
            # 写入/管理操作需要管理员权限
            if permission.value.startswith("write:") or permission.value.startswith("admin:"):
                user_perms = self.get_user_permissions(user_id)
                if Permission.ADMIN_SETTINGS in user_perms:
                    return True
                return False
            return True
        
        # 所有者拥有完全访问权限
        if resource.owner == user_id:
            return True
        
        # 非所有者的写入权限需要特殊检查
        if permission.value.startswith("write:") or permission.value.startswith("admin:"):
            # 检查用户是否有管理权限
            user_perms = self.get_user_permissions(user_id)
            if Permission.ADMIN_SETTINGS in user_perms:
                return True
            return False
        
        # 读取权限允许所有有权限的用户
        return True
    
    def _resolve_permissions(self, role_name: str) -> Set[Permission]:
        """
        解析角色的所有权限（包括继承的权限）
        
        递归解析权限继承链，避免循环继承。
        """
        if role_name not in self._role_permissions:
            return set()
        return self._role_permissions[role_name].copy()
    
    def _invalidate_user_cache(self):
        """清除所有用户权限缓存"""
        self._user_permissions.clear()
        self._cache_timestamp.clear()
    
    def require_permission(
        self,
        permission: Permission,
        resource: Resource = None,
    ) -> Callable:
        """
        权限检查依赖注入
        
        用于依赖注入场景，返回一个权限检查函数。
        """
        def checker(user_id: str = None) -> bool:
            if user_id is None:
                return False
            return self.check_permission(user_id, permission, resource)
        return checker
    
    # ==================== 批量操作 ====================
    
    def import_roles(self, roles: List[Dict[str, Any]]):
        """
        批量导入角色
        
        从字典列表导入角色定义，用于配置加载。
        """
        for role_data in roles:
            try:
                perms = {Permission(p) for p in role_data.get("permissions", []) if p}
                self.create_role(
                    name=role_data["name"],
                    description=role_data.get("description", ""),
                    permissions=perms,
                    inherits_from=role_data.get("inherits_from", []),
                    level=role_data.get("level", 0),
                )
            except ValueError as e:
                logger.warning(f"导入角色失败: {e}")
            except Exception as e:
                logger.error(f"导入角色异常: {e}")
    
    def export_roles(self) -> List[Dict[str, Any]]:
        """
        导出角色定义
        
        导出非默认角色，用于配置保存。
        """
        default_names = set(_build_default_roles().keys())
        return [
            {
                "name": r.name,
                "description": r.description,
                "permissions": [p.value for p in r.permissions],
                "inherits_from": r.inherits_from,
                "level": r.level,
            }
            for r in self._roles.values()
            if r.name not in default_names
        ]


# 全局权限管理器实例
permission_manager = PermissionManager()


# ==================== 权限检查装饰器 ====================

def require_permission(
    resource: Union[ResourceType, str],
    action: Union[Action, str],
):
    """
    权限检查装饰器
    
    用于保护需要特定权限的函数，自动检查调用者是否有权限。
    
    使用示例：
        @require_permission(ResourceType.TRIPLE, Action.CREATE)
        def create_triple(user_id: str, ...):
            ...
    
    参数：
        resource: 资源类型（ResourceType枚举或字符串）
        action: 操作类型（Action枚举或字符串）
    
    注意：
        被装饰的函数必须接受 user_id 参数，或者通过 kwargs 传递。
    """
    # 解析资源和操作
    if isinstance(resource, str):
        try:
            resource = ResourceType(resource)
        except ValueError:
            resource = ResourceType.TRIPLE  # 默认资源类型
    
    if isinstance(action, str):
        try:
            action = Action(action)
        except ValueError:
            action = Action.READ  # 默认操作类型
    
    # 根据资源和操作映射到权限
    permission = _map_resource_action_to_permission(resource, action)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 从 kwargs 中提取 user_id（支持多种常见命名）
            user_id = kwargs.get("user_id") or kwargs.get("user") or kwargs.get("uid")
            
            # 如果 kwargs 中没有，尝试从所有位置参数中查找字符串类型的 user_id
            if user_id is None:
                for arg in args:
                    if isinstance(arg, str) and arg and not arg.startswith("<"):
                        # 启发式判断：看起来像用户ID（非空字符串，不是对象表示）
                        user_id = arg
                        break
            
            # 尝试从函数签名中定位 user_id 参数
            if user_id is None and len(args) > 0:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if "user_id" in params:
                    idx = params.index("user_id")
                    if idx < len(args):
                        user_id = args[idx]
            
            # 当 user_id 为 None 时不应静默放行，记录 WARNING 并根据配置决定
            if user_id is None:
                config = get_config().permission
                logger.warning(
                    f"无法从参数中提取 user_id，权限检查被跳过。函数: {func.__name__}"
                )
                # 根据配置决定是拒绝还是放行（默认拒绝更安全）
                if getattr(config, "strict_mode", True):
                    if config.denial_action == "raise":
                        raise PermissionError(
                            f"无法识别用户身份，拒绝执行 {action.value} 操作于 {resource.value}"
                        )
                    return None
                # 非严格模式下放行（向后兼容）
                return func(*args, **kwargs)
            
            # 执行权限检查
            if not permission_manager.check_permission(user_id, permission):
                # 根据配置决定拒绝行为
                config = get_config().permission
                if config.denial_action == "raise":
                    raise PermissionError(
                        f"权限不足: 需要 {permission.value} 权限才能执行 {action.value} 操作于 {resource.value}"
                    )
                else:
                    logger.warning(
                        f"用户 {user_id} 权限不足: 需要 {permission.value}"
                    )
                    return None
            
            # 执行原函数
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 从 kwargs 中提取 user_id（支持多种常见命名）
            user_id = kwargs.get("user_id") or kwargs.get("user") or kwargs.get("uid")
            
            # 如果 kwargs 中没有，尝试从所有位置参数中查找字符串类型的 user_id
            if user_id is None:
                for arg in args:
                    if isinstance(arg, str) and arg and not arg.startswith("<"):
                        user_id = arg
                        break
            
            # 尝试从函数签名中定位 user_id 参数
            if user_id is None and len(args) > 0:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if "user_id" in params:
                    idx = params.index("user_id")
                    if idx < len(args):
                        user_id = args[idx]
            
            # 当 user_id 为 None 时不应静默放行，记录 WARNING 并根据配置决定
            if user_id is None:
                config = get_config().permission
                logger.warning(
                    f"无法从参数中提取 user_id，权限检查被跳过。函数: {func.__name__}"
                )
                # 根据配置决定是拒绝还是放行（默认拒绝更安全）
                if getattr(config, "strict_mode", True):
                    if config.denial_action == "raise":
                        raise PermissionError(
                            f"无法识别用户身份，拒绝执行 {action.value} 操作于 {resource.value}"
                        )
                    return None
                # 非严格模式下放行（向后兼容）
                return await func(*args, **kwargs)
            
            # 执行权限检查
            if not permission_manager.check_permission(user_id, permission):
                config = get_config().permission
                if config.denial_action == "raise":
                    raise PermissionError(
                        f"权限不足: 需要 {permission.value} 权限才能执行 {action.value} 操作于 {resource.value}"
                    )
                else:
                    logger.warning(
                        f"用户 {user_id} 权限不足: 需要 {permission.value}"
                    )
                    return None
            
            # 执行原函数
            return await func(*args, **kwargs)
        
        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def require_role(role_name: str):
    """
    角色检查装饰器
    
    检查用户是否拥有指定角色。
    
    使用示例：
        @require_role("admin")
        def admin_only_function(user_id: str, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id")
            if user_id:
                user_roles = permission_manager.get_user_roles(user_id)
                if role_name not in user_roles:
                    raise PermissionError(f"需要角色: {role_name}")
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id")
            if user_id:
                user_roles = permission_manager.get_user_roles(user_id)
                if role_name not in user_roles:
                    raise PermissionError(f"需要角色: {role_name}")
            return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def require_level(min_level: int):
    """
    角色层级检查装饰器
    
    检查用户的最高角色层级是否达到要求。
    
    使用示例：
        @require_level(50)  # 至少 editor 级别
        def editor_function(user_id: str, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id")
            if user_id:
                highest_role = permission_manager.get_user_highest_role(user_id)
                if highest_role:
                    level = permission_manager.get_role_level(highest_role)
                    if level < min_level:
                        raise PermissionError(
                            f"权限等级不足: 需要等级 {min_level}，当前等级 {level}"
                        )
                else:
                    raise PermissionError("用户未分配任何角色")
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id")
            if user_id:
                highest_role = permission_manager.get_user_highest_role(user_id)
                if highest_role:
                    level = permission_manager.get_role_level(highest_role)
                    if level < min_level:
                        raise PermissionError(
                            f"权限等级不足: 需要等级 {min_level}，当前等级 {level}"
                        )
                else:
                    raise PermissionError("用户未分配任何角色")
            return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def _map_resource_action_to_permission(
    resource: ResourceType,
    action: Action,
) -> Permission:
    """
    将资源类型和操作映射到具体权限
    
    这是权限系统的核心映射逻辑，定义了资源和操作的权限对应关系。
    """
    # 定义资源-操作到权限的映射
    # 格式：(ResourceType, Action) -> Permission
    mapping = {
        # Schema 权限
        (ResourceType.SCHEMA, Action.READ): Permission.READ_SCHEMA,
        (ResourceType.SCHEMA, Action.CREATE): Permission.WRITE_SCHEMA,
        (ResourceType.SCHEMA, Action.UPDATE): Permission.WRITE_SCHEMA,
        (ResourceType.SCHEMA, Action.DELETE): Permission.WRITE_SCHEMA,
        (ResourceType.SCHEMA, Action.ADMIN): Permission.ADMIN_SETTINGS,
        
        # Entity 权限
        (ResourceType.ENTITY, Action.READ): Permission.READ_ENTITIES,
        (ResourceType.ENTITY, Action.CREATE): Permission.WRITE_ENTITIES,
        (ResourceType.ENTITY, Action.UPDATE): Permission.WRITE_ENTITIES,
        (ResourceType.ENTITY, Action.DELETE): Permission.WRITE_ENTITIES,
        
        # Relationship 权限
        (ResourceType.RELATIONSHIP, Action.READ): Permission.READ_RELATIONSHIPS,
        (ResourceType.RELATIONSHIP, Action.CREATE): Permission.WRITE_RELATIONSHIPS,
        (ResourceType.RELATIONSHIP, Action.UPDATE): Permission.WRITE_RELATIONSHIPS,
        (ResourceType.RELATIONSHIP, Action.DELETE): Permission.WRITE_RELATIONSHIPS,
        
        # Triple 权限
        (ResourceType.TRIPLE, Action.READ): Permission.READ_TRIPLES,
        (ResourceType.TRIPLE, Action.CREATE): Permission.WRITE_TRIPLES,
        (ResourceType.TRIPLE, Action.UPDATE): Permission.WRITE_TRIPLES,
        (ResourceType.TRIPLE, Action.DELETE): Permission.WRITE_TRIPLES,
        
        # Inference 权限
        (ResourceType.INFERENCE, Action.READ): Permission.READ_INFERENCES,
        (ResourceType.INFERENCE, Action.CREATE): Permission.WRITE_INFERENCES,
        (ResourceType.INFERENCE, Action.EXECUTE): Permission.EXECUTE_REASONING,
        
        # Rule 权限
        (ResourceType.RULE, Action.READ): Permission.READ_SCHEMA,
        (ResourceType.RULE, Action.CREATE): Permission.WRITE_SCHEMA,
        
        # Agent 权限
        (ResourceType.AGENT, Action.READ): Permission.READ_STATS,
        (ResourceType.AGENT, Action.EXECUTE): Permission.EXECUTE_AGENT,
        (ResourceType.AGENT, Action.ADMIN): Permission.ADMIN_SETTINGS,
        
        # Tool 权限
        (ResourceType.TOOL, Action.READ): Permission.READ_STATS,
        (ResourceType.TOOL, Action.EXECUTE): Permission.EXECUTE_AGENT,
        
        # User 权限
        (ResourceType.USER, Action.READ): Permission.ADMIN_USERS,
        (ResourceType.USER, Action.CREATE): Permission.ADMIN_USERS,
        (ResourceType.USER, Action.UPDATE): Permission.ADMIN_USERS,
        (ResourceType.USER, Action.DELETE): Permission.ADMIN_USERS,
        
        # Role 权限
        (ResourceType.ROLE, Action.READ): Permission.ADMIN_ROLES,
        (ResourceType.ROLE, Action.CREATE): Permission.ADMIN_ROLES,
        (ResourceType.ROLE, Action.UPDATE): Permission.ADMIN_ROLES,
        (ResourceType.ROLE, Action.DELETE): Permission.ADMIN_ROLES,
        
        # Audit Log 权限
        (ResourceType.AUDIT_LOG, Action.READ): Permission.READ_AUDIT_LOG,
        (ResourceType.AUDIT_LOG, Action.ADMIN): Permission.ADMIN_SECURITY,
        
        # Export 权限
        (ResourceType.EXPORT, Action.CREATE): Permission.EXPORT_DATA,
        (ResourceType.EXPORT, Action.READ): Permission.READ_STATS,
        (ResourceType.EXPORT, Action.EXECUTE): Permission.EXPORT_DATA,
        
        # Metrics 权限
        (ResourceType.METRICS, Action.READ): Permission.READ_STATS,
        (ResourceType.METRICS, Action.ADMIN): Permission.ADMIN_SETTINGS,
        
        # Trace 权限
        (ResourceType.TRACE, Action.READ): Permission.READ_LINEAGE,
    }
    
    # 查找映射的权限
    permission = mapping.get((resource, action))
    
    # 如果没有找到精确映射，使用默认规则
    if permission is None:
        if action == Action.READ:
            permission = Permission.READ_STATS
        elif action in (Action.CREATE, Action.UPDATE, Action.DELETE):
            permission = Permission.WRITE_TRIPLES
        elif action == Action.EXECUTE:
            permission = Permission.EXECUTE_REASONING
        elif action == Action.ADMIN:
            permission = Permission.ADMIN_SETTINGS
        else:
            permission = Permission.READ_STATS
    
    return permission


# ==================== 便捷函数 ====================

def check_permission(user_id: str, permission: Permission) -> bool:
    """
    便捷函数：检查用户权限
    
    快速检查用户是否拥有指定权限。
    """
    return permission_manager.check_permission(user_id, permission)


def check_role(user_id: str, role_name: str) -> bool:
    """
    便捷函数：检查用户角色
    
    快速检查用户是否拥有指定角色。
    """
    return role_name in permission_manager.get_user_roles(user_id)


def assign_role(user_id: str, role_name: str) -> bool:
    """
    便捷函数：分配角色
    
    快速为用户分配角色。
    """
    return permission_manager.assign_role(user_id, role_name)


def get_user_permissions(user_id: str) -> Set[Permission]:
    """
    便捷函数：获取用户权限
    
    快速获取用户的所有权限。
    """
    return permission_manager.get_user_permissions(user_id)
