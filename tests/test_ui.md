# File Browser UI Test Documentation

## Test Environment Setup

### Quick Setup

Run the setup script to create the test environment:

**From project root:**
```bash
./tests/setup_test_env.sh
```

**From tests directory:**
```bash
cd tests
./setup_test_env.sh
```

This script will:
- Create the `tmp_test` folder in project root
- Generate all text files
- Create test images (requires ImageMagick or Python PIL)

### Server Configuration

**Default Port:** The tests use port **3000** by default.

**Starting the server:**
```bash
# Default (port 3000)
go build -o file-browser && ./file-browser -port 3000 -path tmp_test -write
```

**If port 3000 is already in use:**

Option 1: Use a different port for the server and tests:
```bash
# Start server on port 8080
./file-browser -port 8080 -path tmp_test -write

# Run tests with custom port
PORT=8080 /Users/nikolayk/opt/miniconda3/envs/playwright/bin/python tests/test_browser.py
```

Option 2: Find and kill the process using port 3000:
```bash
# Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>
```

**Port Configuration:**
All test files now support the `PORT` environment variable. If not set, they default to 3000:
- `PORT=3000` - Default (http://localhost:3000)
- `PORT=8080` - Alternative (http://localhost:8080)
- `PORT=5000` - Custom port (http://localhost:5000)

### Folder Structure
```
tmp_test/
├── folder1/
│   ├── file1.txt
│   ├── screenshot_root.png
│   └── subfolder1/
│       ├── deep_file.txt
│       └── screenshot_subfolder1.png
├── folder2/
│   ├── file2.txt
│   ├── screenshot_subfolder2.png
│   └── subfolder2/
│       ├── another_deep.txt
│       └── screenshot_folder1.png
├── folder3/
│   ├── file3.txt
│   └── screenshot_folder2.png
├── test1.txt
└── test2.txt
```

## Navigation Test Steps

### Step 1: Root Folder View
**URL**: `http://127.0.0.1:8080`

**Expected Path Display**: `/Users/nikolayk/github/wile/tmp_test`

**Expected Items**:
- 📁 folder1
- 📁 folder2
- 📁 folder3
- 📄 test1.txt
- 📄 test2.txt

**Actions**:
- Load page
- Wait for content to load
- Take screenshot: `screenshot_root.png`

**UI Elements**:
- Back button: HIDDEN (at root)
- Selection count: "No items selected"
- Tab: "Tab 1"

---

### Step 2: Navigate to folder1
**Action**: Double-click on "folder1"

**Expected Path Display**: `/Users/nikolayk/github/wile/tmp_test/folder1`

**Expected Items**:
- 📁 subfolder1
- 📄 file1.txt
- 🖼️ screenshot_root.png

**Actions**:
- Take screenshot: `screenshot_folder1.png`

**UI Elements**:
- Back button: VISIBLE
- Selection count: "No items selected"

---

### Step 3: Navigate to subfolder1
**Action**: Double-click on "subfolder1"

**Expected Path Display**: `/Users/nikolayk/github/wile/tmp_test/folder1/subfolder1`

**Expected Items**:
- 📄 deep_file.txt
- 🖼️ screenshot_subfolder1.png

**Actions**:
- Take screenshot: `screenshot_subfolder1.png`

**UI Elements**:
- Back button: VISIBLE
- Selection count: "No items selected"

---

### Step 4: Navigate back to root
**Action**: Navigate to `http://127.0.0.1:8080` (or use Back button twice)

**Expected Path Display**: `/Users/nikolayk/github/wile/tmp_test`

**Expected Items**:
- Same as Step 1

---

### Step 5: Navigate to folder2
**Action**: Double-click on "folder2"

**Expected Path Display**: `/Users/nikolayk/github/wile/tmp_test/folder2`

**Expected Items**:
- 📁 subfolder2
- 📄 file2.txt
- 🖼️ screenshot_subfolder2.png

**Actions**:
- Take screenshot: `screenshot_folder2.png`

**UI Elements**:
- Back button: VISIBLE
- Selection count: "No items selected"

---

### Step 6: Navigate to subfolder2
**Action**: Double-click on "subfolder2"

**Expected Path Display**: `/Users/nikolayk/github/wile/tmp_test/folder2/subfolder2`

**Expected Items**:
- 📄 another_deep.txt
- 🖼️ screenshot_folder1.png

**Actions**:
- Take screenshot: `screenshot_subfolder2.png`

**UI Elements**:
- Back button: VISIBLE
- Selection count: "No items selected"

---

## Key UI Elements to Verify

### Navigation
- ✅ Double-click on folders navigates into them
- ✅ Path display updates correctly
- ✅ Back button appears when not at root
- ✅ Back button hidden at root level

### File Display
- ✅ Folders displayed first (yellow folder icon)
- ✅ Files displayed after divider (blue file icon)
- ✅ Images have green icon (🖼️)
- ✅ Modified dates shown in dd/mm/yy format
- ✅ Delete button (red trash icon) on each item

### Operations
- ✅ Copy/Cut/Paste buttons present
- ✅ Selection counter displays correctly
- ✅ Tab system functional
- ✅ Add tab button (+) visible

## Playwright Automation Notes

### Selectors Used
- Text-based selector for folders: `text=folder1`, `text=subfolder1`, etc.
- Double-click action: `page.dblclick('text=folder1')`
- Screenshot capture: `page.screenshot(path='filename.png')`

### Wait Strategy
- `page.wait_for_load_state('networkidle')` after navigation
- Additional 1-second sleep for UI stability

### Navigation Pattern
```python
# Navigate to folder
page.dblclick('text=folder_name')
page.wait_for_load_state('networkidle')
time.sleep(1)

# Take screenshot
page.screenshot(path='screenshot_name.png')
```

## Test Execution Summary

**Server Command**: `./file-browser -path tmp_test -write`

**Server URL**: `http://127.0.0.1:8080`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_browser.py`

**Total Screenshots**: 5
- screenshot_root.png (now in folder1)
- screenshot_folder1.png (now in folder2/subfolder2)
- screenshot_folder2.png (now in folder3)
- screenshot_subfolder1.png (now in folder1/subfolder1)
- screenshot_subfolder2.png (now in folder2)

**Test Result**: ✅ All navigation steps successful

---

## File Upload Test

### Test Script
**File**: `test_upload.py`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_upload.py`

### Test Steps

1. **Check dropzone exists**
   - Verify upload dropzone element `#uploadDropzone` is present
   - Verify dropzone is visible

2. **Simulate file drag-and-drop**
   - Create temporary test file: `test_upload.txt`
   - Content: "This is a test file for upload verification"
   - Simulate drag-and-drop by:
     - Creating hidden file input
     - Setting file to input
     - Dispatching drop event with DataTransfer API

3. **Wait for upload completion**
   - Sleep 3 seconds for upload to complete
   - Server logs should show:
     ```
     Upload completed - ID: [upload_id], Filename: test_upload.txt, TargetPath:
     Moving from uploads/[upload_id] to /path/test_upload.txt
     Successfully moved uploaded file to /path/test_upload.txt
     ```

4. **Verify file appears in list**
   - Reload page
   - Check page content contains `test_upload.txt`

5. **Take screenshot**
   - Save to `upload_test.png`

### Expected Server Logs

**On startup**:
```
Uploads directory already exists: ./uploads
TUS upload handler initialized successfully
```

**During upload**:
```
Upload completed - ID: 09956df373e399b883c52dcb2f06fde0, Filename: test_upload.txt, TargetPath:
Moving from uploads/09956df373e399b883c52dcb2f06fde0 to /Users/nikolayk/github/wile/tmp_test/test_upload.txt
Successfully moved uploaded file to /Users/nikolayk/github/wile/tmp_test/test_upload.txt
```

### Test Result
✅ Upload test passed
- File successfully uploaded via drag-and-drop
- File appears in file list after upload
- Server logging shows complete upload flow

### Notes
- Requires `--write` flag for upload functionality
- Dropzone automatically hidden in read-only mode
- Upload uses TUS protocol for resumable uploads
- Files stored temporarily in `./uploads/` then moved to target location

---

## File Download Test

### Test Script
**File**: `test_download.py`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_download.py`

### Test Steps

1. **Check download handler exists**
   - Verify file element `[data-path="test1.txt"]` has `ondblclick` attribute
   - Verify ondblclick contains: `window.location.href='/file?path=...'`

2. **Test double-click behavior**
   - Double-click on test1.txt
   - Browser triggers download via `/file?path=test1.txt` endpoint

3. **Take screenshot**
   - Save to `test_download.png`

### Expected Behavior

**Double-click on any file (.txt, .pdf, etc.)**:
- Browser navigates to `/file?path=<filename>`
- Server responds with file download
- File downloaded to browser's default download folder

### Notes
- Double-click works for all non-image, non-document files
- Images open in lightbox on double-click
- Office documents open in doc viewer on double-click
- Single-click still selects files for copy/cut operations

### Test Result
✓ Download handler properly configured
- ondblclick attribute: `window.location.href='/file?path=...'`
- Server endpoint: `/file` (handleFileStream in main.go)

---

## Column Headers Test

### Test Script
**File**: `test_header.py`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_header.py`

### Test Steps

1. **Load page**
   - Navigate to `http://localhost:3000`
   - Wait for network idle state

2. **Verify column headers exist**
   - Check for Name button with sort icon
   - Check for Modified button with sort icon
   - Verify headers are aligned with file items

3. **Take screenshot**
   - Save to `test_header.png`

### Expected Elements

**Column Headers**:
- Name button (clickable, with sort icon)
- Modified button (clickable, with sort icon)
- Empty column for delete buttons (36px width)

**Grid Layout**: `grid-cols-[1fr_auto_auto]`
- Matches file item layout for perfect alignment

### Test Result
✅ Column headers properly displayed and aligned

---

## Sorting Functionality Test

### Test Script
**File**: `test_sorting.py`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_sorting.py`

### Test Steps

1. **Initial page load**
   - Default sort: name asc
   - Console log: `Sort: name asc`

2. **Click Name button (toggle to desc)**
   - Expected: name desc
   - Console log: `New sort: name desc`

3. **Click Name button again (toggle to asc)**
   - Expected: name asc
   - Console log: `New sort: name asc`

4. **Click Modified button (switch to modified asc)**
   - Expected: modified asc
   - Console log: `New sort: modified asc`

5. **Click Modified button again (toggle to desc)**
   - Expected: modified desc
   - Console log: `New sort: modified desc`

6. **Take screenshot**
   - Save to `test_sorting.png`

### Expected Behavior

**Sort Toggling**:
- Clicking same column toggles asc/desc
- Clicking different column switches to that column with asc default
- Server receives sortBy and dir parameters in WebSocket request

**Console Logs**:
- Initial: `Requesting path: ID: 1 Sort: name asc`
- After operations: 5 total requests with correct sort parameters

**Sorting Order**:
- Folders always sorted separately from files
- Within each group, items sorted by selected column and direction

### Test Result
✅ Sorting functionality working correctly
- All 5 sort operations executed successfully
- Console logs show correct sort parameters
- Server receives and processes sort requests

---

## Tab-Specific Sort State Test

### Test Script
**File**: `test_tab_sorting.py`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_tab_sorting.py`

### Test Steps

1. **Tab 1 - Initial state**
   - Starts with default sort: name asc

2. **Tab 1 - Change to Modified desc**
   - Click Modified button (→ modified asc)
   - Click Modified button again (→ modified desc)

3. **Create Tab 2**
   - Click + button
   - Tab 2 inherits current sort: modified desc

4. **Tab 2 - Change to Name desc**
   - Click Name button twice (→ name desc)

5. **Switch to Tab 1**
   - Verify sort restored: modified desc
   - Console: `Requesting path: ID: 7 Sort: modified desc`

6. **Switch to Tab 2**
   - Verify sort preserved: name desc
   - Console: `Requesting path: ID: 8 Sort: name desc`

7. **Switch back to Tab 1 (final check)**
   - Verify sort still: modified desc
   - Console: `Requesting path: ID: 9 Sort: modified desc`

8. **Take screenshot**
   - Save to `test_tab_sorting.png`

### Expected Behavior

**Per-Tab Sort State**:
- Each tab maintains its own sortBy and dir settings
- Switching tabs restores that tab's sort state
- New tabs inherit current sort state

**TabState Structure**:
```javascript
class TabState {
    sortBy: 'name'  // or 'modified'
    sortDir: 'asc'  // or 'desc'
}
```

**Functions Updated**:
- `saveCurrentStateToTab()` - Saves sort state when leaving tab
- `clearAndLoadTabState()` - Restores sort state when entering tab
- `createTab()` - Initializes new tab with current sort state

### Test Result
✅ Sort state successfully preserved per tab
- Modified desc requests: 5 (Tab 1)
- Name desc requests: (Tab 2)
- Each tab maintains independent sort settings

---

## Copy and Cut Operations Test

### Test Script
**File**: `test_copy_cut.py`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_copy_cut.py`

### Test Steps

**Part 1 - Copy Operation:**
1. **Select test1.txt**
   - Single click on test1.txt
   - Verify selection count: "1 item selected"

2. **Click Copy button**
   - Copy button should be enabled
   - Notification: "1 item copied"

3. **Navigate to folder3**
   - Double-click folder3
   - Verify path contains "folder3"

4. **Click Paste button**
   - Paste button should be enabled
   - Wait for operation to complete
   - Verify test1.txt appears in folder3

**Part 2 - Cut Operation:**
5. **Navigate back to root**
   - Load root path

6. **Select test2.txt**
   - Single click on test2.txt
   - Verify selection count: "1 item selected"

7. **Click Cut button**
   - Cut button should be enabled
   - Notification: "1 item cut"

8. **Navigate to folder2**
   - Double-click folder2

9. **Click Paste button**
   - File moved from root to folder2

10. **Verify test2.txt removed from root**
    - Navigate back to root
    - test2.txt should not be present

### Expected Behavior

**Copy Operation**:
- File copied to destination
- Source file remains in original location
- Copy/Cut clipboard cleared after paste

**Cut Operation**:
- File moved to destination
- Source file removed from original location
- Move operation uses server's "paste" action

**Server Endpoints**:
- `/manage?action=copy&srcs=...&dest=...`
- `/manage?action=paste&srcs=...&dest=...`

### Test Result
✅ Copy and cut operations working correctly
- Copy: File duplicated successfully
- Cut: File moved successfully
- Source removed after cut operation

---

## Icons Display Test

### Test Script
**File**: `test_icons.py`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_icons.py`

### Test Steps

1. **Load page**
   - Navigate to file browser
   - Wait for content to load

2. **Verify page content**
   - Check folder1 and test1.txt exist in HTML

3. **Verify ICONS constant**
   - Check JavaScript ICONS object is defined
   - Count number of icons

4. **Take screenshot**
   - Save to `test_icons.png`

### Expected Behavior

**ICONS Constant**:
```javascript
const ICONS = {
    back, copy, cut, paste, delete,
    image, document, file, folder,
    notification
}
```

**Icon Usage**:
- Folder icon (yellow)
- File icon (blue)
- Image icon (green)
- Document icon (purple)
- Delete icon (red trash)
- Operation buttons (copy/cut/paste)

### Test Result
✅ ICONS constant properly defined
- All SVG icons loaded
- Icons used throughout UI
- Consistent visual representation

---

## Lightbox Navigation Test

### Test Script
**File**: `test_lightbox_navigation.py`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_lightbox_navigation.py`

### Test Steps

1. **Open first image**
   - Double-click test_image_1.png
   - Lightbox should open

2. **Test NEXT button (3 times)**
   - Click Next button
   - Should cycle through images: 1 → 2 → 3 → ...

3. **Test PREV button (2 times)**
   - Click Prev button
   - Should go backward through images

4. **Test wrap-around forward**
   - Navigate to last image
   - Click Next
   - Should wrap to first image

5. **Test wrap-around backward**
   - At first image
   - Click Prev
   - Should wrap to last image

6. **Take screenshot**
   - Save to `lightbox_test.png`

### Expected Behavior

**Lightbox Features**:
- Opens on double-click of image
- Next/Prev buttons visible
- Smooth navigation between images
- Wrap-around at boundaries

**Navigation Handler**:
```javascript
function findImageElement(currentHref, direction) {
    // direction: 1 (next) or -1 (prev)
    // Finds next/prev image in DOM
    // Wraps around at boundaries
}
```

**Implementation**:
- Uses GLightbox library
- Custom navigation handler
- Searches DOM for image elements
- Maintains cyclic order

### Test Result
✅ Lightbox navigation working correctly
- Forward navigation: WORKING
- Backward navigation: WORKING
- Wrap-around (both directions): WORKING

---

## Lightbox with 3 Images Test

### Test Script
**File**: `test_lightbox_3images.py`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_lightbox_3images.py`

### Test Steps

1. **Open test_image_1.png (red)**
   - Double-click
   - Lightbox opens showing red image

2. **Click Next → test_image_2.png (blue)**
   - Navigate to second image

3. **Click Next → test_image_3.png (green)**
   - Navigate to third image

4. **Click Next → wrap to test_image_1.png (red)**
   - Wrap forward to first image

5. **Click Prev → wrap to test_image_3.png (green)**
   - Wrap backward to last image

6. **Take screenshot**
   - Save to `lightbox_3images_test.png`

### Expected Behavior

**Image Sequence**:
- Image 1: Red (400x400)
- Image 2: Blue (400x400)
- Image 3: Green (400x400)

**Navigation Pattern**:
- Forward: 1 → 2 → 3 → 1 (wrap)
- Backward: 1 → 3 (wrap) → 2 → 1

**Visual Feedback**:
- Clear color changes confirm navigation
- Next/Prev buttons always visible
- Smooth transitions

### Test Result
✅ Lightbox navigation with 3 images working
- All 3 images accessible
- Forward wrap-around: WORKING
- Backward wrap-around: WORKING
- Color verification: PASSED

---

## Deep Navigation Test

### Test Script
**File**: `test_deep_navigation.py`

**Playwright Command**: `/Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_deep_navigation.py`

### Test Steps

1. **Load root**
   - Start at root level
   - Track WebSocket connections

2. **Navigate 5 levels deep**
   - folder1 → subfolder1 → deep1 → deep2 → deep3
   - Each navigation uses same WebSocket

3. **Navigate back 5 levels**
   - Use Back button 5 times
   - Return to root

4. **Jump to different branch**
   - folder2 → subfolder2
   - Test cross-branch navigation

5. **Navigate back to root**
   - Use Back button twice

### Expected Behavior

**WebSocket Reuse**:
- Single WebSocket connection for entire session
- All navigation uses `requestPath()` without reconnecting
- Request ID increments for each path request

**Console Logs**:
```
🔌 WebSocket connected
📂 Requesting: /
📂 Requesting: folder1
📂 Requesting: folder1/subfolder1
📂 Requesting: folder1/subfolder1/deep1
📂 Requesting: folder1/subfolder1/deep1/deep2
📂 Requesting: folder1/subfolder1/deep1/deep2/deep3
... (back navigation)
📂 Requesting: folder2
📂 Requesting: folder2/subfolder2
```

**Verification**:
- Exactly 1 WebSocket connection
- Zero disconnections
- ~13 path requests total
- Stale message detection working

### Test Result
✅ Deep navigation working correctly
- Single WebSocket connection maintained
- All 13+ navigation requests successful
- No reconnections during session
- Back button works at all levels
- Cross-branch navigation works

---

## Test Suite Summary

### All Tests

| Test File | Purpose | Status |
|-----------|---------|--------|
| test_browser.py | Basic navigation through folders | ✅ |
| test_upload.py | File upload via drag-and-drop | ✅ |
| test_download.py | File download on double-click | ✅ |
| test_copy_cut.py | Copy and cut operations | ✅ |
| test_icons.py | Icon constants and display | ✅ |
| test_lightbox_navigation.py | Lightbox image navigation | ✅ |
| test_lightbox_3images.py | Lightbox with 3 test images | ✅ |
| test_deep_navigation.py | Deep folder navigation | ✅ |
| test_header.py | Column headers display | ✅ |
| test_sorting.py | Sorting functionality | ✅ |
| test_tab_sorting.py | Per-tab sort state | ✅ |

### Running All Tests

**From project root:**
```bash
# Setup environment
./tests/setup_test_env.sh

# Build and start server
go build -o file-browser && ./file-browser -port 3000 -path tmp_test -write

# Run all tests
cd tests
for test in test_*.py; do
    echo "Running $test..."
    /Users/nikolayk/opt/miniconda3/envs/playwright/bin/python "$test"
done
```

**From tests directory:**
```bash
# Setup environment (creates tmp_test in parent directory)
./setup_test_env.sh

# Build and start server (from parent directory)
cd ..
go build -o file-browser && ./file-browser -port 3000 -path tmp_test -write

# Run all tests (from tests directory)
cd tests
for test in test_*.py; do
    echo "Running $test..."
    /Users/nikolayk/opt/miniconda3/envs/playwright/bin/python "$test"
done
```
