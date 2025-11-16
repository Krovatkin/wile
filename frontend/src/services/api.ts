// API service for backend communication

import type { ApiResponse, RenameRequest } from '@/types';

export const api = {
  /**
   * Rename a file or folder
   */
  async rename(path: string, newName: string): Promise<ApiResponse> {
    const response = await fetch('/rename', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ path, newName } as RenameRequest),
    });
    return response.json();
  },

  /**
   * Delete files or folders
   */
  async delete(paths: string[]): Promise<ApiResponse> {
    const params = new URLSearchParams();
    params.append('action', 'delete');
    paths.forEach(path => params.append('srcs', path));

    const response = await fetch(`/manage?${params.toString()}`);
    return response.json();
  },

  /**
   * Copy files to a destination
   */
  async copy(sources: string[], destination: string): Promise<ApiResponse> {
    const params = new URLSearchParams();
    params.append('action', 'copy');
    params.append('dest', destination);
    sources.forEach(src => params.append('srcs', src));

    const response = await fetch(`/manage?${params.toString()}`);
    return response.json();
  },

  /**
   * Move (paste) files to a destination
   */
  async move(sources: string[], destination: string): Promise<ApiResponse> {
    const params = new URLSearchParams();
    params.append('action', 'paste');
    params.append('dest', destination);
    sources.forEach(src => params.append('srcs', src));

    const response = await fetch(`/manage?${params.toString()}`);
    return response.json();
  },

  /**
   * Download a folder as ZIP
   */
  downloadFolder(path: string): void {
    const encodedPath = encodeURIComponent(path);
    window.location.href = `/zip?path=${encodedPath}`;
  },

  /**
   * Get file stream URL
   */
  getFileUrl(path: string): string {
    return `/file?path=${encodeURIComponent(path)}`;
  },
};
