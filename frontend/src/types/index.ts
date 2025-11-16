// Core types for the file browser application

export interface FileEntry {
  name: string;
  path: string;
  type: 'file' | 'folder';
  modified: string;
  size?: number;
}

export interface TabState {
  id: string;
  path: string;
  sortBy: 'name' | 'modified';
  sortDir: 'asc' | 'desc';
  selected: Set<string>;
  ws?: WebSocket;
}

export interface ClipboardState {
  files: string[];
  operation: 'copy' | 'cut' | null;
}

export type SortColumn = 'name' | 'modified';
export type SortDirection = 'asc' | 'desc';

export interface WebSocketMessage {
  type: 'files' | 'sort' | 'error';
  id?: number;
  payload?: {
    entries?: FileEntry[];
    folders?: FileEntry[];
    files?: FileEntry[];
    sortBy?: SortColumn;
    sortDir?: SortDirection;
    error?: string;
  };
}

export interface ApiResponse<T = unknown> {
  status: 'success' | 'error' | 'ok';
  error?: string;
  data?: T;
  newPath?: string;
  newName?: string;
}

export interface RenameRequest {
  path: string;
  newName: string;
}

export interface FileOperation {
  action: 'copy' | 'paste' | 'delete';
  srcs: string[];
  dest?: string;
}

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  id: string;
  message: string;
  type: NotificationType;
}
