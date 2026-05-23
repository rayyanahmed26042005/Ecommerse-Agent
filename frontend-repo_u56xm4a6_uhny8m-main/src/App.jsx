import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Menu, Sparkles, SlidersHorizontal } from 'lucide-react'
import ThemeToggle from './components/ThemeToggle'
import Sidebar from './components/Sidebar'
import ChatMessage from './components/ChatMessage'
import ChatComposer from './components/ChatComposer'
import CompareBar from './components/CompareBar'
import AchievementToast from './components/AchievementToast'
import ApiErrorBanner from './components/ApiErrorBanner'
import LoadingDots from './components/LoadingDots'
import { enrichProduct, enrichProducts } from './utils/enrichProduct'

/* ── Mock products for initial state ────────────────── */
function buildMockProducts() {
  return [
    {
      title: 'Aurora Pro Wireless Earbuds',
      category: 'Audio',
      price: 129,
      rating: 4.7,
      image: 'https://images.unsplash.com/photo-1518443895914-06e0f2eeaad6?q=80&w=1200&auto=format&fit=crop',
      specs: ['ANC', 'Bluetooth 5.3', 'IPX4', '28h battery'],
      retailers: [{ name: 'Amazon', price: 129, best: true }, { name: 'BestBuy', price: 139 }],
    },
    {
      title: 'Nimbus Lite Vacuum',
      category: 'Home',
      price: 179,
      rating: 4.5,
      image: 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?q=80&w=1200&auto=format&fit=crop',
      specs: ['Quiet', 'HEPA', 'Cordless', '40min'],
      retailers: [{ name: 'Target', price: 179, best: true }, { name: 'Walmart', price: 189 }],
    },
    {
      title: 'Luma Desk Lamp',
      category: 'Office',
      price: 89,
      rating: 4.6,
      image: 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?q=80&w=1200&auto=format&fit=crop',
      specs: ['Dimmable', 'USB-C', 'CRI 95', 'Adjustable'],
      retailers: [{ name: 'Ikea', price: 89, best: true }, { name: 'Amazon', price: 95 }],
    },
    {
      title: 'Voyage Travel Kit',
      category: 'Travel',
      price: 49,
      rating: 4.4,
      image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop',
      specs: ['TSA-ready', 'Compact', 'Organizer'],
      retailers: [{ name: 'Amazon', price: 49, best: true }],
    },
  ]
}

