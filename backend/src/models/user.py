"""
User Model
User authentication and authorization
"""
import uuid
from typing import Optional
from datetime import datetime
import enum
from sqlalchemy import String, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from . import Base, UUIDMixin, TimestampMixin


class UserRole(str, enum.Enum):
    """User role enum"""
    ADMIN = "admin"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin):
    """
    System user with role-based access control

    Attributes:
        user_id: Human-readable user identifier (e.g., john.doe)
        username: Login username
        email: User email address
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        role: User role (admin, engineer, viewer)
        is_active: Account status
    """
    __tablename__ = "user"

    user_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="User identifier (john.doe)"
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Login username"
    )

    email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Email address"
    )

    hashed_password: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Bcrypt hashed password"
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User's full name"
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        nullable=False,
        default=UserRole.VIEWER,
        comment="User role: admin, engineer, viewer"
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="Account active status"
    )

    # Optional: Track last login
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Last login timestamp"
    )

    def __repr__(self) -> str:
        return f"<User(user_id='{self.user_id}', username='{self.username}', role='{self.role}')>"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN

    @property
    def is_engineer(self) -> bool:
        """Check if user has engineer role"""
        return self.role == UserRole.ENGINEER

    @property
    def can_write(self) -> bool:
        """Check if user has write permissions"""
        return self.role in (UserRole.ADMIN, UserRole.ENGINEER)
