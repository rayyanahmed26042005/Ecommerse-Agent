import { motion, AnimatePresence } from 'framer-motion'
import { Award } from 'lucide-react'

export default function AchievementToast({ achievement }) {
  return (
    <AnimatePresence>
      {achievement && (
        <motion.div
          initial={{ y: 40, opacity: 0, scale: 0.9 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          exit={{ y: 40, opacity: 0, scale: 0.9 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          className="fixed bottom-20 right-4 z-40 max-w-xs"
        >
          <div className="flex items-center gap-3 rounded-2xl border border-emerald-200 dark:border-emerald-400/30 bg-emerald-50 dark:bg-emerald-400/10 px-4 py-3 shadow-lg shadow-emerald-500/10">
            <div className="shrink-0 h-9 w-9 rounded-xl bg-emerald-100 dark:bg-emerald-400/20 flex items-center justify-center">
              <Award className="text-emerald-600 dark:text-emerald-300" size={18} />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-semibold text-emerald-800 dark:text-emerald-200 truncate">
                {achievement.title}
              </div>
              <div className="text-xs text-emerald-700 dark:text-emerald-300/90 truncate">
                {achievement.desc}
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
