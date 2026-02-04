"""Human-like browser behavior simulation utilities."""

import random
import time

from playwright.sync_api import Page

from config import Settings
from utils.types import BoundingBox


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

    def mouse_move(self, x: float, y: float) -> None:
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

    def click_at(self, x: float, y: float) -> None:
        """
        Click at specific coordinates with human-like behavior.

        Args:
            x: X coordinate to click
            y: Y coordinate to click
        """
        self.mouse_move(x, y)
        time.sleep(random.uniform(0.1, 0.3))
        self.page.mouse.click(x, y)

    def hold_at(self, x: float, y: float, duration: float | None = None) -> None:
        """
        Press and hold at specific coordinates with human-like behavior.

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Hold duration in seconds (randomized 2-4s if not specified)
        """
        self.mouse_move(x, y)
        time.sleep(random.uniform(0.1, 0.3))
        hold_time = duration or random.uniform(2.0, 4.0)
        self.page.mouse.down()
        time.sleep(hold_time)
        self.page.mouse.up()

    def click_box(
        self,
        box: BoundingBox,
        hold: bool = False,
        hold_duration: float | None = None
    ) -> None:
        """
        Click or hold within a bounding box with human-like behavior.

        Args:
            box: Bounding box with x, y, width, height
            hold: If True, press and hold instead of click
            hold_duration: Hold duration in seconds (used only if hold=True)
        """
        x = box["x"] + box["width"] / 2 + random.randint(-3, 3)
        y = box["y"] + box["height"] / 2 + random.randint(-3, 3)

        if hold:
            self.hold_at(x, y, hold_duration)
        else:
            self.click_at(x, y)

    def click(self, selector: str) -> None:
        """
        Click an element with human-like behavior.

        Args:
            selector: CSS selector for the element to click
        """
        element = self.page.locator(selector)
        bounding_box: BoundingBox | None = element.bounding_box()

        if bounding_box:
            self.click_box(bounding_box)
        else:
            element.click()

        self.random_delay()

    def drag(self, start_box: BoundingBox, end_x: float, end_y: float | None = None) -> None:
        """
        Perform a human-like drag operation.

        Args:
            start_box: Bounding box of the element to drag from (center is calculated)
            end_x: Ending X coordinate
            end_y: Ending Y coordinate (defaults to start_y for horizontal drag)
        """
        start_x = start_box["x"] + start_box["width"] / 2
        start_y = start_box["y"] + start_box["height"] / 2

        if end_y is None:
            end_y = start_y

        # Move to start position
        self.mouse_move(start_x, start_y)
        time.sleep(random.uniform(0.1, 0.3))

        # Press mouse button
        self.page.mouse.down()
        time.sleep(random.uniform(0.05, 0.15))

        # Drag with human-like motion
        self.mouse_move(end_x, end_y)

        # Release mouse button
        self.page.mouse.up()

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

    def wait_for_ready(self, timeout: int = 5000) -> None:
        """
        Wait for page to be ready after an action.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except Exception:
            pass
