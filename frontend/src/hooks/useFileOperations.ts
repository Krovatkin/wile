// Hook for file operations (copy, cut, paste, delete, rename)

import { useCallback } from 'react';
import { api } from '@/services/api';
import type { ApiResponse } from '@/types';

interface UseFileOperationsReturn {
  deleteFiles: (paths: string[]) => Promise<ApiResponse>;
  renameFile: (path: string, newName: string) => Promise<ApiResponse>;
  copyFiles: (sources: string[], destination: string) => Promise<ApiResponse>;
  moveFiles: (sources: string[], destination: string) => Promise<ApiResponse>;
  downloadFolder: (path: string) => void;
}

export function useFileOperations(): UseFileOperationsReturn {
  const deleteFiles = useCallback(async (paths: string[]): Promise<ApiResponse> => {
    try {
      const response = await api.delete(paths);
      return response;
    } catch (error) {
      console.error('Delete error:', error);
      return {
        status: 'error',
        error: error instanceof Error ? error.message : 'Failed to delete files',
      };
    }
  }, []);

  const renameFile = useCallback(async (path: string, newName: string): Promise<ApiResponse> => {
    try {
      const response = await api.rename(path, newName);
      return response;
    } catch (error) {
      console.error('Rename error:', error);
      return {
        status: 'error',
        error: error instanceof Error ? error.message : 'Failed to rename',
      };
    }
  }, []);

  const copyFiles = useCallback(async (sources: string[], destination: string): Promise<ApiResponse> => {
    try {
      const response = await api.copy(sources, destination);
      return response;
    } catch (error) {
      console.error('Copy error:', error);
      return {
        status: 'error',
        error: error instanceof Error ? error.message : 'Failed to copy files',
      };
    }
  }, []);

  const moveFiles = useCallback(async (sources: string[], destination: string): Promise<ApiResponse> => {
    try {
      const response = await api.move(sources, destination);
      return response;
    } catch (error) {
      console.error('Move error:', error);
      return {
        status: 'error',
        error: error instanceof Error ? error.message : 'Failed to move files',
      };
    }
  }, []);

  const downloadFolder = useCallback((path: string): void => {
    api.downloadFolder(path);
  }, []);

  return {
    deleteFiles,
    renameFile,
    copyFiles,
    moveFiles,
    downloadFolder,
  };
}
