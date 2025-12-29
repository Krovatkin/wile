package scan

import (
	"path/filepath"
	"testing"
)

func TestPathReconstruction(t *testing.T) {
	root := newRootFileData("/root")
	child1 := newFileData(root, "folder1", true, false, 0)
	root.Children = append(root.Children, child1)

	child2 := newFileData(child1, "file2.txt", false, false, 100)
	child1.Children = append(child1.Children, child2)

	// Verify paths
	if root.Path() != "/root" {
		t.Errorf("Root path mismatch: got %s, want /root", root.Path())
	}

	expectedChild1 := filepath.Join("/root", "folder1")
	if child1.Path() != expectedChild1 {
		t.Errorf("Child1 path mismatch: got %s, want %s", child1.Path(), expectedChild1)
	}

	expectedChild2 := filepath.Join(expectedChild1, "file2.txt")
	if child2.Path() != expectedChild2 {
		t.Errorf("Child2 path mismatch: got %s, want %s", child2.Path(), expectedChild2)
	}
}

func TestIDGeneration(t *testing.T) {
	root := newRootFileData("/root")
	if root.ID == "" {
		t.Error("Root ID is empty")
	}

	child := newFileData(root, "test", false, false, 0)
	if child.ID == "" {
		t.Error("Child ID is empty")
	}

	if root.ID == child.ID {
		t.Error("Root and Child IDs are identical")
	}
}

func TestFindByID(t *testing.T) {
	root := newRootFileData("/root")
	child1 := newFileData(root, "c1", true, false, 0)
	root.Children = append(root.Children, child1)

	child2 := newFileData(child1, "c2", false, false, 0)
	child1.Children = append(child1.Children, child2)

	// Find Root
	if found := root.FindByID(root.ID); found != root {
		t.Error("Failed to find root by ID")
	}

	// Find Leaf
	if found := root.FindByID(child2.ID); found != child2 {
		t.Error("Failed to find leaf by ID")
	}

	// Find Non-existent
	if found := root.FindByID("non-existent"); found != nil {
		t.Error("Found non-existent ID")
	}
}
