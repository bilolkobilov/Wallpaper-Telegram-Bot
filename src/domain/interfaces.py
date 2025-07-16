from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import (
    Wallpaper,
    WallpaperSource,
    WallpaperCategory,
    SentImage,
    BotStats,
    SourceRotation,
)


# =========================================================================
# REPOSITORIES (Data Access Layer)
# These abstract classes define interfaces for interacting with data storage.
# =========================================================================


class WallpaperRepository(ABC):
    """Abstract wallpaper repository."""

    @abstractmethod
    async def get_wallpapers(
        self, source: WallpaperSource, category: WallpaperCategory, count: int = 10
    ) -> List[Wallpaper]:
        """Get wallpapers from source."""
        pass


class ImageDownloader(ABC):
    """Abstract image downloader."""

    @abstractmethod
    async def download_image(self, url: str, filename: str) -> bool:
        """Download image from URL."""
        pass

    @abstractmethod
    def get_image_hash(self, filepath: str) -> str:
        """Calculate image hash."""
        pass


# =========================================================================
# SERVICES (External System Interactions)
# These abstract classes define interfaces for interacting with external services.
# =========================================================================


class TelegramService(ABC):
    """Abstract Telegram service."""

    @abstractmethod
    async def send_photo(self, chat_id: str, photo_path: str, caption: str) -> bool:
        """Send photo to Telegram."""
        pass

    @abstractmethod
    async def send_message(
        self, chat_id: str, text: str, parse_mode: str = "HTML"
    ) -> bool:
        """Send message to Telegram."""
        pass


class StorageService(ABC):
    """Abstract storage service."""

    @abstractmethod
    async def save_sent_images(self, images: List[SentImage]) -> None:
        """Save sent images."""
        pass

    @abstractmethod
    async def load_sent_images(self) -> List[SentImage]:
        """Load sent images."""
        pass

    @abstractmethod
    async def save_stats(self, stats: BotStats) -> None:
        """Save bot statistics."""
        pass

    @abstractmethod
    async def load_stats(self) -> BotStats:
        """Load bot statistics."""
        pass

    @abstractmethod
    async def save_source_rotation(self, rotation: SourceRotation) -> None:
        """Save source rotation state."""
        pass

    @abstractmethod
    async def load_source_rotation(self) -> SourceRotation:
        """Load source rotation state."""
        pass


class CacheService(ABC):
    """Abstract cache service."""

    @abstractmethod
    async def is_image_sent(self, url: str) -> bool:
        """Check if image was already sent."""
        pass

    @abstractmethod
    async def mark_image_as_sent(self, sent_image: SentImage) -> None:
        """Mark image as sent."""
        pass


class LoggingService(ABC):
    """Abstract logging service."""

    @abstractmethod
    def info(self, message: str) -> None:
        """Log info message."""
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        """Log warning message."""
        pass

    @abstractmethod
    def error(self, message: str) -> None:
        """Log error message."""
        pass

    @abstractmethod
    def debug(self, message: str) -> None:
        """Log debug message."""
        pass


class NotificationService(ABC):
    """Abstract notification service."""

    @abstractmethod
    async def notify_admin(self, message: str) -> None:
        """Send notification to admin."""
        pass

    @abstractmethod
    async def notify_batch_complete(
        self, sent_count: int, source: WallpaperSource
    ) -> None:
        """Notify batch completion."""
        pass

    @abstractmethod
    async def notify_error(self, error: str) -> None:
        """Notify about error."""
        pass
