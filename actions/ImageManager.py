"""
ImageManager - Centralized image loading and caching for Google Meet plugin

Handles all image loading, grayscale conversion, and caching at plugin startup.
"""

import os
from enum import Enum, auto
from PIL import Image, ImageOps
from loguru import logger as log


class ImageMode(Enum):
    """Image display modes"""
    REGULAR = auto()
    DISABLED = auto()


class ImageManager:
    """
    Manages image loading, caching, and grayscale conversion.

    All images are preloaded at plugin startup and stored in memory.
    Each image is stored in two modes: REGULAR (color) and DISABLED (grayscale).
    """

    # Class-level cache: {name__mode: PIL.Image}
    _image_cache = {}
    _initialized = False
    _assets_path = None

    @classmethod
    def initialize(cls, assets_path: str):
        """
        Initialize ImageManager and preload all plugin images.

        This should be called once during plugin initialization.

        Args:
            assets_path: Absolute path to the assets directory
        """
        if cls._initialized:
            log.warning("ImageManager already initialized, skipping")
            return

        cls._assets_path = assets_path
        log.info(f"Initializing ImageManager with assets path: {assets_path}")

        try:
            # Preload common images
            cls._preload_common_images()

            # Preload action-specific images
            cls._preload_mic_images()
            cls._preload_camera_images()
            cls._preload_hand_images()
            cls._preload_info_images()

            # Preload reaction images
            cls._preload_reaction_images()

            cls._initialized = True
            log.info(f"ImageManager initialized successfully. Loaded {len(cls._image_cache)} image variants.")
        except Exception as e:
            log.error(f"Error initializing ImageManager: {e}")
            raise

    @classmethod
    def get_image(cls, name: str, mode: ImageMode = ImageMode.REGULAR) -> Image.Image:
        """
        Get a preloaded image from cache.

        Args:
            name: Image name (e.g., "mic_on", "reaction_thumbs_up")
            mode: ImageMode.REGULAR (color) or ImageMode.DISABLED (grayscale)

        Returns:
            PIL Image object or None if not found
        """
        if not cls._initialized:
            log.error("ImageManager not initialized. Call initialize() first.")
            return None

        cache_key = f"{name}__{mode.name.lower()}"
        img = cls._image_cache.get(cache_key)

        if img is None:
            log.warning(f"Image not found in cache: {cache_key}")

        return img

    @classmethod
    def _preload_common_images(cls):
        """Preload common images used by multiple actions"""
        common_images = {
            "error": "error.png",
            "success": "success.png",
            "failure": "failure.png",
        }

        for name, filename in common_images.items():
            cls._load_image(name, filename)

        log.debug(f"Preloaded {len(common_images)} common images")

    @classmethod
    def _preload_mic_images(cls):
        """Preload microphone action images"""
        mic_images = {
            "mic_on": "mic_on.png",
            "mic_off": "mic_off.png",
        }

        for name, filename in mic_images.items():
            cls._load_image(name, filename)

        log.debug(f"Preloaded {len(mic_images)} mic images")

    @classmethod
    def _preload_camera_images(cls):
        """Preload camera action images"""
        camera_images = {
            "camera_on": "camera_on.png",
            "camera_off": "camera_off.png",
        }

        for name, filename in camera_images.items():
            cls._load_image(name, filename)

        log.debug(f"Preloaded {len(camera_images)} camera images")

    @classmethod
    def _preload_hand_images(cls):
        """Preload hand raising action images"""
        hand_images = {
            "hand_raised": "hand_raised.png",
            "hand_lowered": "hand_lowered.png",
        }

        for name, filename in hand_images.items():
            cls._load_image(name, filename)

        log.debug(f"Preloaded {len(hand_images)} hand images")

    @classmethod
    def _preload_info_images(cls):
        """Preload informational action images"""
        info_images = {
            "leave": "leave.png",
            "in_meeting": "in_meeting.png",
            "participants": "participants.png",
        }

        for name, filename in info_images.items():
            cls._load_image(name, filename)

        log.debug(f"Preloaded {len(info_images)} info images")

    @classmethod
    def _preload_reaction_images(cls):
        """Preload all reaction emoji images"""
        reactions = [
            "sparkling_heart",
            "thumbs_up",
            "celebrate",
            "applause",
            "laugh",
            "surprised",
            "sad",
            "thinking",
            "thumbs_down",
        ]

        for reaction_id in reactions:
            name = f"reaction_{reaction_id}"
            filename = f"{reaction_id}.png"
            cls._load_image_from_subdir(name, "reactions", filename)

        log.debug(f"Preloaded {len(reactions)} reaction images")

    @classmethod
    def _load_image(cls, name: str, filename: str):
        """
        Load an image from assets directory and create both regular and disabled variants.

        Args:
            name: Cache key name (e.g., "mic_on")
            filename: Filename in assets directory (e.g., "mic_on.png")
        """
        path = os.path.join(cls._assets_path, filename)

        if not os.path.exists(path):
            log.warning(f"Image file not found: {path}")
            return

        try:
            with Image.open(path) as img:
                # Store regular (color) version
                regular_img = img.copy()
                cls._image_cache[f"{name}__regular"] = regular_img

                # Create and store disabled (grayscale) version
                disabled_img = cls._convert_to_grayscale(regular_img)
                cls._image_cache[f"{name}__disabled"] = disabled_img

                log.debug(f"Loaded image: {name} from {filename}")
        except Exception as e:
            log.error(f"Error loading image {filename}: {e}")

    @classmethod
    def _load_image_from_subdir(cls, name: str, subdir: str, filename: str):
        """
        Load an image from a subdirectory and create both regular and disabled variants.

        Args:
            name: Cache key name (e.g., "reaction_thumbs_up")
            subdir: Subdirectory name (e.g., "reactions")
            filename: Filename (e.g., "thumbs_up.png")
        """
        path = os.path.join(cls._assets_path, subdir, filename)

        if not os.path.exists(path):
            log.warning(f"Image file not found: {path}")
            return

        try:
            with Image.open(path) as img:
                # Store regular (color) version
                regular_img = img.copy()
                cls._image_cache[f"{name}__regular"] = regular_img

                # Create and store disabled (grayscale) version
                disabled_img = cls._convert_to_grayscale(regular_img)
                cls._image_cache[f"{name}__disabled"] = disabled_img

                log.debug(f"Loaded image: {name} from {subdir}/{filename}")
        except Exception as e:
            log.error(f"Error loading image {subdir}/{filename}: {e}")

    @staticmethod
    def _convert_to_grayscale(img: Image.Image) -> Image.Image:
        """
        Convert an image to grayscale.

        Args:
            img: PIL Image object

        Returns:
            Grayscale PIL Image object
        """
        # Convert to grayscale and back to RGB to maintain compatibility
        # This preserves the RGBA mode if original has alpha channel
        if img.mode == 'RGBA':
            # Handle images with alpha channel
            grayscale = ImageOps.grayscale(img)
            # Convert back to RGBA
            result = Image.new('RGBA', img.size)
            result.paste(grayscale.convert('RGB'), (0, 0))
            # Preserve alpha channel
            result.putalpha(img.getchannel('A'))
            return result
        else:
            # For RGB images, convert to grayscale and back to RGB
            grayscale = ImageOps.grayscale(img)
            return grayscale.convert('RGB')
