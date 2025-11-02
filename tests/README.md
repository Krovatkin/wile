# Wile Test Suite

This directory contains all tests for the wile file browser application.

## Quick Start

### 1. Setup Test Environment

From project root:
```bash
./tests/setup_test_env.sh
```

This creates the `tmp_test` folder structure with all necessary files and images.

### 2. Run Server

From project root:
```bash
go build -o file-browser && ./file-browser -port 3000 -path tmp_test -write
```

**Note:** Port 3000 is the default. If port 3000 is in use, you can:
- Use a different port: `./file-browser -port 8080 -path tmp_test -write`
- Kill the process using port 3000: `lsof -i :3000` then `kill -9 <PID>`

### 3. Run Tests

From project root:
```bash
/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python tests/test_<name>.py
```

Or from tests directory:
```bash
cd tests
/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_<name>.py
```

**Using a custom port:**
```bash
# If your server is running on port 8080
PORT=8080 /Users/nikolayk/opt/miniconda3/envs/playwright/bin/python tests/test_browser.py
```

## Test Files

| File | Description |
|------|-------------|
| `test_browser.py` | Basic folder navigation |
| `test_copy_cut.py` | Copy and cut file operations |
| `test_deep_navigation.py` | Deep folder navigation and WebSocket reuse |
| `test_download.py` | File download functionality |
| `test_header.py` | Column headers display |
| `test_icons.py` | Icon constants verification |
| `test_lightbox_navigation.py` | Lightbox image navigation |
| `test_lightbox_3images.py` | Lightbox with 3 test images |
| `test_sorting.py` | Sorting functionality |
| `test_tab_sorting.py` | Per-tab sort state preservation |
| `test_upload.py` | File upload via drag-and-drop |

## Helper Scripts

| File | Description |
|------|-------------|
| `setup_test_env.sh` | Creates test environment |
| `create_test_images.py` | Helper to create test images |
| `create_backup_images.py` | Helper to backup test images |

## Documentation

See [`test_ui.md`](./test_ui.md) for detailed test documentation including:
- Test environment setup
- Individual test descriptions
- Expected behavior
- Test results

## Running All Tests

From project root:
```bash
cd tests
for test in test_*.py; do
    echo "Running $test..."
    /Users/nikolayk/opt/miniconda3/envs/playwright/bin/python "$test"
done
```
