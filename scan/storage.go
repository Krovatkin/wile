package scan

import (
	"bytes"
	"encoding/gob"
)

// StoredFileData is a serializable version of FileData without pointers
type StoredFileData struct {
	ID       string
	Name     string
	IsDir    bool
	IsLink   bool
	Size     int64
	Modified int64
	ParentID string   // Reference to parent
	ChildIDs []string // References to children
	RootPath string   // Only for root node
}

// ToStored converts FileData to a serializable format
func (f *FileData) ToStored() *StoredFileData {
	childIDs := make([]string, len(f.Children))
	for i, child := range f.Children {
		childIDs[i] = child.ID
	}

	parentID := ""
	if f.Parent != nil {
		parentID = f.Parent.ID
	}

	return &StoredFileData{
		ID:       f.ID,
		Name:     f.Name,
		IsDir:    f.IsDir,
		IsLink:   f.IsLink,
		Size:     f.CachedSize,
		Modified: f.Modified,
		ParentID: parentID,
		ChildIDs: childIDs,
		RootPath: f.RootPath,
	}
}

// Serialize encodes StoredFileData using gob
func (s *StoredFileData) Serialize() ([]byte, error) {
	var buf bytes.Buffer
	enc := gob.NewEncoder(&buf)
	if err := enc.Encode(s); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// Deserialize decodes StoredFileData from gob
func (s *StoredFileData) Deserialize(data []byte) error {
	dec := gob.NewDecoder(bytes.NewReader(data))
	return dec.Decode(s)
}

// LoadTreeFromStored reconstructs the full FileData tree from a map of stored nodes
// This rebuilds parent pointers and children pointers based on IDs
func LoadTreeFromStored(storedNodes map[string]*StoredFileData, rootPath string) (*FileData, error) {
	// First pass: Create all nodes without relationships
	allNodes := make(map[string]*FileData)
	var root *FileData

	// Helper to find root from stored data if possible
	for id, stored := range storedNodes {
		node := &FileData{
			ID:         stored.ID,
			Name:       stored.Name,
			IsDir:      stored.IsDir,
			IsLink:     stored.IsLink,
			CachedSize: stored.Size,
			Modified:   stored.Modified,
			Children:   []*FileData{},
			RootPath:   stored.RootPath,
		}
		allNodes[id] = node

		// If this looks like the root (no parent ID or matching root path request)
		// Note: The caller passes rootPath, but checking if RootPath is set in stored data is safer for identity
		if stored.RootPath != "" {
			root = node
		}
	}

	// Fallback/Safety: If we didn't identify root by RootPath property, try to find the one with matching path
	// This part is tricky because we don't know the paths yet.
	// But we know root has NO parent.
	if root == nil {
		for _, stored := range storedNodes {
			if stored.ParentID == "" {
				root = allNodes[stored.ID]
				// Ensure its root path is set if mismatched
				if root.RootPath == "" {
					root.RootPath = rootPath
				}
				break
			}
		}
	}

	if root == nil {
		// New graph or corrupted DB -> Start fresh
		return nil, nil // Return nil, nil to trigger rebuild in caller
	}

	// Second pass: Build relationships
	for id, stored := range storedNodes {
		node := allNodes[id]

		// Connect children
		for _, childID := range stored.ChildIDs {
			if child := allNodes[childID]; child != nil {
				child.Parent = node
				node.Children = append(node.Children, child)
			}
		}

		// Integrity check: stored.ParentID should match node.Parent.ID if set
		// (The child loop above sets the pointers, so this is implicitly handled)
	}

	return root, nil
}
