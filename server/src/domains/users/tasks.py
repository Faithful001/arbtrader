import smtplib
import structlog
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.infrastructure.celery.app import app
from src.core.config import settings

logger = structlog.get_logger(__name__)

@app.task(name="src.domains.users.tasks.send_otp", bind=True, max_retries=3, default_retry_delay=5)
def send_otp(self, email: str, otp: str):
    print(f"TASK STARTED: {email}", flush=True)
    print(f"GMAIL_USER: {settings.GMAIL_USER}", flush=True)
    print(f"GMAIL_APP_PASSWORD set: {bool(settings.GMAIL_APP_PASSWORD)}", flush=True)
    
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

        print("Connecting to SMTP...", flush=True)
        with smtplib.SMTP_SSL("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            print("Logging in...", flush=True)
            server.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
            print("Sending...", flush=True)
            server.sendmail(settings.GMAIL_USER, email, msg.as_string())

        print(f"OTP SENT to {email}", flush=True)
        logger.info("OTP sent", email=email)

    except Exception as e:
        print(f"TASK FAILED: {type(e).__name__}: {e}", flush=True)
        raise  # no retry, just fail loudly