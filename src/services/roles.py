from fastapi import Depends, HTTPException, status
from src.database.models import User, Role
from src.services.auth import auth_service


class RoleChecker:
    """Dependency class for role-based access control.

    The class receives a list of allowed roles and checks whether the current
    authenticated user has one of these roles. If the user's role is not allowed,
    the dependency raises a 403 Forbidden error.

    :param allowed_roles: List of roles that are allowed to access the route.
    """

    def __init__(self, allowed_roles: list[Role]):
        """Store allowed roles for a protected route.

        :param allowed_roles: Roles that can access the endpoint.
        """
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(auth_service.get_current_user)):
        """Validate the current user's role.

        :param current_user: User resolved from the JWT token.
        :raises HTTPException: If the user does not have the required role.
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation forbidden: insufficient permissions"
            )
