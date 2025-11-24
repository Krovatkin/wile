package main

import (
	"archive/zip"
	"encoding/json"
	"flag"
	"fmt"
	"html/template"
	"io"
	"io/ioutil"
	"log"
	"net/url"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/adaptor"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/websocket/v2"
	"github.com/otiai10/copy"
	"github.com/tus/tusd/pkg/filestore"
	"github.com/tus/tusd/pkg/handler"

	"file-browser/scan"
)

func move(src, dst string) error {
	// Copy file OR directory to destination
	if err := copy.Copy(src, dst); err != nil {
		return err
	}

	// Remove source file OR directory after successful copy
	return os.RemoveAll(src)
}

type DocumentData struct {
	Title        string
	DocumentName string
	Content      template.HTML
}

type IndexData struct {
	WriteMode bool // Changed to WriteMode
	RootPath  string
}

// ModificationLogEntry represents a single file operation logged to JSONL
type ModificationLogEntry struct {
	Timestamp string   `json:"timestamp"`
	Action    string   `json:"action"`     // delete, copy, paste
	Sources   []string `json:"sources"`    // source file paths
	Dest      string   `json:"dest,omitempty"` // destination (empty for delete)
	Errors    []string `json:"errors,omitempty"` // errors if any
}

// logModification appends a file operation to modifications.jsonl
// NEVER overwrites the file, only appends
func logModification(action string, sources []string, dest string, errors []string) {
	logFilePath := filepath.Join(rootPath, "modifications.jsonl")

	// Open file with append mode - creates if doesn't exist, never overwrites
	f, err := os.OpenFile(logFilePath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("Failed to open modification log: %v", err)
		return
	}
	defer f.Close()

	entry := ModificationLogEntry{
		Timestamp: time.Now().Format(time.RFC3339),
		Action:    action,
		Sources:   sources,
		Dest:      dest,
		Errors:    errors,
	}

	data, err := json.Marshal(entry)
	if err != nil {
		log.Printf("Failed to marshal log entry: %v", err)
		return
	}

	// Write JSON + newline
	if _, err := f.Write(append(data, '\n')); err != nil {
		log.Printf("Failed to write log entry: %v", err)
	}
}

