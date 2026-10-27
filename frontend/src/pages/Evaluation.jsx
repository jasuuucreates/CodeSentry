// Evaluation page (route "/evaluation") — how well each detection method separates disguised copies
// from honest submissions on the labelled dataset (contract section 10).
//
// Every number comes from evaluation/results/evaluation.json, written by
// `python evaluation/evaluate.py` after it has scored every labelled pair. This page only reads that
// file through GET /api/evaluation and presents it; nothing here is typed in by hand.
import { useEffect, useMemo, useState } from 'react'
import { errorMessage, getEvaluation } from '../api/client.js'
import MetricsChart from '../components/MetricsChart.jsx'
import Badge from '../components/ui/Badge.jsx'
import Button from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Spinner from '../components/ui/Spinner.jsx'
import StatCard from '../components/ui/StatCard.jsx'
import { dateTime, pct, score } from '../lib/format.js'

const TITLE = 'Evaluation'
const SUBTITLE =
  "How accurately each method separates disguised copies from honest work on the labelled dataset: CodeSentry's hybrid detector compared with simpler methods and with its trained variants."

// One line per method saying what it actually compares, shown under the method name.
const METHOD_NOTES = {
  text: 'Line-by-line diff of the raw source',
  tfidf: 'Cosine similarity of TF-IDF word vectors',
  token: 'Winnowing fingerprints of normalised tokens',
  structure: 'Canonical AST skeleton comparison',
  hybrid: 'Token and structure scores fused',
  hybrid_calibrated: 'Fused score with learned weights and thresholds',
  logreg: 'Logistic regression over all pair features',
}

// Methods whose parameters were learned from the labelled pairs (evaluated with cross-validation).
const TRAINED_METHODS = new Set(['hybrid_calibrated', 'logreg'])

/** "5-fold grouped CV: F1 1.00 ± 0.00" from an optional {folds, f1_mean, f1_std} object. */
function cvNote(cv) {
  if (!cv || !isNumber(cv.f1_mean)) return null
  const folds = isNumber(cv.folds) ? `${cv.folds}-fold ` : ''
  const spread = isNumber(cv.f1_std) ? ` ± ${score(cv.f1_std)}` : ''
  return `${folds}cross-validation: F1 ${score(cv.f1_mean)}${spread}`
}

// Human-readable names for the dataset categories. Keys follow the order the obfuscator applies
// them, so the robustness table reads from the simplest disguise to the combined one.
const POSITIVE_CATEGORIES = {
  rename: 'Renamed identifiers',
  comments_format: 'Comments and formatting changed',
  reorder: 'Functions reordered',
  loop_swap: 'for loops rewritten as while',
  dead_code: 'Dead code inserted',
  combined: 'All five disguises combined',
}
const NEGATIVE_CATEGORIES = {
  independent_same_problem: 'Independent solutions, same problem',
  obfuscated_vs_independent: 'Disguised copy vs independent solution',
  different_problem: 'Different problems',
}

// Colour ramps for the category tables, as [value, [r, g, b]] stops. Each is a single hue from light
// to dark, because the cells show a magnitude. Recall uses indigo (more copies caught = darker);
// false-positive rate uses slate (more false alarms = darker). Red/amber/green stay reserved for
// verdicts, so a dark cell is never mistaken for a "High" plagiarism verdict.
const RECALL_RAMP = [
  [0, [238, 242, 255]],
  [0.5, [165, 180, 252]],
  [0.8, [99, 102, 241]],
  [1, [55, 48, 163]],
]
const FPR_RAMP = [
  [0, [248, 250, 252]],
  [0.2, [203, 213, 225]],
  [0.5, [100, 116, 139]],
  [1, [51, 65, 85]],
]

function isNumber(x) {
  return typeof x === 'number' && Number.isFinite(x)
}

function categoryLabel(key, names) {
  return names[key] ?? key.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())
}

function rampRgb(value, stops) {
  const v = Math.min(1, Math.max(0, value))
  for (let i = 1; i < stops.length; i += 1) {
    const [hi, hiRgb] = stops[i]
    if (v <= hi) {
      const [lo, loRgb] = stops[i - 1]
      const t = (v - lo) / (hi - lo)
      return loRgb.map((c, k) => Math.round(c + (hiRgb[k] - c) * t))
    }
  }
  return stops[stops.length - 1][1]
}

