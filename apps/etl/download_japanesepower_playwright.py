#!/usr/bin/env python3
"""
Automated JapanesePower.org JEPX Data Download using Playwright

Downloads JEPX spot price history from japanesepower.org
bypassing any access restrictions by simulating real browser behavior.

Source: https://japanesepower.org

SETUP:
  pip install playwright
  playwright install chromium

USAGE:
  python download_japanesepower_playwright.py --area TOKYO --output data/japanesepower/
  python download_japanesepower_playwright.py --area TOHOKU --headless false
  python download_japanesepower_playwright.py --all-areas --output data/japanesepower/
"""
import os
import sys
import argparse
import logging
import time
from pathlib import Path
from typing import Optional, List

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
JAPANESEPOWER_BASE_URL = "https://japanesepower.org"
AREA_PAGES = {
    'TOKYO': 'Tokyo_main.html',
    'TOHOKU': 'Tohoku_main.html',
    'HOKKAIDO': 'Hokkaido_main.html',
    'KANSAI': 'Kansai_main.html',
    'CHUBU': 'Chuubu_main.html',
    'KYUSHU': 'Kyushu_main.html',
    'CHUGOKU': 'Chuugoku_main.html',
    'SHIKOKU': 'Shikoku_main.html',
    'HOKURIKU': 'Hokuriku_main.html'
}
DEFAULT_TIMEOUT = 30000  # 30 seconds
DOWNLOAD_TIMEOUT = 120000  # 2 minutes


class JapanesePowerDownloader:
    """Automated JapanesePower.org data downloader using Playwright"""

    def __init__(self, headless: bool = True, slow_mo: int = 100):
        """
        Initialize downloader

        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations by N milliseconds
        """
        self.headless = headless
        self.slow_mo = slow_mo

    def download_area_data(
        self,
        area: str,
        output_dir: str
    ) -> List[str]:
        """
        Download JEPX spot price data for specified area

        Args:
            area: Area name (TOKYO, TOHOKU, HOKKAIDO, etc.)
            output_dir: Directory to save downloaded files

        Returns:
            List of downloaded file paths
        """
        if area not in AREA_PAGES:
            logger.error(f"Unknown area: {area}")
            logger.error(f"Available areas: {', '.join(AREA_PAGES.keys())}")
            return []

        logger.info(f"Starting JapanesePower.org download for {area}")
        logger.info(f"Output directory: {output_dir}")

        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Construct URL
        page_url = f"{JAPANESEPOWER_BASE_URL}/{AREA_PAGES[area]}"

        downloaded_files = []

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
                # Step 1: Navigate to area page
                logger.info(f"Navigating to {page_url}")
                page.goto(page_url, wait_until='networkidle', timeout=DEFAULT_TIMEOUT)

                # Human-like pause
                time.sleep(2)

                # Take screenshot for debugging
                debug_path = output_path / f"japanesepower_{area}_page.png"
                page.screenshot(path=str(debug_path))
                logger.info(f"Screenshot saved: {debug_path}")

                # Step 2: Look for CSV download links
                logger.info("Searching for CSV download links...")

                # JapanesePower.org typically has:
                # - Links with "CSV" or "download" text
                # - Links to .csv files
                # - Download buttons

                csv_link_selectors = [
                    'a[href$=".csv"]',
                    'a:has-text("CSV")',
                    'a:has-text("ダウンロード")',
                    'a:has-text("Download")',
                    'a[href*="csv"]',
                    'button:has-text("CSV")',
                    'button:has-text("ダウンロード")',
                ]

                found_links = []
                for selector in csv_link_selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        elements = page.locator(selector).all()

                        for element in elements:
                            if element.is_visible(timeout=3000):
                                href = element.get_attribute('href') if element.evaluate('el => el.tagName') == 'A' else None
                                text = element.text_content()

                                if href and '.csv' in href.lower():
                                    logger.info(f"  Found CSV link: {text} -> {href}")
                                    found_links.append((element, href, text))
                                elif text and ('csv' in text.lower() or 'download' in text.lower()):
                                    logger.info(f"  Found download element: {text}")
                                    found_links.append((element, href, text))

                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue

                if not found_links:
                    logger.error("Could not find any CSV download links")
                    logger.info("Available links on page:")
                    all_links = page.locator('a[href]').all()
                    for link in all_links[:30]:
                        try:
                            href = link.get_attribute('href')
                            text = link.text_content()
                            logger.info(f"  {text[:50]} -> {href}")
                        except:
                            pass

                    return []

                # Step 3: Download all found CSV files
                logger.info(f"Found {len(found_links)} potential download links")

                for idx, (element, href, text) in enumerate(found_links):
                    try:
                        logger.info(f"\nDownloading file {idx + 1}/{len(found_links)}: {text}")

                        with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_promise:
                            element.click()
                            download_info = download_promise.value

                        # Save file
                        original_filename = download_info.suggested_filename
                        if original_filename:
                            output_file = output_path / original_filename
                        else:
                            # Generate filename
                            output_file = output_path / f"{area.lower()}_jepx_{idx + 1}.csv"

                        download_info.save_as(str(output_file))

                        # Verify file
                        if output_file.exists():
                            file_size = output_file.stat().st_size
                            logger.info(f"✓ Downloaded: {output_file.name} ({file_size:,} bytes)")

                            # Quick validation
                            with open(output_file, 'rb') as f:
                                header = f.read(200)
                                try:
                                    # Try Shift-JIS decoding
                                    header_text = header.decode('shift_jis')
                                    logger.info(f"  Preview: {header_text[:80]}")

                                    if '年月日' in header_text or 'Date' in header_text or '時刻' in header_text:
                                        logger.info("✓ File appears to be valid JEPX CSV")
                                    else:
                                        logger.warning("  Warning: File might not be JEPX data")
                                except:
                                    # Try UTF-8
                                    try:
                                        header_text = header.decode('utf-8')
                                        logger.info(f"  Preview (UTF-8): {header_text[:80]}")
                                    except:
                                        logger.warning("  Could not decode file preview")

                            downloaded_files.append(str(output_file))
                        else:
                            logger.warning(f"✗ Download failed for: {text}")

                        # Small delay between downloads
                        time.sleep(1)

                    except PlaywrightTimeout:
                        logger.warning(f"✗ Timeout downloading: {text}")
                        continue
                    except Exception as e:
                        logger.warning(f"✗ Error downloading {text}: {e}")
                        continue

                if downloaded_files:
                    logger.info(f"\n✓ Successfully downloaded {len(downloaded_files)} files for {area}")
                    return downloaded_files
                else:
                    logger.error(f"✗ No files downloaded for {area}")
                    return []

            except PlaywrightTimeout as e:
                logger.error(f"Timeout error: {e}")
                screenshot_path = output_path / f"japanesepower_{area}_timeout.png"
                page.screenshot(path=str(screenshot_path))
                logger.error(f"Screenshot saved to {screenshot_path}")
                return []

            except Exception as e:
                logger.error(f"Error during download: {e}")
                import traceback
                traceback.print_exc()
                screenshot_path = output_path / f"japanesepower_{area}_error.png"
                try:
                    page.screenshot(path=str(screenshot_path))
                    logger.error(f"Screenshot saved to {screenshot_path}")
                except:
                    pass
                return []

            finally:
                context.close()
                browser.close()


