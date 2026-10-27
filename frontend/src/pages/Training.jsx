// Model Training page (route "/training") — how the fusion weight and verdict thresholds were learned
// from the labelled dataset, and how well that generalises to assignments the training never saw.
//
// Data: GET /api/training -> {report: training_report.json, points: features.csv rows, trained: trained_config.json}.
// The hero chart plots every labelled pair by its token score (x) and structure score (y) with the
// learned decision boundary w*x + (1-w)*y = t drawn over it, next to the untrained 0.5 / 0.5 / 0.5 line.
import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { Bar, Scatter } from 'react-chartjs-2'
import { errorMessage, getTraining } from '../api/client.js'
import Button from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Spinner from '../components/ui/Spinner.jsx'
import StatCard from '../components/ui/StatCard.jsx'
import { palette } from '../lib/colors.js'
import { pct, score } from '../lib/format.js'

ChartJS.register(LinearScale, CategoryScale, PointElement, LineElement, BarElement, Tooltip, Legend)

const FONT = { family: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif', size: 12 }

const FEATURE_LABELS = {
  token: 'Token similarity',
  containment: 'Containment',
  structure: 'Structure similarity',
  ted: 'Tree edit similarity',
  subtree: 'Subtree overlap',
  text: 'Plain text diff',
  tfidf: 'TF-IDF cosine',
  length_ratio: 'Length ratio',
}

const CATEGORY_LABELS = {
  rename: 'Renamed identifiers',
  comments_format: 'Comments and formatting changed',
  reorder: 'Functions reordered',
  loop_swap: 'for loops rewritten as while',
  dead_code: 'Dead code inserted',
  combined: 'All five disguises combined',
  independent_same_problem: 'Independent solutions, same problem',
  obfuscated_vs_independent: 'Disguised copy vs independent solution',
  different_problem: 'Different problems',
}

function isNumber(x) {
  return typeof x === 'number' && Number.isFinite(x)
}

function meanStd(values) {
  const xs = values.filter(isNumber)
  if (!xs.length) return null
  const mean = xs.reduce((s, x) => s + x, 0) / xs.length
  const variance = xs.reduce((s, x) => s + (x - mean) ** 2, 0) / xs.length
  return { mean, std: Math.sqrt(variance) }
}

/**
 * How far the weakest copy lies above, and the strongest honest pair below, the line
 * w*token + (1-w)*structure = t. `separates` is true when every pair is on its correct side.
 */
function margins(points, w, t) {
  let minCopied = Infinity
  let maxHonest = -Infinity
  for (const p of points) {
    const fused = w * p.token + (1 - w) * p.structure
    if (p.label === 1) minCopied = Math.min(minCopied, fused)
    else maxHonest = Math.max(maxHonest, fused)
  }
  const copied = minCopied - t
  const honest = t - maxHonest
  return { copied, honest, separates: Number.isFinite(copied) && Number.isFinite(honest) && copied >= 0 && honest > 0 }
}

/** "generated/c/p01_grade_statistics/variant_rename.c" -> "c/p01/variant_rename.c" */
function shortPath(path) {
  const parts = String(path || '').split('/')
  if (parts.length >= 4) return `${parts[1]}/${parts[2].split('_')[0]}/${parts[3]}`
  return String(path || '')
}

/**
 * The part of the line w*x + (1-w)*y = t that lies inside the unit square, as two {x, y} points
 * (or [] if the line misses the square).
 */
function boundarySegment(w, t) {
  const points = []
  const add = (x, y) => {
    if (x >= -1e-9 && x <= 1 + 1e-9 && y >= -1e-9 && y <= 1 + 1e-9) {
      const p = { x: Math.min(1, Math.max(0, x)), y: Math.min(1, Math.max(0, y)) }
      if (!points.some((q) => Math.abs(q.x - p.x) < 1e-9 && Math.abs(q.y - p.y) < 1e-9)) points.push(p)
    }
  }
  if (Math.abs(1 - w) < 1e-9) {
    add(t / w, 0)
    add(t / w, 1)
  } else {
    add(0, t / (1 - w)) // x = 0
    add(1, (t - w) / (1 - w)) // x = 1
    if (Math.abs(w) > 1e-9) {
      add(t / w, 0) // y = 0
      add((t - (1 - w)) / w, 1) // y = 1
    }
  }
  return points.length >= 2 ? points.sort((p, q) => p.x - q.x).slice(0, 2) : []
}

function BoundaryChart({ points, w, t }) {
  const data = useMemo(() => {
    const toPoint = (p) => ({ x: p.token, y: p.structure, a: p.a, b: p.b, category: p.category, language: p.language })
    const copied = points.filter((p) => p.label === 1).map(toPoint)
    const honest = points.filter((p) => p.label !== 1).map(toPoint)
    return {
      datasets: [
        {
          label: `Copied pairs (${copied.length})`,
          data: copied,
          backgroundColor: 'rgba(220, 38, 38, 0.55)',
          borderColor: palette.red,
          borderWidth: 1,
          pointRadius: 4,
          pointHoverRadius: 6,
          order: 2,
        },
        {
          label: `Honest pairs (${honest.length})`,
          data: honest,
          backgroundColor: 'rgba(22, 163, 74, 0.45)',
          borderColor: palette.green,
          borderWidth: 1,
          pointRadius: 4,
          pointHoverRadius: 6,
          order: 3,
        },
        {
          label: `Learned boundary (${score(w)}·token + ${score(1 - w)}·structure = ${score(t)})`,
          data: boundarySegment(w, t),
          showLine: true,
          borderColor: palette.indigo,
          backgroundColor: palette.indigo,
          borderWidth: 3,
          pointRadius: 0,
          pointHoverRadius: 0,
          order: 0,
          isBoundary: true,
        },
        {
          label: 'Untrained boundary (0.5·token + 0.5·structure = 0.5)',
          data: boundarySegment(0.5, 0.5),
          showLine: true,
          borderColor: palette.slate,
          backgroundColor: palette.slate,
          borderDash: [6, 6],
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 0,
          order: 1,
          isBoundary: true,
        },
      ],
    }
  }, [points, w, t])

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: {
          type: 'linear',
          min: 0,
          max: 1,
          title: { display: true, text: 'Token similarity (winnowing Jaccard)', color: palette.text, font: FONT },
          ticks: { color: palette.text, font: FONT, callback: (v) => `${Math.round(v * 100)}%` },
          grid: { color: palette.grid },
        },
        y: {
          type: 'linear',
          min: 0,
          max: 1,
          title: { display: true, text: 'Structure similarity (AST)', color: palette.text, font: FONT },
          ticks: { color: palette.text, font: FONT, callback: (v) => `${Math.round(v * 100)}%` },
          grid: { color: palette.grid },
        },
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: palette.text, font: FONT, usePointStyle: true, padding: 16 },
        },
        tooltip: {
          backgroundColor: '#0f172a',
          padding: 10,
          filter: (item) => !item.dataset.isBoundary,
          callbacks: {
            title: (items) => {
              const raw = items[0]?.raw
              return raw ? `${shortPath(raw.a)}  vs  ${shortPath(raw.b)}` : ''
            },
            label: (item) => {
              const raw = item.raw
              return [
                `${CATEGORY_LABELS[raw.category] ?? raw.category} (${raw.language === 'c' ? 'C' : 'Python'})`,
                `token ${pct(raw.x)} · structure ${pct(raw.y)}`,
              ]
            },
          },
        },
      },
    }),
    [],
  )

  return (
    <div className="h-[460px]">
      <Scatter
        data={data}
        options={options}
        role="img"
        aria-label={`Scatter plot of ${points.length} labelled pairs by token and structure similarity, with the learned decision boundary.`}
      />
    </div>
  )
}

