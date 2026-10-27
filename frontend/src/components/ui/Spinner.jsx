// Spinner — animated loading indicator.
// Props:
//   size      'sm' | 'md' | 'lg'  (default 'md')
//   label     optional visible text next to the spinner; screen readers always hear it (or "Loading")
//   center    boolean — centre the spinner in a padded block, for whole-page or whole-card loading
//   inherit   boolean — use the surrounding text colour instead of indigo (e.g. inside a Button)
//   className extra classes for the outer element

const SIZES = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-10 w-10',
}

export default function Spinner({ size = 'md', label, center = false, inherit = false, className = '' }) {
  const spinner = (
    <span role="status" className={`inline-flex items-center gap-3 ${center ? '' : className}`}>
      <svg
        className={`${SIZES[size] ?? SIZES.md} shrink-0 animate-spin ${inherit ? '' : 'text-indigo-600'}`}
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="9.5" stroke="currentColor" strokeWidth="3" opacity="0.2" />
        <path d="M21.5 12A9.5 9.5 0 0 0 12 2.5" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
      {label ? (
        <span className={`text-sm ${inherit ? '' : 'text-slate-600'}`}>{label}</span>
      ) : (
        <span className="sr-only">Loading</span>
      )}
    </span>
  )

  if (!center) return spinner
  return <div className={`flex items-center justify-center py-16 ${className}`}>{spinner}</div>
}
