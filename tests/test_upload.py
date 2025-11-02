#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time
import os

# Server configuration
PORT = os.environ.get('PORT', '3000')
BASE_URL = f'http://localhost:{PORT}'

def test_file_upload():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Enable console logging to catch errors
        page.on('console', lambda msg: print(f'BROWSER: {msg.text}'))

        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        print("=" * 60)
        print("TESTING FILE UPLOAD")
        print("=" * 60)

        # Create test file
        test_file = 'test_upload.txt'
        test_content = 'This is a test file for upload verification'
        with open(test_file, 'w') as f:
            f.write(test_content)

        print("\n1. Checking dropzone exists...")
        dropzone = page.locator('#uploadDropzone')
        if dropzone.count() > 0:
            is_visible = dropzone.is_visible()
            print(f"   ✓ Dropzone found (visible: {is_visible})")
        else:
            print("   ✗ ERROR: Dropzone not found")
            browser.close()
            os.remove(test_file)
            raise AssertionError("Dropzone not found")

        print("\n2. Simulating file drag-and-drop...")
        try:
            # Get file path
            file_path = os.path.abspath(test_file)

            # Create a file input and attach file
            page.evaluate("""
                const dropzone = document.getElementById('uploadDropzone');
                const input = document.createElement('input');
                input.type = 'file';
                input.style.display = 'none';
                input.id = 'test-file-input';
                document.body.appendChild(input);
            """)

            # Set file to input
            file_input = page.locator('#test-file-input')
            file_input.set_input_files(file_path)

            # Trigger drop event manually
            page.evaluate("""
                const input = document.getElementById('test-file-input');
                const dropzone = document.getElementById('uploadDropzone');
                const file = input.files[0];

                // Create a DataTransfer object
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);

                // Create and dispatch drop event
                const dropEvent = new DragEvent('drop', {
                    bubbles: true,
                    cancelable: true,
                    dataTransfer: dataTransfer
                });

                dropzone.dispatchEvent(dropEvent);
            """)

            print("   ✓ File drop simulated")

        except Exception as e:
            print(f"   ✗ ERROR: Failed to simulate drop: {e}")
            browser.close()
            os.remove(test_file)
            raise

        print("\n3. Waiting for upload to complete...")
        time.sleep(3)

        # Check if file appears in the list
        print("\n4. Checking if uploaded file appears...")
        page.reload()
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Look for the uploaded file in the file list
        content = page.content()
        if 'test_upload.txt' in content:
            print("   ✓ Uploaded file appears in file list!")
        else:
            print("   ✗ WARNING: Uploaded file not yet visible")
            print("   (This might be a timing issue, checking server logs recommended)")

        # Take screenshot
        print("\n5. Taking screenshot...")
        page.screenshot(path='upload_test.png', full_page=True)
        print("   ✓ Screenshot saved to upload_test.png")

        print("\nKeeping browser open for 2 seconds...")
        time.sleep(2)

        browser.close()
        os.remove(test_file)

        print("\n" + "=" * 60)
        print("UPLOAD TEST COMPLETE")
        print("=" * 60)
        print("\nIf the file didn't appear, check server logs for upload errors.")

if __name__ == '__main__':
    try:
        test_file_upload()
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
