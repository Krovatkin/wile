// WebSocket service for file listing

import type { WebSocketMessage, SortColumn, SortDirection } from '@/types';

export type MessageHandler = (message: WebSocketMessage) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageId = 1;

  constructor(private path: string = '') {}

  connect(): void {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/files`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      // Request initial path
      this.requestPath(this.path);
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.notifyHandlers(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.attemptReconnect();
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... attempt ${this.reconnectAttempts}`);
      setTimeout(() => this.connect(), this.reconnectDelay);
    }
  }

  requestPath(path: string, sortBy: SortColumn = 'name', sortDir: SortDirection = 'asc'): void {
    const message = {
      path,
      requestId: this.messageId++,
      sortBy,
      dir: sortDir,
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not ready');
    }
  }

  requestSort(sortBy: SortColumn, sortDir: SortDirection): void {
    const message = {
      path: this.path,
      requestId: this.messageId++,
      sortBy,
      dir: sortDir,
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    // Return unsubscribe function
    return () => this.handlers.delete(handler);
  }

  private notifyHandlers(message: WebSocketMessage): void {
    this.handlers.forEach(handler => handler(message));
  }

  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

export function createWebSocket(path: string = ''): WebSocketService {
  return new WebSocketService(path);
}
