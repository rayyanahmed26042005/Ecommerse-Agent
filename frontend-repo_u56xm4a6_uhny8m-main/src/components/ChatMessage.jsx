import { motion, AnimatePresence } from 'framer-motion'
import { ChevronRight, ChevronDown, Sparkles, Layers } from 'lucide-react'
import ProductCard from './ProductCard'

export default function ChatMessage({
  message,
  showSummary,
  onToggleSummary,
  selections,
  onToggleSelect,
  onSendMessage,
}) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className={isUser ? 'flex justify-end' : 'flex justify-start'}
    >
      <div
        className={`${
          isUser
            ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white border-blue-700/50 rounded-br-md'
            : 'bg-white dark:bg-neutral-900 text-gray-900 dark:text-neutral-100 border border-gray-100 dark:border-neutral-800 rounded-bl-md'
        } max-w-[90%] sm:max-w-[85%] md:max-w-[75%] lg:max-w-[70%] rounded-2xl p-4 shadow-sm`}
      >
        {/* Message text */}
        <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">{message.content}</div>

        {/* Research summary (assistant only) */}
        {!isUser && (message.summary || (message.insights && message.insights.length > 0)) && (
          <div className="mt-3">
            <button
              onClick={onToggleSummary}
              className="text-xs text-gray-500 dark:text-neutral-400 inline-flex items-center gap-1 hover:text-gray-700 dark:hover:text-neutral-300 transition-colors"
              aria-expanded={showSummary}
            >
              {showSummary ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              Research Summary
            </button>
            <AnimatePresence initial={false}>
              {showSummary && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease: 'easeInOut' }}
                  className="overflow-hidden"
                >
                  {message.summary && (
                    <p className="mt-2 text-sm text-gray-700 dark:text-neutral-300 leading-relaxed">
                      {message.summary}
                    </p>
                  )}
                  {message.insights?.length > 0 && (
                    <ul className="mt-2 space-y-1 text-sm text-gray-600 dark:text-neutral-300 list-disc pl-5">
                      {message.insights.map((insight, k) => (
                        <li key={k} className="leading-relaxed">{insight}</li>
                      ))}
                    </ul>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Product grid */}
        {message.suggestions?.length > 0 && (
          <div className="mt-4 border border-gray-100 dark:border-neutral-800 rounded-2xl bg-gray-50/50 dark:bg-neutral-800/20 p-3 sm:p-4">
            <div className="mb-3 flex items-center justify-between">
              <div className="text-sm font-semibold text-gray-900 dark:text-neutral-100">
                Top Products
              </div>
              <div className="text-[11px] text-gray-400 dark:text-neutral-500">
                Curated for you
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4">
              {message.suggestions.map((p, pi) => (
                <ProductCard
                  key={pi}
                  item={p}
                  selected={selections.includes(p.title)}
                  onToggleSelect={() => onToggleSelect(p.title)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Action buttons */}
        {message.suggestions?.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={() => onSendMessage('Find better alternatives to these')}
              className="inline-flex items-center gap-1.5 rounded-xl bg-blue-600 text-white px-3 py-1.5 text-xs font-medium hover:bg-blue-500 active:scale-[0.97] transition-all"
            >
              <Layers size={13} /> Find Alternatives
            </button>
            <button
              onClick={() => onSendMessage('Give me a deeper analysis of these products')}
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-3 py-1.5 text-xs text-gray-700 dark:text-neutral-200 hover:bg-gray-50 dark:hover:bg-neutral-800 active:scale-[0.97] transition-all"
            >
              <Sparkles size={13} className="text-blue-500" /> Deeper Analysis
            </button>
          </div>
        )}
      </div>
    </motion.div>
  )
}
