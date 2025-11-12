#!/usr/bin/env python3
"""
Test Download - Single Day Data Collection

Quick test to download data for 1-2 days in November 2025.
This helps verify all downloaders work correctly without waiting hours.

Usage:
  python test_download_single_day.py --date 2025-11-09
  python test_download_single_day.py --date 2025-11-09 --headless false
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_tepco_day(date: datetime, headless: bool = True) -> bool:
    """Download TEPCO data for single day using direct URL"""
    logger.info(f"\n{'='*60}")
    logger.info(f"TEPCO: Downloading {date.strftime('%Y-%m-%d')}")
    logger.info(f"{'='*60}")

    import httpx

    date_str = date.strftime('%Y%m%d')
    url = f"https://www.tepco.co.jp/forecast/html/images/juyo-{date_str}.csv"

    logger.info(f"URL: {url}")

    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)

        if response.status_code == 200:
            # Save file
            output_dir = Path('data/tepco')
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"juyo-{date_str}.csv"

            with open(output_file, 'wb') as f:
                f.write(response.content)

            logger.info(f"✓ SUCCESS: Downloaded {output_file.name} ({len(response.content)} bytes)")

            # Show preview
            try:
                with open(output_file, 'r', encoding='shift_jis') as f:
                    lines = f.readlines()[:5]
                    logger.info(f"Preview (first 5 lines):")
                    for line in lines:
                        logger.info(f"  {line.strip()}")
            except:
                logger.info("(Could not preview file)")

            return True

        elif response.status_code == 403:
            logger.error(f"✗ FAILED: 403 Forbidden - WAF blocking")
            logger.error(f"  Need to use Playwright for this date")
            return False

        elif response.status_code == 404:
            logger.error(f"✗ FAILED: 404 Not Found - Data not published yet")
            logger.error(f"  Try an earlier date (TEPCO has 1-2 day lag)")
            return False

        else:
            logger.error(f"✗ FAILED: HTTP {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"✗ FAILED: {type(e).__name__}: {e}")
        return False

def download_openmeteo_day(date: datetime, area: str = "TOKYO") -> bool:
    """Download Open-Meteo solar radiation for single day"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Open-Meteo: Downloading {area} {date.strftime('%Y-%m-%d')}")
    logger.info(f"{'='*60}")

    import httpx

    # Area coordinates
    coords = {
        'TOKYO': {'lat': 35.6762, 'lon': 139.6503},
        'TOHOKU': {'lat': 38.2682, 'lon': 140.8694},
        'HOKKAIDO': {'lat': 43.0642, 'lon': 141.3469},
    }

    if area not in coords:
        logger.error(f"Unknown area: {area}")
        return False

    lat = coords[area]['lat']
    lon = coords[area]['lon']

    # Format dates
    start_date = date.strftime('%Y-%m-%d')
    end_date = date.strftime('%Y-%m-%d')

    # Open-Meteo Forecast API (for recent data)
    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date,
        'end_date': end_date,
        'hourly': 'shortwave_radiation,direct_radiation,diffuse_radiation',
        'timezone': 'Asia/Tokyo'
    }

    logger.info(f"API: {url}")
    logger.info(f"Coords: {lat}, {lon}")

    try:
        response = httpx.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if 'hourly' in data and data['hourly']:
                times = data['hourly'].get('time', [])
                ghi = data['hourly'].get('shortwave_radiation', [])

                logger.info(f"✓ SUCCESS: Got {len(times)} hourly data points")
                logger.info(f"Preview (first 5 hours):")
                for i in range(min(5, len(times))):
                    logger.info(f"  {times[i]}: GHI = {ghi[i]} W/m²")

                # Save to file
                output_dir = Path('data/openmeteo')
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / f"{area.lower()}_{date.strftime('%Y%m%d')}.json"

                import json
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)

                logger.info(f"Saved to: {output_file}")
                return True
            else:
                logger.error(f"✗ FAILED: No data in response")
                return False

        else:
            logger.error(f"✗ FAILED: HTTP {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"✗ FAILED: {type(e).__name__}: {e}")
        return False

def download_jepx_year(year: int = 2025) -> bool:
    """Download JEPX full year data (if accessible via HTTP)"""
    logger.info(f"\n{'='*60}")
    logger.info(f"JEPX: Downloading full year {year} data")
    logger.info(f"{'='*60}")

    import httpx

    urls = [
        ("spot", f"https://www.jepx.jp/market/excel/spot_{year}.csv"),
        ("summary", f"https://www.jepx.jp/market/excel/spot_summary_{year}.csv"),
    ]

    for file_type, url in urls:
        logger.info(f"\nTrying {file_type}: {url}")
        try:
            response = httpx.get(url, timeout=30, follow_redirects=True)

            if response.status_code == 200:
                content = response.content

                # Check if it's actually CSV data (not error page)
                if len(content) < 1000:
                    logger.info(f"  ✗ Response too small ({len(content)} bytes) - probably error page")
                    try:
                        error_msg = content.decode('utf-8', errors='ignore')
                        logger.info(f"  Content: {error_msg}")
                    except:
                        pass
                    continue

                logger.info(f"  ✓ Available! (200 OK, {len(content):,} bytes)")

                # Save file
                output_dir = Path('data/jepx')
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / f"spot_{year}.csv" if file_type == "spot" else output_dir / f"spot_summary_{year}.csv"

                with open(output_file, 'wb') as f:
                    f.write(content)

                logger.info(f"  ✓ Saved to: {output_file}")

                # Show preview
                try:
                    with open(output_file, 'r', encoding='cp932') as f:
                        lines = f.readlines()[:5]
                        logger.info(f"  Preview (first 5 lines):")
                        for line in lines:
                            logger.info(f"    {line.strip()[:100]}")
                except Exception as e:
                    logger.info(f"  (Could not preview: {e})")

                return True

            elif response.status_code == 403:
                logger.info(f"  ✗ 403 Forbidden - Playwright required")
            elif response.status_code == 404:
                logger.info(f"  ✗ 404 Not Found - File doesn't exist")
            else:
                logger.info(f"  ? HTTP {response.status_code}")

        except Exception as e:
            logger.info(f"  ✗ Error: {type(e).__name__}: {str(e)[:100]}")

        time.sleep(0.5)

    logger.info(f"\n→ JEPX not accessible via direct HTTP")
    logger.info(f"  Run: make download-jepx-playwright")
    return False

def main():
    parser = argparse.ArgumentParser(
        description='Test download data for a single day'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Date to download (YYYY-MM-DD). Default: 2 days ago'
    )
    parser.add_argument(
        '--area',
        type=str,
        default='TOKYO',
        choices=['TOKYO', 'TOHOKU', 'HOKKAIDO'],
        help='Area for solar radiation data (default: TOKYO)'
    )
    parser.add_argument(
        '--headless',
        type=lambda x: x.lower() == 'true',
        default=True,
        help='Headless mode (not used in this test)'
    )

    args = parser.parse_args()

    # Determine test date
    if args.date:
        try:
            test_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid date format: {args.date}")
            logger.error(f"Use: YYYY-MM-DD (e.g., 2025-11-09)")
            return 1
    else:
        # Default: 2 days ago (TEPCO has 1-2 day lag)
        test_date = datetime.now() - timedelta(days=2)

    logger.info("="*60)
    logger.info("TEST DOWNLOAD - Single Day Data Collection")
    logger.info("="*60)
    logger.info(f"Date: {test_date.strftime('%Y-%m-%d')}")
    logger.info(f"Area: {args.area}")
    logger.info(f"Current date: {datetime.now().strftime('%Y-%m-%d')}")
    logger.info("="*60)

    results = {}

    # Test 1: TEPCO (direct HTTP)
    results['TEPCO'] = download_tepco_day(test_date, args.headless)

    # Test 2: Open-Meteo (API)
    results['Open-Meteo'] = download_openmeteo_day(test_date, args.area)

    # Test 3: JEPX download (full year)
    results['JEPX'] = download_jepx_year(year=test_date.year)

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Date tested: {test_date.strftime('%Y-%m-%d')}")
    logger.info(f"")

    for source, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        logger.info(f"{source:15} : {status}")

    logger.info(f"\n{'='*60}")

    if results['TEPCO']:
        logger.info("✓ TEPCO data downloaded successfully")
        logger.info(f"  File: data/tepco/juyo-{test_date.strftime('%Y%m%d')}.csv")
    else:
        logger.info("✗ TEPCO download failed")
        logger.info("  Possible reasons:")
        logger.info("    - Data not published yet (try earlier date)")
        logger.info("    - 403 Forbidden (need Playwright)")
        logger.info("    - Network issues")

    if results['Open-Meteo']:
        logger.info("✓ Open-Meteo data downloaded successfully")
        logger.info(f"  File: data/openmeteo/{args.area.lower()}_{test_date.strftime('%Y%m%d')}.json")
    else:
        logger.info("✗ Open-Meteo download failed")
        logger.info("  Check API availability and network")

    if results['JEPX']:
        logger.info("✓ JEPX data downloaded via direct HTTP!")
        logger.info(f"  File: data/jepx/spot_{test_date.year}.csv")
        logger.info("  Direct HTTP works - no Playwright needed!")
    else:
        logger.info("⚠ JEPX download failed")
        logger.info("  Direct HTTP blocked - need Playwright")
        logger.info("  Run: make download-jepx-playwright")

    logger.info(f"{'='*60}")

    # Next steps
    logger.info("\nNEXT STEPS:")

    if any(results.values()):
        logger.info("✓ At least one data source works!")

        if results['TEPCO']:
            logger.info("\n1. Import TEPCO data:")
            logger.info(f"   docker-compose exec api python /etl/tepco_demand_ingest.py \\")
            logger.info(f"     --file /app/data/tepco/juyo-{test_date.strftime('%Y%m%d')}.csv")

        if results['JEPX']:
            logger.info("\n2. Import JEPX data:")
            logger.info(f"   docker-compose exec api python /etl/import_jepx_csv.py \\")
            logger.info(f"     --file /app/data/jepx/spot_{test_date.year}.csv \\")
            logger.info(f"     --areas {args.area}")
        else:
            logger.info("\n2. Download JEPX with Playwright:")
            logger.info("   make download-jepx-playwright")

        if results['TEPCO'] and results['JEPX']:
            logger.info("\n3. Build features:")
            logger.info("   docker-compose exec api python /etl/build_features.py \\")
            logger.info(f"     --areas {args.area} \\")
            logger.info(f"     --start-date {test_date.strftime('%Y-%m-%d')} \\")
            logger.info(f"     --end-date {test_date.strftime('%Y-%m-%d')}")
    else:
        logger.info("⚠ Some downloads failed - check errors above")
        logger.info("\nTry:")
        logger.info(f"  python test_download_single_day.py --date {(test_date - timedelta(days=1)).strftime('%Y-%m-%d')}")
        logger.info("  (Try 1 day earlier)")

    logger.info(f"\n{'='*60}\n")

    # Return 0 if at least one source worked
    return 0 if any(results.values()) else 1

if __name__ == '__main__':
    sys.exit(main())
