import { motion, AnimatePresence } from 'framer-motion'
import { GitCompareArrows, X } from 'lucide-react'

export default function CompareBar({ count, onCompare, onClear }) {
  return (
    <AnimatePresence>
      {count > 0 && (
        <motion.div
          initial={{ y: 60, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 60, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 400, damping: 28 }}
          className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 w-[calc(100%-2rem)] max-w-sm"
        >
          <div className="rounded-2xl border border-gray-200 dark:border-neutral-700 bg-white/90 dark:bg-neutral-900/90 backdrop-blur-xl shadow-xl shadow-black/10 dark:shadow-black/30 px-4 py-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-neutral-200">
              <GitCompareArrows size={16} className="text-blue-500" />
              <span className="font-medium">{count}</span>
              <span className="hidden sm:inline text-gray-500 dark:text-neutral-400">selected</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={onCompare}
                className="rounded-xl bg-blue-600 text-white text-sm font-medium px-4 py-2 hover:bg-blue-500 active:scale-[0.97] transition-all"
              >
                Compare
              </button>
              <button
                onClick={onClear}
                className="rounded-xl border border-gray-200 dark:border-neutral-700 text-sm px-3 py-2 bg-white dark:bg-neutral-900 hover:bg-gray-50 dark:hover:bg-neutral-800 text-gray-700 dark:text-neutral-200 active:scale-[0.97] transition-all"
                aria-label="Clear selection"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
