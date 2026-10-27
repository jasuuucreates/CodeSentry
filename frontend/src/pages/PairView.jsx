// Pair Comparison page (route "/runs/:runId/pairs/:aId/:bId").
//
// The page a teacher opens after spotting a suspicious pair: the fused score and what it means, how
// it was built from each signal, and both source files side by side with every matched region
// highlighted in the same colour on both sides.
import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { errorMessage, getPair, getRun } from '../api/client.js'
import CodePane from '../components/CodePane.jsx'
import MatchList from '../components/MatchList.jsx'
import ScoreBreakdown from '../components/ScoreBreakdown.jsx'
import Badge from '../components/ui/Badge.jsx'
import Button from '../components/ui/Button.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Spinner from '../components/ui/Spinner.jsx'
import { verdictTone } from '../lib/colors.js'
import { pct } from '../lib/format.js'

/**
 * Colours for matched regions; match i uses MATCH_PALETTE[i % length] in both code panes and in the
 * match list. Red, amber and green are left out on purpose: in CodeSentry those colours always mean a
 * verdict, and a highlighted region is evidence, not a verdict. Neighbouring entries differ in hue so
 * adjacent regions stay distinguishable.
 */
const MATCH_PALETTE = ['#6366f1', '#0d9488', '#c026d3', '#0284c7', '#7c3aed', '#db2777', '#0891b2', '#2563eb']

// Engine defaults (engine/models.py). The upload form cannot change the thresholds, so these are what
// every run uses; the run's own config replaces them as soon as it has loaded.
const DEFAULT_THRESHOLDS = { high: 0.75, moderate: 0.5 }

const VERDICT_TEXT = {
  red: 'text-red-600',
  amber: 'text-amber-600',
  green: 'text-green-600',
  neutral: 'text-slate-900',
}

const LANGUAGE_LABELS = { python: 'Python', c: 'C' }

// A gap of 0.2 between the token and structure scores is large enough to say which signal drives the
// result; smaller gaps are treated as the two signals agreeing.
const SIGNAL_GAP = 0.2

/**
 * One sentence telling a non-specialist what the verdict means for this pair. It names the threshold
 * that was crossed and, for suspicious pairs, which kind of evidence is behind the score.
 */
function verdictSentence(pair, thresholds) {
  const { token, structure } = pair.scores ?? {}
  const high = pct(thresholds.high, 0)
  const moderate = pct(thresholds.moderate, 0)

  let evidence = 'the shared code sequences and the program structure point the same way'
  if (typeof structure !== 'number') {
    evidence = 'the evidence comes from shared code sequences only, because the structure could not be compared'
  } else if (structure - token >= SIGNAL_GAP) {
    evidence = 'the program skeletons agree far more than the literal code, the typical sign of a copy that was renamed or restructured'
  } else if (token - structure >= SIGNAL_GAP) {
    evidence = 'long identical code sequences are shared even though the overall structure differs'
  }

  switch (pair.verdict) {
    case 'High':
      return `The fused score reaches the ${high} high-similarity threshold and ${evidence}, so this pair should be reviewed by hand.`
    case 'Moderate':
      return `The fused score falls between the ${moderate} and ${high} thresholds and ${evidence}, so check the matched regions before drawing a conclusion.`
    case 'Low':
      return `The fused score is below the ${moderate} threshold: the files share little code or structure, which is typical of independently written solutions.`
    default:
      return 'The engine did not return a verdict for this pair.'
  }
}

function SwapIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
      <path d="M7 4 3 8l4 4M3 8h14M17 20l4-4-4-4M21 16H7" />
    </svg>
  )
}

