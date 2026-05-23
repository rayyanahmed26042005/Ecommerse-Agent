import { motion, AnimatePresence } from 'framer-motion'
import { X, AlertTriangle } from 'lucide-react'
import { useState } from 'react'

export default function ApiErrorBanner({ error }) {
  const [dismissed, setDismissed] = useState(false)

  if (!error || dismissed) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: -40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -40, opacity: 0 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        className="fixed top-0 left-0 right-0 z-[60] bg-red-600 text-white text-xs px-4 py-2.5"
        role="alert"
      >
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <AlertTriangle size={14} className="shrink-0" />
            <span className="truncate">{error}</span>
          </div>
          <button
            onClick={() => setDismissed(true)}
            className="shrink-0 h-5 w-5 rounded-full hover:bg-white/20 flex items-center justify-center transition-colors"
            aria-label="Dismiss error"
          >
            <X size={12} />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
