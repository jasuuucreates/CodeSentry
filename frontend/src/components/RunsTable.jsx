// RunsTable — table of stored analysis runs, newest first, as returned by GET /api/runs.
// Props:
//   runs      RunSummary[]: {id, name, created_at, file_count, pair_count, high, moderate, low,
//             max_score, mean_score, elapsed_ms}
//   onDelete  async (run) => void — deletes the run on the server and removes it from `runs`;
//             if the promise rejects, the error is shown above the table
//
// Deleting a run cannot be undone, so Delete first asks for confirmation inside the row itself
// instead of in a browser pop-up. Keyboard focus moves onto the confirmation buttons (Cancel first,
// the safe choice) and returns to the Delete button if the user backs out or presses Escape.
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage } from '../api/client.js'
import { dateTime, duration } from '../lib/format.js'
import Badge from './ui/Badge.jsx'
import Button from './ui/Button.jsx'
import ErrorBanner from './ui/ErrorBanner.jsx'
import ScoreBar from './ui/ScoreBar.jsx'

const HEADER_CELL = 'px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 first:pl-6 last:pr-6'
const BODY_CELL = 'px-4 py-4 align-middle first:pl-6 last:pr-6'

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
      <path d="M4 7h16" />
      <path d="M9.5 7V4.5h5V7" />
      <path d="M6.5 7l.9 12.2a1.5 1.5 0 0 0 1.5 1.3h6.2a1.5 1.5 0 0 0 1.5-1.3L17.5 7" />
      <path d="M10 11v6M14 11v6" />
    </svg>
  )
}

/**
 * Counts of High / Moderate / Low pairs. A zero count is drawn in neutral grey so that red only
 * ever appears when there really is a highly similar pair in the run.
 */
function VerdictCounts({ run }) {
  const counts = [
    ['High', run.high],
    ['Moderate', run.moderate],
    ['Low', run.low],
  ]
  return (
    <div className="flex gap-1.5">
      {counts.map(([verdict, count]) => {
        const n = count ?? 0
        return (
          <Badge key={verdict} tone={n > 0 ? verdict : 'neutral'} dot={n > 0} className="tabular-nums">
            {n} {verdict}
          </Badge>
        )
      })}
    </div>
  )
}

export default function RunsTable({ runs, onDelete }) {
  const [confirmingId, setConfirmingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [error, setError] = useState(null)
  const cancelButton = useRef(null)
  const deleteButtons = useRef(new Map())
  const restoreFocusTo = useRef(null)

  // Focus follows the confirmation: onto Cancel when it opens, back to the row's Delete button
  // when it closes without deleting (a deleted row no longer has a button to return to).
  useEffect(() => {
    if (confirmingId !== null) {
      cancelButton.current?.focus()
      return
    }
    if (restoreFocusTo.current !== null) {
      deleteButtons.current.get(restoreFocusTo.current)?.focus()
      restoreFocusTo.current = null
    }
  }, [confirmingId])

  const askToDelete = (run) => {
    setError(null)
    setConfirmingId(run.id)
  }

  const cancelDelete = (run) => {
    restoreFocusTo.current = run.id
    setConfirmingId(null)
  }

  const confirmDelete = async (run) => {
    setDeletingId(run.id)
    setError(null)
    try {
      await onDelete(run)
    } catch (err) {
      setError(`"${run.name}" was not deleted. ${errorMessage(err)}`)
      restoreFocusTo.current = run.id
    } finally {
      setDeletingId(null)
      setConfirmingId(null)
    }
  }

  return (
    <div>
      {error && (
        <div className="border-b border-slate-200 p-4">
          <ErrorBanner title="Delete failed" message={error} onDismiss={() => setError(null)} />
        </div>
      )}
      {/* `relative` makes this scroll box the containing block of the screen-reader-only labels
          inside the table; otherwise those absolutely positioned labels escape the box and widen
          the whole page on a phone. */}
      <div className="relative overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <caption className="sr-only">Stored analysis runs, newest first</caption>
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className={`${HEADER_CELL} text-left`}>
                Analysis
              </th>
              <th scope="col" className={`${HEADER_CELL} text-left`}>
                Date
              </th>
              <th scope="col" className={`${HEADER_CELL} text-right`}>
                Files
              </th>
              <th scope="col" className={`${HEADER_CELL} text-right`}>
                Pairs
              </th>
              <th scope="col" className={`${HEADER_CELL} text-left`}>
                Verdicts
              </th>
              <th scope="col" className={`${HEADER_CELL} text-left`}>
                Max score
              </th>
              <th scope="col" className={`${HEADER_CELL} text-right`}>
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {runs.map((run) => {
              const confirming = confirmingId === run.id
              const deleting = deletingId === run.id
              return (
                <tr key={run.id} className={confirming ? 'bg-red-50/50' : 'hover:bg-slate-50/70'}>
                  <td className={BODY_CELL}>
                    <Link
                      to={`/runs/${run.id}`}
                      className="block max-w-[16rem] truncate rounded font-medium text-slate-900 hover:text-indigo-700"
                      title={run.name}
                    >
                      {run.name}
                    </Link>
                    <span className="mt-0.5 block text-xs text-slate-500">Run #{run.id}</span>
                  </td>
                  <td className={`${BODY_CELL} whitespace-nowrap`}>
                    <span className="block text-slate-700">{dateTime(run.created_at)}</span>
                    <span className="mt-0.5 block text-xs text-slate-500">Analyzed in {duration(run.elapsed_ms)}</span>
                  </td>
                  <td className={`${BODY_CELL} text-right tabular-nums text-slate-700`}>{run.file_count ?? '—'}</td>
                  <td className={`${BODY_CELL} text-right tabular-nums text-slate-700`}>{run.pair_count ?? '—'}</td>
                  <td className={BODY_CELL}>
                    <VerdictCounts run={run} />
                  </td>
                  <td className={BODY_CELL}>
                    <ScoreBar value={run.max_score} inline size="sm" label={`Highest similarity in ${run.name}`} className="w-36" />
                  </td>
                  <td className={`${BODY_CELL} whitespace-nowrap text-right`}>
                    {confirming ? (
                      <div
                        role="group"
                        aria-label={`Confirm deleting ${run.name}`}
                        className="flex items-center justify-end gap-2"
                        onKeyDown={(event) => {
                          if (event.key === 'Escape' && !deleting) cancelDelete(run)
                        }}
                      >
                        <span className="mr-1 text-sm font-medium text-slate-700">Delete this run?</span>
                        <Button ref={cancelButton} variant="secondary" size="sm" disabled={deleting} onClick={() => cancelDelete(run)}>
                          Cancel
                        </Button>
                        <Button variant="danger" size="sm" loading={deleting} onClick={() => confirmDelete(run)}>
                          Delete
                        </Button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-end gap-2">
                        <Button variant="secondary" size="sm" to={`/runs/${run.id}`} aria-label={`Open ${run.name}`}>
                          Open
                        </Button>
                        <Button
                          ref={(node) => {
                            deleteButtons.current.set(run.id, node)
                            return () => deleteButtons.current.delete(run.id)
                          }}
                          variant="ghost"
                          size="sm"
                          icon={<TrashIcon />}
                          disabled={deletingId !== null}
                          onClick={() => askToDelete(run)}
                          aria-label={`Delete ${run.name}`}
                        >
                          Delete
                        </Button>
                      </div>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
