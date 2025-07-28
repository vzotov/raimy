import { useEffect, useRef, useState, useCallback } from 'react';

interface SSEEvent {
  type: string;
  data: any;
}

interface UseSSEOptions {
  url?: string;
  onMessage?: (event: SSEEvent) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  retryInterval?: number;
  maxRetries?: number;
}

export const useSSE = (options: UseSSEOptions = {}) => {
  const {
    url = '/api/events',
    onMessage,
    onError,
    onOpen,
    onClose,
    retryInterval = 5000,
    maxRetries = 5,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setError(null);
        retryCountRef.current = 0;
        onOpen?.();
      };

      eventSource.onmessage = (event) => {
        try {
          const parsedEvent: SSEEvent = JSON.parse(event.data);
          setLastEvent(parsedEvent);
          onMessage?.(parsedEvent);
        } catch (err) {
          console.error('Failed to parse SSE event:', err);
        }
      };

      eventSource.onerror = (event) => {
        setIsConnected(false);
        setError('SSE connection error');
        onError?.(event);

        // Retry logic
        if (retryCountRef.current < maxRetries) {
          retryCountRef.current++;
          retryTimeoutRef.current = setTimeout(() => {
            connect();
          }, retryInterval);
        }
      };

      eventSource.addEventListener('ping', () => {
        // Handle keepalive pings
        console.log('SSE ping received');
      });

    } catch (err) {
      setError('Failed to create SSE connection');
      console.error('SSE connection error:', err);
    }
  }, [url, onMessage, onError, onOpen, retryInterval, maxRetries]);

  const disconnect = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setIsConnected(false);
    onClose?.();
  }, [onClose]);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const sendEvent = useCallback(async (eventType: string, data: any) => {
    try {
      const response = await fetch(`/api/${eventType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.error(`Failed to send ${eventType} event:`, err);
      throw err;
    }
  }, []);

  return {
    isConnected,
    lastEvent,
    error,
    connect,
    disconnect,
    sendEvent,
  };
}; 