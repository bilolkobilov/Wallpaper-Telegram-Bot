from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re
import asyncio
import os
import random


# =========================================================================
# ENUMERATIONS (Categorization and Source Definitions)
# These enums define the types of data used throughout the application.
# =========================================================================


class WallpaperSource(Enum):
    """Supported wallpaper sources."""

    PEXELS = "pexels"
    UNSPLASH = "unsplash"
    WALLHAVEN = "wallhaven"


class WallpaperCategory(Enum):
    """Wallpaper categories (filtered to exclude humans and certain animals)."""

    NATURE = "nature"
    ABSTRACT = "abstract"
    ANIME = "anime"
    CITY = "city"
    TECHNOLOGY = "technology"
    MINIMAL = "minimal"
    DARK = "dark"
    LANDSCAPE = "landscape"
    NEON = "neon"
    AESTHETIC = "aesthetic"
    GRADIENT = "gradient"
    MOUNTAINS = "mountains"
    NIGHT = "night"
    FOREST = "forest"
    SPACE = "space"
    CARS = "cars"
    DESIGN = "design"
    SUNSET = "sunset"
    OCEAN = "ocean"
    SKY = "sky"
    CLOUDS = "clouds"
    FLOWERS = "flowers"
    ARCHITECTURE = "architecture"
    URBAN = "urban"
    VINTAGE = "vintage"
    GEOMETRIC = "geometric"
    COLORFUL = "colorful"
    BLACK_AND_WHITE = "black and white"
    ARTISTIC = "artistic"
    FUTURISTIC = "futuristic"
    GALAXY = "galaxy"
    BEACH = "beach"
    WINTER = "winter"
    AUTUMN = "autumn"
    SPRING = "spring"
    SUMMER = "summer"
    MACRO = "macro"
    STREET = "street"
    MINIMALIST = "minimalist"
    CYBERPUNK = "cyberpunk"
    RETROWAVE = "retrowave"
    SYNTHWAVE = "synthwave"
    DIGITAL_ART = "digital art"
    TEXTURES = "textures"
    PATTERNS = "patterns"
    WATER = "water"
    FIRE = "fire"
    LIGHTNING = "lightning"
    CRYSTALS = "crystals"
    GLASS = "glass"
    METAL = "metal"
    WOOD = "wood"
    STONE = "stone"
    FANTASY = "fantasy"
    SCI_FI = "sci-fi"
    STEAMPUNK = "steampunk"
    VAPORWAVE = "vaporwave"
    OUTRUN = "outrun"


# =========================================================================
# DATA MODELS (Entities)
# These dataclasses define the structure of data objects used throughout the system.
# =========================================================================


@dataclass
class Wallpaper:
    """Wallpaper entity."""

    url: str
    width: int
    height: int
    source: WallpaperSource
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Ensure description and author are not None."""
        if self.description is None:
            self.description = ""
        if self.author is None:
            self.author = ""
        if self.tags is None:
            self.tags = []

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio."""
        return self.height / self.width if self.width > 0 else 0

    @property
    def is_mobile_friendly(self) -> bool:
        """Check if wallpaper is mobile-friendly."""
        return self.aspect_ratio >= 1.2 and self.height >= 800

    def is_valid_url(self) -> bool:
        """Check if URL is valid."""
        try:
            if not self.url:
                return False

            # Basic URL validation
            url_pattern = re.compile(
                r"^https?://"
                r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
                r"localhost|"
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                r"(?::\d+)?"
                r"(?:/?|[/?]\S+)$",
                re.IGNORECASE,
            )

            return bool(url_pattern.match(self.url))
        except:
            return False

    def contains_excluded_content(self) -> bool:
        """Check if wallpaper contains excluded content - SIMPLIFIED VERSION."""

        excluded_keywords = [
            # Direct human references
            "person",
            "people",
            "human",
            "man",
            "woman",
            "girl",
            "boy",
            "face",
            "portrait",
            "model",
            "selfie",
            "crowd",
            "group",
            "children"
            # Body parts
            "hand",
            "hands",
            "eye",
            "eyes",
            "body",
            "finger",
            "fingers",
            # Common animals (keep only obvious ones)
            "dog",
            "cat",
            "bird",
            "horse",
            "cow",
            "pig",
            "sheep",
            # Religious content (keep only obvious ones)
            "church",
            "temple",
            "mosque",
            "cross",
            "jesus",
            "buddha",
            # Obvious text content
            "text",
            "writing",
            "letter",
            "letters",
            "sign",
            "signage",
            "billboard",
            "poster",
            "graffiti",
            # Adult content
            "nude",
            "naked",
            "sexy",
            "bikini",
            "lingerie",
            # Violence
            "violence",
            "blood",
            "weapon",
            "gun",
            "knife",
            "fight",
        ]

        try:
            description = (self.description or "").lower()
            author = (self.author or "").lower()
            tags = [tag.lower() for tag in (self.tags or [])]

            all_text = f"{description} {author} {' '.join(tags)}"

            for keyword in excluded_keywords:
                pattern = r"\b" + re.escape(keyword) + r"\b"
                if re.search(pattern, all_text, re.IGNORECASE):
                    return True

            text_patterns = [
                r"[\u3040-\u309F]",  # Hiragana
                r"[\u30A0-\u30FF]",  # Katakana
                r"[\u4E00-\u9FFF]",  # CJK Unified Ideographs
                r"[\u0590-\u05FF]",  # Hebrew
                r"[\u0600-\u06FF]",  # Arabic
            ]

            for pattern in text_patterns:
                if re.search(pattern, all_text, re.UNICODE):
                    return True

            return False

        except Exception as e:
            return False

    def is_valid(self) -> bool:
        """Check if wallpaper is valid."""
        return (
            bool(self.url)
            and self.width > 0
            and self.height > 0
            and self.is_valid_url()
            and self.is_mobile_friendly
            and not self.contains_excluded_content()
        )


