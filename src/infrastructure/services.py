import logging
from typing import List, Dict, Any
from datetime import datetime
from ..domain.entities import SentImage, WallpaperSource
from ..domain.interfaces import (
    CacheService,
    LoggingService,
    NotificationService,
    StorageService,
    TelegramService,
)


class LoggingServiceImpl(LoggingService):
    """Logging service implementation."""

    # =========================================================================
    # INITIALIZATION AND SETUP METHODS (High Priority)
    # These methods handle the initial setup and configuration of the logging service.
    # =========================================================================

    def __init__(self, log_file: str = "logs/wallpaper_bot.log"):
        """
        Initializes the LoggingServiceImpl with a specified log file.
        Sets up file and console handlers for logging.
        """
        self.logger = logging.getLogger("WallpaperBot")
        self.logger.setLevel(logging.INFO)

        import os

        os.makedirs("logs", exist_ok=True)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    # =========================================================================
    # LOGGING METHODS (High Priority)
    # These methods provide different levels of logging functionality.
    # =========================================================================

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)


class CacheServiceImpl(CacheService):
    """Cache service implementation."""

    # =========================================================================
    # INITIALIZATION AND SETUP METHODS (High Priority)
    # These methods handle the initial setup and configuration of the cache service.
    # =========================================================================

    def __init__(self, storage_service: StorageService):
        """
        Initializes the CacheServiceImpl with a storage service.
        Sets up an empty cache for sent images.
        """
        self.storage_service = storage_service
        self._sent_images_cache: Dict[str, SentImage] = {}
        self._cache_loaded = False

    # =========================================================================
    # CORE CACHE METHODS (High Priority)
    # These methods are responsible for loading, checking, and marking images in the cache.
    # =========================================================================

    async def _load_cache(self) -> None:
        """
        Loads the sent images cache from storage if it hasn't been loaded yet.
        """
        if not self._cache_loaded:
            sent_images = await self.storage_service.load_sent_images()
            self._sent_images_cache = {img.url: img for img in sent_images}
            self._cache_loaded = True

    async def is_image_sent(self, url: str) -> bool:
        """
        Checks if an image with the given URL has already been marked as sent.
        Ensures the cache is loaded before checking.
        """
        await self._load_cache()
        return url in self._sent_images_cache

    async def mark_image_as_sent(self, sent_image: SentImage) -> None:
        """
        Marks an image as sent by adding it to the cache and persisting the cache to storage.
        Ensures the cache is loaded before marking.
        """
        await self._load_cache()
        self._sent_images_cache[sent_image.url] = sent_image

        await self.storage_service.save_sent_images(
            list(self._sent_images_cache.values())
        )


class NotificationServiceImpl(NotificationService):
    """Notification service implementation."""

    # =========================================================================
    # INITIALIZATION AND SETUP METHODS (High Priority)
    # These methods handle the initial setup and configuration of the notification service.
    # =========================================================================

    def __init__(self, admin_user_id: str, telegram_service: TelegramService):
        """
        Initializes the NotificationServiceImpl with the admin user ID and a Telegram service.
        """
        self.admin_user_id = admin_user_id
        self.telegram_service = telegram_service

    # =========================================================================
    # NOTIFICATION METHODS (High Priority)
    # These methods are responsible for sending various types of notifications.
    # =========================================================================

    async def notify_admin(self, message: str) -> None:
        """
        Sends a message as a notification to the configured admin user.
        """
        await self.telegram_service.send_message(self.admin_user_id, message)

    async def notify_batch_complete(
        self, sent_count: int, source: WallpaperSource
    ) -> None:
        """
        Notifies the admin about the completion of a batch of wallpapers sent.
        Includes details like sent count, source, and next batch time.
        """
        next_batch_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        next_batch_time = next_batch_time.replace(hour=next_batch_time.hour + 2)

        message = (
            f"✅ <b>Batch Complete!</b>\n\n"
            f"📊 Successfully sent {sent_count} wallpapers\n"
            f"📤 Source: {source.value.title()}\n"
            f"⏰ Next batch: {next_batch_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🔄 Source will rotate for next batch"
        )

        await self.notify_admin(message)

    async def notify_error(self, error: str) -> None:
        """
        Notifies the admin about an error that occurred.
        """
        message = f"❌ <b>Error:</b> {error}"
        await self.notify_admin(message)
