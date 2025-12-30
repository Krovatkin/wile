#!/bin/bash
set +e

# Reset test environment
echo "Resetting test environment..."
chmod +x tests/setup_test_env.sh
./tests/setup_test_env.sh

# Build the server
echo "Building server..."
go build -o file-browser

# Start server in background
./file-browser -port 9102 -path tmp_test -write -modifications-log tmp_test/modifications.jsonl > server.log 2>&1 &
SERVER_PID=$!
echo "Server started with PID $SERVER_PID"

# Wait for server
sleep 5

# Define Python path
PYTHON_PATH="/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python"

# Run Tests
echo "---------------------------------------------------"
echo "Running test_copy_cut.py"
PORT=9102 $PYTHON_PATH tests/test_copy_cut.py

echo "---------------------------------------------------"
echo "Running test_lightbox_navigation.py"
PORT=9102 $PYTHON_PATH tests/test_lightbox_navigation.py

echo "---------------------------------------------------"
echo "Running test_tabs_operations.py"
PORT=9102 $PYTHON_PATH tests/test_tabs_operations.py

# Cleanup
echo "Stopping server..."
kill $SERVER_PID
echo "Done."
