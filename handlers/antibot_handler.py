"""Antibot detection and challenge solving utilities."""

import random
import time

from playwright.sync_api import Page

from utils import BoundingBox


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
                        self._human_move_and_click(box)
                        self._wait_for_state_change()
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
                checkbox.click()
                self._wait_for_state_change()
                return True

        except Exception:
            pass

        return False

    def solve_press_and_hold(self, selector: str | None = None, hold_duration: float | None = None) -> bool:
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

                    # Press and hold (duration is the actual functionality)
                    duration = hold_duration or random.uniform(2.0, 4.0)
                    self.page.mouse.down()
                    time.sleep(duration)
                    self.page.mouse.up()

                    self._wait_for_state_change()
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
                self._wait_for_state_change()
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
                    return self._try_puzzle_drag_positions(handle)

            if handle:
                handle_box = handle.bounding_box()
                if handle_box:
                    return self._try_puzzle_drag_positions(handle_box)

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
            self._wait_for_state_change()

            # First, try the Turnstile-specific solver
            if self.solve_cloudflare_turnstile():
                return True

            # Check for turnstile widget by ID
            turnstile = self.page.locator(self.CAPTCHA_SELECTORS["cloudflare_turnstile"])
            if turnstile.count() > 0:
                box = turnstile.bounding_box()
                if box:
                    self._human_move_and_click(box)
                    return True

            # Check for checkbox in iframe
            cf_iframe = self.page.locator(self.CAPTCHA_SELECTORS["cloudflare_checkbox"])
            if cf_iframe.count() > 0:
                cf_iframe.click()
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
                self._wait_for_state_change()

                # Attempt to solve the Turnstile
                if self.solve_cloudflare_turnstile():
                    print(f"    Turnstile clicked (attempt {attempt + 1})")

                    # Wait for the verification to complete
                    self._wait_for_state_change(timeout=int(wait_after_solve * 1000))

                    # Check if we're still on a challenge page
                    if not self.is_cloudflare_challenge_page():
                        print("    Challenge solved successfully!")
                        return True

            except Exception as e:
                print(f"    Challenge solve attempt {attempt + 1} failed: {e}")

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
            self._wait_for_state_change()

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
                    return True

            # Try generic robot checkbox
            robot_checkbox = self.page.locator(self.CAPTCHA_SELECTORS["generic_robot_checkbox"]).first
            if robot_checkbox.is_visible():
                box = robot_checkbox.bounding_box()
                if box:
                    self._human_move_and_click(box)
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

    def _wait_for_state_change(self, timeout: int = 5000) -> None:
        """Wait for page state to change after an action (click, solve, etc.)."""
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except Exception:
            pass

    def _human_move_and_click(self, box: BoundingBox) -> None:
        """Move to element and click with human-like behavior."""
        x = box["x"] + box["width"] / 2 + random.randint(-3, 3)
        y = box["y"] + box["height"] / 2 + random.randint(-3, 3)

        self._smooth_mouse_move(x, y)
        time.sleep(random.uniform(0.1, 0.3))
        self.page.mouse.click(x, y)

    def _click_turnstile_checkbox(self, box: BoundingBox) -> bool:
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
        return True

    def _try_puzzle_drag_positions(self, handle_box: BoundingBox) -> bool:
        """
        Try dragging a puzzle slider to multiple positions.

        Args:
            handle_box: Bounding box of the slider handle (x, y, width, height)

        Returns:
            True if puzzle was solved or all positions were tried
        """
        track_width = 200  # Approximate width in pixels
        offset_attempts = [0.65, 0.55, 0.75, 0.45, 0.85]  # Positions to try (center first)

        start_x = handle_box["x"] + handle_box["width"] / 2
        start_y = handle_box["y"] + handle_box["height"] / 2

        for offset_percent in offset_attempts:
            end_x = start_x + track_width * offset_percent
            self._human_drag(start_x, start_y, end_x)
            self._wait_for_state_change()

            # Check if puzzle was solved (slider might disappear)
            if self.page.locator("text='Slide to complete'").count() == 0:
                print("    Puzzle slider solved!")
                return True

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
