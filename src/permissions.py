"""
Permission Management Module
Provides fine-grained role-based access control (RBAC)

v1.0.0 - Initial version
- Role management
- Permission definitions
- Resource access control
- User-role mapping
"""

import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


# ==================== Permission Definitions ====================

class Permission(Enum):
    """System permissions"""
    # Read permissions
    READ_SCHEMA = "read:schema"
    READ_ENTITIES = "read:entities"
    READ_RELATIONSHIPS = "read:relationships"
    READ_TRIPLES = "read:triples"
    READ_INFERENCES = "read:inferences"
    READ_STATS = "read:stats"
    
    # Write permissions
    WRITE_SCHEMA = "write:schema"
    WRITE_ENTITIES = "write:entities"
    WRITE_RELATIONSHIPS = "write:relationships"
    WRITE_TRIPLES = "write:triples"
    WRITE_INFERENCES = "write:inferences"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_ROLES = "admin:roles"
    ADMIN_API_KEYS = "admin:api_keys"
    ADMIN_EXPORT = "admin:export"
    ADMIN_SETTINGS = "admin:settings"
    
    # Special permissions
    EXECUTE_REASONING = "execute:reasoning"
    EXPORT_DATA = "export:data"
    VIEW_AUDIT_LOG = "audit:view"


class ResourceType(Enum):
    """Resource types"""
    SCHEMA = "schema"
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    TRIPLE = "triple"
    INFERENCE = "inference"
    API_KEY = "api_key"
    USER = "user"
    ROLE = "role"
    EXPORT = "export"


@dataclass
class Resource:
    """Resource definition"""
    type: ResourceType
    id: str
    owner: str
    attributes: Dict = field(default_factory=dict)


@dataclass
class AccessRule:
    """Access control rule"""
    permission: Permission
    resource_type: ResourceType
    resource_id: Optional[str] = None
    owner_only: bool = False


# ==================== Role Definitions ====================