func handleManage(c *fiber.Ctx) error {
	// Track this operation for graceful shutdown
	fileOpsInProgress.Add(1)
	defer fileOpsInProgress.Done()

	// Add this check at the beginning
	if !writeMode {
		return c.Status(403).JSON(fiber.Map{
			"status": "error",
			"error":  "File operations are disabled. Use --write flag to enable write mode",
		})
	}

	// Get parameters
	sources := c.Query("srcs")
	action := c.Query("action")
	dest := c.Query("dest", "")

	if sources == "" || action == "" {
		return c.Status(400).JSON(fiber.Map{
			"status": "error",
			"error":  "Missing required parameters: srcs and action",
		})
	}

	// Parse sources (they come as multiple values with same key)
	query := string(c.Request().URI().QueryString())
	values, _ := url.ParseQuery(query)
	srcList := values["srcs"] // This returns []string
	if len(srcList) == 0 {
		return c.Status(400).JSON(fiber.Map{
			"status": "error",
			"error":  "No source files provided",
		})
	}

	// Validate action
	if action != "copy" && action != "paste" && action != "delete" {
		return c.Status(400).JSON(fiber.Map{
			"status": "error",
			"error":  "Invalid action. Must be 'copy' or 'paste'",
		})
	}

	// Build destination path
	if action != "delete" {
		// Build destination path
		destPath := filepath.Join(rootPath, dest)

		// Check if destination exists and is a directory
		destInfo, err := os.Stat(destPath)
		if err != nil {
			return c.Status(400).JSON(fiber.Map{
				"status": "error",
				"error":  "Destination path does not exist",
			})
		}

		if !destInfo.IsDir() {
			return c.Status(400).JSON(fiber.Map{
				"status": "error",
				"error":  "Destination must be a directory",
			})
		}
	}

	var errors []string

	// Process each source file
	for _, src := range srcList {
		srcPath := filepath.Join(rootPath, src)

		// Check if source exists
		srcInfo, err := os.Stat(srcPath)
		if err != nil {
			errors = append(errors, fmt.Sprintf("Failed to %s %s: source does not exist", action, src))
			continue
		}

		if action == "delete" {
			// Handle delete operation
			log.Printf("Would DELETE: %s", srcPath)

			// Get node and size BEFORE deleting from filesystem
			var nodeToDelete *scan.FileData
			var sizeToSubtract int64
			if withSizes && sizeTreeRoot != nil {
				sizeTreeMutex.RLock()
				nodeToDelete = sizeTreeRoot.FindByPath(srcPath)
				if nodeToDelete != nil {
					sizeToSubtract = nodeToDelete.Size()
				}
				sizeTreeMutex.RUnlock()
			}

			// Delete from filesystem (no lock held during I/O)
			err = os.RemoveAll(srcPath) // RemoveAll works for both files and directories
			if err != nil {
				errors = append(errors, fmt.Sprintf("Failed to delete %s: %v", src, err))
			} else if nodeToDelete != nil {
				// Update size tree after successful delete
				sizeTreeMutex.Lock()
				nodeToDelete.UpdateParentSizes(-sizeToSubtract) // Subtract from parent chain
				if nodeToDelete.Parent != nil {
					nodeToDelete.Parent.RemoveChild(nodeToDelete)
				}
				sizeTreeMutex.Unlock()
			}
		} else {
			// Handle copy/paste operations (existing code)
			destPath := filepath.Join(rootPath, dest)
			baseName := filepath.Base(srcPath)
			targetPath := filepath.Join(destPath, baseName)

			// Perform the operation
			if srcInfo.IsDir() {
				// Handle directory
				if action == "copy" {
					log.Printf("Would COPY DIR: %s -> %s", srcPath, targetPath)
					err = copy.Copy(srcPath, targetPath)
				} else { // paste (move)
					log.Printf("Would MOVE DIR: %s -> %s", srcPath, targetPath)
					err = move(srcPath, targetPath)
				}
			} else {
				// Handle file
				if action == "copy" {
					log.Printf("Would COPY FILE: %s -> %s", srcPath, targetPath)
					err = copy.Copy(srcPath, targetPath)
				} else { // paste (move)
					log.Printf("Would MOVE FILE: %s -> %s", srcPath, targetPath)
					err = move(srcPath, targetPath)
				}
			}

			if err != nil {
				errors = append(errors, fmt.Sprintf("Failed to %s %s to %s: %v", action, src, dest, err))
			} else if withSizes && sizeTreeRoot != nil {
				// Update size tree after successful operation
				// IMPORTANT: Must hold lock during size calculation to prevent races
				sizeTreeMutex.Lock()
				if action == "copy" {
					// For copy, add size to new parent chain
					newInfo, statErr := os.Stat(targetPath)
					if statErr == nil {
						isDir := newInfo.IsDir()
						var sizeToAdd int64
						if isDir {
							// For directories, walk and calculate total size
							// Lock is held during this - necessary to prevent size from
							// changing between calculation and tree update
							filepath.Walk(targetPath, func(_ string, fi os.FileInfo, _ error) error {
								if fi != nil && !fi.IsDir() {
									sizeToAdd += fi.Size()
								}
								return nil
							})
						} else {
							sizeToAdd = newInfo.Size()
						}

						// Add to new parent
						parentPath := filepath.Dir(targetPath)
						if parent := sizeTreeRoot.FindByPath(parentPath); parent != nil {
							parent.UpdateParentSizes(sizeToAdd)
						}
					}
				} else { // paste (move)
					// For move, subtract from old parent and add to new parent
					if oldNode := sizeTreeRoot.FindByPath(srcPath); oldNode != nil {
						size := oldNode.Size()

						// Remove from old location
						oldNode.UpdateParentSizes(-size)
						if oldNode.Parent != nil {
							oldNode.Parent.RemoveChild(oldNode)
						}

						// Add to new location
						newParentPath := filepath.Dir(targetPath)
						if newParent := sizeTreeRoot.FindByPath(newParentPath); newParent != nil {
							oldNode.Parent = newParent
							newParent.Children = append(newParent.Children, oldNode)
							oldNode.UpdateParentSizes(size)
							// Update the Info with new stat
							newInfo, statErr := os.Stat(targetPath)
							if statErr == nil {
								oldNode.Info = newInfo
								oldNode.Dir = targetPath
							}
						}
					}
				}
				sizeTreeMutex.Unlock()
			}
		}
	}

	// Log the operation to modifications.jsonl
	logModification(action, srcList, dest, errors)

	// Return response
	if len(errors) > 0 {
		return c.JSON(fiber.Map{
			"status": "error",
			"error":  strings.Join(errors, "; "),
		})
	}

	return c.JSON(fiber.Map{
		"status": "ok",
	})
}

type FileItem struct {
	Name      string `json:"name"`
	Path      string `json:"path"`      // Relative path for navigation/actions
	IsDir     bool   `json:"isDir"`     // Whether this is a directory
	Size      int64  `json:"size"`      // -1 when --with-sizes not used
	SizeStale bool   `json:"sizeStale"` // True if size data may be invalid
}

type WSMessage struct {
	RequestID int        `json:"requestId"`
	Items     []FileItem `json:"items"`
}

