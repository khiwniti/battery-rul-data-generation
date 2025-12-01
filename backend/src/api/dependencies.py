"""
FastAPI Dependencies
Dependency injection for database sessions, authentication, etc.
"""
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.security import verify_token
from ..models.user import User, UserRole


# HTTP Bearer token security
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User model instance

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Verify token and extract user_id
    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.user_id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Require admin role

    Args:
        current_user: Current active user

    Returns:
        User with admin role

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_engineer_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Require engineer or admin role (write permissions)

    Args:
        current_user: Current active user

    Returns:
        User with engineer or admin role

    Raises:
        HTTPException: If user doesn't have write permissions
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.ENGINEER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer or Admin access required"
        )
    return current_user


# Optional authentication (allows public access but provides user if authenticated)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if token provided, otherwise None

    Useful for endpoints that have optional authentication

    Args:
        credentials: Optional HTTP Bearer token
        db: Database session

    Returns:
        User if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# Example usage in routes:
# @router.get("/profile")
# async def get_profile(
#     current_user: User = Depends(get_current_active_user)
# ):
#     return current_user
#
# @router.post("/admin-only")
# async def admin_endpoint(
#     current_user: User = Depends(require_admin)
# ):
#     return {"message": "Admin access granted"}
#
# @router.get("/public-or-private")
# async def optional_auth(
#     current_user: Optional[User] = Depends(get_current_user_optional)
# ):
#     if current_user:
#         return {"message": f"Hello {current_user.username}"}
#     return {"message": "Hello guest"}