@dataclass
class Role:
    """Role definition"""
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    inherits_from: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has permission"""
        return permission in self.permissions


# Default roles
DEFAULT_ROLES = {
    "admin": Role(
        name="admin",
        description="Full system access",
        permissions={
            Permission.READ_SCHEMA, Permission.READ_ENTITIES,
            Permission.READ_RELATIONSHIPS, Permission.READ_TRIPLES,
            Permission.READ_INFERENCES, Permission.READ_STATS,
            Permission.WRITE_SCHEMA, Permission.WRITE_ENTITIES,
            Permission.WRITE_RELATIONSHIPS, Permission.WRITE_TRIPLES,
            Permission.WRITE_INFERENCES,
            Permission.ADMIN_USERS, Permission.ADMIN_ROLES,
            Permission.ADMIN_API_KEYS, Permission.ADMIN_EXPORT,
            Permission.ADMIN_SETTINGS,
            Permission.EXECUTE_REASONING, Permission.EXPORT_DATA,
            Permission.VIEW_AUDIT_LOG
        }
    ),
    "editor": Role(
        name="editor",
        description="Can read and write ontology data",
        permissions={
            Permission.READ_SCHEMA, Permission.READ_ENTITIES,
            Permission.READ_RELATIONSHIPS, Permission.READ_TRIPLES,
            Permission.READ_INFERENCES, Permission.READ_STATS,
            Permission.WRITE_SCHEMA, Permission.WRITE_ENTITIES,
            Permission.WRITE_RELATIONSHIPS, Permission.WRITE_TRIPLES,
            Permission.WRITE_INFERENCES,
            Permission.EXECUTE_REASONING
        }
    ),
    "viewer": Role(
        name="viewer",
        description="Read-only access",
        permissions={
            Permission.READ_SCHEMA, Permission.READ_ENTITIES,
            Permission.READ_RELATIONSHIPS, Permission.READ_TRIPLES,
            Permission.READ_INFERENCES, Permission.READ_STATS
        }
    ),
    "api_user": Role(
        name="api_user",
        description="API programmatic access",
        permissions={
            Permission.READ_SCHEMA, Permission.READ_ENTITIES,
            Permission.READ_RELATIONSHIPS, Permission.READ_TRIPLES,
            Permission.READ_INFERENCES, Permission.EXECUTE_REASONING
        }
    ),
    "export_user": Role(
        name="export_user",
        description="Can export data",
        permissions={
            Permission.READ_SCHEMA, Permission.READ_ENTITIES,
            Permission.READ_RELATIONSHIPS, Permission.READ_TRIPLES,
            Permission.EXPORT_DATA
        }
    )
}


# ==================== Permission Manager ====================

class PermissionManager:
    """Manages roles, permissions, and access control"""
    
    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._user_roles: Dict[str, Set[str]] = {}  # user_id -> set of role names
        self._user_permissions: Dict[str, Set[Permission]] = {}  # cached user permissions
        self._role_permissions: Dict[str, Set[Permission]] = {}  # cached role permissions
        self._lock = Lock()
        
        # Initialize default roles
        for name, role in DEFAULT_ROLES.items():
            self._roles[name] = role
            self._role_permissions[name] = role.permissions.copy()
        
        logger.info(f"Initialized PermissionManager with {len(self._roles)} default roles")
    
    # ==================== Role Management ====================
    
    def create_role(
        self,
        name: str,
        description: str,
        permissions: Set[Permission] = None,
        inherits_from: List[str] = None
    ) -> Role:
        """Create a new role"""
        with self._lock:
            if name in self._roles:
                raise ValueError(f"Role already exists: {name}")
            
            role = Role(
                name=name,
                description=description,
                permissions=permissions or set(),
                inherits_from=inherits_from or []
            )
            
            # Resolve inherited permissions
            all_perms = set(permissions or [])
            for parent_name in role.inherits_from:
                if parent_name in self._roles:
                    all_perms.update(self._resolve_permissions(parent_name))
            
            role.permissions = all_perms
            self._roles[name] = role
            self._role_permissions[name] = all_perms
            
            # Clear user permission cache
            self._user_permissions.clear()
            
            logger.info(f"Created role: {name}")
            return role
    
    def update_role(
        self,
        name: str,
        description: str = None,
        permissions: Set[Permission] = None,
        inherits_from: List[str] = None
    ) -> Role:
        """Update an existing role"""
        with self._lock:
            if name not in self._roles:
                raise ValueError(f"Role not found: {name}")
            
            role = self._roles[name]
            
            if description:
                role.description = description
            if permissions:
                role.permissions = permissions
            if inherits_from:
                role.inherits_from = inherits_from
            
            # Recalculate permissions
            all_perms = set(permissions or role.permissions)
            for parent_name in role.inherits_from:
                if parent_name in self._roles:
                    all_perms.update(self._resolve_permissions(parent_name))
            
            role.permissions = all_perms
            role.updated_at = datetime.now()
            self._role_permissions[name] = all_perms
            
            # Clear user permission cache
            self._user_permissions.clear()
            
            logger.info(f"Updated role: {name}")
            return role
    
    def delete_role(self, name: str) -> bool:
        """Delete a role"""
        with self._lock:
            if name not in self._roles:
                return False
            
            # Don't allow deleting default roles
            if name in DEFAULT_ROLES:
                raise ValueError(f"Cannot delete default role: {name}")
            
            # Remove role from all users
            for user_id in self._user_roles:
                self._user_roles[user_id].discard(name)
            
            del self._roles[name]
            self._role_permissions.pop(name, None)
            
            # Clear user permission cache
            self._user_permissions.clear()
            
            logger.info(f"Deleted role: {name}")
            return True
    
    def get_role(self, name: str) -> Optional[Role]:
        """Get a role by name"""
        return self._roles.get(name)
    
    def list_roles(self) -> List[Dict]:
        """List all roles"""
        with self._lock:
            return [
                {
                    "name": r.name,
                    "description": r.description,
                    "permissions": [p.value for p in r.permissions],
                    "inherits_from": r.inherits_from,
                    "created_at": r.created_at.isoformat(),
                    "updated_at": r.updated_at.isoformat()
                }
                for r in self._roles.values()
            ]
    
    # ==================== User-Role Management ====================
    
    def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign a role to a user"""
        with self._lock:
            if role_name not in self._roles:
                raise ValueError(f"Role not found: {role_name}")
            
            if user_id not in self._user_roles:
                self._user_roles[user_id] = set()
            
            self._user_roles[user_id].add(role_name)
            
            # Clear user permission cache
            self._user_permissions.pop(user_id, None)
            
            logger.info(f"Assigned role {role_name} to user {user_id}")
            return True
    
    def remove_role(self, user_id: str, role_name: str) -> bool:
        """Remove a role from a user"""
        with self._lock:
            if user_id in self._user_roles:
                self._user_roles[user_id].discard(role_name)
                self._user_permissions.pop(user_id, None)
                logger.info(f"Removed role {role_name} from user {user_id}")
                return True
            return False
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """Get all roles for a user"""
        with self._lock:
            return list(self._user_roles.get(user_id, set()))
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user"""
        with self._lock:
            if user_id in self._user_permissions:
                return self._user_permissions[user_id].copy()
            
            # Calculate permissions
            perms = set()
            roles = self._user_roles.get(user_id, set())
            
            for role_name in roles:
                if role_name in self._role_permissions:
                    perms.update(self._role_permissions[role_name])
            
            self._user_permissions[user_id] = perms
            return perms.copy()
    
    def _resolve_permissions(self, role_name: str) -> Set[Permission]:
        """Resolve all permissions for a role (including inherited)"""
        if role_name not in self._role_permissions:
            return set()
        
        return self._role_permissions[role_name].copy()
    
    # ==================== Access Control ====================
    
    def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource: Resource = None
    ) -> bool:
        """Check if user has permission"""
        # Admin bypass
        admin_perms = self.get_user_permissions("admin")
        if Permission.ADMIN_SETTINGS in admin_perms:
            return True
        
        user_perms = self.get_user_permissions(user_id)
        
        # Check direct permission
        if permission in user_perms:
            # Check resource ownership if needed
            if resource and resource.owner and resource.owner != user_id:
                # Check if owner-only restriction exists
                return False
            return True
        
        return False
    
    def require_permission(
        self,
        permission: Permission,
        resource: Resource = None
    ):
        """Dependency for requiring permission"""
        def checker(user_id: str = None) -> bool:
            return self.check_permission(user_id, permission, resource)
        return checker
    
    # ==================== Bulk Operations ====================
    
    def import_roles(self, roles: List[Dict]):
        """Import roles from dict list"""
        for role_data in roles:
            try:
                perms = {Permission(p) for p in role_data.get("permissions", [])}
                self.create_role(
                    name=role_data["name"],
                    description=role_data.get("description", ""),
                    permissions=perms,
                    inherits_from=role_data.get("inherits_from", [])
                )
            except Exception as e:
                logger.warning(f"Failed to import role: {e}")
    
    def export_roles(self) -> List[Dict]:
        """Export roles to dict list"""
        return [
            {
                "name": r.name,
                "description": r.description,
                "permissions": [p.value for p in r.permissions],
                "inherits_from": r.inherits_from
            }
            for r in self._roles.values()
            if r.name not in DEFAULT_ROLES
        ]


# Global permission manager
permission_manager = PermissionManager()


# ==================== Decorators ====================

def require_permission(permission: Permission):
    """Decorator to require permission for a function"""
    def decorator(func):
        def sync_wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id")
            if user_id and not permission_manager.check_permission(user_id, permission):
                raise PermissionError(f"Permission denied: {permission.value}")
            return func(*args, **kwargs)
        
        async def async_wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id")
            if user_id and not permission_manager.check_permission(user_id, permission):
                raise PermissionError(f"Permission denied: {permission.value}")
            return await func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def require_role(role_name: str):
    """Decorator to require role for a function"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id")
            if user_id:
                user_roles = permission_manager.get_user_roles(user_id)
                if role_name not in user_roles:
                    raise PermissionError(f"Role required: {role_name}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
