// File list component

import type { FileEntry, SortColumn, SortDirection } from '@/types';
import { FileItem } from './FileItem';
import { LoadingSpinner } from './LoadingSpinner';
import { Icons } from '@/services/icons';

interface FileListProps {
  files: FileEntry[];
  folders: FileEntry[];
  selectedPaths: Set<string>;
  isLoading: boolean;
  sortBy: SortColumn;
  sortDir: SortDirection;
  onSelect: (path: string) => void;
  onNavigate: (path: string) => void;
  onRename: (path: string, currentName: string) => void;
  onDelete: (path: string) => void;
  onDownload: (path: string) => void;
  onSort: (column: SortColumn) => void;
}

export function FileList({
  files,
  folders,
  selectedPaths,
  isLoading,
  sortBy: _sortBy,
  sortDir: _sortDir,
  onSelect,
  onNavigate,
  onRename,
  onDelete,
  onDownload,
  onSort,
}: FileListProps) {
  const allEntries = [...folders, ...files];

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Column Headers */}
      <div className="bg-base-100 rounded-t-box px-4 py-2 border-b border-gray-200">
        <div className="grid grid-cols-[1fr_auto_auto] gap-2 items-center w-full">
          <button
            className="flex items-center gap-1 text-sm font-semibold text-gray-600 hover:text-gray-900 text-left"
            onClick={() => onSort('name')}
          >
            Name
            <Icons.sort />
          </button>
          <button
            className="text-sm font-semibold text-gray-600 hover:text-gray-900 whitespace-nowrap"
            onClick={() => onSort('modified')}
          >
            Modified
            <Icons.sort />
          </button>
          <div style={{ width: '36px' }}></div>
        </div>
      </div>

      {/* File List */}
      <ul className="menu bg-base-100 rounded-b-box p-2 overflow-y-auto flex-1" id="fileList">
        {isLoading ? (
          <LoadingSpinner />
        ) : allEntries.length === 0 ? (
          <li className="text-center text-gray-500 py-4">No files or folders</li>
        ) : (
          allEntries.map((entry) => (
            <FileItem
              key={entry.path}
              entry={entry}
              isSelected={selectedPaths.has(entry.path)}
              onSelect={onSelect}
              onNavigate={entry.type === 'folder' ? onNavigate : undefined}
              onRename={onRename}
              onDelete={onDelete}
              onDownload={entry.type === 'folder' ? onDownload : undefined}
            />
          ))
        )}
      </ul>
    </div>
  );
}
