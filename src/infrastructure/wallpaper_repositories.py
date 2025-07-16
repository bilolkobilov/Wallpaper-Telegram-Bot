import requests
import asyncio
from typing import List, Dict, Any
from ..domain.entities import Wallpaper, WallpaperSource, WallpaperCategory
from ..domain.interfaces import WallpaperRepository, LoggingService


class PexelsWallpaperRepository(WallpaperRepository):
    """Pexels wallpaper repository implementation."""

    # =========================================================================
    # INITIALIZATION AND SETUP METHODS (High Priority)
    # These methods handle the initial setup and configuration of the repository.
    # =========================================================================

    def __init__(self, api_key: str, logger: LoggingService):
        """
        Initializes the PexelsWallpaperRepository with an API key and a logger.
        Sets the base URL for Pexels API.
        """
        self.api_key = api_key
        self.logger = logger
        self.base_url = "https://api.pexels.com/v1"

    # =========================================================================
    # CORE WALLPAPER RETRIEVAL METHODS (High Priority)
    # These methods are responsible for fetching wallpapers from Pexels.
    # =========================================================================

    async def get_wallpapers(
        self, source: WallpaperSource, category: WallpaperCategory, count: int = 10
    ) -> List[Wallpaper]:
        """
        Fetches wallpapers from Pexels based on the given source, category, and count.
        Filters for mobile-friendly wallpapers.
        """
        if source != WallpaperSource.PEXELS:
            return []

        if not self.api_key:
            self.logger.error("Pexels API key not configured")
            return []

        try:
            url = f"{self.base_url}/search"
            headers = {"Authorization": self.api_key}
            params = {
                "query": f"{category.value} mobile wallpaper portrait",
                "per_page": count,
                "orientation": "portrait",
            }

            self.logger.info(
                f"Requesting wallpapers from Pexels: {url} with params: {params}"
            )

            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            self.logger.info(
                f"Pexels response: {len(data.get('photos', []))} photos found"
            )

            wallpapers = []

            for photo in data.get("photos", []):
                wallpaper = Wallpaper(
                    url=photo["src"]["original"],
                    width=photo.get("width", 0),
                    height=photo.get("height", 0),
                    source=WallpaperSource.PEXELS,
                    description=photo.get("alt") or "",
                    author=photo.get("photographer") or "Unknown",
                )

                if wallpaper.is_mobile_friendly:
                    wallpapers.append(wallpaper)
                else:
                    self.logger.debug(
                        f"Skipping non-mobile wallpaper: {wallpaper.width}x{wallpaper.height}"
                    )

            self.logger.info(
                f"Found {len(wallpapers)} mobile wallpapers from Pexels for {category.value}"
            )
            return wallpapers

        except Exception as e:
            self.logger.error(f"Error getting wallpapers from Pexels: {str(e)}")
            return []


class UnsplashWallpaperRepository(WallpaperRepository):
    """Unsplash wallpaper repository implementation."""

    # =========================================================================
    # INITIALIZATION AND SETUP METHODS (High Priority)
    # These methods handle the initial setup and configuration of the repository.
    # =========================================================================

    def __init__(self, access_key: str, logger: LoggingService):
        """
        Initializes the UnsplashWallpaperRepository with an access key and a logger.
        Sets the base URL for Unsplash API.
        """
        self.access_key = access_key
        self.logger = logger
        self.base_url = "https://api.unsplash.com"

    # =========================================================================
    # CORE WALLPAPER RETRIEVAL METHODS (High Priority)
    # These methods are responsible for fetching wallpapers from Unsplash.
    # =========================================================================

    async def get_wallpapers(
        self, source: WallpaperSource, category: WallpaperCategory, count: int = 10
    ) -> List[Wallpaper]:
        """
        Fetches wallpapers from Unsplash based on the given source, category, and count.
        Handles API errors and retries with a simpler query if no results are found.
        Filters for mobile-friendly wallpapers based on aspect ratio.
        """
        if source != WallpaperSource.UNSPLASH:
            return []

        if not self.access_key:
            self.logger.error("Unsplash access key not configured")
            return []

        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": f"{category.value} mobile wallpaper vertical",
                "per_page": min(count, 30),
                "order_by": "relevant",
                "orientation": "portrait",
                "client_id": self.access_key,
            }

            self.logger.info(
                f"Requesting wallpapers from Unsplash: {url} with params: {params}"
            )

            response = requests.get(url, params=params, timeout=30)
            self.logger.info(f"Unsplash response status: {response.status_code}")

            if response.status_code == 401:
                self.logger.error("Unsplash API key is invalid or expired")
                return []
            elif response.status_code == 403:
                self.logger.error("Unsplash API rate limit exceeded")
                return []

            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])
            self.logger.info(f"Unsplash response: {len(results)} photos found")

            if not results:
                self.logger.warning(f"No results found for query: {params['query']}")
                params["query"] = category.value
                self.logger.info(f"Retrying with simpler query: {category.value}")

                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                self.logger.info(f"Retry response: {len(results)} photos found")

            wallpapers = []

            for photo in results:
                image_url = photo["urls"].get("regular", photo["urls"]["full"])

                actual_width = photo.get("width", 1080)
                actual_height = photo.get("height", 1920)

                user_info = photo.get("user", {})
                author_name = user_info.get("name") if user_info else "Unknown"

                wallpaper = Wallpaper(
                    url=image_url,
                    width=actual_width,
                    height=actual_height,
                    source=WallpaperSource.UNSPLASH,
                    description=photo.get("description")
                    or photo.get("alt_description")
                    or "",
                    author=author_name or "Unknown",
                )

                aspect_ratio = (
                    wallpaper.height / wallpaper.width if wallpaper.width > 0 else 0
                )
                if aspect_ratio >= 1.3:
                    wallpapers.append(wallpaper)
                    self.logger.debug(
                        f"Added wallpaper: {wallpaper.width}x{wallpaper.height} (ratio: {aspect_ratio:.2f})"
                    )
                else:
                    self.logger.debug(
                        f"Skipping non-mobile wallpaper: {wallpaper.width}x{wallpaper.height} (ratio: {aspect_ratio:.2f})"
                    )

            self.logger.info(
                f"Found {len(wallpapers)} mobile wallpapers from Unsplash for {category.value}"
            )
            return wallpapers

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Network error getting wallpapers from Unsplash: {str(e)}"
            )
            return []
        except Exception as e:
            self.logger.error(f"Error getting wallpapers from Unsplash: {str(e)}")
            return []


