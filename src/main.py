import asyncio
import sys
from telegram.ext import Application

from .config import ConfigurationManager
from .infrastructure.services import (
    LoggingServiceImpl,
    CacheServiceImpl,
    NotificationServiceImpl,
)
from .infrastructure.storage_service import JsonStorageService
from .infrastructure.telegram_service import TelegramServiceImpl
from .infrastructure.image_downloader import ImageDownloaderImpl
from .infrastructure.wallpaper_repositories import (
    PexelsWallpaperRepository,
    UnsplashWallpaperRepository,
    WallhavenWallpaperRepository,
    CompositeWallpaperRepository,
)
from .application.use_cases import (
    SendWallpaperBatchUseCase,
    RotateSourceUseCase,
    GetBotStatusUseCase,
    AutoSchedulerUseCase,
)
from .presentation.bot_handlers import BotHandlers


class WallpaperBotApp:
    def __init__(self):
        self.config_manager = ConfigurationManager()
        self.config = None
        self.logger = None
        self.app = None
        self.bot_handlers = None

    async def initialize(self) -> None:
        self.config = self.config_manager.get_bot_configuration()
        self.config_manager.validate_configuration(self.config)

        self.logger = LoggingServiceImpl()
        self.logger.info("Initializing Wallpaper Bot...")

        storage_service = JsonStorageService(self.logger)
        telegram_service = TelegramServiceImpl(self.config.bot_token, self.logger)
        image_downloader = ImageDownloaderImpl(self.logger)
        cache_service = CacheServiceImpl(storage_service)
        notification_service = NotificationServiceImpl(
            str(self.config.admin_user_id), telegram_service
        )

        repositories = []
        if self.config.api_keys.get("pexels"):
            repositories.append(
                PexelsWallpaperRepository(self.config.api_keys["pexels"], self.logger)
            )
        if self.config.api_keys.get("unsplash"):
            repositories.append(
                UnsplashWallpaperRepository(
                    self.config.api_keys["unsplash"], self.logger
                )
            )
        if self.config.api_keys.get("wallhaven"):
            repositories.append(
                WallhavenWallpaperRepository(
                    self.config.api_keys["wallhaven"], self.logger
                )
            )

        wallpaper_repo = CompositeWallpaperRepository(repositories)

        send_batch_use_case = SendWallpaperBatchUseCase(
            self.config,
            wallpaper_repo,
            image_downloader,
            telegram_service,
            storage_service,
            cache_service,
            self.logger,
            notification_service,
        )

        rotate_source_use_case = RotateSourceUseCase(
            storage_service, self.logger, notification_service
        )

        get_status_use_case = GetBotStatusUseCase(storage_service, self.logger)

        auto_scheduler_use_case = AutoSchedulerUseCase(
            self.config,
            send_batch_use_case,
            rotate_source_use_case,
            storage_service,
            self.logger,
        )

        self.bot_handlers = BotHandlers(
            self.config,
            send_batch_use_case,
            rotate_source_use_case,
            get_status_use_case,
            auto_scheduler_use_case,
            self.logger,
        )

        self.app = Application.builder().token(self.config.bot_token).build()
        self.bot_handlers.setup_handlers(self.app)

        self.logger.info("Wallpaper Bot initialized successfully")

    # =========================================================================
    # CORE USER INTERACTION HANDLERS (High Priority)
    # These methods directly respond to Telegram updates (commands, messages, callbacks).
    # =========================================================================

    async def run(self) -> None:
        if not self.app:
            await self.initialize()

        try:
            self.logger.info("Starting Telegram bot...")

            await self.app.bot.send_message(
                chat_id=self.config.admin_user_id,
                text=(
                    "🚀 <b>Wallpaper Bot Started!</b>\n\n"
                    f"📊 Configuration:\n"
                    f"• Admin ID: {self.config.admin_user_id}\n"
                    f"• Channel: {self.config.channel_id}\n"
                    f"• Wallpapers per batch: {self.config.wallpapers_per_batch}\n"
                    f"• Batch interval: {self.config.batch_interval_hours} hours\n\n"
                    "Use /start to begin automatic wallpaper posting."
                ),
                parse_mode="HTML",
            )

            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(drop_pending_updates=True)

            self.logger.info("Bot is running! Press Ctrl+C to stop.")

            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        if self.app:
            try:
                if (
                    self.bot_handlers
                    and self.bot_handlers.auto_scheduler_use_case.is_running
                ):
                    self.bot_handlers.auto_scheduler_use_case.stop()

                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()

                self.logger.info("Application shutdown complete")

            except Exception as e:
                self.logger.error(f"Error during shutdown: {str(e)}")


async def main():
    """Main application entry point."""
    app = WallpaperBotApp()
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
