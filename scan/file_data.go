package scan

import (
	"os"
	"path/filepath"
)

type FileData struct {
	Parent     *FileData   `json:"-"` // Don't serialize parent to avoid cycles
	Dir        string      `json:"dir"`
	Info       os.FileInfo `json:"-"` // Don't serialize os.FileInfo
	CachedSize int64       `json:"size"`
	Children   []*FileData `json:"children,omitempty"`
}

func newRootFileData(dir string) *FileData {
	return &FileData{Dir: dir, CachedSize: 0}
}

func newFileData(parent *FileData, file os.FileInfo) *FileData {
	var size int64 = -1
	if !file.IsDir() {
		size = file.Size()
	}
	// Store full path in Dir field (parent path + filename)
	fullPath := filepath.Join(parent.Path(), file.Name())
	return &FileData{Parent: parent, Dir: fullPath, Info: file, CachedSize: size}
}

func (d FileData) Root() bool {
	return d.Info == nil
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
	if d.Info != nil {
		s += d.Info.Size()
	}
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

// FindByPath recursively searches for a node with the given path
func (d *FileData) FindByPath(targetPath string) *FileData {
	if d.Path() == targetPath {
		return d
	}
	for _, child := range d.Children {
		if found := child.FindByPath(targetPath); found != nil {
			return found
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
