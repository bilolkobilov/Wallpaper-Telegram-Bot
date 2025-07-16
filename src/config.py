import os
from typing import Dict
from dotenv import load_dotenv
from .domain.entities import BotConfiguration

load_dotenv()


class ConfigurationManager:
    """Manages the configuration settings for the bot, loaded from environment variables."""

    # =========================================================================
    # INITIALIZATION AND SETUP METHODS (High Priority)
    # These methods handle the initial loading of configuration from environment variables.
    # =========================================================================

    def __init__(self):
        """
        Initializes the ConfigurationManager by loading all necessary environment variables.
        """
        self.bot_token = os.getenv("BOT_TOKEN")
        self.channel_id = os.getenv("CHANNEL_ID")
        self.admin_user_id = int(os.getenv("ADMIN_USER_ID"))

        self.api_keys = {
            "pexels": os.getenv("PEXELS_API_KEY"),
            "unsplash": os.getenv("UNSPLASH_API_KEY"),
            "wallhaven": os.getenv("WALLHAVEN_API_KEY"),
        }

        self.wallpapers_per_batch = int(os.getenv("WALLPAPERS_PER_BATCH"))
        self.batch_interval_hours = int(os.getenv("BATCH_INTERVAL_HOURS"))
        self.send_delay_seconds = int(os.getenv("SEND_DELAY_SECONDS"))
        self.max_retries = int(os.getenv("MAX_RETRIES"))

    # =========================================================================
    # CONFIGURATION RETRIEVAL METHODS (High Priority)
    # These methods provide access to the loaded configuration settings.
    # =========================================================================

    def get_bot_configuration(self) -> BotConfiguration:
        """
        Returns a BotConfiguration object populated with the loaded settings.
        """
        return BotConfiguration(
            bot_token=self.bot_token,
            channel_id=self.channel_id,
            admin_user_id=self.admin_user_id,
            wallpapers_per_batch=self.wallpapers_per_batch,
            batch_interval_hours=self.batch_interval_hours,
            send_delay_seconds=self.send_delay_seconds,
            max_retries=self.max_retries,
            api_keys=self.api_keys,
        )

    # =========================================================================
    # CONFIGURATION VALIDATION METHODS (Medium Priority)
    # These methods ensure the loaded configuration values are within acceptable ranges.
    # =========================================================================

    def validate_configuration(self, config: BotConfiguration) -> None:
        """
        Validates the provided BotConfiguration object to ensure all values are within expected ranges.
        Raises ValueError for any invalid configuration settings.
        """
        if config.wallpapers_per_batch < 1 or config.wallpapers_per_batch > 10:
            raise ValueError("WALLPAPERS_PER_BATCH must be between 1 and 10")

        if config.batch_interval_hours < 1 or config.batch_interval_hours > 24:
            raise ValueError("BATCH_INTERVAL_HOURS must be between 1 and 24")

        if config.send_delay_seconds < 1 or config.send_delay_seconds > 300:
            raise ValueError("SEND_DELAY_SECONDS must be between 1 and 300")

        if config.max_retries < 1 or config.max_retries > 10:
            raise ValueError("MAX_RETRIES must be between 1 and 10")
