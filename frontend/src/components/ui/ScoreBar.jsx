// ScoreBar — horizontal bar for a similarity score between 0 and 1.
// Props:
//   value     score in [0, 1]; null/undefined draws an empty track and "—" (e.g. no structure score)
//   label     optional text naming the score, e.g. "Token (winnowing)"
//   showValue boolean — print the percentage (default true)
//   inline    boolean — bar and percentage on one row with no label line, for table cells (default false)
//   size      'sm' | 'md' track height (default 'md')
//   color     optional CSS colour that overrides the verdict colouring (e.g. palette.indigo for metrics)
//   high      score at or above which the bar is red (default 0.75, the engine's high threshold)
//   moderate  score at or above which the bar is amber (default 0.50); below it the bar is green
//   className extra classes for the outer element
import { pct } from '../../lib/format.js'

const HEIGHTS = { sm: 'h-1.5', md: 'h-2.5' }

export default function ScoreBar({
  value,
  label,
  showValue = true,
  inline = false,
  size = 'md',
  color,
  high = 0.75,
  moderate = 0.5,
  className = '',
}) {
  const hasValue = typeof value === 'number' && Number.isFinite(value)
  const clamped = hasValue ? Math.min(1, Math.max(0, value)) : 0

  // Same bands as the verdict badges, so a red bar and a "High" badge always mean the same thing.
  let band = 'bg-green-500'
  if (clamped >= high) band = 'bg-red-500'
  else if (clamped >= moderate) band = 'bg-amber-500'

  const track = (
    <div
      role="meter"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={hasValue ? Math.round(clamped * 100) : undefined}
      aria-label={typeof label === 'string' ? label : 'Similarity score'}
      className={`w-full overflow-hidden rounded-full bg-slate-100 ${HEIGHTS[size] ?? HEIGHTS.md}`}
    >
      {hasValue && (
        <div
          className={`h-full rounded-full transition-[width] duration-500 ease-out ${color ? '' : band}`}
          style={{ width: `${clamped * 100}%`, backgroundColor: color }}
        />
      )}
    </div>
  )

  const number = <span className="font-medium text-slate-900 tabular-nums">{pct(hasValue ? value : null)}</span>

  if (inline) {
    return (
      <div className={`flex items-center gap-3 text-sm ${className}`}>
        <div className="min-w-16 flex-1">{track}</div>
        {showValue && <span className="w-14 shrink-0 text-right">{number}</span>}
      </div>
    )
  }

  return (
    <div className={className}>
      {(label || showValue) && (
        <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
          <span className="min-w-0 truncate text-slate-600">{label}</span>
          {showValue && number}
        </div>
      )}
      {track}
    </div>
  )
}