@dataclass
class SentImage:
    """Sent image tracking entity."""

    url: str
    hash: str
    source: WallpaperSource
    sent_at: datetime
    query: str
    channel_id: str


@dataclass
class BotStats:
    """Bot statistics entity."""

    total_sent: int = 0
    successful_batches: int = 0
    failed_batches: int = 0
    sources_used: Dict[str, int] = field(default_factory=dict)
    queries_used: Dict[str, int] = field(default_factory=dict)
    daily_stats: Dict[str, int] = field(default_factory=dict)
    errors: List[Dict] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    last_batch_time: Optional[datetime] = None
    filtered_images: int = 0

    def __post_init__(self):
        """Initialize default values."""
        if not self.sources_used:
            self.sources_used = {source.value: 0 for source in WallpaperSource}


@dataclass
class SourceRotation:
    """Source rotation state entity."""

    current_source_index: int = 0
    last_rotation_time: datetime = field(default_factory=datetime.now)

    def get_current_source(self) -> WallpaperSource:
        """Get current source."""
        sources = list(WallpaperSource)
        return sources[self.current_source_index % len(sources)]

    def get_next_source(self) -> WallpaperSource:
        """Get next source."""
        sources = list(WallpaperSource)
        next_index = (self.current_source_index + 1) % len(sources)
        return sources[next_index]

    def rotate_to_next(self) -> WallpaperSource:
        """Rotate to next source."""
        sources = list(WallpaperSource)
        self.current_source_index = (self.current_source_index + 1) % len(sources)
        self.last_rotation_time = datetime.now()
        return self.get_current_source()


@dataclass
class BotConfiguration:
    """Bot configuration entity."""

    bot_token: str
    channel_id: str
    admin_user_id: int
    wallpapers_per_batch: int = 4
    batch_interval_hours: int = 2
    send_delay_seconds: int = 10
    max_retries: int = 3
    api_keys: Dict[str, str] = field(default_factory=dict)
    enable_content_filtering: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if not self.bot_token:
            raise ValueError("Bot token is required")
        if not self.channel_id:
            raise ValueError("Channel ID is required")
        if not self.admin_user_id:
            raise ValueError("Admin user ID is required")


# =========================================================================
# USE CASES (Business Logic)
# These classes encapsulate specific business logic flows.
# =========================================================================


