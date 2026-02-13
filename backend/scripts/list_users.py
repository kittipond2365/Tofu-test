"""
List all users to find LINE ID for super admin setup
Usage: python list_users.py
"""
import asyncio
from sqlmodel import select

from app.core.database import AsyncSessionLocal
from app.models.models import User


async def list_users():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        if not users:
            print("❌ No users found in database")
            return

        print("\n" + "=" * 100)
        print(f"{'ID':<38} {'Display Name':<20} {'LINE ID':<30} {'Super Admin':<12}")
        print("=" * 100)

        for user in users:
            super_admin = "✅ YES" if user.is_super_admin else "❌ NO"
            line_id = (user.line_user_id or "")
            line_id = line_id[:27] + "..." if len(line_id) > 30 else line_id
            print(f"{user.id:<38} {user.display_name:<20} {line_id:<30} {super_admin:<12}")

        print("=" * 100)
        print(f"\nTotal users: {len(users)}")
        print("\n💡 To set super admin:")
        print("   python set_superadmin_line.py <LINE_ID>")


if __name__ == "__main__":
    asyncio.run(list_users())
