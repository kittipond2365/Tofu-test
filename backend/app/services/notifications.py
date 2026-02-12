import httpx
import structlog
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.schemas.notifications import NotificationPayload, PushNotificationConfig, EmailConfig

logger = structlog.get_logger()

class NotificationService:
    """Service to send notifications through multiple channels"""
    
    def __init__(self):
        self.email_config: Optional[EmailConfig] = None
        self.fcm_server_key: Optional[str] = None
    
    def configure_email(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str, from_email: str):
        """Configure Email SMTP"""
        self.email_config = EmailConfig(
            enabled=True,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email
        )
        logger.info("Email configured", host=smtp_host)
    
    def configure_push(self, fcm_server_key: str):
        """Configure Firebase Cloud Messaging"""
        self.fcm_server_key = fcm_server_key
        logger.info("FCM configured")
    
    async def send_push_notification(self, fcm_token: str, title: str, body: str, data: Optional[dict] = None) -> bool:
        """Send push notification via Firebase Cloud Messaging
        
        Args:
            fcm_token: Device FCM token
            title: Notification title
            body: Notification body
            data: Extra data payload
        """
        if not self.fcm_server_key:
            logger.warning("FCM not configured")
            return False
        
        payload = {
            "message": {
                "token": fcm_token,
                "notification": {
                    "title": title,
                    "body": body
                },
                "data": data or {}
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # FCM HTTP v1 API
                response = await client.post(
                    "https://fcm.googleapis.com/v1/projects/badminton-app/messages:send",
                    headers={
                        "Authorization": f"Bearer {self.fcm_server_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                if response.status_code == 200:
                    logger.info("Push notification sent successfully")
                    return True
                else:
                    logger.error("Push notification failed", status=response.status_code)
                    return False
        except Exception as e:
            logger.error("Push notification error", error=str(e))
            return False
    
    async def send_email(self, to_email: str, subject: str, body: str, html: bool = False) -> bool:
        """Send email via SMTP
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
            html: Whether body is HTML
        """
        if not self.email_config or not self.email_config.enabled:
            logger.warning("Email not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            
            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type))
            
            await aiosmtplib.send(
                msg,
                hostname=self.email_config.smtp_host,
                port=self.email_config.smtp_port,
                username=self.email_config.smtp_user,
                password=self.email_config.smtp_password,
                use_tls=True
            )
            
            logger.info("Email sent successfully", to=to_email)
            return True
            
        except Exception as e:
            logger.error("Email error", error=str(e))
            return False
    
    async def notify_user(self, payload: NotificationPayload, 
                         fcm_token: Optional[str] = None,
                         email: Optional[str] = None) -> dict:
        """Send notification through all configured channels
        
        Returns:
            Dict with status of each channel
        """
        results = {
            "push": False,
            "email": False
        }
        
        # Push Notification
        if payload.channel in ["push", "all"] and fcm_token:
            results["push"] = await self.send_push_notification(
                fcm_token, payload.title, payload.message, payload.data
            )
        
        # Email
        if payload.channel in ["email", "all"] and email:
            results["email"] = await self.send_email(
                email, payload.title, payload.message
            )
        
        return results

# Global instance
notification_service = NotificationService()