export default function PairView() {
  const { runId, aId, bId } = useParams()
  const [reloadKey, setReloadKey] = useState(0)
  const [syncScroll, setSyncScroll] = useState(false)

  // Every piece of per-pair state remembers which request it belongs to. When the URL changes (or
  // "Try again" is pressed) the key changes, so stale data is simply ignored during rendering instead
  // of being cleared with an extra state update.
  const requestKey = `${runId}/${aId}/${bId}#${reloadKey}`
  const [response, setResponse] = useState({ key: null, pair: null, error: null, notFound: false })
  const [selection, setSelection] = useState({ key: null, index: -1 })
  const [runInfo, setRunInfo] = useState({ id: null, run: null })

  const paneA = useRef(null)
  const paneB = useRef(null)
  const codeArea = useRef(null)

  useEffect(() => {
    // `active` discards a response that arrives after the reader has already moved to another pair.
    let active = true
    getPair(runId, aId, bId)
      .then((pair) => {
        if (active) setResponse({ key: requestKey, pair, error: null, notFound: false })
      })
      .catch((err) => {
        if (active) {
          setResponse({ key: requestKey, pair: null, error: errorMessage(err), notFound: err?.response?.status === 404 })
        }
      })
    return () => {
      active = false
    }
  }, [runId, aId, bId, requestKey])

  // The run supplies its name and engine settings (fusion weights, k). They only enrich the page, so
  // the pair is shown without waiting for them, and a failure here deliberately shows no error.
  useEffect(() => {
    let active = true
    getRun(runId)
      .then((run) => {
        if (active) setRunInfo({ id: runId, run })
      })
      .catch(() => {
        if (active) setRunInfo({ id: runId, run: null })
      })
    return () => {
      active = false
    }
  }, [runId])

  let status = 'ready'
  if (response.key !== requestKey) status = 'loading'
  else if (response.error) status = 'error'

  const pair = status === 'ready' ? response.pair : null
  const run = runInfo.id === runId ? runInfo.run : null
  const activeIndex = selection.key === requestKey ? selection.index : -1

  const matches = useMemo(() => pair?.matches ?? [], [pair])
  const rangesA = useMemo(() => matches.map((m) => ({ start: m.a_start, end: m.a_end })), [matches])
  const rangesB = useMemo(() => matches.map((m) => ({ start: m.b_start, end: m.b_end })), [matches])

  /**
   * Selects match `index`. From the list (no `origin`) both panes scroll to the start of the match.
   * From a click inside one pane, only the OTHER pane moves, and it places its half of the match at
   * the same height as the clicked half, so the two blocks end up level without the text under the
   * reader's cursor jumping away.
   */
  function selectMatch(index, origin) {
    const match = matches[index]
    if (!match) return
    setSelection({ key: requestKey, index })

    if (origin === 'a') {
      paneB.current?.scrollToLine(match.b_start, paneA.current?.lineOffset(match.a_start))
      return
    }
    if (origin === 'b') {
      paneA.current?.scrollToLine(match.a_start, paneB.current?.lineOffset(match.b_start))
      return
    }

    // On narrow screens the list sits above the code, so bring the panes into view first. The page
    // jump is instant: only the panes animate, which keeps the two scroll animations independent.
    const area = codeArea.current
    if (area) {
      const { top } = area.getBoundingClientRect()
      if (top < 0 || top > window.innerHeight * 0.6) area.scrollIntoView({ block: 'start' })
    }
    paneA.current?.scrollToLine(match.a_start)
    paneB.current?.scrollToLine(match.b_start)
  }

  const back = { to: `/runs/${runId}`, label: 'Back to run results' }
  const eyebrow = run?.name ?? `Run #${runId}`

  if (status === 'loading') {
    return (
      <>
        <PageHeader title="Pair comparison" eyebrow={eyebrow} back={back} />
        <Spinner center size="lg" label="Loading the pair comparison…" />
      </>
    )
  }

  if (status === 'error') {
    return (
      <>
        <PageHeader title="Pair comparison" eyebrow={eyebrow} back={back} />
        {response.notFound ? (
          <EmptyState
            title="Pair not found"
            description={`${response.error} The run may have been deleted, or these two files are not part of it.`}
            action={<Button to={`/runs/${runId}`}>Back to run results</Button>}
          />
        ) : (
          <ErrorBanner
            title="Could not load this pair"
            message={response.error}
            onRetry={() => setReloadKey((key) => key + 1)}
          />
        )}
      </>
    )
  }

  const scores = pair.scores ?? {}
  const stats = pair.stats ?? {}
  const config = run?.config
  const thresholds = {
    high: config?.high_threshold ?? DEFAULT_THRESHOLDS.high,
    moderate: config?.moderate_threshold ?? DEFAULT_THRESHOLDS.moderate,
  }

  // The largest region is the single strongest piece of copying evidence, so it is worth a headline.
  const largestRegion = matches.reduce((largest, m) => Math.max(largest, m.tokens ?? 0), 0)
  const facts = [
    { label: 'Language', value: LANGUAGE_LABELS[pair.language] ?? pair.language ?? '—' },
    { label: 'Matched regions', value: matches.length },
    { label: 'Largest region', value: matches.length ? `${largestRegion} tokens` : '—' },
  ]

  return (
    <>
      <PageHeader
        eyebrow={eyebrow}
        title={`${pair.a_name} vs ${pair.b_name}`}
        subtitle={
          matches.length
            ? 'Matched regions share a colour in both files. Select one in the list, or click a highlighted line, to line the two files up.'
            : 'The two files share no code sequences, so nothing is highlighted in the source below.'
        }
        back={back}
        actions={
          <>
            <Badge tone={pair.verdict} dot>
              {pair.verdict ? `${pair.verdict} similarity` : 'No verdict'}
            </Badge>
            <Button variant="secondary" size="sm" icon={<SwapIcon />} to={`/runs/${runId}/pairs/${bId}/${aId}`}>
              Swap sides
            </Button>
          </>
        }
      />

      <div className="grid gap-6 xl:grid-cols-3">
        {/* self-start: the card keeps its natural height instead of stretching beside the taller breakdown. */}
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm xl:self-start" aria-labelledby="fused-score-heading">
          <div className="flex flex-col gap-6 md:flex-row md:items-start xl:flex-col">
            <div className="shrink-0">
              <h2 id="fused-score-heading" className="text-sm font-medium text-slate-500">
                Fused similarity
              </h2>
              <p className={`mt-1 text-6xl font-semibold tracking-tight tabular-nums ${VERDICT_TEXT[verdictTone(pair.verdict)]}`}>
                {pct(scores.fused)}
              </p>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm leading-6 text-slate-700">{verdictSentence(pair, thresholds)}</p>
              <dl className="mt-5 grid grid-cols-3 gap-4 border-t border-slate-200 pt-4">
                {facts.map((fact) => (
                  <div key={fact.label} className="min-w-0">
                    <dt className="text-xs text-slate-500">{fact.label}</dt>
                    <dd className="mt-0.5 text-sm font-semibold text-slate-900 tabular-nums">{fact.value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        </section>

        <ScoreBreakdown
          className="xl:col-span-2"
          scores={scores}
          stats={stats}
          warnings={pair.warnings ?? []}
          config={config}
        />
      </div>

      <div className="mt-8 grid gap-6 2xl:grid-cols-[16rem_minmax(0,1fr)]">
        <MatchList
          className="2xl:sticky 2xl:top-6 2xl:self-start"
          matches={matches}
          palette={MATCH_PALETTE}
          activeIndex={activeIndex}
          onSelect={(index) => selectMatch(index)}
          syncScroll={syncScroll}
          onSyncScrollChange={setSyncScroll}
        />

        <div ref={codeArea} className="grid min-w-0 scroll-mt-20 gap-4 md:grid-cols-2">
          <CodePane
            ref={paneA}
            side="A"
            name={pair.a_name}
            language={pair.language}
            source={pair.a_source}
            ranges={rangesA}
            palette={MATCH_PALETTE}
            activeIndex={activeIndex}
            onSelectMatch={(index) => selectMatch(index, 'a')}
            onUserScroll={(dy, dx) => syncScroll && paneB.current?.applyScrollDelta(dy, dx)}
          />
          <CodePane
            ref={paneB}
            side="B"
            name={pair.b_name}
            language={pair.language}
            source={pair.b_source}
            ranges={rangesB}
            palette={MATCH_PALETTE}
            activeIndex={activeIndex}
            onSelectMatch={(index) => selectMatch(index, 'b')}
            onUserScroll={(dy, dx) => syncScroll && paneA.current?.applyScrollDelta(dy, dx)}
          />
        </div>
      </div>
    </>
  )
}
