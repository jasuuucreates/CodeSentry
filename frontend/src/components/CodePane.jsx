// CodePane — one submission's source code with line numbers and its matched regions highlighted.
// Props:
//   ref           receives { scrollToLine(line, offset?), lineOffset(line), applyScrollDelta(dy, dx) }
//   side          short marker shown before the file name, e.g. 'A' or 'B'
//   name          file name, e.g. "student_01.py"
//   language      'python' | 'c'
//   source        full source text (shown exactly: whitespace, tabs and blank lines are preserved)
//   ranges        [{ start, end }] 1-based inclusive line ranges, index-aligned with the pair's matches,
//                 so range i here and range i in the other pane are the same match
//   palette       array of 6-digit hex colours ('#rrggbb'); match i is drawn in palette[i % palette.length].
//                 The page passes the same array to both panes and the match list so colours agree.
//   activeIndex   index of the selected match (-1 for none); its lines are drawn more strongly
//   onSelectMatch (index) => void, called when the reader clicks a highlighted line
//   onUserScroll  (dy, dx) => void, called for scrolling done by the reader (never for scrolling the
//                 pane did itself), which is what lets the parent keep two panes in step
//   className     extra classes for the outer element
import { useImperativeHandle, useMemo, useRef } from 'react'

// Two-digit hex alpha suffixes appended to a palette colour: a light wash for every matched line and a
// stronger one for the selected match.
const TINT_ALPHA = '1f'
const ACTIVE_TINT_ALPHA = '42'

// Pixels of context left above a line the pane scrolls to, so the reader sees what leads into the match.
const CONTEXT_PX = 48

// How long a smooth programmatic scroll may take before it is considered finished anyway (for example
// when the reader grabs the scrollbar half-way through the animation).
const JUMP_TIMEOUT_MS = 1200

const LANGUAGE_LABELS = { python: 'Python', c: 'C' }

// One shared empty list, so a pane without matches does not recompute its line coverage on every render.
const NO_RANGES = []

/**
 * Splits source text into display lines. A final newline ends the last line rather than starting an
 * empty one, so the count agrees with Python's str.splitlines() that the engine uses for line numbers.
 */
function splitLines(text) {
  if (!text) return []
  const lines = text.split(/\r\n|\r|\n/)
  if (lines.length > 1 && lines[lines.length - 1] === '') lines.pop()
  return lines
}

/** Smooth scrolling is a nicety; readers who asked the OS to reduce motion get an instant jump. */
function scrollBehavior() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
}

