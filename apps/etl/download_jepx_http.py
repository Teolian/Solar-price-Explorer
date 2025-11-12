#!/usr/bin/env python3
"""
Download JEPX data via direct HTTP (if accessible)

Quick download without Playwright for testing.
"""
import sys
import httpx
from pathlib import Path

def download_jepx_direct(year: int, output_file: str) -> bool:
    """Download JEPX data via direct HTTP"""
    url = f"https://www.jepx.jp/market/excel/spot_{year}.csv"

    print(f"Downloading: {url}")
    print(f"Output: {output_file}")

    try:
        response = httpx.get(url, timeout=30, follow_redirects=True)

        if response.status_code == 200:
            # Check if it's actually CSV data
            content = response.content

            if len(content) < 1000:
                # Too small - probably error page
                print(f"✗ FAILED: Response too small ({len(content)} bytes)")
                print(f"Content: {content.decode('utf-8', errors='ignore')}")
                return False

            # Save file
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(content)

            print(f"✓ SUCCESS: Downloaded {len(content):,} bytes")

            # Show preview (first few lines)
            try:
                with open(output_path, 'r', encoding='cp932') as f:
                    lines = f.readlines()[:5]
                    print("\nPreview (first 5 lines):")
                    for line in lines:
                        print(f"  {line.strip()}")
            except Exception as e:
                print(f"(Could not preview: {e})")

            return True

        elif response.status_code == 403:
            print(f"✗ FAILED: 403 Forbidden")
            print("Need Playwright automation")
            return False

        elif response.status_code == 404:
            print(f"✗ FAILED: 404 Not Found")
            print("File doesn't exist yet")
            return False

        else:
            print(f"✗ FAILED: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {e}")
        return False

if __name__ == '__main__':
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    output = sys.argv[2] if len(sys.argv) > 2 else f'/app/data/jepx/spot_{year}.csv'

    success = download_jepx_direct(year, output)
    sys.exit(0 if success else 1)
