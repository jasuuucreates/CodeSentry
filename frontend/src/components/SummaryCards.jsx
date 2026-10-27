// SummaryCards — the headline numbers of one analysis run, as a row of StatCards.
// Props:
//   run   the GET /api/runs/:id response: RunSummary fields (file_count, pair_count, high, moderate,
//         low, max_score, mean_score, elapsed_ms) plus files, pairs and config
//
// Red, amber and green are used only for the three verdict counts and for the highest score (coloured by
// the verdict of that pair), so colour on this page always means "how suspicious".
import StatCard from './ui/StatCard.jsx'
import { duration, pct } from '../lib/format.js'

const LANGUAGE_NAMES = { python: 'Python', c: 'C' }

function Icon({ children }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
      {children}
    </svg>
  )
}

const ICONS = {
  files: (
    <Icon>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5M9 13h6M9 17h4" />
    </Icon>
  ),
  pairs: (
    <Icon>
      <path d="M7 7h11l-3-3M17 17H6l3 3" />
    </Icon>
  ),
  high: (
    <Icon>
      <path d="M12 3 2.5 20h19z" />
      <path d="M12 10v4.5M12 17.5h.01" />
    </Icon>
  ),
  moderate: (
    <Icon>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.5v5M12 16h.01" />
    </Icon>
  ),
  low: (
    <Icon>
      <circle cx="12" cy="12" r="9" />
      <path d="m8 12.5 2.8 2.8L16 10" />
    </Icon>
  ),
  max: (
    <Icon>
      <path d="M4 20h16M7 16l4-5 3 3 5-7" />
    </Icon>
  ),
  mean: (
    <Icon>
      <path d="M4 20h16M4 12h16" strokeDasharray="2 3" />
      <path d="M6 16V9M12 16V5M18 16v-4" />
    </Icon>
  ),
  time: (
    <Icon>
      <circle cx="12" cy="13" r="8" />
      <path d="M12 9v4l2.5 2.5M10 2h4" />
    </Icon>
  ),
}

function isNumber(x) {
  return typeof x === 'number' && Number.isFinite(x)
}

export default function SummaryCards({ run }) {
  const files = run?.files ?? []
  const pairs = run?.pairs ?? []
  const config = run?.config ?? {}
  const fileCount = run?.file_count ?? files.length
  const pairCount = run?.pair_count ?? pairs.length
  const high = config.high_threshold ?? 0.75
  const moderate = config.moderate_threshold ?? 0.5

  // "11 Python · 2 C" tells the reader at a glance why some pairs were never compared.
  const languageCounts = files.reduce((acc, file) => {
    acc[file.language] = (acc[file.language] ?? 0) + 1
    return acc
  }, {})
  const languages = Object.entries(languageCounts)
    .map(([language, n]) => `${n} ${LANGUAGE_NAMES[language] ?? language}`)
    .join(' · ')

  const share = (n) => (pairCount > 0 && isNumber(n) ? `${Math.round((n / pairCount) * 100)}% of pairs` : 'no pairs compared')

  const top = pairs.reduce((best, pair) => (isNumber(pair.scores?.fused) && (!best || pair.scores.fused > best.scores.fused) ? pair : best), null)
  const topNames = top ? `${top.a_name} vs ${top.b_name}` : null

  const cards = [
    { key: 'files', label: 'Files analysed', value: fileCount, hint: languages || 'no files' },
    { key: 'pairs', label: 'Pairs compared', value: pairCount, hint: 'same-language pairs only' },
    { key: 'high', label: 'High similarity', value: run?.high ?? 0, tone: 'red', hint: `${pct(high, 0)} or above · ${share(run?.high)}` },
    {
      key: 'moderate',
      label: 'Moderate similarity',
      value: run?.moderate ?? 0,
      tone: 'amber',
      hint: `${pct(moderate, 0)} to ${pct(high, 0)} · ${share(run?.moderate)}`,
    },
    { key: 'low', label: 'Low similarity', value: run?.low ?? 0, tone: 'green', hint: `below ${pct(moderate, 0)} · ${share(run?.low)}` },
    {
      key: 'max',
      label: 'Highest score',
      value: pct(run?.max_score),
      tone: top?.verdict ?? 'neutral',
      hint: topNames ? (
        <span className="block truncate" title={topNames}>
          {topNames}
        </span>
      ) : (
        'no pairs compared'
      ),
    },
    { key: 'mean', label: 'Mean score', value: pct(run?.mean_score), hint: 'average fused score of all pairs' },
    {
      key: 'time',
      label: 'Analysis time',
      value: duration(run?.elapsed_ms),
      hint: isNumber(config.k) ? `k = ${config.k} · w = ${config.w} · weights ${config.w_token} / ${config.w_structure}` : null,
    },
  ]

  return (
    <section aria-label="Run summary" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <StatCard key={card.key} label={card.label} value={card.value} hint={card.hint} tone={card.tone} icon={ICONS[card.key]} className="min-w-0" />
      ))}
    </section>
  )
}
