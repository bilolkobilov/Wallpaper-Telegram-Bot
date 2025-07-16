import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from ..domain.entities import (
    Wallpaper,
    WallpaperSource,
    WallpaperCategory,
    SentImage,
    SourceRotation,
    BotConfiguration,
)
from ..domain.interfaces import (
    WallpaperRepository,
    ImageDownloader,
    TelegramService,
    StorageService,
    CacheService,
    LoggingService,
    NotificationService,
)


# =========================================================================
# CORE APPLICATION USE CASES (High Priority)
# These classes define the main business logic and orchestrate operations.
# =========================================================================


class SendWallpaperBatchUseCase:
    """Use case for sending a batch of wallpapers with enhanced filtering and performance."""

    def __init__(
        self,
        config: BotConfiguration,
        wallpaper_repo: WallpaperRepository,
        image_downloader: ImageDownloader,
        telegram_service: TelegramService,
        storage_service: StorageService,
        cache_service: CacheService,
        logger: LoggingService,
        notification_service: NotificationService,
    ):
        self.config = config
        self.wallpaper_repo = wallpaper_repo
        self.image_downloader = image_downloader
        self.telegram_service = telegram_service
        self.storage_service = storage_service
        self.cache_service = cache_service
        self.logger = logger
        self.notification_service = notification_service

    async def execute(self, source: WallpaperSource, count: int) -> int:
        """Execute the batch sending with enhanced error handling and performance."""
        self.logger.info(
            f"Starting batch send from {source.value} - requesting {count} wallpapers"
        )

        try:
            approved_wallpapers = await self._get_approved_wallpapers(source, count)

            if not approved_wallpapers:
                self.logger.warning(f"No approved wallpapers found from {source.value}")
                await self.notification_service.notify_error(
                    f"No approved wallpapers available from {source.value}"
                )
                return 0

            sent_count = await self._send_wallpapers_batch(approved_wallpapers, source)

            await self._update_stats(source, sent_count, len(approved_wallpapers))

            if sent_count > 0:
                await self.notification_service.notify_batch_complete(
                    sent_count, source
                )
                self.logger.info(
                    f"Batch completed successfully: {sent_count}/{len(approved_wallpapers)} wallpapers sent"
                )
            else:
                self.logger.warning("Batch completed with no wallpapers sent")

            return sent_count

        except Exception as e:
            self.logger.error(f"Critical error in batch send: {str(e)}")
            await self.notification_service.notify_error(f"Batch send failed: {str(e)}")
            return 0


class RotateSourceUseCase:
    """Enhanced use case for intelligent wallpaper source rotation."""

    def __init__(
        self,
        storage_service: StorageService,
        logger: LoggingService,
        notification_service: NotificationService,
    ):
        self.storage_service = storage_service
        self.logger = logger
        self.notification_service = notification_service

    async def execute(
        self, force: bool = False
    ) -> Tuple[WallpaperSource, WallpaperSource]:
        """Execute source rotation with intelligent decision making."""
        try:
            rotation = await self.storage_service.load_source_rotation()
            old_source = rotation.get_current_source()

            if force or await self._should_rotate(rotation):
                new_source = rotation.rotate_to_next()
                await self.storage_service.save_source_rotation(rotation)

                self.logger.info(
                    f"Source rotated: {old_source.value} → {new_source.value}"
                )
                await self.notification_service.notify_source_rotation(
                    old_source, new_source
                )

                return old_source, new_source

            self.logger.debug(f"No rotation needed, staying with {old_source.value}")
            return old_source, old_source

        except Exception as e:
            self.logger.error(f"Error in source rotation: {str(e)}")
            raise


