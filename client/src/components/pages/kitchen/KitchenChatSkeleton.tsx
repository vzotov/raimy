export default function KitchenChatSkeleton() {
  return (
    <div className="flex flex-col h-dvh bg-background animate-pulse">
      {/* Header skeleton */}
      <div className="flex-shrink-0 border-b border-text/10 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-text/10 rounded"></div>
            <div className="h-6 bg-text/10 rounded w-40"></div>
          </div>
          <div className="w-8 h-8 bg-text/10 rounded"></div>
        </div>
      </div>

      {/* Messages area skeleton */}
      <div className="flex-1 overflow-hidden p-4 space-y-4">
        {/* Assistant message */}
        <div className="flex gap-3">
          <div className="w-8 h-8 bg-primary/20 rounded-full flex-shrink-0"></div>
          <div className="flex-1 space-y-2 max-w-[80%]">
            <div className="h-4 bg-text/10 rounded w-full"></div>
            <div className="h-4 bg-text/10 rounded w-3/4"></div>
          </div>
        </div>

        {/* User message */}
        <div className="flex gap-3 justify-end">
          <div className="space-y-2 max-w-[80%]">
            <div className="h-4 bg-primary/20 rounded w-48 ml-auto"></div>
          </div>
        </div>

        {/* Assistant message */}
        <div className="flex gap-3">
          <div className="w-8 h-8 bg-primary/20 rounded-full flex-shrink-0"></div>
          <div className="flex-1 space-y-2 max-w-[80%]">
            <div className="h-4 bg-text/10 rounded w-full"></div>
            <div className="h-4 bg-text/10 rounded w-5/6"></div>
            <div className="h-4 bg-text/10 rounded w-2/3"></div>
          </div>
        </div>
      </div>

      {/* Input area skeleton */}
      <div className="flex-shrink-0 border-t border-text/10 p-4">
        <div className="flex gap-2">
          <div className="flex-1 h-12 bg-text/10 rounded-lg"></div>
          <div className="w-12 h-12 bg-primary/30 rounded-lg"></div>
        </div>
      </div>
    </div>
  );
}
