// PageHeader — title block at the top of every page; also sets the browser tab title.
// Props:
//   title     page heading (string recommended; a string also becomes "<title> · CodeSentry" in the tab)
//   subtitle  optional description under the heading
//   actions   optional element(s) shown on the right (buttons); wraps below the title on narrow screens
//   eyebrow   optional small uppercase label above the title (e.g. a run name)
//   back      optional { to, label } — renders a "back" link above the title, e.g. { to: '/', label: 'Dashboard' }
import { Link } from 'react-router-dom'

export default function PageHeader({ title, subtitle, actions, eyebrow, back }) {
  return (
    <header className="mb-8 flex flex-col gap-4 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
      {/* React 19 hoists <title> into <head>, so each page names its own browser tab. */}
      {typeof title === 'string' && <title>{`${title} · CodeSentry`}</title>}
      <div className="min-w-0">
        {back && (
          <Link
            to={back.to}
            className="mb-3 inline-flex items-center gap-1 rounded text-sm font-medium text-slate-500 hover:text-indigo-600"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
              <path d="m15 18-6-6 6-6" />
            </svg>
            {back.label}
          </Link>
        )}
        {eyebrow && <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">{eyebrow}</p>}
        <h1 className={`text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl ${eyebrow ? 'mt-1' : ''}`}>{title}</h1>
        {subtitle && <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2 sm:shrink-0">{actions}</div>}
    </header>
  )
}
