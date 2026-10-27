// ScoreHistogram — how the fused scores of a run are distributed, as a Chart.js bar chart.
// Props:
//   pairs   run.pairs — PairResult objects; only scores.fused and verdict are used
//   config  run.config — high_threshold and moderate_threshold define the verdict bands in the caption
//
// Scores are counted in ten buckets (0–10%, 10–20%, … 90–100%). A bucket can straddle a threshold
// (with the default 75% threshold, 70–80% holds both Moderate and High pairs), so each bar is stacked
// by verdict instead of being painted one colour: the colours then never misreport a pair's verdict.
import { BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip } from 'chart.js'
import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import { palette } from '../lib/colors.js'
import { pct } from '../lib/format.js'

// Chart.js is tree-shakable: only the pieces a bar chart needs are registered.
ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const BUCKETS = 10
const FONT = { family: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif', size: 12 }
const LABELS = Array.from({ length: BUCKETS }, (_, i) => `${i * 10}–${(i + 1) * 10}%`)

// Stack order bottom to top follows the score axis: Low, then Moderate, then High.
const BANDS = [
  { verdict: 'Low', color: palette.green, swatch: 'bg-green-600' },
  { verdict: 'Moderate', color: palette.amber, swatch: 'bg-amber-600' },
  { verdict: 'High', color: palette.red, swatch: 'bg-red-600' },
]

/** Bucket index of a score; the tiny epsilon stops 0.3 * 10 = 2.9999… from landing one bucket low. */
function bucketOf(value) {
  return Math.min(BUCKETS - 1, Math.max(0, Math.floor(value * BUCKETS + 1e-9)))
}

function plural(n) {
  return `${n} ${n === 1 ? 'pair' : 'pairs'}`
}

export default function ScoreHistogram({ pairs = [], config }) {
  const high = config?.high_threshold ?? 0.75
  const moderate = config?.moderate_threshold ?? 0.5

  const counts = useMemo(() => {
    const result = Object.fromEntries(BANDS.map((band) => [band.verdict, new Array(BUCKETS).fill(0)]))
    for (const pair of pairs) {
      const value = pair.scores?.fused
      if (typeof value !== 'number' || !Number.isFinite(value)) continue
      // The pair's own verdict is used so the chart always agrees with the badges in the table.
      let verdict = pair.verdict
      if (!(verdict in result)) verdict = value >= high ? 'High' : value >= moderate ? 'Moderate' : 'Low'
      result[verdict][bucketOf(value)] += 1
    }
    return result
  }, [pairs, high, moderate])

  // Memoised so the chart options keep the same identity between renders and Chart.js does not redraw.
  const totals = useMemo(() => LABELS.map((_, i) => BANDS.reduce((sum, band) => sum + counts[band.verdict][i], 0)), [counts])
  const counted = totals.reduce((sum, n) => sum + n, 0)

  const data = useMemo(
    () => ({
      labels: LABELS,
      datasets: BANDS.map((band) => ({
        label: band.verdict,
        data: counts[band.verdict],
        backgroundColor: band.color,
        hoverBackgroundColor: band.color,
        borderRadius: 3,
        borderSkipped: false,
        maxBarThickness: 56,
      })),
    }),
    [counts],
  )

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f172a',
          padding: 10,
          cornerRadius: 8,
          boxPadding: 4,
          titleFont: { ...FONT, weight: '600' },
          bodyFont: FONT,
          footerFont: { ...FONT, weight: '400' },
          // Hide the verdicts with no pairs in the hovered bucket instead of listing "0 pairs".
          filter: (item) => item.parsed.y > 0,
          callbacks: {
            title: (items) => (items.length ? `Fused score ${items[0].label}` : ''),
            label: (item) => `${item.dataset.label}: ${plural(item.parsed.y)}`,
            footer: (items) => (items.length > 1 ? `Total: ${plural(totals[items[0].dataIndex])}` : ''),
          },
        },
      },
      scales: {
        x: {
          stacked: true,
          grid: { display: false },
          border: { color: palette.slateLight },
          ticks: { color: palette.text, font: FONT },
          title: { display: true, text: 'Fused similarity score', color: palette.slate, font: FONT },
        },
        y: {
          stacked: true,
          beginAtZero: true,
          border: { display: false },
          grid: { color: palette.grid },
          ticks: { color: palette.text, font: FONT, precision: 0 },
          title: { display: true, text: 'Number of pairs', color: palette.slate, font: FONT },
        },
      },
    }),
    [totals],
  )

  if (counted === 0) {
    return <p className="text-sm text-slate-500">No pair in this run has a fused score, so there is no distribution to show.</p>
  }

  const bandText = {
    High: `${pct(high, 0)} or above`,
    Moderate: `${pct(moderate, 0)} to below ${pct(high, 0)}`,
    Low: `below ${pct(moderate, 0)}`,
  }

  return (
    <figure>
      <div className="relative h-72">
        <Bar
          data={data}
          options={options}
          role="img"
          aria-label={`Histogram of ${plural(counted)} by fused score. ${LABELS.map((label, i) => `${label}: ${totals[i]}`).join(', ')}.`}
        />
      </div>

      {/* Screen-reader copy of the chart. The wrapper div is what gets hidden: a <table> ignores the 1px
          width of sr-only and would stretch the page on narrow screens. */}
      <div className="sr-only">
        <table>
          <caption>Number of pairs per fused score range and verdict</caption>
          <thead>
            <tr>
              <th scope="col">Score range</th>
              {BANDS.map((band) => (
                <th key={band.verdict} scope="col">
                  {band.verdict}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {LABELS.map((label, i) => (
              <tr key={label}>
                <th scope="row">{label}</th>
                {BANDS.map((band) => (
                  <td key={band.verdict}>{counts[band.verdict][i]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <figcaption className="mt-4 space-y-3 border-t border-slate-100 pt-4 text-sm leading-6 text-slate-600">
        <ul className="flex flex-wrap gap-x-6 gap-y-2" aria-label="Verdict bands of this run">
          {[...BANDS].reverse().map((band) => (
            <li key={band.verdict} className="flex items-center gap-2">
              <span className={`h-3 w-3 rounded-sm ${band.swatch}`} aria-hidden="true" />
              <span className="font-medium text-slate-800">{band.verdict}</span>
              <span className="text-slate-500">{bandText[band.verdict]}</span>
            </li>
          ))}
        </ul>
        <p>
          Each bar counts the pairs whose fused score falls in that 10-point range, split by verdict using this
          run&rsquo;s thresholds. Independent solutions to the same assignment normally pile up on the left, because
          every student still uses similar keywords and loops; bars standing apart on the right are the pairs to
          review first.
        </p>
      </figcaption>
    </figure>
  )
}
