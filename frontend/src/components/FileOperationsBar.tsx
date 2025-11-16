// File operations toolbar component

import { Icons } from '@/services/icons';

interface FileOperationsBarProps {
  canGoBack: boolean;
  selectedCount: number;
  canPaste: boolean;
  onBack: () => void;
  onCopy: () => void;
  onCut: () => void;
  onPaste: () => void;
}

export function FileOperationsBar({
  canGoBack,
  selectedCount,
  canPaste,
  onBack,
  onCopy,
  onCut,
  onPaste,
}: FileOperationsBarProps) {
  const hasSelection = selectedCount > 0;

  return (
    <div className="flex items-center gap-2 mb-4 p-2 bg-white rounded-lg shadow-sm">
      {/* Back button */}
      {canGoBack && (
        <>
          <button
            id="backButton"
            className="btn btn-sm btn-ghost"
            onClick={onBack}
          >
            <Icons.back />
            Back
          </button>
          <div className="divider divider-horizontal"></div>
        </>
      )}

      {/* Copy button */}
      <button
        id="copyBtn"
        className="btn btn-sm btn-ghost"
        disabled={!hasSelection}
        onClick={onCopy}
      >
        <Icons.copy />
        Copy
      </button>

      {/* Cut button */}
      <button
        id="cutBtn"
        className="btn btn-sm btn-ghost"
        disabled={!hasSelection}
        onClick={onCut}
      >
        <Icons.cut />
        Cut
      </button>

      {/* Paste button */}
      <button
        id="pasteBtn"
        className="btn btn-sm btn-ghost"
        disabled={!canPaste}
        onClick={onPaste}
      >
        <Icons.paste />
        Paste
      </button>

      <div className="divider divider-horizontal"></div>

      {/* Selection count */}
      <span id="selectionCount" className="text-sm text-gray-500">
        {hasSelection
          ? `${selectedCount} item${selectedCount > 1 ? 's' : ''} selected`
          : 'No items selected'}
      </span>
    </div>
  );
}
