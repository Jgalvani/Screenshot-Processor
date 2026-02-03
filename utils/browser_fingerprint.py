"""Browser fingerprint configuration for antibot evasion."""

import random

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

# Timezone to locale mapping
TIMEZONE_LOCALE_MAP = {
    # English - United States
    "America/New_York": "en-US",
    "America/Chicago": "en-US",
    "America/Denver": "en-US",
    "America/Los_Angeles": "en-US",
    # English - Other
    "America/Toronto": "en-CA",
    "Europe/London": "en-GB",
    "Europe/Dublin": "en-IE",
    "Australia/Sydney": "en-AU",
    # French
    "America/Montreal": "fr-CA",
    "Europe/Paris": "fr-FR",
    "Europe/Brussels": "fr-BE",
    "Europe/Zurich": "fr-CH",
}


def get_random_user_agent() -> str:
    """Get a random user agent string."""
    return random.choice(USER_AGENTS)


def get_random_viewport() -> dict:
    """Get a random viewport size."""
    return random.choice(SCREEN_RESOLUTIONS)


def get_random_timezone() -> str:
    """Get a random timezone."""
    return random.choice(list(TIMEZONE_LOCALE_MAP.keys()))


def get_browser_context_options() -> dict:
    """Get randomized browser context options for better antibot evasion."""
    user_agent = get_random_user_agent()
    viewport = get_random_viewport()
    timezone = get_random_timezone()
    locale = TIMEZONE_LOCALE_MAP[timezone]

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
