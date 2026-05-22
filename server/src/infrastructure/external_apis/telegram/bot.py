
import structlog
from telegram import Bot
# pyrefly: ignore [missing-import]
from telegram.constants import MessageLimit
# pyrefly: ignore [missing-import]
from telegram.error import TelegramError
import asyncio

from src.core.config import settings

logger = structlog.get_logger(__name__)

MAX_TEXT_LENGTH = MessageLimit.MAX_TEXT_LENGTH 


class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self._bot: Bot | None = None
        self._initialized: bool = False
        self._init_failed: bool = False

    async def _get_bot(self) -> Bot | None:
        """Lazily initialize and return the Bot instance."""
        if self._init_failed:
            return None

        if self._bot is None:
            try:
                self._bot = Bot(token=self.token)
                await self._bot.initialize()
                self._initialized = True
                logger.info("Telegram bot initialized")
            except Exception as e:
                self._init_failed = True
                self._bot = None
                logger.error("Telegram bot init failed", error=str(e))
                return None

        return self._bot

 

    async def close(self) -> None:
        if self._bot is None or not self._initialized:
            return
        try:
            await asyncio.wait_for(self._bot.shutdown(), timeout=3.0)
            logger.info("Telegram bot shut down")
        except asyncio.TimeoutError:
            logger.warning("Telegram bot shutdown timed out, forcing close")
        except Exception as e:
            logger.warning("Telegram bot shutdown error", error=str(e))
        finally:
            self._bot = None
            self._initialized = False

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        parse_mode: str = "HTML",
    ) -> bool:
        if not chat_id:
            logger.warning("send_message called with empty chat_id")
            return False

        # Truncate to Telegram's hard limit
        if len(text) > MAX_TEXT_LENGTH:
            text = text[: MAX_TEXT_LENGTH - 3] + "..."

        if settings.USE_MOCK_DATA:
            logger.info("MOCK Telegram message", chat_id=chat_id, preview=text[:100])
            return True

        try:
            bot = await self._get_bot()
            if bot is None:
                logger.error("Telegram bot unavailable", chat_id=chat_id)
                return False

            await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
            logger.info("Telegram message sent", chat_id=chat_id)
            return True

        except TelegramError as e:
            logger.error("Telegram send failed", chat_id=chat_id, error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error sending Telegram message", chat_id=chat_id, error=str(e))
            return False

    async def send_opportunity_alert(
        self,
        chat_id: str | int,
        card_name: str,
        buy_market: str,
        sell_market: str,
        net_profit_gbp: float,
        roi_percent: float,
        confidence: float,
    ) -> bool:
        """
        Send a formatted arbitrage opportunity alert.

        Args:
            chat_id: Telegram chat ID.
            card_name: Name of the trading card.
            buy_market: Market/platform to buy from.
            sell_market: Market/platform to sell on.
            net_profit_gbp: Expected net profit in GBP.
            roi_percent: Return on investment as a percentage.
            confidence: Confidence score in range [0.0, 1.0].

        Returns:
            True on success, False on failure.
        """
        # Clamp confidence to valid range
        confidence = max(0.0, min(1.0, confidence))

        emoji = "🔥" if net_profit_gbp > settings.ALERT_HIGH_PROFIT_THRESHOLD_GBP else "📈"

        text = (
            f"{emoji} <b>Arbitrage Opportunity</b>\n\n"
            f"🃏 <b>{card_name}</b>\n"
            f"🛒 Buy: <b>{buy_market}</b>\n"
            f"💰 Sell: <b>{sell_market}</b>\n"
            f"💵 Net Profit: <b>£{net_profit_gbp:.2f}</b>\n"
            f"📊 ROI: <b>{roi_percent:.1f}%</b>\n"
            f"🎯 Confidence: <b>{confidence * 100:.0f}%</b>"
        )

        return await self.send_message(chat_id, text)


# Singleton
telegram_bot = TelegramBot()