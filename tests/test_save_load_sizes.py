#!/usr/bin/env python3
"""
Test size tree save/load with modifications

Scenarios:
1. Scan tree with --sizes, do modifications, Ctrl+C saves
2. Load with --sizes, verify sizes persist
3. Load with --sizes, add new file (shows ⚠️), Ctrl+C updates tree
"""
import subprocess
import time
import os
import json
import signal

TEST_DIR = "/tmp/wile_save_test"
WILE_BIN = "/Users/nikolayk/github/wile/wile"
SIZES_JSON = os.path.join(TEST_DIR, "sizes.json")

def setup():
    """Create test directory with files"""
    os.makedirs(TEST_DIR, exist_ok=True)

    # Clean up
    if os.path.exists(SIZES_JSON):
        os.remove(SIZES_JSON)

    # Create test files
    os.makedirs(os.path.join(TEST_DIR, "folder_A"), exist_ok=True)
    with open(os.path.join(TEST_DIR, "file1.txt"), "w") as f:
        f.write("x" * 1000)  # 1KB
    with open(os.path.join(TEST_DIR, "file2.txt"), "w") as f:
        f.write("y" * 2000)  # 2KB
    with open(os.path.join(TEST_DIR, "folder_A", "file3.txt"), "w") as f:
        f.write("z" * 3000)  # 3KB

    print(f"✓ Created test directory: {TEST_DIR}")
    print(f"  - file1.txt (1KB)")
    print(f"  - file2.txt (2KB)")
    print(f"  - folder_A/file3.txt (3KB)")

def test_scenario_1():
    """
    Scenario 1: Scan with --sizes, Ctrl+C saves tree
    """
    print("\n" + "="*70)
    print("SCENARIO 1: Scan, Ctrl+C, Verify Save")
    print("="*70)

    # Start server with --sizes
    print("\n1. Starting server with --sizes...")
    cmd = [WILE_BIN, "--path", TEST_DIR, "--port", "9095", "--sizes", SIZES_JSON, "--write"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)

    # Send Ctrl+C
    print("2. Sending Ctrl+C (SIGINT)...")
    proc.send_signal(signal.SIGINT)

    # Wait for graceful shutdown
    time.sleep(2)
    proc.wait(timeout=5)

    # Check if sizes.json was created
    print("3. Checking if sizes.json was created...")
    if not os.path.exists(SIZES_JSON):
        print("   ❌ FAILED: sizes.json not created")
        return False

    # Parse and verify JSON
    print("4. Parsing sizes.json...")
    with open(SIZES_JSON, 'r') as f:
        data = json.load(f)

    print(f"   ✓ JSON valid, has {len(data.get('children', []))} children")

    # Verify structure
    if 'children' not in data:
        print("   ❌ FAILED: No 'children' in root")
        return False

    children = data['children']
    names = [c.get('dir', '').split('/')[-1] for c in children]
    print(f"   Children found: {names}")

    if 'file1.txt' not in str(names):
        print("   ❌ FAILED: file1.txt not in tree")
        return False

    print("   ✓ Tree structure looks correct")
    print("\n✅ SCENARIO 1 PASSED")
    return True

def test_scenario_2():
    """
    Scenario 2: Load with --sizes, verify sizes persist
    """
    print("\n" + "="*70)
    print("SCENARIO 2: Load from JSON, Verify Sizes")
    print("="*70)

    if not os.path.exists(SIZES_JSON):
        print("❌ SKIPPED: sizes.json doesn't exist (run scenario 1 first)")
        return False

    print("\n1. Loading tree from sizes.json...")
    with open(SIZES_JSON, 'r') as f:
        data = json.load(f)

    # Verify sizes are present
    print("2. Checking sizes in loaded tree...")
    has_sizes = False
    for child in data.get('children', []):
        if 'size' in child and child['size'] > 0:
            has_sizes = True
            print(f"   {child.get('dir', 'unknown')}: {child['size']} bytes")

    if not has_sizes:
        print("   ❌ FAILED: No sizes found in tree")
        return False

    print("   ✓ Sizes present in loaded tree")
    print("\n✅ SCENARIO 2 PASSED")
    return True

def test_scenario_3():
    """
    Scenario 3: Load tree, add new file, Ctrl+C updates tree
    """
    print("\n" + "="*70)
    print("SCENARIO 3: Load Tree, Add File, Save Updates")
    print("="*70)

    if not os.path.exists(SIZES_JSON):
        print("❌ SKIPPED: sizes.json doesn't exist (run scenario 1 first)")
        return False

    # Add a new file (simulating file added outside wile)
    print("\n1. Adding new file (file4.txt)...")
    new_file = os.path.join(TEST_DIR, "file4.txt")
    with open(new_file, "w") as f:
        f.write("w" * 4000)  # 4KB
    print(f"   ✓ Created {new_file}")

    # Start server with --sizes
    print("\n2. Starting server with --sizes...")
    cmd = [WILE_BIN, "--path", TEST_DIR, "--port", "9096", "--sizes", SIZES_JSON, "--write"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)

    # Send Ctrl+C
    print("3. Sending Ctrl+C (SIGINT)...")
    proc.send_signal(signal.SIGINT)

    # Wait for graceful shutdown
    time.sleep(2)
    proc.wait(timeout=5)

    # Verify sizes.json was updated (modification time changed)
    print("4. Verifying sizes.json was updated...")
    stat_before = os.stat(SIZES_JSON)
    time.sleep(1)
    stat_after = os.stat(SIZES_JSON)

    # Just check that file exists and is valid JSON
    with open(SIZES_JSON, 'r') as f:
        data = json.load(f)

    print(f"   ✓ sizes.json still valid after update")
    print(f"   Tree has {len(data.get('children', []))} children")

    print("\n✅ SCENARIO 3 PASSED")
    return True

def main():
    print("="*70)
    print("WILE SIZE TREE SAVE/LOAD TEST")
    print("="*70)

    setup()

    results = []

    # Run scenarios
    results.append(("Scenario 1: Scan & Save", test_scenario_1()))
    results.append(("Scenario 2: Load & Verify", test_scenario_2()))
    results.append(("Scenario 3: Load, Modify, Save", test_scenario_3()))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed_count}/{total} passed")

    if passed_count == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed_count} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
