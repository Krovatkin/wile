#!/bin/bash

# Run all wile tests
echo "======================================================================"
echo "RUNNING ALL WILE TESTS"
echo "======================================================================"
echo ""

PYTHON="/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python"

# Tests to run
TESTS=(
    "tests/test_sizes.py"
    "tests/test_modifications_log.py"
    "tests/test_sorting.py"
    "tests/test_tab_sorting.py"
    "tests/test_lightbox_navigation.py"
    "tests/test_lightbox_3images.py"
    "tests/test_deep_navigation.py"
)

PASSED=0
FAILED=0
FAILED_TESTS=()

for test in "${TESTS[@]}"; do
    echo "----------------------------------------------------------------------"
    echo "Running: $test"
    echo "----------------------------------------------------------------------"

    if $PYTHON "$test" 2>&1; then
        echo "✅ PASSED: $test"
        ((PASSED++))
    else
        echo "❌ FAILED: $test"
        ((FAILED++))
        FAILED_TESTS+=("$test")
    fi
    echo ""

    # Clean up between tests
    pkill -f "wile.*--port" 2>/dev/null
    sleep 2
done

echo "======================================================================"
echo "TEST RESULTS SUMMARY"
echo "======================================================================"
echo "Total tests run: $((PASSED + FAILED))"
echo "Passed: $PASSED"
echo "Failed: $FAILED"

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    exit 1
else
    echo ""
    echo "✅ ALL TESTS PASSED!"
    exit 0
fi
