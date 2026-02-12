from typing import Optional
from pydantic import BaseModel, EmailStr

class NotificationPayload(BaseModel):
    user_id: str
    title: str
    message: str
    channel: str  # push, email, all
    data: Optional[dict] = None  # extra data for deep linking, etc.

class PushNotificationConfig(BaseModel):
    enabled: bool = False
    fcm_token: Optional[str] = None  # Firebase Cloud Messaging token

class EmailConfig(BaseModel):
    enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
