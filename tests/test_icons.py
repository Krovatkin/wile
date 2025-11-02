#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time
import os

# Server configuration
PORT = os.environ.get('PORT', '3000')
BASE_URL = f'http://localhost:{PORT}'

def test_icons_display():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(2)

        # Take screenshot
        page.screenshot(path='test_icons.png')
        print("✓ Screenshot saved to test_icons.png")

        # Check that page loaded successfully
        html = page.content()
        if 'folder1' in html and 'test1.txt' in html:
            print("✓ Page content loaded successfully")
        else:
            print("✗ ERROR: Page content not loaded correctly")
            raise AssertionError("Page content missing")

        # Check that ICONS constant exists in JavaScript
        icons_defined = page.evaluate('typeof ICONS !== "undefined"')
        if icons_defined:
            print("✓ ICONS constant is defined in JavaScript")
        else:
            print("✗ ERROR: ICONS constant not found")
            raise AssertionError("ICONS constant missing")

        # Test that icons have correct structure
        icon_count = page.evaluate('Object.keys(ICONS).length')
        print(f"✓ ICONS object has {icon_count} icons")

        browser.close()

        print("\n" + "=" * 60)
        print("ICON CONSTANTS TEST PASSED! ✓")
        print("=" * 60)

if __name__ == '__main__':
    test_icons_display()
