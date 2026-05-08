import classNames from 'classnames';
import {
  type FormEvent,
  forwardRef,
  type KeyboardEvent,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from 'react';

export interface ChatInputHandle {
  focus: () => void;
  setValue: (value: string) => void;
}

export interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  sendDisabled?: boolean;
  loading?: boolean;
  placeholder?: string;
  defaultValue?: string;
  variant?: 'chat' | 'home';
}

const MAX_HEIGHT = 140; // ~5 lines

const ChatInput = forwardRef<ChatInputHandle, ChatInputProps>(
  function ChatInput(
    {
      onSend,
      disabled = false,
      sendDisabled,
      loading = false,
      placeholder = 'Type a message...',
      defaultValue = '',
      variant = 'chat',
    },
    ref,
  ) {
    const isDisabled = disabled || loading;
    const isButtonDisabled = sendDisabled ?? isDisabled;
    const [message, setMessage] = useState(defaultValue);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useImperativeHandle(ref, () => ({
      focus: () => textareaRef.current?.focus(),
      setValue: (value: string) => {
        setMessage(value);
        textareaRef.current?.focus();
      },
    }));

    useEffect(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
    }, [message]);

    const handleSubmit = (e: FormEvent) => {
      e.preventDefault();
      if (message.trim() && !isButtonDisabled) {
        onSend(message.trim());
        setMessage('');
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
        }
        setTimeout(() => textareaRef.current?.focus(), 0);
      }
    };

    useEffect(() => {
      if (variant === 'chat') {
        textareaRef.current?.focus();
      }
    }, [variant]);

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    };

    if (variant === 'home') {
      return (
        <form onSubmit={handleSubmit} className="w-full">
          <div className="flex gap-2 items-center rounded-2xl border border-accent/30 bg-surface shadow-sm p-2 pl-5">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isDisabled}
              placeholder={placeholder}
              rows={1}
              className="flex-1 resize-none bg-transparent text-base text-text placeholder:text-text/40 focus:outline-none disabled:opacity-50 overflow-y-auto"
              style={{ minHeight: '25px' }}
            />
            <button
              type="submit"
              disabled={isButtonDisabled || !message.trim()}
              className="w-11 h-11 rounded-xl flex items-center justify-center bg-primary text-white hover:bg-primary/90 disabled:opacity-40 transition-colors flex-shrink-0"
              aria-label="Start cooking"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
              )}
            </button>
          </div>
        </form>
      );
    }

    return (
      <form onSubmit={handleSubmit} className="border-t border-accent/20 p-4">
        <div className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isDisabled}
            placeholder={placeholder}
            maxLength={1000}
            rows={1}
            className={classNames(
              'flex-1 resize-none rounded-lg px-4 py-3 text-sm sm:text-base',
              'bg-surface border border-accent/20',
              'text-text placeholder:text-text/50 placeholder:truncate',
              'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'overflow-y-auto',
            )}
            style={{ minHeight: '48px' }}
          />
          <button
            type="submit"
            disabled={isButtonDisabled || !message.trim()}
            className={classNames(
              'w-12 h-12 rounded-lg flex items-center justify-center',
              'bg-primary text-white',
              'hover:bg-primary-hover active:bg-primary-pressed',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-colors duration-150',
              'flex-shrink-0',
            )}
            aria-label="Send message"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            )}
          </button>
        </div>
        <p className="text-xs text-text/50 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </form>
    );
  },
);

export default ChatInput;
