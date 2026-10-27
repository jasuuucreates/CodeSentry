// PairsTable — every compared pair of a run, ranked by fused score, with filtering, search and sorting.
// Props:
//   pairs   run.pairs — PairResult objects (contract section 6), without source text
//   runId   id of the run, used to build each "Compare" link
//   config  run.config — its thresholds colour the fused-score bars exactly like the verdict badges
//
// "Rank" is fixed by the fused score (1 = most similar pair of the run), so a pair keeps its rank while
// the user sorts by another column or filters, and can still be talked about as "pair number 3".
// Only 50 rows are drawn at first: a 200-file class produces ~20,000 pairs, and rendering them all
// at once would freeze the page for no benefit — the suspicious pairs are at the top anyway.
import { useMemo, useState } from 'react'
import Badge from './ui/Badge.jsx'
import Button from './ui/Button.jsx'
import EmptyState from './ui/EmptyState.jsx'
import ScoreBar from './ui/ScoreBar.jsx'
import { pct } from '../lib/format.js'

const PAGE_SIZE = 50
const VERDICTS = ['High', 'Moderate', 'Low']
const VERDICT_ORDER = { High: 3, Moderate: 2, Low: 1 }
const LANGUAGE_NAMES = { python: 'Python', c: 'C' }
const CHIP_DOTS = { All: 'bg-slate-400', High: 'bg-red-500', Moderate: 'bg-amber-500', Low: 'bg-green-500' }

// `firstDirection` is the direction a column sorts in when first clicked: scores start with the most
// similar pair, names start from A.
const COLUMNS = [
  { key: 'rank', label: 'Rank', value: (p) => p.rank, firstDirection: 'asc' },
  { key: 'a', label: 'File A', value: (p) => p.a_name, firstDirection: 'asc' },
  { key: 'b', label: 'File B', value: (p) => p.b_name, firstDirection: 'asc' },
  { key: 'language', label: 'Language', value: (p) => p.language, firstDirection: 'asc' },
  { key: 'fused', label: 'Fused score', value: (p) => p.scores?.fused, firstDirection: 'desc' },
  { key: 'token', label: 'Token', value: (p) => p.scores?.token, firstDirection: 'desc', numeric: true },
  { key: 'structure', label: 'Structure', value: (p) => p.scores?.structure, firstDirection: 'desc', numeric: true },
  // Shown only when the server has a trained model (scores.ml_probability present).
  { key: 'ml', label: 'ML', value: (p) => p.scores?.ml_probability, firstDirection: 'desc', numeric: true, optional: true },
  { key: 'verdict', label: 'Verdict', value: (p) => VERDICT_ORDER[p.verdict], firstDirection: 'desc' },
]

// Numeric collation sorts "student_2" before "student_10", the way a person would.
const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' })

function isMissing(x) {
  return x === null || x === undefined || (typeof x === 'number' && !Number.isFinite(x))
}

/** Comparator for a column. Missing values (e.g. no structure score) always sink to the bottom. */
function comparatorFor(column, direction) {
  const sign = direction === 'asc' ? 1 : -1
  return (x, y) => {
    const a = column.value(x)
    const b = column.value(y)
    if (isMissing(a) || isMissing(b)) {
      if (isMissing(a) && isMissing(b)) return x.rank - y.rank
      return isMissing(a) ? 1 : -1
    }
    const diff = typeof a === 'string' ? collator.compare(a, b) : a - b
    return diff !== 0 ? diff * sign : x.rank - y.rank
  }
}

function SortIcon({ direction }) {
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 shrink-0" fill="currentColor" aria-hidden="true">
      <path d="M8 3 11 7H5z" className={direction === 'asc' ? 'text-indigo-600' : direction ? 'opacity-20' : 'opacity-40'} />
      <path d="M8 13 5 9h6z" className={direction === 'desc' ? 'text-indigo-600' : direction ? 'opacity-20' : 'opacity-40'} />
    </svg>
  )
}

function FilterChip({ label, count, selected, onClick }) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={`inline-flex h-8 items-center gap-2 rounded-full border px-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-1 ${
        selected
          ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
          : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900'
      }`}
    >
      <span className={`h-2 w-2 rounded-full ${CHIP_DOTS[label]}`} aria-hidden="true" />
      {label}
      <span
        className={`rounded-full px-1.5 text-xs tabular-nums ${selected ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-600'}`}
      >
        {count}
      </span>
    </button>
  )
}