/** Background and a readable text colour (WCAG relative luminance decides dark or white text). */
function rampStyle(value, stops) {
  if (!isNumber(value)) return { backgroundColor: 'rgb(241, 245, 249)', color: '#64748b' }
  const rgb = rampRgb(value, stops)
  const [r, g, b] = rgb.map((c) => {
    const s = c / 255
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4
  })
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
  return { backgroundColor: `rgb(${rgb.join(', ')})`, color: luminance > 0.4 ? '#0f172a' : '#ffffff' }
}

function rampGradient(stops) {
  return `linear-gradient(to right, ${stops.map(([at, rgb]) => `rgb(${rgb.join(', ')}) ${at * 100}%`).join(', ')})`
}

/** Category keys in a sensible order: the known ones first in their defined order, then any others. */
function orderCategories(keys, names) {
  const known = Object.keys(names).filter((key) => keys.has(key))
  const extra = [...keys].filter((key) => !(key in names)).sort()
  return [...known, ...extra]
}

/** Turns the raw evaluation.json into rows and category lists the tables can render directly. */
function buildView(data) {
  const methods = data?.methods && typeof data.methods === 'object' ? data.methods : {}
  const order = Array.isArray(data?.method_order) && data.method_order.length ? data.method_order : Object.keys(methods)

  const rows = order
    .filter((key) => methods[key])
    .map((key) => {
      const m = methods[key]
      const def = m.at_default ?? {}
      return {
        key,
        label: m.label || key,
        def,
        best: m.best ?? {},
        auc: m.auc,
        meanMs: m.mean_ms,
        recallByCategory: m.recall_by_category ?? {},
        fprByCategory: m.fpr_by_category ?? {},
        cv: m.cv,
        // Flat copies for the chart component.
        precision: def.precision,
        recall: def.recall,
        f1: def.f1,
      }
    })

  const positiveKeys = new Set(rows.flatMap((row) => Object.keys(row.recallByCategory)))
  const negativeKeys = new Set(rows.flatMap((row) => Object.keys(row.fprByCategory)))

  return {
    rows,
    dataset: data?.dataset ?? {},
    threshold: isNumber(data?.default_threshold) ? data.default_threshold : 0.5,
    generatedAt: data?.generated_at,
    positiveCategories: orderCategories(positiveKeys, POSITIVE_CATEGORIES),
    negativeCategories: orderCategories(negativeKeys, NEGATIVE_CATEGORIES),
  }
}

/**
 * The displayed text of the best value in a column. Cells are compared by their formatted text, so
 * two methods that both show "91.7%" are both highlighted instead of only one of them.
 */
function bestText(rows, pick, format, lowerIsBetter = false) {
  const values = rows.map(pick).filter(isNumber)
  if (values.length === 0) return null
  return format(lowerIsBetter ? Math.min(...values) : Math.max(...values))
}

function formatMs(x) {
  if (!isNumber(x)) return '—'
  return `${x < 10 ? x.toFixed(2) : x.toFixed(1)} ms`
}

function signedPoints(delta) {
  if (!isNumber(delta)) return '—'
  const points = delta * 100
  if (Math.abs(points) < 0.05) return '±0.0 pts'
  return `${points > 0 ? '+' : '−'}${Math.abs(points).toFixed(1)} pts`
}

/** A numeric table cell; the best value in its column gets an indigo highlight plus hidden text. */
function MetricCell({ text, best }) {
  const isBest = best !== null && text === best && text !== '—'
  return (
    <td className="whitespace-nowrap px-4 py-3 text-right tabular-nums">
      <span
        className={`inline-block rounded-md px-2 py-0.5 ${
          isBest ? 'bg-indigo-50 font-semibold text-indigo-700 ring-1 ring-inset ring-indigo-600/20' : 'text-slate-700'
        }`}
      >
        {text}
        {isBest && <span className="sr-only"> (best in column)</span>}
      </span>
    </td>
  )
}

