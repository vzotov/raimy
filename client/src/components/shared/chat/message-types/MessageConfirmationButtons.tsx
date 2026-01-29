export interface MessageConfirmationButtonsProps {
  onAskQuestion: () => void;
  onSendDone: () => void;
  doneLabel?: string;
}

/**
 * Confirmation buttons for kitchen step messages.
 * Displays a question button (?) and a done/continue button.
 */
export default function MessageConfirmationButtons({
  onAskQuestion,
  onSendDone,
  doneLabel,
}: MessageConfirmationButtonsProps) {
  return (
    <div className="flex gap-3 mt-4 justify-center">
      {/* Question button */}
      <button
        type="button"
        onClick={onAskQuestion}
        aria-label="Ask a question"
        className="w-12 h-12 rounded-full border-2 border-text/30
          hover:border-text/50 hover:bg-text/5
          transition-colors duration-150
          flex items-center justify-center cursor-pointer"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </button>

      {/* Done/Continue button */}
      <button
        type="button"
        onClick={onSendDone}
        aria-label={doneLabel || 'Mark as done'}
        className={`rounded-full bg-primary/20 text-primary
          hover:bg-primary/30
          transition-colors duration-150
          flex items-center justify-center cursor-pointer
          ${doneLabel ? 'px-5 h-12 text-sm font-medium' : 'w-12 h-12'}`}
      >
        {doneLabel || (
          <svg
            className="w-7 h-7"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2.5}
              d="M5 13l4 4L19 7"
            />
          </svg>
        )}
      </button>
    </div>
  );
}