function FileName({ name }) {
  return (
    <span className="block max-w-[15rem] truncate font-mono text-[13px] text-slate-900" title={name}>
      {name}
    </span>
  )
}

export default function PairsTable({ pairs = [], runId, config }) {
  const [verdict, setVerdict] = useState('All')
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState({ key: 'rank', direction: 'asc' })
  const [visible, setVisible] = useState(PAGE_SIZE)

  const high = config?.high_threshold ?? 0.75
  const moderate = config?.moderate_threshold ?? 0.5
  const hasModel = pairs.some((p) => typeof p.scores?.ml_probability === 'number')
  const columns = hasModel ? COLUMNS : COLUMNS.filter((c) => !c.optional)

  // The API already sorts by fused score; sorting again keeps the ranks correct even if it did not.
  const ranked = useMemo(
    () =>
      [...pairs]
        .sort((x, y) => (y.scores?.fused ?? -1) - (x.scores?.fused ?? -1))
        .map((pair, index) => ({ ...pair, rank: index + 1 })),
    [pairs],
  )

  const needle = query.trim().toLowerCase()
  const searched = useMemo(
    () =>
      needle
        ? ranked.filter((p) => String(p.a_name).toLowerCase().includes(needle) || String(p.b_name).toLowerCase().includes(needle))
        : ranked,
    [ranked, needle],
  )

  // Chip counts follow the search box, so a chip never promises rows that the search then hides.
  const counts = useMemo(() => {
    const result = { All: searched.length, High: 0, Moderate: 0, Low: 0 }
    for (const pair of searched) if (pair.verdict in result) result[pair.verdict] += 1
    return result
  }, [searched])

  const sorted = useMemo(() => {
    const filtered = verdict === 'All' ? searched : searched.filter((p) => p.verdict === verdict)
    const column = COLUMNS.find((c) => c.key === sort.key) ?? COLUMNS[0]
    return [...filtered].sort(comparatorFor(column, sort.direction))
  }, [searched, verdict, sort])

  const rows = sorted.slice(0, visible)
  const remaining = sorted.length - rows.length
  const filtersActive = verdict !== 'All' || needle !== ''

  // Any change to what is listed starts again from the first page of rows.
  const changeVerdict = (next) => {
    setVerdict(next)
    setVisible(PAGE_SIZE)
  }
  const changeQuery = (next) => {
    setQuery(next)
    setVisible(PAGE_SIZE)
  }
  const changeSort = (column) => {
    setSort((current) =>
      current.key === column.key
        ? { key: column.key, direction: current.direction === 'asc' ? 'desc' : 'asc' }
        : { key: column.key, direction: column.firstDirection },
    )
    setVisible(PAGE_SIZE)
  }
  const clearFilters = () => {
    changeVerdict('All')
    setQuery('')
  }

  if (pairs.length === 0) {
    return (
      <EmptyState
        className="m-6"
        title="No pairs were compared"
        description="CodeSentry compares only files written in the same language, and skips files that could not be tokenized. No pair in this run met both conditions."
      />
    )
  }

  return (
    <div>
      <div className="flex flex-col gap-3 border-b border-slate-200 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div role="group" aria-label="Filter pairs by verdict" className="flex flex-wrap gap-2">
          {['All', ...VERDICTS].map((label) => (
            <FilterChip key={label} label={label} count={counts[label]} selected={verdict === label} onClick={() => changeVerdict(label)} />
          ))}
        </div>
        <div className="relative w-full lg:w-72">
          <label htmlFor="pairs-search" className="sr-only">
            Search pairs by file name
          </label>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true">
            <circle cx="11" cy="11" r="6.5" />
            <path d="m16 16 4.5 4.5" />
          </svg>
          <input
            id="pairs-search"
            type="search"
            value={query}
            onChange={(event) => changeQuery(event.target.value)}
            placeholder="Search file names"
            autoComplete="off"
            className="h-9 w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
          />
        </div>
      </div>

      {sorted.length === 0 ? (
        <EmptyState
          className="m-6"
          title="No pairs match these filters"
          description={needle ? `No ${verdict === 'All' ? '' : `${verdict} `}pair involves a file whose name contains “${query.trim()}”.` : `This run has no ${verdict} pairs.`}
          action={
            <Button variant="secondary" onClick={clearFilters}>
              Clear filters
            </Button>
          }
        />
      ) : (
        // `relative` makes this scroll box the containing block of the visually hidden caption and header
        // label (position: absolute); without it they escape the box and widen the page on phones.
        <div className="relative overflow-x-auto">
          <table className="min-w-full text-sm">
            <caption className="sr-only">
              Compared pairs. Rank 1 is the most similar pair. Column headers are buttons that sort the table.
            </caption>
            <thead className="bg-slate-50">
              <tr>
                {columns.map((column) => {
                  const direction = sort.key === column.key ? sort.direction : null
                  return (
                    <th
                      key={column.key}
                      scope="col"
                      aria-sort={direction === 'asc' ? 'ascending' : direction === 'desc' ? 'descending' : 'none'}
                      className={`whitespace-nowrap px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500 first:pl-6 ${
                        column.numeric ? 'text-right' : 'text-left'
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => changeSort(column)}
                        className={`-mx-1 inline-flex items-center gap-1 rounded px-1 py-0.5 uppercase hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                          direction ? 'text-slate-900' : ''
                        }`}
                      >
                        {column.label}
                        <SortIcon direction={direction} />
                      </button>
                    </th>
                  )
                })}
                <th scope="col" className="px-3 py-2.5 pr-6">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((pair) => (
                <tr key={`${pair.a_id}-${pair.b_id}`} className="transition-colors hover:bg-slate-50">
                  <td className="px-3 py-3 pl-6 font-medium tabular-nums text-slate-500">{pair.rank}</td>
                  <td className="px-3 py-3">
                    <FileName name={pair.a_name} />
                  </td>
                  <td className="px-3 py-3">
                    <FileName name={pair.b_name} />
                  </td>
                  <td className="px-3 py-3">
                    <span className="inline-flex rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 ring-1 ring-inset ring-slate-500/10">
                      {LANGUAGE_NAMES[pair.language] ?? pair.language}
                    </span>
                  </td>
                  <td className="w-44 min-w-[10rem] px-3 py-3">
                    <ScoreBar value={pair.scores?.fused} inline size="sm" high={high} moderate={moderate} label="Fused score" />
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-slate-700">{pct(pair.scores?.token)}</td>
                  <td
                    className="px-3 py-3 text-right tabular-nums text-slate-700"
                    title={isMissing(pair.scores?.structure) ? 'No structure score: a syntax tree could not be built for one of the files' : undefined}
                  >
                    {pct(pair.scores?.structure)}
                  </td>
                  {hasModel && (
                    <td
                      className="px-3 py-3 text-right tabular-nums text-slate-700"
                      title="Probability of plagiarism from the trained logistic-regression model"
                    >
                      {pct(pair.scores?.ml_probability)}
                    </td>
                  )}
                  <td className="px-3 py-3">
                    <Badge tone={pair.verdict} dot>
                      {pair.verdict}
                    </Badge>
                  </td>
                  <td className="px-3 py-3 pr-6 text-right">
                    <Button
                      to={`/runs/${runId}/pairs/${pair.a_id}/${pair.b_id}`}
                      variant="secondary"
                      size="sm"
                      aria-label={`Compare ${pair.a_name} with ${pair.b_name}`}
                    >
                      Compare
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex flex-col items-center gap-3 border-t border-slate-200 px-6 py-3 sm:flex-row sm:justify-between">
        <p className="text-sm text-slate-500" aria-live="polite">
          Showing <span className="font-medium tabular-nums text-slate-700">{rows.length}</span> of{' '}
          <span className="font-medium tabular-nums text-slate-700">{sorted.length}</span> {sorted.length === 1 ? 'pair' : 'pairs'}
          {filtersActive && ` (filtered from ${pairs.length})`}
        </p>
        {remaining > 0 && (
          <Button variant="secondary" size="sm" onClick={() => setVisible((n) => n + PAGE_SIZE)}>
            Show more ({remaining} remaining)
          </Button>
        )}
      </div>
    </div>
  )
}
