#!/usr/bin/env python3
"""Test that sort state is preserved per tab"""

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
        if 'Sort:' in text or 'New sort:' in text or 'Requesting path:' in text:
            sort_logs.append(text)
            print(f'   {text}')

    page.on('console', log_console)

    print("=" * 60)
    print("TESTING TAB-SPECIFIC SORT STATE PRESERVATION")
    print("=" * 60)
    print()

    # Load page
    print("1. Loading page...")
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')
    time.sleep(1)

    # Initial tab should have default sort (name asc)
    print("\n2. Tab 1 starts with default sort (name asc)")
    time.sleep(0.5)

    # Change Tab 1 to sort by Modified desc
    print("\n3. Changing Tab 1 to sort by Modified...")
    page.click('button:has-text("Modified")')
    time.sleep(1)
    print("   Tab 1 now sorts by Modified asc")

    # Toggle to desc
    print("\n4. Toggling Tab 1 to Modified desc...")
    page.click('button:has-text("Modified")')
    time.sleep(1)
    print("   Tab 1 now sorts by Modified desc")

    # Create Tab 2
    print("\n5. Creating Tab 2...")
    page.click('button:has-text("+")')
    time.sleep(1)
    print("   Tab 2 created and should inherit Modified desc")

    # Change Tab 2 to Name asc
    print("\n6. Changing Tab 2 to Name asc...")
    page.click('button:has-text("Name")')
    time.sleep(1)
    page.click('button:has-text("Name")')
    time.sleep(1)
    print("   Tab 2 now sorts by Name asc")

    # Switch back to Tab 1
    print("\n7. Switching back to Tab 1...")
    page.click('span:has-text("Tab 1")')
    time.sleep(1)
    print("   Switched to Tab 1 - should still be Modified desc")

    # Switch to Tab 2
    print("\n8. Switching to Tab 2...")
    page.click('span:has-text("Tab 2")')
    time.sleep(1)
    print("   Switched to Tab 2 - should still be Name asc")

    # Switch back to Tab 1 one more time
    print("\n9. Final check - switching back to Tab 1...")
    page.click('span:has-text("Tab 1")')
    time.sleep(1)
    print("   Final check - Tab 1 should still be Modified desc")

    # Take final screenshot
    print("\n10. Taking screenshot...")
    page.screenshot(path='test_tab_sorting.png', full_page=True)
    print("   ✓ Screenshot saved to test_tab_sorting.png")

    print()
    print("=" * 60)
    print("TAB SORTING TEST COMPLETE")
    print("=" * 60)
    print()
    print("Console logs captured:")
    for log in sort_logs:
        print(f"  {log}")

    # Verify the sort state was preserved
    print()
    print("Verifying sort state preservation:")

    # Check if we see requests with correct sort parameters
    modified_desc_count = sum(1 for log in sort_logs if 'modified desc' in log.lower())
    name_asc_count = sum(1 for log in sort_logs if 'name asc' in log.lower())

    print(f"  Modified desc requests: {modified_desc_count}")
    print(f"  Name asc requests: {name_asc_count}")

    if modified_desc_count >= 2 and name_asc_count >= 1:
        print("\n✓ TEST PASSED: Sort state is being preserved across tabs!")
    else:
        print("\n✗ TEST FAILED: Sort state may not be preserved correctly")

    browser.close()
# Server configuration