type WSRequest struct {
	Path      string `json:"path"`
	RequestID int    `json:"requestId"`
	SortBy    string `json:"sortBy"`
	Dir       string `json:"dir"`
}


func handleDocument(c *fiber.Ctx) error {
	// Check if office docs are enabled
	if libreOfficeAppPath == "" {
		return c.Status(503).SendString("Office document viewing is not enabled.")
	}

	// Get document path from query parameter and decode it
	encodedDocPath := c.Query("path")
	if encodedDocPath == "" {
		return c.Status(400).SendString("Document path is required")
	}

	// Decode the URL-encoded path
	decodedDocPath, err := url.QueryUnescape(encodedDocPath)
	if err != nil {
		return c.Status(400).SendString("Invalid document path encoding")
	}

	// Concatenate with root path to get full file path
	fullDocPath := filepath.Join(rootPath, decodedDocPath)

	// Check if file exists
	if _, err := os.Stat(fullDocPath); os.IsNotExist(err) {
		return c.Status(404).SendString("File not found: " + decodedDocPath)
	}

	// Parse the template from file
	tmpl, err := template.ParseFiles("doc_viewer.html.tmpl")
	if err != nil {
		return c.Status(500).SendString("Template error: " + err.Error())
	}

	// Convert document to HTML using LibreOffice
	htmlContent, err := convertDocumentToHTML(fullDocPath)
	if err != nil {
		return c.Status(500).SendString("Document conversion failed: " + err.Error())
	}

	// Prepare template data
	data := DocumentData{
		Title:        decodedDocPath,
		DocumentName: decodedDocPath,
		Content:      template.HTML(htmlContent),
	}

	// Execute the template
	c.Set("Content-Type", "text/html")
	return tmpl.Execute(c.Response().BodyWriter(), data)
}

func convertDocumentToHTML(docPath string) (string, error) {
	// Create temporary directory for output
	tempDir, err := ioutil.TempDir("", "libreoffice_convert_")
	if err != nil {
		return "", fmt.Errorf("failed to create temp directory: %v", err)
	}
	defer os.RemoveAll(tempDir) // Clean up temp directory

	// Determine the file extension to choose appropriate filter
	ext := strings.ToLower(filepath.Ext(docPath))
	var convertFilter string

	switch ext {
	case ".docx", ".doc", ".odt", ".rtf":
		convertFilter = "html:XHTML Writer File:BodyOnly,EmbedImages"
	case ".xlsx", ".xls", ".ods":
		convertFilter = "html:HTML (StarCalc):EmbedImages:BodyOnly"
	case ".pptx", ".ppt", ".odp":
		convertFilter = "html:HTML (Impress):EmbedImages:BodyOnly"
	default:
		return "", fmt.Errorf("unsupported file format: %s", ext)
	}

	// Prepare LibreOffice command
	cmd := exec.Command(
		libreOfficeAppPath,
		"--headless",
		"--convert-to", convertFilter,
		"--outdir", tempDir,
		docPath,
	)

	// Execute the conversion
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("LibreOffice conversion failed: %v, output: %s", err, string(output))
	}

	// Determine the output HTML filename
	baseName := filepath.Base(docPath)
	nameWithoutExt := strings.TrimSuffix(baseName, filepath.Ext(baseName))
	htmlFileName := nameWithoutExt + ".html"
	htmlFilePath := filepath.Join(tempDir, htmlFileName)

	// Read the generated HTML file
	htmlContent, err := ioutil.ReadFile(htmlFilePath)
	if err != nil {
		return "", fmt.Errorf("failed to read converted HTML file: %v", err)
	}

	return string(htmlContent), nil
}

var (
	rootPath           string
	libreOfficeAppPath string
	writeMode          bool
	withSizes          bool
	sizesFrom          string
	sizesTo            string
	sizeTreeRoot       *scan.FileData // Root of the size tree, walk from here
	sizeTreeMutex      sync.RWMutex   // Protects sizeTreeRoot from concurrent access
	fileOpsInProgress  sync.WaitGroup // Tracks in-flight file operations
	// Version information - these will be set at build time
	version   = "0.2.1-alpha" // Default version
	buildDate = "unknown"     // Will be set during build
	gitCommit = "unknown"     // Will be set during build
)

