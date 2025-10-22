# -*- coding: utf-8 -*-
import smtplib
import ssl
import os
import logging
from fastapi import HTTPException
from jose import jwt, JWTError
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import EmailStr


class EmailVerificationUtility:
    def __init__(self, service, config_path="config.json"):
        from config_loader import ConfigLoader

        config_loader = ConfigLoader(config_path)
        smtp_config = config_loader.get_smtp_config()
        jwt_config = config_loader.get_jwt_config()

        self.smtp_host = smtp_config["host"]
        self.smtp_port = smtp_config["port"]
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.frontend_url = smtp_config["url"]

        self.auth_enabled = str(smtp_config.get("auth"))
        self.ssl_enabled = str(smtp_config.get("ssl_enable"))
        self.secret_key = jwt_config["secret_key"]
        self.algorithm = jwt_config["algorithm"]
        self.service = service
        self.template_path = os.path.join(os.path.dirname(__file__), "email-template.html")
        self.logger = logging.getLogger("EmailVerificationUtility")

    def create_verification_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(hours=24)
        data = {"sub": user_id, "exp": expire}
        token = jwt.encode(data, self.secret_key, algorithm=self.algorithm)
        self.logger.info(f"Verification token created for user_id={user_id}")
        return token

    def decode_verification_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=400, detail="Invalid verification token")
            return user_id
        except JWTError as e:
            self.logger.error(f"Invalid or expired token: {e}")
            raise HTTPException(status_code=400, detail="Invalid or expired token")

    def render_template(self, username: str, verify_link: str) -> str:
        if not os.path.exists(self.template_path):
            self.logger.error(f"Email template not found: {self.template_path}")
            raise HTTPException(status_code=500, detail="Email template not found")

        try:
            with open(self.template_path, "r", encoding="utf-8") as file:
                html = file.read()
                html = html.replace("{{username}}", username)
                html = html.replace("{{verify_link}}", verify_link)
                return html
        except Exception as e:
            self.logger.error(f"Template rendering failed: {e}")
            raise HTTPException(status_code=500, detail="Template rendering failed")

    def send_verification_email(self, to_email: EmailStr, username: str, user_id: str):
        token = self.create_verification_token(user_id)
        verify_link = f"{self.frontend_url}/auth/verify-email?token={token}"
        html_content = self.render_template(username, verify_link)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify your AegisAI Account"
        msg["From"] = self.smtp_user
        msg["To"] = str(to_email)
        msg.attach(MIMEText(html_content, "html"))

        context = ssl.create_default_context()

        try:
            self.logger.info(f"Connecting to {self.smtp_host}:{self.smtp_port} (SSL Mode)")
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=20) as server:
                server.ehlo()
                if self.auth_enabled:
                    self.logger.info("Authenticating user...")
                    server.login(self.smtp_user, self.smtp_pass)
                self.logger.info(f"Sending email to {to_email}...")
                server.send_message(msg)
                self.logger.info(f"✅ Email sent successfully to {to_email}")
        except smtplib.SMTPException as e:
            self.logger.error(f"❌ SMTP error: {e}")
            raise HTTPException(status_code=500, detail=f"SMTP error: {str(e)}")
        except Exception as e:
            self.logger.error(f"❌ Email sending failed: {e}")
            raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")