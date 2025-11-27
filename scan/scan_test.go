package scan

import (
	"os"
	"path/filepath"
	"testing"
)

func TestScanDirConcurrent(t *testing.T) {
	// Create a temporary test directory structure
	tmpDir := t.TempDir()

	// Create test files and directories
	testFile1 := filepath.Join(tmpDir, "file1.txt")
	testFile2 := filepath.Join(tmpDir, "file2.txt")
	testDir := filepath.Join(tmpDir, "subdir")
	testFile3 := filepath.Join(testDir, "file3.txt")

	// Write some data to files
	if err := os.WriteFile(testFile1, []byte("hello"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(testFile2, []byte("world!"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(testDir, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(testFile3, []byte("test"), 0644); err != nil {
		t.Fatal(err)
	}

	// Scan the directory
	children, err := ScanDirConcurrent(tmpDir, 0, nil)
	if err != nil {
		t.Fatalf("ScanDirConcurrent failed: %v", err)
	}

	// Should have 3 items (2 files + 1 dir)
	if len(children) != 3 {
		t.Errorf("Expected 3 children, got %d", len(children))
	}

	// Find the subdir and check its size
	var subdir *FileData
	for _, child := range children {
		if child.IsDir && filepath.Base(child.Dir) == "subdir" {
			subdir = child
			break
		}
	}

	if subdir == nil {
		t.Fatal("Could not find subdir in children")
	}

	// Check that subdir has the file
	if len(subdir.Children) != 1 {
		t.Errorf("Expected subdir to have 1 child, got %d", len(subdir.Children))
	}

	// Check cumulative size calculation
	subdirSize := subdir.Size()
	expectedSize := int64(4) // "test" = 4 bytes

	if subdirSize < expectedSize {
		t.Errorf("Expected subdir size to be at least %d, got %d", expectedSize, subdirSize)
	}
}

func TestToHumanSize(t *testing.T) {
	tests := []struct {
		input    int64
		expected string
	}{
		{-1, "-"},
		{0, "0  B"},
		{500, "500  B"},
		{1024, "1.00 KB"},
		{1536, "1.50 KB"},
		{1048576, "1.00 MB"},
		{1073741824, "1.00 GB"},
		{1099511627776, "1.00 TB"},
	}

	for _, test := range tests {
		result := ToHumanSize(test.input)
		if result != test.expected {
			t.Errorf("ToHumanSize(%d) = %s, expected %s", test.input, result, test.expected)
		}
	}
}

func TestFileDataSize(t *testing.T) {
	// Create a temporary test directory
	tmpDir := t.TempDir()

	// Create some test files
	file1 := filepath.Join(tmpDir, "file1.txt")
	file2 := filepath.Join(tmpDir, "file2.txt")

	content1 := []byte("hello world") // 11 bytes
	content2 := []byte("test")        // 4 bytes

	if err := os.WriteFile(file1, content1, 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(file2, content2, 0644); err != nil {
		t.Fatal(err)
	}

	// Scan the directory
	children, err := ScanDirConcurrent(tmpDir, 1, nil)
	if err != nil {
		t.Fatalf("ScanDirConcurrent failed: %v", err)
	}

	// Calculate total size
	var totalSize int64
	for _, child := range children {
		totalSize += child.Size()
	}

	expectedSize := int64(15) // 11 + 4
	if totalSize != expectedSize {
		t.Errorf("Expected total size %d, got %d", expectedSize, totalSize)
	}
}