func setupTusUpload(app *fiber.App) {
	if !writeMode {
		log.Println("Upload disabled: not in write mode")
		return
	}

	// Check uploads directory
	uploadsDir := "./uploads"
	info, err := os.Stat(uploadsDir)
	if err == nil {
		// Directory exists
		if !info.IsDir() {
			log.Printf("Error: %s exists but is not a directory", uploadsDir)
			return
		}
		log.Printf("Uploads directory already exists: %s", uploadsDir)
	} else if os.IsNotExist(err) {
		// Directory doesn't exist, create it
		if err := os.Mkdir(uploadsDir, 0755); err != nil {
			log.Printf("Failed to create uploads directory: %s", err)
			return
		}
		log.Printf("Created uploads directory: %s", uploadsDir)
	} else {
		// Other error (permission, etc.)
		log.Printf("Failed to check uploads directory: %s", err)
		return
	}

	// Create file store
	store := filestore.New(uploadsDir)

	// Create composer
	composer := handler.NewStoreComposer()
	store.UseIn(composer)

	// Create config
	config := handler.Config{
		StoreComposer:         composer,
		NotifyCompleteUploads: true,
		BasePath:              "/upload/tus/",
	}

	// Create handler
	tusHandler, err := handler.NewHandler(config)
	if err != nil {
		log.Printf("Unable to create TUS handler: %s", err)
		return
	}
	log.Println("TUS upload handler initialized successfully")

	// Handle completed uploads
	go func() {
		for event := range tusHandler.CompleteUploads {
			info := event.Upload
			targetPath := info.MetaData["relativePath"]
			filename := info.MetaData["filename"]

			log.Printf("Upload completed - ID: %s, Filename: %s, TargetPath: %s", event.Upload.ID, filename, targetPath)

			tempFile := filepath.Join(uploadsDir, event.Upload.ID)
			finalPath := filepath.Join(rootPath, targetPath, filename)
			log.Printf("Moving from %s to %s", tempFile, finalPath)

			os.MkdirAll(filepath.Dir(finalPath), 0755)
			move(tempFile, finalPath)
			log.Printf("Successfully moved uploaded file to %s", finalPath)
		}
	}()

	// Mount using the bridge pattern - no manual conversion needed!
	prefix := "/upload/tus/"
	group := app.Group(prefix, adaptor.HTTPMiddleware(tusHandler.Middleware))

	group.Post("", adaptor.HTTPHandlerFunc(tusHandler.PostFile))
	group.Head(":id", adaptor.HTTPHandlerFunc(tusHandler.HeadFile))
	group.Patch(":id", adaptor.HTTPHandlerFunc(tusHandler.PatchFile))
	group.Get(":id", adaptor.HTTPHandlerFunc(tusHandler.GetFile))
	group.Delete(":id", adaptor.HTTPHandlerFunc(tusHandler.DelFile))
}

// loadSizeTree loads the size tree from a JSON file
func loadSizeTree(filename string) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	sizeTreeRoot = &scan.FileData{}
	err = json.Unmarshal(data, sizeTreeRoot)
	if err != nil {
		return fmt.Errorf("failed to unmarshal JSON: %w", err)
	}

	// Rebuild parent pointers after deserialization
	sizeTreeRoot.RebuildParentPointers(nil)

	return nil
}

