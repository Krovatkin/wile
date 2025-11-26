#!/usr/bin/env python3
"""
Simple test for size tree delete operation
"""
from playwright.sync_api import sync_playwright
import subprocess
import time

BASE_URL = "http://localhost:3000"
WILE_PATH = "/Users/nikolayk/github/wile/wile"
TEST_DIR = "/Users/nikolayk/github/wile/test_sizes"

def start_server():
    cmd = [WILE_PATH, "--path", TEST_DIR, "--port", "3000", "--with-sizes", "--write"]
    print(f"Starting: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(4)
    return process

def stop_server(process):
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        time.sleep(1)

def get_folder_size(page, folder_name):
    folder = page.locator(f'li:has(span:text-is("{folder_name}"))').first
    size_text = folder.locator('.text-sm.text-gray-500').text_content().strip()
    return size_text

print("=" * 70)
print("SIMPLE DELETE TEST")
print("=" * 70)

process = start_server()

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(2)

        print("✓ Page loaded")

        page.wait_for_selector('li[data-file-type]', timeout=10000)
        time.sleep(1)

        # Get initial folder_A size
        initial_size = get_folder_size(page, "folder_A")
        print(f"\n1. Initial folder_A size: {initial_size}")

        # Navigate into folder_A
        page.locator('li:has(span:text-is("folder_A"))').first.dblclick()
        time.sleep(2)
        print("2. Navigated into folder_A")

        # Select file1.bin
        file1 = page.locator('li:has(span:text-is("file1.bin"))').first
        file1.click()
        time.sleep(1)
        print("3. Selected file1.bin (5 MB)")

        # Get the delete button
        page.locator('#copyBtn').click()  # Just to activate the selection
        time.sleep(0.5)

        # Look for delete button in the selected file
        delete_btn = file1.locator('button.delete-btn').first
        delete_btn.click()
        time.sleep(2)
        print("4. Clicked delete button")

        # Go back to root
        back_btn = page.locator('#backButton')
        if back_btn.is_visible():
            back_btn.click()
            time.sleep(2)
            print("5. Navigated back to root")

        # Check new size
        new_size = get_folder_size(page, "folder_A")
        print(f"\n✓ After delete, folder_A size: {new_size}")
        print(f"  (should be ~5 MB, was {initial_size})")

        # Take screenshot
        page.screenshot(path='test_delete_simple.png', full_page=True)
        print("\n✓ Screenshot saved: test_delete_simple.png")

        browser.close()

        if "5" in new_size:
            print("\n✅ DELETE TEST PASSED!")
        else:
            print("\n❌ DELETE TEST FAILED - size didn't update")

finally:
    stop_server(process)
