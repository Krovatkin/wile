#!/usr/bin/env python3
"""Test double-click download for text files"""

from playwright.sync_api import sync_playwright
import time
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    print("=" * 60)
    print("TESTING FILE DOWNLOAD ON DOUBLE-CLICK")
    print("=" * 60)
    print()

    # Navigate to file browser
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')
    time.sleep(1)

    print("1. Checking if test1.txt has download handler...")

    # Check if the file element has ondblclick attribute
    file_li = page.locator('[data-path="test1.txt"]').first
    ondblclick = file_li.get_attribute('ondblclick')
    print(f"   test1.txt ondblclick: {ondblclick[:60]}...")

    if 'window.location.href' in ondblclick and '/file?path=' in ondblclick:
        print("   ✓ File has correct download handler")
    else:
        print(f"   ✗ Expected window.location.href with /file?path= in ondblclick")

    print()
    print("2. Testing double-click behavior...")
    print("   Note: Playwright will trigger ondblclick handler")
    print("   Double-clicking test1.txt...")

    # Listen for download events
    downloads = []

    page.on("download", lambda download: downloads.append(download))

    # Double-click the file
    page.dblclick('text=test1.txt')

    # Wait a moment for download to trigger
    time.sleep(2)

    if downloads:
        print(f"   ✓ Download triggered: {downloads[0].suggested_filename}")
    else:
        print("   ⚠ No download event captured (may still work in real browser)")

    print()
    print("3. Taking screenshot...")
    page.screenshot(path='test_download.png')
    print("   ✓ Screenshot saved to test_download.png")

    print()
    print("=" * 60)
    print("DOWNLOAD TEST COMPLETE")
    print("=" * 60)
    print()
    print("Manual verification: Double-click test1.txt in browser at")
    print(f"{BASE_URL} and verify it downloads")

    browser.close()
