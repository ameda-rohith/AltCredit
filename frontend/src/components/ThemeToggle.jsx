import { useState } from 'react'
import { Icon } from './ui'

const KEY = 'altcredit-theme'

export function ThemeToggle({ className = '' }) {
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || 'light')
  const flip = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    const root = document.documentElement
    // brief class so the whole surface cross-fades instead of snapping
    root.classList.add('theme-anim')
    root.dataset.theme = next
    setTheme(next)
    document.querySelector('meta[name=theme-color]')?.setAttribute('content', next === 'dark' ? '#1c1f1e' : '#e6ebf2')
    try { localStorage.setItem(KEY, next) } catch { /* private mode */ }
    setTimeout(() => root.classList.remove('theme-anim'), 500)
  }
  return (
    <button type="button" className={`icon-btn theme-toggle ${className}`} onClick={flip} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`} title={theme === 'dark' ? 'Light theme' : 'Dark theme'}>
      <span key={theme} className="theme-ico"><Icon name={theme === 'dark' ? 'light_mode' : 'dark_mode'} /></span>
    </button>
  )
}