def main():
    parser = argparse.ArgumentParser(
        description='Download JEPX data from JapanesePower.org using Playwright'
    )
    parser.add_argument(
        '--area',
        type=str,
        help=f'Area name: {", ".join(AREA_PAGES.keys())}'
    )
    parser.add_argument(
        '--all-areas',
        action='store_true',
        help='Download data for all areas'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/japanesepower',
        help='Output directory (default: data/japanesepower)'
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

    if not args.area and not args.all_areas:
        parser.error("Either --area or --all-areas must be specified")

    # Determine areas to download
    if args.all_areas:
        areas = list(AREA_PAGES.keys())
    else:
        areas = [args.area.upper()]

    # Create downloader
    downloader = JapanesePowerDownloader(
        headless=args.headless,
        slow_mo=args.slow_mo
    )

    # Download data for each area
    all_downloaded_files = []
    successful_areas = []
    failed_areas = []

    for area in areas:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing area: {area}")
        logger.info(f"{'='*60}")

        files = downloader.download_area_data(
            area=area,
            output_dir=args.output
        )

        if files:
            all_downloaded_files.extend(files)
            successful_areas.append(area)
        else:
            failed_areas.append(area)

        # Delay between areas
        if len(areas) > 1:
            time.sleep(2)

    # Summary
    logger.info("\n" + "="*60)
    if all_downloaded_files:
        logger.info("SUCCESS! JapanesePower.org data downloaded")
        logger.info("="*60)
        logger.info(f"Total files: {len(all_downloaded_files)}")
        logger.info(f"Successful areas: {', '.join(successful_areas)}")
        if failed_areas:
            logger.info(f"Failed areas: {', '.join(failed_areas)}")
        logger.info(f"\nFiles saved to: {args.output}")
        logger.info("\nNext steps:")
        logger.info("  1. Import to database:")
        logger.info(f"     python apps/etl/japanesepower_ingest.py --directory {args.output}")
        logger.info("  2. Or process single file:")
        logger.info(f"     python apps/etl/japanesepower_ingest.py --file {all_downloaded_files[0]}")
        logger.info("="*60 + "\n")
        return 0
    else:
        logger.error("FAILED to download JapanesePower.org data")
        logger.error("="*60)
        logger.error(f"All areas failed: {', '.join(failed_areas)}")
        logger.error("\nPossible reasons:")
        logger.error("  1. Website structure changed")
        logger.error("  2. Access restrictions/bot detection")
        logger.error("  3. Data not available for these areas")
        logger.error("\nTry:")
        logger.error("  - Run with --headless false to see browser")
        logger.error("  - Check screenshots in output directory")
        logger.error("  - Manual download: https://japanesepower.org")
        logger.error("="*60 + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