// saveSizeTree saves the size tree to a JSON file
func saveSizeTree(filename string) error {
	// Acquire read lock to prevent modifications during save
	sizeTreeMutex.RLock()
	defer sizeTreeMutex.RUnlock()

	if sizeTreeRoot == nil {
		return fmt.Errorf("size tree is not initialized")
	}

	data, err := json.MarshalIndent(sizeTreeRoot, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	err = os.WriteFile(filename, data, 0644)
	if err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	return nil
}

// buildSizeTree scans the directory tree and builds the size tree
func buildSizeTree(rootPath string) error {
	// Create and start progress spinner
	spinner := scan.NewProgressSpinner()

	// Scan the directory tree
	children, err := scan.ScanDirConcurrent(rootPath, 0, spinner)

	// Stop spinner regardless of error
	spinner.Stop()

	if err != nil {
		return err
	}

	// Create root node with children
	sizeTreeRoot = &scan.FileData{}
	sizeTreeRoot.Children = children

	// Compute all sizes eagerly by calling Size() on root
	// This recursively computes and caches sizes for all nodes
	sizeTreeRoot.Size()

	return nil
}

func main() {
	// Parse command line arguments
	var showVersion bool
	var port string
	flag.BoolVar(&showVersion, "version", false, "Show version information and exit")
	flag.StringVar(&rootPath, "path", ".", "Root path to serve files from")
	flag.StringVar(&libreOfficeAppPath, "libreoffice", "", "Path to LibreOffice AppImage executable (optional - enables office document viewing)")
	flag.BoolVar(&writeMode, "write", false, "Enable write mode (allows file operations)")
	flag.BoolVar(&withSizes, "with-sizes", false, "Compute and display cumulative directory sizes")
	flag.StringVar(&sizesFrom, "sizes-from", "", "Load size tree from JSON file (default: sizes.json if flag provided without value)")
	flag.StringVar(&sizesTo, "sizes-to", "sizes.json", "Save size tree to JSON file on exit (default: sizes.json)")
	flag.StringVar(&port, "port", "8080", "Port to listen on (default 8080)")
	flag.Parse()

	// Validate mutually exclusive flags
	if withSizes && sizesFrom != "" {
		log.Fatal("Error: --with-sizes and --sizes-from are mutually exclusive")
	}

	// Handle version flag
	if showVersion {
		fmt.Printf("doc-viewer version %s\n", version)
		fmt.Printf("Build date: %s\n", buildDate)
		fmt.Printf("Git commit: %s\n", gitCommit)
		return
	}

	// Validate LibreOffice path if provided
	if libreOfficeAppPath != "" {
		if _, err := os.Stat(libreOfficeAppPath); os.IsNotExist(err) {
			log.Printf("LibreOffice AppImage not found at: %s - resetting to disabled", libreOfficeAppPath)
			libreOfficeAppPath = ""
		}
	}

	// Print final LibreOffice path status
	if libreOfficeAppPath != "" {
		log.Printf("LibreOffice path: %s", libreOfficeAppPath)
	} else {
		log.Printf("LibreOffice path: (not set - office document viewing disabled)")
	}

	// Convert to absolute path
	absPath, err := filepath.Abs(rootPath)
	if err != nil {
		log.Fatal("Invalid root path:", err)
	}
	rootPath = absPath

	log.Printf("Serving files from: %s", rootPath)

	// Load or compute sizes
	if sizesFrom != "" {
		// Load sizes from JSON
		if sizesFrom == "sizes.json" || sizesFrom == "" {
			sizesFrom = filepath.Join(rootPath, "sizes.json")
		}
		log.Printf("Loading size tree from: %s", sizesFrom)
		err := loadSizeTree(sizesFrom)
		if err != nil {
			log.Fatalf("Failed to load size tree: %v", err)
		}
		log.Println("Size tree loaded successfully")
		withSizes = true // Enable size display
	} else if withSizes {
		// Compute sizes from scratch
		log.Println("Computing directory sizes...")
		err := buildSizeTree(rootPath)
		if err != nil {
			log.Printf("Warning: Failed to compute sizes: %v", err)
			withSizes = false
		} else {
			log.Println("Directory size computation complete")
		}
	}

	// Create Fiber app
	app := fiber.New(fiber.Config{
		ErrorHandler: func(c *fiber.Ctx, err error) error {
			log.Printf("Error: %v", err)
			return c.Status(500).SendString("Internal Server Error")
		},
	})

	// Enable CORS
	app.Use(cors.New())

	// Serve static files from ./static directory
	app.Static("/static", "./static")

	// Your existing server setup code here...
	app.Get("/doc_viewer", handleDocument)

	// Serve the main HTML file at root
	app.Get("/", func(c *fiber.Ctx) error {
		tmpl, err := template.ParseFiles("./index.html.tmpl")
		if err != nil {
			return c.Status(500).SendString("Template error: " + err.Error())
		}

		data := IndexData{
			WriteMode: writeMode, // Pass writeMode
			RootPath:  rootPath,
		}

		c.Set("Content-Type", "text/html")
		return tmpl.Execute(c.Response().BodyWriter(), data)
	})

	// Image streaming route - now uses query parameter
	app.Get("/image", handleImageStream)

	// File streaming route - now uses query parameter
	app.Get("/file", handleFileStream)

	// Zip download route - streams folder as zip
	app.Get("/zip", handleZipDownload)

	// Rename route - renames file or folder
	app.Post("/rename", handleRename)

	//
	app.Get("/manage", handleManage)

	// WebSocket upgrade middleware
	app.Use("/files", func(c *fiber.Ctx) error {
		if websocket.IsWebSocketUpgrade(c) {
			c.Locals("allowed", true)
			return c.Next()
		}
		return fiber.ErrUpgradeRequired
	})

	setupTusUpload(app)
	// WebSocket handler
	app.Get("/files", websocket.New(handleWebSocket))

	// Setup signal handler for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	// Start server in goroutine
	go func() {
		log.Printf("Server starting on :%s\n", port)
		log.Println("Static files served from: ./static")
		if err := app.Listen(":" + port); err != nil {
			log.Printf("Server error: %v", err)
		}
	}()

	// Block on signal channel
	<-sigChan
	log.Println("\nReceived interrupt signal, waiting for in-progress operations...")

	// Wait for all file operations to complete
	fileOpsInProgress.Wait()
	log.Println("All file operations completed")

	// Save size tree if it exists and either --with-sizes or --sizes-from was used
	if sizeTreeRoot != nil && withSizes {
		saveFile := sizesTo
		if saveFile == "" {
			saveFile = "sizes.json"
		}
		// If it's a relative path, make it relative to rootPath
		if !filepath.IsAbs(saveFile) {
			saveFile = filepath.Join(rootPath, saveFile)
		}

		log.Printf("Saving size tree to: %s", saveFile)
		err := saveSizeTree(saveFile)
		if err != nil {
			log.Printf("Error saving size tree: %v", err)
		} else {
			log.Println("Size tree saved successfully")
		}
	}

	log.Println("Shutting down...")
	os.Exit(0)
}

func handleImageStream(c *fiber.Ctx) error {
	// Get the path from query parameter
	relativePath := c.Query("path")
	if relativePath == "" {
		return c.Status(400).SendString("Path parameter required")
	}

	// Explicitly URL decode the path
	decodedPath, err := url.QueryUnescape(relativePath)
	if err != nil {
		log.Printf("Error decoding path: %v", err)
		return c.Status(400).SendString("Invalid path encoding")
	}

	log.Printf("Image request for path: %s", decodedPath)

	// Construct full path using decoded path
	fullPath := filepath.Join(rootPath, decodedPath)

	// Check if file exists
	info, err := os.Stat(fullPath)
	if err != nil {
		log.Printf("Image file does not exist: %s", fullPath)
		return c.Status(404).SendString("Image not found")
	}

	// Check if it's a file (not directory)
	if info.IsDir() {
		return c.Status(400).SendString("Path is a directory, not a file")
	}

	// Check if it's an image file
	ext := strings.ToLower(filepath.Ext(fullPath))
	if !isImageFile(ext) {
		return c.Status(400).SendString("File is not a supported image format")
	}

	// Set appropriate content type
	contentType := getImageContentType(ext)
	c.Set("Content-Type", contentType)

	// Stream the file
	return c.SendFile(fullPath)
}

func handleFileStream(c *fiber.Ctx) error {
	// Get the path from query parameter
	relativePath := c.Query("path")
	if relativePath == "" {
		return c.Status(400).SendString("Path parameter required")
	}

	// Explicitly URL decode the path
	decodedPath, err := url.QueryUnescape(relativePath)
	if err != nil {
		log.Printf("Error decoding path: %v", err)
		return c.Status(400).SendString("Invalid path encoding")
	}

	log.Printf("File request for path: %s", decodedPath)

	// Construct full path using decoded path
	fullPath := filepath.Join(rootPath, decodedPath)

	// Check if file exists
	info, err := os.Stat(fullPath)
	if err != nil {
		log.Printf("File does not exist: %s", fullPath)
		return c.Status(404).SendString("File not found")
	}

	// Check if it's a file (not directory)
	if info.IsDir() {
		return c.Status(400).SendString("Path is a directory, not a file")
	}

	// Set appropriate content type
	ext := strings.ToLower(filepath.Ext(fullPath))
	contentType := getFileContentType(ext)
	c.Set("Content-Type", contentType)

	// Set Content-Disposition header for documents to suggest download
	if isDocumentFile(ext) {
		filename := filepath.Base(fullPath)
		c.Set("Content-Disposition", "inline; filename=\""+filename+"\"")
	}

	// Stream the file
	return c.SendFile(fullPath)
}

func handleZipDownload(c *fiber.Ctx) error {
	// Get the path from query parameter
	relativePath := c.Query("path")
	if relativePath == "" {
		return c.Status(400).SendString("Path parameter required")
	}

	// Explicitly URL decode the path
	decodedPath, err := url.QueryUnescape(relativePath)
	if err != nil {
		log.Printf("Error decoding path: %v", err)
		return c.Status(400).SendString("Invalid path encoding")
	}

	log.Printf("Zip download request for path: %s", decodedPath)

	// Construct full path using decoded path
	fullPath := filepath.Join(rootPath, decodedPath)

	// Check if path exists
	info, err := os.Stat(fullPath)
	if err != nil {
		log.Printf("Path does not exist: %s", fullPath)
		return c.Status(404).SendString("Path not found")
	}

	// Check if it's a directory
	if !info.IsDir() {
		return c.Status(400).SendString("Path must be a directory")
	}

	// Set headers for zip download
	zipName := filepath.Base(fullPath) + ".zip"
	c.Set("Content-Type", "application/zip")
	c.Set("Content-Disposition", "attachment; filename=\""+zipName+"\"")

	// Create zip writer that writes directly to response
	zipWriter := zip.NewWriter(c.Response().BodyWriter())
	defer zipWriter.Close()

	// Walk the directory and add files to zip
	err = filepath.Walk(fullPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip hidden files
		if strings.HasPrefix(filepath.Base(path), ".") {
			if info.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}

		// Get relative path for zip entry
		relPath, err := filepath.Rel(fullPath, path)
		if err != nil {
			return err
		}

		// Skip the root directory itself
		if relPath == "." {
			return nil
		}

		// Create zip header
		header, err := zip.FileInfoHeader(info)
		if err != nil {
			return err
		}

		// Use forward slashes in zip paths
		header.Name = filepath.ToSlash(relPath)

		// Set compression method
		if info.IsDir() {
			header.Name += "/"
		} else {
			header.Method = zip.Deflate
		}

		// Write header
		writer, err := zipWriter.CreateHeader(header)
		if err != nil {
			return err
		}

		// If it's a file, copy contents
		if !info.IsDir() {
			file, err := os.Open(path)
			if err != nil {
				return err
			}
			defer file.Close()

			_, err = io.Copy(writer, file)
			if err != nil {
				return err
			}
		}

		return nil
	})

	if err != nil {
		log.Printf("Error creating zip: %v", err)
		return c.Status(500).SendString("Failed to create zip archive")
	}

	log.Printf("Successfully created zip for: %s", decodedPath)
	return nil
}

