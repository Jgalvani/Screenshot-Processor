"""Application settings and configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Centralized configuration settings for the application."""

    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    OUTPUT_DIR = BASE_DIR / "output"

    # OpenAI configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    SKIP_EXTRACTION = os.getenv("SKIP_EXTRACTION", "false").lower() == "true"

    # Browser configuration
    BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
    BROWSER_SLOW_MO = int(os.getenv("BROWSER_SLOW_MO", "100"))
    VIEWPORT_WIDTH = int(os.getenv("VIEWPORT_WIDTH", "1920"))
    VIEWPORT_HEIGHT = int(os.getenv("VIEWPORT_HEIGHT", "1080"))

    # Screenshot configuration
    SCREENSHOT_FORMAT = os.getenv("SCREENSHOT_FORMAT", "png")
    SCREENSHOT_FULL_PAGE = os.getenv("SCREENSHOT_FULL_PAGE", "false").lower() == "true"

    # Human-like behavior delays (in milliseconds)
    MIN_ACTION_DELAY = int(os.getenv("MIN_ACTION_DELAY", "100"))
    MAX_ACTION_DELAY = int(os.getenv("MAX_ACTION_DELAY", "500"))
    PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "5000"))

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required settings and return list of errors."""
        errors = []
        if not cls.SKIP_EXTRACTION and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set in environment variables")
        return errors
