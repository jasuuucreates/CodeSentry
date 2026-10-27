// Button — the one button style used across the app.
// Props:
//   variant   'primary' | 'secondary' | 'danger' | 'ghost'  (default 'primary')
//   size      'sm' | 'md' | 'lg'  (default 'md')
//   loading   boolean — shows a spinner and disables the button so a request cannot be sent twice
//   disabled  boolean
//   icon      optional element (e.g. an inline <svg>) shown before the text; replaced by the spinner while loading
//   to        optional router path — renders a react-router <Link> styled as a button (ignored while disabled/loading)
//   type      button type (default 'button', so a Button inside a form never submits by accident)
//   className extra classes; every other prop (onClick, aria-*, form, ...) is passed to the element
import { Link } from 'react-router-dom'
import Spinner from './Spinner.jsx'

const BASE =
  'inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium ' +
  'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ' +
  'disabled:cursor-not-allowed disabled:opacity-60'

const VARIANTS = {
  primary:
    'bg-indigo-600 text-white shadow-sm hover:bg-indigo-700 active:bg-indigo-800 focus-visible:ring-indigo-500 disabled:hover:bg-indigo-600',
  secondary:
    'border border-slate-300 bg-white text-slate-700 shadow-sm hover:bg-slate-50 hover:text-slate-900 active:bg-slate-100 focus-visible:ring-indigo-500 disabled:hover:bg-white',
  danger:
    'bg-red-600 text-white shadow-sm hover:bg-red-700 active:bg-red-800 focus-visible:ring-red-500 disabled:hover:bg-red-600',
  ghost:
    'text-slate-600 hover:bg-slate-100 hover:text-slate-900 active:bg-slate-200 focus-visible:ring-indigo-500 disabled:hover:bg-transparent',
}

const SIZES = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-base',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  to,
  type = 'button',
  className = '',
  children,
  ...rest
}) {
  const classes = `${BASE} ${VARIANTS[variant] ?? VARIANTS.primary} ${SIZES[size] ?? SIZES.md} ${className}`
  const content = (
    <>
      {loading ? <Spinner size="sm" inherit /> : icon}
      {children}
    </>
  )

  // A link cannot be disabled in HTML, so a disabled or busy link button falls back to a real
  // disabled <button> below.
  if (to && !disabled && !loading) {
    return (
      <Link to={to} className={classes} {...rest}>
        {content}
      </Link>
    )
  }

  return (
    <button type={type} className={classes} disabled={disabled || loading} aria-busy={loading || undefined} {...rest}>
      {content}
    </button>
  )
}
