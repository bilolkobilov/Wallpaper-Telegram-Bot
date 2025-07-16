import os
import hashlib
import shutil
import requests
from PIL import Image
from ..domain.interfaces import ImageDownloader, LoggingService


class ImageDownloaderImpl(ImageDownloader):
    """Image downloader implementation."""

    # =========================================================================
    # INITIALIZATION AND SETUP METHODS (High Priority)
    # These methods handle the initial setup and configuration of the downloader.
    # =========================================================================

    def __init__(self, logger: LoggingService):
        """
        Initializes the ImageDownloaderImpl with a logger.
        Ensures the temporary directory exists.
        """
        self.logger = logger
        self.tmp_dir = os.path.join(os.getcwd(), "tmp")
        self._ensure_tmp_directory()

    def _ensure_tmp_directory(self):
        """
        Ensures that the temporary directory for image downloads exists.
        Creates it if it doesn't.
        """
        os.makedirs(self.tmp_dir, exist_ok=True)
        self.logger.info(f"Temporary directory ensured: {self.tmp_dir}")

    # =========================================================================
    # CORE IMAGE HANDLING METHODS (High Priority)
    # These methods are responsible for the primary image download and processing.
    # =========================================================================

    async def download_image(self, url: str, filename: str) -> bool:
        """
        Downloads an image from the given URL to the temporary directory.
        Includes error handling, content type validation, and progress logging.
        After download, it verifies and optimizes the image.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            self.logger.info(f"Downloading image from: {url}")

            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                self.logger.error(f"Invalid content type: {content_type}")
                return False

            clean_filename = os.path.basename(filename)
            filepath = os.path.join(self.tmp_dir, clean_filename)

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:
                                self.logger.debug(f"Download progress: {progress:.1f}%")

            self.logger.info(f"Downloaded {downloaded} bytes")

            if not self._verify_and_optimize_image(filepath):
                if os.path.exists(filepath):
                    os.remove(filepath)
                return False

            self.logger.info(f"Successfully downloaded and verified image: {filename}")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error downloading image from {url}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error downloading image from {url}: {str(e)}")
            return False

    def _verify_and_optimize_image(self, filepath: str) -> bool:
        """
        Verifies the downloaded image for valid dimensions and aspect ratio.
        Optimizes the image by converting it to JPEG if it's not already.
        """
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                self.logger.info(f"Image dimensions: {width}x{height}")

                if width <= 0 or height <= 0:
                    self.logger.error("Invalid image dimensions")
                    return False

                if width < 500 or height < 800:
                    self.logger.warning(f"Image too small: {width}x{height}")
                    return False

                aspect_ratio = height / width if width > 0 else 0
                if aspect_ratio < 1.2:
                    self.logger.warning(
                        f"Image aspect ratio not mobile-friendly: {aspect_ratio:.2f} ({width}x{height})"
                    )

                if img.format != "JPEG":
                    self.logger.info(f"Converting from {img.format} to JPEG")
                    rgb_img = img.convert("RGB")
                    rgb_img.save(filepath, "JPEG", quality=95, optimize=True)
                    self.logger.info("Converted image to high quality JPEG")

                with Image.open(filepath) as verify_img:
                    verify_img.verify()

                return True

        except Exception as e:
            self.logger.error(f"Error verifying image {filepath}: {str(e)}")
            return False

    # =========================================================================
    # UTILITY AND HELPER METHODS (Medium Priority)
    # These methods provide supplementary functionalities like hashing and file size.
    # =========================================================================

    def get_image_hash(self, filepath: str) -> str:
        """
        Calculates the MD5 hash of the image file.
        Useful for checking image integrity or uniqueness.
        """
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {filepath}: {str(e)}")
            return ""

    def get_file_size(self, filepath: str) -> int:
        """
        Gets the size of the file in bytes.
        """
        try:
            return os.path.getsize(filepath)
        except Exception as e:
            self.logger.error(f"Error getting file size for {filepath}: {str(e)}")
            return 0

    # =========================================================================
    # CLEANUP METHODS (Low Priority)
    # These methods are for maintaining the temporary directory.
    # =========================================================================

    def cleanup_tmp_directory(self):
        """
        Cleans up the temporary directory by removing all its contents.
        """
        try:
            if os.path.exists(self.tmp_dir):
                shutil.rmtree(self.tmp_dir)
                self.logger.info(f"Cleaned up temporary directory: {self.tmp_dir}")
        except Exception as e:
            self.logger.error(f"Error cleaning up temporary directory: {str(e)}")
