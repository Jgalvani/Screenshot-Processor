"""Base page class for Page Object Model implementation."""

import time
from pathlib import Path
from playwright.sync_api import Page, Browser, Playwright

from config import Settings
from utils.human_behavior import HumanBehavior
from utils.screenshot_handler import ScreenshotHandler
from handlers import AntibotHandler, CloudflareHandler, CookieHandler, ModalHandler
from utils.chrome_manager import ChromeManager


class BasePage:
    """Base class for all page objects in the POM structure."""

    def __init__(self, page: Page, output_dir: Path | None = None):
        """
        Initialize BasePage with a Playwright page.

        Args:
            page: Playwright Page object
            output_dir: Optional output directory for screenshots
        """
        self.page = page
        self.human = HumanBehavior(page)
        self.screenshot = ScreenshotHandler(output_dir=output_dir)
        self.antibot = AntibotHandler(page)
        self.cloudflare = CloudflareHandler(page)
        self.cookie_handler = CookieHandler(page)
        self.modal_handler = ModalHandler(page)

    @classmethod
    def create_browser_context(cls, playwright: Playwright) -> tuple[Browser, Page]:
        """
        Create a browser context by connecting to a real Chrome instance via CDP.
        This bypasses bot detection by using an authentic Chrome browser.

        Args:
            playwright: Playwright instance

        Returns:
            Tuple of (Browser, Page)
        """
        # Launch Chrome with remote debugging
        ChromeManager.launch(port=9222)

        # Connect to Chrome via CDP
        browser = playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")

        # Get or create a page
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        print("    Connected to Chrome via CDP (stealth mode)")
        return browser, page

    def navigate(self, url: str) -> None:
        """
        Navigate to a URL with human-like behavior.

        Args:
            url: Target URL
        """
        try:
            self.page.goto(url, timeout=Settings.PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
        except Exception:
            pass

        # Wait for page to be fully loaded
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

        # Brief wait for JavaScript rendering
        time.sleep(0.5)

        # Check for human verification during/after navigation
        self._handle_verification_popup()

        # Handle cookie consent modals
        self._handle_cookie_consent()

        # Handle other modals (sign-in, country selection, newsletters, etc.)
        self._handle_modals()

    def _handle_verification_popup(self, timeout: int = 10000) -> None:
        """Handle any verification popups that appear during navigation."""
        try:
            # Check if this is a Cloudflare challenge page first (most common case)
            if self.cloudflare.is_challenge_page():
                print("    Cloudflare challenge detected during navigation...")
                if self.cloudflare.solve_challenge():
                    print("    Cloudflare challenge solved")
                    try:
                        self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
                    except Exception:
                        pass
                    return

            # Check for puzzle captcha (Shein uses this)
            if self.page.locator("text='Slide to complete'").count() > 0:
                print("    Puzzle captcha detected - attempting to solve...")
                if self.antibot.solve_puzzle_slider():
                    try:
                        self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
                    except Exception:
                        pass
                    return

            # Check for other human verification challenges
            if self.antibot.solve_checkbox():
                print("    Verification checkbox clicked")
                try:
                    self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
                except Exception:
                    pass
        except Exception:
            pass

    def _handle_cookie_consent(self) -> None:
        """Handle cookie consent modals that appear after page load."""
        try:
            if self.cookie_handler.detect_cookie_modal():
                if not self.cookie_handler.accept_cookies():
                    self.cookie_handler.dismiss_cookie_modal()
                self.human.wait_for_ready(timeout=3000)
        except Exception:
            pass

    def _handle_modals(self) -> None:
        """Handle various modal popups (sign-in, country selection, newsletters, etc.)."""
        try:
            # Try to close any visible modals
            self.modal_handler.close_all_modals()
        except Exception:
            pass

    def get_title(self) -> str:
        """Get the page title with retry on context destruction."""
        for _ in range(3):
            try:
                return self.page.title()
            except Exception as e:
                if "context was destroyed" in str(e).lower() or "navigation" in str(e).lower():
                    # Page might have navigated, wait and retry
                    time.sleep(1.0)
                    try:
                        self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Exception:
                        pass
                else:
                    return ""
        return ""

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

    def wait_for_ready(self, timeout: int = 5000) -> None:
        """
        Wait for page to be ready after an action.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.human.wait_for_ready(timeout)

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
        self.human.click(selector)

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
