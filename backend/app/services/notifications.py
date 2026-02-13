import httpx
import structlog
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.core.config import get_settings
from app.schemas.notifications import NotificationPayload, EmailConfig
from app.services.fcm_oauth import get_cached_fcm_token

logger = structlog.get_logger()


class NotificationService:
    """Service to send notifications through multiple channels"""

    def __init__(self):
        self.email_config: Optional[EmailConfig] = None
        self.fcm_server_key: Optional[str] = None  # legacy fallback
        self.firebase_project_id: str = ""
        self.fcm_enabled: bool = False

    def configure_email(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str, from_email: str):
        """Configure Email SMTP"""
        self.email_config = EmailConfig(
            enabled=True,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email,
        )
        logger.info("Email configured", host=smtp_host)

    def configure_push(self, firebase_project_id: Optional[str] = None, fcm_server_key: Optional[str] = None):
        """Configure Firebase Cloud Messaging (FCM HTTP v1 + optional legacy fallback)."""
        settings = get_settings()
        self.firebase_project_id = firebase_project_id or settings.FIREBASE_PROJECT_ID
        self.fcm_server_key = fcm_server_key or settings.FCM_SERVER_KEY
        self.fcm_enabled = bool(self.firebase_project_id)

        logger.info(
            "FCM configured",
            v1_enabled=self.fcm_enabled,
            legacy_fallback_enabled=bool(self.fcm_server_key),
        )

    async def _send_v1_push_notification(self, fcm_token: str, title: str, body: str, data: Optional[dict] = None) -> bool:
        access_token = get_cached_fcm_token()

        payload = {
            "message": {
                "token": fcm_token,
                "notification": {"title": title, "body": body},
                "data": {str(k): str(v) for k, v in (data or {}).items()},
                "android": {"priority": "high"},
                "apns": {"payload": {"aps": {"sound": "default"}}},
            }
        }

        url = f"https://fcm.googleapis.com/v1/projects/{self.firebase_project_id}/messages:send"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code == 200:
            logger.info("Push notification sent successfully (v1)")
            return True

        logger.error(
            "Push notification failed (v1)",
            status=response.status_code,
            response=response.text,
        )
        return False

    async def _send_legacy_push_notification(self, fcm_token: str, title: str, body: str, data: Optional[dict] = None) -> bool:
        if not self.fcm_server_key:
            return False

        payload = {
            "to": fcm_token,
            "notification": {"title": title, "body": body},
            "data": data or {},
            "priority": "high",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fcm.googleapis.com/fcm/send",
                headers={
                    "Authorization": f"key={self.fcm_server_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code == 200:
            logger.info("Push notification sent successfully (legacy fallback)")
            return True

        logger.error(
            "Push notification failed (legacy fallback)",
            status=response.status_code,
            response=response.text,
        )
        return False

    async def send_push_notification(self, fcm_token: str, title: str, body: str, data: Optional[dict] = None) -> bool:
        """Send push notification via Firebase Cloud Messaging.

        Returns False on any error to preserve backward-compatible error behavior.
        """
        if not self.fcm_enabled and not self.fcm_server_key:
            logger.warning("FCM not configured")
            return False

        try:
            if self.fcm_enabled:
                return await self._send_v1_push_notification(fcm_token, title, body, data)

            logger.warning("Using legacy FCM fallback because FIREBASE_PROJECT_ID is not configured")
            return await self._send_legacy_push_notification(fcm_token, title, body, data)

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
                use_tls=True,
            )

            logger.info("Email sent successfully", to=to_email)
            return True

        except Exception as e:
            logger.error("Email error", error=str(e))
            return False

    async def notify_user(self, payload: NotificationPayload, fcm_token: Optional[str] = None, email: Optional[str] = None) -> dict:
        """Send notification through all configured channels

        Returns:
            Dict with status of each channel
        """
        results = {"push": False, "email": False}

        if payload.channel in ["push", "all"] and fcm_token:
            results["push"] = await self.send_push_notification(fcm_token, payload.title, payload.message, payload.data)

        if payload.channel in ["email", "all"] and email:
            results["email"] = await self.send_email(email, payload.title, payload.message)

        return results


# Global instance
notification_service = NotificationService()


async def send_push_notification(fcm_token: str, title: str, body: str, data: Optional[dict] = None) -> bool:
    """Backward-compatible module-level helper."""
    return await notification_service.send_push_notification(fcm_token, title, body, data)
