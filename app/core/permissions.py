"""
Role-based access control and permissions management.
"""

from enum import Enum
from typing import Optional, Set, List
import logging

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """Available user roles."""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SYSTEM = "system"

    @property
    def permissions(self) -> Set["Permission"]:
        return ROLE_PERMISSIONS.get(self, set())


class Permission(str, Enum):
    """Available permissions."""
    # Dispute permissions
    CREATE_DISPUTE = "create_dispute"
    READ_DISPUTE = "read_dispute"
    UPDATE_DISPUTE = "update_dispute"
    DELETE_DISPUTE = "delete_dispute"
    
    # SLA permissions
    VIEW_SLA = "view_sla"
    MANAGE_SLA = "manage_sla"
    
    # Routing permissions
    VIEW_ROUTING = "view_routing"
    MANAGE_ROUTING = "manage_routing"
    
    # Confluence permissions
    PUBLISH_CONFLUENCE = "publish_confluence"
    VIEW_CONFLUENCE = "view_confluence"
    
    # System permissions
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_SYSTEM = "manage_system"
    MANAGE_ROLES = "manage_roles"
    
    # API permissions
    ACCESS_API = "access_api"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # All permissions for admin
        Permission.CREATE_DISPUTE,
        Permission.READ_DISPUTE,
        Permission.UPDATE_DISPUTE,
        Permission.DELETE_DISPUTE,
        Permission.VIEW_SLA,
        Permission.MANAGE_SLA,
        Permission.VIEW_ROUTING,
        Permission.MANAGE_ROUTING,
        Permission.PUBLISH_CONFLUENCE,
        Permission.VIEW_CONFLUENCE,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOG,
        Permission.MANAGE_SYSTEM,
        Permission.MANAGE_ROLES,
        Permission.ACCESS_API,
    },
    Role.MANAGER: {
        Permission.CREATE_DISPUTE,
        Permission.READ_DISPUTE,
        Permission.UPDATE_DISPUTE,
        Permission.VIEW_SLA,
        Permission.MANAGE_SLA,
        Permission.VIEW_ROUTING,
        Permission.MANAGE_ROUTING,
        Permission.PUBLISH_CONFLUENCE,
        Permission.VIEW_CONFLUENCE,
        Permission.VIEW_AUDIT_LOG,
        Permission.ACCESS_API,
    },
    Role.ANALYST: {
        Permission.CREATE_DISPUTE,
        Permission.READ_DISPUTE,
        Permission.UPDATE_DISPUTE,
        Permission.VIEW_SLA,
        Permission.VIEW_ROUTING,
        Permission.VIEW_CONFLUENCE,
        Permission.ACCESS_API,
    },
    Role.VIEWER: {
        Permission.READ_DISPUTE,
        Permission.VIEW_SLA,
        Permission.VIEW_ROUTING,
        Permission.VIEW_CONFLUENCE,
        Permission.ACCESS_API,
    },
    Role.SYSTEM: {
        # System role has all permissions for automated tasks
        Permission.CREATE_DISPUTE,
        Permission.READ_DISPUTE,
        Permission.UPDATE_DISPUTE,
        Permission.DELETE_DISPUTE,
        Permission.VIEW_SLA,
        Permission.MANAGE_SLA,
        Permission.VIEW_ROUTING,
        Permission.MANAGE_ROUTING,
        Permission.PUBLISH_CONFLUENCE,
        Permission.VIEW_CONFLUENCE,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOG,
        Permission.MANAGE_SYSTEM,
        Permission.ACCESS_API,
    },
}