export default function CodePane({
  ref,
  side,
  name,
  language,
  source,
  ranges = NO_RANGES,
  palette,
  activeIndex = -1,
  onSelectMatch,
  onUserScroll,
  className = '',
}) {
  const scrollRef = useRef(null)
  const linesRef = useRef(null)
  // Last scroll position seen, so each scroll event can be turned into a delta (how far it moved).
  const lastPos = useRef({ top: 0, left: 0 })
  // While the pane animates towards a target it chose itself, its scroll events are not reported as
  // reader scrolling; otherwise synchronised scrolling would drag the other pane along a second time.
  const jump = useRef(null)

  const lines = useMemo(() => splitLines(source), [source])

  // For every line, the indices of the matches covering it (regions may overlap), plus how many lines
  // are covered at all, computed once per source rather than on every render.
  const { coverage, matchedLineCount } = useMemo(() => {
    const cover = new Array(lines.length + 1).fill(null)
    ranges.forEach((range, index) => {
      const first = Math.max(1, range.start)
      const last = Math.min(lines.length, range.end)
      for (let line = first; line <= last; line += 1) {
        if (cover[line]) cover[line].push(index)
        else cover[line] = [index]
      }
    })
    return { coverage: cover, matchedLineCount: cover.filter(Boolean).length }
  }, [lines, ranges])

  function rowFor(line) {
    return linesRef.current?.children[line - 1] ?? null
  }

  function finishJump() {
    if (jump.current) clearTimeout(jump.current.timer)
    jump.current = null
  }

  useImperativeHandle(ref, () => ({
    /**
     * Scrolls so `line` sits `offset` pixels below the top of the visible code; with no usable offset
     * a little context is left above it. The scroll animates on its own.
     */
    scrollToLine(line, offset) {
      const el = scrollRef.current
      const row = rowFor(line)
      if (!el || !row) return
      const usable = typeof offset === 'number' && offset >= 0 && offset <= el.clientHeight - row.offsetHeight
      const desired = row.offsetTop - (usable ? offset : CONTEXT_PX)
      const top = Math.round(Math.max(0, Math.min(el.scrollHeight - el.clientHeight, desired)))
      if (!jump.current && Math.abs(el.scrollTop - top) < 2 && el.scrollLeft === 0) return

      finishJump()
      jump.current = { top, timer: setTimeout(finishJump, JUMP_TIMEOUT_MS) }
      el.scrollTo({ top, left: 0, behavior: scrollBehavior() })
    },

    /** Pixels between the top of the visible code and `line`, or null when the line does not exist. */
    lineOffset(line) {
      const el = scrollRef.current
      const row = rowFor(line)
      return el && row ? row.offsetTop - el.scrollTop : null
    },

    /** Moves the view by the other pane's scroll delta without reporting it back (no echo loop). */
    applyScrollDelta(dy, dx) {
      const el = scrollRef.current
      if (!el || jump.current) return
      el.scrollTop += dy
      el.scrollLeft += dx
      // Reading the clamped position back now means the scroll event this causes carries a zero delta.
      lastPos.current = { top: el.scrollTop, left: el.scrollLeft }
    },
  }))

  function handleScroll() {
    const el = scrollRef.current
    const dy = el.scrollTop - lastPos.current.top
    const dx = el.scrollLeft - lastPos.current.left
    lastPos.current = { top: el.scrollTop, left: el.scrollLeft }

    if (jump.current) {
      if (Math.abs(el.scrollTop - jump.current.top) < 2 && el.scrollLeft === 0) finishJump()
      return
    }
    // Sub-pixel deltas come from rounding on scaled displays; forwarding them would make two synced
    // panes nudge each other back and forth forever.
    if (onUserScroll && (Math.abs(dy) >= 1 || Math.abs(dx) >= 1)) onUserScroll(dy, dx)
  }

  const gutterDigits = Math.max(2, String(lines.length).length)
  const languageLabel = LANGUAGE_LABELS[language] ?? language ?? 'Unknown language'

  return (
    <section
      className={`flex min-w-0 flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}
      aria-label={`File ${side}: ${name}`}
    >
      <header className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-b border-slate-200 px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <span
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-slate-900 text-xs font-semibold text-white"
            aria-hidden="true"
          >
            {side}
          </span>
          <h3 className="min-w-0 truncate font-mono text-sm font-semibold text-slate-900" title={name}>
            {name}
          </h3>
        </div>
        <p className="text-xs text-slate-500 tabular-nums">
          {languageLabel} · {lines.length} {lines.length === 1 ? 'line' : 'lines'}
          {lines.length > 0 && (
            <>
              {' · '}
              <span className="font-medium text-slate-700">{matchedLineCount} matched</span>
            </>
          )}
        </p>
      </header>

      {lines.length === 0 ? (
        <p className="px-4 py-10 text-center text-sm text-slate-500">
          {source == null ? 'The source text of this file is not available.' : 'This file is empty.'}
        </p>
      ) : (
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          tabIndex={0}
          role="region"
          aria-label={`Source code of ${name}`}
          className="relative h-[min(70vh,44rem)] min-h-80 overflow-auto bg-white font-mono text-[13px] leading-5 text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500"
          // Ligatures are switched off because fonts such as Cascadia Code would draw ">=" as "≥": the
          // pane must show exactly the characters the student typed.
          style={{ tabSize: 4, fontVariantLigatures: 'none' }}
        >
          {/* w-max lets long lines widen the content (horizontal scroll) while min-w-full stretches
              short files, so a highlighted line's background always spans the whole pane. */}
          <div ref={linesRef} className="w-max min-w-full py-2">
            {lines.map((text, i) => {
              const lineNumber = i + 1
              const covering = coverage[lineNumber]
              const shown = covering ? (covering.includes(activeIndex) ? activeIndex : covering[0]) : -1
              const isActive = shown !== -1 && shown === activeIndex
              const color = shown === -1 ? null : palette[shown % palette.length]
              const tint = color ? `${color}${isActive ? ACTIVE_TINT_ALPHA : TINT_ALPHA}` : null
              const clickable = Boolean(color && onSelectMatch)

              return (
                <div
                  key={lineNumber}
                  className={`flex ${clickable ? 'cursor-pointer' : ''}`}
                  style={tint ? { backgroundColor: tint } : undefined}
                  onClick={clickable ? () => onSelectMatch(shown) : undefined}
                  title={color ? `Match ${shown + 1}: click to show the matching lines in the other file` : undefined}
                >
                  {/* The gutter sticks to the left edge during horizontal scrolling. It needs an opaque
                      background to hide the code sliding under it; the gradient layers the same tint on
                      top so the highlight still reads as one continuous band. */}
                  <span
                    className={`sticky left-0 z-10 shrink-0 select-none border-r border-slate-200 pl-3 pr-3 text-right tabular-nums ${
                      isActive ? 'font-semibold text-slate-900' : 'text-slate-400'
                    }`}
                    style={{
                      width: `calc(${gutterDigits}ch + 1.75rem)`,
                      backgroundColor: '#f8fafc',
                      backgroundImage: tint ? `linear-gradient(${tint}, ${tint})` : undefined,
                    }}
                  >
                    {color && (
                      <span
                        className={`absolute inset-y-0 left-0 ${isActive ? 'w-1.5' : 'w-1'}`}
                        style={{ backgroundColor: color }}
                        aria-hidden="true"
                      />
                    )}
                    {lineNumber}
                  </span>
                  <span className="whitespace-pre pl-4 pr-6">{text}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </section>
  )
}
