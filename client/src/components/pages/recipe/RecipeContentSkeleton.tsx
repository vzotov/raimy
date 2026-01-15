export default function RecipeContentSkeleton() {
  return (
    <div className="animate-pulse">
      {/* Sticky Header skeleton */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-text/10 py-4 mb-6">
        <div className="h-9 bg-text/10 rounded-md w-2/3 px-4 sm:px-6 lg:px-8 mx-4 sm:mx-6 lg:mx-8"></div>
      </div>

      {/* Recipe Info skeleton */}
      <div className="flex items-center gap-6 mb-6 px-4 sm:px-6 lg:px-8">
        <div className="h-6 bg-text/10 rounded w-24"></div>
        <div className="h-6 bg-text/10 rounded w-28"></div>
        <div className="h-7 bg-text/10 rounded-full w-16"></div>
      </div>

      {/* Description skeleton */}
      <div className="space-y-2 mb-6 px-4 sm:px-6 lg:px-8">
        <div className="h-4 bg-text/10 rounded w-full"></div>
        <div className="h-4 bg-text/10 rounded w-4/5"></div>
      </div>

      {/* Tags skeleton */}
      <div className="flex flex-wrap gap-2 mb-6 px-4 sm:px-6 lg:px-8">
        <div className="h-8 bg-primary/10 rounded-full w-20"></div>
        <div className="h-8 bg-primary/10 rounded-full w-24"></div>
        <div className="h-8 bg-primary/10 rounded-full w-16"></div>
      </div>

      {/* Ingredients skeleton */}
      <div className="mb-8 px-4 sm:px-6 lg:px-8">
        <div className="h-7 bg-text/10 rounded w-32 mb-4"></div>
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center">
              <div className="w-2 h-2 bg-primary/30 rounded-full mr-3"></div>
              <div className="h-4 bg-text/10 rounded w-48"></div>
            </div>
          ))}
        </div>
      </div>

      {/* Instructions skeleton */}
      <div className="mb-8 px-4 sm:px-6 lg:px-8">
        <div className="h-7 bg-text/10 rounded w-32 mb-4"></div>
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-start">
              <div className="w-8 h-8 bg-primary/20 rounded-full mr-4 flex-shrink-0"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-text/10 rounded w-full"></div>
                <div className="h-4 bg-text/10 rounded w-3/4"></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons skeleton */}
      <div className="sticky bottom-0 bg-background/95 backdrop-blur-sm border-t border-text/10 py-4 mt-8">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row gap-3 sm:justify-center">
            <div className="h-12 bg-primary/30 rounded-lg w-full sm:w-40"></div>
            <div className="h-12 bg-text/10 rounded-lg w-full sm:w-36"></div>
            <div className="h-12 bg-text/10 rounded-lg w-full sm:w-36"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
