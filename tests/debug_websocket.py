#!/usr/bin/env python3
"""Debug script to capture WebSocket messages from the file browser"""
from playwright.sync_api import sync_playwright
import json
import time

PORT = '3000'
BASE_URL = f'http://localhost:{PORT}'

def debug_websocket():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Capture WebSocket messages
        ws_messages = []

        def on_websocket(ws):
            print(f"WebSocket opened: {ws.url}")

            def on_frame_received(payload):
                try:
                    data = json.loads(payload)
                    print("\n=== WebSocket Message RECEIVED ===")
                    print(json.dumps(data, indent=2))
                    ws_messages.append(('received', data))
                except:
                    print(f"Non-JSON payload: {payload[:100]}")

            def on_frame_sent(payload):
                try:
                    data = json.loads(payload)
                    print("\n=== WebSocket Message SENT ===")
                    print(json.dumps(data, indent=2))
                    ws_messages.append(('sent', data))
                except:
                    print(f"Non-JSON payload: {payload[:100]}")

            ws.on("framereceived", on_frame_received)
            ws.on("framesent", on_frame_sent)

        page.on("websocket", on_websocket)

        # Navigate to the page
        print(f"Navigating to {BASE_URL}")
        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')

        # Wait for WebSocket messages
        print("\nWaiting for WebSocket messages...")
        time.sleep(5)

        print(f"\n\n=== SUMMARY ===")
        print(f"Total messages captured: {len(ws_messages)}")

        for direction, msg in ws_messages:
            print(f"\n{direction.upper()}:")
            print(json.dumps(msg, indent=2))

        browser.close()

        return ws_messages

if __name__ == '__main__':
    debug_websocket()
