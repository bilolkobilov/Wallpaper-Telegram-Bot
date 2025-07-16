import json
import os
from datetime import datetime
from typing import List, Dict, Any
from ..domain.entities import SentImage, BotStats, SourceRotation, WallpaperSource
from ..domain.interfaces import StorageService, LoggingService


class JsonStorageService(StorageService):
    """JSON file-based storage service implementation."""

    # =========================================================================
    # INITIALIZATION AND SETUP METHODS (High Priority)
    # These methods handle the initial setup and configuration of the storage service.
    # =========================================================================

    def __init__(self, logger: LoggingService):
        """
        Initializes the JsonStorageService with a logger.
        Sets up file paths for different data types and ensures the data directory exists.
        """
        self.logger = logger
        self.sent_images_file = "data/sent_images.json"
        self.stats_file = "data/bot_stats.json"
        self.source_rotation_file = "data/source_rotation.json"
        self._ensure_data_directory()

    def _ensure_data_directory(self):
        """
        Ensures that the 'data' directory for storing JSON files exists.
        Creates it if it doesn't.
        """
        os.makedirs("data", exist_ok=True)

    # =========================================================================
    # DATA SAVING METHODS (High Priority)
    # These methods are responsible for persisting application data to JSON files.
    # =========================================================================

    async def save_sent_images(self, images: List[SentImage]) -> None:
        """
        Saves a list of SentImage objects to the 'sent_images.json' file.
        Serializes the image data into a dictionary format before saving.
        """
        try:
            data = {}
            for image in images:
                data[image.url] = {
                    "hash": image.hash,
                    "source": image.source.value,
                    "sent_at": image.sent_at.isoformat(),
                    "query": image.query,
                    "channel_id": image.channel_id,
                }

            with open(self.sent_images_file, "w") as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"Saved {len(images)} sent images")

        except Exception as e:
            self.logger.error(f"Error saving sent images: {str(e)}")

    async def save_stats(self, stats: BotStats) -> None:
        """
        Saves the bot's statistics (BotStats object) to the 'bot_stats.json' file.
        Serializes the stats data, including datetime objects, to JSON.
        """
        try:
            data = {
                "total_sent": stats.total_sent,
                "successful_batches": stats.successful_batches,
                "failed_batches": stats.failed_batches,
                "sources_used": stats.sources_used,
                "queries_used": stats.queries_used,
                "daily_stats": stats.daily_stats,
                "errors": stats.errors,
                "start_time": stats.start_time.isoformat(),
                "last_batch_time": stats.last_batch_time.isoformat()
                if stats.last_batch_time
                else None,
            }

            with open(self.stats_file, "w") as f:
                json.dump(data, f, indent=2)

            self.logger.info("Bot statistics saved")

        except Exception as e:
            self.logger.error(f"Error saving stats: {str(e)}")

    async def save_source_rotation(self, rotation: SourceRotation) -> None:
        """
        Saves the source rotation state (SourceRotation object) to the 'source_rotation.json' file.
        Includes the current source index and last rotation time.
        """
        try:
            data = {
                "current_source_index": rotation.current_source_index,
                "last_rotation_time": rotation.last_rotation_time.isoformat(),
            }

            with open(self.source_rotation_file, "w") as f:
                json.dump(data, f, indent=2)

            self.logger.info("Source rotation state saved")

        except Exception as e:
            self.logger.error(f"Error saving source rotation: {str(e)}")

    # =========================================================================
    # DATA LOADING METHODS (High Priority)
    # These methods are responsible for loading application data from JSON files.
    # =========================================================================

    async def load_sent_images(self) -> List[SentImage]:
        """
        Loads a list of SentImage objects from the 'sent_images.json' file.
        Handles cases where the file does not exist and deserializes the data.
        """
        try:
            if not os.path.exists(self.sent_images_file):
                return []

            with open(self.sent_images_file, "r") as f:
                data = json.load(f)

            images = []
            for url, image_data in data.items():
                image = SentImage(
                    url=url,
                    hash=image_data["hash"],
                    source=WallpaperSource(image_data["source"]),
                    sent_at=datetime.fromisoformat(image_data["sent_at"]),
                    query=image_data["query"],
                    channel_id=image_data["channel_id"],
                )
                images.append(image)

            self.logger.info(f"Loaded {len(images)} sent images")
            return images

        except Exception as e:
            self.logger.error(f"Error loading sent images: {str(e)}")
            return []

    async def load_stats(self) -> BotStats:
        """
        Loads the bot's statistics (BotStats object) from the 'bot_stats.json' file.
        Returns a default BotStats object if the file does not exist or an error occurs.
        """
        try:
            if not os.path.exists(self.stats_file):
                return BotStats()

            with open(self.stats_file, "r") as f:
                data = json.load(f)

            stats = BotStats(
                total_sent=data.get("total_sent", 0),
                successful_batches=data.get("successful_batches", 0),
                failed_batches=data.get("failed_batches", 0),
                sources_used=data.get("sources_used", {}),
                queries_used=data.get("queries_used", {}),
                daily_stats=data.get("daily_stats", {}),
                errors=data.get("errors", []),
                start_time=datetime.fromisoformat(data["start_time"])
                if data.get("start_time")
                else datetime.now(),
                last_batch_time=datetime.fromisoformat(data["last_batch_time"])
                if data.get("last_batch_time")
                else None,
            )

            self.logger.info("Bot statistics loaded")
            return stats

        except Exception as e:
            self.logger.error(f"Error loading stats: {str(e)}")
            return BotStats()

    async def load_source_rotation(self) -> SourceRotation:
        """
        Loads the source rotation state (SourceRotation object) from the 'source_rotation.json' file.
        Returns a default SourceRotation object if the file does not exist or an error occurs.
        """
        try:
            if not os.path.exists(self.source_rotation_file):
                return SourceRotation()

            with open(self.source_rotation_file, "r") as f:
                data = json.load(f)

            rotation = SourceRotation(
                current_source_index=data.get("current_source_index", 0),
                last_rotation_time=datetime.fromisoformat(data["last_rotation_time"])
                if data.get("last_rotation_time")
                else datetime.now(),
            )

            self.logger.info("Source rotation state loaded")
            return rotation

        except Exception as e:
            self.logger.error(f"Error loading source rotation: {str(e)}")
            return SourceRotation()
