// Main App component

import { useState, useCallback, useEffect } from 'react';
import { TabBar } from './components/TabBar';
import { FileOperationsBar } from './components/FileOperationsBar';
import { FileList } from './components/FileList';
import { NotificationContainer } from './components/Notification';
import { useWebSocket } from './hooks/useWebSocket';
import { useFileOperations } from './hooks/useFileOperations';
import { useNotifications } from './hooks/useNotifications';
import type { SortColumn, SortDirection, ClipboardState } from './types';

interface Tab {
  id: string;
  label: string;
  path: string;
  sortBy: SortColumn;
  sortDir: SortDirection;
  selected: Set<string>;
}

function App() {
  // Tab management
  const [tabs, setTabs] = useState<Tab[]>([
    {
      id: '1',
      label: 'Tab 1',
      path: '',
      sortBy: 'name',
      sortDir: 'asc',
      selected: new Set(),
    },
  ]);
  const [activeTabId, setActiveTabId] = useState('1');

  // Get active tab
  const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0];

  // WebSocket for file listing
  const { files, folders, isLoading, requestPath, requestSort } = useWebSocket(activeTab.path);

  // File operations
  const { deleteFiles, renameFile, copyFiles, moveFiles, downloadFolder } = useFileOperations();

  // Notifications
  const { notifications, addNotification, removeNotification } = useNotifications();

  // Clipboard state
  const [clipboard, setClipboard] = useState<ClipboardState>({
    files: [],
    operation: null,
  });

  // Path history for back button
  const [pathHistory, setPathHistory] = useState<string[]>(['']);

  // Request files when path changes
  useEffect(() => {
    requestPath(activeTab.path, activeTab.sortBy, activeTab.sortDir);
  }, [activeTab.path, activeTab.sortBy, activeTab.sortDir, requestPath]);

  // Tab operations
  const handleAddTab = useCallback(() => {
    const newId = String(tabs.length + 1);
    const newTab: Tab = {
      id: newId,
      label: `Tab ${newId}`,
      path: '',
      sortBy: 'name',
      sortDir: 'asc',
      selected: new Set(),
    };
    setTabs(prev => [...prev, newTab]);
    setActiveTabId(newId);
  }, [tabs.length]);

  const handleCloseTab = useCallback((tabId: string) => {
    if (tabs.length <= 1) return;
    setTabs(prev => prev.filter(t => t.id !== tabId));
    if (activeTabId === tabId) {
      setActiveTabId(tabs[0].id);
    }
  }, [tabs, activeTabId]);

  // Update active tab state
  const updateActiveTab = useCallback((updates: Partial<Tab>) => {
    setTabs(prev =>
      prev.map(t => (t.id === activeTabId ? { ...t, ...updates } : t))
    );
  }, [activeTabId]);

  // File selection
  const handleSelect = useCallback((path: string) => {
    const newSelected = new Set(activeTab.selected);
    if (newSelected.has(path)) {
      newSelected.delete(path);
    } else {
      newSelected.add(path);
    }
    updateActiveTab({ selected: newSelected });
  }, [activeTab.selected, updateActiveTab]);

  // Navigation
  const handleNavigate = useCallback((path: string) => {
    setPathHistory(prev => [...prev, activeTab.path]);
    updateActiveTab({ path, selected: new Set() });
  }, [activeTab.path, updateActiveTab]);

  const handleBack = useCallback(() => {
    if (pathHistory.length > 0) {
      const previousPath = pathHistory[pathHistory.length - 1];
      setPathHistory(prev => prev.slice(0, -1));
      updateActiveTab({ path: previousPath, selected: new Set() });
    }
  }, [pathHistory, updateActiveTab]);

  // Sorting
  const handleSort = useCallback((column: SortColumn) => {
    const newDir: SortDirection =
      activeTab.sortBy === column && activeTab.sortDir === 'asc' ? 'desc' : 'asc';
    updateActiveTab({ sortBy: column, sortDir: newDir });
    requestSort(column, newDir);
  }, [activeTab.sortBy, activeTab.sortDir, updateActiveTab, requestSort]);

  // Clipboard operations
  const handleCopy = useCallback(() => {
    const selectedArray = Array.from(activeTab.selected);
    setClipboard({ files: selectedArray, operation: 'copy' });
    addNotification(`${selectedArray.length} item(s) copied`, 'info');
  }, [activeTab.selected, addNotification]);

  const handleCut = useCallback(() => {
    const selectedArray = Array.from(activeTab.selected);
    setClipboard({ files: selectedArray, operation: 'cut' });
    addNotification(`${selectedArray.length} item(s) cut`, 'warning');
  }, [activeTab.selected, addNotification]);

  const handlePaste = useCallback(async () => {
    if (clipboard.operation === 'copy') {
      const result = await copyFiles(clipboard.files, activeTab.path);
      if (result.status === 'success' || result.status === 'ok') {
        addNotification('Files copied successfully', 'success');
        requestPath(activeTab.path, activeTab.sortBy, activeTab.sortDir);
      } else {
        addNotification(result.error || 'Failed to copy', 'error');
      }
    } else if (clipboard.operation === 'cut') {
      const result = await moveFiles(clipboard.files, activeTab.path);
      if (result.status === 'success' || result.status === 'ok') {
        addNotification('Files moved successfully', 'success');
        setClipboard({ files: [], operation: null });
        requestPath(activeTab.path, activeTab.sortBy, activeTab.sortDir);
      } else {
        addNotification(result.error || 'Failed to move', 'error');
      }
    }
  }, [clipboard, activeTab.path, activeTab.sortBy, activeTab.sortDir, copyFiles, moveFiles, addNotification, requestPath]);

  // File operations
  const handleRename = useCallback(async (path: string, currentName: string) => {
    const newName = window.prompt('Enter new name:', currentName);
    if (!newName || newName === currentName) return;

    const result = await renameFile(path, newName);
    if (result.status === 'success') {
      addNotification(`Renamed to "${newName}"`, 'success');
      requestPath(activeTab.path, activeTab.sortBy, activeTab.sortDir);
    } else {
      addNotification(result.error || 'Failed to rename', 'error');
    }
  }, [renameFile, addNotification, activeTab.path, activeTab.sortBy, activeTab.sortDir, requestPath]);

  const handleDelete = useCallback(async (path: string) => {
    const fileName = path.split('/').pop();
    if (!window.confirm(`Are you sure you want to delete "${fileName}"?`)) return;

    const result = await deleteFiles([path]);
    if (result.status === 'success' || result.status === 'ok') {
      addNotification('Deleted successfully', 'success');
      requestPath(activeTab.path, activeTab.sortBy, activeTab.sortDir);
      updateActiveTab({ selected: new Set() });
    } else {
      addNotification(result.error || 'Failed to delete', 'error');
    }
  }, [deleteFiles, addNotification, activeTab.path, activeTab.sortBy, activeTab.sortDir, requestPath, updateActiveTab]);

  const handleDownload = useCallback((path: string) => {
    downloadFolder(path);
  }, [downloadFolder]);

  return (
    <div className="bg-gray-100 min-h-screen p-4">
      <div className="w-full max-w-none mx-4 md:w-3/4 md:max-w-4xl md:mx-auto">
        {/* Tab Bar */}
        <TabBar
          tabs={tabs}
          activeTabId={activeTabId}
          onTabClick={setActiveTabId}
          onTabClose={handleCloseTab}
          onAddTab={handleAddTab}
        />

        {/* File Operations Bar */}
        <FileOperationsBar
          canGoBack={pathHistory.length > 0}
          selectedCount={activeTab.selected.size}
          canPaste={clipboard.files.length > 0}
          onBack={handleBack}
          onCopy={handleCopy}
          onCut={handleCut}
          onPaste={handlePaste}
        />

        {/* File Browser Container */}
        <div className="bg-blue-100 rounded-lg flex flex-col" style={{ height: 'calc(100vh - 200px)' }}>
          <div className="p-4 text-xl font-medium">
            📁 <span id="currentPath">/{activeTab.path}</span>
          </div>
          <div className="px-4 pb-4 flex flex-col flex-1 overflow-hidden">
            <FileList
              files={files}
              folders={folders}
              selectedPaths={activeTab.selected}
              isLoading={isLoading}
              sortBy={activeTab.sortBy}
              sortDir={activeTab.sortDir}
              onSelect={handleSelect}
              onNavigate={handleNavigate}
              onRename={handleRename}
              onDelete={handleDelete}
              onDownload={handleDownload}
              onSort={handleSort}
            />

            {/* Upload Dropzone - placeholder */}
            <div
              id="uploadDropzone"
              className="mt-2 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 flex items-center justify-center text-gray-500 text-sm"
              style={{ minHeight: '48px', maxHeight: '48px' }}
            >
              Drop files here to upload
            </div>
          </div>
        </div>

        {/* Notifications */}
        <NotificationContainer
          notifications={notifications}
          onClose={removeNotification}
        />
      </div>
    </div>
  );
}

export default App;
