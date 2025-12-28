#!/bin/bash
# Setup script for wile test environment
# Creates test folder structure and all necessary test images

set -e  # Exit on error

echo "======================================"
echo "Setting up wile test environment"
echo "======================================"
echo

# Go to project root (parent of tests directory)
cd "$(dirname "$0")/.."

# Clean up existing test folder if it exists
if [ -d "tmp_test" ]; then
    echo "Removing existing tmp_test folder..."
    rm -rf tmp_test
fi

# Create folder structure
echo "Creating folder structure..."
mkdir -p tmp_test/folder1/subfolder1/deep1/deep2/deep3
mkdir -p tmp_test/folder2/subfolder2
mkdir -p tmp_test/folder3
mkdir -p "tmp_test/folder with spaces"
mkdir -p "tmp_test/folder with spaces/sub folder"

echo "✓ Folders created"

# Create text files
echo "Creating text files..."
echo "This is test file 1" > tmp_test/test1.txt
echo "This is test file 2" > tmp_test/test2.txt
echo "File in folder 1" > tmp_test/folder1/file1.txt
echo "File in folder 2" > tmp_test/folder2/file2.txt
echo "File in folder 3" > tmp_test/folder3/file3.txt
echo "Deep file content" > tmp_test/folder1/subfolder1/deep_file.txt
echo "Another deep file" > tmp_test/folder2/subfolder2/another_deep.txt
echo "Deep level 1" > tmp_test/folder1/subfolder1/deep1/file_deep1.txt
echo "Deep level 2" > tmp_test/folder1/subfolder1/deep1/deep2/file_deep2.txt
echo "Deep level 3" > tmp_test/folder1/subfolder1/deep1/deep2/deep3/file_deep3.txt
echo "File with spaces content" > "tmp_test/folder with spaces/file with spaces.txt"
echo "Another spaced file" > "tmp_test/folder with spaces/sub folder/nested file.txt"

echo "✓ Text files created"

# Create test images using ImageMagick (if available) or Python
echo "Creating test images..."

if command -v convert &> /dev/null; then
    # Using ImageMagick
    echo "Using ImageMagick to create images..."

    # Red image 400x400
    convert -size 400x400 xc:red tmp_test/test_image_1.png

    # Blue image 400x400
    convert -size 400x400 xc:blue tmp_test/test_image_2.png

    # Green image 400x400
    convert -size 400x400 xc:green tmp_test/test_image_3.png

    # Additional test images for navigation
    convert -size 300x300 xc:yellow tmp_test/folder1/screenshot_root.png
    convert -size 300x300 xc:cyan tmp_test/folder1/subfolder1/screenshot_subfolder1.png
    convert -size 300x300 xc:magenta tmp_test/folder2/screenshot_subfolder2.png
    convert -size 300x300 xc:orange tmp_test/folder2/subfolder2/screenshot_folder1.png
    convert -size 300x300 xc:purple tmp_test/folder3/screenshot_folder2.png

    echo "✓ Images created with ImageMagick"

elif command -v /Users/nikolayk/opt/miniconda3/envs/playwright/bin/python &> /dev/null; then
    # Using Python PIL
    echo "Using Python PIL to create images..."
    /Users/nikolayk/opt/miniconda3/envs/playwright/bin/python -c "
from PIL import Image
import os

# Create test images directory
os.makedirs('tmp_test', exist_ok=True)

# Create colored images
colors = {
    'tmp_test/test_image_1.png': (255, 0, 0),      # Red
    'tmp_test/test_image_2.png': (0, 0, 255),      # Blue
    'tmp_test/test_image_3.png': (0, 255, 0),      # Green
    'tmp_test/folder1/screenshot_root.png': (255, 255, 0),  # Yellow
    'tmp_test/folder1/subfolder1/screenshot_subfolder1.png': (0, 255, 255),  # Cyan
    'tmp_test/folder2/screenshot_subfolder2.png': (255, 0, 255),  # Magenta
    'tmp_test/folder2/subfolder2/screenshot_folder1.png': (255, 165, 0),  # Orange
    'tmp_test/folder3/screenshot_folder2.png': (128, 0, 128),  # Purple
}

for path, color in colors.items():
    size = (400, 400) if 'test_image' in path else (300, 300)
    img = Image.new('RGB', size, color)
    img.save(path)
    print('Created {}'.format(path))
"
    echo "✓ Images created with Python PIL"

else
    echo "⚠ Warning: Neither ImageMagick nor Python PIL available"
    echo "  Please install one of them to create test images:"
    echo "    brew install imagemagick"
    echo "    OR"
    echo "    pip3 install Pillow"
    exit 1
fi

# Verify structure
echo
echo "======================================"
echo "Verification"
echo "======================================"
echo

# Count folders
folder_count=$(find tmp_test -type d | wc -l | tr -d ' ')
echo "Folders created: $folder_count"

# Count text files
txt_count=$(find tmp_test -name "*.txt" | wc -l | tr -d ' ')
echo "Text files created: $txt_count"

# Count image files
img_count=$(find tmp_test -name "*.png" | wc -l | tr -d ' ')
echo "Image files created: $img_count"

echo
echo "======================================"
echo "Test environment ready!"
echo "======================================"
echo
echo "To run the server (from project root):"
echo "  go build -o file-browser && ./file-browser -port 3000 -path tmp_test -write"
echo
echo "To run tests (from project root):"
echo "  /Users/nikolayk/opt/miniconda3/envs/playwright/bin/python tests/test_<name>.py"
echo
echo "Or run from tests directory:"
echo "  cd tests"
echo "  /Users/nikolayk/opt/miniconda3/envs/playwright/bin/python test_<name>.py"
echo
