'use client';

import { MessageContent, ChatIngredient } from '@/types/chat-message-types';

// Sample data
const sampleIngredients: ChatIngredient[] = [
  { name: 'Chicken breast', amount: 2, unit: 'lbs', notes: 'boneless, skinless' },
  { name: 'Olive oil', amount: 2, unit: 'tbsp' },
  { name: 'Garlic', amount: 4, unit: 'cloves', notes: 'minced' },
  { name: 'Salt', notes: 'to taste' },
  { name: 'Black pepper', notes: 'to taste' },
];

export interface ChatDebugPanelProps {
  onAddMessage: (role: 'user' | 'assistant', content: MessageContent) => void;
  onClear?: () => void;
}

/**
 * Debug panel for testing chat message types without invoking LLM.
 * Shows buttons to inject fake data into the chat.
 */
export default function ChatDebugPanel({ onAddMessage, onClear }: ChatDebugPanelProps) {
  const addUserText = () => {
    onAddMessage('user', {
      type: 'text',
      content: 'Can you help me plan meals for this week?',
    });
  };

  const addAssistantText = () => {
    onAddMessage('assistant', {
      type: 'text',
      content: "I'd be happy to help you plan meals! What are your dietary preferences and goals?",
    });
  };

  const addIngredients = () => {
    onAddMessage('assistant', {
      type: 'ingredients',
      title: 'Shopping List for This Week',
      items: sampleIngredients,
    });
  };

  return (
    <div className="border-l border-accent/20 bg-surface/50 p-4 w-64 flex-shrink-0 overflow-y-auto">
      <div className="space-y-4">
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-text">Debug Panel</h3>
          <p className="text-xs text-text/60">
            Add fake messages to test UI without LLM
          </p>
        </div>

        <div className="space-y-2">
          <p className="text-xs font-medium text-text/70 uppercase">Text Messages</p>
          <div className="space-y-1">
            <button
              onClick={addUserText}
              className="w-full px-3 py-2 text-xs bg-primary/20 hover:bg-primary/30 text-text rounded-lg transition-colors"
            >
              + User Text
            </button>
            <button
              onClick={addAssistantText}
              className="w-full px-3 py-2 text-xs bg-accent/20 hover:bg-accent/30 text-text rounded-lg transition-colors"
            >
              + Assistant Text
            </button>
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-xs font-medium text-text/70 uppercase">Structured Messages</p>
          <div className="space-y-1">
            <button
              onClick={addIngredients}
              className="w-full px-3 py-2 text-xs bg-accent/20 hover:bg-accent/30 text-text rounded-lg transition-colors"
            >
              + Ingredient List
            </button>
          </div>
        </div>

        {onClear && (
          <div className="pt-2 border-t border-accent/20">
            <button
              onClick={onClear}
              className="w-full px-3 py-2 text-xs bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
            >
              Clear All Messages
            </button>
          </div>
        )}

        <div className="pt-2 border-t border-accent/20 text-xs text-text/50">
          <p className="mb-1">💡 Quick tip:</p>
          <p>Use these buttons to test message layouts without using LLM tokens.</p>
        </div>
      </div>
    </div>
  );
}
