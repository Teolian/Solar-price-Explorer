#!/usr/bin/env python3
"""
Check Data Availability - Test what data is actually accessible

This script tests URLs without Playwright to understand data availability:
1. JEPX - Check which years are available
2. TEPCO - Check which dates are available (recent days)
3. JapanesePower.org - Check site status

Usage:
  python check_data_availability.py
"""
import sys
import httpx
from datetime import datetime, timedelta
import time

def check_jepx():
    """Check JEPX data availability"""
    print("\n" + "="*60)
    print("JEPX Data Availability Check")
    print("="*60)

    base_urls = [
        "https://www.jepx.jp/market/excel/spot_{year}.csv",
        "https://www.jepx.jp/market/excel/spot_summary_{year}.csv",
    ]

    years = [2025, 2024, 2023, 2022]

    for url_pattern in base_urls:
        print(f"\nTesting pattern: {url_pattern}")
        for year in years:
            url = url_pattern.format(year=year)
            try:
                response = httpx.get(url, timeout=5, follow_redirects=True)
                if response.status_code == 200:
                    print(f"  ✓ {year}: Available (200 OK, {len(response.content)} bytes)")
                elif response.status_code == 403:
                    print(f"  ✗ {year}: 403 Forbidden (blocked)")
                elif response.status_code == 404:
                    print(f"  ✗ {year}: 404 Not Found")
                else:
                    print(f"  ? {year}: HTTP {response.status_code}")
            except httpx.TimeoutException:
                print(f"  ✗ {year}: Timeout")
            except Exception as e:
                print(f"  ✗ {year}: {type(e).__name__}")
            time.sleep(0.5)

def check_tepco():
    """Check TEPCO data availability"""
    print("\n" + "="*60)
    print("TEPCO Data Availability Check")
    print("="*60)

    today = datetime.now()

    # Test recent days (TEPCO publishes with 1-2 day lag)
    test_dates = [
        today - timedelta(days=1),  # Yesterday
        today - timedelta(days=2),  # 2 days ago
        today - timedelta(days=7),  # 1 week ago
        today - timedelta(days=30),  # 1 month ago
        datetime(2025, 9, 1),  # Sept 1, 2025
        datetime(2024, 11, 1),  # Nov 1, 2024
    ]

    print(f"Current date: {today.strftime('%Y-%m-%d')}")
    print("\nTesting daily CSV pattern: juyo-YYYYMMDD.csv")

    for date in test_dates:
        date_str = date.strftime('%Y%m%d')
        url = f"https://www.tepco.co.jp/forecast/html/images/juyo-{date_str}.csv"

        try:
            response = httpx.get(url, timeout=5, follow_redirects=True)

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'csv' in content_type.lower() or 'text' in content_type.lower():
                    print(f"  ✓ {date.strftime('%Y-%m-%d')}: Available (200 OK, {len(response.content)} bytes)")
                else:
                    print(f"  ? {date.strftime('%Y-%m-%d')}: 200 OK but not CSV ({content_type})")
            elif response.status_code == 403:
                print(f"  ✗ {date.strftime('%Y-%m-%d')}: 403 Forbidden (blocked)")
            elif response.status_code == 404:
                print(f"  ✗ {date.strftime('%Y-%m-%d')}: 404 Not Found")
            else:
                print(f"  ? {date.strftime('%Y-%m-%d')}: HTTP {response.status_code}")

        except httpx.TimeoutException:
            print(f"  ✗ {date.strftime('%Y-%m-%d')}: Timeout")
        except Exception as e:
            print(f"  ✗ {date.strftime('%Y-%m-%d')}: {type(e).__name__}: {str(e)[:50]}")

        time.sleep(0.5)

def check_japanesepower():
    """Check JapanesePower.org availability"""
    print("\n" + "="*60)
    print("JapanesePower.org Availability Check")
    print("="*60)

    base_url = "https://japanesepower.org"
    test_pages = [
        "",
        "/Tokyo_main.html",
        "/Tohoku_main.html",
        "/Hokkaido_main.html",
    ]

    for page in test_pages:
        url = f"{base_url}{page}"

        try:
            response = httpx.get(url, timeout=10, follow_redirects=True)

            if response.status_code == 200:
                content_length = len(response.content)
                print(f"  ✓ {page or '/'}: Available (200 OK, {content_length} bytes)")

                # Check if page contains CSV links
                if b'.csv' in response.content.lower() or b'CSV' in response.content:
                    print(f"    → Page contains CSV links")
            elif response.status_code == 403:
                print(f"  ✗ {page or '/'}: 403 Forbidden")
            elif response.status_code == 404:
                print(f"  ✗ {page or '/'}: 404 Not Found")
            else:
                print(f"  ? {page or '/'}: HTTP {response.status_code}")

        except httpx.TimeoutException:
            print(f"  ✗ {page or '/'}: Timeout (>10s)")
        except httpx.ConnectError:
            print(f"  ✗ {page or '/'}: Cannot connect (site down?)")
        except Exception as e:
            print(f"  ✗ {page or '/'}: {type(e).__name__}: {str(e)[:50]}")

        time.sleep(1)

def main():
    print("="*60)
    print("Japanese Energy Data Availability Check")
    print("="*60)
    print("This tests direct HTTP access to understand data availability")
    print("Note: 403 errors = Playwright required")
    print()

    try:
        check_jepx()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1

    try:
        check_tepco()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1

    try:
        check_japanesepower()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1

    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print("If most sources return 403 Forbidden:")
    print("  → Playwright automation is required")
    print("  → Use: make download-all-playwright")
    print()
    print("If sources return 404 Not Found:")
    print("  → Data not published yet (check dates)")
    print("  → TEPCO has ~1-2 day lag")
    print("  → JEPX 2025 data might not be available until year end")
    print()
    print("If sources return 200 OK:")
    print("  → Direct HTTP fetching works!")
    print("  → Can use simple HTTP scripts")
    print("="*60)

    return 0

if __name__ == '__main__':
    sys.exit(main())
