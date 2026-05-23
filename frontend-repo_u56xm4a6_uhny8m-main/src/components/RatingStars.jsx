import { Star } from 'lucide-react'

export default function RatingStars({ value = 0, size = 14 }) {
  const full = Math.floor(value)
  const half = value - full >= 0.5

  return (
    <div className="flex items-center gap-0.5" aria-label={`Rating ${value} out of 5`} role="img">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          size={size}
          className={
            i < full
              ? 'text-amber-400 fill-amber-400'
              : i === full && half
              ? 'text-amber-300 fill-amber-300'
              : 'text-gray-300 dark:text-neutral-700'
          }
        />
      ))}
      <span className="ml-1 text-xs text-gray-500 dark:text-neutral-400 tabular-nums">
        {value.toFixed(1)}
      </span>
    </div>
  )
}
