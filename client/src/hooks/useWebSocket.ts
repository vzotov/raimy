/**
 * WebSocket Hook for Chat Communication
 *
 * Manages WebSocket connection to the backend chat service
 * with automatic reconnection and message handling.
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { MessageContent } from '@/types/chat-message-types';

export interface ChatMessage {
  type: 'user_message' | 'agent_message' | 'system';
  content?: MessageContent;
  session_id?: string;
  message_id?: string;
}

interface UseWebSocketOptions {
  sessionId: string;
  userId?: string;
  onMessage?: (message: ChatMessage) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  sendMessage: (content: string) => void;
  isConnected: boolean;
  error: string | null;
  reconnect: () => void;
}

export function useWebSocket({
  sessionId,
  userId = 'anonymous',
  onMessage,
  onError,
  onConnect,
  onDisconnect,
  autoReconnect = true,
  reconnectInterval = 3000,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnect = useRef(true);

  const connect = useCallback(() => {
    try {
      // Build WebSocket URL (authentication via cookies)
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = process.env.NEXT_PUBLIC_WS_HOST || window.location.host.replace(':3000', ':8000');
      const wsUrl = `${wsProtocol}//${wsHost}/ws/chat/${sessionId}`;

      console.log('📡 Connecting to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setError(null);
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: ChatMessage = JSON.parse(event.data);
          console.log('📨 Received message:', message);
          onMessage?.(message);
        } catch (err) {
          console.error('❌ Failed to parse message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('❌ WebSocket error:', event);
        setError('WebSocket connection error');
        onError?.(event);
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        onDisconnect?.();

        // Auto-reconnect if enabled
        if (autoReconnect && shouldReconnect.current) {
          console.log(`🔄 Reconnecting in ${reconnectInterval}ms...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('❌ Failed to create WebSocket:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [sessionId, onMessage, onError, onConnect, onDisconnect, autoReconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    shouldReconnect.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    shouldReconnect.current = true;
    connect();
  }, [connect, disconnect]);

  const sendMessage = useCallback(
    (content: string) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        const message: ChatMessage = {
          type: 'user_message',
          content: {
            type: 'text',
            content: content
          },
        };

        // Include userId in the message
        const messageWithUser = {
          ...message,
          user_id: userId,
        };

        console.log('📤 Sending message:', messageWithUser);
        wsRef.current.send(JSON.stringify(messageWithUser));
      } else {
        console.error('❌ WebSocket not connected. Cannot send message.');
        setError('WebSocket not connected');
      }
    },
    [userId]
  );

  // Connect on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    sendMessage,
    isConnected,
    error,
    reconnect,
  };
}
