"""Main orchestrator for the screenshot saver automation workflow."""

import sys
import json
import atexit
import signal
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

from config import Settings
from utils import WordReader, TextReader, OpenAIExtractor, ChromeManager
from pages import GenericPage


def _sigterm_handler(signum, frame):
    """Handle SIGTERM signal to ensure Chrome cleanup."""
    print("\n    Received SIGTERM, cleaning up...")
    ChromeManager.cleanup()
    sys.exit(1)


# Register SIGTERM handler (for kill command)
# SIGINT (Ctrl+C) is handled by KeyboardInterrupt exception
signal.signal(signal.SIGTERM, _sigterm_handler)


def process_url(page, extractor: OpenAIExtractor | None, url: str, index: int, output_dir: Path) -> dict:
    """
    Process a single URL: navigate, screenshot, and extract data.

    Args:
        page: Playwright Page object
        extractor: OpenAI extractor instance
        url: URL to process
        index: URL index for naming
        output_dir: Output directory for screenshots

    Returns:
        Dictionary with processing results
    """
    print(f"\n[{index}] Processing: {url}")

    generic_page = GenericPage(page, openai_extractor=extractor, output_dir=output_dir)

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
        output_dir: Output directory (session folder)

    Returns:
        Path to the results file
    """
    results_file = output_dir / "results.json"

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


def get_reader(file_path: Path):
    """Get the appropriate reader based on file extension."""
    ext = file_path.suffix.lower()
    if ext == ".docx":
        return WordReader(file_path)
    elif ext == ".txt":
        return TextReader(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def select_files(files: list[Path]) -> list[Path]:
    """Prompt user to select which files to process."""
    print("\nAvailable files:")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")
    print(f"  {len(files) + 1}. Process ALL files")

    while True:
        try:
            choice = input("\nSelect file(s) to process (number or 'all'): ").strip().lower()

            if choice == 'all' or choice == str(len(files) + 1):
                return files

            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return [files[idx]]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number or 'all'.")
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            sys.exit(0)


def main(file_path: str | None = None) -> None:
    """
    Main entry point for the automation workflow.

    Args:
        file_path: Path to file containing URLs (.docx or .txt)
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

    # Get URL file(s)
    if file_path:
        selected_files = [Path(file_path)]
        print(f"\nUsing file: {file_path}")
    else:
        # Look for .docx and .txt files in data directory
        docx_files = list(Settings.DATA_DIR.glob("*.docx"))
        txt_files = list(Settings.DATA_DIR.glob("*.txt"))
        all_files = sorted(docx_files + txt_files, key=lambda f: f.name)

        if not all_files:
            print(f"\nNo .docx or .txt files found in {Settings.DATA_DIR}")
            print("Please add a file with URLs to process.")
            sys.exit(1)

        if len(all_files) == 1:
            selected_files = all_files
            print(f"\nUsing file: {all_files[0].name}")
        else:
            selected_files = select_files(all_files)

    # Read URLs from selected file(s)
    urls = []
    for f in selected_files:
        try:
            reader = get_reader(f)
            file_urls = reader.extract_urls()
            print(f"\n{f.name}: {len(file_urls)} URL(s) found")
            urls.extend(file_urls)
        except Exception as e:
            print(f"\nError reading {f.name}: {e}")
            continue

    if not urls:
        print("\nNo URLs found in the selected file(s).")
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

    # Create session folder with date
    session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = Settings.OUTPUT_DIR / f"session_{session_timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nSession folder: {session_dir}")

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
                    result = process_url(page, extractor, url, index, session_dir)
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

    # Save results in session folder
    results_file = save_results(results, session_dir)

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
    # Accept optional file path as command line argument (.docx or .txt)
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    main(file_path)
