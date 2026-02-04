"""Antibot detection and challenge solving utilities."""

from playwright.sync_api import Page

from utils import BoundingBox, HumanBehavior
from .cloudflare_handler import CloudflareHandler


class AntibotHandler:
    """Handles antibot detection and challenge solving."""

    # Common antibot selectors (excluding Cloudflare - see CloudflareHandler)
    CAPTCHA_SELECTORS = {
        # reCAPTCHA
        "recaptcha_checkbox": "iframe[src*='recaptcha']",
        "recaptcha_checkbox_inner": "#recaptcha-anchor",
        # hCaptcha
        "hcaptcha_checkbox": "iframe[src*='hcaptcha']",
        "hcaptcha_checkbox_inner": "#checkbox",
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
        self.human = HumanBehavior(page)
        self.cloudflare = CloudflareHandler(page)

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

            # Check for Cloudflare (delegated to CloudflareHandler)
            if self.cloudflare.is_challenge_page():
                results["has_cloudflare"] = True

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

            # Check for human verification
            if self.page.locator(self.CAPTCHA_SELECTORS["human_verify_checkbox"]).count() > 0:
                results["has_human_verify"] = True
            elif self.page.locator(self.CAPTCHA_SELECTORS["generic_robot_checkbox"]).count() > 0:
                results["has_human_verify"] = True

        except Exception:
            pass

        return results

    def solve_checkbox(self, selector: str | None = None, use_iframe: bool = False) -> bool:
        """
        Solve a checkbox-type captcha by clicking it with human-like behavior.

        Args:
            selector: Optional specific selector for the checkbox
            use_iframe: If True, access checkbox via reCAPTCHA iframe

        Returns:
            True if checkbox was found and clicked
        """
        try:
            selectors_to_try = [selector] if selector else [
                self.CAPTCHA_SELECTORS["recaptcha_checkbox_inner"],
                self.CAPTCHA_SELECTORS["human_verify_checkbox"],
                self.CAPTCHA_SELECTORS["generic_robot_checkbox"],
                "input[type='checkbox']",
            ]

            # Access via iframe or directly
            if use_iframe:
                container = self.page.frame_locator(self.CAPTCHA_SELECTORS["recaptcha_checkbox"])
            else:
                container = self.page

            for sel in selectors_to_try:
                if sel and container.locator(sel).count() > 0:
                    checkbox = container.locator(sel).first
                    box = checkbox.bounding_box()

                    if box:
                        self.human.click_box(box)
                        self.human.wait_for_ready()
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
                    self.human.click_box(box, hold=True, hold_duration=hold_duration)
                    self.human.wait_for_ready()
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
                # End position (track end with some margin)
                end_x = track_box["x"] + track_box["width"] - 10

                # Perform human-like drag
                self.human.drag(handle_box, end_x)
                self.human.wait_for_ready()
                return True

        except Exception:
            pass

        return False
    
    
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

        # Calculate start_x for end position calculation
        start_x = handle_box["x"] + handle_box["width"] / 2

        for offset_percent in offset_attempts:
            end_x = start_x + track_width * offset_percent
            self.human.drag(handle_box, end_x)
            self.human.wait_for_ready()

            # Check if puzzle was solved (slider might disappear)
            if self.page.locator("text='Slide to complete'").count() == 0:
                print("    Puzzle slider solved!")
                return True

        return True

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
    

    def auto_solve(self) -> bool:
        """
        Automatically detect and attempt to solve any antibot challenges.

        Returns:
            True if a challenge was solved
        """
        detection = self.detect_antibot()

        if detection["has_cloudflare"] and self.cloudflare.solve_challenge():
            return True

        if detection["has_recaptcha"] and self.solve_checkbox(use_iframe=True):
            return True

        if detection["has_human_verify"] and self.solve_checkbox():
            return True

        if detection["has_slider"] and self.solve_slider():
            return True

        if detection["has_press_hold"] and self.solve_press_and_hold():
            return True

        if detection["has_checkbox"] and self.solve_checkbox():
            return True

        return False

