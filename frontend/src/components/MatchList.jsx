// MatchList — the matched regions of a pair, as a clickable list, plus the scrolling controls.
// Props:
//   matches             [{ a_start, a_end, b_start, b_end, tokens }] exactly as the API returns them
//   palette             array of CSS colours; match i uses palette[i % palette.length], the same array the
//                       code panes use, so a list entry and its highlighted blocks share one colour
//   activeIndex         index of the selected match, or -1
//   onSelect            (index) => void; the parent scrolls both code panes to that match
//   syncScroll          boolean — whether the two code panes scroll together
//   onSyncScrollChange  (nextValue) => void
//   className           extra classes for the outer element (the page uses it for layout)
import { useEffect, useRef } from 'react'

/** "Line 7" for a one-line region, otherwise "Lines 12–20". */
function lineRange(start, end) {
  return start === end ? `Line ${start}` : `Lines ${start}–${end}`
}

/** The same range worded for screen readers, which read "–" and "↔" unpredictably. */
function spokenRange(start, end) {
  return start === end ? `line ${start}` : `lines ${start} to ${end}`
}

function Chevron({ direction }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
      <path d={direction === 'up' ? 'm18 15-6-6-6 6' : 'm6 9 6 6 6-6'} />
    </svg>
  )
}

const ICON_BUTTON =
  'flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 ' +
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent'

export default function MatchList({
  matches = [],
  palette,
  activeIndex = -1,
  onSelect,
  syncScroll = false,
  onSyncScrollChange,
  className = '',
}) {
  const listRef = useRef(null)
  const itemRefs = useRef([])
  const count = matches.length

  // Keep the selected entry visible inside the list's own scroll area. The list's scrollTop is set
  // directly instead of calling scrollIntoView, which could also scroll the whole page away from the
  // code panes the reader is trying to look at.
  useEffect(() => {
    const list = listRef.current
    const item = itemRefs.current[activeIndex]
    if (!list || !item) return
    if (item.offsetTop < list.scrollTop) {
      list.scrollTop = item.offsetTop - 8
    } else if (item.offsetTop + item.offsetHeight > list.scrollTop + list.clientHeight) {
      list.scrollTop = item.offsetTop + item.offsetHeight - list.clientHeight + 8
    }
  }, [activeIndex])

  /** Selects an entry, wrapping around at either end, and returns the index actually selected. */
  function select(index) {
    const wrapped = (index + count) % count
    onSelect?.(wrapped)
    return wrapped
  }

  // Arrow keys, Home and End move through the entries like a native list box, so a keyboard user can
  // step through every match without tabbing past each one.
  function handleKeyDown(event, index) {
    const moves = { ArrowDown: index + 1, ArrowRight: index + 1, ArrowUp: index - 1, ArrowLeft: index - 1, Home: 0, End: count - 1 }
    if (!(event.key in moves)) return
    event.preventDefault()
    itemRefs.current[select(moves[event.key])]?.focus()
  }

  const active = matches[activeIndex]

  return (
    <section className={`flex min-w-0 flex-col rounded-xl border border-slate-200 bg-white shadow-sm ${className}`} aria-labelledby="match-list-title">
      <header className="flex items-center justify-between gap-2 border-b border-slate-200 py-3 pl-4 pr-2">
        <div className="min-w-0">
          <h2 id="match-list-title" className="text-sm font-semibold text-slate-900">
            Matched regions
          </h2>
          <p className="text-xs text-slate-500">
            {count === 0 ? 'None found' : `${count} ${count === 1 ? 'region' : 'regions'} · click to line up`}
          </p>
        </div>
        <div className="flex shrink-0 items-center">
          <button
            type="button"
            className={ICON_BUTTON}
            onClick={() => select(activeIndex < 0 ? count - 1 : activeIndex - 1)}
            disabled={count === 0}
            aria-label="Previous match"
          >
            <Chevron direction="up" />
          </button>
          <button type="button" className={ICON_BUTTON} onClick={() => select(activeIndex + 1)} disabled={count === 0} aria-label="Next match">
            <Chevron direction="down" />
          </button>
        </div>
      </header>

      <button
        type="button"
        role="switch"
        aria-checked={syncScroll}
        onClick={() => onSyncScrollChange?.(!syncScroll)}
        className="flex w-full items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 text-left transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500"
      >
        <span className="min-w-0">
          <span className="block text-sm font-medium text-slate-700">Synchronised scrolling</span>
          <span className="block text-xs text-slate-500">Scroll one file and the other follows</span>
        </span>
        <span
          className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors ${syncScroll ? 'bg-indigo-600' : 'bg-slate-300'}`}
          aria-hidden="true"
        >
          <span className={`h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${syncScroll ? 'translate-x-4.5' : 'translate-x-0.5'}`} />
        </span>
      </button>

      {count === 0 ? (
        <div className="px-4 py-8 text-center">
          <p className="text-sm font-medium text-slate-700">No shared code sequences</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            The files have no winnowed fingerprints in common, so there are no line ranges to highlight or
            line up.
          </p>
        </div>
      ) : (
        <ol
          ref={listRef}
          className="relative grid max-h-72 gap-1 overflow-y-auto p-2 sm:grid-cols-2 lg:grid-cols-3 2xl:max-h-[60vh] 2xl:grid-cols-1"
        >
          {matches.map((match, index) => {
            const isActive = index === activeIndex
            const color = palette[index % palette.length]
            return (
              <li key={`${match.a_start}-${match.b_start}-${index}`}>
                <button
                  ref={(element) => {
                    itemRefs.current[index] = element
                  }}
                  type="button"
                  onClick={() => select(index)}
                  onKeyDown={(event) => handleKeyDown(event, index)}
                  aria-current={isActive ? 'true' : undefined}
                  aria-label={`Match ${index + 1}: ${spokenRange(match.a_start, match.a_end)} of file A match ${spokenRange(match.b_start, match.b_end)} of file B, ${match.tokens} tokens`}
                  className={`flex w-full items-start gap-3 rounded-lg px-3 py-2 text-left text-[13px] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                    isActive ? 'bg-indigo-50 ring-1 ring-inset ring-indigo-200' : 'hover:bg-slate-50'
                  }`}
                >
                  <span
                    className={`mt-1 h-3 w-3 shrink-0 rounded-sm ${isActive ? 'ring-2 ring-offset-1' : ''}`}
                    style={{ backgroundColor: color, '--tw-ring-color': color }}
                    aria-hidden="true"
                  />
                  <span className="flex min-w-0 flex-wrap gap-x-1.5 tabular-nums">
                    {/* The "·" separator ends the first part, so in a narrow column the token count
                        wraps onto its own line instead of starting a line with a stray dot. */}
                    <span className={isActive ? 'font-semibold text-slate-900' : 'font-medium text-slate-800'}>
                      {lineRange(match.a_start, match.a_end)} ↔ {lineRange(match.b_start, match.b_end)}
                      <span className="font-normal text-slate-500"> ·</span>
                    </span>
                    <span className="text-slate-500">{match.tokens} tokens</span>
                  </span>
                </button>
              </li>
            )
          })}
        </ol>
      )}

      {/* Announces the selection to screen-reader users, since the visible change happens in the panes. */}
      <p className="sr-only" aria-live="polite">
        {active
          ? `Showing match ${activeIndex + 1} of ${count}: ${spokenRange(active.a_start, active.a_end)} of file A and ${spokenRange(active.b_start, active.b_end)} of file B.`
          : ''}
      </p>
    </section>
  )
}
