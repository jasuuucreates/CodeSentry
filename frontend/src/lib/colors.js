// Colour helpers. Tailwind classes cannot be computed at runtime (the heat map needs one colour per
// similarity value) and Chart.js needs plain colour strings, so those colours are defined here.

/** Hex values of the design palette, for places that cannot use Tailwind classes (Chart.js). */
export const palette = {
  indigo: '#4f46e5',
  indigoLight: '#a5b4fc',
  slate: '#64748b',
  slateLight: '#cbd5e1',
  grid: '#e2e8f0',
  text: '#334155',
  red: '#dc2626',
  amber: '#d97706',
  green: '#16a34a',
}

// Colour stops of the heat-map scale as [score, [r, g, b]]. Low similarity is a pale green that
// recedes into the page, moderate similarity turns amber and high similarity becomes a strong red,
// so suspicious pairs are the cells the eye is drawn to.
const STOPS = [
  [0.0, [240, 253, 244]],
  [0.3, [187, 247, 208]],
  [0.5, [253, 230, 138]],
  [0.75, [251, 146, 60]],
  [1.0, [220, 38, 38]],
]

const NULL_COLOR = 'rgb(226, 232, 240)'

function interpolate(x) {
  const v = Math.min(1, Math.max(0, x))
  for (let i = 1; i < STOPS.length; i += 1) {
    const [hi, hiRgb] = STOPS[i]
    if (v <= hi) {
      const [lo, loRgb] = STOPS[i - 1]
      const t = (v - lo) / (hi - lo)
      return loRgb.map((c, k) => Math.round(c + (hiRgb[k] - c) * t))
    }
  }
  return STOPS[STOPS.length - 1][1]
}

function isNumber(x) {
  return typeof x === 'number' && Number.isFinite(x)
}

/** Continuous heat-map colour for a score in [0, 1] as "rgb(r, g, b)"; null (not compared) -> grey. */
export function scoreColor(x) {
  if (!isNumber(x)) return NULL_COLOR
  const [r, g, b] = interpolate(x)
  return `rgb(${r}, ${g}, ${b})`
}

/**
 * Readable text colour to place on top of scoreColor(x): dark on pale cells, white on strong ones.
 * Uses the relative-luminance formula from WCAG so the choice follows perceived brightness.
 */
export function scoreTextColor(x) {
  if (!isNumber(x)) return '#475569'
  const [r, g, b] = interpolate(x).map((c) => {
    const s = c / 255
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4
  })
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
  return luminance > 0.4 ? '#0f172a' : '#ffffff'
}

/** Verdict -> Badge tone: "High" -> "red", "Moderate" -> "amber", "Low" -> "green", else "neutral". */
export function verdictTone(v) {
  switch (String(v ?? '').toLowerCase()) {
    case 'high':
      return 'red'
    case 'moderate':
      return 'amber'
    case 'low':
      return 'green'
    default:
      return 'neutral'
  }
}
