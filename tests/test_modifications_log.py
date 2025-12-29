#!/usr/bin/env python3
"""
Test modifications.jsonl logging functionality
"""
import json
import os
import subprocess
import time
import requests

# Server configuration
WILE_PATH = "/Users/nikolayk/github/wile/wile"
TEST_DIR = "/tmp/wile_log_test"
PORT = "9002"
BASE_URL = f"http://localhost:{PORT}"
LOG_FILE = os.path.join(TEST_DIR, "modifications.jsonl")

def setup_test_env():
    """Create test directory and files"""
    os.makedirs(TEST_DIR, exist_ok=True)

    # Remove old log file
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    # Create test files
    with open(os.path.join(TEST_DIR, "file1.txt"), "w") as f:
        f.write("test1")
    with open(os.path.join(TEST_DIR, "file2.txt"), "w") as f:
        f.write("test2")
    with open(os.path.join(TEST_DIR, "file3.txt"), "w") as f:
        f.write("test3")

    # Create subdirectories
    os.makedirs(os.path.join(TEST_DIR, "folder_A"), exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, "folder_B"), exist_ok=True)

    with open(os.path.join(TEST_DIR, "folder_A", "test.txt"), "w") as f:
        f.write("content")

    print(f"✓ Test environment created: {TEST_DIR}")

def start_server():
    """Start wile server"""
    cmd = [WILE_PATH, "--path", TEST_DIR, "--port", PORT, "--write", "--modifications-log", LOG_FILE]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    return process

def stop_server(process):
    """Stop wile server"""
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        time.sleep(1)

def read_jsonl():
    """Read and parse JSONL log file"""
    if not os.path.exists(LOG_FILE):
        return []

    entries = []
    with open(LOG_FILE, 'r') as f:
        for line in f:
            entries.append(json.loads(line))
    return entries

def test_modifications_log():
    """Test JSONL logging for all file operations"""

    print("=" * 70)
    print("TESTING MODIFICATIONS.JSONL LOGGING")
    print("=" * 70)

    setup_test_env()
    process = start_server()

    try:
        # Wait for server to be ready
        for _ in range(10):
            try:
                r = requests.get(f"{BASE_URL}/")
                if r.status_code == 200:
                    print("✓ Server is ready\n")
                    break
            except:
                time.sleep(0.5)
        else:
            raise Exception("Server failed to start")

        # Verify log file doesn't exist yet
        assert not os.path.exists(LOG_FILE), "Log file should not exist before operations"
        print("✓ Log file does not exist initially\n")

        # Test 1: Single delete
        print("Test 1: Delete single file")
        r = requests.get(f"{BASE_URL}/manage", params={"action": "delete", "srcs": "file1.txt"})
        assert r.json()["status"] == "ok", "Delete failed"
        time.sleep(0.2)

        entries = read_jsonl()
        assert len(entries) == 1, f"Expected 1 entry, got {len(entries)}"
        assert entries[0]["action"] == "delete", "Action should be delete"
        assert entries[0]["sources"] == ["file1.txt"], "Sources should be ['file1.txt']"
        assert "timestamp" in entries[0], "Entry should have timestamp"
        print("✓ Single delete logged correctly\n")

        # Test 2: Bulk delete
        print("Test 2: Delete multiple files")
        params = [("action", "delete"), ("srcs", "file2.txt"), ("srcs", "file3.txt")]
        r = requests.get(f"{BASE_URL}/manage", params=params)
        assert r.json()["status"] == "ok", "Bulk delete failed"
        time.sleep(0.2)

        entries = read_jsonl()
        assert len(entries) == 2, f"Expected 2 entries, got {len(entries)}"
        assert entries[1]["sources"] == ["file2.txt", "file3.txt"], "Should have 2 sources"
        print("✓ Bulk delete logged correctly\n")

        # Test 3: Copy operation
        print("Test 3: Copy file")
        r = requests.get(f"{BASE_URL}/manage", params={
            "action": "copy",
            "srcs": "folder_A/test.txt",
            "dest": "folder_B"
        })
        assert r.json()["status"] == "ok", "Copy failed"
        time.sleep(0.2)

        entries = read_jsonl()
        assert len(entries) == 3, f"Expected 3 entries, got {len(entries)}"
        assert entries[2]["action"] == "copy", "Action should be copy"
        assert entries[2]["dest"] == "folder_B", "Dest should be folder_B"
        print("✓ Copy operation logged correctly\n")

        # Test 4: Move (paste) operation
        print("Test 4: Move (paste) folder")
        r = requests.get(f"{BASE_URL}/manage", params={
            "action": "paste",
            "srcs": "folder_A",
            "dest": "folder_B"
        })
        assert r.json()["status"] == "ok", "Paste failed"
        time.sleep(0.2)

        entries = read_jsonl()
        assert len(entries) == 4, f"Expected 4 entries, got {len(entries)}"
        assert entries[3]["action"] == "paste", "Action should be paste"
        print("✓ Move operation logged correctly\n")

        # Test 5: Operation with error
        print("Test 5: Delete non-existent file (should log error)")
        r = requests.get(f"{BASE_URL}/manage", params={"action": "delete", "srcs": "nonexistent.txt"})
        assert r.json()["status"] == "error", "Should return error status"
        time.sleep(0.2)

        entries = read_jsonl()
        assert len(entries) == 5, f"Expected 5 entries, got {len(entries)}"
        assert "errors" in entries[4], "Entry should have errors field"
        assert len(entries[4]["errors"]) > 0, "Should have at least one error"
        print("✓ Error logged correctly\n")

        # Verify JSONL format
        print("Test 6: Verify JSONL format")
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 5, f"Should have 5 lines, got {len(lines)}"

        # Each line should be valid JSON
        for i, line in enumerate(lines):
            try:
                json.loads(line)
            except json.JSONDecodeError:
                raise AssertionError(f"Line {i+1} is not valid JSON: {line}")

        # Entire file should NOT be valid JSON (not an array)
        with open(LOG_FILE, 'r') as f:
            full_content = f.read()

        try:
            json.loads(full_content)
            raise AssertionError("Entire file should not be valid JSON (should be JSONL, not JSON array)")
        except json.JSONDecodeError:
            pass  # This is expected

        print("✓ JSONL format is correct (one JSON object per line)\n")

        # Display log summary
        print("=" * 70)
        print("LOG SUMMARY")
        print("=" * 70)
        for i, entry in enumerate(entries, 1):
            print(f"\nEntry {i}:")
            print(f"  Time:    {entry['timestamp']}")
            print(f"  Action:  {entry['action']}")
            print(f"  Sources: {entry['sources']}")
            if entry.get('dest'):
                print(f"  Dest:    {entry['dest']}")
            if entry.get('errors'):
                print(f"  Errors:  {entry['errors']}")

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print(f"✓ {len(entries)} operations logged correctly")
        print(f"✓ JSONL format verified")
        print(f"✓ Errors captured in log")
        print(f"✓ Log file: {LOG_FILE}")

    finally:
        stop_server(process)

if __name__ == "__main__":
    test_modifications_log()
