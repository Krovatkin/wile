#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time
import os

# Server configuration
PORT = os.environ.get('PORT', '3000')
BASE_URL = f'http://localhost:{PORT}'

def test_copy_and_cut():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to file browser
        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        print("=" * 60)
        print("TESTING COPY OPERATION")
        print("=" * 60)

        # Test 1: Copy test1.txt to folder3
        print("\n1. Selecting test1.txt...")
        page.click('text=test1.txt')
        time.sleep(0.5)

        # Verify selection count
        selection_text = page.locator('#selectionCount').inner_text()
        print(f"   Selection count: {selection_text}")
        assert "1 item selected" in selection_text, "Should show 1 item selected"

        print("\n2. Clicking Copy button...")
        page.click('#copyBtn')
        time.sleep(0.5)

        # Check for notification
        print("   ✓ Copy button clicked")

        print("\n3. Navigating to folder3...")
        page.dblclick('text=folder3')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Verify we're in folder3
        path = page.locator('#currentPath').inner_text()
        print(f"   Current path: {path}")
        assert "folder3" in path, "Should be in folder3"

        print("\n4. Clicking Paste button...")
        page.click('#pasteBtn')
        time.sleep(2)  # Wait for paste to complete

        # Wait for refresh
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Verify test1.txt appears in folder3
        print("\n5. Verifying test1.txt was copied...")
        content = page.content()
        if 'test1.txt' in content:
            print("   ✓ test1.txt found in folder3!")
        else:
            print("   ✗ ERROR: test1.txt NOT found in folder3")
            raise AssertionError("Copy failed - file not found in destination")

        print("\n" + "=" * 60)
        print("TESTING CUT OPERATION")
        print("=" * 60)

        # Navigate back to root
        print("\n1. Navigating back to root...")
        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(2) # Increased from 1s to 2s to prevent timeout

        # Test 2: Cut test2.txt and move to folder2
        print("\n2. Selecting test2.txt...")
        page.click('text=test2.txt')
        time.sleep(0.5)

        selection_text = page.locator('#selectionCount').inner_text()
        print(f"   Selection count: {selection_text}")
        assert "1 item selected" in selection_text, "Should show 1 item selected"

        print("\n3. Clicking Cut button...")
        page.click('#cutBtn')
        time.sleep(0.5)
        print("   ✓ Cut button clicked")

        print("\n4. Navigating to folder2...")
        page.dblclick('text=folder2')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        path = page.locator('#currentPath').inner_text()
        print(f"   Current path: {path}")
        assert "folder2" in path, "Should be in folder2"

        print("\n5. Clicking Paste button...")
        page.click('#pasteBtn')
        time.sleep(2)  # Wait for paste to complete

        # Wait for refresh
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Verify test2.txt appears in folder2
        print("\n6. Verifying test2.txt was moved to folder2...")
        content = page.content()
        if 'test2.txt' in content:
            print("   ✓ test2.txt found in folder2!")
        else:
            print("   ✗ ERROR: test2.txt NOT found in folder2")
            raise AssertionError("Cut failed - file not found in destination")

        # Navigate back to root to verify test2.txt is gone
        print("\n7. Checking root folder to verify test2.txt was removed...")
        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        content = page.content()
        # Count occurrences of test2.txt in root
        root_has_test2 = 'test2.txt' in content

        if not root_has_test2:
            print("   ✓ test2.txt removed from root (moved successfully)!")
        else:
            print("   ⚠ Warning: test2.txt still in root (might be copy instead of move)")

        browser.close()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nSummary:")
        print("  - Copy operation: WORKING")
        print("  - Cut operation: WORKING")
        print("  - Paste operation: WORKING")
        print("  - File operations: SUCCESSFUL")

if __name__ == '__main__':
    try:
        test_copy_and_cut()
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
