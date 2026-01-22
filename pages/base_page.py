"""Base page class for Page Object Model implementation."""

from pathlib import Path
from playwright.sync_api import Page, Browser, Playwright

from config import Settings
from utils.human_behavior import HumanBehavior
from utils.screenshot_handler import ScreenshotHandler


class BasePage:
    """Base class for all page objects in the POM structure."""

    def __init__(self, page: Page):
        """
        Initialize BasePage with a Playwright page.

        Args:
            page: Playwright Page object
        """
        self.page = page
        self.human = HumanBehavior(page)
        self.screenshot = ScreenshotHandler()

    @classmethod
    def create_browser_context(cls, playwright: Playwright) -> tuple[Browser, Page]:
        """
        Create a browser context with human-like settings.

        Args:
            playwright: Playwright instance

        Returns:
            Tuple of (Browser, Page)
        """
        browser = playwright.chromium.launch(
            headless=Settings.BROWSER_HEADLESS,
            slow_mo=Settings.BROWSER_SLOW_MO
        )

        context = browser.new_context(
            viewport={
                "width": Settings.VIEWPORT_WIDTH,
                "height": Settings.VIEWPORT_HEIGHT
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York"
        )

        page = context.new_page()
        return browser, page

    def navigate(self, url: str) -> None:
        """
        Navigate to a URL with human-like behavior.

        Args:
            url: Target URL
        """
        self.page.goto(url, timeout=Settings.PAGE_LOAD_TIMEOUT)
        self.human.wait_for_page_ready()

    def get_title(self) -> str:
        """Get the page title."""
        return self.page.title()

    def get_url(self) -> str:
        """Get the current page URL."""
        return self.page.url

    def take_screenshot(self, name: str | None = None) -> Path:
        """
        Take a screenshot of the current page.

        Args:
            name: Optional custom name for the screenshot

        Returns:
            Path to the saved screenshot
        """
        return self.screenshot.capture(self.page, name=name)

    def take_element_screenshot(
        self,
        selector: str,
        name: str | None = None,
        padding: int = 10
    ) -> Path:
        """
        Take a screenshot of a specific element.

        Args:
            selector: CSS selector for the element
            name: Optional custom name for the screenshot
            padding: Extra padding around element in pixels

        Returns:
            Path to the saved screenshot
        """
        return self.screenshot.crop_element(
            self.page,
            selector,
            name=name,
            padding=padding
        )

    def wait_for_element(self, selector: str, timeout: int = Settings.PAGE_LOAD_TIMEOUT) -> None:
        """
        Wait for an element to be visible.

        Args:
            selector: CSS selector for the element
            timeout: Maximum wait time in milliseconds
        """
        self.page.locator(selector).wait_for(
            state="visible",
            timeout=timeout 
        )

    def scroll_to_element(self, selector: str) -> None:
        """
        Scroll an element into view.

        Args:
            selector: CSS selector for the element
        """
        self.page.locator(selector).scroll_into_view_if_needed()
        self.human.random_delay(300, 600)

    def click(self, selector: str) -> None:
        """
        Click an element with human-like behavior.

        Args:
            selector: CSS selector for the element
        """
        self.human.human_click(selector)

    def fill(self, selector: str, text: str) -> None:
        """
        Fill an input field with human-like typing.

        Args:
            selector: CSS selector for the input
            text: Text to enter
        """
        self.human.human_type(selector, text)

    def get_text(self, selector: str) -> str:
        """
        Get text content of an element.

        Args:
            selector: CSS selector for the element

        Returns:
            Text content of the element
        """
        return self.page.locator(selector).text_content() or ""

    def is_visible(self, selector: str) -> bool:
        """
        Check if an element is visible.

        Args:
            selector: CSS selector for the element

        Returns:
            True if element is visible
        """
        return self.page.locator(selector).is_visible()

    def close(self) -> None:
        """Close the page."""
        self.page.close()
