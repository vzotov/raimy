import { useEffect, useRef, useState, useCallback } from 'react';

interface SSEEvent {
  type: string;
  data: Record<string, unknown>;
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
    url = `${process.env.NEXT_PUBLIC_API_URL!}/api/events`,
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
  
  // Store callbacks in refs to avoid recreating connection
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);
  
  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);
  
  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);
  
  useEffect(() => {
    onOpenRef.current = onOpen;
  }, [onOpen]);
  
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

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
        onOpenRef.current?.();
      };

      eventSource.onmessage = (event) => {
        try {
          const parsedEvent: SSEEvent = JSON.parse(event.data);
          setLastEvent(parsedEvent);
          onMessageRef.current?.(parsedEvent);
        } catch (err) {
          console.error('Failed to parse SSE event:', err);
        }
      };

      eventSource.onerror = (event) => {
        setIsConnected(false);
        setError('SSE connection error');
        onErrorRef.current?.(event);

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
  }, [url, retryInterval, maxRetries]);

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
    onCloseRef.current?.();
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastEvent,
    error,
    connect,
    disconnect,
  };
};
