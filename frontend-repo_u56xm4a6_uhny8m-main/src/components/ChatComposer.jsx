import { Search, Mic, Send } from 'lucide-react'

export default function ChatComposer({
  query,
  onQueryChange,
  onSend,
  onVoice,
  listening,
  suggestions = [],
}) {
  return (
    <div className="pt-3 pb-1 bg-gradient-to-t from-neutral-50 via-neutral-50/95 to-transparent dark:from-neutral-950 dark:via-neutral-950/95 shrink-0 max-w-4xl mx-auto w-full">
      {/* Input bar */}
      <div className="rounded-2xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-2 shadow-sm hover:shadow-md transition-shadow focus-within:border-gray-300 dark:focus-within:border-neutral-600">
        <div className="flex items-center gap-2">
          <Search size={18} className="text-gray-400 dark:text-neutral-500 ml-2 shrink-0" />
          <input
            id="chat-input"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                onSend()
              }
            }}
            placeholder="What are you shopping for today?"
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-gray-400 dark:placeholder:text-neutral-500 text-gray-900 dark:text-neutral-100 min-w-0 ring-0 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0"
            aria-label="Search for products"
          />
          <button
            onClick={onVoice}
            className={`h-9 w-9 rounded-xl border shrink-0 flex items-center justify-center transition-all active:scale-90 ${
              listening
                ? 'border-blue-300 bg-blue-50 text-blue-600 dark:border-blue-400/40 dark:bg-blue-400/10 dark:text-blue-300 animate-pulse'
                : 'border-gray-200 text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:border-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 dark:hover:bg-neutral-800'
            }`}
            aria-label="Voice input"
          >
            <Mic size={16} />
          </button>
          <button
            onClick={onSend}
            className="h-9 rounded-xl bg-blue-600 text-white px-3 sm:px-4 inline-flex items-center gap-1.5 text-sm font-medium hover:bg-blue-500 active:scale-[0.97] transition-all shrink-0"
            aria-label="Send message"
          >
            <Send size={14} />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </div>

      {/* Quick suggestions */}
      {suggestions.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1.5 sm:gap-2">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => onSend(s)}
              className="rounded-full bg-gray-100 dark:bg-neutral-800 hover:bg-gray-200 dark:hover:bg-neutral-700 text-gray-700 dark:text-neutral-300 text-[11px] sm:text-xs px-2.5 sm:px-3 py-1 sm:py-1.5 transition-colors truncate max-w-[45%] sm:max-w-none active:scale-95"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
