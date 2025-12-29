#!/usr/bin/env python3
"""
Test size tree updates for file operations (delete, rename, move, copy)
"""
from playwright.sync_api import sync_playwright
import subprocess
import time
import os

BASE_URL = "http://localhost:3000"
WILE_PATH = "/Users/nikolayk/github/wile/wile"
TEST_DIR = "/Users/nikolayk/github/wile/test_sizes"

def start_server():
    """Start wile server with --with-sizes and --write flags"""
    cmd = [WILE_PATH, "--path", TEST_DIR, "--port", "3000", "--with-sizes", "--write", "--modifications-log", os.path.join(TEST_DIR, "modifications.jsonl")]
    print(f"Starting wile: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)
    return process

def stop_server(process):
    """Stop the wile server"""
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        time.sleep(1)

def get_folder_size(page, folder_name):
    """Get the displayed size of a folder"""
    folder = page.locator(f'li:has(span:text-is("{folder_name}"))').first
    size_text = folder.locator('.text-sm.text-gray-500').text_content().strip()
    return size_text

def test_size_updates():
    """Test that file operations correctly update parent sizes"""
    print("\n=== TEST: Size Tree Updates ===")

    process = start_server()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(BASE_URL)
            page.wait_for_load_state('networkidle')
            time.sleep(2)

            print("✓ Page loaded")

            # Wait for file list
            page.wait_for_selector('li[data-file-type]', timeout=10000)
            time.sleep(1)

            # Get initial size of folder_A (should be 10 MB)
            initial_folder_a_size = get_folder_size(page, "folder_A")
            print(f"✓ Initial folder_A size: {initial_folder_a_size}")

            # TEST 1: Delete a file and verify parent size decreases
            print("\n--- Test 1: Delete file ---")
            page.locator('li:has(span:text-is("folder_A"))').first.dblclick()
            time.sleep(2)
            print("  Navigated into folder_A")

            # Select file1.bin (5 MB)
            file1 = page.locator('li:has(span:text-is("file1.bin"))').first
            file1.click()
            time.sleep(1)
            print("  Selected file1.bin")

            # Click delete button (trash icon)
            delete_btn = file1.locator('button[title*="Delete"]').first
            delete_btn.click()
            time.sleep(1)

            # Confirm delete in dialog
            try:
                page.get_by_role("button", name="OK").click()
                time.sleep(2)
                print("  Deleted file1.bin")
            except:
                print("  No confirmation dialog, proceeding...")

            # Go back to root
            back_btn = page.locator('#backButton')
            if back_btn.is_visible():
                back_btn.click()
                time.sleep(2)
                print("  Navigated back to root")

            # Check folder_A size decreased (should be ~5 MB now)
            new_folder_a_size = get_folder_size(page, "folder_A")
            print(f"✓ After delete, folder_A size: {new_folder_a_size}")
            print(f"  Expected: ~5 MB (was {initial_folder_a_size})")

            # TEST 2: Rename a file and verify size unchanged
            print("\n--- Test 2: Rename file ---")
            tiny_file = page.locator('li:has(span:text-is("tiny.txt"))').first
            initial_tiny_size = tiny_file.locator('.text-sm.text-gray-500').text_content().strip()
            print(f"  Initial tiny.txt size: {initial_tiny_size}")

            # Click rename button
            rename_btn = tiny_file.locator('button[title*="Rename"]').first
            rename_btn.click()
            time.sleep(1)

            # Enter new name
            page.fill('input[type="text"]', 'renamed_tiny.txt')
            page.get_by_role("button", name="OK").click()
            time.sleep(2)
            print("  Renamed tiny.txt to renamed_tiny.txt")

            # Check size unchanged
            renamed_file = page.locator('li:has(span:text-is("renamed_tiny.txt"))').first
            renamed_size = renamed_file.locator('.text-sm.text-gray-500').text_content().strip()
            print(f"✓ After rename, size: {renamed_size}")
            print(f"  Expected: same as before ({initial_tiny_size})")

            # TEST 3: Move a file and verify sizes update
            print("\n--- Test 3: Move file ---")
            initial_folder_b_size = get_folder_size(page, "folder_B")
            print(f"  Initial folder_B size: {initial_folder_b_size}")

            # Select small.txt (5 KB) and cut it
            small_file = page.locator('li:has(span:text-is("small.txt"))').first
            small_file.click()
            time.sleep(1)
            small_size = small_file.locator('.text-sm.text-gray-500').text_content().strip()
            print(f"  Selected small.txt ({small_size})")

            # Click cut button
            page.locator('#cutBtn').click()
            time.sleep(1)
            print("  Cut small.txt")

            # Navigate into folder_B
            page.locator('li:has(span:text-is("folder_B"))').first.dblclick()
            time.sleep(2)
            print("  Navigated into folder_B")

            # Paste the file
            page.locator('#pasteBtn').click()
            time.sleep(2)
            print("  Pasted small.txt into folder_B")

            # Go back and check sizes
            back_btn = page.locator('#backButton')
            if back_btn.is_visible():
                back_btn.click()
                time.sleep(2)

            new_folder_b_size = get_folder_size(page, "folder_B")
            print(f"✓ After move, folder_B size: {new_folder_b_size}")
            print(f"  Expected: increased by {small_size} from {initial_folder_b_size}")

            # TEST 4: Copy a file and verify new parent increases
            print("\n--- Test 4: Copy file ---")

            # Select medium.txt and copy it
            medium_file = page.locator('li:has(span:text-is("medium.txt"))').first
            medium_file.click()
            time.sleep(1)
            medium_size = medium_file.locator('.text-sm.text-gray-500').text_content().strip()
            print(f"  Selected medium.txt ({medium_size})")

            # Click copy button
            page.locator('#copyBtn').click()
            time.sleep(1)
            print("  Copied medium.txt")

            current_folder_a_size = get_folder_size(page, "folder_A")
            print(f"  Current folder_A size: {current_folder_a_size}")

            # Navigate into folder_A
            page.locator('li:has(span:text-is("folder_A"))').first.dblclick()
            time.sleep(2)
            print("  Navigated into folder_A")

            # Paste the file
            page.locator('#pasteBtn').click()
            time.sleep(3)
            print("  Pasted medium.txt into folder_A")

            # Go back and check folder_A size increased
            back_btn = page.locator('#backButton')
            if back_btn.is_visible():
                back_btn.click()
                time.sleep(2)

            final_folder_a_size = get_folder_size(page, "folder_A")
            print(f"✓ After copy, folder_A size: {final_folder_a_size}")
            print(f"  Expected: increased by {medium_size} from {current_folder_a_size}")

            # Take final screenshot
            page.screenshot(path='test_size_updates.png', full_page=True)
            print("\n✓ Screenshot saved: test_size_updates.png")

            browser.close()
            print("\n✅ All size update tests completed!")

    finally:
        stop_server(process)

if __name__ == "__main__":
    print("=" * 70)
    print("SIZE TREE UPDATE TEST")
    print("=" * 70)

    try:
        test_size_updates()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