function CoefficientChart({ features, weights }) {
  const rows = features
    .map((name, i) => ({ name, label: FEATURE_LABELS[name] ?? name, weight: weights[i] }))
    .filter((row) => isNumber(row.weight))
    .sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight))
  const data = {
    labels: rows.map((r) => r.label),
    datasets: [
      {
        label: 'Standardised coefficient',
        data: rows.map((r) => r.weight),
        backgroundColor: rows.map((r) => (r.weight >= 0 ? palette.indigo : palette.slate)),
        borderRadius: 4,
        maxBarThickness: 22,
      },
    ],
  }
  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    scales: {
      x: {
        title: { display: true, text: 'Weight per standard deviation of the feature', color: palette.text, font: FONT },
        ticks: { color: palette.text, font: FONT },
        grid: { color: palette.grid },
      },
      y: { ticks: { color: palette.text, font: FONT }, grid: { display: false } },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0f172a',
        callbacks: { label: (item) => `coefficient ${item.parsed.x >= 0 ? '+' : ''}${item.parsed.x.toFixed(3)}` },
      },
    },
  }
  return (
    <div style={{ height: `${Math.max(220, rows.length * 38 + 60)}px` }}>
      <Bar data={data} options={options} role="img" aria-label="Logistic regression coefficients of each feature." />
    </div>
  )
}