class WallhavenWallpaperRepository(WallpaperRepository):
    """Wallhaven wallpaper repository implementation."""

    # =========================================================================
    # INITIALIZATION AND SETUP METHODS (High Priority)
    # These methods handle the initial setup and configuration of the repository.
    # =========================================================================

    def __init__(self, api_key: str, logger: LoggingService):
        """
        Initializes the WallhavenWallpaperRepository with an API key and a logger.
        Sets the base URL for Wallhaven API.
        """
        self.api_key = api_key
        self.logger = logger
        self.base_url = "https://wallhaven.cc/api/v1"

    # =========================================================================
    # CORE WALLPAPER RETRIEVAL METHODS (High Priority)
    # These methods are responsible for fetching wallpapers from Wallhaven.
    # =========================================================================

    async def get_wallpapers(
        self, source: WallpaperSource, category: WallpaperCategory, count: int = 10
    ) -> List[Wallpaper]:
        """
        Fetches wallpapers from Wallhaven based on the given source, category, and count.
        Applies specific filters for mobile-friendly resolutions and ratios.
        """
        if source != WallpaperSource.WALLHAVEN:
            return []

        try:
            url = f"{self.base_url}/search"
            params = {
                "q": category.value,
                "categories": "101",  # General, Anime, People
                "purity": "100",  # SFW only
                "ratios": "9x16,10x16,9x18,9x19.5,9x20",  # Common mobile aspect ratios
                "resolutions": "1080x1920,1440x2560,1080x2340,1170x2532",  # Common mobile resolutions
                "sorting": "favorites",
                "order": "desc",
                "page": 1,
            }

            if self.api_key:
                params["apikey"] = self.api_key

            self.logger.info(
                f"Requesting wallpapers from Wallhaven: {url} with params: {params}"
            )

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            wallpaper_data = data.get("data", [])
            self.logger.info(
                f"Wallhaven response: {len(wallpaper_data)} wallpapers found"
            )

            wallpapers = []

            for wallpaper_info in wallpaper_data[:count]:
                resolution = wallpaper_info["resolution"].split("x")
                width = int(resolution[0])
                height = int(resolution[1])

                wallpaper = Wallpaper(
                    url=wallpaper_info["path"],
                    width=width,
                    height=height,
                    source=WallpaperSource.WALLHAVEN,
                    description="",
                    author="Community",
                )

                if wallpaper.is_mobile_friendly:
                    wallpapers.append(wallpaper)
                else:
                    self.logger.debug(
                        f"Skipping non-mobile wallpaper: {wallpaper.width}x{wallpaper.height}"
                    )

            self.logger.info(
                f"Found {len(wallpapers)} mobile wallpapers from Wallhaven for {category.value}"
            )
            return wallpapers

        except Exception as e:
            self.logger.error(f"Error getting wallpapers from Wallhaven: {str(e)}")
            return []


class CompositeWallpaperRepository(WallpaperRepository):
    """Composite wallpaper repository that combines multiple sources."""

    # =========================================================================
    # INITIALIZATION AND SETUP METHODS (High Priority)
    # These methods handle the initial setup and configuration of the repository.
    # =========================================================================

    def __init__(self, repositories: List[WallpaperRepository]):
        """
        Initializes the CompositeWallpaperRepository with a list of other wallpaper repositories.
        """
        self.repositories = repositories

    # =========================================================================
    # CORE WALLPAPER RETRIEVAL METHODS (High Priority)
    # These methods are responsible for fetching wallpapers from the composite sources.
    # =========================================================================

    async def get_wallpapers(
        self, source: WallpaperSource, category: WallpaperCategory, count: int = 10
    ) -> List[Wallpaper]:
        """
        Iterates through the configured repositories to get wallpapers from the appropriate source.
        Returns wallpapers from the first repository that successfully provides them.
        """
        for repo in self.repositories:
            wallpapers = await repo.get_wallpapers(source, category, count)
            if wallpapers:
                return wallpapers
        return []
