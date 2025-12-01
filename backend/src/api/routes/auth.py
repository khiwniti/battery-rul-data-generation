"""
Authentication API Routes
Endpoints for user authentication and token management
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.database import get_db
from ...core.logging import logger
from ...core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from ...core.config import settings
from ...api.dependencies import get_current_active_user, require_admin
from ...models.user import User, UserRole
from ...schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserInfo,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserListResponse,
)

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    User login with username and password

    Args:
        request: Login credentials

    Returns:
        Access token, refresh token, and user information

    Raises:
        401: Invalid credentials or inactive user
    """
    logger.info("Login attempt", username=request.username)

    # Query user by username
    result = await db.execute(
        select(User).where(User.username == request.username)
    )
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(request.password, user.hashed_password):
        logger.warning("Login failed: Invalid credentials", username=request.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Check if user is active
    if not user.is_active:
        logger.warning("Login failed: User inactive", username=request.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_id, "role": user.role.value},
        expires_delta=access_token_expires,
    )

    # Create refresh token
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.user_id},
        expires_delta=refresh_token_expires,
    )

    logger.info(
        "Login successful",
        username=user.username,
        user_id=user.user_id,
        role=user.role.value,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
        ),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token

    Args:
        request: Refresh token

    Returns:
        New access token

    Raises:
        401: Invalid refresh token
    """
    # Verify refresh token
    user_id = verify_token(request.refresh_token)

    if not user_id:
        logger.warning("Refresh token invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Get user
    result = await db.execute(
        select(User).where(User.user_id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Refresh token: User not found or inactive", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_id, "role": user.role.value},
        expires_delta=access_token_expires,
    )

    logger.info("Access token refreshed", user_id=user.user_id)

    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
):
    """
    User logout

    Note: Since we use JWT tokens, logout is handled client-side
    by deleting the tokens. This endpoint is for logging purposes.

    Returns:
        Success message
    """
    logger.info("User logged out", user_id=current_user.user_id)

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user information

    Returns:
        Current user details
    """
    return UserResponse(**current_user.__dict__)


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user's password

    Args:
        request: Current and new password

    Returns:
        Success message

    Raises:
        401: Incorrect current password
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        logger.warning(
            "Password change failed: Incorrect current password",
            user_id=current_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password",
        )

    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    await db.commit()

    logger.info("Password changed successfully", user_id=current_user.user_id)

    return {"message": "Password changed successfully"}


# Admin-only user management endpoints

@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users (Admin only)

    Args:
        skip: Pagination offset
        limit: Maximum results

    Returns:
        List of users
    """
    logger.info("Listing users", admin_user=current_user.username)

    # Query users
    result = await db.execute(
        select(User)
        .order_by(User.username)
        .offset(skip)
        .limit(min(limit, 1000))
    )
    users = result.scalars().all()

    return UserListResponse(
        users=[UserResponse(**user.__dict__) for user in users],
        total=len(users),
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create new user (Admin only)

    Args:
        request: User creation data

    Returns:
        Created user

    Raises:
        400: User already exists
        400: Invalid role
    """
    logger.info(
        "Creating user",
        admin_user=current_user.username,
        new_username=request.username,
    )

    # Check if user already exists
    result = await db.execute(
        select(User).where(
            (User.user_id == request.user_id) | (User.username == request.username)
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this user_id or username already exists",
        )

    # Validate role
    try:
        role_enum = UserRole(request.role.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {request.role}. Must be one of: admin, engineer, viewer",
        )

    # Create user
    new_user = User(
        user_id=request.user_id,
        username=request.username,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        role=role_enum,
        is_active=True,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info(
        "User created successfully",
        admin_user=current_user.username,
        new_user_id=new_user.user_id,
        role=new_user.role.value,
    )

    return UserResponse(**new_user.__dict__)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user by ID (Admin only)

    Args:
        user_id: User identifier

    Returns:
        User details

    Raises:
        404: User not found
    """
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    return UserResponse(**user.__dict__)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user (Admin only)

    Args:
        user_id: User identifier
        request: Update data

    Returns:
        Updated user

    Raises:
        404: User not found
        400: Invalid role
    """
    logger.info(
        "Updating user",
        admin_user=current_user.username,
        target_user_id=user_id,
    )

    # Get user
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    # Update fields
    if request.email is not None:
        user.email = request.email

    if request.full_name is not None:
        user.full_name = request.full_name

    if request.role is not None:
        try:
            user.role = UserRole(request.role.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request.role}",
            )

    if request.is_active is not None:
        user.is_active = request.is_active

    await db.commit()
    await db.refresh(user)

    logger.info("User updated successfully", target_user_id=user_id)

    return UserResponse(**user.__dict__)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete user (Admin only)

    Args:
        user_id: User identifier

    Returns:
        Success message

    Raises:
        404: User not found
        400: Cannot delete self
    """
    logger.info(
        "Deleting user",
        admin_user=current_user.username,
        target_user_id=user_id,
    )

    # Prevent self-deletion
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Get user
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    # Delete user
    await db.delete(user)
    await db.commit()

    logger.info("User deleted successfully", target_user_id=user_id)

    return {"message": f"User {user_id} deleted successfully"}
