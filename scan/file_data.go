package scan

import (
	"path/filepath"
	"strings"
)

type FileData struct {
	Parent     *FileData   `json:"-"` // Don't serialize parent to avoid cycles
	Dir        string      `json:"dir"`
	IsDir      bool        `json:"isDir"`
	IsLink     bool        `json:"isLink"`
	CachedSize int64       `json:"size"`
	Children   []*FileData `json:"children,omitempty"`
}

func newRootFileData(dir string) *FileData {
	return &FileData{Dir: dir, IsDir: true, CachedSize: 0}
}

func newFileData(parent *FileData, name string, isDir bool, isLink bool, size int64) *FileData {
	fullPath := filepath.Join(parent.Path(), name)
	return &FileData{
		Parent:     parent,
		Dir:        fullPath,
		IsDir:      isDir,
		IsLink:     isLink,
		CachedSize: size,
	}
}

func (d FileData) Root() bool {
	return d.Parent == nil
}

func (d FileData) Path() string {
	// Dir now contains the full path
	return d.Dir
}

func (d *FileData) Size() int64 {
	if d.CachedSize != -1 {
		return d.CachedSize
	}

	var s int64
	for _, f := range d.Children {
		s += f.Size()
	}
	d.CachedSize = s
	return s
}

// UpdateParentSizes updates all parent sizes by the given delta
// delta can be positive (add) or negative (subtract)
func (d *FileData) UpdateParentSizes(delta int64) {
	parent := d.Parent
	for parent != nil {
		parent.CachedSize += delta
		parent = parent.Parent
	}
}

// FindByPath efficiently searches for a node with the given path.
// Optimized to O(depth) instead of O(total files) by only descending into
// children that are on the path to the target.
func (d *FileData) FindByPath(targetPath string) *FileData {
	if d.Path() == targetPath {
		return d
	}

	// Only recurse into child if it's on the path to target
	// We append "/" to both paths to ensure exact path component matching:
	// - "/tmp/test/" is a prefix of "/tmp/test/folder/" ✓
	// - "/tmp/test/" is NOT a prefix of "/tmp/test123/" ✗
	for _, child := range d.Children {
		if strings.HasPrefix(targetPath+"/", child.Path()+"/") {
			return child.FindByPath(targetPath)
		}
	}
	return nil
}

// RemoveChild removes a child from this node's Children slice
func (d *FileData) RemoveChild(child *FileData) {
	for i, c := range d.Children {
		if c == child {
			d.Children = append(d.Children[:i], d.Children[i+1:]...)
			return
		}
	}
}

// RebuildParentPointers recursively rebuilds Parent pointers after JSON deserialization
func (d *FileData) RebuildParentPointers(parent *FileData) {
	d.Parent = parent
	for _, child := range d.Children {
		child.RebuildParentPointers(d)
	}
}
