"""Cloudflare challenge detection and solving utilities."""

from playwright.sync_api import Page

from utils import BoundingBox, HumanBehavior


class CloudflareHandler:
    """Handles Cloudflare challenge detection and solving."""

    # Cloudflare-specific selectors
    SELECTORS = {
        "checkbox_iframe": "iframe[src*='challenges.cloudflare']",
        "turnstile": "#cf-turnstile",
        "turnstile_container": "[class*='cf-turnstile'], [id*='turnstile'], [id*='cf-'], [class*='turnstile']",
        "turnstile_clickable": "[class*='cf-turnstile'] input, [class*='cf-turnstile'] [role='checkbox'], #challenge-stage input, .cf-turnstile-wrapper input",
    }

    def __init__(self, page: Page):
        """Initialize CloudflareHandler with a Playwright page."""
        self.page = page
        self.human = HumanBehavior(page)

    def is_challenge_page(self) -> bool:
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

    def solve_challenge(self, max_attempts: int = 3, wait_after_solve: float = 5.0) -> bool:
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
        if not self.is_challenge_page():
            return False

        print("    Cloudflare challenge page detected, attempting to solve...")

        for attempt in range(max_attempts):
            try:
                # Attempt to solve the Turnstile
                if self.solve_turnstile():
                    print(f"    Turnstile clicked (attempt {attempt + 1})")

                    # Wait for the verification to complete
                    self.human.wait_for_ready(timeout=int(wait_after_solve * 1000))

                    # Check if we're still on a challenge page
                    if not self.is_challenge_page():
                        print("    Challenge solved successfully!")
                        return True

            except Exception as e:
                print(f"    Challenge solve attempt {attempt + 1} failed: {e}")

        print("    Failed to solve Cloudflare challenge after max attempts")
        return False

    def solve_turnstile(self) -> bool:
        """
        Solve Cloudflare Turnstile "Verify you are human" challenge.

        The Turnstile widget is typically inside an iframe from challenges.cloudflare.com.
        The iframe may be inside a closed shadow DOM, so we need multiple strategies.

        Returns:
            True if turnstile was found and clicked
        """
        try:
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
            hidden_input = self.page.locator("input[name='cf-turnstile-response'], input[id*='cf-chl-widget'][id*='_response']")
            if hidden_input.count() > 0:
                parent_box = self.page.evaluate("""
                    () => {
                        const input = document.querySelector("input[name='cf-turnstile-response'], input[id*='cf-chl-widget'][id*='_response']");
                        if (input && input.parentElement) {
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
            verify_text = self.page.locator("text='Verify you are human'")
            if verify_text.count() > 0:
                text_box = verify_text.first.bounding_box()
                if text_box:
                    widget_box: BoundingBox = {
                        "x": text_box["x"],
                        "y": text_box["y"] + text_box["height"] + 20,
                        "width": 300.0,
                        "height": 65.0
                    }
                    return self._click_turnstile_checkbox(widget_box)

            # Strategy 7: Fallback to label-based checkbox (older Cloudflare style)
            checkbox = self.page.locator("label.cb-lb input[type='checkbox']")
            if checkbox.count() > 0:
                checkbox.click()
                return True

            # Strategy 8: Try finding by the label text
            for text in ['Verify you are human', 'Vérifiez que vous êtes humain', 'I am human']:
                checkbox = self.page.locator(f"label:has-text('{text}') input[type='checkbox']")
                if checkbox.count() > 0:
                    checkbox.click()
                    return True

        except Exception as e:
            print(f"    Turnstile solve error: {e}")

        return False

    def _click_turnstile_checkbox(self, box: BoundingBox) -> bool:
        """
        Click on a Turnstile checkbox given its bounding box.
        The checkbox is typically on the left side of the widget.

        Args:
            box: Bounding box with x, y, width, height

        Returns:
            True after clicking
        """
        # Turnstile checkbox is on the left side of the widget
        click_x = box["x"] + min(35, box["width"] / 4)
        click_y = box["y"] + box["height"] / 2
        self.human.click_at(click_x, click_y)
        return True