function MethodName({ row }) {
  return (
    <th scope="row" className="px-6 py-3 text-left align-top font-normal">
      <span className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-slate-900">{row.label}</span>
        {row.key === 'hybrid' && <Badge tone="indigo">CodeSentry</Badge>}
        {TRAINED_METHODS.has(row.key) && <Badge tone="neutral">Trained</Badge>}
      </span>
      {METHOD_NOTES[row.key] && <span className="mt-0.5 block text-xs text-slate-500">{METHOD_NOTES[row.key]}</span>}
      {cvNote(row.cv) && <span className="mt-0.5 block text-xs text-slate-500">{cvNote(row.cv)}</span>}
    </th>
  )
}

const TH = 'whitespace-nowrap px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500'
const TH_FIRST = 'px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500'

function BestLegend({ children }) {
  return (
    <p className="flex flex-wrap items-center gap-2 border-t border-slate-200 px-6 py-3 text-xs text-slate-500">
      <span className="inline-block h-3 w-3 rounded-sm bg-indigo-50 ring-1 ring-inset ring-indigo-600/30" aria-hidden="true" />
      {children}
    </p>
  )
}

function HeadlineTable({ rows, threshold }) {
  const columns = [
    { key: 'precision', label: 'Precision', pick: (r) => r.def.precision, format: (x) => pct(x) },
    { key: 'recall', label: 'Recall', pick: (r) => r.def.recall, format: (x) => pct(x) },
    { key: 'f1', label: 'F1 score', pick: (r) => r.def.f1, format: (x) => pct(x) },
    { key: 'accuracy', label: 'Accuracy', pick: (r) => r.def.accuracy, format: (x) => pct(x) },
    { key: 'auc', label: 'ROC AUC', pick: (r) => r.auc, format: (x) => score(x, 3) },
  ]
  const best = Object.fromEntries(columns.map((c) => [c.key, bestText(rows, c.pick, c.format)]))
  const count = (x) => (isNumber(x) ? x : '—')

  return (
    <Card
      title={`Detection quality at the default threshold (${score(threshold)})`}
      subtitle="A pair is flagged when its score is at or above the threshold. The threshold was fixed before any results were seen."
      bodyClassName="p-0"
    >
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <caption className="sr-only">
            Precision, recall, F1 score, accuracy and ROC AUC of each method at threshold {score(threshold)}
          </caption>
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className={TH_FIRST}>
                Method
              </th>
              {columns.map((c) => (
                <th key={c.key} scope="col" className={TH}>
                  {c.label}
                </th>
              ))}
              <th scope="col" className={TH}>
                <abbr title="true positives / false positives / true negatives / false negatives" className="no-underline">
                  TP / FP / TN / FN
                </abbr>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row) => (
              <tr key={row.key} className={row.key === 'hybrid' ? 'bg-indigo-50/30' : undefined}>
                <MethodName row={row} />
                {columns.map((c) => (
                  <MetricCell key={c.key} text={c.format(c.pick(row))} best={best[c.key]} />
                ))}
                <td className="whitespace-nowrap px-4 py-3 text-right font-mono text-xs text-slate-500 tabular-nums">
                  {count(row.def.tp)} / {count(row.def.fp)} / {count(row.def.tn)} / {count(row.def.fn)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <BestLegend>Best value in each column. ROC AUC does not depend on the threshold.</BestLegend>
    </Card>
  )
}

function RampLegend({ stops, low, high }) {
  return (
    <div className="flex items-center gap-2 text-xs text-slate-500" aria-hidden="true">
      <span>{low}</span>
      <span className="h-2.5 w-28 rounded-full ring-1 ring-inset ring-slate-900/5" style={{ backgroundImage: rampGradient(stops) }} />
      <span>{high}</span>
    </div>
  )
}

/** Categories as rows, methods as columns, each cell tinted by its value. */
function CategoryTable({ title, subtitle, caption, rows, categories, names, pick, stops, legend, counts, footnote }) {
  return (
    <Card title={title} subtitle={subtitle} actions={legend} bodyClassName="p-0">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className={TH_FIRST}>
                Category
              </th>
              {rows.map((row) => (
                <th key={row.key} scope="col" className="px-2 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {row.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {categories.map((category) => (
              <tr key={category}>
                <th scope="row" className="px-6 py-2 text-left font-normal">
                  <span className="block font-medium text-slate-900">{categoryLabel(category, names)}</span>
                  {isNumber(counts?.[category]) && (
                    <span className="block text-xs text-slate-500">
                      {counts[category]} {counts[category] === 1 ? 'pair' : 'pairs'}
                    </span>
                  )}
                </th>
                {rows.map((row) => {
                  const value = pick(row)[category]
                  return (
                    <td key={row.key} className="px-2 py-2">
                      <span
                        className="mx-auto flex h-9 min-w-16 items-center justify-center rounded-md text-sm font-medium tabular-nums"
                        style={rampStyle(value, stops)}
                        title={isNumber(value) ? `${row.label}: ${pct(value, 2)}` : undefined}
                      >
                        {pct(value, 0)}
                      </span>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {footnote && <p className="border-t border-slate-200 px-6 py-3 text-xs leading-5 text-slate-500">{footnote}</p>}
    </Card>
  )
}

function TunedTable({ rows }) {
  const columns = [
    { key: 'precision', label: 'Precision' },
    { key: 'recall', label: 'Recall' },
    { key: 'f1', label: 'F1 score' },
    { key: 'accuracy', label: 'Accuracy' },
  ]
  const best = Object.fromEntries(columns.map((c) => [c.key, bestText(rows, (r) => r.best[c.key], (x) => pct(x))]))

  return (
    <Card
      title="Tuned threshold (optimistic — tuned on the same dataset)"
      subtitle="For each method, the threshold between 0.00 and 1.00 with the highest F1 on these same labelled pairs. Treat these figures as an upper bound, not as expected performance on a new class."
      bodyClassName="p-0"
    >
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <caption className="sr-only">Metrics of each method at its F1-maximising threshold, tuned on the evaluation dataset</caption>
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className={TH_FIRST}>
                Method
              </th>
              <th scope="col" className={TH}>
                Tuned threshold
              </th>
              {columns.map((c) => (
                <th key={c.key} scope="col" className={TH}>
                  {c.label}
                </th>
              ))}
              <th scope="col" className={TH}>
                F1 vs default
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row) => (
              <tr key={row.key}>
                <MethodName row={row} />
                <td className="whitespace-nowrap px-4 py-3 text-right font-mono text-slate-700 tabular-nums">{score(row.best.threshold)}</td>
                {columns.map((c) => (
                  <MetricCell key={c.key} text={pct(row.best[c.key])} best={best[c.key]} />
                ))}
                <td className="whitespace-nowrap px-4 py-3 text-right text-slate-600 tabular-nums">
                  {isNumber(row.best.f1) && isNumber(row.def.f1) ? signedPoints(row.best.f1 - row.def.f1) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <BestLegend>Best value in each column at the tuned thresholds.</BestLegend>
    </Card>
  )
}

function SpeedCard({ rows }) {
  const slowest = Math.max(0, ...rows.map((row) => row.meanMs).filter(isNumber))
  return (
    <Card title="Mean time per pair" subtitle="Average wall-clock time each method needed to score one pair during the evaluation run.">
      <ul className="space-y-4">
        {rows.map((row) => {
          const width = isNumber(row.meanMs) && slowest > 0 ? Math.max(1, (row.meanMs / slowest) * 100) : 0
          return (
            <li key={row.key}>
              <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
                <span className="text-slate-700">{row.label}</span>
                <span className="font-medium text-slate-900 tabular-nums">{formatMs(row.meanMs)}</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
                <div className="h-full rounded-full bg-indigo-500" style={{ width: `${width}%` }} />
              </div>
            </li>
          )
        })}
      </ul>
      <p className="mt-5 text-xs leading-5 text-slate-500">Bar length is relative to the slowest method. Times depend on the machine that ran the evaluation.</p>
    </Card>
  )
}

function MethodologyCard({ dataset }) {
  const positives = dataset.positives
  const negatives = dataset.negatives
  const imbalanced = isNumber(positives) && isNumber(negatives) && positives !== negatives

  return (
    <Card title="Methodology" subtitle="How the dataset was built and how to read the numbers above.">
      <div className="grid gap-x-10 gap-y-6 text-sm leading-6 text-slate-600 md:grid-cols-2">
        <section>
          <h3 className="font-semibold text-slate-900">How the dataset was built</h3>
          <p className="mt-1">
            Ten programming assignments were each solved in Python and in C. Every assignment has an original submission and two
            independent solutions written with different algorithms, decomposition and naming. The original was then disguised
            automatically in six ways: renamed identifiers, rewritten comments and formatting, reordered functions, for loops turned
            into while loops, inserted dead code, and all of these combined.
          </p>
          <p className="mt-2">
            Each original paired with one of its disguised copies is a positive (plagiarism). Negatives are the independent solutions
            compared with the original and with each other, the fully disguised copy compared with an independent solution, and
            originals of different assignments compared with each other.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-slate-900">Why same-problem solutions are hard negatives</h3>
          <p className="mt-1">
            Two honest students solving the same assignment use the same sample data, print the same output, call the same library
            functions and often choose the same names, such as <code className="font-mono text-[13px] text-slate-800">marks</code> or{' '}
            <code className="font-mono text-[13px] text-slate-800">total</code>. Plain text matching and TF-IDF reward that shared
            vocabulary, so these pairs are exactly where false accusations come from. A detector is only useful if it flags disguised
            copies while leaving these honest pairs alone, which is why their false-positive rate is reported on its own.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-slate-900">Why tuned thresholds are optimistic</h3>
          <p className="mt-1">
            The default threshold of 0.50 was fixed in advance. The tuned threshold is found by trying every value from 0.00 to 1.00
            and keeping the one with the best F1 on the same labelled pairs it is then scored on, so the answer key helps set the
            cut-off. That makes the tuned figures an upper bound; a fair tuned result would need a separate validation set of
            submissions the threshold never saw.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-slate-900">What the metrics mean</h3>
          <ul className="mt-1 space-y-1">
            <li>
              <span className="font-medium text-slate-800">Precision</span> = TP / (TP + FP): of the pairs flagged, how many really were
              copies.
            </li>
            <li>
              <span className="font-medium text-slate-800">Recall</span> = TP / (TP + FN): of the real copies, how many were caught.
            </li>
            <li>
              <span className="font-medium text-slate-800">F1</span> is the harmonic mean of precision and recall, so it is high only
              when both are.
            </li>
            <li>
              <span className="font-medium text-slate-800">Accuracy</span> = (TP + TN) / all pairs.
              {imbalanced &&
                ` Here the dataset has ${positives} positives and ${negatives} negatives, so accuracy alone can look good for a method that favours the larger class.`}
            </li>
            <li>
              <span className="font-medium text-slate-800">ROC AUC</span> is the probability that a randomly chosen copy scores higher
              than a randomly chosen honest pair, computed with the Mann–Whitney rank formula (ties count as half). It needs no
              threshold.
            </li>
          </ul>
        </section>
      </div>
    </Card>
  )
}

function languageHint(byLanguage) {
  if (!byLanguage || typeof byLanguage !== 'object') return undefined
  const names = { python: 'Python', c: 'C' }
  const parts = Object.entries(byLanguage).map(([key, n]) => `${n} ${names[key] ?? key}`)
  return parts.length ? parts.join(' · ') : undefined
}

function Results({ view }) {
  const { rows, dataset, threshold } = view
  const byCategory = dataset.by_category ?? {}

  return (
    <div className="space-y-8">
      <section aria-labelledby="dataset-heading">
        <h2 id="dataset-heading" className="sr-only">
          Dataset summary
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Labelled pairs" value={dataset.pairs} hint={languageHint(dataset.by_language)} />
          <StatCard label="Plagiarised pairs" value={dataset.positives} hint="Original vs a disguised copy" tone="indigo" />
          <StatCard label="Honest pairs" value={dataset.negatives} hint="Independent or unrelated programs" />
          <StatCard label="Default threshold" value={score(threshold)} hint="Score at which a pair is flagged" />
        </div>
      </section>

      <HeadlineTable rows={rows} threshold={threshold} />

      <Card
        title="Precision, recall and F1 per method"
        subtitle={`Measured at the default threshold of ${score(threshold)}. Select a legend entry to hide or show a metric.`}
      >
        <MetricsChart rows={rows} threshold={threshold} />
      </Card>

      {view.positiveCategories.length > 0 && (
        <CategoryTable
          title="Robustness by obfuscation type"
          subtitle={`Recall at ${score(threshold)}: the share of disguised copies of each kind that the method still flagged. Higher is better.`}
          caption="Recall per obfuscation category for each method"
          rows={rows}
          categories={view.positiveCategories}
          names={POSITIVE_CATEGORIES}
          pick={(row) => row.recallByCategory}
          stops={RECALL_RAMP}
          counts={byCategory}
          legend={<RampLegend stops={RECALL_RAMP} low="0% caught" high="100%" />}
        />
      )}

      {view.negativeCategories.length > 0 && (
        <CategoryTable
          title="False-positive rate by negative category"
          subtitle={`The share of honest pairs of each kind wrongly flagged at ${score(threshold)}. Lower is better.`}
          caption="False-positive rate per negative category for each method"
          rows={rows}
          categories={view.negativeCategories}
          names={NEGATIVE_CATEGORIES}
          pick={(row) => row.fprByCategory}
          stops={FPR_RAMP}
          counts={byCategory}
          legend={<RampLegend stops={FPR_RAMP} low="0% flagged" high="100%" />}
          footnote="Independent solutions to the same assignment are the hardest honest pairs: they share data, output and vocabulary without any copying."
        />
      )}

      {/* Stacked rather than side by side: with seven methods the tuned table needs the full width. */}
      <div className="grid gap-8">
        <div className="min-w-0">
          <TunedTable rows={rows} />
        </div>
        <SpeedCard rows={rows} />
      </div>

      <MethodologyCard dataset={dataset} />
    </div>
  )
}

export default function Evaluation() {
  // `reloadKey` re-runs the request effect; `missing` means the backend answered 404 because
  // evaluate.py has not produced a results file yet, which is an expected state, not an error.
  const [reloadKey, setReloadKey] = useState(0)
  const [state, setState] = useState({ loading: true, data: null, missing: false, error: '' })

  useEffect(() => {
    // `active` ignores a response that arrives after the page was left (or re-requested).
    let active = true
    getEvaluation()
      .then((data) => active && setState({ loading: false, data, missing: false, error: '' }))
      .catch((err) => {
        if (!active) return
        if (err?.response?.status === 404) setState({ loading: false, data: null, missing: true, error: '' })
        else setState({ loading: false, data: null, missing: false, error: errorMessage(err) })
      })
    return () => {
      active = false
    }
  }, [reloadKey])

  const reload = () => {
    setState((prev) => ({ ...prev, loading: true, error: '' }))
    setReloadKey((key) => key + 1)
  }

  const view = useMemo(() => (state.data ? buildView(state.data) : null), [state.data])

  const actions = (
    <>
      {view?.generatedAt && <span className="text-sm text-slate-500">Generated {dateTime(view.generatedAt)}</span>}
      <Button variant="secondary" onClick={reload} loading={state.loading && Boolean(state.data)} disabled={state.loading}>
        Reload results
      </Button>
    </>
  )

  let body
  if (state.loading && !state.data) {
    body = <Spinner center size="lg" label="Loading evaluation results…" />
  } else if (state.error) {
    body = <ErrorBanner title="Could not load the evaluation results" message={state.error} onRetry={reload} />
  } else if (state.missing) {
    body = (
      <EmptyState
        title="No evaluation results yet"
        description={
          <>
            The results file has not been generated. From the project root run{' '}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[13px] text-slate-800">python evaluation/evaluate.py</code>{' '}
            (after <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[13px] text-slate-800">python dataset/build_dataset.py</code>{' '}
            has built the labelled dataset), then reload this page.
          </>
        }
        action={
          <Button variant="secondary" onClick={reload}>
            Reload results
          </Button>
        }
      />
    )
  } else if (!view || view.rows.length === 0) {
    body = (
      <EmptyState
        title="The results file contains no methods"
        description="evaluation.json was found but lists no scored methods. Run python evaluation/evaluate.py again to regenerate it."
        action={
          <Button variant="secondary" onClick={reload}>
            Reload results
          </Button>
        }
      />
    )
  } else {
    body = <Results view={view} />
  }

  return (
    <>
      <PageHeader title={TITLE} subtitle={SUBTITLE} actions={actions} />
      {body}
    </>
  )
}
