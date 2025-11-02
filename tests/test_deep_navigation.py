#!/usr/bin/env python3
"""Test deep subfolder navigation with WebSocket reuse"""

from playwright.sync_api import sync_playwright
import time
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    # Track WebSocket connections
    ws_connections = []
    path_requests = []

    def log_console(msg):
        text = msg.text
        if 'WebSocket connected' in text:
            ws_connections.append('connect')
            print(f'🔌 {text}')
        elif 'WebSocket disconnected' in text:
            ws_connections.append('disconnect')
            print(f'❌ {text}')
        elif 'Requesting path:' in text:
            path = text.split('Requesting path:')[1].strip()
            path_requests.append(path)
            print(f'📂 Requesting: {path if path else "/"} ')
        elif 'Ignoring message' in text:
            print(f'⏭️  {text}')

    page.on('console', log_console)

    print("="*60)
    print("DEEP NAVIGATION TEST WITH WEBSOCKET REUSE")
    print("="*60)
    print()

    # Load initial page
    print("1. Loading root...")
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')
    time.sleep(1)

    # Navigate deep: root -> folder1 -> subfolder1 -> deep1 -> deep2 -> deep3
    print("\n2. Going 5 levels deep: folder1 -> subfolder1 -> deep1 -> deep2 -> deep3")

    print("   → folder1")
    page.dblclick('text=folder1')
    time.sleep(1)

    print("   → subfolder1")
    page.dblclick('text=subfolder1')
    time.sleep(1)

    print("   → deep1")
    page.dblclick('text=deep1')
    time.sleep(1)

    print("   → deep2")
    page.dblclick('text=deep2')
    time.sleep(1)

    print("   → deep3")
    page.dblclick('text=deep3')
    time.sleep(1)

    # Verify we're at deep3
    if 'deep3' in page.content():
        print("   ✓ Reached deepest level (deep3)")

    # Navigate back all the way
    print("\n3. Navigating back 5 levels to root...")

    for i in range(5):
        print(f"   ← back (level {i+1})")
        page.click('#backButton')
        time.sleep(1)

    # Verify we're back at root
    if 'folder1' in page.content():
        print("   ✓ Back at root")

    # Jump to different branch
    print("\n4. Jumping to different branch: folder2 -> subfolder2")

    print("   → folder2")
    page.dblclick('text=folder2')
    time.sleep(1)

    print("   → subfolder2")
    page.dblclick('text=subfolder2')
    time.sleep(1)

    # Navigate back
    print("\n5. Navigating back to root...")
    page.click('#backButton')
    time.sleep(1)
    page.click('#backButton')
    time.sleep(1)

    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    print(f"WebSocket connections: {ws_connections.count('connect')}")
    print(f"WebSocket disconnections: {ws_connections.count('disconnect')}")
    print(f"Total path requests: {len(path_requests)}")
    print(f"\nPath sequence:")
    for i, path in enumerate(path_requests, 1):
        print(f"  {i}. {path if path else '/'}")

    print()
    if ws_connections.count('connect') == 1 and ws_connections.count('disconnect') == 0:
        print("✅ SUCCESS: Single WebSocket connection for all navigation!")
    else:
        print(f"❌ FAIL: Expected 1 connection, got {ws_connections.count('connect')}")

    if len(path_requests) >= 12:  # Should have ~13 requests
        print(f"✅ SUCCESS: All {len(path_requests)} path requests on same connection")
    else:
        print(f"⚠️  WARNING: Only {len(path_requests)} path requests (expected ~13)")

    print("="*60)

    browser.close()
# Server configuration
PORT = os.environ.get('PORT', '3000')
BASE_URL = f'http://localhost:{PORT}'

