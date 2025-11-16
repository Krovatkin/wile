// Hook for WebSocket connection and file listing

import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketService, createWebSocket } from '@/services/websocket';
import type { FileEntry, SortColumn, SortDirection } from '@/types';

interface UseWebSocketReturn {
  files: FileEntry[];
  folders: FileEntry[];
  isConnected: boolean;
  isLoading: boolean;
  requestPath: (path: string, sortBy?: SortColumn, sortDir?: SortDirection) => void;
  requestSort: (sortBy: SortColumn, sortDir: SortDirection) => void;
}

export function useWebSocket(initialPath: string = ''): UseWebSocketReturn {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [folders, setFolders] = useState<FileEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const wsRef = useRef<WebSocketService | null>(null);

  useEffect(() => {
    // Create WebSocket instance
    const ws = createWebSocket(initialPath);
    wsRef.current = ws;

    // Subscribe to messages
    const unsubscribe = ws.onMessage((message: any) => {
      // Server sends: { requestId: 1, items: [...] }
      // Items can have type: "folder", "file", or "image"
      if (message.items && Array.isArray(message.items)) {
        const items = message.items as FileEntry[];

        // Empty array signals completion - hide spinner and return
        if (items.length === 0) {
          setIsLoading(false);
          return;
        }

        // Split into folders and files (treat "image" as file)
        const foldersList = items.filter(e => e.type === 'folder');
        const filesList = items.filter(e => e.type !== 'folder');
        setFolders(foldersList);
        setFiles(filesList);
        setIsLoading(false);
      } else if (message.type === 'error') {
        console.error('WebSocket error:', message.payload?.error || message.error);
        setIsLoading(false);
      }
    });

    // Connect
    ws.connect();

    // Check connection status periodically
    const intervalId = setInterval(() => {
      const state = ws.getReadyState();
      setIsConnected(state === WebSocket.OPEN);
    }, 1000);

    // Cleanup
    return () => {
      unsubscribe();
      clearInterval(intervalId);
      ws.disconnect();
    };
  }, [initialPath]);

  const requestPath = useCallback((path: string, sortBy: SortColumn = 'name', sortDir: SortDirection = 'asc') => {
    setIsLoading(true);
    wsRef.current?.requestPath(path, sortBy, sortDir);
  }, []);

  const requestSort = useCallback((sortBy: SortColumn, sortDir: SortDirection) => {
    wsRef.current?.requestSort(sortBy, sortDir);
  }, []);

  return {
    files,
    folders,
    isConnected,
    isLoading,
    requestPath,
    requestSort,
  };
}
