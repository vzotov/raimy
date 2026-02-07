export default function ProfileContentSkeleton() {
  return (
    <div className="animate-pulse space-y-8">
      {/* Account Section */}
      <div>
        <div className="h-6 bg-text/10 rounded w-24 mb-4"></div>
        <div className="bg-surface rounded-lg p-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-text/10 rounded-full"></div>
            <div className="space-y-2">
              <div className="h-5 bg-text/10 rounded w-32"></div>
              <div className="h-4 bg-text/10 rounded w-48"></div>
            </div>
          </div>
        </div>
        <div className="h-10 bg-text/10 rounded w-24 mt-4"></div>
      </div>

      {/* Memory Section */}
      <div>
        <div className="h-6 bg-text/10 rounded w-64 mb-4"></div>
        <div className="bg-surface rounded-lg p-4">
          <div className="space-y-2">
            <div className="h-4 bg-text/10 rounded w-full"></div>
            <div className="h-4 bg-text/10 rounded w-4/5"></div>
            <div className="h-4 bg-text/10 rounded w-3/4"></div>
            <div className="h-4 bg-text/10 rounded w-5/6"></div>
            <div className="h-4 bg-text/10 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
