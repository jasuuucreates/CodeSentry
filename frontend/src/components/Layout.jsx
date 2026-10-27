// Layout — the application shell wrapped around every page.
// Props:
//   children  optional content; when omitted the matched child route is rendered through <Outlet />
//
// Wide screens (lg and up): a fixed sidebar on the left and the page content to its right.
// Narrow screens: a top bar with a menu button that slides the same sidebar in as a drawer, so
// there is one navigation component rather than two that could drift apart.
import { useEffect, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { getHealth } from '../api/client.js'

/** Shield (protection) with a magnifier (inspection) — the CodeSentry brand mark. */
function BrandMark({ className = 'h-9 w-9' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path fill="#4f46e5" d="M12 1.8 20.5 5v6.2c0 5.4-3.6 9.8-8.5 11-4.9-1.2-8.5-5.6-8.5-11V5z" />
      <path fill="#6366f1" d="M12 1.8 20.5 5v6.2c0 5.4-3.6 9.8-8.5 11z" opacity="0.55" />
      <circle cx="11.2" cy="10.6" r="3.4" fill="none" stroke="#fff" strokeWidth="1.9" />
      <path d="m13.7 13.1 2.8 2.8" stroke="#fff" strokeWidth="1.9" strokeLinecap="round" />
    </svg>
  )
}

/** Outline icon drawn with the current text colour, so it follows the link's active state. */
function Icon({ children, className = 'h-5 w-5' }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {children}
    </svg>
  )
}

// `match` decides when a link is highlighted. Run results and pair views are opened from the
// dashboard, so the Dashboard link stays active on those pages to show where the user is.
const NAV_SECTIONS = [
  {
    heading: 'Workspace',
    items: [
      {
        to: '/',
        label: 'Dashboard',
        match: (path) => path === '/' || path.startsWith('/runs'),
        icon: (
          <>
            <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" />
            <rect x="13.5" y="3.5" width="7" height="7" rx="1.5" />
            <rect x="3.5" y="13.5" width="7" height="7" rx="1.5" />
            <rect x="13.5" y="13.5" width="7" height="7" rx="1.5" />
          </>
        ),
      },
      {
        to: '/new',
        label: 'New Analysis',
        match: (path) => path.startsWith('/new'),
        icon: (
          <>
            <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
            <path d="M14 3v5h5" />
            <path d="M12 11v6M9 14h6" />
          </>
        ),
      },
    ],
  },
  {
    heading: 'Learn',
    items: [
      {
        to: '/evaluation',
        label: 'Evaluation',
        match: (path) => path.startsWith('/evaluation'),
        icon: (
          <>
            <path d="M4 20h16" />
            <path d="M7 16v-5M12 16V6M17 16v-8" />
          </>
        ),
      },
      {
        to: '/how-it-works',
        label: 'How It Works',
        match: (path) => path.startsWith('/how-it-works'),
        icon: (
          <>
            <path d="m12 3 9 5-9 5-9-5z" />
            <path d="m3 13 9 5 9-5" />
          </>
        ),
      },
      {
        to: '/about',
        label: 'About',
        match: (path) => path.startsWith('/about'),
        icon: (
          <>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 11v5.5M12 7.5h.01" />
          </>
        ),
      },
    ],
  },
]

/** Asks the backend for /api/health once, so the sidebar can say whether the engine is reachable. */
function useServerStatus() {
  const [status, setStatus] = useState({ state: 'checking', version: null })

  useEffect(() => {
    // `active` prevents a state update after unmount (and ignores the first StrictMode run).
    let active = true
    getHealth()
      .then((data) => active && setStatus({ state: 'online', version: data?.version ?? null }))
      .catch(() => active && setStatus({ state: 'offline', version: null }))
    return () => {
      active = false
    }
  }, [])

  return status
}