class PermissionChecker:
    """Check user permissions based on roles."""
    
    @staticmethod
    def get_permissions_for_role(role: Role) -> Set[Permission]:
        """
        Get all permissions for a role.
        
        Args:
            role: User role
            
        Returns:
            Set of permissions
        """
        return ROLE_PERMISSIONS.get(role, set())
    
    @staticmethod
    def get_permissions_for_roles(roles: List[str]) -> Set[Permission]:
        """
        Get all permissions for a list of roles.
        
        Args:
            roles: List of role names
            
        Returns:
            Combined set of permissions
        """
        permissions = set()
        for role_name in roles:
            try:
                role = Role(role_name)
                permissions.update(PermissionChecker.get_permissions_for_role(role))
            except ValueError:
                logger.warning(f"Unknown role: {role_name}")
        
        return permissions
    
    @staticmethod
    def has_permission(
        roles: List[str] | Permission,
        required_permission: Optional[Permission] = None,
    ) -> bool:
        """
        Check if user with given roles has a permission.
        
        Args:
            roles: List of role names
            required_permission: Required permission
            
        Returns:
            True if user has permission
        """
        if required_permission is None:
            return isinstance(roles, Permission)

        role_list: List[str]
        if isinstance(roles, Permission):
            role_list = []
        elif isinstance(roles, list):
            role_list = roles
        else:
            role_list = [str(roles)]

        permissions = PermissionChecker.get_permissions_for_roles(role_list)
        return required_permission in permissions

    @staticmethod
    def has_role(role: Role | str) -> bool:
        try:
            Role(str(role))
            return True
        except ValueError:
            return False
    
    @staticmethod
    def has_any_permission(
        roles: List[str],
        required_permissions: List[Permission]
    ) -> bool:
        """
        Check if user has any of the required permissions.
        
        Args:
            roles: List of role names
            required_permissions: List of permissions
            
        Returns:
            True if user has at least one permission
        """
        permissions = PermissionChecker.get_permissions_for_roles(roles)
        return any(perm in permissions for perm in required_permissions)
    
    @staticmethod
    def has_all_permissions(
        roles: List[str],
        required_permissions: List[Permission]
    ) -> bool:
        """
        Check if user has all required permissions.
        
        Args:
            roles: List of role names
            required_permissions: List of permissions
            
        Returns:
            True if user has all permissions
        """
        permissions = PermissionChecker.get_permissions_for_roles(roles)
        return all(perm in permissions for perm in required_permissions)
    
    @staticmethod
    def get_role_hierarchy() -> dict[Role, int]:
        """
        Get role hierarchy (higher number = more privileged).
        
        Returns:
            Dictionary mapping roles to their hierarchy level
        """
        return {
            Role.VIEWER: 1,
            Role.ANALYST: 2,
            Role.MANAGER: 3,
            Role.ADMIN: 4,
            Role.SYSTEM: 5,
        }
    
    @staticmethod
    def get_highest_role(roles: List[str]) -> Optional[Role]:
        """
        Get the highest privileged role from a list.
        
        Args:
            roles: List of role names
            
        Returns:
            Highest role or None
        """
        hierarchy = PermissionChecker.get_role_hierarchy()
        highest_role = None
        highest_level = 0
        
        for role_name in roles:
            try:
                role = Role(role_name)
                level = hierarchy.get(role, 0)
                if level > highest_level:
                    highest_level = level
                    highest_role = role
            except ValueError:
                logger.warning(f"Unknown role: {role_name}")
        
        return highest_role


class ResourceOwnershipChecker:
    """Check resource ownership for fine-grained access control."""
    
    @staticmethod
    def can_edit_resource(
        user_id: str,
        resource_owner_id: str,
        roles: List[str]
    ) -> bool:
        """
        Check if user can edit a resource.
        
        Args:
            user_id: User ID
            resource_owner_id: Resource owner ID
            roles: User roles
            
        Returns:
            True if user can edit resource
        """
        # Admin and manager can edit any resource
        if PermissionChecker.has_permission(roles, Permission.MANAGE_ROUTING):
            return True
        
        # User can edit their own resource
        if user_id == resource_owner_id:
            return True
        
        return False
    
    @staticmethod
    def can_delete_resource(
        user_id: str,
        resource_owner_id: str,
        roles: List[str]
    ) -> bool:
        """
        Check if user can delete a resource.
        
        Args:
            user_id: User ID
            resource_owner_id: Resource owner ID
            roles: User roles
            
        Returns:
            True if user can delete resource
        """
        # Only admin can delete resources
        if PermissionChecker.has_permission(roles, Permission.DELETE_DISPUTE):
            return True
        
        return False


# Backward-compatible aliases for older role/permission naming.
Role.USER = Role.VIEWER
Role.GUEST = Role.VIEWER
Permission.READ = Permission.READ_DISPUTE
