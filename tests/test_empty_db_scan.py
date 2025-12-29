#!/usr/bin/env python3
"""
Test that starting with an empty/non-existent database triggers a scan.
"""
import subprocess
import time
import os
import shutil

WILE_PATH = "./wile"
TEST_DIR = "/tmp/wile_empty_db_test"
PORT = "9099"
DB_FILE = os.path.join(TEST_DIR, "empty.db")
LOG_FILE = os.path.join(TEST_DIR, "modifications.jsonl")

def setup_env():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)
    
    # Create some files to scan
    os.makedirs(os.path.join(TEST_DIR, "sub"))
    with open(os.path.join(TEST_DIR, "sub", "file1.txt"), "w") as f:
        f.write("content")

def test_empty_db_trigger_scan():
    print("=" * 70)
    print("TEST: Empty DB triggers scan")
    print("=" * 70)

    setup_env()

    # Ensure DB doesn't exist
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    cmd = [
        WILE_PATH, 
        "--path", TEST_DIR, 
        "--port", PORT, 
        "--sizes-db", DB_FILE,
        "--write",
        "--modifications-log", LOG_FILE
    ]
    
    print(f"Starting server with non-existent DB: {DB_FILE}")
    print(f"Command: {' '.join(cmd)}")

    # Start process and capture output
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, # Merge stderr into stdout
        universal_newlines=True,
        bufsize=0 # Unbuffered
    )

    found_loading = False
    found_computing = False
    
    try:
        # Read output line by line with a timeout mechanism
        start_time = time.time()
        while time.time() - start_time < 10:
            # Non-blocking read? Python's readline is blocking but we can rely on fast startup
            # A cleaner way given bufsize=0 is iterating, but subprocess pipe can be tricky.
            # We'll just read line by line.
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if line:
                print(f"LOG: {line.strip()}")
                if "Loading size tree from bbolt database..." in line:
                    found_loading = True
                if "Computing directory sizes..." in line:
                    found_computing = True
                
                # If we found both, test passed!
                if found_loading and found_computing:
                    print("\n✅ SUCCESS: Found both log messages!")
                    print("   - 'Loading size tree from bbolt database...'")
                    print("   - 'Computing directory sizes...'")
                    return

        if not found_loading:
             print("\n❌ FAILED: Did not find 'Loading size tree...' message")
        if not found_computing:
             print("\n❌ FAILED: Did not find 'Computing directory sizes...' message (Bug regression?)")
        
        raise Exception("Test Failed")

    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except:
            process.kill()

if __name__ == "__main__":
    try:
        test_empty_db_trigger_scan()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
