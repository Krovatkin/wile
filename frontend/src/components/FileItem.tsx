// Individual file/folder item component

import type { FileEntry } from '@/types';
import { Icons, getFileIcon } from '@/services/icons';

interface FileItemProps {
  entry: FileEntry;
  isSelected: boolean;
  onSelect: (path: string) => void;
  onNavigate?: (path: string) => void;
  onRename: (path: string, currentName: string) => void;
  onDelete: (path: string) => void;
  onDownload?: (path: string) => void;
}

export function FileItem({
  entry,
  isSelected,
  onSelect,
  onNavigate,
  onRename,
  onDelete,
  onDownload,
}: FileItemProps) {
  const { name, path, type, modified } = entry;

  // Format date to dd/mm/yy
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
    }).format(date);
  };

  const formattedDate = formatDate(modified);
  const Icon = getFileIcon(name, type);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onSelect(path);
  };

  const handleDoubleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (type === 'folder' && onNavigate) {
      onNavigate(path);
    }
  };

  const handleRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRename(path, name);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(path);
  };

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDownload) {
      onDownload(path);
    }
  };

  const colorClass = type === 'folder' ? 'text-yellow-600 hover:bg-yellow-50' : '';
  const selectedClass = isSelected ? '!bg-blue-200 !text-white' : '';

  return (
    <li
      className={`cursor-pointer ${colorClass} ${selectedClass}`}
      title={name}
      data-path={path}
      data-file-type={type}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
    >
      <div className="grid grid-cols-[1fr_auto_auto] gap-2 items-center w-full">
        <div className="flex items-center gap-2 min-w-0 overflow-hidden">
          <Icon />
          <span className="truncate">{name}</span>
        </div>
        <div className="text-sm text-gray-500 whitespace-nowrap">
          {formattedDate}
        </div>
        <div className="flex gap-1">
          {/* Download button (folders only) */}
          {type === 'folder' && onDownload && (
            <button
              className="p-1 hover:bg-blue-100 rounded"
              title="Download folder as ZIP"
              onClick={handleDownload}
            >
              <Icons.download />
            </button>
          )}
          {/* Rename button */}
          <button
            className="p-1 hover:bg-gray-100 rounded"
            title={`Rename ${type}`}
            onClick={handleRename}
          >
            <Icons.rename />
          </button>
          {/* Delete button */}
          <button
            className="delete-btn p-1 hover:bg-red-100 rounded"
            title={`Delete ${type}`}
            onClick={handleDelete}
          >
            <Icons.delete />
          </button>
        </div>
      </div>
    </li>
  );
}
