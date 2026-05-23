import { useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Sparkles, TrendingUp, ShoppingBag, Heart } from 'lucide-react'

const sidebarItemVariants = {
  hidden: { opacity: 0, x: -8 },
  visible: (i) => ({
    opacity: 1,
    x: 0,
    transition: { delay: i * 0.025, type: 'spring', stiffness: 400, damping: 28 },
  }),
}

function SectionHeader({ icon: Icon, children }) {
  return (
    <div className="flex items-center gap-2 text-[11px] uppercase tracking-widest text-gray-400 dark:text-neutral-500 mb-3 font-semibold">
      <Icon size={13} />
      {children}
    </div>
  )
}

function SidebarSkeleton({ rows = 3 }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 rounded-xl border border-gray-100 dark:border-neutral-800 p-2.5">
          <div className="h-10 w-10 rounded-lg skeleton-shimmer bg-gray-100 dark:bg-neutral-800 shrink-0" />
          <div className="flex-1 space-y-1.5">
            <div className="h-3.5 w-3/4 rounded skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />
            <div className="h-3 w-1/2 rounded skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />
          </div>
        </div>
      ))}
    </div>
  )
}

export default function Sidebar({
  isOpen,
  onClose,
  quickActions = [],
  trending = [],
  essentials = [],
  picks = [],
  onSendMessage,
  isDataLoading = false,
}) {
  const sidebarRef = useRef(null)

  // Close on Escape
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape' && isOpen) onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [isOpen, onClose])

  // Lock body scroll when sidebar is open on mobile
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  const handleAction = useCallback(
    (text) => {
      onSendMessage(text)
      onClose()
    },
    [onSendMessage, onClose]
  )

  const hasApiData = trending.length > 0 || essentials.length > 0 || picks.length > 0

  return (
    <>
      {/* Mobile backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden fixed inset-0 z-30 sidebar-backdrop"
            onClick={onClose}
            aria-hidden="true"
          />
        )}
      </AnimatePresence>

      {/* Sidebar — always fixed, visible on desktop via translate */}
      <aside
        ref={sidebarRef}
        role="navigation"
        aria-label="Shopping assistant sidebar"
        className={`
          fixed inset-y-0 left-0 z-40
          border-r border-gray-100 dark:border-neutral-800
          bg-white/90 dark:bg-neutral-950/90 backdrop-blur-xl
          w-[85%] max-w-[320px] md:w-[280px] lg:w-[300px]
          transition-transform duration-300 ease-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Spacer for desktop to clear top bar */}
        <div className="hidden md:block h-3" />

        <div className="p-4 md:p-5 space-y-7 h-full overflow-y-auto">
          {/* Mobile header */}
          <div className="md:hidden flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-sm shadow-blue-500/25">
                <Sparkles size={14} className="text-white" />
              </div>
              <div className="font-semibold tracking-tight text-gray-900 dark:text-neutral-100 text-sm">
                Shopping Assistant
              </div>
            </div>
            <button
              onClick={onClose}
              className="h-8 w-8 rounded-xl border border-gray-200 dark:border-neutral-700 text-gray-500 dark:text-neutral-400 flex items-center justify-center hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors"
              aria-label="Close sidebar"
            >
              <X size={16} />
            </button>
          </div>

          {/* Quick Actions — always shown immediately */}
          <div>
            <SectionHeader icon={Sparkles}>Quick Actions</SectionHeader>
            <div className="flex flex-wrap gap-2">
              {quickActions.map((qa, i) => (
                <motion.button
                  key={i}
                  custom={i}
                  initial="hidden"
                  animate="visible"
                  variants={sidebarItemVariants}
                  onClick={() => handleAction(qa)}
                  className="rounded-xl bg-gray-100 dark:bg-neutral-800/80 hover:bg-gray-200 dark:hover:bg-neutral-700 text-gray-700 dark:text-neutral-300 text-xs px-3 py-1.5 transition-colors active:scale-95"
                >
                  {qa}
                </motion.button>
              ))}
            </div>
          </div>

          {/* Trending */}
          <div>
            <SectionHeader icon={TrendingUp}>Trending This Week</SectionHeader>
            {!hasApiData && isDataLoading ? (
              <SidebarSkeleton rows={3} />
            ) : trending.length > 0 ? (
              <div className="space-y-2">
                {trending.map((t, i) => (
                  <motion.button
                    key={i}
                    custom={i}
                    initial="hidden"
                    animate="visible"
                    variants={sidebarItemVariants}
                    onClick={() => handleAction(`Find ${t.title.toLowerCase()}`)}
                    className="w-full flex items-center gap-3 rounded-xl border border-gray-100 dark:border-neutral-800 bg-white dark:bg-neutral-900/60 p-2.5 hover:shadow-sm hover:border-gray-200 dark:hover:border-neutral-700 transition-all group"
                  >
                    <img
                      src={t.image}
                      alt=""
                      className="h-10 w-10 rounded-lg object-cover shrink-0 group-hover:scale-105 transition-transform"
                      loading="lazy"
                    />
                    <div className="text-left min-w-0">
                      <div className="text-sm font-medium text-gray-900 dark:text-neutral-100 truncate">
                        {t.title}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-neutral-400">
                        ${t.price.toFixed(0)} · {t.category}
                      </div>
                    </div>
                  </motion.button>
                ))}
              </div>
            ) : null}
          </div>

          {/* Daily Essentials */}
          <div>
            <SectionHeader icon={ShoppingBag}>Daily Essentials</SectionHeader>
            {!hasApiData && isDataLoading ? (
              <div className="grid grid-cols-2 gap-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-2 rounded-xl border border-gray-100 dark:border-neutral-800 p-2">
                    <div className="h-9 w-9 rounded-lg skeleton-shimmer bg-gray-100 dark:bg-neutral-800 shrink-0" />
                    <div className="flex-1 space-y-1">
                      <div className="h-3 w-full rounded skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />
                      <div className="h-2.5 w-1/2 rounded skeleton-shimmer bg-gray-100 dark:bg-neutral-800" />
                    </div>
                  </div>
                ))}
              </div>
            ) : essentials.length > 0 ? (
              <div className="grid grid-cols-2 gap-2">
                {essentials.map((t, i) => (
                  <motion.button
                    key={i}
                    custom={i}
                    initial="hidden"
                    animate="visible"
                    variants={sidebarItemVariants}
                    onClick={() => handleAction(`Best ${t.title.toLowerCase()}`)}
                    className="flex items-center gap-2 rounded-xl border border-gray-100 dark:border-neutral-800 bg-white dark:bg-neutral-900/60 p-2 hover:shadow-sm hover:border-gray-200 dark:hover:border-neutral-700 transition-all group"
                  >
                    <img
                      src={t.image}
                      alt=""
                      className="h-9 w-9 rounded-lg object-cover shrink-0 group-hover:scale-105 transition-transform"
                      loading="lazy"
                    />
                    <div className="text-left min-w-0">
                      <div className="text-[11px] font-medium text-gray-900 dark:text-neutral-100 line-clamp-2 leading-4">
                        {t.title}
                      </div>
                      <div className="text-[10px] text-gray-500 dark:text-neutral-400">
                        ${t.price.toFixed(0)}
                      </div>
                    </div>
                  </motion.button>
                ))}
              </div>
            ) : null}
          </div>

          {/* Personal Picks */}
          {(picks.length > 0 || (!hasApiData && isDataLoading)) && (
            <div>
              <SectionHeader icon={Heart}>Personal Picks</SectionHeader>
              {!hasApiData && isDataLoading ? (
                <SidebarSkeleton rows={2} />
              ) : (
                <div className="space-y-2">
                  {picks.map((t, i) => (
                    <motion.button
                      key={i}
                      custom={i}
                      initial="hidden"
                      animate="visible"
                      variants={sidebarItemVariants}
                      onClick={() => handleAction(`Recommend a ${t.title.toLowerCase()}`)}
                      className="w-full flex items-center gap-3 rounded-xl border border-gray-100 dark:border-neutral-800 bg-white dark:bg-neutral-900/60 p-2.5 hover:shadow-sm hover:border-gray-200 dark:hover:border-neutral-700 transition-all group"
                    >
                      <img
                        src={t.image}
                        alt=""
                        className="h-10 w-10 rounded-lg object-cover shrink-0 group-hover:scale-105 transition-transform"
                        loading="lazy"
                      />
                      <div className="text-left min-w-0">
                        <div className="text-sm font-medium text-gray-900 dark:text-neutral-100 truncate">
                          {t.title}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-neutral-400">
                          {t.category}
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Bottom spacer for mobile safe area */}
          <div className="h-8 md:h-4" />
        </div>
      </aside>
    </>
  )
}