/* ══════════════════════════════════════════════════════ */
/*                       APP                            */
/* ══════════════════════════════════════════════════════ */
export default function App() {
  // ── Config ──
  const baseUrl = (import.meta.env.VITE_BACKEND_URL || '').replace(/\/$/, '')
  const chatSync = import.meta.env.VITE_CHAT_SYNC !== 'false'

  // ── State ──
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [apiError, setApiError] = useState(null)
  const [sidebarDataLoading, setSidebarDataLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hi! I'm your shopping expert. Tell me what you're looking for — I'll summarize the best options and show top picks.",
      summary: 'Premium overview tailored to your goals',
      insights: [
        "I'll give you a quick summary first, then details on demand.",
        "You'll see prices across retailers with best price highlighted.",
        'Tap compare to line up specs instantly.',
      ],
      suggestions: buildMockProducts(),
    },
  ])
  const [trending, setTrending] = useState([])
  const [essentials, setEssentials] = useState([])
  const [picks, setPicks] = useState([])
  const [selections, setSelections] = useState([])
  const [showSummary, setShowSummary] = useState(true)
  const [listening, setListening] = useState(false)
  const [achievement, setAchievement] = useState(null)
  const chatEndRef = useRef(null)
  const userId = 'demo-user-1'

  // ── Fetch sidebar data ──
  useEffect(() => {
    const load = async () => {
      setSidebarDataLoading(true)
      try {
        const health = await fetch(`${baseUrl}/health`)
        if (!health.ok) {
          setApiError('Backend not reachable. Start API on port 8000 and restart npm run dev.')
          setSidebarDataLoading(false)
          return
        }
        setApiError(null)
        const [t, e, p] = await Promise.all([
          fetch(`${baseUrl}/api/trending`),
          fetch(`${baseUrl}/api/essentials`),
          fetch(`${baseUrl}/api/picks/${userId}`),
        ])
        if (t.ok) setTrending(enrichProducts(await t.json()))
        if (e.ok) setEssentials(enrichProducts(await e.json()))
        if (p.ok) setPicks(enrichProducts(await p.json()))
      } catch (err) {
        console.error('Backend connection failed:', err)
        setApiError(
          'Cannot reach backend. Run: uvicorn on :8000, then restart frontend (npm run dev).'
        )
      } finally {
        setSidebarDataLoading(false)
      }
    }
    load()
  }, [baseUrl])

  // ── Auto-scroll chat ──
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // ── Derived data ──
  const quickActions = useMemo(
    () => [
      'Best earbuds under $150',
      'Quietest vacuum for apartments',
      'Sleek desk lamp',
      'Travel essentials kit',
    ],
    []
  )
  const smartSearch = useMemo(() => trending.slice(0, 4).map((t) => t.title), [trending])

  // ── Task polling ──
  const pollTaskResult = async (taskId, _message, maxAttempts = 60) => {
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 1500))
      const res = await fetch(`${baseUrl}/api/chat/tasks/${taskId}`)
      if (!res.ok) continue
      const task = await res.json()
      if (task.status === 'completed' && task.result) return task.result
      if (task.status === 'failed') throw new Error(task.error || 'Agent task failed')
    }
    throw new Error('Request timed out')
  }

  // ── Send chat message ──
  const sendMessage = useCallback(
    async (text) => {
      const message = (text ?? query).trim()
      if (!message) return
      setQuery('')
      setLoading(true)
      setMessages((prev) => [...prev, { role: 'user', content: message }])
      try {
        const chatUrl = `${baseUrl}/api/chat${chatSync ? '?sync=true' : ''}`
        const res = await fetch(chatUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, message }),
        })
        if (!res.ok) {
          const errText = await res.text().catch(() => '')
          throw new Error(`Backend error ${res.status}: ${errText.slice(0, 120)}`)
        }
        let data = await res.json().catch(() => ({}))
        if (data.task_id && data.status === 'processing') {
          data = await pollTaskResult(data.task_id, message)
        }
        const assistantMsg = {
          role: 'assistant',
          content: 'Here are refined picks tailored to your request.',
          summary: data.summary || 'Top options based on value, reliability, and user satisfaction.',
          suggestions: enrichProducts(data.suggestions),
          insights: data.insights || [],
        }
        if (!assistantMsg.suggestions.length) {
          throw new Error('Backend returned no products. Check GEMINI_API_KEY in backend/.env')
        }
        setApiError(null)
        setMessages((prev) => [...prev, assistantMsg])
        if ((assistantMsg.suggestions || []).length >= 2) {
          setAchievement({ title: 'Smart Move', desc: 'Compared multiple options for best value.' })
          setTimeout(() => setAchievement(null), 2600)
        }
      } catch (e) {
        console.error('Chat failed:', e)
        const msg = e?.message || 'Unknown error'
        setApiError(msg)
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Could not reach the shopping agent: ${msg}`, suggestions: [] },
        ])
      } finally {
        setLoading(false)
      }
    },
    [query, baseUrl, chatSync]
  )

  // ── Selection / compare ──
  const toggleSelect = useCallback((title) => {
    setSelections((sel) => (sel.includes(title) ? sel.filter((t) => t !== title) : [...sel, title]))
  }, [])

  const compareItems = useCallback(() => {
    const pool = messages.flatMap((m) => m.suggestions || [])
    const selected = pool.filter((p) => selections.includes(p.title)).map(enrichProduct)
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: `Comparing ${selections.length} items: ${selections.join(', ')}. Prioritizing value, reliability, and warranty coverage.`,
        suggestions: selected.length ? selected : buildMockProducts(),
      },
    ])
    setSelections([])
  }, [messages, selections])

  // ── Voice ──
  const startVoice = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      return alert('Voice input not supported in this environment.')
    }
    try {
      setListening(true)
      setTimeout(() => {
        setListening(false)
        setQuery((q) => q || 'Find premium noise‑cancelling earbuds for commuting')
      }, 1500)
      await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      setListening(false)
    }
  }, [])

  // ── Composer suggestions ──
  const composerSuggestions = useMemo(
    () => [...quickActions.slice(0, 2), ...smartSearch.slice(0, 2)],
    [quickActions, smartSearch]
  )

  /* ══════════════════════════════════════════════════ */
  /*                     RENDER                        */
  /* ══════════════════════════════════════════════════ */
  return (
    <div className="h-screen surface text-basecolor transition-colors overflow-hidden">
      {/* API error banner */}
      <ApiErrorBanner error={apiError} />

      {/* Top bar — hamburger (mobile) + theme toggle (all screens) */}
      <div className="fixed top-0 left-0 right-0 z-50 pointer-events-none">
        <div className="md:ml-[280px] lg:ml-[300px] flex items-center justify-between px-3 py-2.5">
          {/* Hamburger (mobile only) */}
          <button
            onClick={() => setSidebarOpen((s) => !s)}
            className="md:hidden pointer-events-auto h-9 w-9 rounded-xl border border-gray-200 dark:border-neutral-700 bg-white/80 dark:bg-neutral-900/80 backdrop-blur text-gray-700 dark:text-neutral-200 flex items-center justify-center shadow-sm hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors active:scale-90"
            aria-label="Open sidebar"
          >
            <Menu size={18} />
          </button>
          {/* Spacer for desktop */}
          <div className="hidden md:block" />
          {/* Theme toggle */}
          <div className="pointer-events-auto">
            <ThemeToggle />
          </div>
        </div>
      </div>

      {/* Sidebar — fixed, outside normal flow */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        quickActions={quickActions}
        trending={trending}
        essentials={essentials}
        picks={picks}
        onSendMessage={sendMessage}
        isDataLoading={sidebarDataLoading}
      />

      {/* Main content — offset by sidebar width on desktop */}
      <main
        className="h-full md:ml-[280px] lg:ml-[300px] overflow-hidden flex flex-col"
        role="main"
      >
        {/* Header */}
        <div className="shrink-0 px-4 sm:px-6 md:px-8 pt-14 md:pt-14 pb-2">
          <div className="max-w-4xl mx-auto">
            <div className="hidden md:block">
              <h1 className="text-xl font-semibold tracking-tight text-gray-900 dark:text-neutral-100">
                Your personal shopping expert
              </h1>
              <p className="text-sm text-gray-500 dark:text-neutral-400 mt-0.5">
                Structured, premium recommendations — facts first, opinions clearly marked.
              </p>
            </div>

            {/* Smart search suggestions (desktop) */}
            {smartSearch.length > 0 && (
              <div className="mt-3 hidden md:flex flex-wrap gap-2">
                {smartSearch.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(s)}
                    className="rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 px-3 py-1.5 text-xs text-gray-600 dark:text-neutral-300 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors active:scale-95"
                  >
                    <SlidersHorizontal className="inline mr-1.5" size={11} />
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Conversation */}
        <div
          className="flex-1 overflow-y-auto px-4 sm:px-6 md:px-8 pb-2"
          role="log"
          aria-label="Chat messages"
          aria-live="polite"
        >
          <div className="max-w-4xl mx-auto space-y-5">
            {messages.map((m, idx) => (
              <ChatMessage
                key={idx}
                message={m}
                showSummary={showSummary}
                onToggleSummary={() => setShowSummary((s) => !s)}
                selections={selections}
                onToggleSelect={toggleSelect}
                onSendMessage={sendMessage}
              />
            ))}
            {loading && <LoadingDots />}
            <div ref={chatEndRef} className="h-1" />
          </div>
        </div>

        {/* Composer — pinned at bottom, never scrolls */}
        <div className="shrink-0 px-4 sm:px-6 md:px-8 pb-2">
          <ChatComposer
            query={query}
            onQueryChange={setQuery}
            onSend={sendMessage}
            onVoice={startVoice}
            listening={listening}
            suggestions={composerSuggestions}
          />
        </div>
      </main>

      {/* Compare bar */}
      <CompareBar
        count={selections.length}
        onCompare={compareItems}
        onClear={() => setSelections([])}
      />

      {/* Achievement toast */}
      <AchievementToast achievement={achievement} />
    </div>
  )
}
