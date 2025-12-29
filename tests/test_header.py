#!/usr/bin/env python3
"""Test the column header display"""

from playwright.sync_api import sync_playwright
import time
import os

# Server configuration
PORT = os.environ.get('PORT', '3000')
BASE_URL = f'http://localhost:{PORT}'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    print("=" * 60)
    print("TESTING COLUMN HEADERS")
    print("=" * 60)
    print()

    # Navigate to file browser
    print("1. Loading page...")
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')
    time.sleep(1)

    # Check if header exists
    print("2. Checking for column headers...")

    # Check Name button
    name_button = page.locator('button:has-text("Name")').first
    if name_button.is_visible():
        print("   ✓ Name column header found")
    else:
        print("   ✗ Name column header not found")

    # Check Modified button
    modified_button = page.locator('button:has-text("Modified")').first
    if modified_button.is_visible():
        print("   ✓ Modified column header found")
    else:
        print("   ✗ Modified column header not found")

    # Check Size button
    size_button = page.locator('button:has-text("Size")').first
    if size_button.is_visible():
        print("   ✓ Size column header found")
    else:
        print("   ✗ Size column header not found")

    # Actions column is now an icon/empty space, skipping text check

    # Test clicking Name button
    print()
    print("3. Testing Name sort button...")
    page.click('button:has-text("Name")')
    time.sleep(0.5)
    print("   ✓ Name button clicked (check console for 'Sort by: name')")

    # Test clicking Modified button
    print()
    print("4. Testing Modified sort button...")
    page.click('button:has-text("Modified")')
    time.sleep(0.5)
    print("   ✓ Modified button clicked (check console for 'Sort by: modified')")

    # Test clicking Size button
    print()
    print("5. Testing Size sort button...")
    page.click('button:has-text("Size")')
    time.sleep(0.5)
    print("   ✓ Size button clicked (check console for 'Sort by: size')")

    # Take screenshot
    print()
    print("5. Taking screenshot...")
    page.screenshot(path='test_header.png', full_page=True)
    print("   ✓ Screenshot saved to test_header.png")

    print()
    print("=" * 60)
    print("HEADER TEST COMPLETE")
    print("=" * 60)

    browser.close()
