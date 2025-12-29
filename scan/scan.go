package scan

import (
	"io/fs"
	"os"
	"runtime"
	"sync"
)

func ScanDirConcurrent(dir string, concurrency int, spinner *ProgressSpinner) ([]*FileData, error) {
	root := newRootFileData(dir)

	if concurrency == 0 {
		concurrency = DefaultConcurrency()
	}

	ch := make(chan *FileData)
	closeWait := &sync.WaitGroup{}

	var wait sync.WaitGroup
	wait.Add(concurrency)
	for i := 0; i < concurrency; i++ {
		go func() {
			for file := range ch {
				scanDir(file, ch, closeWait, spinner)
				closeWait.Done()
				if spinner != nil {
					spinner.IncrementProcessed()
				}
			}
			wait.Done()
		}()
	}

	err := scanDir(root, ch, closeWait, spinner)
	if err != nil {
		return nil, err
	}

	go func() {
		closeWait.Wait()
		close(ch)
	}()

	wait.Wait()

	return root.Children, nil
}

func DefaultConcurrency() int {
	maxProcs := runtime.GOMAXPROCS(0)
	numCPU := runtime.NumCPU()
	if maxProcs < numCPU {
		return maxProcs
	}
	return numCPU
}

func scanDir(parent *FileData, ch chan *FileData, closeWait *sync.WaitGroup, spinner *ProgressSpinner) error {
	if !parent.IsDir || parent.IsLink {
		return nil
	}

	entries, err := os.ReadDir(parent.Path())
	if err != nil {
		return err
	}

	children := []*FileData{}
	closeWait.Add(len(entries))
	if spinner != nil {
		spinner.IncrementDiscovered(len(entries))
	}
	for _, entry := range entries {
		isDir := entry.IsDir()
		isLink := entry.Type()&fs.ModeSymlink != 0

		var size int64 = -1
		var modified int64 = 0

		if !isDir && !isLink {
			// Only stat regular files to get size
			info, err := entry.Info()
			if err != nil {
				closeWait.Done()
				continue
			}
			size = info.Size()
			modified = info.ModTime().Unix()
		} else {
			// For dirs/links, we might still want mod time if available cheaply
			info, err := entry.Info()
			if err == nil {
				modified = info.ModTime().Unix()
			}
		}

		f := newFileData(parent, entry.Name(), isDir, isLink, size, modified)
		go func() {
			ch <- f
		}()
		children = append(children, f)
	}

	parent.Children = children
	return nil
}
