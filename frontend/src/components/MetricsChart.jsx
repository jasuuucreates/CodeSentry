// MetricsChart — grouped bar chart of precision, recall and F1 for every detection method.
// Props:
//   rows       [{ key, label, precision, recall, f1 }] in display order (the evaluation's method_order);
//              each metric is a fraction in [0, 1] or null
//   threshold  decision threshold the metrics were measured at (used in the screen-reader summary)
//   className  extra classes for the outer element
//
// The same numbers are always shown in a table next to the chart, so the chart is a quick visual
// comparison and never the only place a value can be read.
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js'
import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import { palette } from '../lib/colors.js'
import { pct, score } from '../lib/format.js'

// Chart.js is tree-shakeable: only the pieces a bar chart needs are registered.
ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

// Series colours. Red, amber and green are reserved for verdicts in CodeSentry, so the metrics use
// sky, violet and indigo. This trio was checked with a colour-vision-deficiency validator: adjacent
// bars stay distinguishable for protanopia, deuteranopia and tritanopia. F1 gets the strongest
// colour (the brand indigo) because it is the headline metric.
const SERIES = [
  { key: 'precision', label: 'Precision', color: '#0284c7' },
  { key: 'recall', label: 'Recall', color: '#a78bfa' },
  { key: 'f1', label: 'F1 score', color: palette.indigo },
]
const F1_LABEL = SERIES[2].label

// Chart.js draws on a canvas, which cannot use CSS font stacks from index.css, so the same system
// stack is passed explicitly (no web fonts: the app must work offline).
const FONT_FAMILY = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
const FONT = { family: FONT_FAMILY, size: 12 }

function isNumber(x) {
  return typeof x === 'number' && Number.isFinite(x)
}

// Prints the F1 value above each F1 bar. Only the headline series is labelled: a number on every
// bar would be unreadable, and the legend, tooltip and table carry the rest. Labels matter here
// because this page is screenshotted into a printed report, where tooltips do not exist.
const f1LabelPlugin = {
  id: 'codesentryF1Labels',
  afterDatasetsDraw(chart) {
    const index = chart.data.datasets.findIndex((dataset) => dataset.label === F1_LABEL)
    if (index < 0 || !chart.isDatasetVisible(index)) return
    const values = chart.data.datasets[index].data
    const { ctx } = chart
    ctx.save()
    ctx.font = `600 11px ${FONT_FAMILY}`
    ctx.fillStyle = palette.text
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    chart.getDatasetMeta(index).data.forEach((bar, i) => {
      if (isNumber(values[i])) ctx.fillText(pct(values[i], 1), bar.x, bar.y - 4)
    })
    ctx.restore()
  },
}

function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

export default function MetricsChart({ rows = [], threshold, className = '' }) {
  const data = useMemo(
    () => ({
      labels: rows.map((row) => row.label),
      datasets: SERIES.map((series) => ({
        label: series.label,
        data: rows.map((row) => (isNumber(row[series.key]) ? row[series.key] : null)),
        backgroundColor: series.color,
        hoverBackgroundColor: series.color,
        // Thin bars with a 4px rounded data end; the baseline end stays square.
        borderRadius: 4,
        maxBarThickness: 24,
        barPercentage: 0.88,
        categoryPercentage: 0.7,
      })),
    }),
    [rows],
  )

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      animation: prefersReducedMotion() ? false : { duration: 500 },
      // Room above the tallest bar for its F1 label.
      layout: { padding: { top: 18 } },
      // Hovering anywhere over a method's group shows all three of its numbers together.
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: {
          grid: { display: false },
          border: { color: palette.slateLight },
          ticks: { color: palette.text, font: FONT },
        },
        y: {
          min: 0,
          max: 1,
          border: { display: false },
          grid: { color: palette.grid },
          ticks: { stepSize: 0.25, color: palette.slate, font: FONT, callback: (value) => pct(value, 0) },
        },
      },
      plugins: {
        legend: {
          // Bottom, not top: the F1 value labels drawn above 100% bars would collide with a top legend.
          position: 'bottom',
          align: 'center',
          labels: {
            color: palette.text,
            font: FONT,
            boxWidth: 12,
            boxHeight: 12,
            useBorderRadius: true,
            borderRadius: 2,
            padding: 16,
          },
        },
        tooltip: {
          backgroundColor: '#0f172a',
          padding: 10,
          cornerRadius: 8,
          boxPadding: 4,
          titleFont: { ...FONT, weight: '600' },
          bodyFont: FONT,
          callbacks: {
            label: (context) => `${context.dataset.label}: ${pct(context.parsed.y)}`,
          },
        },
      },
    }),
    [],
  )

  if (rows.length === 0) return null

  // A canvas is invisible to screen readers, so the chart describes itself in words.
  const summary =
    `Grouped bar chart of precision, recall and F1 score per method` +
    (isNumber(threshold) ? ` at threshold ${score(threshold)}. ` : '. ') +
    rows.map((row) => `${row.label}: precision ${pct(row.precision)}, recall ${pct(row.recall)}, F1 ${pct(row.f1)}`).join('; ')

  return (
    <div className={`relative h-80 w-full ${className}`}>
      <Bar data={data} options={options} plugins={[f1LabelPlugin]} role="img" aria-label={summary} />
    </div>
  )
}
