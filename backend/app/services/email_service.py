#!/usr/bin/env python3
"""
Email Service - Gửi email thông báo khi có tín hiệu (SMTP)
"""

import os
import logging
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    """Đơn giản hoá gửi email qua SMTP với TLS."""

    def __init__(self) -> None:
        self.smtp_host = os.getenv("SMTP_HOST", os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com"))
        self.smtp_port = int(os.getenv("SMTP_PORT", os.getenv("EMAIL_SMTP_PORT", "587")))
        self.sender_address = os.getenv("EMAIL_ADDRESS")
        self.sender_password = os.getenv("EMAIL_PASSWORD")
        # Danh sách người nhận, phân tách bởi dấu phẩy
        self.recipients: List[str] = [
            addr.strip() for addr in os.getenv("EMAIL_TO", "").split(",") if addr.strip()
        ]

        safe_recipients = ",".join(self.recipients[:3]) + ("..." if len(self.recipients) > 3 else "")
        logger.info(
            f"Email Service initialized: host={self.smtp_host}:{self.smtp_port}, sender={self.sender_address}, to=[{safe_recipients}]"
        )

    def is_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_port and self.sender_address and self.sender_password and self.recipients)

    def send(self, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
        """Gửi email tới danh sách `EMAIL_TO`.

        Returns True nếu gửi thành công tới ít nhất một người nhận.
        """
        if not self.is_configured():
            logger.warning("Email service not fully configured - skipping email send")
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_address
            message["To"] = ", ".join(self.recipients)

            part_text = MIMEText(body_text or "", "plain", _charset="utf-8")
            message.attach(part_text)
            if body_html:
                part_html = MIMEText(body_html, "html", _charset="utf-8")
                message.attach(part_html)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_address, self.sender_password)
                server.sendmail(self.sender_address, self.recipients, message.as_string())

            logger.info("Email sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


# Singleton instance
email_service = EmailService()


