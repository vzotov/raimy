import type { SelectorOption } from '@/types/chat-message-types';

export interface MessageSelectorButtonsProps {
  options: SelectorOption[];
  onSelect: (option: string) => void;
}

/**
 * Selector buttons for multiple choice messages.
 * Displays options as vertical full-width buttons with optional descriptions.
 */
export default function MessageSelectorButtons({
  options,
  onSelect,
}: MessageSelectorButtonsProps) {
  return (
    <div className="flex flex-col gap-2 mt-4">
      {options.map((option) => (
        <button
          key={option.text}
          type="button"
          onClick={() => onSelect(option.text)}
          className="w-full px-4 py-3 rounded-lg border-2 border-text/20
            hover:border-primary/50 hover:bg-primary/5
            transition-colors duration-150
            text-left cursor-pointer"
        >
          <span className="text-sm font-medium">{option.text}</span>
          {option.description && (
            <span className="block text-xs text-text/60 mt-0.5">
              {option.description}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
