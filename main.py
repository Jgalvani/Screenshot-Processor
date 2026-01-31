"""Main orchestrator for the screenshot saver automation workflow."""

import sys
import json
import atexit
import signal
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

from config import Settings
from utils import WordReader, OpenAIExtractor, ChromeManager
from pages import GenericPage


def _sigterm_handler(signum, frame):
    """Handle SIGTERM signal to ensure Chrome cleanup."""
    print("\n    Received SIGTERM, cleaning up...")
    ChromeManager.cleanup()
    sys.exit(1)


# Register SIGTERM handler (for kill command)
# SIGINT (Ctrl+C) is handled by KeyboardInterrupt exception
signal.signal(signal.SIGTERM, _sigterm_handler)


def process_url(page, extractor: OpenAIExtractor | None, url: str, index: int) -> dict:
    """
    Process a single URL: navigate, screenshot, and extract data.

    Args:
        page: Playwright Page object
        extractor: OpenAI extractor instance
        url: URL to process
        index: URL index for naming

    Returns:
        Dictionary with processing results
    """
    print(f"\n[{index}] Processing: {url}")

    generic_page = GenericPage(page, openai_extractor=extractor)

    try:
        # Navigate to URL
        generic_page.navigate(url)
        print(f"    Page loaded: {generic_page.get_title()}")

        # Check if we're still on a Cloudflare challenge page after navigation
        # (navigation handler might have already tried to solve it)
        if generic_page.antibot.is_cloudflare_challenge_page():
            print("    Still on Cloudflare challenge page, retrying...")
            if generic_page.antibot.solve_cloudflare_challenge(max_attempts=3):
                print("    Cloudflare challenge solved!")
                generic_page.human.wait_for_page_ready()
            else:
                print("    Warning: Could not solve Cloudflare challenge")

        # Only handle antibot challenges on actual challenge pages
        # Check if this is a challenge/verification page (not a normal product page)
        page_title = generic_page.get_title().lower()
        is_challenge_page = any(term in page_title for term in [
            "just a moment", "verify", "access denied", "blocked",
            "security check", "challenge", "captcha"
        ])

        if is_challenge_page:
            print("    Antibot challenge detected, attempting to solve...")
            if generic_page.antibot.auto_solve():
                print("    Challenge handled, waiting for page...")
                generic_page.human.wait_for_page_ready()

        # Capture and extract
        result = generic_page.capture_and_extract(
            screenshot_name=f"url_{index}"
        )

        print(f"    Screenshot saved: {result['screenshot_path']}")

        if result.get("product_info"):
            print(f"    Product: {result['product_info'].get('product_name', 'N/A')}")
            print(f"    Final price: {result.get('final_price', 'N/A')}")

        return {
            "success": True,
            "url": url,
            "index": index,
            **result
        }

    except Exception as e:
        print(f"    Error: {str(e)}")
        return {
            "success": False,
            "url": url,
            "index": index,
            "error": str(e)
        }


def save_results(results: list[dict], output_dir: Path) -> Path:
    """
    Save processing results to a JSON file.

    Args:
        results: List of processing results
        output_dir: Output directory

    Returns:
        Path to the results file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"results_{timestamp}.json"

    # Convert Path objects to strings for JSON serialization
    serializable_results = []
    for result in results:
        r = result.copy()
        if "screenshot_path" in r and r["screenshot_path"]:
            r["screenshot_path"] = str(r["screenshot_path"])
        serializable_results.append(r)

    with open(results_file, "w") as f:
        json.dump(serializable_results, f, indent=2)

    return results_file


def main(word_file_path: str | None = None) -> None:
    """
    Main entry point for the automation workflow.

    Args:
        word_file_path: Path to Word document containing URLs
    """
    print("=" * 60)
    print("Screenshot Saver - Browser Automation Workflow")
    print("=" * 60)

    # Validate settings
    Settings.ensure_directories()
    errors = Settings.validate()
    if errors:
        print("\nConfiguration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease check your .env file and try again.")
        sys.exit(1)

    # Get Word file path
    if word_file_path:
        word_path = Path(word_file_path)
    else:
        # Look for .docx files in data directory
        docx_files = list(Settings.DATA_DIR.glob("*.docx"))
        if not docx_files:
            print(f"\nNo .docx files found in {Settings.DATA_DIR}")
            print("Please add a Word document with URLs to process.")
            sys.exit(1)
        word_path = docx_files[0]
        print(f"\nUsing Word file: {word_path}")

    # Read URLs from Word document
    try:
        reader = WordReader(word_path)
        urls = reader.extract_urls()
    except Exception as e:
        print(f"\nError reading Word document: {e}")
        sys.exit(1)

    if not urls:
        print("\nNo URLs found in the Word document.")
        sys.exit(1)

    print(f"\nFound {len(urls)} URL(s) to process:")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")

    # Initialize OpenAI extractor (skip if SKIP_EXTRACTION is enabled)
    extractor = None
    if Settings.SKIP_EXTRACTION:
        print("\n[SKIP_EXTRACTION mode] Skipping OpenAI extraction")
    else:
        try:
            extractor = OpenAIExtractor()
        except ValueError as e:
            print(f"\nOpenAI setup error: {e}")
            sys.exit(1)

    # Process URLs sequentially
    results = []

    # Register cleanup for unexpected exits (backup for atexit)
    atexit.register(ChromeManager.cleanup)

    browser = None
    try:
        with sync_playwright() as playwright:
            browser, page = GenericPage.create_browser_context(playwright)

            try:
                for index, url in enumerate(urls, 1):
                    result = process_url(page, extractor, url, index)
                    results.append(result)

            finally:
                # Close browser connection
                if browser:
                    try:
                        browser.close()
                    except Exception:
                        pass

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Cleaning up...")

    finally:
        # Always cleanup Chrome process
        ChromeManager.cleanup()
        # Unregister atexit since we've already cleaned up
        try:
            atexit.unregister(ChromeManager.cleanup)
        except Exception:
            pass

    # Save results
    results_file = save_results(results, Settings.OUTPUT_DIR)

    # Summary
    print("\n" + "=" * 60)
    print("Processing Complete")
    print("=" * 60)

    successful = sum(1 for r in results if r.get("success"))
    print(f"\nProcessed: {len(results)} URLs")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    print(f"\nResults saved to: {results_file}")

    # Print final prices if available
    prices = [
        (r.get("product_info", {}).get("product_name"), r.get("final_price"))
        for r in results
        if r.get("success") and r.get("final_price")
    ]
    if prices:
        print("\nExtracted Prices:")
        for name, price in prices:
            print(f"  - {name or 'Unknown'}: {price}")


if __name__ == "__main__":
    # Accept optional Word file path as command line argument
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    main(file_path)
