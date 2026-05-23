# pyrefly: ignore [missing-import]
import resend
import structlog

from src.infrastructure.celery.app import app
from src.core.config import settings

logger = structlog.get_logger(__name__)


@app.task(name="src.domains.users.tasks.send_otp", bind=True, max_retries=3, default_retry_delay=5)
def send_otp(self, email: str, otp: str):
    try:
        resend.api_key = settings.RESEND_API_KEY

        resend.Emails.send({
            "from": "ArbTrader <noreply@faithfulking.xyz>",
            "to": email,
            "subject": "Your ArbTrader sign-in code",
            "html": f"""
                <div style="font-family: monospace; padding: 24px;">
                    <h2 style="letter-spacing: 0.05em;">ARBTRADER</h2>
                    <p>Your one-time password is:</p>
                    <h1 style="letter-spacing: 0.2em; font-size: 36px;">{otp}</h1>
                    <p style="color: #888; font-size: 12px;">
                        Expires in 5 minutes. Do not share this code.
                    </p>
                </div>
            """,
        })

        logger.info("OTP sent", email=email)

    except Exception as e:
        logger.error("Failed to send OTP", email=email, error=str(e))
        raise self.retry(exc=e)