const TH = 'whitespace-nowrap px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-500'
const TD = 'whitespace-nowrap px-4 py-3 tabular-nums text-slate-700'

function FoldTable({ folds }) {
  return (
    <div className="relative overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th scope="col" className={`${TH} pl-6`}>Fold</th>
            <th scope="col" className={TH}>Held-out problems</th>
            <th scope="col" className={`${TH} text-right`}>Train / test pairs</th>
            <th scope="col" className={`${TH} text-right`}>Learned w_token</th>
            <th scope="col" className={`${TH} text-right`}>Learned threshold</th>
            <th scope="col" className={`${TH} text-right`}>Calibrated hybrid F1</th>
            <th scope="col" className={`${TH} pr-6 text-right`}>Logistic regression F1</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {folds.map((f) => (
            <tr key={f.fold}>
              <td className={`${TD} pl-6 font-medium text-slate-900`}>{f.fold}</td>
              <td className="px-4 py-3 text-slate-700">
                {(f.test_problems ?? []).map((p) => p.replace(/^p(\d+)_/, 'p$1 ').replace(/_/g, ' ')).join(', ')}
              </td>
              <td className={`${TD} text-right`}>
                {f.train_pairs} / {f.test_pairs}
              </td>
              <td className={`${TD} text-right`}>{score(f.learned_w_token)}</td>
              <td className={`${TD} text-right`}>{score(f.learned_threshold)}</td>
              <td className={`${TD} text-right`}>{score(f.calibrated_f1, 3)}</td>
              <td className={`${TD} pr-6 text-right`}>{score(f.logreg_f1, 3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const COMPARISON_NOTES = {
  hybrid_calibrated: 'trained',
  logreg: 'trained',
  hybrid: 'CodeSentry default',
}

function ComparisonTable({ comparison }) {
  const rows = Object.entries(comparison ?? {}).filter(([, m]) => m && typeof m === 'object')
  return (
    <div className="relative overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th scope="col" className={`${TH} pl-6`}>Method</th>
            <th scope="col" className={`${TH} text-right`}>Precision</th>
            <th scope="col" className={`${TH} text-right`}>Recall</th>
            <th scope="col" className={`${TH} text-right`}>F1</th>
            <th scope="col" className={`${TH} text-right`}>Accuracy</th>
            <th scope="col" className={`${TH} text-right`}>ROC AUC</th>
            <th scope="col" className={`${TH} pr-6 text-right`}>TP / FP / TN / FN</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map(([key, m]) => (
            <tr key={key} className={COMPARISON_NOTES[key] === 'trained' ? 'bg-indigo-50/30' : undefined}>
              <th scope="row" className="px-4 py-3 pl-6 text-left font-medium text-slate-900">
                {m.label ?? key}
                {COMPARISON_NOTES[key] && (
                  <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                    {COMPARISON_NOTES[key]}
                  </span>
                )}
              </th>
              <td className={`${TD} text-right`}>{pct(m.precision)}</td>
              <td className={`${TD} text-right`}>{pct(m.recall)}</td>
              <td className={`${TD} text-right font-semibold text-slate-900`}>{pct(m.f1)}</td>
              <td className={`${TD} text-right`}>{pct(m.accuracy)}</td>
              <td className={`${TD} text-right`}>{score(m.auc, 3)}</td>
              <td className={`${TD} pr-6 text-right font-mono text-xs`}>
                {m.tp} / {m.fp} / {m.tn} / {m.fn}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Training() {
  const [state, setState] = useState({ loading: true, data: null, error: null, missing: false })

  const load = useCallback(() => {
    let alive = true
    setState((s) => ({ ...s, loading: true, error: null }))
    getTraining()
      .then((data) => alive && setState({ loading: false, data, error: null, missing: false }))
      .catch((err) => {
        if (!alive) return
        const missing = err?.response?.status === 404
        setState({ loading: false, data: null, error: missing ? null : errorMessage(err), missing })
      })
    return () => {
      alive = false
    }
  }, [])

  useEffect(() => load(), [load])

  const header = (
    <PageHeader
      title="Model Training"
      subtitle="How CodeSentry learned its fusion weight and verdict thresholds from 290 labelled pairs, and how well they hold up on assignments the training never saw."
    />
  )

  if (state.loading && !state.data) {
    return (
      <>
        {header}
        <Spinner center label="Loading the training results…" />
      </>
    )
  }
  if (state.missing) {
    return (
      <>
        {header}
        <EmptyState
          title="No training results yet"
          description="Run python training/train_model.py from the project root (after building the dataset), then reload this page."
          action={<Button variant="secondary" onClick={load}>Reload</Button>}
        />
      </>
    )
  }
  if (state.error) {
    return (
      <>
        {header}
        <ErrorBanner title="The training results could not be loaded" message={state.error} onRetry={load} />
      </>
    )
  }

  const { report = {}, points = [], trained } = state.data ?? {}
  const config = trained ?? report.trained_config ?? {}
  const folds = Array.isArray(report.folds) ? report.folds : []
  const cv = meanStd(folds.map((f) => f.calibrated_f1))
  const w = isNumber(config.w_token) && isNumber(config.w_structure) ? config.w_token / (config.w_token + config.w_structure) : 0.5
  const t = isNumber(config.moderate_threshold) ? config.moderate_threshold : 0.5
  const lr = report.logistic_regression ?? {}
  const learned = margins(points, w, t)
  const untrained = margins(points, 0.5, 0.5)
  const positives = report.positives ?? points.filter((p) => p.label === 1).length
  const negatives = report.negatives ?? points.filter((p) => p.label !== 1).length

  return (
    <>
      {header}
      <div className="space-y-8">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Labelled pairs" value={report.pairs ?? points.length} hint={`${positives} copied · ${negatives} honest`} />
          <StatCard
            label="Validation"
            value={`${folds.length || 5}-fold`}
            hint="cross-validation grouped by assignment problem"
          />
          <StatCard
            label="Cross-validated F1 (calibrated hybrid)"
            value={cv ? `${score(cv.mean)} ± ${score(cv.std)}` : '—'}
            hint="mean ± standard deviation over the held-out folds"
            tone="indigo"
          />
          <StatCard
            label="Learned settings"
            value={`${score(config.w_token)} / ${score(config.w_structure)}`}
            hint={`token / structure weight · Moderate ${pct(config.moderate_threshold, 0)} · High ${pct(config.high_threshold, 0)}`}
          />
        </div>

        <Card
          title="The learned decision boundary"
          subtitle="Every labelled pair placed by its token score (x) and structure score (y). Hover a point to see the two files."
        >
          <BoundaryChart points={points} w={w} t={t} />
          <p className="mt-4 text-sm leading-6 text-slate-600">
            Honest solutions to the same assignment share a program skeleton (loops over the marks, a few helper
            functions), so their structure score is often around 0.5 even though no code was copied. Copying, on the
            other hand, always leaves long runs of identical normalised tokens. The learned line therefore leans on the
            token axis: weight {score(w)} on tokens and {score(1 - w)} on structure, with the Moderate threshold at{' '}
            {pct(t, 0)}.{' '}
            {learned.separates
              ? `Every copied pair lies above the solid line and every honest pair below it, with a margin of ${score(learned.copied)} on the copied side and ${score(learned.honest)} on the honest side.`
              : 'Most copied pairs lie above the solid line and most honest pairs below it.'}{' '}
            {untrained.separates
              ? `The dashed untrained line (equal weights, threshold 0.5) also separates this dataset, but the weakest copy clears it by only ${score(untrained.copied)}.`
              : 'The dashed untrained line (equal weights, threshold 0.5) misclassifies some of these pairs.'}
          </p>
        </Card>

        <Card
          title="Cross-validation folds"
          subtitle="Each fold holds out every pair from two assignment problems, learns the weight and threshold on the rest, then scores the held-out pairs."
          bodyClassName="p-0"
        >
          <FoldTable folds={folds} />
          <p className="border-t border-slate-200 px-6 py-4 text-sm leading-6 text-slate-600">
            Grouping by problem prevents leakage: the original, its disguised copies and the independent solutions of
            one assignment are always in the same fold, so the model is never tested on a program whose copies it saw
            during training. The scores therefore estimate performance on a new assignment, not on memorised code.
          </p>
        </Card>

        <div className="grid gap-8 xl:grid-cols-2">
          <Card
            title="Logistic regression coefficients"
            subtitle="Each feature is standardised, so the bar length compares how strongly it pushes a pair towards 'copied' (positive) or 'honest' (negative)."
          >
            {Array.isArray(lr.features) && Array.isArray(lr.weights) ? (
              <CoefficientChart features={lr.features} weights={lr.weights} />
            ) : (
              <p className="text-sm text-slate-500">The report contains no logistic regression model.</p>
            )}
          </Card>
          <Card title="What was learned" subtitle="Stored in engine/trained_config.json and used as the defaults of every new run.">
            <dl className="grid grid-cols-2 gap-4 text-sm">
              {[
                ['k-gram length k', config.k],
                ['Winnowing window w', config.w],
                ['Token weight', score(config.w_token)],
                ['Structure weight', score(config.w_structure)],
                ['Moderate threshold', pct(config.moderate_threshold, 0)],
                ['High threshold', pct(config.high_threshold, 0)],
              ].map(([label, value]) => (
                <div key={label} className="rounded-lg bg-slate-50 px-3 py-2.5">
                  <dt className="text-xs text-slate-500">{label}</dt>
                  <dd className="mt-0.5 font-semibold tabular-nums text-slate-900">{value ?? '—'}</dd>
                </div>
              ))}
            </dl>
            {config.meta?.method && <p className="mt-4 text-sm leading-6 text-slate-600">Method: {config.meta.method}.</p>}
            {config.meta?.high_threshold_rule && (
              <p className="mt-1 text-sm leading-6 text-slate-600">High threshold: {config.meta.high_threshold_rule}.</p>
            )}
          </Card>
        </div>

        <Card
          title="Comparison on held-out pairs"
          subtitle="Every pair scored by a model that never saw its assignment problem during training (pooled over the five folds)."
          bodyClassName="p-0"
        >
          <ComparisonTable comparison={report.comparison_on_held_out_pairs} />
        </Card>
      </div>
    </>
  )
}