func handleRename(c *fiber.Ctx) error {
	// Track this operation for graceful shutdown
	fileOpsInProgress.Add(1)
	defer fileOpsInProgress.Done()

	// Parse JSON body
	var req struct {
		Path    string `json:"path"`
		NewName string `json:"newName"`
	}

	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{
			"status": "error",
			"error":  "Invalid request body",
		})
	}

	// Validate inputs
	if req.Path == "" || req.NewName == "" {
		return c.Status(400).JSON(fiber.Map{
			"status": "error",
			"error":  "Path and newName are required",
		})
	}

	// Ensure newName doesn't contain path separators
	if strings.Contains(req.NewName, "/") || strings.Contains(req.NewName, "\\") {
		return c.Status(400).JSON(fiber.Map{
			"status": "error",
			"error":  "New name cannot contain path separators",
		})
	}

	// Build old and new paths
	oldPath := filepath.Join(rootPath, req.Path)
	dirPath := filepath.Dir(oldPath)
	newPath := filepath.Join(dirPath, req.NewName)

	// Check if old path exists
	if _, err := os.Stat(oldPath); err != nil {
		return c.Status(404).JSON(fiber.Map{
			"status": "error",
			"error":  "File or folder not found",
		})
	}

	// Check if new path already exists
	if _, err := os.Stat(newPath); err == nil {
		return c.Status(400).JSON(fiber.Map{
			"status": "error",
			"error":  "A file or folder with that name already exists",
		})
	}

	// Perform rename
	if err := os.Rename(oldPath, newPath); err != nil {
		log.Printf("Error renaming %s to %s: %v", oldPath, newPath, err)
		return c.Status(500).JSON(fiber.Map{
			"status": "error",
			"error":  fmt.Sprintf("Failed to rename: %v", err),
		})
	}

	// Update size tree after successful rename
	if withSizes && sizeTreeRoot != nil {
		sizeTreeMutex.Lock()
		if node := sizeTreeRoot.FindByPath(oldPath); node != nil {
			// Update the Info with new stat
			newInfo, err := os.Stat(newPath)
			if err == nil {
				node.Info = newInfo
				// Update Dir field with new path
				node.Dir = newPath
			}
		}
		sizeTreeMutex.Unlock()
	}

	log.Printf("Renamed: %s -> %s", req.Path, req.NewName)

	// Return new path relative to root
	newRelativePath := filepath.Join(filepath.Dir(req.Path), req.NewName)

	return c.JSON(fiber.Map{
		"status":  "success",
		"newPath": newRelativePath,
		"newName": req.NewName,
	})
}

