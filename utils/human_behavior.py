"""Human-like browser behavior simulation utilities."""

import random
import time
from enum import Enum

from playwright.sync_api import Page

from config import Settings


class ScrollDirection(Enum):
    """Enum for scroll directions."""
    UP = "up"
    DOWN = "down"


class HumanBehavior:
    """Simulates human-like browser interactions."""

    def __init__(self, page: Page):
        """
        Initialize HumanBehavior with a Playwright page.

        Args:
            page: Playwright Page object
        """
        self.page = page

    def random_delay(
        self,
        min_ms: int | None = None,
        max_ms: int | None = None
    ) -> None:
        """
        Wait for a random duration to simulate human timing.

        Args:
            min_ms: Minimum delay in milliseconds
            max_ms: Maximum delay in milliseconds
        """
        min_delay = min_ms or Settings.MIN_ACTION_DELAY
        max_delay = max_ms or Settings.MAX_ACTION_DELAY
        delay = random.randint(min_delay, max_delay) / 1000
        time.sleep(delay)

    def human_scroll(
        self,
        direction: ScrollDirection = ScrollDirection.DOWN,
        amount: int | None = None
    ) -> None:
        """
        Scroll the page in a human-like manner.

        Args:
            direction: Scroll direction (ScrollDirection.UP or ScrollDirection.DOWN)
            amount: Scroll amount in pixels (randomized if not specified)
        """
        if amount is None:
            amount = random.randint(100, 400)

        if direction == ScrollDirection.UP:
            amount = -amount

        self.page.mouse.wheel(0, amount)
        self.random_delay(200, 500)

    def human_move_to(self, x: int, y: int) -> None:
        """
        Move mouse to coordinates with human-like motion.

        Args:
            x: Target X coordinate
            y: Target Y coordinate
        """
        # Get current position (approximate from viewport center)
        viewport = self.page.viewport_size
        if viewport:
            current_x = viewport["width"] // 2
            current_y = viewport["height"] // 2
        else:
            current_x, current_y = 0, 0

        # Calculate steps for smooth movement
        steps = random.randint(10, 25)
        for i in range(steps):
            progress = (i + 1) / steps
            # Add slight randomness to path
            jitter_x = random.randint(-2, 2)
            jitter_y = random.randint(-2, 2)

            intermediate_x = int(current_x + (x - current_x) * progress) + jitter_x
            intermediate_y = int(current_y + (y - current_y) * progress) + jitter_y

            self.page.mouse.move(intermediate_x, intermediate_y)
            time.sleep(random.uniform(0.005, 0.02))

    def human_click(self, selector: str) -> None:
        """
        Click an element with human-like behavior.

        Args:
            selector: CSS selector for the element to click
        """
        element = self.page.locator(selector)
        bounding_box = element.bounding_box()

        if bounding_box:
            # Add slight randomness within the element
            x = bounding_box["x"] + random.randint(5, int(bounding_box["width"]) - 5)
            y = bounding_box["y"] + random.randint(5, int(bounding_box["height"]) - 5)

            self.human_move_to(int(x), int(y))
            self.random_delay(100, 300)

        element.click()
        self.random_delay()

    def human_type(self, selector: str, text: str) -> None:
        """
        Type text with human-like timing.

        Args:
            selector: CSS selector for the input element
            text: Text to type
        """
        element = self.page.locator(selector)
        element.click()
        self.random_delay(200, 500)

        for char in text:
            element.press_sequentially(char, delay=random.randint(50, 150))

    def wait_for_page_ready(self) -> None:
        """Wait for page to be fully loaded and ready."""
        self.page.wait_for_load_state("networkidle")
        self.random_delay(500, 1000)

    def simulate_reading(self, duration_seconds: float | None = None) -> None:
        """
        Simulate user reading the page content.

        Args:
            duration_seconds: Reading duration (randomized if not specified)
        """
        if duration_seconds is None:
            duration_seconds = random.uniform(1.5, 4.0)

        # Occasionally scroll while "reading"
        elapsed = 0.0
        while elapsed < duration_seconds:
            wait_time = random.uniform(0.3, 0.8)
            time.sleep(wait_time)
            elapsed += wait_time

            # Occasionally scroll a bit
            if random.random() < 0.3:
                self.human_scroll(ScrollDirection.DOWN, random.randint(50, 150))
