#!/usr/bin/env python3
"""
Create Admin User Script
Interactive script to create an admin user for the Battery RUL Monitoring System
"""
import asyncio
import sys
from pathlib import Path
import getpass
import re
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.user import User, UserRole
from src.core.config import settings
from src.core.security import get_password_hash


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    return True, ""


async def create_admin_user():
    """Create an admin user interactively"""

    print("=" * 80)
    print("BATTERY RUL PREDICTION - CREATE ADMIN USER")
    print("=" * 80)
    print()

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create async session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Prompt for user details
            print("Please enter admin user details:")
            print()

            # User ID
            while True:
                user_id = input("User ID (e.g., admin): ").strip()
                if not user_id:
                    print("❌ User ID cannot be empty")
                    continue
                if len(user_id) < 3:
                    print("❌ User ID must be at least 3 characters")
                    continue

                # Check if user already exists
                result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    print(f"❌ User ID '{user_id}' already exists")
                    continue

                break

            # Username
            while True:
                username = input("Username (e.g., admin): ").strip()
                if not username:
                    print("❌ Username cannot be empty")
                    continue
                if len(username) < 3:
                    print("❌ Username must be at least 3 characters")
                    continue

                # Check if username already exists
                result = await session.execute(
                    select(User).where(User.username == username)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    print(f"❌ Username '{username}' already exists")
                    continue

                break

            # Email
            while True:
                email = input("Email (e.g., admin@example.com): ").strip()
                if not email:
                    print("❌ Email cannot be empty")
                    continue
                if not validate_email(email):
                    print("❌ Invalid email format")
                    continue
                break

            # Full name
            full_name = input("Full Name (e.g., System Administrator): ").strip()
            if not full_name:
                full_name = "Administrator"

            # Password
            while True:
                password = getpass.getpass("Password (min 8 chars, uppercase, lowercase, digit): ")
                if not password:
                    print("❌ Password cannot be empty")
                    continue

                is_valid, error_msg = validate_password(password)
                if not is_valid:
                    print(f"❌ {error_msg}")
                    continue

                password_confirm = getpass.getpass("Confirm password: ")
                if password != password_confirm:
                    print("❌ Passwords do not match")
                    continue

                break

            print()
            print("Creating admin user...")

            # Create user
            admin_user = User(
                user_id=user_id,
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True,
            )

            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            print()
            print("=" * 80)
            print("✅ ADMIN USER CREATED SUCCESSFULLY!")
            print("=" * 80)
            print(f"User ID:    {admin_user.user_id}")
            print(f"Username:   {admin_user.username}")
            print(f"Email:      {admin_user.email}")
            print(f"Full Name:  {admin_user.full_name}")
            print(f"Role:       {admin_user.role.value}")
            print(f"Active:     {admin_user.is_active}")
            print()
            print("You can now login with:")
            print(f"  Username: {admin_user.username}")
            print(f"  Password: <your-password>")
            print()
            print("Next steps:")
            print("  1. Start backend: uvicorn src.main:app_with_sockets --reload")
            print("  2. Test login: POST http://localhost:8000/api/v1/auth/login")
            print("  3. Access Swagger UI: http://localhost:8000/api/docs")
            print()

        except Exception as e:
            print(f"\n❌ Error creating admin user: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise

        finally:
            await engine.dispose()


async def quick_create_admin(user_id: str, username: str, email: str, password: str, full_name: str):
    """
    Quick create admin user (non-interactive)

    Args:
        user_id: User identifier
        username: Username
        email: Email address
        password: Password (plain text)
        full_name: Full name
    """
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Check if user already exists
            result = await session.execute(
                select(User).where(
                    (User.user_id == user_id) | (User.username == username)
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"❌ User already exists: {existing.user_id}")
                return

            # Create user
            admin_user = User(
                user_id=user_id,
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True,
            )

            session.add(admin_user)
            await session.commit()

            print(f"✅ Admin user created: {username}")

        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--user-id", help="User ID (non-interactive)")
    parser.add_argument("--username", help="Username (non-interactive)")
    parser.add_argument("--email", help="Email (non-interactive)")
    parser.add_argument("--password", help="Password (non-interactive)")
    parser.add_argument("--full-name", help="Full name (non-interactive)")

    args = parser.parse_args()

    if args.user_id and args.username and args.email and args.password:
        # Non-interactive mode
        full_name = args.full_name or "Administrator"
        asyncio.run(quick_create_admin(
            args.user_id,
            args.username,
            args.email,
            args.password,
            full_name
        ))
    else:
        # Interactive mode
        asyncio.run(create_admin_user())
