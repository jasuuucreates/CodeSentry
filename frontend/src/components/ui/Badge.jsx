// Badge — small rounded label, mainly for plagiarism verdicts.
// Props:
//   tone      'red' | 'amber' | 'green' | 'indigo' | 'neutral', OR a verdict string
//             ('High' -> red, 'Moderate' -> amber, 'Low' -> green); anything else -> neutral
//   dot       boolean — show a small coloured dot before the text
//   className extra classes
//   children  badge text
// Example: <Badge tone={pair.verdict}>{pair.verdict}</Badge>
import { verdictTone } from '../../lib/colors.js'

const TONES = {
  red: { badge: 'bg-red-50 text-red-700 ring-red-600/20', dot: 'bg-red-500' },
  amber: { badge: 'bg-amber-50 text-amber-800 ring-amber-600/25', dot: 'bg-amber-500' },
  green: { badge: 'bg-green-50 text-green-700 ring-green-600/20', dot: 'bg-green-500' },
  indigo: { badge: 'bg-indigo-50 text-indigo-700 ring-indigo-600/20', dot: 'bg-indigo-500' },
  neutral: { badge: 'bg-slate-100 text-slate-700 ring-slate-500/20', dot: 'bg-slate-400' },
}

export default function Badge({ tone = 'neutral', dot = false, className = '', children }) {
  const style = TONES[tone] ?? TONES[verdictTone(tone)]

  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${style.badge} ${className}`}
    >
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} aria-hidden="true" />}
      {children}
    </span>
  )
}
