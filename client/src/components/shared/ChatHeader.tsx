import classNames from 'classnames';

interface ChatHeaderProps {
  title: string;
  isConnected: boolean;
  error?: string | null;
}

export function ChatHeader({ title, isConnected, error }: ChatHeaderProps) {
  return (
    <div className="border-b border-accent/20 p-4">
      <div className="flex items-center gap-2">
        <div
          className={classNames('h-2 w-2 flex-shrink-0 rounded-full', {
            'bg-green-500': isConnected,
            'bg-yellow-500': !isConnected && !error,
            'bg-red-500': error,
          })}
        />
        <h1 className="truncate text-2xl font-bold text-text">{title}</h1>
      </div>
    </div>
  );
}
