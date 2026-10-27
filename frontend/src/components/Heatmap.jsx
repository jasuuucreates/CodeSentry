// Heatmap — the N x N similarity matrix of one analysis run, drawn as a CSS grid (no chart library).
// Props:
//   files   run.files  — [{id, name, language, ...}], in the same order as the matrix
//   matrix  run.matrix — fused scores; matrix[r][c] compares files[r] with files[c]; null = not compared
//   pairs   run.pairs  — optional; used so a cell shows exactly the verdict the pairs table shows
//   runId   id of the run, used to build the pair comparison link
//   config  run.config — its thresholds classify a cell when no pair verdict is available
//
// Reading the grid: row file vs column file. Each cell's colour comes from scoreColor(), so the eye is
// drawn to red (near-identical) cells. The matrix is symmetric, which is why every pair appears twice,
// mirrored across the dark diagonal where a file meets itself.
//
// Performance: a 200-file run has 40,000 cells. Rows are memoised and hover/focus is handled by one
// delegated listener on the grid, so moving the mouse re-renders only the rows whose highlight changes.
import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { scoreColor, scoreTextColor } from '../lib/colors.js'
import { pct } from '../lib/format.js'

const GAP_PX = 2
const DIAGONAL_COLOR = '#475569'
// Diagonal stripes set "not compared" cells apart from low scores, which are also pale.
const HATCH = 'repeating-linear-gradient(45deg, #e2e8f0 0px, #e2e8f0 3px, #f8fafc 3px, #f8fafc 6px)'
const LANGUAGE_TAGS = { python: 'PY', c: 'C' }

function isNumber(x) {
  return typeof x === 'number' && Number.isFinite(x)
}

/** The pair route and lookup are order-insensitive, so the key always puts the smaller id first. */
function pairKey(aId, bId) {
  return aId < bId ? `${aId}:${bId}` : `${bId}:${aId}`
}

/** Same rule as engine/fusion.py verdict(): at or above high -> High, at or above moderate -> Moderate. */
function verdictFor(value, config) {
  const high = config?.high_threshold ?? 0.75
  const moderate = config?.moderate_threshold ?? 0.5
  if (value >= high) return 'High'
  if (value >= moderate) return 'Moderate'
  return 'Low'
}

function stripPath(name) {
  return name.split(/[\\/]/).pop()
}

function stripExtension(name) {
  const dot = name.lastIndexOf('.')
  return dot > 0 ? name.slice(0, dot) : name
}

/**
 * Short axis labels. A class batch usually shares a prefix ("student_01.py", "student_02.py"), which
 * would waste most of every label, so the common prefix (cut at a separator) and the extension are
 * dropped: "student_01.py" -> "01". If that makes two labels identical (e.g. "a.py" and "a.c") the
 * full file names are used instead. Returns the labels and the prefix that was removed.
 */
function buildLabels(files) {
  const bases = files.map((file) => stripExtension(stripPath(String(file.name ?? ''))))
  let prefix = ''
  if (bases.length > 1) {
    prefix = bases.reduce((common, base) => {
      let i = 0
      while (i < common.length && i < base.length && common[i] === base[i]) i += 1
      return common.slice(0, i)
    })
    const cut = Math.max(prefix.lastIndexOf('_'), prefix.lastIndexOf('-'), prefix.lastIndexOf('.'), prefix.lastIndexOf(' '))
    prefix = cut >= 0 ? prefix.slice(0, cut + 1) : ''
  }

  let labels = bases.map((base) => base.slice(prefix.length) || base)
  if (new Set(labels).size !== labels.length) {
    labels = files.map((file) => stripPath(String(file.name ?? '')))
    prefix = ''
  }
  return {
    prefix,
    labels: labels.map((label) => (label.length > 14 ? `${label.slice(0, 13)}…` : label)),
  }
}

/** Cells shrink as the class grows so a large run still fits a reasonable scroll width. */
function cellSizeFor(count) {
  if (count <= 16) return 44
  if (count <= 30) return 34
  if (count <= 60) return 24
  return 16
}

