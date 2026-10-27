// PipelineExplainer — runs the real detection engine on two short snippets and shows what every
// stage produced, so the pipeline described on the How It Works page can be demonstrated live.
// Props: none. Calls POST /api/explain and GET /api/config/defaults through api/client.js.
//
// The snippets start as an original function and a disguised copy of it (renamed variables, a for
// loop rewritten as a while loop, an added comment). Stepping through the tabs shows why those
// disguises do not hide the copy: the normalised symbols, shared fingerprints and loop nodes line up.
import { useEffect, useMemo, useRef, useState } from 'react'
import { errorMessage, explain, getDefaults } from '../api/client.js'
import Badge from './ui/Badge.jsx'
import Button from './ui/Button.jsx'
import ErrorBanner from './ui/ErrorBanner.jsx'
import ScoreBar from './ui/ScoreBar.jsx'
import { palette } from '../lib/colors.js'
import { pct, score } from '../lib/format.js'

const SAMPLES = {
  python: {
    a: `def average(marks):
    total = 0
    for i in range(len(marks)):
        total += marks[i]
    return total / len(marks)
`,
    b: `def mean_score(scores):
    # add up every score, then divide by how many there are
    s = 0
    j = 0
    while j < len(scores):
        s += scores[j]
        j += 1
    return s / len(scores)
`,
  },
  c: {
    a: `int sum_array(int arr[], int n) {
    int total = 0;
    for (int i = 0; i < n; i++) {
        total += arr[i];
    }
    return total;
}
`,
    b: `int add_all(int values[], int count) {
    /* accumulate every element of the array */
    int acc = 0;
    int k = 0;
    while (k < count) {
        acc += values[k];
        k++;
    }
    return acc;
}
`,
  },
}

const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'c', label: 'C' },
]

const INDENT = '    '

const TABS = [
  { id: 'tokens', label: 'Tokens' },
  { id: 'kgrams', label: 'k-grams' },
  { id: 'fingerprints', label: 'Fingerprints' },
  { id: 'trees', label: 'Skeleton trees' },
  { id: 'score', label: 'Final score' },
]

const SIDES = [
  { key: 'a', title: 'Snippet A', role: 'original' },
  { key: 'b', title: 'Snippet B', role: 'suspected copy' },
]

function isNumber(x) {
  return typeof x === 'number' && Number.isFinite(x)
}

function plural(n, word) {
  return `${n} ${word}${n === 1 ? '' : 's'}`
}

function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

// ---------------------------------------------------------------------------------------------
// Code editor
// ---------------------------------------------------------------------------------------------

/**
 * Monospace textarea with line numbers. Tab inserts spaces (or indents the selected lines) and
 * Shift+Tab outdents, as in a code editor. Because that takes over the Tab key, pressing Escape
 * first lets the next Tab move focus onward, so keyboard users are never trapped in the editor.
 */
