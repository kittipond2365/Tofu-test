"""
Set Super Admin for LINE Login users
Usage: python set_superadmin_line.py <line_user_id>
Example: python set_superadmin_line.py U4af4980629...
"""
import sys
import asyncio
from sqlmodel import select
from app.core.database import get_db_session
from app.models.models import User

async def set_superadmin(line_user_id: str):
    async with get_db_session() as db:
        # Find user by LINE ID
        result = await db.execute(
            select(User).where(User.line_user_id == line_user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with LINE ID {line_user_id} not found")
            print("\n💡 Tips:")
            print("1. Login to the app first (to create user record)")
            print("2. Check database for line_user_id")
            print("3. Or use: python get_users.py to list all users")
            return
        
        # Check if already super admin
        if user.is_super_admin:
            print(f"✅ User {user.display_name} is already super admin")
            return
        
        # Set as super admin
        user.is_super_admin = True
        await db.commit()
        
        print(f"✅ Success! User '{user.display_name}' is now super admin")
        print(f"   LINE ID: {user.line_user_id}")
        print(f"   User ID: {user.id}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python set_superadmin_line.py <line_user_id>")
        print("Example: python set_superadmin_line.py U4af4980629...")
        sys.exit(1)
    
    line_user_id = sys.argv[1]
    asyncio.run(set_superadmin(line_user_id))