const HeatmapRow = memo(function HeatmapRow({ rowIndex, file, label, values, count, cellSize, template, activeCol, highlighted, describe }) {
  const cells = []
  for (let c = 0; c < count; c += 1) {
    const info = describe(rowIndex, c)
    const value = values?.[c]
    let style
    let content = null
    if (info.kind === 'self') {
      style = { backgroundColor: DIAGONAL_COLOR }
    } else if (info.kind === 'none') {
      style = { backgroundImage: HATCH }
    } else {
      style = { backgroundColor: scoreColor(value), color: scoreTextColor(value) }
      if (cellSize >= 34) content = Math.round(value * 100)
    }

    cells.push(
      <div
        key={c}
        role="gridcell"
        data-r={rowIndex}
        data-c={c}
        tabIndex={activeCol === c ? 0 : -1}
        aria-label={info.detail ? `${info.text}. ${info.detail}` : info.text}
        className={`relative flex select-none items-center justify-center rounded-[3px] text-[11px] font-medium tabular-nums outline-none focus-visible:z-[5] focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-1 ${
          info.clickable ? 'cursor-pointer hover:z-[5] hover:ring-2 hover:ring-slate-900' : 'cursor-default'
        }`}
        style={{ ...style, height: cellSize }}
      >
        {content}
      </div>,
    )
  }

  return (
    <div role="row" className="grid" style={{ gridTemplateColumns: template, columnGap: GAP_PX }}>
      <div
        role="rowheader"
        data-header="row"
        data-index={rowIndex}
        aria-label={file.name}
        className={`sticky left-0 z-10 flex min-w-0 items-center justify-between gap-2 bg-white pr-2 text-xs ${
          highlighted ? 'font-semibold text-indigo-700' : 'text-slate-600'
        }`}
      >
        <span className="truncate font-mono" aria-hidden="true">
          {label}
        </span>
        <span className="shrink-0 text-[10px] font-semibold tracking-wide text-slate-400" aria-hidden="true">
          {LANGUAGE_TAGS[file.language] ?? String(file.language ?? '').toUpperCase()}
        </span>
      </div>
      {cells}
    </div>
  )
})

/** 0–100% colour ramp sampled from scoreColor(), plus swatches for the two special cell kinds. */
function Legend({ prefix }) {
  const ramp = Array.from({ length: 11 }, (_, i) => `${scoreColor(i / 10)} ${i * 10}%`).join(', ')
  return (
    <div className="mt-5 flex flex-wrap items-end gap-x-8 gap-y-4 text-xs text-slate-600">
      <div className="w-full max-w-xs">
        <p className="mb-1.5 font-medium text-slate-700">Fused similarity</p>
        <div className="h-3 rounded-sm ring-1 ring-inset ring-slate-900/5" style={{ backgroundImage: `linear-gradient(to right, ${ramp})` }} aria-hidden="true" />
        <div className="mt-1 flex justify-between tabular-nums text-slate-500" aria-hidden="true">
          <span>0%</span>
          <span>25%</span>
          <span>50%</span>
          <span>75%</span>
          <span>100%</span>
        </div>
        <p className="sr-only">Colour scale from pale green at 0% through amber at 50% to red at 100%.</p>
      </div>
      <div className="flex items-center gap-2">
        <span className="h-4 w-4 rounded-[3px]" style={{ backgroundColor: DIAGONAL_COLOR }} aria-hidden="true" />
        Same file
      </div>
      <div className="flex items-center gap-2">
        <span className="h-4 w-4 rounded-[3px] ring-1 ring-inset ring-slate-300" style={{ backgroundImage: HATCH }} aria-hidden="true" />
        Not compared
      </div>
      {prefix && (
        <p className="text-slate-500">
          Labels omit the shared prefix <span className="font-mono text-slate-700">{prefix}</span> and the file extension.
        </p>
      )}
    </div>
  )
}

