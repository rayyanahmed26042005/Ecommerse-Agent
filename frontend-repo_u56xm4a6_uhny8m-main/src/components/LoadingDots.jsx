import { Sparkles } from 'lucide-react'

export default function LoadingDots() {
  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] md:max-w-[70%] rounded-2xl rounded-bl-sm p-4 shadow-sm bg-white dark:bg-neutral-900 border border-gray-100 dark:border-neutral-800">
        <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-neutral-400">
          <Sparkles size={16} className="text-blue-500 shrink-0" />
          <span>Thinking</span>
          <span className="flex items-center gap-1">
            <span className="loading-dot inline-block h-1.5 w-1.5 rounded-full bg-blue-500" />
            <span className="loading-dot inline-block h-1.5 w-1.5 rounded-full bg-blue-500" />
            <span className="loading-dot inline-block h-1.5 w-1.5 rounded-full bg-blue-500" />
          </span>
        </div>
      </div>
    </div>
  )
}
