export default function RecipeCardSkeleton() {
  return (
    <div className="bg-surface rounded-lg shadow-md overflow-hidden h-full flex flex-col animate-pulse">
      <div className="p-6 flex flex-col flex-1">
        {/* Title skeleton */}
        <div className="h-7 bg-text/10 rounded-md w-3/4 mb-4"></div>

        {/* Description skeleton */}
        <div className="space-y-2 mb-4">
          <div className="h-4 bg-text/10 rounded w-full"></div>
          <div className="h-4 bg-text/10 rounded w-5/6"></div>
        </div>

        {/* Tags skeleton */}
        <div className="flex gap-2 mb-4">
          <div className="h-7 bg-primary/10 rounded-full w-16"></div>
          <div className="h-7 bg-primary/10 rounded-full w-20"></div>
        </div>

        {/* Spacer */}
        <div className="flex-1"></div>

        {/* Button skeleton */}
        <div className="flex gap-2">
          <div className="flex-1 h-10 bg-primary/30 rounded-lg"></div>
          <div className="h-10 w-12 bg-text/10 rounded-lg"></div>
        </div>
      </div>
    </div>
  );
}

export function RecipeListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:auto-rows-fr">
      {Array.from({ length: count }).map((_, i) => (
        <RecipeCardSkeleton key={i} />
      ))}
    </div>
  );
}
