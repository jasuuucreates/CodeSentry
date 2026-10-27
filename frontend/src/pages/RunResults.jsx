// Run Results page (route "/runs/:runId").
//
// Loads one stored analysis run with getRun(runId) and presents it from overview to detail:
// headline numbers -> heat map of every file against every other -> ranked list of pairs -> the
// distribution of scores. Each pair links on to the side-by-side comparison page.
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { errorMessage, getRun } from '../api/client.js'
import Heatmap from '../components/Heatmap.jsx'
import PairsTable from '../components/PairsTable.jsx'
import ScoreHistogram from '../components/ScoreHistogram.jsx'
import SummaryCards from '../components/SummaryCards.jsx'
import Button from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Spinner from '../components/ui/Spinner.jsx'
import { dateTime } from '../lib/format.js'

function HeaderActions() {
  return (
    <>
      <Button to="/" variant="secondary">
        Dashboard
      </Button>
      <Button
        to="/new"
        icon={
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="h-4 w-4" aria-hidden="true">
            <path d="M12 5v14M5 12h14" />
          </svg>
        }
      >
        New analysis
      </Button>
    </>
  )
}

/** Short guide shown above the heat map, so the grid can be read without prior explanation. */
function HowToRead() {
  return (
    <aside className="mb-6 flex gap-3 rounded-lg border border-indigo-100 bg-indigo-50/60 px-4 py-3 text-sm leading-6 text-slate-700">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600" aria-hidden="true">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 11v5.5M12 7.5h.01" />
      </svg>
      <p>
        <span className="font-semibold text-slate-900">How to read this: </span>
        each cell is the fused similarity between the file in its row and the file in its column. Pale green means
        little in common, red means nearly the same program. The grid is mirrored across the dark diagonal (a file
        against itself), so every pair appears twice. Hatched cells were not compared because the files are in
        different languages. Click a coloured cell, or move to it with the arrow keys and press Enter, to open the
        side-by-side comparison.
      </p>
    </aside>
  )
}

/** Lists files the engine had trouble with, because their pairs may be missing or less reliable. */
function FileWarnings({ files }) {
  return (
    <details className="group rounded-xl border border-slate-200 bg-white px-5 py-3 shadow-sm">
      <summary className="flex cursor-pointer list-none items-center gap-3 rounded text-sm font-medium text-slate-700 [&::-webkit-details-marker]:hidden">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0 text-slate-500" aria-hidden="true">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7.5v5.5M12 16.5h.01" />
        </svg>
        <span className="flex-1">
          {files.length} {files.length === 1 ? 'file' : 'files'} reported warnings during analysis
        </span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4 text-slate-400 transition-transform group-open:rotate-180" aria-hidden="true">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </summary>
      <ul className="mt-3 space-y-2 border-t border-slate-100 pt-3 text-sm">
        {files.map((file) => (
          <li key={file.id}>
            <span className="font-mono text-[13px] font-medium text-slate-900">{file.name}</span>
            <ul className="mt-0.5 list-disc pl-5 text-slate-600">
              {file.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </details>
  )
}

export default function RunResults() {
  const { runId } = useParams()
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState(null)

  // Each response is tagged with the request it answers. While the tag does not match the current
  // run id and attempt, the page is loading — so opening another run never flashes stale data, and a
  // late response for a run the user already left is simply ignored.
  const requestKey = `${runId}#${attempt}`

  useEffect(() => {
    let active = true
    getRun(runId)
      .then((run) => {
        if (active) setResult({ key: requestKey, run })
      })
      .catch((err) => {
        if (!active) return
        if (err?.response?.status === 404) setResult({ key: requestKey, notFound: true })
        else setResult({ key: requestKey, error: errorMessage(err) })
      })
    return () => {
      active = false
    }
  }, [runId, requestKey])

  const current = result?.key === requestKey ? result : null

  if (!current) {
    return (
      <>
        <PageHeader title="Run results" subtitle="Fetching the similarity matrix and ranked pairs for this run." actions={<HeaderActions />} />
        <Spinner center size="lg" label="Loading analysis results…" />
      </>
    )
  }

  if (current.notFound) {
    return (
      <>
        <PageHeader title="Run not found" subtitle="There is no stored analysis run at this address." actions={<HeaderActions />} />
        <EmptyState
          title={`Analysis run #${runId} does not exist`}
          description="It may have been deleted, or the link may be mistyped. The dashboard lists every run that is still stored."
          action={<Button to="/">Go to Dashboard</Button>}
        />
      </>
    )
  }

  if (current.error) {
    return (
      <>
        <PageHeader title="Run results" actions={<HeaderActions />} />
        <ErrorBanner title="Could not load this analysis run" message={current.error} onRetry={() => setAttempt((n) => n + 1)} />
      </>
    )
  }

  const { run } = current
  const files = run.files ?? []
  const pairs = run.pairs ?? []
  const warningFiles = files.filter((file) => file.warnings?.length > 0)
  const fileCount = run.file_count ?? files.length

  return (
    <>
      <PageHeader
        eyebrow={`Run #${run.id}`}
        title={run.name || `Analysis run #${run.id}`}
        subtitle={`Analysed ${dateTime(run.created_at)} · ${fileCount} ${fileCount === 1 ? 'file' : 'files'} · ${run.pair_count ?? pairs.length} pairs compared`}
        actions={<HeaderActions />}
      />

      <div className="space-y-8">
        <SummaryCards run={run} />

        {warningFiles.length > 0 && <FileWarnings files={warningFiles} />}

        <Card title="Similarity heat map" subtitle={`Fused score of every file against every other file (${files.length} × ${files.length}).`}>
          <HowToRead />
          <Heatmap files={files} matrix={run.matrix ?? []} pairs={pairs} runId={run.id} config={run.config} />
        </Card>

        <Card
          title="Ranked pairs"
          subtitle="Most similar first. Filter by verdict, search by file name, sort any column, then open a pair to see the matching code."
          bodyClassName="p-0"
        >
          <PairsTable pairs={pairs} runId={run.id} config={run.config} />
        </Card>

        <Card title="Score distribution" subtitle="How the fused scores of all compared pairs are spread across the 0–100% range.">
          <ScoreHistogram pairs={pairs} config={run.config} />
        </Card>
      </div>
    </>
  )
}
