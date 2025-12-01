"""
Quick Admin User Creation Script (Non-Interactive)
Creates an admin user with predefined credentials
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.core.config import settings
from src.core.security import get_password_hash
from src.models.user import User, UserRole


async def create_admin():
    """Create admin user with predefined credentials"""

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Check if admin already exists
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.username == "admin"))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("❌ Admin user already exists!")
                return False

            # Create admin user
            admin_user = User(
                user_id="admin",
                username="admin",
                email="admin@battery-rul.com",
                hashed_password=get_password_hash("Admin123!"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )

            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            print("\n" + "=" * 80)
            print("✅ ADMIN USER CREATED SUCCESSFULLY!")
            print("=" * 80)
            print(f"\nUser ID:  {admin_user.user_id}")
            print(f"Username: {admin_user.username}")
            print(f"Email:    {admin_user.email}")
            print(f"Role:     {admin_user.role.value}")
            print(f"\n🔐 Password: Admin123!")
            print("\n⚠️  IMPORTANT: Change this password after first login!")
            print("=" * 80)

            return True

    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(create_admin())
    sys.exit(0 if success else 1)
