"""Generic page class for handling any URL."""

from .base_page import BasePage
from utils.openai_extractor import OpenAIExtractor
from utils.human_behavior import ScrollDirection
from pathlib import Path


class GenericPage(BasePage):
    """Generic page handler for any website URL."""

    def __init__(self, page, openai_extractor: OpenAIExtractor | None = None, output_dir: Path | None = None):
        """
        Initialize GenericPage.

        Args:
            page: Playwright Page object
            openai_extractor: Optional OpenAI extractor instance
            output_dir: Optional output directory for screenshots
        """
        super().__init__(page, output_dir=output_dir)
        self.extractor = openai_extractor
    
    def getResult(self, screenshot_path: Path, extraction_prompt: str | None = None) -> dict:
        """
        Create results from the screenshot extraction.

        Args:
            path: Path to the screenshot
        """
        result = {
            "url": self.get_url(),
            "title": self.get_title(),
            "screenshot_path": screenshot_path,
            "extracted_data": None,
            "product_info": None,
            "final_price": None
        }

        # Extract data if extractor is available
        if self.extractor:
            if extraction_prompt:
                result["extracted_data"] = self.extractor.extract_data(
                    screenshot_path,
                    extraction_prompt
                )
            else:
                # Default to product info extraction
                product_info = self.extractor.extract_product_info(screenshot_path)
                result["product_info"] = product_info
                result["final_price"] = self.extractor.calculate_final_price(product_info)

        return result

    def capture_and_extract(
        self,
        screenshot_name: str | None = None,
        extraction_prompt: str | None = None
    ) -> dict:
        """
        Capture screenshot and extract data using OpenAI.

        Args:
            screenshot_name: Optional custom name for screenshot
            extraction_prompt: Custom prompt for data extraction

        Returns:
            Dictionary with screenshot path and extracted data
        """
        # Take screenshot
        screenshot_path = self.take_screenshot(name=screenshot_name)
        return self.getResult(screenshot_path, extraction_prompt)

    def capture_element_and_extract(
        self,
        selector: str,
        screenshot_name: str | None = None,
        extraction_prompt: str | None = None,
        padding: int = 10
    ) -> dict:
        """
        Capture specific element screenshot and extract data.

        Args:
            selector: CSS selector for the element
            screenshot_name: Optional custom name for screenshot
            extraction_prompt: Custom prompt for data extraction
            padding: Extra padding around element

        Returns:
            Dictionary with screenshot path and extracted data
        """
        # Take element screenshot
        screenshot_path = self.take_element_screenshot(
            selector,
            name=screenshot_name,
            padding=padding
        )
        return self.getResult(screenshot_path, extraction_prompt)

    def simulate_browsing(self, scroll_times: int = 3) -> None:
        """
        Simulate human-like browsing behavior.

        Args:
            scroll_times: Number of times to scroll
        """
        self.human.simulate_reading()

        for _ in range(scroll_times):
            self.human.human_scroll(ScrollDirection.DOWN)
            self.human.simulate_reading(duration_seconds=1.0)
