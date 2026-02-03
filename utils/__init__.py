"""Utility modules for the screenshot saver project."""

from .types import BoundingBox
from .word_reader import WordReader
from .text_reader import TextReader
from .screenshot_handler import ScreenshotHandler
from .openai_extractor import OpenAIExtractor
from .human_behavior import HumanBehavior, ScrollDirection
from .browser_fingerprint import get_browser_context_options, get_random_user_agent
from .chrome_manager import ChromeManager

__all__ = [
    "BoundingBox",
    "WordReader",
    "TextReader",
    "ScreenshotHandler",
    "OpenAIExtractor",
    "HumanBehavior",
    "ScrollDirection",
    "get_browser_context_options",
    "get_random_user_agent",
    "ChromeManager",
]
