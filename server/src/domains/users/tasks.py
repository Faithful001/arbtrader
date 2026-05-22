import smtplib
import structlog
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.infrastructure.celery.app import app
from src.core.config import settings

logger = structlog.get_logger(__name__)

@app.task(name="src.domains.users.tasks.send_otp", bind=True, max_retries=3, default_retry_delay=5)
def send_otp(self, email: str, otp: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your ArbTrader OTP"
        msg["From"] = f"ArbTrader <{settings.GMAIL_USER}>"
        msg["To"] = email

        html = f"""
            <div style="font-family: monospace; padding: 24px;">
                <h2 style="letter-spacing: 0.05em;">ARBTRADER</h2>
                <p>Your one-time password is:</p>
                <h1 style="letter-spacing: 0.2em; font-size: 36px;">{otp}</h1>
                <p style="color: #888; font-size: 12px;">
                    Expires in 5 minutes. Do not share this code.
                </p>
            </div>
        """
        plain = f"Your ArbTrader OTP is: {otp}\n\nExpires in 5 minutes. Do not share this code."
        
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
            server.sendmail(settings.GMAIL_USER, email, msg.as_string())

        logger.info("OTP sent", email=email)
    except Exception as e:
        logger.error("Failed to send OTP", email=email, error=str(e))
        raise self.retry(exc=e)