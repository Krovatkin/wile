#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time
import os

# Server configuration
PORT = os.environ.get('PORT', '3000')
BASE_URL = f'http://localhost:{PORT}'

def test_file_browser():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to file browser
        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Screenshot 1: Root folder
        print("Taking screenshot of root folder...")
        page.screenshot(path='screenshot_root.png')
        print("Saved screenshot_root.png")

        # Navigate to folder1
        print("\nNavigating to folder1...")
        page.dblclick('text=folder1')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Screenshot 2: folder1
        print("Taking screenshot of folder1...")
        page.screenshot(path='screenshot_folder1.png')
        print("Saved screenshot_folder1.png")

        # Navigate to subfolder1
        print("\nNavigating to subfolder1...")
        page.dblclick('text=subfolder1')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Screenshot 3: subfolder1
        print("Taking screenshot of subfolder1...")
        page.screenshot(path='screenshot_subfolder1.png')
        print("Saved screenshot_subfolder1.png")

        # Go back to root
        print("\nNavigating back to root...")
        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Navigate to folder2
        print("Navigating to folder2...")
        page.dblclick('text=folder2')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Screenshot 4: folder2
        print("Taking screenshot of folder2...")
        page.screenshot(path='screenshot_folder2.png')
        print("Saved screenshot_folder2.png")

        # Navigate to subfolder2
        print("\nNavigating to subfolder2...")
        page.dblclick('text=subfolder2')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Screenshot 5: subfolder2
        print("Taking screenshot of subfolder2...")
        page.screenshot(path='screenshot_subfolder2.png')
        print("Saved screenshot_subfolder2.png")

        browser.close()
        print("\nAll screenshots saved successfully!")

if __name__ == '__main__':
    test_file_browser()
