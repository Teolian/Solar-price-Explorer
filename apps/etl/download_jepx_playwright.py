#!/usr/bin/env python3
"""
Automated JEPX CSV Download using Playwright

This script uses a headless browser to download JEPX spot market data,
bypassing WAF/bot protection by simulating real user behavior.

SETUP:
  pip install playwright
  playwright install chromium

USAGE:
  python download_jepx_playwright.py --year 2024 --output data/jepx/spot_2024.csv
  python download_jepx_playwright.py --year 2025 --type summary --headless false
"""
import os
import sys
import argparse
import logging
import time
from pathlib import Path
from typing import Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: Playwright not installed!")
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
JEPX_SPOT_URL = "https://www.jepx.jp/electricpower/market-data/spot/"
DEFAULT_TIMEOUT = 30000  # 30 seconds
DOWNLOAD_TIMEOUT = 120000  # 2 minutes for large files


class JEPXDownloader:
    """Automated JEPX data downloader using Playwright"""

    def __init__(self, headless: bool = True, slow_mo: int = 100):
        """
        Initialize downloader

        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations by N milliseconds (helps with detection)
        """
        self.headless = headless
        self.slow_mo = slow_mo

    def download_spot_data(
        self,
        year: int,
        output_path: str,
        data_type: str = "spot"
    ) -> bool:
        """
        Download JEPX spot market data for specified year

        Args:
            year: Year to download (e.g., 2024, 2025)
            output_path: Path to save downloaded CSV
            data_type: "spot" for full data or "summary" for aggregated

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting Playwright download for year {year}")
        logger.info(f"Data type: {data_type}")
        logger.info(f"Output: {output_path}")

        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=[
                    '--disable-blink-features=AutomationControlled',  # Hide automation
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )

            # Create context with realistic settings
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='ja-JP',
                timezone_id='Asia/Tokyo',
                accept_downloads=True
            )

            # Override navigator.webdriver flag
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = context.new_page()

            try:
                # Step 1: Navigate to JEPX spot page
                logger.info(f"Navigating to {JEPX_SPOT_URL}")
                page.goto(JEPX_SPOT_URL, wait_until='networkidle', timeout=DEFAULT_TIMEOUT)

                # Human-like pause
                time.sleep(2)

                # Step 2: Look for "Data Download" button or link
                # JEPX page structure may vary, try multiple selectors
                download_selectors = [
                    'text=Data Download',
                    'text=データダウンロード',
                    'a:has-text("Data Download")',
                    'button:has-text("Data Download")',
                    'a:has-text("ダウンロード")',
                    '[href*="download"]',
                ]

                download_button = None
                for selector in download_selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        element = page.locator(selector).first
                        if element.is_visible(timeout=5000):
                            download_button = element
                            logger.info(f"✓ Found download button: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} not found: {e}")
                        continue

                if not download_button:
                    # If no button found, take screenshot for debugging
                    screenshot_path = output_dir / "jepx_page_debug.png"
                    page.screenshot(path=str(screenshot_path))
                    logger.error(f"Could not find download button. Screenshot saved to {screenshot_path}")

                    # Print page content for debugging
                    logger.info("Page content sample:")
                    logger.info(page.content()[:500])

                    return False

                # Step 3: Click download button
                logger.info("Clicking download button...")
                download_button.click()
                time.sleep(2)  # Wait for modal/form to appear

                # Step 4: Look for year selector (might be dropdown or input)
                year_selectors = [
                    f'select >> text={year}',
                    f'option:has-text("{year}")',
                    f'input[value="{year}"]',
                    'select[name*="year"]',
                    'select[name*="Year"]',
                    'select.year-selector'
                ]

                year_selected = False
                for selector in year_selectors:
                    try:
                        logger.info(f"Trying year selector: {selector}")

                        # If it's a select element
                        if 'select' in selector:
                            select = page.locator(selector).first
                            if select.is_visible(timeout=3000):
                                select.select_option(label=str(year))
                                logger.info(f"✓ Selected year {year}")
                                year_selected = True
                                break
                        else:
                            element = page.locator(selector).first
                            if element.is_visible(timeout=3000):
                                element.click()
                                logger.info(f"✓ Selected year {year}")
                                year_selected = True
                                break
                    except Exception as e:
                        logger.debug(f"Year selector {selector} failed: {e}")
                        continue

                if not year_selected:
                    logger.warning(f"Could not find year selector for {year}")
                    logger.warning("Proceeding anyway - might default to current year")

                time.sleep(1)

                # Step 5: Look for final download/submit button
                submit_selectors = [
                    'button:has-text("ダウンロード")',
                    'button:has-text("Download")',
                    'input[type="submit"]',
                    'button[type="submit"]',
                    'a:has-text("ダウンロード")',
                ]

                # Setup download handler
                download_info = None

                with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_promise:
                    submit_clicked = False
                    for selector in submit_selectors:
                        try:
                            logger.info(f"Trying submit selector: {selector}")
                            element = page.locator(selector).first
                            if element.is_visible(timeout=3000):
                                logger.info("Clicking submit button...")
                                element.click()
                                submit_clicked = True
                                break
                        except Exception as e:
                            logger.debug(f"Submit selector {selector} failed: {e}")
                            continue

                    if not submit_clicked:
                        logger.error("Could not find submit button!")
                        return False

                    # Wait for download to start
                    download_info = download_promise.value

                # Step 6: Save downloaded file
                logger.info("Download started, saving file...")
                download_info.save_as(output_path)

                # Verify file was downloaded
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"✓ Download complete!")
                    logger.info(f"  File: {output_path}")
                    logger.info(f"  Size: {file_size:,} bytes")

                    # Quick validation - check if it looks like a CSV
                    with open(output_path, 'rb') as f:
                        header = f.read(100)
                        try:
                            # Try to decode as Shift_JIS
                            header_text = header.decode('cp932')
                            if '年月日' in header_text or '時刻' in header_text or 'Date' in header_text:
                                logger.info("✓ File appears to be valid JEPX CSV")
                            else:
                                logger.warning(f"Warning: File might not be CSV. Header: {header_text[:50]}")
                        except Exception as e:
                            logger.warning(f"Could not validate file: {e}")

                    return True
                else:
                    logger.error("Download failed - file not found")
                    return False

            except PlaywrightTimeout as e:
                logger.error(f"Timeout error: {e}")
                screenshot_path = output_dir / "jepx_timeout_debug.png"
                page.screenshot(path=str(screenshot_path))
                logger.error(f"Screenshot saved to {screenshot_path}")
                return False

            except Exception as e:
                logger.error(f"Error during download: {e}")
                screenshot_path = output_dir / "jepx_error_debug.png"
                try:
                    page.screenshot(path=str(screenshot_path))
                    logger.error(f"Screenshot saved to {screenshot_path}")
                except:
                    pass
                return False

            finally:
                context.close()
                browser.close()


def main():
    parser = argparse.ArgumentParser(
        description='Download JEPX data using Playwright automation'
    )
    parser.add_argument(
        '--year',
        type=int,
        required=True,
        help='Year to download (e.g., 2024, 2025)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output CSV file path (e.g., data/jepx/spot_2024.csv)'
    )
    parser.add_argument(
        '--type',
        type=str,
        default='spot',
        choices=['spot', 'summary'],
        help='Data type: "spot" (full 48-slot data) or "summary" (aggregated)'
    )
    parser.add_argument(
        '--headless',
        type=lambda x: x.lower() == 'true',
        default=True,
        help='Run in headless mode (default: true)'
    )
    parser.add_argument(
        '--slow-mo',
        type=int,
        default=100,
        help='Slow down by N milliseconds (default: 100)'
    )

    args = parser.parse_args()

    # Create downloader
    downloader = JEPXDownloader(
        headless=args.headless,
        slow_mo=args.slow_mo
    )

    # Download data
    success = downloader.download_spot_data(
        year=args.year,
        output_path=args.output,
        data_type=args.type
    )

    if success:
        logger.info("\n" + "="*60)
        logger.info("SUCCESS! JEPX data downloaded")
        logger.info("="*60)
        logger.info(f"File: {args.output}")
        logger.info("\nNext steps:")
        logger.info(f"  1. Import to database:")
        logger.info(f"     python apps/etl/import_jepx_csv.py --file {args.output}")
        logger.info(f"  2. Or use Makefile:")
        logger.info(f"     make import-jepx-csv")
        logger.info("="*60 + "\n")
        return 0
    else:
        logger.error("\n" + "="*60)
        logger.error("FAILED to download JEPX data")
        logger.error("="*60)
        logger.error("Check the debug screenshots in the output directory")
        logger.error("You may need to:")
        logger.error("  1. Update selectors if JEPX changed their website")
        logger.error("  2. Run with --headless false to see what's happening")
        logger.error("  3. Fall back to manual download:")
        logger.error("     https://www.jepx.jp/electricpower/market-data/spot/")
        logger.error("="*60 + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