class SendWallpaperBatchUseCase:
    """Use case for sending a batch of wallpapers with enhanced filtering and performance."""

    def __init__(
        self,
        config: BotConfiguration,
        wallpaper_repo,  # WallpaperRepository
        image_downloader,  # ImageDownloader
        telegram_service,  # TelegramService
        storage_service,  # StorageService
        cache_service,  # CacheService
        logger,  # LoggingService
        notification_service,  # NotificationService
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

    # =========================================================================
    # HELPER METHODS (Internal Logic for Use Cases)
    # These methods support the main use case execution.
    # =========================================================================

    async def _get_approved_wallpapers(
        self, source: WallpaperSource, count: int
    ) -> List[Tuple[WallpaperCategory, Wallpaper]]:
        """Get approved wallpapers using optimized filtering strategy."""
        approved_wallpapers = []

        safe_categories = self._get_safe_categories()

        max_attempts = min(30, count * 2)
        batch_size = min(20, count * 3)
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
                await asyncio.sleep(0.2)

        self.logger.info(
            f"Approved {len(approved_wallpapers)} wallpapers after {attempts} attempts"
        )
        return approved_wallpapers

    def _get_safe_categories(self) -> List[WallpaperCategory]:
        """Get list of safe wallpaper categories optimized for quality content."""
        return [
            # Nature & Landscapes (most likely to work)
            WallpaperCategory.NATURE,
            WallpaperCategory.LANDSCAPE,
            WallpaperCategory.MOUNTAINS,
            WallpaperCategory.FOREST,
            WallpaperCategory.OCEAN,
            WallpaperCategory.WATER,
            WallpaperCategory.SKY,
            WallpaperCategory.CLOUDS,
            WallpaperCategory.SUNSET,
            WallpaperCategory.BEACH,
            # Abstract & Minimal (safe content)
            WallpaperCategory.ABSTRACT,
            WallpaperCategory.MINIMAL,
            WallpaperCategory.GEOMETRIC,
            WallpaperCategory.GRADIENT,
            WallpaperCategory.PATTERNS,
            # Space & Cosmic
            WallpaperCategory.SPACE,
            WallpaperCategory.GALAXY,
            # Seasonal
            WallpaperCategory.WINTER,
            WallpaperCategory.AUTUMN,
            WallpaperCategory.SPRING,
            WallpaperCategory.SUMMER,
            # Materials & Textures
            WallpaperCategory.TEXTURES,
            WallpaperCategory.CRYSTALS,
            WallpaperCategory.GLASS,
            WallpaperCategory.METAL,
            WallpaperCategory.WOOD,
            WallpaperCategory.STONE,
            # Atmospheric
            WallpaperCategory.DARK,
            WallpaperCategory.NIGHT,
            WallpaperCategory.FIRE,
            WallpaperCategory.LIGHTNING,
            # Architecture & Design
            WallpaperCategory.ARCHITECTURE,
            WallpaperCategory.URBAN,
            # Tech & Future
            WallpaperCategory.TECHNOLOGY,
            WallpaperCategory.FUTURISTIC,
            WallpaperCategory.NEON,
            # Art styles
            WallpaperCategory.DIGITAL_ART,
            WallpaperCategory.ARTISTIC,
            WallpaperCategory.COLORFUL,
            WallpaperCategory.BLACK_AND_WHITE,
        ]

    async def _filter_wallpapers(
        self, wallpapers: List[Wallpaper], category: WallpaperCategory
    ) -> List[Wallpaper]:
        """Filter wallpapers using entity-based validation."""
        filtered = []

        for wallpaper in wallpapers:
            try:
                if await self.cache_service.is_image_sent(wallpaper.url):
                    self.logger.debug(f"Skipping already sent: {wallpaper.url}")
                    continue

                if not wallpaper.is_valid():
                    self.logger.debug(f"Wallpaper validation failed: {wallpaper.url}")
                    continue

                filtered.append(wallpaper)
                self.logger.debug(f"Wallpaper passed all filters: {wallpaper.url}")

            except Exception as e:
                self.logger.error(
                    f"Error filtering wallpaper {wallpaper.url}: {str(e)}"
                )
                continue

        self.logger.info(
            f"Filtered {len(filtered)} wallpapers from {len(wallpapers)} candidates"
        )
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

        # Add category-specific description
        category_desc = self._get_category_description(category)
        if category_desc:
            caption += f"🎨 <i>{category_desc}</i>\n\n"

        # Add hashtags
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
            WallpaperCategory.LANDSCAPE: "Stunning landscape photography",
            WallpaperCategory.FOREST: "Peaceful forest scenes",
            WallpaperCategory.GALAXY: "Amazing galaxy and nebula views",
            WallpaperCategory.GEOMETRIC: "Clean geometric patterns",
            WallpaperCategory.GRADIENT: "Smooth gradient backgrounds",
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
            stats.filtered_images += total_count - sent_count

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


# =========================================================================
# DEBUGGING AND UTILITY FUNCTIONS
# Functions that provide supplementary functionality, often for testing or debugging.
# =========================================================================


def debug_wallpaper_validation(wallpaper: Wallpaper) -> dict:
    """Debug function to check why a wallpaper might be rejected."""
    results = {
        "url_valid": wallpaper.is_valid_url(),
        "mobile_friendly": wallpaper.is_mobile_friendly,
        "contains_excluded": wallpaper.contains_excluded_content(),
        "width": wallpaper.width,
        "height": wallpaper.height,
        "aspect_ratio": wallpaper.aspect_ratio,
        "description": wallpaper.description,
        "tags": wallpaper.tags,
        "overall_valid": wallpaper.is_valid(),
    }
    return results
