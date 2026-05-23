import { useEffect, useState } from 'react'
import { Moon, Sun, Laptop2 } from 'lucide-react'

function getSystemPrefersDark() {
  if (typeof window === 'undefined') return false
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
}

const order = ['dark', 'light', 'system']

export default function ThemeToggle({ className = '' }) {
  const [mode, setMode] = useState('dark') // default dark

  useEffect(() => {
    const saved = localStorage.getItem('theme')
    if (saved === 'light' || saved === 'dark' || saved === 'system') {
      setMode(saved)
      applyTheme(saved)
    } else {
      setMode('dark')
      applyTheme('dark')
    }

    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      if (localStorage.getItem('theme') === 'system') applyTheme('system')
    }
    mq.addEventListener?.('change', handler)
    return () => mq.removeEventListener?.('change', handler)
  }, [])

  const applyTheme = (val) => {
    const root = document.documentElement
    if (val === 'system') {
      const dark = getSystemPrefersDark()
      root.classList.toggle('dark', dark)
    } else {
      root.classList.toggle('dark', val === 'dark')
    }
  }

  const cycle = () => {
    const idx = order.indexOf(mode)
    const next = order[(idx + 1) % order.length]
    setMode(next)
    localStorage.setItem('theme', next)
    applyTheme(next)
  }

  const Icon = mode === 'light' ? Sun : mode === 'dark' ? Moon : Laptop2

  return (
    <button
      onClick={cycle}
      aria-label={`Theme: ${mode}`}
      className={`h-8 w-8 rounded-full border border-gray-200 dark:border-neutral-700 bg-white/70 dark:bg-neutral-900/60 text-gray-800 dark:text-neutral-200 flex items-center justify-center shadow-sm hover:bg-gray-50 dark:hover:bg-neutral-800/70 transition ${className}`}
    >
      <Icon size={16} />
    </button>
  )
}
