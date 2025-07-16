import asyncio
from typing import Dict, Any
from telegram import Update
from telegram.ext import (
    ContextTypes,
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from ..domain.entities import BotConfiguration, WallpaperSource
from ..application.use_cases import (
    SendWallpaperBatchUseCase,
    RotateSourceUseCase,
    GetBotStatusUseCase,
    AutoSchedulerUseCase,
)
from ..domain.interfaces import LoggingService


class BotHandlers:
    """Bot command handlers."""

    def __init__(
        self,
        config: BotConfiguration,
        send_batch_use_case: SendWallpaperBatchUseCase,
        rotate_source_use_case: RotateSourceUseCase,
        get_status_use_case: GetBotStatusUseCase,
        auto_scheduler_use_case: AutoSchedulerUseCase,
        logger: LoggingService,
    ):
        self.config = config
        self.send_batch_use_case = send_batch_use_case
        self.rotate_source_use_case = rotate_source_use_case
        self.get_status_use_case = get_status_use_case
        self.auto_scheduler_use_case = auto_scheduler_use_case
        self.logger = logger
        self.scheduler_task = None

    # =========================================================================
    # CORE USER INTERACTION HANDLERS (High Priority)
    # These methods directly respond to Telegram updates (commands, messages, callbacks).
    # =========================================================================

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start command handler."""
        if not await self.admin_only(update, context):
            return

        if self.auto_scheduler_use_case.is_running:
            await update.message.reply_text("🔄 Bot is already running!")
            return

        await update.message.reply_text(
            "🚀 <b>Wallpaper Bot Starting...</b>\n\n"
            f"📊 Configuration:\n"
            f"• {self.config.wallpapers_per_batch} wallpapers per batch\n"
            f"• Every {self.config.batch_interval_hours} hours\n"
            f"• Channel: {self.config.channel_id}\n\n"
            "Starting automatic scheduler...",
            parse_mode=ParseMode.HTML,
        )

        # Start the scheduler
        self.scheduler_task = asyncio.create_task(self.auto_scheduler_use_case.start())

        await update.message.reply_text("✅ Bot started successfully!")

    async def stop_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Stop command handler."""
        if not await self.admin_only(update, context):
            return

        if not self.auto_scheduler_use_case.is_running:
            await update.message.reply_text("⏹️ Bot is not running!")
            return

        self.auto_scheduler_use_case.stop()

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
            self.scheduler_task = None

        await update.message.reply_text("⏹️ Bot stopped successfully!")

    async def status_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Status command handler."""
        if not await self.admin_only(update, context):
            return

        try:
            status = await self.get_status_use_case.execute()

            status_text = (
                f"📊 <b>Bot Status</b>\n\n"
                f"{'🟢 Running' if self.auto_scheduler_use_case.is_running else '🔴 Stopped'}\n\n"
                f"📈 Current Session:\n"
                f"• Current Source: {status['current_source'].title()}\n"
                f"• Next Source: {status['next_source'].title()}\n"
                f"• Last Batch: {status['last_batch_time'].strftime('%Y-%m-%d %H:%M:%S') if status['last_batch_time'] else 'Never'}\n\n"
                f"📊 Statistics:\n"
                f"• Total Sent: {status['total_sent']}\n"
                f"• Successful Batches: {status['successful_batches']}\n"
                f"• Failed Batches: {status['failed_batches']}\n"
                f"• Uptime: {status['uptime']}"
            )

            await update.message.reply_text(status_text, parse_mode=ParseMode.HTML)

        except Exception as e:
            await update.message.reply_text(f"❌ Error getting status: {str(e)}")

    async def stats_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Detailed stats command handler."""
        if not await self.admin_only(update, context):
            return

        try:
            status = await self.get_status_use_case.execute()

            # Source usage
            source_stats = []
            for source, count in status["sources_used"].items():
                source_stats.append(f"• {source.title()}: {count}")

            # Daily stats
            daily_stats = []
            for day, count in status["daily_stats"].items():
                daily_stats.append(f"• {day}: {count}")

            stats_text = (
                f"📊 <b>Detailed Statistics</b>\n\n"
                f"🎯 Source Usage:\n" + "\n".join(source_stats) + "\n\n"
                f"📅 Recent Daily Stats:\n" + "\n".join(daily_stats)
            )

            await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)

        except Exception as e:
            await update.message.reply_text(f"❌ Error getting stats: {str(e)}")

    async def send_batch_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Manually send a batch."""
        if not await self.admin_only(update, context):
            return

        await update.message.reply_text("🔄 Sending batch manually...")

        try:
            # Get current source
            status = await self.get_status_use_case.execute()
            current_source = WallpaperSource(status["current_source"])

            # Send batch
            sent_count = await self.send_batch_use_case.execute(
                current_source, self.config.wallpapers_per_batch
            )

            if sent_count > 0:
                await update.message.reply_text(
                    f"✅ Successfully sent {sent_count} wallpapers!"
                )
            else:
                await update.message.reply_text("❌ Failed to send any wallpapers!")

        except Exception as e:
            await update.message.reply_text(f"❌ Error sending batch: {str(e)}")

    async def rotate_source_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Manually rotate source."""
        if not await self.admin_only(update, context):
            return

        try:
            old_source, new_source = await self.rotate_source_use_case.execute(
                force=True
            )

            await update.message.reply_text(
                f"🔄 Source rotated: {old_source.value.title()} → {new_source.value.title()}"
            )

        except Exception as e:
            await update.message.reply_text(f"❌ Error rotating source: {str(e)}")

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Help command handler."""
        if not await self.admin_only(update, context):
            return

        help_text = (
            "🤖 <b>Wallpaper Bot Commands</b>\n\n"
            "/start - Start the bot\n"
            "/stop - Stop the bot\n"
            "/status - Show current status\n"
            "/stats - Show detailed statistics\n"
            "/send_batch - Send a batch manually\n"
            "/rotate_source - Rotate to next source\n"
            "/help - Show this help message\n\n"
            "The bot automatically sends wallpapers every 2 hours."
        )

        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle non-command messages."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text(
                "❌ Access denied. This bot is for admin use only."
            )
            return

        await update.message.reply_text("Use /help to see available commands.")

    # =========================================================================
    # INTERNAL HELPER METHODS (Utility Functions)
    # These methods provide supporting functionality for the main handlers.
    # =========================================================================

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id == self.config.admin_user_id

    async def admin_only(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """Check admin access."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text(
                "❌ Access denied. This bot is for admin use only."
            )
            return False
        return True

    def setup_handlers(self, app: Application) -> None:
        """Setup bot handlers."""
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("stop", self.stop_command))
        app.add_handler(CommandHandler("status", self.status_command))
        app.add_handler(CommandHandler("stats", self.stats_command))
        app.add_handler(CommandHandler("send_batch", self.send_batch_command))
        app.add_handler(CommandHandler("rotate_source", self.rotate_source_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(MessageHandler(filters.ALL, self.handle_message))
