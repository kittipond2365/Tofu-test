from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.notifications import notification_service
from app.models.models import User

router = APIRouter()


@router.post("/notifications/test/email")
async def test_email_notification(
    subject: str = "ทดสอบ Email",
    body: str = "นี่คือการทดสอบการส่ง Email จาก Badminton App 🏸",
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Test Email notification"""
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not configured for user"
        )
    
    success = await notification_service.send_email(
        to_email=user.email,
        subject=subject,
        body=body
    )
    
    if success:
        return {"message": "Email sent successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )


@router.post("/users/notifications/settings")
async def update_notification_settings(
    fcm_token: str = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update user's notification tokens"""
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if fcm_token:
        user.fcm_token = fcm_token
    
    await db.flush()
    
    return {
        "message": "Notification settings updated",
        "push_configured": bool(user.fcm_token)
    }
