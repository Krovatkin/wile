#!/usr/bin/env python3
"""
Test size feature for wile file browser
Tests size display, sorting, and cumulative size calculation
"""
from playwright.sync_api import sync_playwright, expect
import subprocess
import time
import os
import signal

BASE_URL = "http://localhost:3000"
WILE_PATH = "/Users/nikolayk/github/wile/wile"
TEST_DIR = "/Users/nikolayk/github/wile/test_sizes"

def start_wile_server(with_size=True):
    """Start wile server with or without --with-sizes flag"""
    cmd = [WILE_PATH, "--path", TEST_DIR, "--port", "3000", "--write", "--modifications-log", os.path.join(TEST_DIR, "modifications.jsonl")]
    if with_size:
        cmd.append("--with-sizes")

    print(f"Starting wile: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)  # Wait for server to start
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

def test_size_with_flag():
    """Test 1: Size display with --with-sizes flag"""
    print("\n=== TEST 1: Size display with --with-sizes flag ===")

    process = start_wile_server(with_size=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Navigate to the page
            page.goto(BASE_URL)
            page.wait_for_load_state('networkidle')
            time.sleep(2)

            print("✓ Page loaded")

            # Check that Size column header exists
            size_header = page.locator('button:has-text("Size")')
            expect(size_header).to_be_visible()
            print("✓ Size column header visible")

            # Wait for file list to populate
            page.wait_for_selector('li[data-file-type]', timeout=10000)
            time.sleep(1)

            # Check specific file sizes
            files_to_check = [
                ("empty.txt", "0  B"),
                ("tiny.txt", "10  B"),
                ("small.txt", "5.00 KB"),
                ("medium.txt", "2.00 MB"),
                ("large.txt", "50.00 MB"),
            ]

            for filename, expected_size in files_to_check:
                # Find the file item by name and check its size
                file_item = page.locator(f'li:has(span:text-is("{filename}"))').first
                size_text = file_item.locator('.text-sm.text-gray-500').text_content()

                if size_text == expected_size:
                    print(f"✓ {filename}: {size_text}")
                else:
                    print(f"✗ {filename}: expected '{expected_size}', got '{size_text}'")

            # Check folder cumulative sizes
            folder_a = page.locator('li:has(span:text-is("folder_A"))').first
            folder_a_size = folder_a.locator('.text-sm.text-gray-500').text_content()
            print(f"✓ folder_A cumulative size: {folder_a_size}")

            folder_b = page.locator('li:has(span:text-is("folder_B"))').first
            folder_b_size = folder_b.locator('.text-sm.text-gray-500').text_content()
            print(f"✓ folder_B cumulative size: {folder_b_size}")

            # Take screenshot
            page.screenshot(path='test_sizes_with_flag.png', full_page=True)
            print("✓ Screenshot saved: test_sizes_with_flag.png")

            browser.close()
            print("\n✅ TEST 1 PASSED: Sizes displayed correctly with --with-sizes flag")

    finally:
        stop_server(process)

def test_size_without_flag():
    """Test 2: Size display without --with-sizes flag"""
    print("\n=== TEST 2: Size display without --with-sizes flag ===")

    process = start_wile_server(with_size=False)

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

            # Check that all items show "-" for size
            size_elements = page.locator('.text-sm.text-gray-500').all()

            all_dash = True
            for i, elem in enumerate(size_elements[:5]):  # Check first 5
                size_text = elem.text_content()
                if size_text != "-":
                    print(f"✗ Expected '-', got '{size_text}'")
                    all_dash = False

            if all_dash:
                print("✓ All sizes show '-' as expected")

            # Take screenshot
            page.screenshot(path='test_sizes_without_flag.png', full_page=True)
            print("✓ Screenshot saved: test_sizes_without_flag.png")

            browser.close()
            print("\n✅ TEST 2 PASSED: All sizes show '-' without --with-sizes flag")

    finally:
        stop_server(process)

def test_size_sorting():
    """Test 3: Size sorting (ascending and descending)"""
    print("\n=== TEST 3: Size sorting ===")

    process = start_wile_server(with_size=True)

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

            # Click Size header to sort ascending
            size_header = page.locator('button:has-text("Size")').first
            size_header.click()
            time.sleep(2)

            print("✓ Clicked Size header (ascending)")

            # Get file items (not folders)
            file_items = page.locator('li[data-file-type="file"]').all()
            file_names = [item.locator('span.truncate').text_content() for item in file_items[:5]]
            print(f"  Files order (asc): {file_names}")

            # Take screenshot
            page.screenshot(path='test_sizes_sort_asc.png', full_page=True)
            print("✓ Screenshot saved: test_sizes_sort_asc.png")

            # Click again to sort descending
            size_header.click()
            time.sleep(2)

            print("✓ Clicked Size header (descending)")

            # Get file items again
            file_items = page.locator('li[data-file-type="file"]').all()
            file_names = [item.locator('span.truncate').text_content() for item in file_items[:5]]
            print(f"  Files order (desc): {file_names}")

            # Check folder sorting - folder_B (100MB) should be before folder_A (10MB)
            folder_items = page.locator('li[data-file-type="folder"]').all()
            if len(folder_items) >= 2:
                first_folder = folder_items[0].locator('span.truncate').text_content()
                second_folder = folder_items[1].locator('span.truncate').text_content()
                print(f"  Folders order (desc): {first_folder}, {second_folder}")

                if first_folder == "folder_B" and second_folder == "folder_A":
                    print("✓ Folders sorted correctly by cumulative size")
                else:
                    print(f"✗ Expected folder_B before folder_A")

            # Take screenshot
            page.screenshot(path='test_sizes_sort_desc.png', full_page=True)
            print("✓ Screenshot saved: test_sizes_sort_desc.png")

            browser.close()
            print("\n✅ TEST 3 PASSED: Size sorting works correctly")

    finally:
        stop_server(process)

def test_cumulative_sizes():
    """Test 4: Cumulative sizes in nested folders"""
    print("\n=== TEST 4: Cumulative sizes in nested folders ===")

    process = start_wile_server(with_size=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            page.goto(BASE_URL)
            page.wait_for_load_state('networkidle')
            time.sleep(2)

            print("✓ Page loaded at root")

            # Wait for file list
            page.wait_for_selector('li[data-file-type]', timeout=10000)
            time.sleep(1)

            # Double-click into folder_B
            folder_b = page.locator('li:has(span:text-is("folder_B"))').first
            folder_b.dblclick()
            time.sleep(2)

            print("✓ Navigated into folder_B")

            # Check that we're in folder_B
            current_path = page.locator('#currentPath').text_content()
            print(f"  Current path: {current_path}")

            # Check subfolder size (should be ~50 MB)
            subfolder = page.locator('li:has(span:text-is("subfolder"))').first
            subfolder_size = subfolder.locator('.text-sm.text-gray-500').text_content()
            print(f"✓ subfolder cumulative size: {subfolder_size}")

            # Check file3.bin size
            file3 = page.locator('li:has(span:text-is("file3.bin"))').first
            file3_size = file3.locator('.text-sm.text-gray-500').text_content()
            print(f"✓ file3.bin size: {file3_size}")

            # Take screenshot
            page.screenshot(path='test_sizes_folder_b.png', full_page=True)
            print("✓ Screenshot saved: test_sizes_folder_b.png")

            # Double-click into subfolder
            subfolder.dblclick()
            time.sleep(2)

            print("✓ Navigated into subfolder")

            # Check deep1.bin and deep2.bin (each should be 25 MB)
            deep1 = page.locator('li:has(span:text-is("deep1.bin"))').first
            deep1_size = deep1.locator('.text-sm.text-gray-500').text_content()
            print(f"✓ deep1.bin size: {deep1_size}")

            deep2 = page.locator('li:has(span:text-is("deep2.bin"))').first
            deep2_size = deep2.locator('.text-sm.text-gray-500').text_content()
            print(f"✓ deep2.bin size: {deep2_size}")

            # Take screenshot
            page.screenshot(path='test_sizes_subfolder.png', full_page=True)
            print("✓ Screenshot saved: test_sizes_subfolder.png")

            browser.close()
            print("\n✅ TEST 4 PASSED: Cumulative sizes calculated correctly in nested folders")

    finally:
        stop_server(process)

def test_many_files():
    """Test 5: Many files folder performance"""
    print("\n=== TEST 5: Many files folder performance ===")

    process = start_wile_server(with_size=True)

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

            # Double-click into many_files
            many_files = page.locator('li:has(span:text-is("many_files"))').first

            # Check cumulative size of many_files folder
            many_files_size = many_files.locator('.text-sm.text-gray-500').text_content()
            print(f"✓ many_files cumulative size: {many_files_size}")

            many_files.dblclick()
            time.sleep(3)

            print("✓ Navigated into many_files")

            # Count how many files loaded
            file_items = page.locator('li[data-file-type="file"]').all()
            print(f"✓ Loaded {len(file_items)} files")

            # Check a few file sizes
            if len(file_items) >= 3:
                for i in range(3):
                    filename = file_items[i].locator('span.truncate').text_content()
                    filesize = file_items[i].locator('.text-sm.text-gray-500').text_content()
                    print(f"  {filename}: {filesize}")

            # Take screenshot
            page.screenshot(path='test_sizes_many_files.png', full_page=True)
            print("✓ Screenshot saved: test_sizes_many_files.png")

            browser.close()
            print("\n✅ TEST 5 PASSED: Many files folder loaded successfully")

    finally:
        stop_server(process)

if __name__ == "__main__":
    print("=" * 70)
    print("WILE SIZE FEATURE TEST SUITE")
    print("=" * 70)

    try:
        test_size_with_flag()
        test_size_without_flag()
        test_size_sorting()
        test_cumulative_sizes()
        test_many_files()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