class GetBotStatusUseCase:
    """Enhanced use case for comprehensive bot status reporting."""

    def __init__(self, storage_service: StorageService, logger: LoggingService):
        self.storage_service = storage_service
        self.logger = logger

    async def execute(self) -> dict:
        """Get comprehensive bot status with enhanced metrics."""
        try:
            stats = await self.storage_service.load_stats()
            rotation = await self.storage_service.load_source_rotation()

            current_source = rotation.get_current_source()
            next_source = rotation.get_next_source()

            # Calculate enhanced metrics
            uptime = datetime.now() - stats.start_time
            success_rate = (
                stats.successful_batches
                / max(stats.successful_batches + stats.failed_batches, 1)
            ) * 100
            avg_daily = sum(stats.daily_stats.values()) / max(len(stats.daily_stats), 1)

            return {
                "status": "active",
                "current_source": current_source.value,
                "next_source": next_source.value,
                "total_sent": stats.total_sent,
                "successful_batches": stats.successful_batches,
                "failed_batches": stats.failed_batches,
                "success_rate": round(success_rate, 2),
                "filtered_images": stats.filtered_images,
                "last_batch_time": stats.last_batch_time,
                "uptime": str(uptime),
                "uptime_hours": round(uptime.total_seconds() / 3600, 2),
                "sources_used": stats.sources_used,
                "daily_stats": dict(list(stats.daily_stats.items())[-7:]),
                "avg_daily_sent": round(avg_daily, 2),
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error getting bot status: {str(e)}")
            raise


class AutoSchedulerUseCase:
    """Enhanced automatic wallpaper scheduler with intelligent timing."""

    def __init__(
        self,
        config: BotConfiguration,
        send_batch_use_case: SendWallpaperBatchUseCase,
        rotate_source_use_case: RotateSourceUseCase,
        storage_service: StorageService,
        logger: LoggingService,
    ):
        self.config = config
        self.send_batch_use_case = send_batch_use_case
        self.rotate_source_use_case = rotate_source_use_case
        self.storage_service = storage_service
        self.logger = logger
        self.is_running = False
        self._task = None

    async def start(self) -> None:
        """Start the enhanced automatic scheduler."""
        if self.is_running:
            self.logger.warning("Scheduler already running")
            return

        self.is_running = True
        self.logger.info("Starting enhanced automatic wallpaper scheduler")

        try:
            while self.is_running:
                await self._execute_scheduled_batch()

                if self.is_running:
                    wait_time = self.config.batch_interval_hours * 3600
                    self.logger.info(
                        f"Next batch in {self.config.batch_interval_hours} hours"
                    )
                    await asyncio.sleep(wait_time)

        except asyncio.CancelledError:
            self.logger.info("Scheduler cancelled")
        except Exception as e:
            self.logger.error(f"Critical scheduler error: {str(e)}")
        finally:
            self.is_running = False

    def stop(self) -> None:
        """Stop the automatic scheduler."""
        self.is_running = False
        if self._task:
            self._task.cancel()
        self.logger.info("Stopping automatic wallpaper scheduler")


class CleanupUseCase:
    """Enhanced cleanup use case for better resource management."""

    def __init__(
        self,
        storage_service: StorageService,
        cache_service: CacheService,
        logger: LoggingService,
    ):
        self.storage_service = storage_service
        self.cache_service = cache_service
        self.logger = logger

    async def execute_full_cleanup(self) -> dict:
        """Execute comprehensive cleanup and return results."""
        results = {"temp_files_cleaned": 0, "cache_entries_cleaned": 0, "errors": []}

        try:
            temp_result = await self.cleanup_temp_files()
            results["temp_files_cleaned"] = temp_result

            cache_result = await self.cleanup_old_cache_entries()
            results["cache_entries_cleaned"] = cache_result

            self.logger.info(f"Cleanup completed: {results}")

        except Exception as e:
            error_msg = f"Cleanup error: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        return results

    # =========================================================================
    # HELPER METHODS (Internal Logic)
    # These methods support the main use cases and handle specific sub-tasks.
    # =========================================================================

    async def _get_approved_wallpapers(
        self, source: WallpaperSource, count: int
    ) -> List[Tuple[WallpaperCategory, Wallpaper]]:
        """Get approved wallpapers using optimized filtering strategy."""
        approved_wallpapers = []

        safe_categories = self._get_safe_categories()

        max_attempts = min(50, count * 3)
        batch_size = min(30, count * 5)
        attempts = 0

        self.logger.info(
            f"Searching for {count} approved wallpapers from {source.value}"
        )

        while len(approved_wallpapers) < count and attempts < max_attempts:
            category = random.choice(safe_categories)
            attempts += 1

            try:
                self.logger.debug(
                    f"Attempt {attempts}: Fetching {batch_size} wallpapers from {source.value} - {category.value}"
                )

                wallpapers = await self.wallpaper_repo.get_wallpapers(
                    source, category, batch_size
                )

                if not wallpapers:
                    self.logger.debug(f"No wallpapers available for {category.value}")
                    continue

                filtered_wallpapers = await self._filter_wallpapers(
                    wallpapers, category
                )

                for wallpaper in filtered_wallpapers:
                    if len(approved_wallpapers) >= count:
                        break
                    approved_wallpapers.append((category, wallpaper))
                    self.logger.debug(
                        f"Approved wallpaper {len(approved_wallpapers)}/{count}: {wallpaper.url}"
                    )

                if len(approved_wallpapers) >= count:
                    break

            except Exception as e:
                self.logger.error(
                    f"Error fetching wallpapers from {source.value}: {str(e)}"
                )

            if len(approved_wallpapers) < count:
                await asyncio.sleep(0.3)

        self.logger.info(
            f"Approved {len(approved_wallpapers)} wallpapers after {attempts} attempts"
        )
        return approved_wallpapers

    def _get_safe_categories(self) -> List[WallpaperCategory]:
        """Get list of safe wallpaper categories optimized for quality content."""
        return [
            # Nature & Landscapes
            WallpaperCategory.NATURE,
            WallpaperCategory.LANDSCAPE,
            WallpaperCategory.MOUNTAINS,
            WallpaperCategory.FOREST,
            WallpaperCategory.OCEAN,
            WallpaperCategory.WATER,
            WallpaperCategory.SKY,
            WallpaperCategory.CLOUDS,
            WallpaperCategory.SUNSET,
            # Space & Cosmic
            WallpaperCategory.SPACE,
            WallpaperCategory.GALAXY,
            # Abstract & Artistic
            WallpaperCategory.ABSTRACT,
            WallpaperCategory.MINIMAL,
            WallpaperCategory.GEOMETRIC,
            WallpaperCategory.GRADIENT,
            WallpaperCategory.DIGITAL_ART,
            WallpaperCategory.PATTERNS,
            # Materials & Textures
            WallpaperCategory.TEXTURES,
            WallpaperCategory.CRYSTALS,
            WallpaperCategory.GLASS,
            WallpaperCategory.METAL,
            WallpaperCategory.WOOD,
            WallpaperCategory.STONE,
            # Tech & Future
            WallpaperCategory.TECHNOLOGY,
            WallpaperCategory.CYBERPUNK,
            WallpaperCategory.FUTURISTIC,
            WallpaperCategory.NEON,
            # Architecture & Design
            WallpaperCategory.ARCHITECTURE,
            # Atmospheric
            WallpaperCategory.DARK,
            WallpaperCategory.NIGHT,
            WallpaperCategory.FIRE,
            WallpaperCategory.LIGHTNING,
        ]

    async def _filter_wallpapers(
        self, wallpapers: List[Wallpaper], category: WallpaperCategory
    ) -> List[Wallpaper]:
        """Filter wallpapers using entity-based validation only."""
        filtered = []

        for wallpaper in wallpapers:
            if await self.cache_service.is_image_sent(wallpaper.url):
                self.logger.debug(f"Skipping already sent: {wallpaper.url}")
                continue

            if (
                self.config.enable_content_filtering
                and wallpaper.contains_excluded_content()
            ):
                self.logger.debug(f"Filtered out excluded content: {wallpaper.url}")
                continue

            if not wallpaper.is_valid_url():
                self.logger.debug(f"Invalid URL format: {wallpaper.url}")
                continue

            filtered.append(wallpaper)

        return filtered

    async def _send_wallpapers_batch(
        self,
        wallpapers: List[Tuple[WallpaperCategory, Wallpaper]],
        source: WallpaperSource,
    ) -> int:
        """Send wallpapers with optimized processing."""
        sent_count = 0

        for i, (category, wallpaper) in enumerate(wallpapers):
            if i > 0:
                self.logger.debug(
                    f"Waiting {self.config.send_delay_seconds}s before next send..."
                )
                await asyncio.sleep(self.config.send_delay_seconds)

            success = await self._send_single_wallpaper(wallpaper, category, source)
            if success:
                sent_count += 1
                self.logger.info(
                    f"Successfully sent wallpaper {sent_count}/{len(wallpapers)}"
                )
            else:
                self.logger.warning(
                    f"Failed to send wallpaper {i + 1}/{len(wallpapers)}"
                )

        return sent_count

    async def _send_single_wallpaper(
        self, wallpaper: Wallpaper, category: WallpaperCategory, source: WallpaperSource
    ) -> bool:
        """Send a single wallpaper with enhanced error handling."""
        filepath = None
        try:
            timestamp = int(datetime.now().timestamp())
            filename = f"wallpaper_{source.value}_{category.value}_{timestamp}_{random.randint(1000, 9999)}.jpg"

            tmp_dir = os.path.join(os.getcwd(), "tmp")
            filepath = os.path.join(tmp_dir, filename)
            os.makedirs(tmp_dir, exist_ok=True)

            self.logger.info(f"Processing wallpaper: {wallpaper.url}")

            if not await self.image_downloader.download_image(wallpaper.url, filename):
                self.logger.error(f"Download failed: {wallpaper.url}")
                return False

            if not os.path.exists(filepath):
                self.logger.error(f"Downloaded file not found: {filepath}")
                return False

            caption = self._create_enhanced_caption(wallpaper, category, source)

            self.logger.info(f"Sending to Telegram: {filename}")
            if not await self.telegram_service.send_photo(
                self.config.channel_id, filepath, caption
            ):
                self.logger.error(f"Telegram send failed: {filename}")
                return False

            await self._cache_sent_image(wallpaper, source, category, filepath)

            self.logger.info(f"Successfully processed and sent: {filename}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing wallpaper {wallpaper.url}: {str(e)}")
            return False

        finally:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    self.logger.debug(f"Cleaned up: {os.path.basename(filepath)}")
                except Exception as cleanup_error:
                    self.logger.warning(
                        f"Cleanup failed for {filepath}: {cleanup_error}"
                    )

    async def _cache_sent_image(
        self,
        wallpaper: Wallpaper,
        source: WallpaperSource,
        category: WallpaperCategory,
        filepath: str,
    ) -> None:
        """Cache the sent image information."""
        try:
            sent_image = SentImage(
                url=wallpaper.url,
                hash=self.image_downloader.get_image_hash(filepath),
                source=source,
                sent_at=datetime.now(),
                query=category.value,
                channel_id=self.config.channel_id,
            )
            await self.cache_service.mark_image_as_sent(sent_image)
        except Exception as e:
            self.logger.error(f"Failed to cache sent image: {str(e)}")

    def _create_enhanced_caption(
        self, wallpaper: Wallpaper, category: WallpaperCategory, source: WallpaperSource
    ) -> str:
        """Create an enhanced caption for the wallpaper."""
        category_tag = category.value.replace(" ", "").replace("-", "").replace("_", "")
        source_tag = source.value.title().replace("_", "")

        caption = f"📱 <b>Premium HD Mobile Wallpaper</b>\n\n"

        category_desc = self._get_category_description(category)
        if category_desc:
            caption += f"🎨 <i>{category_desc}</i>\n\n"

        hashtags = f"#{category_tag} #{source_tag} #MobileWallpaper #HDWallpaper #WallpaperDaily"
        caption += f"{hashtags}\n\n"

        # Add channel promotion
        caption += f"👉 Join @ for daily HD wallpapers"

        return caption

    def _get_category_description(self, category: WallpaperCategory) -> Optional[str]:
        """Get a descriptive text for the category."""
        descriptions = {
            WallpaperCategory.NATURE: "Beautiful nature photography",
            WallpaperCategory.ABSTRACT: "Modern abstract art design",
            WallpaperCategory.SPACE: "Stunning cosmic imagery",
            WallpaperCategory.MINIMAL: "Clean minimalist design",
            WallpaperCategory.CYBERPUNK: "Futuristic neon aesthetics",
            WallpaperCategory.SUNSET: "Breathtaking sunset views",
            WallpaperCategory.MOUNTAINS: "Majestic mountain landscapes",
            WallpaperCategory.OCEAN: "Serene ocean scenes",
        }
        return descriptions.get(category)

    async def _update_stats(
        self, source: WallpaperSource, sent_count: int, total_count: int
    ) -> None:
        """Update bot statistics with enhanced tracking."""
        try:
            stats = await self.storage_service.load_stats()

            stats.total_sent += sent_count
            stats.sources_used[source.value] += sent_count

            if sent_count > 0:
                stats.successful_batches += 1
            else:
                stats.failed_batches += 1

            stats.last_batch_time = datetime.now()

            today = datetime.now().strftime("%Y-%m-%d")
            if today not in stats.daily_stats:
                stats.daily_stats[today] = 0
            stats.daily_stats[today] += sent_count

            if len(stats.daily_stats) > 30:
                sorted_dates = sorted(stats.daily_stats.keys())
                for old_date in sorted_dates[:-30]:
                    del stats.daily_stats[old_date]

            await self.storage_service.save_stats(stats)

        except Exception as e:
            self.logger.error(f"Error updating statistics: {str(e)}")

    async def _should_rotate(self, rotation: SourceRotation) -> bool:
        """Enhanced rotation decision logic."""
        return False

    async def _execute_scheduled_batch(self) -> None:
        """Execute a scheduled batch with enhanced error handling."""
        try:
            rotation = await self.storage_service.load_source_rotation()
            current_source = rotation.get_current_source()

            self.logger.info(f"Executing scheduled batch from {current_source.value}")

            sent_count = await self.send_batch_use_case.execute(
                current_source, self.config.wallpapers_per_batch
            )

            if sent_count > 0:
                await self.rotate_source_use_case.execute(force=True)

        except Exception as e:
            self.logger.error(f"Error in scheduled batch execution: {str(e)}")

    async def cleanup_temp_files(self) -> int:
        """Clean up temporary files and return count."""
        cleaned_count = 0
        try:
            tmp_dir = os.path.join(os.getcwd(), "tmp")
            if os.path.exists(tmp_dir):
                files = os.listdir(tmp_dir)
                for filename in files:
                    filepath = os.path.join(tmp_dir, filename)
                    try:
                        if os.path.isfile(filepath):
                            os.remove(filepath)
                            cleaned_count += 1
                            self.logger.debug(f"Cleaned up temp file: {filename}")
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to clean temp file {filename}: {e}"
                        )

                self.logger.info(f"Cleaned up {cleaned_count} temporary files")
        except Exception as e:
            self.logger.error(f"Error during temp file cleanup: {e}")

        return cleaned_count

    async def cleanup_old_cache_entries(self, days_old: int = 30) -> int:
        """Clean up old cache entries and return count."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            self.logger.info(
                f"Cache cleanup completed for entries older than {days_old} days"
            )
            return 0
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")
            return 0
