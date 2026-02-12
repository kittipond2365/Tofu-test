from datetime import datetime, timedelta
from typing import List, Optional
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.models import Session, SessionRegistration, User, Club
from app.services.notifications import notification_service
from app.core.redis import get_redis

logger = structlog.get_logger()

class ScheduledNotificationService:
    """Service to handle scheduled notifications"""
    
    async def check_upcoming_sessions(self):
        """Check for sessions starting within 1 hour and send reminders"""
        async with AsyncSessionLocal() as db:
            now = datetime.utcnow()
            one_hour_later = now + timedelta(hours=1)
            
            # Find sessions starting in next hour
            result = await db.execute(
                select(Session, Club)
                .join(Club)
                .where(
                    Session.start_time >= now,
                    Session.start_time <= one_hour_later,
                    Session.status.in_(["open", "ongoing"])
                )
            )
            sessions = result.all()
            
            for session, club in sessions:
                await self._send_session_reminder(db, session, club)
    
    async def _send_session_reminder(self, db: AsyncSession, session: Session, club: Club):
        """Send reminder to all confirmed participants"""
        # Get confirmed registrations
        result = await db.execute(
            select(SessionRegistration, User)
            .join(User)
            .where(
                SessionRegistration.session_id == session.id,
                SessionRegistration.status == "confirmed"
            )
        )
        registrations = result.all()
        
        message = f"\n🏸 แจ้งเตือนกิจกรรมแบดมินตัน\n\nกิจกรรม: {session.title}\nชมรม: {club.name}\nเวลา: {session.start_time.strftime('%H:%M น.')}\nสถานที่: {session.location}\n\nอย่าลืมมาตรงเวลานะ! 🏸"
        
        for registration, user in registrations:
            # Check if already notified (using Redis)
            r = await get_redis()
            notified_key = f"notified:session:{session.id}:user:{user.id}"
            already_notified = await r.get(notified_key)
            
            if already_notified:
                continue
            
            # Send Push Notification
            if user.fcm_token:
                await notification_service.send_push_notification(
                    user.fcm_token,
                    title=f"แจ้งเตือนกิจกรรม - {session.title}",
                    body=f"กิจกรรมเริ่มในอีก 1 ชั่วโมง ที่ {session.location}",
                    data={"session_id": str(session.id), "type": "session_reminder"}
                )
            
            # Send Email
            if user.email:
                await notification_service.send_email(
                    to_email=user.email,
                    subject=f"[Badminton] แจ้งเตือนกิจกรรม - {session.title}",
                    body=message
                )
            
            # Mark as notified (expire after session end)
            await r.setex(notified_key, 3600 * 4, "1")  # 4 hours expiry
            
            logger.info("Session reminder sent", 
                       user_id=user.id, 
                       session_id=session.id,
                       channels=["push" if user.fcm_token else None, "email" if user.email else None])
    
    async def notify_waitlist_promotion(self, session_id: str, user_id: str):
        """Notify user when they are promoted from waitlist to confirmed"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User, Session, Club)
                .join(Session, Session.id == session_id)
                .join(Club, Club.id == Session.club_id)
                .where(User.id == user_id)
            )
            user, session, club = result.first()
            
            message = f"\n🎉 ยินดีด้วย! คุณได้รับสิทธิเข้าร่วมกิจกรรม\n\nกิจกรรม: {session.title}\nชมรม: {club.name}\nเวลา: {session.start_time.strftime('%d/%m/%Y %H:%M น.')}\nสถานที่: {session.location}\n\nรีบไปลงทะเบียนในแอพเพื่อยืนยันการเข้าร่วม! 🏸"
            
            # Send Push Notification
            if user.fcm_token:
                await notification_service.send_push_notification(
                    user.fcm_token,
                    title="🎉 ได้รับสิทธิเข้าร่วมกิจกรรม!",
                    body=f"{session.title} - {club.name}",
                    data={"session_id": str(session.id), "type": "waitlist_promotion"}
                )
            
            # Send Email
            if user.email:
                await notification_service.send_email(
                    to_email=user.email,
                    subject=f"[Badminton] ได้รับสิทธิเข้าร่วมกิจกรรม - {session.title}",
                    body=message
                )
            
            logger.info("Waitlist promotion notification sent", 
                       user_id=user_id, 
                       session_id=session_id)
    
    async def notify_match_created(self, match_id: str, user_ids: List[str]):
        """Notify players when a match is created for them"""
        async with AsyncSessionLocal() as db:
            for user_id in user_ids:
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    continue
                
                # Send Push Notification
                if user.fcm_token:
                    await notification_service.send_push_notification(
                        user.fcm_token,
                        title="🏸 มีการแข่งขันใหม่!",
                        body="คุณมีการแข่งขันใหม่ กดเพื่อดูรายละเอียด",
                        data={"match_id": match_id, "type": "match_created"}
                    )
                
                logger.info("Match created notification sent", 
                           user_id=user_id, 
                           match_id=match_id)

# Global instance
scheduled_notification_service = ScheduledNotificationService()
