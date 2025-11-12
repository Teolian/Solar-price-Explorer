#!/usr/bin/env python3
"""
Test script to check which JEPX data files are available
"""
import httpx

# Test different years and URL patterns
years_to_test = [2025, 2024, 2023, 2022]
url_patterns = [
    "http://www.jepx.org/market/excel/spot_{year}.csv",
    "http://www.jepx.org/market/excel/spot_summary_{year}.csv",
    "https://www.jepx.jp/market/excel/spot_{year}.csv",
    "https://www.jepx.jp/market/excel/spot_summary_{year}.csv",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
}

print("Testing JEPX data availability...\n")

with httpx.Client(timeout=30.0, follow_redirects=True) as client:
    for year in years_to_test:
        print(f"Testing year {year}:")
        for pattern in url_patterns:
            url = pattern.format(year=year)
            try:
                response = client.head(url, headers=headers)
                status = response.status_code

                if status == 200:
                    size = response.headers.get('content-length', 'unknown')
                    print(f"  ✓ {url}")
                    print(f"    Status: {status}, Size: {size} bytes")

                    # Try to get first few bytes to verify it's CSV
                    get_resp = client.get(url, headers=headers)
                    if get_resp.status_code == 200:
                        preview = get_resp.content[:200].decode('shift_jis', errors='ignore')
                        print(f"    Preview: {preview[:100]}...")
                else:
                    print(f"  ✗ {url} - Status: {status}")
            except Exception as e:
                print(f"  ✗ {url} - Error: {e}")
        print()

print("\nDone!")
