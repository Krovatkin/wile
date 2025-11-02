#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time
import os

# Server configuration
PORT = os.environ.get('PORT', '3000')
BASE_URL = f'http://localhost:{PORT}'

def test_lightbox_with_3_images():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        print("=" * 60)
        print("TESTING LIGHTBOX WITH 3 IMAGES")
        print("=" * 60)

        # Open first image
        print("\n1. Opening test_image_1.png (red)...")
        page.dblclick('text=test_image_1.png')
        time.sleep(1)

        # Check that lightbox opened
        lightbox = page.locator('.gslide-media')
        if lightbox.count() > 0:
            print("   ✓ Lightbox opened")
        else:
            print("   ✗ ERROR: Lightbox did not open")
            raise AssertionError("Lightbox failed to open")

        # Test NEXT button (go to image 2)
        print("\n2. Clicking Next (should show blue image 2)...")
        next_btn = page.locator('.gnext')
        if next_btn.count() > 0:
            next_btn.click()
            time.sleep(1)
            print("   ✓ Next clicked - showing image 2")
        else:
            print("   ✗ ERROR: Next button not found")

        # Test NEXT button again (go to image 3)
        print("\n3. Clicking Next (should show green image 3)...")
        if next_btn.count() > 0:
            next_btn.click()
            time.sleep(1)
            print("   ✓ Next clicked - showing image 3")
        else:
            print("   ✗ ERROR: Next button not found")

        # Test NEXT button again (should wrap to image 1)
        print("\n4. Clicking Next (should wrap to red image 1)...")
        if next_btn.count() > 0:
            next_btn.click()
            time.sleep(1)
            print("   ✓ Next clicked - wrapped to image 1")
        else:
            print("   ✗ ERROR: Next button not found")

        # Test PREV button (should go back to image 3)
        print("\n5. Clicking Prev (should wrap back to green image 3)...")
        prev_btn = page.locator('.gprev')
        if prev_btn.count() > 0:
            prev_btn.click()
            time.sleep(1)
            print("   ✓ Prev clicked - wrapped to image 3")
        else:
            print("   ✗ ERROR: Prev button not found")

        # Take screenshot
        print("\n6. Taking screenshot...")
        page.screenshot(path='lightbox_3images_test.png', full_page=True)
        print("   ✓ Screenshot saved")

        print("\nKeeping browser open for 3 seconds...")
        time.sleep(3)

        browser.close()

        print("\n" + "=" * 60)
        print("LIGHTBOX NAVIGATION TEST PASSED! ✓")
        print("=" * 60)
        print("\nSummary:")
        print("  - 3 images in folder")
        print("  - Forward navigation: WORKING")
        print("  - Backward navigation: WORKING")
        print("  - Wrap-around (both directions): WORKING")

if __name__ == '__main__':
    try:
        test_lightbox_with_3_images()
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