func isImageFile(ext string) bool {
	imageExts := map[string]bool{
		".jpg":  true,
		".jpeg": true,
		".png":  true,
	}
	return imageExts[ext]
}

func isDocumentFile(ext string) bool {
	docExts := map[string]bool{
		".docx": true,
		".doc":  true,
		".xls":  true,
		".xlsx": true,
		".ppt":  true,
		".pptx": true,
		".pdf":  true,
	}
	return docExts[ext]
}

func getImageContentType(ext string) string {
	switch ext {
	case ".jpg", ".jpeg":
		return "image/jpeg"
	case ".png":
		return "image/png"
	default:
		return "application/octet-stream"
	}
}

func getFileContentType(ext string) string {
	switch ext {
	case ".docx":
		return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
	case ".doc":
		return "application/msword"
	case ".xlsx":
		return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
	case ".xls":
		return "application/vnd.ms-excel"
	case ".pptx":
		return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
	case ".ppt":
		return "application/vnd.ms-powerpoint"
	case ".pdf":
		return "application/pdf"
	case ".txt":
		return "text/plain"
	case ".js":
		return "application/javascript"
	case ".css":
		return "text/css"
	case ".html":
		return "text/html"
	case ".json":
		return "application/json"
	default:
		return "application/octet-stream"
	}
}

