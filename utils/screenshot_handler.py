"""Screenshot handling utility for capturing and cropping images."""

from pathlib import Path
from datetime import datetime

from PIL import Image
from playwright.sync_api import Page

from config import Settings
from utils.types import BoundingBox


class ScreenshotHandler:
    """Handles screenshot capture and image manipulation."""

    def __init__(self, output_dir: Path | None = None):
        """
        Initialize ScreenshotHandler.

        Args:
            output_dir: Directory to save screenshots (defaults to Settings.OUTPUT_DIR)
        """
        self.output_dir = output_dir or Settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(
        self,
        page: Page,
        name: str = "screenshot",
        full_page: bool = Settings.SCREENSHOT_FULL_PAGE
    ) -> Path:
        """
        Capture a screenshot from the current page.

        Args:
            page: Playwright Page object
            name: Optional custom name for the screenshot
            full_page: Whether to capture full page (defaults to Settings)

        Returns:
            Path to the saved screenshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.{Settings.SCREENSHOT_FORMAT}"

        screenshot_path = self.output_dir / filename

        page.screenshot(
            path=str(screenshot_path),
            full_page=full_page,
            type=Settings.SCREENSHOT_FORMAT
        )

        return screenshot_path

    def crop(
        self,
        image_path: Path,
        region: tuple[int, int, int, int],
        output_name: str | None = None
    ) -> Path:
        """
        Crop a screenshot to a specific region.

        Args:
            image_path: Path to the source image
            region: Crop region as (left, top, right, bottom)
            output_name: Optional custom name for cropped image

        Returns:
            Path to the cropped image
        """
        with Image.open(image_path) as img:
            cropped = img.crop(region)

            if output_name:
                output_path = self.output_dir / f"{output_name}.{Settings.SCREENSHOT_FORMAT}"
            else:
                stem = image_path.stem
                output_path = self.output_dir / f"{stem}_cropped.{Settings.SCREENSHOT_FORMAT}"

            cropped.save(output_path)
            return output_path

    def crop_element(
        self,
        page: Page,
        selector: str,
        name: str | None = None,
        padding: int = 0
    ) -> Path:
        """
        Capture and crop screenshot to a specific element.

        Args:
            page: Playwright Page object
            selector: CSS selector for the element
            name: Optional custom name for the screenshot
            padding: Extra padding around the element in pixels

        Returns:
            Path to the cropped screenshot
        """
        element = page.locator(selector)
        bounding_box: BoundingBox | None = element.bounding_box()

        if not bounding_box:
            raise ValueError(f"Element not found or not visible: {selector}")

        # Capture full page first
        full_screenshot = self.capture(page, name=f"temp_{name or 'element'}")

        # Calculate crop region with padding
        left = max(0, int(bounding_box["x"]) - padding)
        top = max(0, int(bounding_box["y"]) - padding)
        right = int(bounding_box["x"] + bounding_box["width"]) + padding
        bottom = int(bounding_box["y"] + bounding_box["height"]) + padding

        # Crop to element
        cropped_path = self.crop(
            full_screenshot,
            (left, top, right, bottom),
            output_name=name
        )

        # Clean up temp file
        full_screenshot.unlink(missing_ok=True)

        return cropped_path
