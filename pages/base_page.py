"""Base page class for Page Object Model implementation."""

import subprocess
import time
import os
import signal
from pathlib import Path
from playwright.sync_api import Page, Browser, Playwright

from config import Settings
from utils.human_behavior import HumanBehavior
from utils.screenshot_handler import ScreenshotHandler
from utils.antibot import AntibotHandler, CookieHandler


# Global reference to Chrome process for cleanup
_chrome_process = None


def _launch_chrome_with_debugging(port: int = 9222) -> subprocess.Popen:
    """Launch Chrome with remote debugging enabled."""
    global _chrome_process

    # Kill any existing Chrome debug instances
    subprocess.run(['pkill', '-f', 'Chrome.*remote-debugging'], capture_output=True)
    time.sleep(1)

    # Chrome path for macOS
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    # Create a temporary profile directory
    profile_dir = f"/tmp/chrome-debug-profile-{port}"

    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-default-apps",
        "--disable-popup-blocking",
        "--disable-translate",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-device-discovery-notifications",
        "--window-size=1920,1080",
        "about:blank"
    ]

    # Launch Chrome in background
    _chrome_process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setpgrp
    )

    # Wait for Chrome to start
    time.sleep(3)

    return _chrome_process


def cleanup_chrome():
    """Clean up Chrome process on exit."""
    global _chrome_process

    # First try to kill the tracked process
    if _chrome_process:
        try:
            # Try SIGTERM first (graceful)
            os.killpg(os.getpgid(_chrome_process.pid), signal.SIGTERM)
            time.sleep(1)
        except Exception:
            pass

        try:
            # Force kill if still running
            if _chrome_process.poll() is None:
                os.killpg(os.getpgid(_chrome_process.pid), signal.SIGKILL)
        except Exception:
            pass

        _chrome_process = None

    # Also kill any remaining Chrome debug instances
    try:
        subprocess.run(
            ['pkill', '-f', 'Chrome.*remote-debugging'],
            capture_output=True,
            timeout=5
        )
    except Exception:
        pass

    print("    Chrome process cleaned up")


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
        self.antibot = AntibotHandler(page)
        self.cookie_handler = CookieHandler(page)

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
        _launch_chrome_with_debugging(port=9222)

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
        import time

        try:
            self.page.goto(url, timeout=Settings.PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
        except Exception:
            # Page might timeout due to verification popup - try to handle it
            pass

        # Wait for page to be fully loaded
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        # Additional wait for JavaScript-heavy pages
        time.sleep(2)

        # Check for human verification during/after navigation
        self._handle_verification_popup()
        self.human.wait_for_page_ready()

        # Handle cookie consent modals
        self._handle_cookie_consent()

    def _handle_verification_popup(self) -> None:
        """Handle any verification popups that appear during navigation."""
        import time
        import random

        try:
            # Give page a moment to show verification
            time.sleep(random.uniform(1.0, 2.0))

            # Check if this is a Cloudflare challenge page first (most common case)
            if self.antibot.is_cloudflare_challenge_page():
                print("    Cloudflare challenge detected during navigation...")
                if self.antibot.solve_cloudflare_challenge():
                    print("    Cloudflare challenge solved")
                    # Wait for redirect and new page to load
                    try:
                        self.page.wait_for_load_state("domcontentloaded", timeout=15000)
                    except Exception:
                        pass
                    return

            # Only handle verification if it's clearly a challenge page
            # Check page title and visible content for clear indicators
            page_title = self.page.title().lower()
            is_challenge_page = any(term in page_title for term in [
                "just a moment", "verify", "challenge", "security check", "access denied"
            ])

            # Check for puzzle captcha (Shein uses this - requires manual solving)
            if self.page.locator("text='Slide to complete'").count() > 0:
                print("    Puzzle captcha detected - cannot be auto-solved")
                return

            # Also check if there's a visible Cloudflare turnstile
            has_turnstile = self.page.locator("[class*='cf-turnstile'], [class*='turnstile'], [id*='turnstile']").count() > 0

            # Check for visible "Verify you are human" text
            has_verify_text = self.page.locator("text='Verify you are human'").count() > 0

            # Check for Cloudflare iframe
            has_cf_iframe = self.page.locator("iframe[src*='challenges.cloudflare.com']").count() > 0

            if is_challenge_page or has_turnstile or has_verify_text or has_cf_iframe:
                print("    Human verification detected during navigation...")

                # Try multiple times to find and click the checkbox
                for _ in range(3):
                    if self.antibot.solve_human_verify():
                        print("    Verification checkbox clicked")
                        time.sleep(random.uniform(3.0, 5.0))

                        # Wait for page to potentially redirect after verification
                        try:
                            self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                        except Exception:
                            pass
                        break
                    time.sleep(random.uniform(1.0, 2.0))
        except Exception:
            pass

    def _handle_cookie_consent(self) -> None:
        """Handle cookie consent modals that appear after page load."""
        import time
        import random

        try:
            # Give page a moment for cookie modal to appear
            time.sleep(random.uniform(0.3, 0.5))

            # Check if cookie modal is present and accept it
            if self.cookie_handler.detect_cookie_modal():
                self.cookie_handler.accept_cookies()

                # Wait for page to stabilize after cookie acceptance
                # Some sites reload the page after accepting cookies
                time.sleep(1.5)

                # Try to wait for page to be ready again
                try:
                    self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    pass

                try:
                    self.page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass

        except Exception:
            # Context may have been destroyed due to navigation - that's OK
            pass

    def get_title(self) -> str:
        """Get the page title with retry on context destruction."""
        import time

        for attempt in range(3):
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
