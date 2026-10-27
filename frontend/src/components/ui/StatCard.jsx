// StatCard — one headline number with a label, for summary rows on dashboards.
// Props:
//   label     what the number measures, e.g. "Pairs compared"
//   value     the number or pre-formatted text, e.g. 78 or pct(0.91)
//   hint      optional muted line under the value, e.g. "across 13 files"
//   tone      'neutral' | 'indigo' | 'red' | 'amber' | 'green', or a verdict string (default 'neutral')
//   icon      optional inline <svg> element shown in a tinted square
//   className extra classes for the outer element
import { verdictTone } from '../../lib/colors.js'

const TONES = {
  neutral: { value: 'text-slate-900', icon: 'bg-slate-100 text-slate-600' },
  indigo: { value: 'text-indigo-700', icon: 'bg-indigo-50 text-indigo-600' },
  red: { value: 'text-red-600', icon: 'bg-red-50 text-red-600' },
  amber: { value: 'text-amber-600', icon: 'bg-amber-50 text-amber-600' },
  green: { value: 'text-green-600', icon: 'bg-green-50 text-green-600' },
}

export default function StatCard({ label, value, hint, tone = 'neutral', icon, className = '' }) {
  const style = TONES[tone] ?? TONES[verdictTone(tone)]

  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        {icon && <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${style.icon}`}>{icon}</span>}
      </div>
      <p className={`mt-2 text-3xl font-semibold tracking-tight tabular-nums ${style.value}`}>{value ?? '—'}</p>
      {hint && <p className="mt-1 text-sm text-slate-500">{hint}</p>}
    </div>
  )
}
