"""Antibot detection and evasion utilities."""

import random
import time
from playwright.sync_api import Page


# Modern user agents pool (Chrome, Firefox, Safari, Edge on Windows/Mac)
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
]

# Common screen resolutions
SCREEN_RESOLUTIONS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
    {"width": 2560, "height": 1440},
]

# Timezones
TIMEZONES = [
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Paris",
]


def get_random_user_agent() -> str:
    """Get a random user agent string."""
    return random.choice(USER_AGENTS)


def get_random_viewport() -> dict:
    """Get a random viewport size."""
    return random.choice(SCREEN_RESOLUTIONS)


def get_random_timezone() -> str:
    """Get a random timezone."""
    return random.choice(TIMEZONES)


def get_browser_context_options() -> dict:
    """Get randomized browser context options for better antibot evasion."""
    user_agent = get_random_user_agent()
    viewport = get_random_viewport()
    timezone = get_random_timezone()

    # Determine locale based on user agent
    locale = "en-US"
    if "Firefox" in user_agent and "rv:123" in user_agent:
        locale = random.choice(["en-US", "en-GB"])

    return {
        "user_agent": user_agent,
        "viewport": viewport,
        "timezone_id": timezone,
        "locale": locale,
        "color_scheme": random.choice(["light", "dark", "no-preference"]),
        "has_touch": False,
        "is_mobile": False,
        "java_script_enabled": True,
    }


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

    def __init__(self, page):
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

    def __init__(self, page):
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
            if self._has_visible_element(self.COOKIE_MODAL_SELECTORS):
                return True

            # Check for accept buttons visibility
            if self._has_visible_element(self.COOKIE_ACCEPT_SELECTORS[:20]):
                return True

            return False

        except Exception:
            return False

    def accept_cookies(self) -> bool:
        """
        Attempt to accept cookies by clicking the accept button.

        Returns:
            True if cookies were accepted successfully
        """
        try:
            # Wait a bit for any cookie modal to appear
            time.sleep(random.uniform(0.3, 0.6))

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

                            # Wait for page to stabilize after cookie acceptance
                            # Some sites reload or navigate after accepting cookies
                            time.sleep(1.0)
                            try:
                                self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                            except Exception:
                                pass

                            return True

                except Exception:
                    continue

            # Fallback: Try JavaScript-based approach for stubborn modals
            # Be more careful - only click buttons, not links that might navigate away
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

            return False

        except Exception as e:
            print(f"    Cookie accept error: {e}")
            return False

    def dismiss_cookie_modal(self) -> bool:
        """
        Try to dismiss/close a cookie modal without accepting (for testing).

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


class AntibotHandler:
    """Handles antibot detection and challenge solving."""

    # Common antibot selectors
    CAPTCHA_SELECTORS = {
        # reCAPTCHA
        "recaptcha_checkbox": "iframe[src*='recaptcha']",
        "recaptcha_checkbox_inner": "#recaptcha-anchor",
        # hCaptcha
        "hcaptcha_checkbox": "iframe[src*='hcaptcha']",
        "hcaptcha_checkbox_inner": "#checkbox",
        # Cloudflare
        "cloudflare_checkbox": "iframe[src*='challenges.cloudflare']",
        "cloudflare_turnstile": "#cf-turnstile",
        # Cloudflare Turnstile (the "Verify you are human" widget)
        "cloudflare_turnstile_container": "[class*='cf-turnstile'], [id*='turnstile'], [id*='cf-'], [class*='turnstile']",
        "cloudflare_turnstile_clickable": "[class*='cf-turnstile'] input, [class*='cf-turnstile'] [role='checkbox'], #challenge-stage input, .cf-turnstile-wrapper input",
        # Human verification checkboxes - more specific to avoid false positives
        "human_verify_checkbox": "[class*='captcha'] input[type='checkbox'], [class*='verify'] input[type='checkbox'], [class*='challenge'] input[type='checkbox']",
        "human_verify_button": "button:has-text('Verify'), button:has-text('Continue'):not([class*='search']):not([class*='nav'])",
        "generic_robot_checkbox": "input[type='checkbox'][name*='robot'], input[type='checkbox'][id*='robot'], input[type='checkbox'][name*='human'], input[type='checkbox'][id*='human']",
        # Press and hold buttons
        "press_hold_button": "[class*='press'], [class*='hold'], button[class*='verify']",
        # Sliders (including puzzle sliders)
        "slider_track": "[class*='slider'], [class*='captcha-slider'], [class*='drag'], [class*='JJCAPTCHA'], [class*='verify-wrap']",
        "slider_handle": "[class*='slider-handle'], [class*='slider-button'], [class*='drag-handle'], [class*='geetest'], [class*='verify-btn']",
        # Puzzle captcha (Shein uses this)
        "puzzle_captcha": "[class*='puzzle'], [class*='jigsaw'], text='Slide to complete'",
        # Access denied / blocked pages
        "access_denied": "body:has-text('Access Denied'), body:has-text('blocked'), body:has-text('forbidden')",
    }

    def __init__(self, page: Page):
        """Initialize AntibotHandler with a Playwright page."""
        self.page = page

    def detect_antibot(self) -> dict:
        """
        Detect if page has antibot challenges.

        Returns:
            Dictionary with detection results
        """
        results = {
            "has_recaptcha": False,
            "has_hcaptcha": False,
            "has_cloudflare": False,
            "has_cloudflare_turnstile": False,
            "has_slider": False,
            "has_press_hold": False,
            "has_checkbox": False,
            "has_human_verify": False,
            "is_blocked": False,
        }

        try:
            page_title = self.page.title().lower()

            # Check for reCAPTCHA
            if self.page.locator(self.CAPTCHA_SELECTORS["recaptcha_checkbox"]).count() > 0:
                results["has_recaptcha"] = True

            # Check for hCaptcha
            if self.page.locator(self.CAPTCHA_SELECTORS["hcaptcha_checkbox"]).count() > 0:
                results["has_hcaptcha"] = True

            # Check for Cloudflare challenge page (the "Just a moment..." page)
            if self.is_cloudflare_challenge_page():
                results["has_cloudflare"] = True
                results["has_cloudflare_turnstile"] = True

            # Check for Cloudflare iframe/turnstile elements
            if self.page.locator(self.CAPTCHA_SELECTORS["cloudflare_checkbox"]).count() > 0:
                results["has_cloudflare"] = True
            if self.page.locator(self.CAPTCHA_SELECTORS["cloudflare_turnstile"]).count() > 0:
                results["has_cloudflare"] = True
            if self.page.locator("iframe[src*='challenges.cloudflare.com']").count() > 0:
                results["has_cloudflare"] = True
                results["has_cloudflare_turnstile"] = True
            if self.page.locator("iframe[id^='cf-chl-widget']").count() > 0:
                results["has_cloudflare"] = True
                results["has_cloudflare_turnstile"] = True

            # Check for slider captcha
            if self.page.locator(self.CAPTCHA_SELECTORS["slider_track"]).count() > 0:
                results["has_slider"] = True

            # Check for press and hold
            if self.page.locator(self.CAPTCHA_SELECTORS["press_hold_button"]).count() > 0:
                results["has_press_hold"] = True

            # Check for generic checkbox
            if self.page.locator(self.CAPTCHA_SELECTORS["generic_robot_checkbox"]).count() > 0:
                results["has_checkbox"] = True

            # Check if page is blocked
            if any(term in page_title for term in ["access denied", "blocked", "forbidden"]):
                results["is_blocked"] = True

            # Check for human verification - use more specific checks
            # Check for Cloudflare Turnstile widget
            if self.page.locator("[class*='cf-turnstile'], [class*='turnstile']").count() > 0:
                results["has_human_verify"] = True
            # Check for visible "Verify you are human" text (Cloudflare challenge page)
            elif self.page.locator("text='Verify you are human'").count() > 0:
                results["has_human_verify"] = True
            # Check for challenge page titles
            elif any(term in page_title for term in ["just a moment", "verify", "security check", "challenge"]):
                results["has_human_verify"] = True

        except Exception:
            pass

        return results

    def solve_checkbox(self, selector: str | None = None) -> bool:
        """
        Solve a checkbox-type captcha by clicking it with human-like behavior.

        Args:
            selector: Optional specific selector for the checkbox

        Returns:
            True if checkbox was found and clicked
        """
        try:
            # Try specific selector or common ones
            selectors_to_try = [selector] if selector else [
                self.CAPTCHA_SELECTORS["generic_robot_checkbox"],
                "input[type='checkbox']",
            ]

            for sel in selectors_to_try:
                if sel and self.page.locator(sel).count() > 0:
                    checkbox = self.page.locator(sel).first
                    box = checkbox.bounding_box()

                    if box:
                        # Human-like movement to checkbox
                        self._human_move_and_click(box)
                        time.sleep(random.uniform(0.5, 1.5))
                        return True

        except Exception:
            pass

        return False

    def solve_recaptcha_checkbox(self) -> bool:
        """
        Attempt to solve reCAPTCHA checkbox (I'm not a robot).

        Returns:
            True if checkbox was clicked
        """
        try:
            iframe = self.page.frame_locator(self.CAPTCHA_SELECTORS["recaptcha_checkbox"])
            checkbox = iframe.locator(self.CAPTCHA_SELECTORS["recaptcha_checkbox_inner"])

            if checkbox.count() > 0:
                # Random delay before clicking
                time.sleep(random.uniform(0.5, 2.0))
                checkbox.click()
                time.sleep(random.uniform(1.0, 3.0))
                return True

        except Exception:
            pass

        return False

    def solve_press_and_hold(self, selector: str | None = None, hold_duration: float = None) -> bool:
        """
        Solve a press-and-hold verification button.

        Args:
            selector: Optional specific selector for the button
            hold_duration: How long to hold (randomized if not specified)

        Returns:
            True if button was found and held
        """
        try:
            sel = selector or self.CAPTCHA_SELECTORS["press_hold_button"]
            button = self.page.locator(sel).first

            if button.count() > 0:
                box = button.bounding_box()

                if box:
                    # Calculate center with slight randomness
                    x = box["x"] + box["width"] / 2 + random.randint(-5, 5)
                    y = box["y"] + box["height"] / 2 + random.randint(-3, 3)

                    # Move to button
                    self._smooth_mouse_move(x, y)
                    time.sleep(random.uniform(0.1, 0.3))

                    # Press and hold
                    duration = hold_duration or random.uniform(2.0, 4.0)
                    self.page.mouse.down()
                    time.sleep(duration)
                    self.page.mouse.up()

                    time.sleep(random.uniform(0.5, 1.0))
                    return True

        except Exception:
            pass

        return False

    def solve_slider(self, track_selector: str | None = None, handle_selector: str | None = None) -> bool:
        """
        Solve a slider captcha by dragging the handle across the track.

        Args:
            track_selector: Optional specific selector for the slider track
            handle_selector: Optional specific selector for the slider handle

        Returns:
            True if slider was found and dragged
        """
        try:
            track_sel = track_selector or self.CAPTCHA_SELECTORS["slider_track"]
            handle_sel = handle_selector or self.CAPTCHA_SELECTORS["slider_handle"]

            # Find track and handle
            track = self.page.locator(track_sel).first
            handle = self.page.locator(handle_sel).first

            track_box = track.bounding_box() if track.count() > 0 else None
            handle_box = handle.bounding_box() if handle.count() > 0 else None

            if track_box and handle_box:
                # Starting position (handle center)
                start_x = handle_box["x"] + handle_box["width"] / 2
                start_y = handle_box["y"] + handle_box["height"] / 2

                # End position (track end with some margin)
                end_x = track_box["x"] + track_box["width"] - 10

                # Perform human-like drag
                self._human_drag(start_x, start_y, end_x)
                time.sleep(random.uniform(0.5, 1.5))
                return True

        except Exception:
            pass

        return False

    def solve_puzzle_slider(self) -> bool:
        """
        Attempt to solve a puzzle slider captcha (like Shein's).
        Tries dragging to different positions since we can't determine the exact position.

        Returns:
            True if puzzle slider was found and attempted
        """
        try:
            # Check for puzzle slider text
            has_puzzle = self.page.locator("text='Slide to complete'").count() > 0

            if not has_puzzle:
                return False

            print("    Attempting puzzle slider solve...")

            # Find the slider handle (arrow button)
            handle_selectors = [
                "[class*='slider'] [class*='btn']",
                "[class*='slider'] [class*='arrow']",
                "[class*='slider'] button",
                "[class*='verify'] [class*='btn']",
                "[class*='captcha'] [class*='slider']",
                "div[class*='drag']",
            ]

            handle = None
            for sel in handle_selectors:
                loc = self.page.locator(sel)
                if loc.count() > 0:
                    first = loc.first
                    if first.is_visible():
                        handle = first
                        break

            if not handle:
                # Fallback: Look for any draggable element in the puzzle area
                handle = self.page.evaluate("""
                    () => {
                        const candidates = document.querySelectorAll('[class*="slider"], [class*="drag"], [class*="verify"]');
                        for (const el of candidates) {
                            const btn = el.querySelector('button, [class*="btn"], [class*="arrow"], [role="slider"]');
                            if (btn && btn.offsetParent !== null) {
                                const rect = btn.getBoundingClientRect();
                                return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
                            }
                        }
                        return null;
                    }
                """)
                if handle:
                    # We got coordinates directly, perform drag
                    start_x = handle["x"] + handle["width"] / 2
                    start_y = handle["y"] + handle["height"] / 2

                    # Try dragging to approximately 60-70% of the track (common puzzle position)
                    for offset_percent in [0.65, 0.55, 0.75, 0.45, 0.85]:
                        end_x = start_x + 200 * offset_percent  # Approximate track width
                        self._human_drag(start_x, start_y, end_x)
                        time.sleep(1.0)

                        # Check if puzzle was solved (slider might disappear)
                        if self.page.locator("text='Slide to complete'").count() == 0:
                            print("    Puzzle slider solved!")
                            return True

                        # Reset for next attempt
                        time.sleep(0.5)

                    return True

            if handle:
                handle_box = handle.bounding_box()
                if handle_box:
                    start_x = handle_box["x"] + handle_box["width"] / 2
                    start_y = handle_box["y"] + handle_box["height"] / 2

                    # Try multiple positions
                    for offset_percent in [0.65, 0.55, 0.75, 0.45, 0.85]:
                        end_x = start_x + 200 * offset_percent
                        self._human_drag(start_x, start_y, end_x)
                        time.sleep(1.0)

                        if self.page.locator("text='Slide to complete'").count() == 0:
                            print("    Puzzle slider solved!")
                            return True

                        time.sleep(0.5)

                    return True

        except Exception as e:
            print(f"    Puzzle slider error: {e}")

        return False

    def handle_cloudflare(self) -> bool:
        """
        Handle Cloudflare challenge page.

        Returns:
            True if challenge was potentially solved
        """
        try:
            # Wait for Cloudflare to process initial checks
            time.sleep(random.uniform(2.0, 4.0))

            # First, try the Turnstile-specific solver
            if self.solve_cloudflare_turnstile():
                return True

            # Check for turnstile widget by ID
            turnstile = self.page.locator(self.CAPTCHA_SELECTORS["cloudflare_turnstile"])
            if turnstile.count() > 0:
                box = turnstile.bounding_box()
                if box:
                    self._human_move_and_click(box)
                    time.sleep(random.uniform(2.0, 5.0))
                    return True

            # Check for checkbox in iframe
            cf_iframe = self.page.locator(self.CAPTCHA_SELECTORS["cloudflare_checkbox"])
            if cf_iframe.count() > 0:
                cf_iframe.click()
                time.sleep(random.uniform(2.0, 5.0))
                return True

        except Exception:
            pass

        return False

    def is_cloudflare_challenge_page(self) -> bool:
        """
        Check if the current page is a Cloudflare challenge page.

        Returns:
            True if this is a Cloudflare challenge page
        """
        try:
            page_title = self.page.title().lower()

            # Check for common Cloudflare challenge page indicators
            title_indicators = ["just a moment", "attention required", "one more step"]
            if any(indicator in page_title for indicator in title_indicators):
                return True

            # Check for Cloudflare-specific elements
            has_cf_ray = self.page.locator("code:has-text('Ray ID')").count() > 0
            has_cf_script = self.page.locator("script[src*='challenge-platform']").count() > 0
            has_verify_text = self.page.locator("text='Verify you are human'").count() > 0
            has_turnstile_iframe = self.page.locator("iframe[src*='challenges.cloudflare.com']").count() > 0

            return has_cf_ray or has_cf_script or has_verify_text or has_turnstile_iframe

        except Exception:
            return False

    def solve_cloudflare_challenge(self, max_attempts: int = 3, wait_after_solve: float = 5.0) -> bool:
        """
        Full solution for Cloudflare challenge pages.

        This method handles the complete Cloudflare "Just a moment..." challenge page,
        including the Turnstile widget verification.

        Args:
            max_attempts: Maximum number of attempts to solve the challenge
            wait_after_solve: Seconds to wait after clicking the checkbox

        Returns:
            True if the challenge was solved and page redirected
        """
        if not self.is_cloudflare_challenge_page():
            return False

        print("    Cloudflare challenge page detected, attempting to solve...")

        for attempt in range(max_attempts):
            try:
                # Wait for the Turnstile widget to fully load
                time.sleep(random.uniform(2.0, 4.0))

                # Attempt to solve the Turnstile
                if self.solve_cloudflare_turnstile():
                    print(f"    Turnstile clicked (attempt {attempt + 1})")

                    # Wait for the verification to complete
                    time.sleep(wait_after_solve)

                    # Check if we're still on a challenge page
                    if not self.is_cloudflare_challenge_page():
                        print("    Challenge solved successfully!")
                        return True

                    # Check if page has started redirecting
                    try:
                        self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                        if not self.is_cloudflare_challenge_page():
                            print("    Challenge solved successfully!")
                            return True
                    except Exception:
                        pass

                # Small delay before retry
                time.sleep(random.uniform(1.0, 2.0))

            except Exception as e:
                print(f"    Challenge solve attempt {attempt + 1} failed: {e}")
                time.sleep(random.uniform(1.0, 2.0))

        print("    Failed to solve Cloudflare challenge after max attempts")
        return False

    def solve_cloudflare_turnstile(self) -> bool:
        """
        Solve Cloudflare Turnstile "Verify you are human" challenge.

        The Turnstile widget is typically inside an iframe from challenges.cloudflare.com.
        The iframe may be inside a closed shadow DOM, so we need multiple strategies.

        Returns:
            True if turnstile was found and clicked
        """
        try:
            # Wait for the page to stabilize
            time.sleep(random.uniform(1.5, 3.0))

            # Strategy 1: Find the Cloudflare Turnstile iframe directly
            turnstile_iframe = self.page.locator("iframe[src*='challenges.cloudflare.com'][src*='turnstile']")
            if turnstile_iframe.count() > 0:
                box = turnstile_iframe.first.bounding_box()
                if box:
                    return self._click_turnstile_checkbox(box)

            # Strategy 2: Find iframe by id pattern (cf-chl-widget-*)
            cf_widget_iframe = self.page.locator("iframe[id^='cf-chl-widget']")
            if cf_widget_iframe.count() > 0:
                box = cf_widget_iframe.first.bounding_box()
                if box:
                    return self._click_turnstile_checkbox(box)

            # Strategy 3: Find any iframe from challenges.cloudflare.com
            cf_challenge_iframe = self.page.locator("iframe[src*='challenges.cloudflare.com']")
            if cf_challenge_iframe.count() > 0:
                box = cf_challenge_iframe.first.bounding_box()
                if box:
                    return self._click_turnstile_checkbox(box)

            # Strategy 4: Use JavaScript to find iframe in closed shadow DOM and get its position
            # The shadow DOM container typically has a visible size matching the iframe
            iframe_info = self.page.evaluate("""
                () => {
                    // Look for elements that might contain the Turnstile widget
                    const selectors = [
                        'div[style*="display: grid"]',
                        'div[style*="grid"]',
                        '[class*="turnstile"]',
                        '[class*="cf-"]',
                        '[id*="turnstile"]'
                    ];

                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            const rect = el.getBoundingClientRect();
                            // Turnstile widget is typically 300x65 pixels
                            if (rect.width >= 280 && rect.width <= 320 &&
                                rect.height >= 50 && rect.height <= 80 &&
                                rect.top > 0 && rect.left >= 0) {
                                return {
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height,
                                    found: true
                                };
                            }
                        }
                    }

                    // Also try to find by looking for elements with the right size
                    const allDivs = document.querySelectorAll('div');
                    for (const div of allDivs) {
                        const rect = div.getBoundingClientRect();
                        if (rect.width >= 280 && rect.width <= 320 &&
                            rect.height >= 50 && rect.height <= 80 &&
                            rect.top > 100 && rect.left >= 0) {
                            // Check if it has shadow root or contains turnstile-related elements
                            const html = div.innerHTML.toLowerCase();
                            if (html.includes('turnstile') || html.includes('cf-') ||
                                div.shadowRoot || html.includes('challenge')) {
                                return {
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height,
                                    found: true
                                };
                            }
                        }
                    }

                    return { found: false };
                }
            """)

            if iframe_info and iframe_info.get("found"):
                return self._click_turnstile_checkbox(iframe_info)

            # Strategy 5: Find the hidden input and click near it
            # The cf-turnstile-response input is usually next to the widget
            hidden_input = self.page.locator("input[name='cf-turnstile-response'], input[id*='cf-chl-widget'][id*='_response']")
            if hidden_input.count() > 0:
                # Get the parent element and click on it
                parent_box = self.page.evaluate("""
                    () => {
                        const input = document.querySelector("input[name='cf-turnstile-response'], input[id*='cf-chl-widget'][id*='_response']");
                        if (input && input.parentElement) {
                            // Go up to find a reasonably sized container
                            let el = input.parentElement;
                            for (let i = 0; i < 5 && el; i++) {
                                const rect = el.getBoundingClientRect();
                                if (rect.width >= 280 && rect.height >= 50) {
                                    return { x: rect.x, y: rect.y, width: rect.width, height: rect.height, found: true };
                                }
                                el = el.parentElement;
                            }
                        }
                        return { found: false };
                    }
                """)
                if parent_box and parent_box.get("found"):
                    return self._click_turnstile_checkbox(parent_box)

            # Strategy 6: Click on fixed coordinates based on typical Cloudflare layout
            # The Turnstile widget is usually centered horizontally and appears below the title
            verify_text = self.page.locator("text='Verify you are human'")
            if verify_text.count() > 0:
                text_box = verify_text.first.bounding_box()
                if text_box:
                    # Widget typically appears below the "Verify you are human" text
                    # Create a pseudo box for the expected widget position
                    widget_box = {
                        "x": text_box["x"],
                        "y": text_box["y"] + text_box["height"] + 20,
                        "width": 300,
                        "height": 65
                    }
                    return self._click_turnstile_checkbox(widget_box)

            # Strategy 7: Fallback to label-based checkbox (older Cloudflare style)
            checkbox = self.page.locator("label.cb-lb input[type='checkbox']")
            if checkbox.count() > 0:
                checkbox.click()
                time.sleep(random.uniform(3.0, 5.0))
                return True

            # Strategy 8: Try finding by the label text
            for text in ['Verify you are human', 'Vérifiez que vous êtes humain', 'I am human']:
                checkbox = self.page.locator(f"label:has-text('{text}') input[type='checkbox']")
                if checkbox.count() > 0:
                    checkbox.click()
                    time.sleep(random.uniform(3.0, 5.0))
                    return True

        except Exception as e:
            print(f"    Turnstile solve error: {e}")

        return False

    def solve_human_verify(self) -> bool:
        """
        Solve human verification checkbox/button challenges.

        Returns:
            True if verification element was found and clicked
        """
        try:
            # First try Cloudflare Turnstile specifically
            if self.solve_cloudflare_turnstile():
                return True

            # Try to find and click a specific captcha checkbox
            checkbox = self.page.locator(self.CAPTCHA_SELECTORS["human_verify_checkbox"]).first
            if checkbox.is_visible():
                box = checkbox.bounding_box()
                if box:
                    self._human_move_and_click(box)
                    time.sleep(random.uniform(1.0, 2.0))
                    return True

            # Try generic robot checkbox
            robot_checkbox = self.page.locator(self.CAPTCHA_SELECTORS["generic_robot_checkbox"]).first
            if robot_checkbox.is_visible():
                box = robot_checkbox.bounding_box()
                if box:
                    self._human_move_and_click(box)
                    time.sleep(random.uniform(1.0, 2.0))
                    return True

        except Exception:
            pass

        return False

    def auto_solve(self) -> bool:
        """
        Automatically detect and attempt to solve any antibot challenges.

        Returns:
            True if any challenge was detected and attempted
        """
        detection = self.detect_antibot()
        solved_any = False

        # Prioritize Cloudflare Turnstile challenge (the "Just a moment..." page)
        if detection["has_cloudflare_turnstile"]:
            solved_any = self.solve_cloudflare_challenge() or solved_any
            # If solved, no need to try other methods
            if solved_any:
                return solved_any

        if detection["has_cloudflare"]:
            solved_any = self.handle_cloudflare() or solved_any

        if detection["has_recaptcha"]:
            solved_any = self.solve_recaptcha_checkbox() or solved_any

        if detection["has_human_verify"]:
            solved_any = self.solve_human_verify() or solved_any

        if detection["has_slider"]:
            solved_any = self.solve_slider() or solved_any

        if detection["has_press_hold"]:
            solved_any = self.solve_press_and_hold() or solved_any

        if detection["has_checkbox"]:
            solved_any = self.solve_checkbox() or solved_any

        return solved_any

    def _smooth_mouse_move(self, target_x: float, target_y: float) -> None:
        """Move mouse to target with human-like motion."""
        viewport = self.page.viewport_size
        if viewport:
            current_x = viewport["width"] // 2
            current_y = viewport["height"] // 2
        else:
            current_x, current_y = 100, 100

        # Calculate distance and steps
        distance = ((target_x - current_x) ** 2 + (target_y - current_y) ** 2) ** 0.5
        steps = max(10, int(distance / 20))

        for i in range(steps):
            progress = (i + 1) / steps
            # Ease-out curve for more natural movement
            eased_progress = 1 - (1 - progress) ** 2

            x = current_x + (target_x - current_x) * eased_progress
            y = current_y + (target_y - current_y) * eased_progress

            # Add slight randomness
            x += random.uniform(-2, 2)
            y += random.uniform(-2, 2)

            self.page.mouse.move(x, y)
            time.sleep(random.uniform(0.005, 0.02))

    def _human_move_and_click(self, box: dict) -> None:
        """Move to element and click with human-like behavior."""
        x = box["x"] + box["width"] / 2 + random.randint(-3, 3)
        y = box["y"] + box["height"] / 2 + random.randint(-3, 3)

        self._smooth_mouse_move(x, y)
        time.sleep(random.uniform(0.1, 0.3))
        self.page.mouse.click(x, y)

    def _click_turnstile_checkbox(self, box: dict) -> bool:
        """
        Click on a Turnstile checkbox given its bounding box.
        The checkbox is typically on the left side of the widget.

        Args:
            box: Bounding box with x, y, width, height

        Returns:
            True after clicking
        """
        click_x = box["x"] + min(35, box["width"] / 4)
        click_y = box["y"] + box["height"] / 2
        self._smooth_mouse_move(click_x, click_y)
        time.sleep(random.uniform(0.2, 0.5))
        self.page.mouse.click(click_x, click_y)
        time.sleep(random.uniform(3.0, 6.0))
        return True

    def _human_drag(self, start_x: float, start_y: float, end_x: float) -> None:
        """Perform a human-like horizontal drag operation."""
        # Move to start position
        self._smooth_mouse_move(start_x, start_y)
        time.sleep(random.uniform(0.1, 0.3))

        # Press mouse button
        self.page.mouse.down()
        time.sleep(random.uniform(0.05, 0.15))

        # Drag with human-like motion (not perfectly straight)
        distance = end_x - start_x
        steps = max(20, int(distance / 10))

        for i in range(steps):
            progress = (i + 1) / steps
            # Add slight vertical wobble
            wobble_y = random.uniform(-3, 3)

            x = start_x + (end_x - start_x) * progress
            y = start_y + wobble_y

            self.page.mouse.move(x, y)
            time.sleep(random.uniform(0.01, 0.03))

        # Small pause at end
        time.sleep(random.uniform(0.1, 0.2))

        # Release mouse button
        self.page.mouse.up()
