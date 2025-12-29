package scan

import (
	"path/filepath"
	"strings"

	"github.com/google/uuid"
)

type FileData struct {
	ID       string      `json:"id"`
	Name     string      `json:"name"`
	Parent   *FileData   `json:"-"` // Don't serialize parent to avoid cycles
	Children []*FileData `json:"children,omitempty"`

	// Metadata
	IsDir  bool `json:"isDir"`
	IsLink bool `json:"isLink"`

	CachedSize int64 `json:"size"`
	Modified   int64 `json:"modified"`

	// Root specific
	RootPath string `json:"-"`
}

func newRootFileData(dir string) *FileData {
	return &FileData{
		ID:         uuid.New().String(),
		Name:       filepath.Base(dir),
		IsDir:      true,
		CachedSize: 0,
		Modified:   0, // Root doesn't really have a modified time usually, or set to now
		RootPath:   dir,
	}
}

func newFileData(parent *FileData, name string, isDir bool, isLink bool, size int64, modified int64) *FileData {
	return &FileData{
		ID:         uuid.New().String(),
		Name:       name,
		Parent:     parent,
		IsDir:      isDir,
		IsLink:     isLink,
		CachedSize: size,
		Modified:   modified,
	}
}

func (d FileData) Root() bool {
	return d.Parent == nil
}

// Path returns the absolute path dynamically derived from the tree
func (d FileData) Path() string {
	if d.Root() {
		return d.RootPath
	}
	return filepath.Join(d.Parent.Path(), d.Name)
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
func (d *FileData) FindByPath(targetPath string) *FileData {
	myPath := d.Path()
	if myPath == targetPath {
		return d
	}

	// Clean paths to ensure consistent comparison
	targetPath = filepath.Clean(targetPath)
	myPath = filepath.Clean(myPath)

	// If I am not a prefix of target, then target is not in my subtree
	if !strings.HasPrefix(targetPath, myPath) {
		return nil
	}

	// This assumes standard path separator '/' or '\'
	// Extract the relative path part
	relPath := ""
	if myPath == "/" || myPath == "\\" || strings.HasSuffix(myPath, string(filepath.Separator)) {
		relPath = strings.TrimPrefix(targetPath, myPath)
	} else {
		relPath = strings.TrimPrefix(targetPath, myPath+string(filepath.Separator))
	}

	// Get the first component of the relative path
	parts := strings.Split(relPath, string(filepath.Separator))
	if len(parts) == 0 {
		return nil
	}
	nextName := parts[0]

	for _, child := range d.Children {
		if child.Name == nextName {
			if len(parts) == 1 {
				return child
			}
			return child.FindByPath(targetPath)
		}
	}
	return nil
}

// FindByID recursively searches for a node with the given ID
func (d *FileData) FindByID(id string) *FileData {
	if d.ID == id {
		return d
	}
	for _, child := range d.Children {
		if found := child.FindByID(id); found != nil {
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
