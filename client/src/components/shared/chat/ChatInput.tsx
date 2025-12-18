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
}

export interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * Stateless component for text input with send button.
 * Handles enter key to send, shift+enter for new line.
 * Auto-focuses input after sending message for continuous UX.
 * Exposes focus() method via ref for programmatic focus.
 */
const ChatInput = forwardRef<ChatInputHandle, ChatInputProps>(
  function ChatInput(
    { onSend, disabled = false, placeholder = 'Type a message...' },
    ref,
  ) {
    const [message, setMessage] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Expose focus method via ref
    useImperativeHandle(ref, () => ({
      focus: () => textareaRef.current?.focus(),
    }));

    const handleSubmit = (e: FormEvent) => {
      e.preventDefault();
      if (message.trim() && !disabled) {
        onSend(message.trim());
        setMessage('');
        // Auto-focus input after sending for continuous conversation
        setTimeout(() => {
          textareaRef.current?.focus();
        }, 0);
      }
    };

    // Focus on mount for immediate typing
    useEffect(() => {
      textareaRef.current?.focus();
    }, []);

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Send on Enter, new line on Shift+Enter
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    };

    return (
      <form onSubmit={handleSubmit} className="border-t border-accent/20 p-4">
        <div className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder={placeholder}
            rows={1}
            className={classNames(
              'flex-1 resize-none rounded-lg px-4 py-3 text-sm sm:text-base',
              'bg-surface border border-accent/20',
              'text-text placeholder:text-text/50',
              'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'max-h-32 overflow-y-auto',
            )}
            style={{
              minHeight: '48px',
              height: 'auto',
            }}
          />
          <button
            type="submit"
            disabled={disabled || !message.trim()}
            className={classNames(
              'px-6 py-3 rounded-lg font-medium text-sm sm:text-base',
              'bg-primary text-white',
              'hover:bg-primary-hover active:bg-primary-pressed',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-colors duration-150',
              'flex-shrink-0',
            )}
          >
            Send
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
