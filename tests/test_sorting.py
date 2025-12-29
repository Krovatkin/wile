#!/usr/bin/env python3
"""Test sorting functionality"""

from playwright.sync_api import sync_playwright
import time
import os

# Server configuration
PORT = os.environ.get('PORT', '3000')
BASE_URL = f'http://localhost:{PORT}'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    # Track console logs
    sort_logs = []

    def log_console(msg):
        text = msg.text
        if 'Sort:' in text or 'New sort:' in text:
            sort_logs.append(text)
            print(f'   {text}')

    page.on('console', log_console)

    print("=" * 60)
    print("TESTING SORTING FUNCTIONALITY")
    print("=" * 60)
    print()

    # Load page
    print("1. Loading page...")
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')
    time.sleep(1)

    # Initial load should use default sort (name asc)
    print("\n2. Default sort on page load:")
    time.sleep(0.5)

    # Click Name button (should toggle to desc)
    print("\n3. Clicking Name button (should toggle to desc)...")
    page.click('button:has-text("Name")')
    time.sleep(1)

    # Click Name button again (should toggle back to asc)
    print("\n4. Clicking Name button again (should toggle to asc)...")
    page.click('button:has-text("Name")')
    time.sleep(1)

    # Click Modified button (should switch to modified asc)
    print("\n5. Clicking Modified button (should switch to modified asc)...")
    page.click('button:has-text("Modified")')
    time.sleep(1)

    # Click Modified button again (should toggle to desc)
    print("\n6. Clicking Modified button again (should toggle to desc)...")
    page.click('button:has-text("Modified")')
    time.sleep(1)

    # Click Size button (should switch to size asc)
    print("\n7. Clicking Size button (should switch to size asc)...")
    page.click('button:has-text("Size")')
    time.sleep(1)

    # Click Size button again (should toggle to desc)
    print("\n8. Clicking Size button again (should toggle to desc)...")
    page.click('button:has-text("Size")')
    time.sleep(1)

    # Take final screenshot
    print("\n7. Taking screenshot...")
    page.screenshot(path='test_sorting.png', full_page=True)
    print("   ✓ Screenshot saved to test_sorting.png")

    print()
    print("=" * 60)
    print("SORTING TEST COMPLETE")
    print("=" * 60)
    print()
    print("Console logs captured:")
    for log in sort_logs:
        print(f"  {log}")

    browser.close()
# Server configuration


