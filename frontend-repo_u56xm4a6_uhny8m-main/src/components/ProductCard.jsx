import { useState } from 'react'
import { motion } from 'framer-motion'
import { Check, Plus, Sparkles } from 'lucide-react'
import RatingStars from './RatingStars'

export default function ProductCard({ item, selected, onToggleSelect }) {
  const [imgLoaded, setImgLoaded] = useState(false)

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 16 }}
      whileHover={{ y: -4, scale: 1.015 }}
      transition={{ type: 'spring', stiffness: 300, damping: 24 }}
      className={
        'group relative rounded-2xl border bg-white/70 dark:bg-neutral-900/60 backdrop-blur p-4 shadow-sm ' +
        'hover:shadow-lg hover:shadow-black/5 dark:hover:shadow-black/20 transition-shadow ' +
        (selected
          ? 'border-blue-300 dark:border-blue-500/40 ring-1 ring-blue-200 dark:ring-blue-500/20'
          : 'border-gray-100 dark:border-neutral-800')
      }
    >
      {/* Select button */}
      <div className="absolute top-3 right-3 z-10">
        <button
          onClick={onToggleSelect}
          className={`h-7 w-7 rounded-full border flex items-center justify-center transition-all active:scale-90 ${
            selected
              ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-500 dark:border-blue-500 shadow-sm shadow-blue-500/25'
              : 'bg-white/80 dark:bg-neutral-900/80 backdrop-blur text-gray-500 border-gray-200 hover:border-gray-300 dark:text-neutral-400 dark:border-neutral-700 dark:hover:border-neutral-600'
          }`}
          aria-label={selected ? 'Deselect product' : 'Select for comparison'}
        >
          {selected ? <Check size={14} strokeWidth={2.5} /> : <Plus size={14} />}
        </button>
      </div>

      {/* Product image */}
      <div className="aspect-[4/3] w-full overflow-hidden rounded-xl bg-gray-100 dark:bg-neutral-800 relative">
        {!imgLoaded && (
          <div className="absolute inset-0 skeleton-shimmer rounded-xl" />
        )}
        <img
          src={item.image}
          alt={item.title}
          loading="lazy"
          onLoad={() => setImgLoaded(true)}
          className={`h-full w-full object-cover object-center transition-all duration-500 group-hover:scale-105 ${
            imgLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          onError={(e) => {
            e.currentTarget.onerror = null
            e.currentTarget.src =
              'https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=1200&auto=format&fit=crop'
            setImgLoaded(true)
          }}
        />
      </div>

      {/* Title + price */}
      <div className="mt-3 flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-neutral-100 tracking-tight truncate">
            {item.title}
          </h3>
          <p className="mt-0.5 text-xs text-gray-500 dark:text-neutral-400">{item.category}</p>
        </div>
        <div className="text-right shrink-0">
          <div className="text-sm font-bold text-gray-900 dark:text-neutral-100 tabular-nums">
            ${item.price.toFixed(0)}
          </div>
          <RatingStars value={item.rating ?? 4.6} size={12} />
        </div>
      </div>

      {/* Specs */}
      {item.specs?.length > 0 && (
        <div className="mt-3">
          <div className="flex flex-wrap gap-1.5">
            {item.specs.slice(0, 4).map((s, i) => (
              <span
                key={i}
                className="inline-flex items-center rounded-full border border-gray-200 dark:border-neutral-700 px-2 py-0.5 text-[10px] text-gray-600 dark:text-neutral-300 bg-gray-50 dark:bg-neutral-800/60"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Retailers */}
      {item.retailers?.length > 0 && (
        <div className="mt-3 border-t border-gray-100 dark:border-neutral-800 pt-3">
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            {item.retailers.map((r, i) => (
              <span
                key={i}
                className={`rounded-full px-2 py-0.5 border transition-colors ${
                  r.best
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-400/30 dark:bg-emerald-400/10 dark:text-emerald-300 font-medium'
                    : 'border-gray-200 bg-gray-50 text-gray-600 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300'
                }`}
              >
                {r.name} · ${r.price}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Why we recommend */}
      <div className="mt-3">
        <div className="relative group/why">
          <div className="text-xs text-gray-500 dark:text-neutral-400 inline-flex items-center gap-1 cursor-help">
            <Sparkles size={12} className="text-blue-500" /> Why we recommend this
          </div>
          <div className="pointer-events-none opacity-0 group-hover/why:opacity-100 transition-opacity duration-200">
            <div className="absolute z-20 mt-2 left-0 right-0 sm:w-64 sm:left-auto sm:right-auto rounded-xl border border-gray-100 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-3 text-xs text-gray-600 dark:text-neutral-300 shadow-xl">
              {item.reasoning ||
                'Balanced performance-to-price, reliable brand support, and strong user feedback.'}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