function CodeEditor({ id, label, hint, value, onChange }) {
  const gutterRef = useRef(null)
  const releaseTab = useRef(false)
  const lineCount = Math.max(1, value.split('\n').length)

  function handleKeyDown(event) {
    if (event.key === 'Escape') {
      releaseTab.current = true
      return
    }
    const leaving = releaseTab.current
    releaseTab.current = false
    if (event.key !== 'Tab' || leaving || event.ctrlKey || event.altKey || event.metaKey) return

    event.preventDefault()
    const el = event.currentTarget
    const { selectionStart: start, selectionEnd: end, value: text } = el

    if (!event.shiftKey && !text.slice(start, end).includes('\n')) {
      // Plain Tab inside one line: type four spaces, like pressing space four times.
      el.setRangeText(INDENT, start, end, 'end')
    } else {
      // Indent or outdent every line the selection touches. A selection that ends right after a
      // line break does not include the next line, matching how code editors behave.
      const lineStart = text.lastIndexOf('\n', start - 1) + 1
      let blockEnd
      if (end > start && text[end - 1] === '\n') blockEnd = end - 1
      else blockEnd = text.indexOf('\n', end) === -1 ? text.length : text.indexOf('\n', end)

      const lines = text.slice(lineStart, blockEnd).split('\n')
      const changed = event.shiftKey ? lines.map((line) => line.replace(/^ {1,4}/, '')) : lines.map((line) => INDENT + line)
      el.setRangeText(changed.join('\n'), lineStart, blockEnd, 'select')

      if (start === end) {
        const shift = changed[0].length - lines[0].length
        const caret = Math.max(lineStart, start + shift)
        el.setSelectionRange(caret, caret)
      }
    }
    // setRangeText edits the DOM directly and fires no React change event, so state is updated
    // by hand. The DOM already holds the new text, so React keeps the caret where it is.
    onChange(el.value)
  }

  return (
    <div className="min-w-0">
      <label htmlFor={id} className="block text-sm font-medium text-slate-800">
        {label}
      </label>
      <p id={`${id}-hint`} className="mt-0.5 text-xs text-slate-500">
        {hint}
      </p>
      <div className="mt-2 flex overflow-hidden rounded-lg border border-slate-300 bg-white shadow-sm focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/40">
        <div
          ref={gutterRef}
          aria-hidden="true"
          className="shrink-0 select-none overflow-hidden border-r border-slate-200 bg-slate-50 px-2.5 pb-8 pt-3 text-right font-mono text-xs leading-6 text-slate-400"
        >
          {Array.from({ length: lineCount }, (_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>
        <textarea
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          onScroll={(event) => {
            if (gutterRef.current) gutterRef.current.scrollTop = event.currentTarget.scrollTop
          }}
          aria-describedby={`${id}-hint`}
          wrap="off"
          spellCheck={false}
          autoCapitalize="off"
          autoCorrect="off"
          autoComplete="off"
          rows={10}
          className="block h-64 min-h-40 w-full resize-y overflow-auto whitespace-pre bg-white px-3 py-3 font-mono text-[13px] leading-6 text-slate-800 focus-visible:outline-none"
        />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------------------------
// Shared pieces of the result panels
// ---------------------------------------------------------------------------------------------

function SideHeading({ side, meta }) {
  return (
    <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
      <h4 className="text-sm font-semibold text-slate-900">
        {side.title} <span className="font-normal text-slate-500">({side.role})</span>
      </h4>
      {meta && <p className="text-xs text-slate-500">{meta}</p>}
    </div>
  )
}

function Intro({ children }) {
  return <p className="mb-5 max-w-3xl text-sm leading-6 text-slate-600">{children}</p>
}

function TruncationNote({ shown, total, noun }) {
  if (!isNumber(total) || shown >= total) return null
  return (
    <p className="mt-2 text-xs text-slate-500">
      Showing the first {shown} of {plural(total, noun)}.
    </p>
  )
}

function Mono({ children }) {
  return <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[12px] text-slate-800">{children}</code>
}

// ---------------------------------------------------------------------------------------------
// Step 1: tokens
// ---------------------------------------------------------------------------------------------

const RAW_KIND_STYLES = {
  KEYWORD: 'bg-indigo-50 text-indigo-700 ring-1 ring-inset ring-indigo-600/20',
  IDENT: 'bg-sky-50 text-sky-800 ring-1 ring-inset ring-sky-600/20',
  NUMBER: 'bg-violet-50 text-violet-700 ring-1 ring-inset ring-violet-600/20',
  STRING: 'bg-violet-50 text-violet-700 ring-1 ring-inset ring-violet-600/20',
  CHAR: 'bg-violet-50 text-violet-700 ring-1 ring-inset ring-violet-600/20',
  OP: 'bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-500/20',
  INDENT: 'bg-white text-slate-500 ring-1 ring-inset ring-slate-300',
  DEDENT: 'bg-white text-slate-500 ring-1 ring-inset ring-slate-300',
  COMMENT: 'border border-dashed border-slate-300 bg-white text-slate-400 line-through',
  PREPROC: 'border border-dashed border-slate-300 bg-white text-slate-400 line-through',
}

const KIND_LEGEND = [
  { label: 'Keyword', className: RAW_KIND_STYLES.KEYWORD },
  { label: 'Name (identifier)', className: RAW_KIND_STYLES.IDENT },
  { label: 'Literal', className: RAW_KIND_STYLES.NUMBER },
  { label: 'Operator / punctuation', className: RAW_KIND_STYLES.OP },
  { label: 'Indentation', className: RAW_KIND_STYLES.INDENT },
  { label: 'Removed (comment / #directive)', className: RAW_KIND_STYLES.COMMENT },
]

const PLACEHOLDER_SYMBOLS = new Set(['ID', 'NUM', 'STR', 'CHR', 'INDENT', 'DEDENT'])

function symbolStyle(symbol) {
  if (symbol === 'ID') return RAW_KIND_STYLES.IDENT
  if (symbol === 'NUM' || symbol === 'STR' || symbol === 'CHR') return RAW_KIND_STYLES.NUMBER
  if (symbol === 'INDENT' || symbol === 'DEDENT') return RAW_KIND_STYLES.INDENT
  // Any other word-like symbol is a keyword kept as itself; everything else is an operator.
  if (!PLACEHOLDER_SYMBOLS.has(symbol) && /^[A-Za-z_]\w*$/.test(symbol)) return RAW_KIND_STYLES.KEYWORD
  return RAW_KIND_STYLES.OP
}

/** What a raw token chip shows: layout tokens have no visible text, long comments are shortened. */
function tokenText(token) {
  if (token.kind === 'INDENT' || token.kind === 'DEDENT') return token.kind
  const text = String(token.value ?? '').replace(/\r?\n/g, '\\n')
  return text.length > 28 ? `${text.slice(0, 27)}…` : text
}

const CHIP = 'inline-flex max-w-full items-center rounded-md px-1.5 py-0.5 font-mono text-xs leading-5'

function TokensPanel({ data }) {
  const [view, setView] = useState('raw')
  const options = [
    { id: 'raw', label: 'Raw tokens' },
    { id: 'normalized', label: 'Normalised symbols' },
  ]

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
        <p className="max-w-2xl text-sm leading-6 text-slate-600">
          {view === 'raw'
            ? 'Every token the lexer found, coloured by kind. Names and comments still differ between the two snippets.'
            : 'After normalisation every name becomes ID and every literal NUM, STR or CHR, and comments are gone. The two streams now look almost the same.'}
        </p>
        <div role="group" aria-label="Token view" className="inline-flex rounded-lg border border-slate-300 bg-slate-50 p-0.5">
          {options.map((option) => (
            <button
              key={option.id}
              type="button"
              aria-pressed={view === option.id}
              onClick={() => setView(option.id)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                view === option.id ? 'bg-white text-indigo-700 shadow-sm ring-1 ring-slate-200' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {SIDES.map((side) => {
          const snippet = data[side.key] ?? {}
          const counts = snippet.counts ?? {}
          const raw = snippet.raw_tokens ?? []
          const normalized = snippet.normalized ?? []
          return (
            <div key={side.key} className="min-w-0 rounded-lg border border-slate-200 p-4">
              <SideHeading side={side} meta={`${plural(counts.raw_tokens ?? raw.length, 'raw token')} → ${plural(counts.normalized ?? normalized.length, 'symbol')}`} />
              {view === 'raw' ? (
                <>
                  <ul className="flex flex-wrap gap-1.5" aria-label={`${side.title} raw tokens`}>
                    {raw.map((token, i) => (
                      <li key={i} className={`${CHIP} ${RAW_KIND_STYLES[token.kind] ?? RAW_KIND_STYLES.OP}`} title={`${token.kind} · line ${token.line}`}>
                        <span className="truncate whitespace-pre">{tokenText(token)}</span>
                      </li>
                    ))}
                  </ul>
                  <TruncationNote shown={raw.length} total={counts.raw_tokens} noun="raw token" />
                </>
              ) : (
                <>
                  <ul className="flex flex-wrap gap-1.5" aria-label={`${side.title} normalised symbols`}>
                    {normalized.map((symbol, i) => (
                      <li key={i} className={`${CHIP} ${symbolStyle(symbol)}`}>
                        {symbol}
                      </li>
                    ))}
                  </ul>
                  <TruncationNote shown={normalized.length} total={counts.normalized} noun="symbol" />
                </>
              )}
            </div>
          )
        })}
      </div>

      {view === 'raw' && (
        <ul className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-600" aria-label="Token kind colours">
          {KIND_LEGEND.map((item) => (
            <li key={item.label} className="flex items-center gap-1.5">
              <span className={`inline-block h-3.5 w-5 rounded ${item.className}`} aria-hidden="true" />
              {item.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------------------------
// Step 2: k-grams
// ---------------------------------------------------------------------------------------------

function KgramsPanel({ data, result }) {
  const k = result?.stats?.k_effective
  const hashSets = {
    a: new Set((data.a?.kgrams ?? []).map((g) => g.hash)),
    b: new Set((data.b?.kgrams ?? []).map((g) => g.hash)),
  }

  return (
    <div>
      <Intro>
        A k-gram is a window of {isNumber(k) ? <strong className="font-semibold text-slate-800">k = {k}</strong> : 'k'} consecutive symbols,
        moved forward one symbol at a time. Each k-gram is hashed with BLAKE2b into a 64-bit number, shown here in hexadecimal. Equal
        pieces of code always give equal hashes, so numbers can be compared instead of text. Highlighted rows have a hash that also
        appears among the other snippet&rsquo;s k-grams listed here.
      </Intro>
      <div className="grid gap-6 lg:grid-cols-2">
        {SIDES.map((side) => {
          const snippet = data[side.key] ?? {}
          const kgrams = snippet.kgrams ?? []
          const other = hashSets[side.key === 'a' ? 'b' : 'a']
          return (
            <div key={side.key} className="min-w-0">
              <SideHeading side={side} meta={plural(snippet.counts?.kgrams ?? kgrams.length, 'k-gram')} />
              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="min-w-full text-sm">
                  <caption className="sr-only">{side.title} k-grams and their hashes</caption>
                  <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th scope="col" className="px-3 py-2 text-right">
                        #
                      </th>
                      <th scope="col" className="px-3 py-2 text-left">
                        k-gram
                      </th>
                      <th scope="col" className="px-3 py-2 text-left">
                        Hash
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono text-xs">
                    {kgrams.map((gram) => {
                      const shared = other.has(gram.hash)
                      return (
                        <tr key={gram.index} className={shared ? 'bg-indigo-50' : undefined}>
                          <td className="px-3 py-2 text-right text-slate-400 tabular-nums">{gram.index}</td>
                          <td className="whitespace-nowrap px-3 py-2 text-slate-800">{gram.text}</td>
                          <td className={`whitespace-nowrap px-3 py-2 ${shared ? 'font-semibold text-indigo-700' : 'text-slate-600'}`}>
                            {gram.hash}
                            {shared && <span className="sr-only"> (also in the other snippet)</span>}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              <TruncationNote shown={kgrams.length} total={snippet.counts?.kgrams} noun="k-gram" />
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------------------------
// Step 3: fingerprints
// ---------------------------------------------------------------------------------------------

function FingerprintsPanel({ data, result }) {
  const lists = { a: data.a?.fingerprints ?? [], b: data.b?.fingerprints ?? [] }
  const sets = { a: new Set(lists.a.map((f) => f.hash)), b: new Set(lists.b.map((f) => f.hash)) }
  const shared = new Set([...sets.a].filter((hash) => sets.b.has(hash)))
  const union = new Set([...sets.a, ...sets.b])
  // The API caps each list; the fraction can only be recomputed here when nothing was cut off.
  const complete =
    lists.a.length >= (data.a?.counts?.fingerprints ?? 0) && lists.b.length >= (data.b?.counts?.fingerprints ?? 0)
  const scores = result?.scores ?? {}

  return (
    <div>
      <Intro>
        Winnowing slides a window over consecutive k-gram hashes and keeps the smallest hash in each window (the rightmost one on a
        tie). The kept hashes are the snippet&rsquo;s fingerprints. Any matching run long enough to fill a window is guaranteed to
        leave a shared fingerprint, which is what makes copied blocks impossible to miss. Shared fingerprints are highlighted in both
        columns.
      </Intro>

      <div className="mb-6 flex flex-wrap items-center gap-x-8 gap-y-3 rounded-lg border border-indigo-100 bg-indigo-50/60 px-4 py-3 text-sm">
        {complete && union.size > 0 ? (
          <p className="text-slate-700">
            Token score (Jaccard) = shared ÷ all distinct ={' '}
            <span className="font-mono text-slate-900">
              {shared.size} ÷ {union.size}
            </span>{' '}
            = <span className="font-semibold text-indigo-700">{pct(shared.size / union.size)}</span>
          </p>
        ) : (
          <p className="text-slate-700">
            Token score (Jaccard): <span className="font-semibold text-indigo-700">{pct(scores.token)}</span>
            {isNumber(result?.stats?.shared_fingerprints) && ` · ${plural(result.stats.shared_fingerprints, 'shared fingerprint')} in total`}
          </p>
        )}
        <p className="text-slate-700">
          Containment (shared ÷ smaller set): <span className="font-semibold text-slate-900">{pct(scores.containment)}</span>
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {SIDES.map((side) => {
          const snippet = data[side.key] ?? {}
          const fingerprints = lists[side.key]
          return (
            <div key={side.key} className="min-w-0">
              <SideHeading side={side} meta={plural(snippet.counts?.fingerprints ?? fingerprints.length, 'fingerprint')} />
              {fingerprints.length === 0 ? (
                <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
                  This snippet is too short to produce fingerprints.
                </p>
              ) : (
                <div className="overflow-x-auto rounded-lg border border-slate-200">
                  <table className="min-w-full text-sm">
                    <caption className="sr-only">{side.title} fingerprints</caption>
                    <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <tr>
                        <th scope="col" className="px-3 py-2 text-left">
                          Hash
                        </th>
                        <th scope="col" className="px-3 py-2 text-right">
                          Position
                        </th>
                        <th scope="col" className="px-3 py-2 text-right">
                          Lines
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-xs">
                      {fingerprints.map((fp, i) => {
                        const isShared = shared.has(fp.hash)
                        const lines = fp.line_start === fp.line_end ? `${fp.line_start}` : `${fp.line_start}–${fp.line_end}`
                        return (
                          <tr key={`${fp.hash}-${fp.position}-${i}`} className={isShared ? 'bg-indigo-50' : undefined}>
                            <td className="whitespace-nowrap px-3 py-2 font-mono">
                              <span className={isShared ? 'font-semibold text-indigo-700' : 'text-slate-600'}>{fp.hash}</span>
                              {isShared && (
                                <Badge tone="indigo" className="ml-2 font-sans">
                                  shared
                                </Badge>
                              )}
                            </td>
                            <td className="px-3 py-2 text-right text-slate-600 tabular-nums">{fp.position}</td>
                            <td className="whitespace-nowrap px-3 py-2 text-right text-slate-600 tabular-nums">{lines}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
              <TruncationNote shown={fingerprints.length} total={snippet.counts?.fingerprints} noun="fingerprint" />
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------------------------
// Step 4: skeleton trees
// ---------------------------------------------------------------------------------------------

/** Paths ("0", "0.1", "0.1.2") of every node that has children, i.e. every node that can collapse. */
function branchPaths(root) {
  const paths = []
  const stack = [[root, '0']]
  while (stack.length) {
    const [node, path] = stack.pop()
    const children = node.children ?? []
    if (children.length) paths.push(path)
    children.forEach((child, i) => stack.push([child, `${path}.${i}`]))
  }
  return paths
}

function countNodes(root, predicate = () => true) {
  let count = 0
  const stack = [root]
  while (stack.length) {
    const node = stack.pop()
    if (predicate(node)) count += 1
    stack.push(...(node.children ?? []))
  }
  return count
}

function TreeItem({ node, path, collapsed, onToggle }) {
  const children = node.children ?? []
  const hasChildren = children.length > 0
  const open = !collapsed.has(path)
  const isLoop = node.label === 'Loop'

  return (
    <li>
      <div className="flex items-center gap-1 py-0.5">
        {hasChildren ? (
          <button
            type="button"
            onClick={() => onToggle(path)}
            aria-expanded={open}
            aria-label={`${open ? 'Collapse' : 'Expand'} ${node.label}`}
            className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-slate-400 hover:bg-slate-200 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className={`h-3.5 w-3.5 transition-transform ${open ? 'rotate-90' : ''}`} aria-hidden="true">
              <path d="m9 6 6 6-6 6" />
            </svg>
          </button>
        ) : (
          <span className="w-5 shrink-0" aria-hidden="true" />
        )}
        <span
          className={`rounded px-1.5 py-0.5 ${
            isLoop ? 'bg-indigo-600 font-semibold text-white' : 'bg-white text-slate-700 ring-1 ring-inset ring-slate-200'
          }`}
        >
          {node.label}
        </span>
        {hasChildren && !open && <span className="ml-1 font-sans text-[11px] text-slate-400">{plural(countNodes(node) - 1, 'node')} hidden</span>}
        {node.truncated && <span className="ml-1 font-sans text-[11px] text-slate-400">deeper levels not shown</span>}
      </div>
      {hasChildren && open && (
        <ul className="ml-2.5 border-l border-slate-200 pl-3">
          {children.map((child, i) => (
            <TreeItem key={i} node={child} path={`${path}.${i}`} collapsed={collapsed} onToggle={onToggle} />
          ))}
        </ul>
      )}
    </li>
  )
}

function SkeletonTree({ root, side, nodes }) {
  const [collapsed, setCollapsed] = useState(() => new Set())
  const paths = useMemo(() => branchPaths(root), [root])
  const loops = useMemo(() => countNodes(root, (node) => node.label === 'Loop'), [root])

  const toggle = (path) =>
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })

  return (
    <div className="min-w-0">
      <SideHeading side={side} meta={`${plural(nodes ?? countNodes(root), 'node')} · ${plural(loops, 'Loop node')}`} />
      <div className="mb-2 flex gap-2">
        <Button variant="ghost" size="sm" onClick={() => setCollapsed(new Set())}>
          Expand all
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setCollapsed(new Set(paths.filter((p) => p !== '0')))}>
          Collapse all
        </Button>
      </div>
      <div className="max-h-[28rem] overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-3 font-mono text-xs">
        <ul aria-label={`${side.title} syntax skeleton`}>
          <TreeItem node={root} path="0" collapsed={collapsed} onToggle={toggle} />
        </ul>
      </div>
    </div>
  )
}

function TreesPanel({ data, result }) {
  const scores = result?.scores ?? {}
  const stats = result?.stats ?? {}

  return (
    <div>
      <Intro>
        Each snippet is parsed into a syntax tree and reduced to a skeleton that keeps only the kind of each node, never names or
        values. Every loop form (for, while, do-while) becomes the same{' '}
        <span className="rounded bg-indigo-600 px-1.5 py-0.5 font-mono text-xs font-semibold text-white">Loop</span> node, so a for loop
        rewritten as a while loop leaves the skeleton unchanged. Use the arrows to fold branches.
      </Intro>

      <div className="mb-6 grid gap-4 rounded-lg border border-indigo-100 bg-indigo-50/60 px-4 py-3 text-sm sm:grid-cols-3">
        <p className="text-slate-700">
          Tree edit similarity: <span className="font-semibold text-slate-900">{pct(scores.ted)}</span>
        </p>
        <p className="text-slate-700">
          Shared subtrees: <span className="font-semibold text-slate-900">{pct(scores.subtree)}</span>
        </p>
        <p className="text-slate-700">
          Structure = ½ × both: <span className="font-semibold text-indigo-700">{pct(scores.structure)}</span>
        </p>
        {stats.structure_method && (
          <p className="text-xs text-slate-500 sm:col-span-3">
            Method: <Mono>{stats.structure_method}</Mono>
          </p>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {SIDES.map((side) => {
          const snippet = data[side.key] ?? {}
          return snippet.skeleton ? (
            <SkeletonTree key={side.key} root={snippet.skeleton} side={side} nodes={snippet.counts?.nodes} />
          ) : (
            <div key={side.key} className="min-w-0">
              <SideHeading side={side} />
              <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
                No syntax tree could be built for this snippet, so the final score relies on tokens alone.
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------------------------
// Step 5: final score
// ---------------------------------------------------------------------------------------------

function ScorePanel({ result, defaults }) {
  const scores = result?.scores ?? {}
  const stats = result?.stats ?? {}
  const matches = result?.matches ?? []
  const warnings = result?.warnings ?? []
  const hasStructure = isNumber(scores.structure)

  // fuse() normalises the two weights to sum to 1, so the arithmetic below does the same.
  const wt = defaults?.w_token
  const ws = defaults?.w_structure
  const weightsKnown = isNumber(wt) && isNumber(ws) && wt + ws > 0
  const nt = weightsKnown ? wt / (wt + ws) : null
  const ns = weightsKnown ? ws / (wt + ws) : null

  const statItems = [
    ['Symbols (A / B)', `${stats.a_tokens ?? '—'} / ${stats.b_tokens ?? '—'}`],
    ['Fingerprints (A / B)', `${stats.a_fingerprints ?? '—'} / ${stats.b_fingerprints ?? '—'}`],
    ['Shared fingerprints', stats.shared_fingerprints ?? '—'],
    ['Tree nodes (A / B)', `${stats.a_nodes ?? '—'} / ${stats.b_nodes ?? '—'}`],
    ['Effective k', stats.k_effective ?? '—'],
  ]

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      <div className="space-y-6 lg:col-span-3">
        <div className="flex flex-wrap items-center gap-4 rounded-lg border border-slate-200 p-5">
          <div>
            <p className="text-sm font-medium text-slate-500">Fused similarity</p>
            <p className="mt-1 text-4xl font-semibold tracking-tight text-slate-900">{pct(scores.fused)}</p>
          </div>
          {result?.verdict && (
            <Badge tone={result.verdict} dot className="text-sm">
              {result.verdict} similarity
            </Badge>
          )}
          <div className="w-full">
            <ScoreBar
              value={scores.fused}
              inline
              showValue={false}
              label="Fused similarity"
              high={defaults?.high_threshold ?? 0.75}
              moderate={defaults?.moderate_threshold ?? 0.5}
            />
          </div>
        </div>

        <div className="space-y-4">
          <ScoreBar value={scores.token} label="Token score (winnowing Jaccard)" color={palette.indigo} />
          <ScoreBar value={scores.structure} label="Structure score (AST skeleton)" color={palette.indigo} />
        </div>

        <div className="rounded-lg border border-indigo-100 bg-indigo-50/60 px-4 py-3 text-sm text-slate-700">
          <p className="font-medium text-slate-900">How the fused score is computed</p>
          {!hasStructure ? (
            <p className="mt-1">No structure score is available, so the fused score equals the token score.</p>
          ) : weightsKnown ? (
            <p className="mt-1 font-mono text-[13px]">
              {score(nt)} × {score(scores.token, 3)} + {score(ns)} × {score(scores.structure, 3)} ={' '}
              <span className="font-semibold text-indigo-700">{score(nt * scores.token + ns * scores.structure, 3)}</span>
            </p>
          ) : (
            <p className="mt-1">A weighted average of the token score and the structure score.</p>
          )}
          {isNumber(defaults?.high_threshold) && isNumber(defaults?.moderate_threshold) && (
            <p className="mt-2 text-xs text-slate-600">
              Verdict: High at {pct(defaults.high_threshold, 0)} or more, Moderate from {pct(defaults.moderate_threshold, 0)}, otherwise
              Low.
            </p>
          )}
        </div>

        <div>
          <h4 className="text-sm font-semibold text-slate-900">Baselines for comparison</h4>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            Methods that look at the text as written. They drop sharply when names, comments and loops change, which is why CodeSentry
            normalises tokens and compares structure instead.
          </p>
          <div className="mt-3 space-y-4">
            <ScoreBar value={scores.text_baseline} label="Plain text matching" color={palette.slate} />
            <ScoreBar value={scores.tfidf_baseline} label="TF-IDF cosine" color={palette.slate} />
          </div>
        </div>
      </div>

      <div className="space-y-6 lg:col-span-2">
        <div className="rounded-lg border border-slate-200 p-4">
          <h4 className="text-sm font-semibold text-slate-900">Details</h4>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Tree edit similarity</dt>
              <dd className="font-medium text-slate-900 tabular-nums">{pct(scores.ted)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Shared subtrees</dt>
              <dd className="font-medium text-slate-900 tabular-nums">{pct(scores.subtree)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Containment</dt>
              <dd className="font-medium text-slate-900 tabular-nums">{pct(scores.containment)}</dd>
            </div>
            {statItems.map(([label, value]) => (
              <div key={label} className="flex justify-between gap-3">
                <dt className="text-slate-500">{label}</dt>
                <dd className="font-medium text-slate-900 tabular-nums">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="rounded-lg border border-slate-200 p-4">
          <h4 className="text-sm font-semibold text-slate-900">Matched regions</h4>
          {matches.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">No shared fingerprints, so no matching lines were found.</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {matches.map((m, i) => (
                <li key={i} className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-slate-50 px-3 py-2">
                  <span className="text-slate-700">
                    A lines {m.a_start}–{m.a_end} <span aria-hidden="true">↔</span>
                    <span className="sr-only">match</span> B lines {m.b_start}–{m.b_end}
                  </span>
                  <span className="text-xs text-slate-500">{plural(m.tokens, 'token')}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {warnings.length > 0 && (
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h4 className="text-sm font-semibold text-slate-900">Warnings</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
              {warnings.map((warning, i) => (
                <li key={i}>{warning}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------------------------
// Results: accessible tabs
// ---------------------------------------------------------------------------------------------

function ResultTabs({ data, defaults, tab, onTabChange }) {
  const tabRefs = useRef([])
  const index = Math.max(0, TABS.findIndex((t) => t.id === tab))
  const result = data.result

  // Arrow keys, Home and End move between tabs (WAI-ARIA tabs pattern); only the selected tab is
  // in the Tab order, so a keyboard user reaches the panel content with a single Tab press.
  function handleKeyDown(event) {
    let next = null
    if (event.key === 'ArrowRight') next = (index + 1) % TABS.length
    else if (event.key === 'ArrowLeft') next = (index - 1 + TABS.length) % TABS.length
    else if (event.key === 'Home') next = 0
    else if (event.key === 'End') next = TABS.length - 1
    if (next === null) return
    event.preventDefault()
    onTabChange(TABS[next].id)
    tabRefs.current[next]?.focus()
  }

  let panel
  if (tab === 'kgrams') panel = <KgramsPanel data={data} result={result} />
  else if (tab === 'fingerprints') panel = <FingerprintsPanel data={data} result={result} />
  else if (tab === 'trees') panel = <TreesPanel data={data} result={result} />
  else if (tab === 'score') panel = <ScorePanel result={result} defaults={defaults} />
  else panel = <TokensPanel data={data} />

  return (
    <div>
      <div role="tablist" aria-label="Pipeline steps" className="-mx-1 flex gap-1 overflow-x-auto border-b border-slate-200 px-1" onKeyDown={handleKeyDown}>
        {TABS.map((t, i) => {
          const selected = t.id === tab
          return (
            <button
              key={t.id}
              ref={(el) => {
                tabRefs.current[i] = el
              }}
              id={`explain-tab-${t.id}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`explain-panel-${t.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => onTabChange(t.id)}
              className={`-mb-px flex shrink-0 items-center gap-2 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500 ${
                selected ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-800'
              }`}
            >
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-semibold ${
                  selected ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'
                }`}
                aria-hidden="true"
              >
                {i + 1}
              </span>
              {t.label}
            </button>
          )
        })}
      </div>

      <div id={`explain-panel-${TABS[index].id}`} role="tabpanel" aria-labelledby={`explain-tab-${TABS[index].id}`} className="pt-6">
        {panel}
      </div>

      <div className="mt-8 flex items-center justify-between gap-3 border-t border-slate-200 pt-4">
        {index > 0 ? (
          <Button variant="secondary" size="sm" onClick={() => onTabChange(TABS[index - 1].id)}>
            Back: {TABS[index - 1].label}
          </Button>
        ) : (
          <span />
        )}
        {index < TABS.length - 1 && (
          <Button size="sm" onClick={() => onTabChange(TABS[index + 1].id)}>
            Next: {TABS[index + 1].label}
          </Button>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------------------------
// The explainer
// ---------------------------------------------------------------------------------------------

export default function PipelineExplainer() {
  const [language, setLanguage] = useState('python')
  // Drafts are kept per language, so switching to C and back does not lose edits to the Python code.
  const [drafts, setDrafts] = useState(() => ({ python: { ...SAMPLES.python }, c: { ...SAMPLES.c } }))
  const [run, setRun] = useState(null) // { data, input } of the last successful explain() call
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null) // { title, message }
  const [tab, setTab] = useState('tokens')
  const [defaults, setDefaults] = useState(null)

  const requestId = useRef(0)
  const resultsRef = useRef(null)
  const focusResults = useRef(false)

  // The engine defaults supply the fusion weights and verdict thresholds shown in the last step.
  // If they cannot be loaded, that step still shows every score and simply omits the arithmetic.
  useEffect(() => {
    let active = true
    getDefaults()
      .then((config) => active && setDefaults(config))
      .catch(() => active && setDefaults(null))
    return () => {
      active = false
    }
  }, [])

  // A response that arrives after the component unmounts must not update state.
  useEffect(
    () => () => {
      requestId.current += 1
    },
    [],
  )

  // After a new run, bring the results into view and move keyboard focus to them.
  useEffect(() => {
    if (!run || !focusResults.current || !resultsRef.current) return
    focusResults.current = false
    resultsRef.current.focus({ preventScroll: true })
    resultsRef.current.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' })
  }, [run])

  const draft = drafts[language]
  const setDraft = (side, value) => setDrafts((prev) => ({ ...prev, [language]: { ...prev[language], [side]: value } }))
  const isSample = draft.a === SAMPLES[language].a && draft.b === SAMPLES[language].b
  const stale =
    run !== null && (run.input.language !== language || run.input.code_a !== draft.a || run.input.code_b !== draft.b)

  async function handleRun() {
    const input = { language, code_a: draft.a, code_b: draft.b }
    if (!input.code_a.trim() || !input.code_b.trim()) {
      setError({ title: 'Nothing to compare', message: 'Both snippets need some code before the pipeline can run.' })
      return
    }

    // Only the most recent request may update the page, even if an older one answers later.
    requestId.current += 1
    const id = requestId.current
    setLoading(true)
    setError(null)
    try {
      const data = await explain(input)
      if (id !== requestId.current) return
      focusResults.current = true
      setRun({ data, input })
      setTab('tokens')
    } catch (err) {
      if (id !== requestId.current) return
      const invalidCode = err?.response?.status === 400
      setError({
        title: invalidCode ? 'The snippets could not be analysed' : 'The pipeline could not run',
        message: errorMessage(err),
      })
    } finally {
      if (id === requestId.current) setLoading(false)
    }
  }

  const languageLabel = LANGUAGES.find((l) => l.value === language)?.label ?? language

  return (
    <div className="space-y-8">
      <div className="space-y-5">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <label htmlFor="explain-language" className="block text-sm font-medium text-slate-800">
              Language
            </label>
            <select
              id="explain-language"
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              className="mt-1.5 h-10 w-40 rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 shadow-sm focus-visible:border-indigo-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40"
            >
              {LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="ghost"
              disabled={isSample || loading}
              onClick={() => setDrafts((prev) => ({ ...prev, [language]: { ...SAMPLES[language] } }))}
            >
              Restore {languageLabel} samples
            </Button>
            <Button onClick={handleRun} loading={loading}>
              {loading ? 'Running…' : 'Run step by step'}
            </Button>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <CodeEditor
            id="explain-code-a"
            label="Snippet A (original)"
            hint="Tab inserts spaces · press Esc, then Tab, to move on"
            value={draft.a}
            onChange={(value) => setDraft('a', value)}
          />
          <CodeEditor
            id="explain-code-b"
            label="Snippet B (suspected copy)"
            hint={isSample ? 'Renamed variables, for loop rewritten as while, comment added' : 'Tab inserts spaces · press Esc, then Tab, to move on'}
            value={draft.b}
            onChange={(value) => setDraft('b', value)}
          />
        </div>

        {error && <ErrorBanner title={error.title} message={error.message} onDismiss={() => setError(null)} />}
      </div>

      {run && (
        <section
          ref={resultsRef}
          tabIndex={-1}
          aria-labelledby="explain-results-title"
          className="scroll-mt-20 rounded-xl border border-slate-200 bg-white p-4 shadow-sm focus-visible:outline-none sm:p-6"
        >
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 id="explain-results-title" className="text-base font-semibold text-slate-900">
                What each step produced
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                {LANGUAGES.find((l) => l.value === run.input.language)?.label ?? run.input.language} snippets · work through the
                steps in order
              </p>
            </div>
            {stale && (
              <p className="rounded-md bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600" role="status">
                The code has changed since this run. Run again to refresh.
              </p>
            )}
          </div>
          <ResultTabs data={run.data} defaults={defaults} tab={tab} onTabChange={setTab} />
        </section>
      )}
    </div>
  )
}