func getFileType(entry os.DirEntry) string {
	if entry.IsDir() {
		return "folder"
	}

	ext := strings.ToLower(filepath.Ext(entry.Name()))
	if isImageFile(ext) {
		return "image"
	} else if isDocumentFile(ext) {
		return "document"
	}
	return "file"
}

func handleWebSocket(c *websocket.Conn) {
	defer c.Close()

	log.Println("WebSocket connected")

	// Listen for path requests from client
	for {
		var req WSRequest
		if err := c.ReadJSON(&req); err != nil {
			log.Printf("WebSocket read error: %v", err)
			return
		}

		relativePath := req.Path
		requestID := req.RequestID
		sortBy := req.SortBy
		dir := req.Dir
		log.Printf("WebSocket received path request: %s (ID: %d, Sort: %s %s)", relativePath, requestID, sortBy, dir)

		// Get file listing for requested path
		items := getDirectoryListing(relativePath, sortBy, dir)

		// Send items in chunks of 10, wrapped with requestId
		chunkSize := 10
		for i := 0; i < len(items); i += chunkSize {
			end := min(i+chunkSize, len(items))
			chunk := items[i:end]

			msg := WSMessage{
				RequestID: requestID,
				Items:     chunk,
			}

			if err := c.WriteJSON(msg); err != nil {
				log.Printf("Error sending chunk: %v", err)
				return
			}
		}

		// Send empty array wrapped with requestId to indicate completion
		completionMsg := WSMessage{
			RequestID: requestID,
			Items:     []FileItem{},
		}
		if err := c.WriteJSON(completionMsg); err != nil {
			log.Printf("Error sending completion signal: %v", err)
			return
		}

		log.Printf("Finished sending files for path: %s (ID: %d)", relativePath, requestID)
	}
}

// Extract directory listing logic into separate function
func getDirectoryListing(relativePath, sortBy, dir string) []FileItem {

	// Simply concatenate rootPath with relativePath
	fullPath := filepath.Join(rootPath, relativePath)

	// Check if path exists
	info, err := os.Stat(fullPath)
	if err != nil {
		log.Printf("Path does not exist: %s (error: %v)", fullPath, err)
		return []FileItem{}
	}

	if !info.IsDir() {
		log.Printf("Path is not a directory: %s", fullPath)
		return []FileItem{}
	}

	// List directory contents
	entries, err := os.ReadDir(fullPath)
	if err != nil {
		log.Printf("Error reading directory %s: %v", fullPath, err)
		return []FileItem{}
	}

	// Convert to FileItems - separate folders from files
	var folders []FileItem
	var files []FileItem

	for _, entry := range entries {
		// Skip hidden files/folders
		if entry.Name()[0] == '.' {
			continue
		}

		// Create relative path for the item
		var itemRelativePath string
		if relativePath == "" {
			itemRelativePath = entry.Name()
		} else {
			itemRelativePath = filepath.Join(relativePath, entry.Name())
		}
		// Normalize path separators for web
		itemRelativePath = filepath.ToSlash(itemRelativePath)

		// Determine size
		var size int64 = -1          // Default when --with-sizes not used
		var sizeStale bool = false   // Track if size data is missing from tree
		if withSizes && sizeTreeRoot != nil {
			// Build full path for this item
			itemFullPath := filepath.Join(fullPath, entry.Name())
			sizeTreeMutex.RLock()
			if fileData := sizeTreeRoot.FindByPath(itemFullPath); fileData != nil {
				size = fileData.Size()
			} else {
				// Item exists on filesystem but not in tree (new file/folder added)
				sizeStale = true
			}
			sizeTreeMutex.RUnlock()
		}

		item := FileItem{
			Name:      entry.Name(),
			Path:      itemRelativePath,
			IsDir:     entry.IsDir(),
			Size:      size,
			SizeStale: sizeStale,
		}

		// Separate folders from files using entry.IsDir()
		if entry.IsDir() {
			folders = append(folders, item)
		} else {
			files = append(files, item)
		}
	}

	// Sort function
	sortItems := func(items []FileItem) {
		sort.Slice(items, func(i, j int) bool {
			var result bool
			switch sortBy {
			case "size":
				result = items[i].Size < items[j].Size
			default: // default to name sorting
				result = strings.ToLower(items[i].Name) < strings.ToLower(items[j].Name)
			}
			// Reverse if descending
			if dir == "desc" {
				result = !result
			}
			return result
		})
	}

	// Sort folders and files separately
	sortItems(folders)
	sortItems(files)

	// Combine: folders first, then files
	allItems := append(folders, files...)

	return allItems
}
