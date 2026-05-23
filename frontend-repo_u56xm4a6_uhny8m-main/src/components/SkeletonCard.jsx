export default function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-gray-100 dark:border-neutral-800 bg-white/70 dark:bg-neutral-900/60 p-4 animate-pulse">
      {/* Image placeholder */}
      <div className="aspect-[4/3] w-full rounded-xl skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />

      {/* Title + price row */}
      <div className="mt-3 flex items-start justify-between gap-3">
        <div className="flex-1 space-y-2">
          <div className="h-4 w-3/4 rounded-md skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />
          <div className="h-3 w-1/2 rounded-md skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />
        </div>
        <div className="space-y-2 text-right">
          <div className="h-4 w-12 rounded-md skeleton-shimmer bg-gray-100 dark:bg-neutral-800 ml-auto" />
          <div className="h-3 w-16 rounded-md skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />
        </div>
      </div>

      {/* Specs placeholder */}
      <div className="mt-3 flex gap-1.5">
        <div className="h-5 w-12 rounded-full skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />
        <div className="h-5 w-16 rounded-full skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />
        <div className="h-5 w-10 rounded-full skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />
      </div>
    </div>
  )
}