function ServerStatus() {
  const { state, version } = useServerStatus()
  const dot = { checking: 'bg-slate-300', online: 'bg-green-500', offline: 'bg-red-500' }[state]
  const text = {
    checking: 'Connecting to engine…',
    online: version ? `Engine v${version} online` : 'Engine online',
    offline: 'Engine server offline',
  }[state]

  return (
    <p className="flex items-center gap-2 text-xs text-slate-500" aria-live="polite">
      <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden="true" />
      {text}
    </p>
  )
}

function Sidebar({ pathname, onNavigate }) {
  return (
    <div className="flex h-full flex-col">
      <Link
        to="/"
        onClick={onNavigate}
        className="flex items-center gap-3 border-b border-slate-200 px-5 py-5 focus-visible:outline-offset-[-2px]"
      >
        <BrandMark />
        <span className="min-w-0">
          <span className="block text-lg font-semibold leading-tight tracking-tight text-slate-900">CodeSentry</span>
          <span className="block text-xs text-slate-500">Code Plagiarism Detection</span>
        </span>
      </Link>

      <nav aria-label="Main" className="flex-1 overflow-y-auto px-3 py-5">
        {NAV_SECTIONS.map((section) => (
          <div key={section.heading} className="mb-6 last:mb-0">
            <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              {section.heading}
            </p>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const active = item.match(pathname)
                return (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      onClick={onNavigate}
                      aria-current={active ? 'page' : undefined}
                      className={`group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                        active
                          ? 'bg-indigo-50 text-indigo-700'
                          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                      }`}
                    >
                      {active && (
                        <span className="absolute inset-y-1.5 -left-3 w-1 rounded-r-full bg-indigo-600" aria-hidden="true" />
                      )}
                      <span className={active ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-600'}>
                        <Icon>{item.icon}</Icon>
                      </span>
                      {item.label}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="space-y-2 border-t border-slate-200 px-5 py-4">
        <ServerStatus />
        <p className="text-xs font-medium text-slate-500">MUJ · CSE · Software Engineering Lab</p>
      </div>
    </div>
  )
}

export default function Layout({ children }) {
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  // A newly opened page should start at the top, not at the scroll position of the previous page.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  // Let keyboard users close the mobile drawer with Escape.
  useEffect(() => {
    if (!menuOpen) return undefined
    const onKey = (event) => {
      if (event.key === 'Escape') setMenuOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [menuOpen])

  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="relative min-h-screen bg-slate-50">
      {/* The sidebar is position:fixed, so a full-page screenshot shows it only at the top. This
          static strip continues its background and border down the whole page. */}
      <div className="pointer-events-none absolute inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block" aria-hidden="true" />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[60] focus:rounded-md focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-indigo-700 focus:shadow"
      >
        Skip to content
      </a>

      {/* Backdrop behind the drawer on narrow screens; clicking it closes the menu. */}
      {menuOpen && (
        <div className="fixed inset-0 z-40 bg-slate-900/40 lg:hidden" onClick={closeMenu} aria-hidden="true" />
      )}

      <aside
        id="app-sidebar"
        className={`fixed inset-y-0 left-0 z-50 w-64 border-r border-slate-200 bg-white transition-transform duration-200 ease-out lg:translate-x-0 ${
          menuOpen ? 'translate-x-0 shadow-xl' : '-translate-x-full'
        }`}
      >
        <Sidebar pathname={pathname} onNavigate={closeMenu} />
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-slate-200 bg-white/95 px-4 backdrop-blur lg:hidden">
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            aria-controls="app-sidebar"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            className="-ml-1 rounded-md p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <Icon className="h-6 w-6">{menuOpen ? <path d="M6 6l12 12M18 6 6 18" /> : <path d="M4 6h16M4 12h16M4 18h16" />}</Icon>
          </button>
          <Link to="/" className="flex items-center gap-2 rounded-md">
            <BrandMark className="h-7 w-7" />
            <span className="text-base font-semibold tracking-tight text-slate-900">CodeSentry</span>
          </Link>
        </header>

        <main id="main-content" className="mx-auto w-full max-w-[1280px] px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  )
}
