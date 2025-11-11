#!/usr/bin/env python3
"""
Automated TEPCO Demand Data Download using Playwright

Downloads electricity demand data from TEPCO (Tokyo Electric Power Company)
bypassing WAF/bot protection by simulating real browser behavior.

Source: https://www.tepco.co.jp/en/forecast/html/download-e.html

SETUP:
  pip install playwright
  playwright install chromium

USAGE:
  python download_tepco_playwright.py --year 2025 --month 9 --output data/tepco/
  python download_tepco_playwright.py --year 2025 --month 10 --headless false
"""
import os
import sys
import argparse
import logging
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

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
TEPCO_DOWNLOAD_URL = "https://www.tepco.co.jp/en/forecast/html/download-e.html"
TEPCO_DOWNLOAD_JP_URL = "https://www.tepco.co.jp/forecast/html/download-j.html"
DEFAULT_TIMEOUT = 60000  # 60 seconds (increased for slow connections)
DOWNLOAD_TIMEOUT = 120000  # 2 minutes


class TEPCODownloader:
    """Automated TEPCO demand data downloader using Playwright"""

    def __init__(self, headless: bool = True, slow_mo: int = 100):
        """
        Initialize downloader

        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations by N milliseconds
        """
        self.headless = headless
        self.slow_mo = slow_mo

    def download_demand_data(
        self,
        year: int,
        month: int,
        output_dir: str,
        use_japanese: bool = False
    ) -> Optional[str]:
        """
        Download TEPCO demand data for specified year and month

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            output_dir: Directory to save downloaded files
            use_japanese: Use Japanese page instead of English

        Returns:
            Path to downloaded file if successful, None otherwise
        """
        logger.info(f"Starting TEPCO download for {year}-{month:02d}")
        logger.info(f"Output directory: {output_dir}")

        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Choose URL
        url = TEPCO_DOWNLOAD_JP_URL if use_japanese else TEPCO_DOWNLOAD_URL

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=[
                    '--disable-blink-features=AutomationControlled',
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
                # Step 1: Navigate to TEPCO download page
                logger.info(f"Navigating to {url}")
                page.goto(url, wait_until='networkidle', timeout=DEFAULT_TIMEOUT)

                # Human-like pause
                time.sleep(2)

                # Take screenshot for debugging
                debug_path = output_path / f"tepco_page_{year}_{month:02d}.png"
                page.screenshot(path=str(debug_path))
                logger.info(f"Screenshot saved: {debug_path}")

                # Step 2: Look for download links
                # TEPCO might have:
                # - Direct CSV download links
                # - Monthly archive ZIP files
                # - Daily CSV files with pattern juyo-YYYYMMDD.csv

                # Try different approaches
                downloaded_file = None

                # Approach 1: Look for monthly ZIP or CSV download links
                logger.info("Looking for download links...")

                # Common patterns for TEPCO data files
                date_patterns = [
                    f"{year}{month:02d}",  # YYYYMM
                    f"{year}-{month:02d}",  # YYYY-MM
                    f"juyo-{year}{month:02d}",  # juyo-YYYYMM
                ]

                link_selectors = [
                    f'a[href*="{pattern}"]' for pattern in date_patterns
                ] + [
                    'a[href*=".csv"]',
                    'a[href*=".zip"]',
                    'a[href*="juyo-"]',
                    'a:has-text("CSV")',
                    'a:has-text("download")',
                ]

                download_link = None
                for selector in link_selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        elements = page.locator(selector).all()

                        for element in elements:
                            if element.is_visible(timeout=3000):
                                href = element.get_attribute('href')
                                text = element.text_content()
                                logger.info(f"  Found link: {text} -> {href}")

                                # Check if link matches our year/month
                                if any(pattern in str(href) for pattern in date_patterns):
                                    download_link = element
                                    logger.info(f"✓ Selected download link for {year}-{month:02d}")
                                    break
                                # Note: Removed fallback to "any CSV/ZIP" - we want specific year/month only

                        if download_link:
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue

                if not download_link:
                    logger.error("Could not find download link")
                    logger.info("Available links on page:")
                    all_links = page.locator('a[href]').all()
                    for link in all_links[:20]:  # Show first 20 links
                        try:
                            href = link.get_attribute('href')
                            text = link.text_content()
                            logger.info(f"  {text} -> {href}")
                        except:
                            pass

                    # Approach 2: Try direct URL construction
                    logger.info("Trying direct URL approach...")
                    return self._try_direct_download(context, year, month, output_path)

                # Step 3: Click download link
                logger.info("Clicking download link...")

                with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_promise:
                    download_link.click()
                    download_info = download_promise.value

                # Step 4: Save downloaded file
                logger.info("Download started, saving file...")

                # Generate filename
                original_filename = download_info.suggested_filename
                if original_filename:
                    output_file = output_path / original_filename
                else:
                    # Generate our own filename
                    output_file = output_path / f"tepco_demand_{year}{month:02d}.csv"

                download_info.save_as(str(output_file))

                # Verify file was downloaded
                if output_file.exists():
                    file_size = output_file.stat().st_size
                    logger.info(f"✓ Download complete!")
                    logger.info(f"  File: {output_file}")
                    logger.info(f"  Size: {file_size:,} bytes")

                    # Quick validation
                    with open(output_file, 'rb') as f:
                        header = f.read(200)
                        try:
                            # Try Shift-JIS decoding
                            header_text = header.decode('shift_jis')
                            logger.info(f"  Header preview: {header_text[:100]}")

                            if 'TIME' in header_text or '時刻' in header_text:
                                logger.info("✓ File appears to be valid TEPCO CSV")
                            else:
                                logger.warning(f"Warning: File might not be TEPCO demand CSV")
                        except Exception as e:
                            logger.warning(f"Could not validate file: {e}")

                    return str(output_file)
                else:
                    logger.error("Download failed - file not found")
                    return None

            except PlaywrightTimeout as e:
                logger.error(f"Timeout error: {e}")
                screenshot_path = output_path / f"tepco_timeout_{year}_{month:02d}.png"
                page.screenshot(path=str(screenshot_path))
                logger.error(f"Screenshot saved to {screenshot_path}")
                return None

            except Exception as e:
                logger.error(f"Error during download: {e}")
                import traceback
                traceback.print_exc()
                screenshot_path = output_path / f"tepco_error_{year}_{month:02d}.png"
                try:
                    page.screenshot(path=str(screenshot_path))
                    logger.error(f"Screenshot saved to {screenshot_path}")
                except:
                    pass
                return None

            finally:
                context.close()
                browser.close()

    def _try_direct_download(self, context, year: int, month: int, output_path: Path) -> Optional[str]:
        """
        Try direct URL download for TEPCO daily files

        TEPCO publishes daily files with pattern:
        https://www.tepco.co.jp/forecast/html/images/juyo-YYYYMMDD.csv

        Note: This attempts to download ALL days in the specified month.
        Recent data (1-2 days ago) should be available.
        Future dates will return 404.
        """
        logger.info("Attempting direct URL download approach...")
        logger.info(f"Requesting data for {year}-{month:02d}")
        logger.info("Note: TEPCO publishes with ~1 day lag. Recent dates should work.")

        page = context.new_page()

        try:
            # Try downloading all days in the month
            import calendar
            from datetime import datetime, timedelta

            days_in_month = calendar.monthrange(year, month)[1]
            today = datetime.now()

            # Don't try to download future dates
            if year == today.year and month == today.month:
                max_day = min(days_in_month, today.day - 1)  # Yesterday at most
                logger.info(f"Current month - will try up to day {max_day} (yesterday)")
            elif year > today.year or (year == today.year and month > today.month):
                logger.error(f"Cannot download future data: {year}-{month:02d}")
                logger.error(f"Current date: {today.strftime('%Y-%m-%d')}")
                return None
            else:
                max_day = days_in_month

            downloaded_files = []

            for day in range(1, max_day + 1):
                date_str = f"{year}{month:02d}{day:02d}"
                url = f"https://www.tepco.co.jp/forecast/html/images/juyo-{date_str}.csv"

                logger.info(f"Trying {date_str}...")

                try:
                    # Try to navigate to the URL
                    response = page.goto(url, wait_until='load', timeout=10000)

                    # Check if we got a valid response
                    if response and response.status == 200:
                        # Check if it's actually a CSV (not an error page)
                        content_type = response.headers.get('content-type', '')
                        if 'text/csv' in content_type or 'application/csv' in content_type or 'octet-stream' in content_type:
                            # Download via expect_download
                            output_file = output_path / f"juyo-{date_str}.csv"

                            # Get page content and save
                            content = page.content()
                            with open(output_file, 'w', encoding='utf-8') as f:
                                f.write(content)

                            if output_file.exists() and output_file.stat().st_size > 0:
                                logger.info(f"  ✓ Downloaded: {output_file.name}")
                                downloaded_files.append(str(output_file))
                            else:
                                logger.debug(f"  ✗ Failed: {date_str}")
                        else:
                            logger.debug(f"  ✗ Not a CSV: {date_str} (content-type: {content_type})")
                    elif response and response.status == 404:
                        logger.debug(f"  ✗ Not found: {date_str}")
                    elif response and response.status == 403:
                        logger.warning(f"  ⚠ Access denied: {date_str} (403 Forbidden)")
                        logger.warning("  TEPCO may be blocking automated requests")
                        break  # Stop trying if we hit 403
                    else:
                        logger.debug(f"  ✗ HTTP {response.status if response else 'N/A'}: {date_str}")

                except Exception as e:
                    logger.debug(f"  ✗ Error on day {day}: {str(e)[:100]}")
                    continue

                # Small delay between requests
                time.sleep(0.5)

            if downloaded_files:
                logger.info(f"✓ Successfully downloaded {len(downloaded_files)} daily files")
                return downloaded_files[0]  # Return first file as example
            else:
                logger.error("Could not download any files via direct URL")
                logger.error(f"Tried dates: {year}-{month:02d}-01 to {year}-{month:02d}-{max_day:02d}")
                logger.error("Possible reasons:")
                logger.error("  - Data not yet published (1-2 day lag)")
                logger.error("  - Future dates requested")
                logger.error("  - 403 Forbidden (access blocked)")
                logger.error("  - Website structure changed")
                return None

        finally:
            page.close()


def main():
    parser = argparse.ArgumentParser(
        description='Download TEPCO demand data using Playwright automation'
    )
    parser.add_argument(
        '--year',
        type=int,
        required=True,
        help='Year (e.g., 2025)'
    )
    parser.add_argument(
        '--month',
        type=int,
        required=True,
        help='Month (1-12)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/tepco',
        help='Output directory (default: data/tepco)'
    )
    parser.add_argument(
        '--japanese',
        action='store_true',
        help='Use Japanese page instead of English'
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
    downloader = TEPCODownloader(
        headless=args.headless,
        slow_mo=args.slow_mo
    )

    # Download data
    result = downloader.download_demand_data(
        year=args.year,
        month=args.month,
        output_dir=args.output,
        use_japanese=args.japanese
    )

    if result:
        logger.info("\n" + "="*60)
        logger.info("SUCCESS! TEPCO data downloaded")
        logger.info("="*60)
        logger.info(f"File: {result}")
        logger.info("\nNext steps:")
        logger.info(f"  1. Import to database:")
        logger.info(f"     python apps/etl/tepco_demand_ingest.py --file {result}")
        logger.info(f"  2. Or process all files in directory:")
        logger.info(f"     python apps/etl/tepco_demand_ingest.py --directory {args.output}")
        logger.info("="*60 + "\n")
        return 0
    else:
        logger.error("\n" + "="*60)
        logger.error("FAILED to download TEPCO data")
        logger.error("="*60)
        logger.error("Possible reasons:")
        logger.error("  1. Data for this month not yet published")
        logger.error("  2. TEPCO changed their website structure")
        logger.error("  3. Additional bot protection")
        logger.error("\nTry:")
        logger.error("  - Run with --headless false to see browser")
        logger.error("  - Try --japanese flag for Japanese page")
        logger.error("  - Manual download: https://www.tepco.co.jp/en/forecast/html/download-e.html")
        logger.error("="*60 + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
