// Display formatting helpers shared by every page, so a score or date looks identical everywhere.

const DASH = '—'

/** True for real finite numbers; null, undefined, NaN and non-numbers are treated as "no value". */
function isNumber(x) {
  return typeof x === 'number' && Number.isFinite(x)
}

/** 0.873 -> "87.3%"; null/undefined/NaN -> "—". Scores in the API are fractions in [0, 1]. */
export function pct(x, digits = 1) {
  if (!isNumber(x)) return DASH
  return `${(x * 100).toFixed(digits)}%`
}

/** 0.8734 -> "0.87"; null/undefined/NaN -> "—". */
export function score(x, digits = 2) {
  if (!isNumber(x)) return DASH
  return x.toFixed(digits)
}

const DATE_TIME = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

/** ISO 8601 string -> localized "15 Sept 2026, 10:42 am" style text; missing or invalid -> "—". */
export function dateTime(iso) {
  if (!iso) return DASH
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return DASH
  return DATE_TIME.format(date)
}

/** Milliseconds -> "812 ms" below one second, otherwise "1.24 s"; missing -> "—". */
export function duration(ms) {
  if (!isNumber(ms)) return DASH
  if (ms < 1000) return `${Math.round(ms)} ms`
  return `${(ms / 1000).toFixed(2)} s`
}
