"""Cookie consent handling utilities."""

import random
import time

from playwright.sync_api import Page


class CookieHandler:
    """Handles cookie consent modals and banners."""

    # Common cookie consent selectors for various platforms
    # Order matters - more specific selectors first
    COOKIE_ACCEPT_SELECTORS = [
        # Site-specific selectors (highest priority)
        # Costco
        "button:has-text('Confirm My Choices')",
        # Shein
        "button:has-text('Accept All'):visible",
        "button:has-text('Reject All')",  # Shein has this option
        # Nike/Adidas specific
        "[data-testid='accept-cookies']",
        # OneTrust (very common - used by many sites)
        "#onetrust-accept-btn-handler",
        "button[id*='onetrust-accept']",
        # Generic "Accept All" buttons (most common)
        "button:has-text('Accept All')",
        "button:has-text('Accept all')",
        "button:has-text('Accept All Cookies')",
        "button:has-text('Accept all cookies')",
        "button:has-text('Accepter tout')",
        "button:has-text('Tout accepter')",
        "button:has-text('Akzeptieren')",
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Aceptar todo')",
        "button:has-text('Accetta tutto')",
        # Generic "I Accept" / "I Agree" buttons
        "button:has-text('I Accept')",
        "button:has-text('I Agree')",
        "button:has-text('Agree')",
        # CookieBot
        "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
        "#CybotCookiebotDialogBodyButtonAccept",
        "a#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
        # TrustArc / TrustE
        ".trustarc-agree-btn",
        "#truste-consent-button",
        ".call[data-testid='uc-accept-all-button']",
        # Quantcast
        ".qc-cmp2-summary-buttons button[mode='primary']",
        "button.css-47sehv",
        # Didomi
        "#didomi-notice-agree-button",
        ".didomi-continue-without-agreeing",
        # Cookielaw
        ".cookielaw-accept",
        "#cookiescript_accept",
        # Generic class-based selectors (lower priority - might match wrong buttons)
        "[class*='cookie'] button:has-text('Accept')",
        "[class*='consent'] button:has-text('Accept')",
        # Link-based accept buttons
        "a:has-text('Accept All')",
        "a:has-text('Accept all cookies')",
    ]

    # Selectors for cookie modal/banner containers
    COOKIE_MODAL_SELECTORS = [
        "[class*='cookie-banner']",
        "[class*='cookie-consent']",
        "[class*='cookie-notice']",
        "[class*='cookie-modal']",
        "[class*='cookie-popup']",
        "[class*='consent-banner']",
        "[class*='consent-modal']",
        "[class*='gdpr-banner']",
        "[class*='privacy-banner']",
        "[id*='cookie-banner']",
        "[id*='cookie-consent']",
        "[id*='cookie-notice']",
        "[id*='onetrust']",
        "[id*='CybotCookiebot']",
        "[id*='didomi']",
        "[id*='truste']",
        "#cookiescript_injected",
        "[aria-label*='cookie']",
        "[aria-label*='consent']",
        "[role='dialog']:has-text('cookie')",
        "[role='dialog']:has-text('Cookie')",
    ]

    def __init__(self, page: Page):
        """Initialize CookieHandler with a Playwright page."""
        self.page = page

    def _has_visible_element(self, selectors: list[str]) -> bool:
        """Check if any selector in the list has a visible element."""
        for selector in selectors:
            try:
                if self.page.locator(selector).count() > 0:
                    if self.page.locator(selector).first.is_visible():
                        return True
            except Exception:
                continue
        return False

    def detect_cookie_modal(self) -> bool:
        """
        Detect if a cookie consent modal/banner is present on the page.

        Returns:
            True if a cookie modal is detected
        """
        try:
            # Check for cookie-related text in the page
            page_content = self.page.content().lower()
            cookie_keywords = [
                'cookie', 'cookies', 'consent', 'gdpr', 'privacy',
                'accept all', 'accepter', 'akzeptieren'
            ]

            has_cookie_text = any(keyword in page_content for keyword in cookie_keywords)
            if not has_cookie_text:
                return False

            # Check for modal/banner containers
            return self._has_visible_element(self.COOKIE_MODAL_SELECTORS)

        except Exception:
            return False

    def accept_cookies(self) -> bool:
        """
        Attempt to accept cookies by clicking the accept button.

        Returns:
            True if cookies were accepted successfully
        """
        # Try each accept selector
        for selector in self.COOKIE_ACCEPT_SELECTORS:
            try:
                locator = self.page.locator(selector)
                if locator.count() > 0:
                    button = locator.first
                    if button.is_visible():
                        # Scroll into view if needed
                        try:
                            button.scroll_into_view_if_needed()
                        except Exception:
                            pass
                        time.sleep(random.uniform(0.1, 0.2))

                        # Click the button
                        try:
                            button.click(timeout=3000)
                        except Exception:
                            # Try force click if normal click fails
                            button.click(force=True, timeout=3000)

                        print("    Cookie consent accepted")

                        # Some sites reload or navigate after accepting cookies
                        try:
                            self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                        except Exception:
                            pass

                        return True

            except Exception:
                continue

        # Fallback: Try JavaScript-based approach for stubborn modals
        try:
            clicked = self.page.evaluate("""
                () => {
                    const acceptTexts = [
                        'accept all', 'accept all cookies', 'accepter tout',
                        'tout accepter', 'i accept', 'i agree', 'allow all',
                        'confirm my choices'
                    ];

                    // Texts to avoid - these might navigate to other pages
                    const avoidTexts = [
                        'cookie notice', 'cookie policy', 'privacy policy',
                        'learn more', 'read more', 'manage', 'settings',
                        'customize', 'preferences'
                    ];

                    // Find only buttons (not links to avoid navigation)
                    const buttons = [...document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]')];

                    for (const el of buttons) {
                        const text = el.textContent.toLowerCase().trim();
                        const isVisible = el.offsetParent !== null &&
                                         el.getBoundingClientRect().height > 0;

                        // Skip if text contains words we want to avoid
                        if (avoidTexts.some(t => text.includes(t))) {
                            continue;
                        }

                        if (isVisible && acceptTexts.some(t => text.includes(t))) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)

            if clicked:
                time.sleep(random.uniform(0.5, 1.0))
                print("    Cookie consent accepted (JS fallback)")
                return True
        except Exception:
            pass

        return False

    def dismiss_cookie_modal(self) -> bool:
        """
        Try to dismiss/close a cookie modal without accepting.

        Returns:
            True if modal was dismissed
        """
        close_selectors = [
            "[class*='cookie'] button[class*='close']",
            "[class*='cookie'] [aria-label='close']",
            "[class*='consent'] button[class*='close']",
            "#onetrust-close-btn-container button",
            ".cookie-banner__close",
        ]

        for selector in close_selectors:
            try:
                if self.page.locator(selector).count() > 0:
                    self.page.locator(selector).first.click()
                    time.sleep(random.uniform(0.3, 0.6))
                    return True
            except Exception:
                continue

        return False
