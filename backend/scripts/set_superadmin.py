#!/usr/bin/env python3
"""
Script to set a user as super admin.
Usage: python scripts/set_superadmin.py user@example.com
"""
import sys
import asyncio
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import select
from app.core.database import AsyncSessionLocal
from app.models.models import User


async def set_super_admin(email: str):
    """Promote user to super admin by email"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ Error: User with email '{email}' not found")
            return False

        if user.is_super_admin:
            print(f"ℹ️  User '{email}' is already a super admin")
            return True

        user.is_super_admin = True
        await session.commit()

        print(f"✅ Success: User '{email}' ({user.full_name}) has been promoted to super admin")
        print(f"   User ID: {user.id}")
        print(f"   Name: {user.full_name}")
        print(f"   Super Admin: {user.is_super_admin}")
        return True


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/set_superadmin.py user@example.com")
        print("\nThis script promotes a user to super admin.")
        sys.exit(1)

    email = sys.argv[1]

    if "@" not in email:
        print(f"❌ Error: Invalid email format: '{email}'")
        sys.exit(1)

    if not os.getenv("DATABASE_URL"):
        print("⚠️  Warning: DATABASE_URL environment variable not set")
        print("   Using default: postgresql+asyncpg://localhost/badminton")

    success = asyncio.run(set_super_admin(email))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
