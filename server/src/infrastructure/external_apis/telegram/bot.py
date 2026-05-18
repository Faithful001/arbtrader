"""
Telegram Bot sender — dispatches alert messages to user Telegram chats.
No-ops in mock mode with a log message.
"""
import structlog
from src.core.config import settings

logger = structlog.get_logger(__name__)


class TelegramBot:
    """
    Sends Telegram messages to users.
    In mock mode, logs the message instead of sending.
    """

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self._bot = None

    def _get_bot(self):
        if settings.USE_MOCK_DATA:
            return None
        if self._bot is None:
            try:
                from telegram import Bot
                self._bot = Bot(token=self.token)
            except Exception as e:
                logger.error("Telegram bot init failed", error=str(e))
        return self._bot

    async def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to a Telegram chat. Returns True on success."""
        if settings.USE_MOCK_DATA or not chat_id:
            logger.info("MOCK Telegram message", chat_id=chat_id, preview=text[:100])
            return True

        try:
            bot = self._get_bot()
            if bot:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
                logger.info("Telegram message sent", chat_id=chat_id)
                return True
        except Exception as e:
            logger.error("Telegram send failed", chat_id=chat_id, error=str(e))
        return False

    async def send_opportunity_alert(
        self,
        chat_id: str,
        card_name: str,
        buy_market: str,
        sell_market: str,
        net_profit_gbp: float,
        roi_percent: float,
        confidence: float,
    ) -> bool:
        emoji = "🔥" if net_profit_gbp > 20 else "📈"
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
