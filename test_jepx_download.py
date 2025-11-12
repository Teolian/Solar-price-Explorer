#!/usr/bin/env python3
"""
Test script to verify JEPX data download using POST method
"""
import httpx
import time
from io import StringIO
import pandas as pd

# JEPX download endpoint
download_url = "https://www.jepx.jp/_download.php"

# Try to download 2024 data (most likely to be available)
years_to_test = [2024, 2023]

# Browser-like headers required by JEPX
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.jepx.jp',
    'Referer': 'https://www.jepx.jp/electricpower/market-data/spot/',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0'
}

print("Testing JEPX POST download mechanism...\n")

with httpx.Client(timeout=30.0, follow_redirects=True) as client:
    for year in years_to_test:
        print(f"Testing year {year}:")

        # Test spot_summary file
        form_data = {
            'dir': 'spot_summary',
            'file': f'spot_summary_{year}.csv'
        }

        try:
            print(f"  Sending POST request for spot_summary_{year}.csv...")
            response = client.post(download_url, data=form_data, headers=headers)

            print(f"    Status: {response.status_code}")
            print(f"    Content-Length: {len(response.content)} bytes")

            if response.status_code == 200 and len(response.content) > 0:
                # Try to parse as CSV
                try:
                    content = response.content.decode('cp932')
                    df = pd.read_csv(StringIO(content))

                    print(f"    ✓ Successfully parsed CSV!")
                    print(f"    Rows: {len(df)}")
                    print(f"    Columns: {list(df.columns[:10])}")

                    # Show first few rows
                    print(f"\n    First 3 rows:")
                    print(df.head(3).to_string(index=False))
                    print()

                except Exception as e:
                    print(f"    ✗ Failed to parse CSV: {e}")
                    # Show first 500 chars of response
                    preview = response.content[:500]
                    print(f"    Response preview: {preview}")
            else:
                print(f"    ✗ Failed or empty response")

        except Exception as e:
            print(f"    ✗ Request failed: {e}")

        # Throttle: wait 2 seconds between requests
        print(f"  Waiting 2 seconds before next request...")
        time.sleep(2)
        print()

print("Test complete!")
