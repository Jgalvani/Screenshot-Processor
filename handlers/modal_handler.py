"""Modal popup handling utilities."""

import random
import time

from playwright.sync_api import Page


class ModalHandler:
    """Handles various modal popups (sign-in, country selection, newsletters, etc.)."""

    # Common modal close button selectors
    MODAL_CLOSE_SELECTORS = [
        # Generic close buttons
        "button[aria-label='Close']",
        "button[aria-label='close']",
        "[aria-label='Close'] button",
        "[aria-label='close'] button",
        # REI specific
        "[aria-label='Close sign in nudge']",
        ".sign-in-nudge__close",
        ".sign-in-nudge__flyout-close",
        ".cdr-modal__close-button_16-2-1",
        # Zara specific
        ".zds-dialog-close-button",
        ".zds-dialog-icon-button.zds-dialog-close-button",
        # Generic patterns
        "[class*='modal'] [class*='close']",
        "[class*='dialog'] [class*='close']",
        "[class*='popup'] [class*='close']",
        "[class*='modal'] button[class*='close']",
        "[class*='overlay'] [class*='close']",
        "[role='dialog'] button[aria-label*='close' i]",
        "[role='dialog'] button[aria-label*='Close']",
        # Newsletter/signup popups
        "[class*='newsletter'] [class*='close']",
        "[class*='signup'] [class*='close']",
        "[class*='sign-up'] [class*='close']",
        "[class*='email'] [class*='close']",
        # Country/region selectors
        "[class*='country'] [class*='close']",
        "[class*='region'] [class*='close']",
        "[class*='geolocation'] [class*='close']",
        "[class*='locale'] [class*='close']",
        # X/close icons (common patterns)
        "button svg[class*='close']",
        "button [class*='icon-close']",
        "button[class*='icon-only'] svg",
    ]

    # Selectors for modal containers
    MODAL_CONTAINER_SELECTORS = [
        "[role='dialog']",
        "[class*='modal']",
        "[class*='popup']",
        "[class*='overlay']",
        "[class*='nudge']",
        "[class*='flyout']",
        ".zds-modal",
        "[class*='sign-in']",
        "[class*='newsletter']",
        "[class*='geolocation']",
    ]

    def __init__(self, page: Page):
        """Initialize ModalHandler with a Playwright page."""
        self.page = page

    def detect_modal(self) -> bool:
        """
        Detect if a modal/popup is visible on the page.

        Returns:
            True if a modal is detected
        """
        for selector in self.MODAL_CONTAINER_SELECTORS:
            try:
                if self.page.locator(selector).count() > 0:
                    if self.page.locator(selector).first.is_visible():
                        return True
            except Exception:
                continue
        return False

    def close_modal(self) -> bool:
        """
        Attempt to close any visible modal by clicking the close button.

        Returns:
            True if a modal was closed
        """
        # Try each close selector
        for selector in self.MODAL_CLOSE_SELECTORS:
            try:
                locator = self.page.locator(selector)
                if locator.count() > 0:
                    button = locator.first
                    if button.is_visible():
                        button.click(timeout=2000)
                        time.sleep(random.uniform(0.3, 0.6))
                        print("    Modal closed")
                        return True
            except Exception:
                continue

        # Fallback: Try to find any close button in visible dialogs
        try:
            close_clicked = self.page.evaluate("""
                () => {
                    // Find visible dialogs/modals
                    const modals = document.querySelectorAll('[role="dialog"], [class*="modal"], [class*="popup"], [class*="overlay"], [class*="nudge"]');

                    for (const modal of modals) {
                        if (modal.offsetParent === null) continue; // Skip hidden

                        // Look for close buttons inside
                        const closeButtons = modal.querySelectorAll('button, [role="button"]');
                        for (const btn of closeButtons) {
                            const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                            const className = (btn.className || '').toLowerCase();
                            const isClose = ariaLabel.includes('close') ||
                                           className.includes('close') ||
                                           btn.querySelector('svg[class*="close"]') ||
                                           btn.querySelector('[class*="icon-close"]');

                            if (isClose && btn.offsetParent !== null) {
                                btn.click();
                                return true;
                            }
                        }
                    }
                    return false;
                }
            """)
            if close_clicked:
                time.sleep(random.uniform(0.3, 0.6))
                print("    Modal closed (JS fallback)")
                return True
        except Exception:
            pass

        return False

    def close_all_modals(self, max_attempts: int = 3) -> int:
        """
        Attempt to close all visible modals.

        Args:
            max_attempts: Maximum number of modals to try to close

        Returns:
            Number of modals closed
        """
        closed_count = 0
        for _ in range(max_attempts):
            if self.detect_modal():
                if self.close_modal():
                    closed_count += 1
                    time.sleep(random.uniform(0.3, 0.5))
                else:
                    break
            else:
                break
        return closed_count
