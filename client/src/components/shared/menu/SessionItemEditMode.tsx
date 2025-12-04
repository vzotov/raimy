'use client';

interface SessionItemEditModeProps {
  value: string;
  onChange: (value: string) => void;
  onSave: () => void;
  onCancel: () => void;
}

export default function SessionItemEditMode({
  value,
  onChange,
  onSave,
  onCancel,
}: SessionItemEditModeProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onSave();
    } else if (e.key === 'Escape') {
      onCancel();
    }
  };

  return (
    <div className="px-2 py-2 flex items-center gap-1">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        className="flex-1 px-2 py-1 text-sm bg-background border border-accent/30 rounded focus:outline-none focus:ring-2 focus:ring-primary"
        autoFocus
      />
      <button
        onClick={onSave}
        className="px-2 py-1 text-xs text-green-500 hover:text-green-600"
        title="Save"
      >
        ✓
      </button>
      <button
        onClick={onCancel}
        className="px-2 py-1 text-xs text-red-500 hover:text-red-600"
        title="Cancel"
      >
        ✕
      </button>
    </div>
  );
}
