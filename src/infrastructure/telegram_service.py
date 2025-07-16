import os
from telegram import Bot
from telegram.error import TelegramError
from telegram.constants import ParseMode
from ..domain.interfaces import TelegramService, LoggingService


class TelegramServiceImpl(TelegramService):
    """Telegram service implementation."""

    def __init__(self, bot_token: str, logger: LoggingService):
        self.bot = Bot(token=bot_token)
        self.logger = logger

    # =========================================================================
    # CORE USER INTERACTION HANDLERS (High Priority)
    # These methods directly respond to Telegram updates (commands, messages, callbacks).
    # =========================================================================

    async def send_photo(self, chat_id: str, photo_path: str, caption: str) -> bool:
        """Send photo to Telegram."""
        try:
            if not os.path.exists(photo_path):
                self.logger.error(f"Photo file not found: {photo_path}")
                return False

            with open(photo_path, "rb") as photo:
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                )

            self.logger.info(f"Photo sent successfully: {os.path.basename(photo_path)}")
            return True

        except TelegramError as e:
            self.logger.error(f"Telegram error sending photo: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending photo: {str(e)}")
            return False

    async def send_message(
        self, chat_id: str, text: str, parse_mode: str = "HTML"
    ) -> bool:
        """Send message to Telegram."""
        try:
            await self.bot.send_message(
                chat_id=chat_id, text=text, parse_mode=parse_mode
            )

            self.logger.info(f"Message sent successfully to {chat_id}")
            return True

        except TelegramError as e:
            self.logger.error(f"Telegram error sending message: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return False
