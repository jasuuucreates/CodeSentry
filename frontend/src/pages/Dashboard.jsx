// Dashboard page (route "/") — the landing page of CodeSentry.
//
// It introduces what the tool does, offers the two ways to start (the bundled demo class or a new
// upload) and lists the analysis runs already stored on the server. The list depends on the Flask
// backend, so the page first asks GET /api/health: if that fails, the server is not running and the
// page says how to start it rather than showing a confusing generic error.
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createDemoRun, deleteRun, errorMessage, getHealth, listRuns } from '../api/client.js'
import RunsTable from '../components/RunsTable.jsx'
import Button from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Spinner from '../components/ui/Spinner.jsx'

function Icon({ children, className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {children}
    </svg>
  )
}

const PLAY_ICON = (
  <Icon>
    <path d="M8 5.5v13l10.5-6.5z" />
  </Icon>
)

const UPLOAD_ICON = (
  <Icon>
    <path d="M12 15V4" />
    <path d="m7.5 8.5 4.5-4.5 4.5 4.5" />
    <path d="M4 14.5V18a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3.5" />
  </Icon>
)

const SERVER_ICON = (
  <Icon className="h-6 w-6">
    <rect x="3.5" y="4" width="17" height="6.5" rx="1.5" />
    <rect x="3.5" y="13.5" width="17" height="6.5" rx="1.5" />
    <path d="M7.5 7.25h.01M7.5 16.75h.01" />
  </Icon>
)

// The disguises listed in the hero are exactly the obfuscations the evaluation dataset applies
// (contract section 9), so the claim on the landing page is one the Evaluation page can back up.
const DISGUISES = [
  { title: 'Renamed variables and functions', detail: 'Every identifier becomes the same ID symbol.' },
  { title: 'Reformatting and rewritten comments', detail: 'Layout and comments never reach the fingerprints.' },
  { title: 'Reordered functions', detail: 'Top-level definitions are compared in a canonical order.' },
  { title: 'for loops rewritten as while loops', detail: 'Every loop form becomes the same Loop node.' },
  { title: 'Inserted dead code', detail: 'Unused lines dilute, but do not hide, the shared code.' },
]

const FEATURES = [
  {
    title: 'Token fingerprinting',
    reference: 'Winnowing (Schleimer, Wilkerson and Aiken, 2003)',
    description:
      'Source code is reduced to normalized tokens: every variable becomes ID and every number NUM. Overlapping k-grams are hashed and winnowed into fingerprints, so renaming and reformatting leave them unchanged.',
    icon: (
      <Icon className="h-6 w-6">
        <path d="M5 8.5a8 8 0 0 1 14 0" />
        <path d="M7.5 20a9.5 9.5 0 0 1-1.5-5.2 6 6 0 0 1 12 0c0 1.2-.2 2.4-.6 3.5" />
        <path d="M12 14.5c0 2.3-.6 4.3-1.8 6" />
        <path d="M9.2 11.3A3 3 0 0 1 15 12.8" />
      </Icon>
    ),
  },
  {
    title: 'Structural AST comparison',
    reference: 'Zhang–Shasha tree edit distance and shared subtrees',
    description:
      'Each submission is parsed into a canonical syntax skeleton with names and literal values removed. Comparing the shapes of two programs catches copies whose functions were reordered or whose loops were rewritten.',
    icon: (
      <Icon className="h-6 w-6">
        <rect x="9" y="3" width="6" height="4.5" rx="1" />
        <rect x="3" y="16.5" width="6" height="4.5" rx="1" />
        <rect x="15" y="16.5" width="6" height="4.5" rx="1" />
        <path d="M12 7.5V12M6 16.5V12h12v4.5" />
      </Icon>
    ),
  },
  {
    title: 'Explainable evidence',
    reference: 'Matched line regions and score breakdowns',
    description:
      'A verdict is never just a number. Every flagged pair shows the matching line ranges side by side and how the token, structure and baseline scores add up, so a teacher can check the evidence before acting on it.',
    icon: (
      <Icon className="h-6 w-6">
        <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4" />
        <path d="M14 3v5h5v2.5" />
        <path d="M8.5 12h4M8.5 15.5h2.5" />
        <circle cx="16.5" cy="16.5" r="3" />
        <path d="m18.7 18.7 2.3 2.3" />
      </Icon>
    ),
  },
]

function CheckIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm3.86-9.64a.75.75 0 0 0-1.22-.87l-3.24 4.53-1.62-1.62a.75.75 0 1 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.1l3.75-5.25Z"
        clipRule="evenodd"
      />
    </svg>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  // 'loading' | 'offline' (health check failed) | 'error' (server up, list failed) | 'ready'
  const [status, setStatus] = useState('loading')
  const [runs, setRuns] = useState([])
  const [loadError, setLoadError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [demoBusy, setDemoBusy] = useState(false)
  const [demoError, setDemoError] = useState(null)
  // The demo run can take a few seconds; if the user leaves the page meanwhile, the finished
  // request must not pull them back to the results page.
  const mounted = useRef(true)

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  useEffect(() => {
    let active = true
    Promise.allSettled([getHealth(), listRuns()]).then(([health, list]) => {
      if (!active) return
      if (health.status === 'rejected') {
        setStatus('offline')
      } else if (list.status === 'rejected') {
        setLoadError(errorMessage(list.reason))
        setStatus('error')
      } else {
        setRuns(Array.isArray(list.value) ? list.value : [])
        setStatus('ready')
      }
    })
    return () => {
      active = false
    }
  }, [reloadKey])

  const reload = () => {
    setStatus('loading')
    setLoadError(null)
    setReloadKey((key) => key + 1)
  }

  const runDemo = async () => {
    setDemoBusy(true)
    setDemoError(null)
    try {
      const run = await createDemoRun()
      if (mounted.current) navigate(`/runs/${run.id}`)
    } catch (err) {
      if (!mounted.current) return
      setDemoError(errorMessage(err))
      setDemoBusy(false)
    }
  }

  // Passed to RunsTable, which shows the error if this throws; the row disappears only after the
  // server has confirmed the deletion.
  const removeRun = async (run) => {
    await deleteRun(run.id)
    setRuns((current) => current.filter((item) => item.id !== run.id))
  }

  const demoButton = (
    <Button size="lg" loading={demoBusy} onClick={runDemo} icon={PLAY_ICON}>
      {demoBusy ? 'Running demo…' : 'Run demo analysis'}
    </Button>
  )

  let recent
  if (status === 'loading') {
    recent = (
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <Spinner center label="Loading recent analyses…" />
      </div>
    )
  } else if (status === 'offline') {
    recent = (
      <EmptyState
        icon={SERVER_ICON}
        title="Cannot reach the CodeSentry server"
        description={
          <>
            Saved analyses are stored by the analysis server, which is not responding. Open a terminal in the project
            folder, start it with{' '}
            <code className="whitespace-nowrap rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[13px] text-slate-800">
              python run_server.py
            </code>
            , then retry.
          </>
        }
        action={
          <Button variant="secondary" onClick={reload}>
            Retry connection
          </Button>
        }
      />
    )
  } else if (status === 'error') {
    recent = <ErrorBanner title="Could not load recent analyses" message={loadError} onRetry={reload} />
  } else if (runs.length === 0) {
    recent = (
      <EmptyState
        title="No analyses yet"
        description="Run the demo analysis to watch CodeSentry flag the planted copies in a sample class, or upload your own students' submissions."
        action={
          <div className="flex flex-wrap items-center justify-center gap-3">
            {demoButton}
            <Button size="lg" variant="secondary" to="/new">
              New analysis
            </Button>
          </div>
        }
      />
    )
  } else {
    recent = (
      <Card bodyClassName="p-0">
        <RunsTable runs={runs} onDelete={removeRun} />
      </Card>
    )
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Start a new plagiarism analysis, try the built-in demo class, or reopen an earlier run."
      />

      <div className="space-y-10">
        <section
          aria-labelledby="dashboard-hero-heading"
          className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
        >
          <div className="pointer-events-none absolute inset-0 bg-linear-to-br from-indigo-50 via-white to-white" aria-hidden="true" />
          <div className="relative grid gap-8 p-6 sm:p-8 lg:grid-cols-[minmax(0,1fr)_20rem] lg:gap-10 lg:p-10">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
                Source-code plagiarism detection for Python and C
              </p>
              <h2
                id="dashboard-hero-heading"
                className="mt-3 max-w-3xl text-2xl font-semibold leading-tight tracking-tight text-slate-900 sm:text-3xl lg:text-[2.125rem]"
              >
                Detect plagiarism in programming assignments — even after renaming, reformatting and reordering
              </h2>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
                CodeSentry compares every pair of submissions in a class twice — once as a stream of normalized tokens and
                once as a syntax tree — then points to the exact lines that match, so every verdict comes with evidence.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                {demoButton}
                <Button size="lg" variant="secondary" to="/new" icon={UPLOAD_ICON}>
                  New analysis
                </Button>
              </div>
              <p className="mt-3 text-sm text-slate-500" aria-live="polite">
                {demoBusy
                  ? 'Analyzing the sample class. This usually takes a few seconds.'
                  : 'The demo analyzes a sample class assignment with planted copies hidden among honest solutions.'}
              </p>
              <ErrorBanner
                className="mt-4"
                title="The demo analysis could not be started"
                message={demoError}
                onDismiss={() => setDemoError(null)}
              />
            </div>

            <div className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900">Built to see through</h3>
              <ul className="mt-4 space-y-3.5">
                {DISGUISES.map((item) => (
                  <li key={item.title} className="flex gap-3 text-sm">
                    <CheckIcon />
                    <span className="min-w-0">
                      <span className="block font-medium text-slate-800">{item.title}</span>
                      <span className="block text-slate-500">{item.detail}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section aria-labelledby="dashboard-features-heading">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
            <h2 id="dashboard-features-heading" className="text-lg font-semibold text-slate-900">
              How CodeSentry compares code
            </h2>
            <Link to="/how-it-works" className="rounded text-sm font-medium text-indigo-600 hover:text-indigo-800">
              See the full pipeline <span aria-hidden="true">→</span>
            </Link>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {FEATURES.map((feature) => (
              <article key={feature.title} className="flex flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                  {feature.icon}
                </span>
                <h3 className="mt-4 text-base font-semibold text-slate-900">{feature.title}</h3>
                <p className="mt-2 flex-1 text-sm leading-6 text-slate-600">{feature.description}</p>
                <p className="mt-4 border-t border-slate-100 pt-3 text-xs font-medium text-slate-500">{feature.reference}</p>
              </article>
            ))}
          </div>
        </section>

        <section aria-labelledby="dashboard-recent-heading">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 id="dashboard-recent-heading" className="text-lg font-semibold text-slate-900">
                Recent analyses
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                {status === 'ready' && runs.length > 0
                  ? `${runs.length} stored ${runs.length === 1 ? 'run' : 'runs'}, newest first. Open one to see its similarity matrix and flagged pairs.`
                  : 'Every analysis is stored on the server so it can be reopened later.'}
              </p>
            </div>
            {status === 'ready' && runs.length > 0 && (
              <Button variant="ghost" size="sm" onClick={reload}>
                Refresh
              </Button>
            )}
          </div>
          {recent}
        </section>
      </div>
    </>
  )
}