export default function Heatmap({ files = [], matrix = [], pairs = [], runId, config }) {
  const navigate = useNavigate()
  const gridRef = useRef(null)
  const focusPending = useRef(false)
  const count = files.length

  const [hover, setHover] = useState(null) // {r, c} of the hovered or focused cell
  const [tooltip, setTooltip] = useState(null) // {x, y, below, title, detail, hint}
  const [active, setActive] = useState({ r: 0, c: count > 1 ? 1 : 0 }) // roving tab stop

  const { labels, prefix } = useMemo(() => buildLabels(files), [files])

  const verdicts = useMemo(() => {
    const map = new Map()
    for (const pair of pairs) map.set(pairKey(pair.a_id, pair.b_id), pair.verdict)
    return map
  }, [pairs])

  // One description per cell drives the tooltip, the screen-reader label and whether a click navigates.
  const describe = useCallback(
    (r, c) => {
      const a = files[r]
      const b = files[c]
      if (r === c) return { kind: 'self', clickable: false, text: `${a.name} — same file` }
      const value = matrix?.[r]?.[c]
      if (!isNumber(value)) {
        const reason = a.language !== b.language ? 'different languages' : 'one of the files could not be analysed'
        return { kind: 'none', clickable: false, text: `${a.name} vs ${b.name}`, detail: `Not compared — ${reason}` }
      }
      const verdict = verdicts.get(pairKey(a.id, b.id)) ?? verdictFor(value, config)
      return { kind: 'score', clickable: true, text: `${a.name} vs ${b.name} — ${pct(value)} (${verdict})` }
    },
    [files, matrix, verdicts, config],
  )

  const cellSize = cellSizeFor(count)
  const labelChars = Math.max(4, ...labels.map((label) => label.length))
  const template = `calc(${labelChars}ch + 2.75rem) repeat(${count}, ${cellSize}px)`
  const verticalHeaders = labelChars > 3
  const safeActive = active.r < count && active.c < count ? active : { r: 0, c: 0 }

  // Keyboard focus follows the roving tab stop after an arrow key moves it.
  useEffect(() => {
    if (!focusPending.current) return
    focusPending.current = false
    gridRef.current?.querySelector(`[data-r="${safeActive.r}"][data-c="${safeActive.c}"]`)?.focus()
  }, [safeActive.r, safeActive.c])

  // A fixed-position tooltip would drift away from its cell while the page scrolls, so hide it instead.
  useEffect(() => {
    if (!tooltip) return undefined
    const hide = () => setTooltip(null)
    window.addEventListener('scroll', hide, true)
    window.addEventListener('resize', hide)
    return () => {
      window.removeEventListener('scroll', hide, true)
      window.removeEventListener('resize', hide)
    }
  }, [tooltip])

  const showFor = useCallback(
    (element) => {
      const rect = element.getBoundingClientRect()
      const below = rect.top < 72
      const half = Math.min(150, window.innerWidth / 2)
      const x = Math.min(Math.max(rect.left + rect.width / 2, half), window.innerWidth - half)
      const y = below ? rect.bottom + 8 : rect.top - 8

      if (element.dataset.header) {
        const index = Number(element.dataset.index)
        const file = files[index]
        setHover(element.dataset.header === 'row' ? { r: index, c: -1 } : { r: -1, c: index })
        setTooltip({ x, y, below, title: file.name, detail: `${file.language === 'c' ? 'C' : 'Python'} · ${file.lines ?? '—'} lines` })
        return
      }

      const r = Number(element.dataset.r)
      const c = Number(element.dataset.c)
      const info = describe(r, c)
      setHover({ r, c })
      setTooltip({ x, y, below, title: info.text, detail: info.detail, hint: info.clickable ? 'Click to compare side by side' : null })
    },
    [describe, files],
  )

  const targetOf = (event) => event.target.closest?.('[data-r], [data-header]')

  const handleOver = (event) => {
    const element = targetOf(event)
    if (element && gridRef.current?.contains(element)) showFor(element)
  }

  const clearHover = () => {
    setHover(null)
    setTooltip(null)
  }

  const handleClick = (event) => {
    const element = event.target.closest?.('[data-r]')
    if (!element) return
    const r = Number(element.dataset.r)
    const c = Number(element.dataset.c)
    setActive({ r, c })
    if (describe(r, c).clickable) navigate(`/runs/${runId}/pairs/${files[r].id}/${files[c].id}`)
  }

  const handleKeyDown = (event) => {
    const element = event.target.closest?.('[data-r]')
    if (!element) return
    const r = Number(element.dataset.r)
    const c = Number(element.dataset.c)
    const last = count - 1
    const moves = {
      ArrowUp: { r: Math.max(0, r - 1), c },
      ArrowDown: { r: Math.min(last, r + 1), c },
      ArrowLeft: { r, c: Math.max(0, c - 1) },
      ArrowRight: { r, c: Math.min(last, c + 1) },
      Home: { r, c: 0 },
      End: { r, c: last },
    }

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      if (describe(r, c).clickable) navigate(`/runs/${runId}/pairs/${files[r].id}/${files[c].id}`)
      return
    }
    const next = moves[event.key]
    if (!next) return
    event.preventDefault()
    if (next.r === r && next.c === c) return
    focusPending.current = true
    setActive(next)
  }

  if (count === 0) {
    return <p className="text-sm text-slate-500">This run contains no files, so there is no matrix to draw.</p>
  }

  return (
    <div>
      <div className="overflow-x-auto pb-2" style={{ scrollPaddingLeft: `calc(${labelChars}ch + 3rem)` }}>
        <div
          ref={gridRef}
          role="grid"
          aria-label={`Similarity matrix of ${count} files. Use the arrow keys to move between cells and Enter to open a pair.`}
          aria-rowcount={count + 1}
          aria-colcount={count + 1}
          className="flex w-max flex-col"
          style={{ rowGap: GAP_PX }}
          onMouseOver={handleOver}
          onMouseLeave={clearHover}
          onFocus={(event) => {
            const element = targetOf(event)
            if (element) showFor(element)
          }}
          onBlur={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget)) clearHover()
          }}
          onClick={handleClick}
          onKeyDown={handleKeyDown}
        >
          <div role="row" className="grid" style={{ gridTemplateColumns: template, columnGap: GAP_PX }}>
            <div role="columnheader" className="sticky left-0 z-10 flex items-end bg-white pb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              File
            </div>
            {files.map((file, c) => (
              <div
                key={file.id ?? c}
                role="columnheader"
                data-header="col"
                data-index={c}
                aria-label={file.name}
                className={`flex items-end justify-center pb-1.5 font-mono text-xs ${
                  hover?.c === c ? 'font-semibold text-indigo-700' : 'text-slate-600'
                }`}
              >
                <span
                  aria-hidden="true"
                  className="whitespace-nowrap"
                  style={verticalHeaders ? { writingMode: 'vertical-rl', transform: 'rotate(180deg)' } : undefined}
                >
                  {labels[c]}
                </span>
              </div>
            ))}
          </div>

          {files.map((file, r) => (
            <HeatmapRow
              key={file.id ?? r}
              rowIndex={r}
              file={file}
              label={labels[r]}
              values={matrix?.[r]}
              count={count}
              cellSize={cellSize}
              template={template}
              activeCol={safeActive.r === r ? safeActive.c : -1}
              highlighted={hover?.r === r}
              describe={describe}
            />
          ))}
        </div>
      </div>

      <Legend prefix={prefix} />

      {tooltip && (
        <div
          role="tooltip"
          className="pointer-events-none fixed z-50 max-w-[300px] rounded-lg bg-slate-900 px-3 py-2 text-xs leading-5 text-white shadow-lg"
          style={{ left: tooltip.x, top: tooltip.y, transform: `translate(-50%, ${tooltip.below ? '0' : '-100%'})` }}
        >
          <p className="font-medium">{tooltip.title}</p>
          {tooltip.detail && <p className="text-slate-300">{tooltip.detail}</p>}
          {tooltip.hint && <p className="text-slate-400">{tooltip.hint}</p>}
        </div>
      )}
    </div>
  )
}
