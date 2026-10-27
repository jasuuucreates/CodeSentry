// New Analysis page (route "/new") — upload one assignment's submissions and start a comparison run.
//
// Files are collected in the browser and checked against the same limits the server enforces (file
// types, number of files, size), so an obvious mistake is explained at once instead of after a long
// upload. The request goes to POST /api/runs as multipart form data. The progress bar follows the
// upload; when every byte has been sent it switches to "Analyzing…", because the server compares all
// pairs before it answers. As soon as the run is stored, the browser opens its results page.
import { useEffect, useId, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createRun, errorMessage, getDefaults } from '../api/client.js'
import UploadZone from '../components/UploadZone.jsx'
import Button from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Spinner from '../components/ui/Spinner.jsx'

// Limits copied from backend/config.py (MAX_FILES, MAX_FILE_BYTES, MAX_CONTENT_LENGTH). The server
// checks them again; checking here as well only makes the feedback faster and clearer.
const MAX_FILES = 200
const MAX_FILE_BYTES = 2_000_000
const MAX_UPLOAD_BYTES = 60_000_000

// Accepted extensions and how each is labelled. `group` drives the per-language counts, because a
// submission is only ever compared with submissions written in the same language.
const FILE_KINDS = {
  '.py': { label: 'Python', group: 'python' },
  '.c': { label: 'C', group: 'c' },
  '.h': { label: 'C', group: 'c' },
  '.zip': { label: 'Archive', group: 'archive' },
}
const ACCEPT = Object.keys(FILE_KINDS).join(',')

const CHIP_CLASSES = {
  python: 'bg-indigo-50 text-indigo-700 ring-indigo-600/20',
  c: 'bg-slate-100 text-slate-700 ring-slate-500/20',
  archive: 'bg-white text-slate-600 ring-slate-300',
}

// EngineConfig defaults from engine/models.py, used only if GET /api/config/defaults cannot be read.
const FALLBACK_DEFAULTS = { k: 5, w: 4, w_token: 0.5, w_structure: 0.5 }

// The engine itself accepts k up to 50 and w up to 100, but assignments of a few hundred tokens
// only make sense with small values, and a narrower slider is precise exactly where it matters.
const K_RANGE = { min: 2, max: 30 }
const W_RANGE = { min: 1, max: 30 }
const PERCENT_RANGE = { min: 0, max: 100 }

const INPUT_BASE =
  'rounded-lg border bg-white text-sm text-slate-900 shadow-sm placeholder:text-slate-400 ' +
  'focus-visible:outline-none focus-visible:ring-2 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500'

/** "Report.PY" -> ".py"; a name without an extension (or a hidden file like ".py") -> "". */
function extensionOf(name) {
  const dot = name.lastIndexOf('.')
  return dot > 0 ? name.slice(dot).toLowerCase() : ''
}

/** Decimal units, matching the server limit of 2 MB = 2,000,000 bytes. */
function formatBytes(bytes) {
  if (bytes < 1000) return `${bytes} B`
  if (bytes < 1_000_000) return `${(bytes / 1000).toFixed(bytes < 10_000 ? 1 : 0)} KB`
  return `${(bytes / 1_000_000).toFixed(1)} MB`
}

function plural(count, word) {
  return `${count} ${word}${count === 1 ? '' : 's'}`
}

/** A readable list of file names that stays short when many files share the same problem. */
function nameList(names) {
  const shown = names.slice(0, 3).join(', ')
  return names.length > 3 ? `${shown} and ${names.length - 3} more` : shown
}

function isWholeNumberIn(text, { min, max }) {
  const trimmed = String(text).trim()
  if (trimmed === '') return false
  const value = Number(trimmed)
  return Number.isInteger(value) && value >= min && value <= max
}

/** Keeps only the four settings this page edits, ignoring anything missing or non-numeric. */
function pickDefaults(config) {
  const picked = { ...FALLBACK_DEFAULTS }
  for (const key of Object.keys(FALLBACK_DEFAULTS)) {
    if (typeof config?.[key] === 'number' && Number.isFinite(config[key])) picked[key] = config[key]
  }
  return picked
}

/**
 * Form state holds the text of every input, so a half-typed value is never silently rewritten.
 * Weights are shown as percentages that add up to 100: the engine normalizes the two weights to
 * sum to 1 anyway, so a 70 / 30 split is the most honest way to present them.
 */
function formFromConfig(config) {
  const total = config.w_token + config.w_structure
  const token = total > 0 ? Math.round((config.w_token / total) * 100) : 50
  return { k: String(config.k), w: String(config.w), token: String(token), structure: String(100 - token) }
}

function sameForm(a, b) {
  return ['k', 'w', 'token', 'structure'].every((key) => String(a[key]).trim() === String(b[key]).trim())
}

/** Turns the per-reason lists of refused files into one sentence each. */
function rejectionMessages(rejected) {
  const messages = []
  if (rejected.type.length) {
    messages.push(
      `${nameList(rejected.type)} ${rejected.type.length === 1 ? 'is not a supported file type' : 'are not supported file types'}; only .py, .c, .h and .zip files can be analyzed.`,
    )
  }
  if (rejected.size.length) {
    messages.push(
      `${nameList(rejected.size)} ${rejected.size.length === 1 ? 'is' : 'are'} larger than the 2 MB limit per file.`,
    )
  }
  if (rejected.empty.length) {
    messages.push(`${nameList(rejected.empty)} ${rejected.empty.length === 1 ? 'is' : 'are'} empty.`)
  }
  if (rejected.duplicate.length) {
    messages.push(`${nameList(rejected.duplicate)} ${rejected.duplicate.length === 1 ? 'is' : 'are'} already in the list.`)
  }
  if (rejected.overLimit > 0) {
    messages.push(
      `${plural(rejected.overLimit, 'file')} ${rejected.overLimit === 1 ? 'was' : 'were'} not added because one analysis can include at most ${MAX_FILES} files.`,
    )
  }
  return messages
}

function FileIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0 text-slate-400" aria-hidden="true">
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
      <path d="m10 13-2 2 2 2M14 13l2 2-2 2" />
    </svg>
  )
}

function ArchiveIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0 text-slate-400" aria-hidden="true">
      <rect x="3.5" y="4" width="17" height="4.5" rx="1" />
      <path d="M5 8.5V18a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.5" />
      <path d="M10 12.5h4" />
    </svg>
  )
}

function KindChip({ kind }) {
  return (
    <span
      className={`inline-flex w-16 shrink-0 justify-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${CHIP_CLASSES[kind.group]}`}
    >
      {kind.label}
    </span>
  )
}

/** A slider and a number box bound to the same value: the slider for quick exploration, the box for exact input. */
function RangeField({ label, description, value, onChange, range, unit, invalid = false, disabled = false, errorId }) {
  const id = useId()
  const numeric = Number(value)
  const sliderValue =
    String(value).trim() !== '' && Number.isFinite(numeric) ? Math.min(range.max, Math.max(range.min, numeric)) : range.min
  const describedBy = invalid && errorId ? `${id}-description ${errorId}` : `${id}-description`

  return (
    <div>
      <label htmlFor={`${id}-number`} className="text-sm font-medium text-slate-900">
        {label}
      </label>
      <p id={`${id}-description`} className="mt-1 text-sm leading-6 text-slate-500">
        {description}
      </p>
      <div className="mt-3 flex items-center gap-4">
        <input
          type="range"
          min={range.min}
          max={range.max}
          step={1}
          value={sliderValue}
          disabled={disabled}
          onChange={(event) => onChange(event.target.value)}
          aria-label={`${label} slider`}
          aria-describedby={`${id}-description`}
          className="h-2 min-w-0 flex-1 cursor-pointer accent-indigo-600 disabled:cursor-not-allowed"
        />
        <div className="flex shrink-0 items-center gap-1.5">
          <input
            id={`${id}-number`}
            type="number"
            inputMode="numeric"
            min={range.min}
            max={range.max}
            step={1}
            value={value}
            disabled={disabled}
            onChange={(event) => onChange(event.target.value)}
            aria-invalid={invalid || undefined}
            aria-describedby={describedBy}
            className={`${INPUT_BASE} h-10 w-20 px-3 text-right tabular-nums ${
              invalid ? 'border-red-400 focus-visible:ring-red-500' : 'border-slate-300 focus-visible:ring-indigo-500'
            }`}
          />
          <span className="w-4 text-sm text-slate-500" aria-hidden="true">
            {unit}
          </span>
        </div>
      </div>
    </div>
  )
}

function FieldError({ id, children }) {
  if (!children) return null
  return (
    <p id={id} className="mt-2 text-sm text-red-600">
      {children}
    </p>
  )
}

function Requirement({ met, children }) {
  return (
    <li className="flex items-start gap-2.5">
      {met ? (
        <svg viewBox="0 0 20 20" fill="currentColor" className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600" aria-hidden="true">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm3.86-9.64a.75.75 0 0 0-1.22-.87l-3.24 4.53-1.62-1.62a.75.75 0 1 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.1l3.75-5.25Z"
            clipRule="evenodd"
          />
        </svg>
      ) : (
        <span className="mt-0.5 h-4 w-4 shrink-0 rounded-full border-2 border-slate-300" aria-hidden="true" />
      )}
      <span className={met ? 'text-slate-700' : 'text-slate-500'}>
        <span className="sr-only">{met ? 'Done: ' : 'Not yet: '}</span>
        {children}
      </span>
    </li>
  )
}

function UploadProgress({ phase, progress, fileCount }) {
  if (phase === 'uploading') {
    const percent = progress === null ? null : Math.round(progress * 100)
    return (
      <div>
        <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
          <span className="font-medium text-slate-700">Uploading {plural(fileCount, 'file')}…</span>
          <span className="tabular-nums text-slate-500">{percent === null ? '' : `${percent}%`}</span>
        </div>
        <div
          role="progressbar"
          aria-label="Upload progress"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent ?? undefined}
          className="h-2 overflow-hidden rounded-full bg-slate-100"
        >
          <div
            className={`h-full rounded-full bg-indigo-600 transition-[width] duration-200 ${percent === null ? 'animate-pulse' : ''}`}
            style={{ width: `${percent ?? 100}%` }}
          />
        </div>
      </div>
    )
  }

  // The upload is complete; the server is now comparing pairs and cannot report partial progress.
  return (
    <div>
      <Spinner size="sm" label="Analyzing… comparing every pair of submissions" />
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-indigo-100" aria-hidden="true">
        <div className="h-full w-full animate-pulse rounded-full bg-indigo-500" />
      </div>
    </div>
  )
}

function Chevron({ open }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`h-5 w-5 shrink-0 text-slate-500 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
      aria-hidden="true"
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  )
}

export default function NewAnalysis() {
  const navigate = useNavigate()
  const [items, setItems] = useState([]) // [{ key, file, kind }]
  const [rejections, setRejections] = useState([])
  const [runName, setRunName] = useState('')
  const [defaults, setDefaults] = useState({ config: FALLBACK_DEFAULTS, status: 'loading' })
  const [form, setForm] = useState(() => formFromConfig(FALLBACK_DEFAULTS))
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [phase, setPhase] = useState('idle') // 'idle' | 'uploading' | 'analyzing'
  const [progress, setProgress] = useState(null)
  const [submitError, setSubmitError] = useState(null)
  const [showValidation, setShowValidation] = useState(false)

  const mounted = useRef(true)
  // Set once the user edits a setting, so server defaults that arrive late never overwrite their input.
  const settingsTouched = useRef(false)
  const fileList = useRef(null)
  const nameId = useId()
  const advancedPanelId = useId()
  const kErrorId = useId()
  const wErrorId = useId()
  const weightErrorId = useId()

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  useEffect(() => {
    let active = true
    getDefaults()
      .then((config) => {
        if (!active) return
        const picked = pickDefaults(config)
        setDefaults({ config: picked, status: 'loaded', trained: config?.trained === true })
        if (!settingsTouched.current) setForm(formFromConfig(picked))
      })
      .catch(() => {
        if (active) setDefaults((current) => ({ ...current, status: 'fallback' }))
      })
    return () => {
      active = false
    }
  }, [])

  const busy = phase !== 'idle'

  // ---- Derived facts about the current selection -------------------------------------------
  const counts = { python: 0, c: 0, archive: 0 }
  let totalBytes = 0
  for (const item of items) {
    counts[item.kind.group] += 1
    totalBytes += item.file.size
  }
  const sourceCount = counts.python + counts.c
  const hasEnoughFiles = counts.archive > 0 || sourceCount >= 2
  const withinTotalSize = totalBytes <= MAX_UPLOAD_BYTES

  const selectionErrors = []
  if (items.length === 0) {
    selectionErrors.push('Add at least two source files, or a .zip archive containing them.')
  } else if (!hasEnoughFiles) {
    selectionErrors.push('Add at least one more source file: a comparison needs two or more submissions (or upload a .zip archive).')
  }
  if (!withinTotalSize) {
    selectionErrors.push(
      `The selected files add up to ${formatBytes(totalBytes)}, but one upload can be at most 60 MB. Remove some files or split the class into two runs.`,
    )
  }

  // Not an error: the server accepts the batch, but it would contain no comparable pair.
  const languageWarning =
    counts.archive === 0 && sourceCount >= 2 && counts.python < 2 && counts.c < 2
      ? 'Submissions are only compared with others in the same language. With one Python file and one C file there is no pair to compare, so add more files in either language.'
      : null

  // ---- Settings validation ------------------------------------------------------------------
  const kError = isWholeNumberIn(form.k, K_RANGE) ? null : `k must be a whole number from ${K_RANGE.min} to ${K_RANGE.max}.`
  const wError = isWholeNumberIn(form.w, W_RANGE) ? null : `w must be a whole number from ${W_RANGE.min} to ${W_RANGE.max}.`
  let weightError = null
  if (!isWholeNumberIn(form.token, PERCENT_RANGE) || !isWholeNumberIn(form.structure, PERCENT_RANGE)) {
    weightError = 'Both weights must be whole percentages from 0 to 100.'
  } else if (Number(form.token) + Number(form.structure) !== 100) {
    weightError = 'The token and structure weights must add up to 100%.'
  }
  const hasSettingErrors = Boolean(kError || wError || weightError)
  const isDefaultSettings = sameForm(form, formFromConfig(defaults.config))
  const guaranteedLength = kError || wError ? null : Number(form.k) + Number(form.w) - 1

  // ---- File list actions --------------------------------------------------------------------
  const addFiles = (files) => {
    const known = new Set(items.map((item) => item.key))
    const added = []
    const rejected = { type: [], size: [], empty: [], duplicate: [], overLimit: 0 }

    for (const file of files) {
      const kind = FILE_KINDS[extensionOf(file.name)]
      // Name, size and modification time together identify "the same file picked twice" without
      // reading its contents; two different students' main.py files still get through.
      const key = `${file.name}:${file.size}:${file.lastModified}`
      if (!kind) rejected.type.push(file.name)
      else if (file.size > MAX_FILE_BYTES) rejected.size.push(file.name)
      else if (file.size === 0) rejected.empty.push(file.name)
      else if (known.has(key)) rejected.duplicate.push(file.name)
      else if (items.length + added.length >= MAX_FILES) rejected.overLimit += 1
      else {
        known.add(key)
        added.push({ key, file, kind })
      }
    }

    if (added.length) {
      // Sorted with numeric awareness so student_2 comes before student_10, whatever order the
      // operating system delivered the dropped files in.
      setItems((current) =>
        [...current, ...added].sort((a, b) =>
          a.file.name.localeCompare(b.file.name, undefined, { numeric: true, sensitivity: 'base' }),
        ),
      )
    }
    setRejections(rejectionMessages(rejected))
    setSubmitError(null)
  }

  const removeItem = (key) => {
    const index = items.findIndex((item) => item.key === key)
    setItems((current) => current.filter((item) => item.key !== key))
    setRejections([])
    setSubmitError(null)
    // Keep keyboard users in the list: focus moves to the remove button that took this row's place.
    requestAnimationFrame(() => {
      const buttons = fileList.current?.querySelectorAll('[data-remove-button]')
      if (buttons?.length) buttons[Math.min(index, buttons.length - 1)].focus()
    })
  }

  const clearAll = () => {
    setItems([])
    setRejections([])
    setSubmitError(null)
  }

  // ---- Settings actions ---------------------------------------------------------------------
  const updateSettings = (changes) => {
    settingsTouched.current = true
    setForm((current) => ({ ...current, ...changes }))
  }

  // Moving one weight moves the other, so the pair always describes a split of 100%.
  const setTokenWeight = (text) =>
    updateSettings(isWholeNumberIn(text, PERCENT_RANGE) ? { token: text, structure: String(100 - Number(text)) } : { token: text })
  const setStructureWeight = (text) =>
    updateSettings(isWholeNumberIn(text, PERCENT_RANGE) ? { structure: text, token: String(100 - Number(text)) } : { structure: text })

  const resetSettings = () => {
    settingsTouched.current = false
    setForm(formFromConfig(defaults.config))
  }

  // ---- Submit -------------------------------------------------------------------------------
  const handleSubmit = async (event) => {
    event.preventDefault()
    if (busy) return
    setSubmitError(null)

    if (selectionErrors.length > 0 || hasSettingErrors) {
      setShowValidation(true)
      if (hasSettingErrors) setAdvancedOpen(true)
      return
    }

    const formData = new FormData()
    for (const { file } of items) formData.append('files', file, file.name)
    const name = runName.trim()
    if (name) formData.append('name', name)
    // Unchanged settings are not sent, so the server applies its own defaults exactly (they may be
    // trained values with more decimals than the percentage sliders can show).
    if (!(isDefaultSettings && defaults.status === 'loaded')) {
      formData.append('k', String(Number(form.k)))
      formData.append('w', String(Number(form.w)))
      formData.append('w_token', String(Number(form.token) / 100))
      formData.append('w_structure', String(Number(form.structure) / 100))
    }

    setShowValidation(false)
    setProgress(null)
    setPhase('uploading')
    try {
      const run = await createRun(formData, (progressEvent) => {
        if (!mounted.current || !progressEvent.total) return
        const fraction = Math.min(1, progressEvent.loaded / progressEvent.total)
        setProgress(fraction)
        if (fraction >= 1) setPhase('analyzing')
      })
      if (mounted.current) navigate(`/runs/${run.id}`)
    } catch (err) {
      if (!mounted.current) return
      setSubmitError(errorMessage(err))
      setPhase('idle')
      setProgress(null)
    }
  }

  let validationMessage = null
  if (showValidation && (selectionErrors.length > 0 || hasSettingErrors)) {
    validationMessage = [...selectionErrors, hasSettingErrors ? 'Correct the highlighted advanced settings.' : null]
      .filter(Boolean)
      .join(' ')
  }

  let buttonLabel = 'Analyze submissions'
  if (phase === 'uploading') buttonLabel = 'Uploading…'
  if (phase === 'analyzing') buttonLabel = 'Analyzing…'

  return (
    <>
      <PageHeader
        back={{ to: '/', label: 'Dashboard' }}
        title="New Analysis"
        subtitle="Upload the submissions for one assignment. Every Python or C file is compared with every other file written in the same language."
      />

      <form onSubmit={handleSubmit} noValidate className="grid gap-6 lg:grid-cols-3 lg:items-start">
        <div className="min-w-0 space-y-6 lg:col-span-2">
          <Card title="Submissions" subtitle="One source file per student, or a .zip archive that contains them.">
            <UploadZone
              onFiles={addFiles}
              accept={ACCEPT}
              disabled={busy}
              hint={`Python (.py) and C (.c, .h) files, or .zip archives of them · up to ${MAX_FILES} files · 2 MB per file`}
            />

            <ErrorBanner
              className="mt-4"
              title="Some files were not added"
              message={rejections.join(' ')}
              onDismiss={() => setRejections([])}
            />

            {items.length === 0 ? (
              <p className="mt-4 text-center text-sm text-slate-500">No files selected yet.</p>
            ) : (
              <div className="mt-6">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-sm font-semibold text-slate-900">
                    Selected files <span className="font-normal text-slate-500">({items.length})</span>
                  </h3>
                  <Button variant="ghost" size="sm" onClick={clearAll} disabled={busy}>
                    Remove all
                  </Button>
                </div>
                <ul
                  ref={fileList}
                  className="mt-2 max-h-[26rem] divide-y divide-slate-200 overflow-y-auto rounded-lg border border-slate-200"
                >
                  {items.map((item) => (
                    <li key={item.key} className="flex items-center gap-3 px-4 py-2.5">
                      {item.kind.group === 'archive' ? <ArchiveIcon /> : <FileIcon />}
                      <span className="min-w-0 flex-1 truncate text-sm font-medium text-slate-900" title={item.file.name}>
                        {item.file.name}
                      </span>
                      <KindChip kind={item.kind} />
                      <span className="w-16 shrink-0 text-right text-sm tabular-nums text-slate-500">
                        {formatBytes(item.file.size)}
                      </span>
                      <button
                        type="button"
                        data-remove-button
                        onClick={() => removeItem(item.key)}
                        disabled={busy}
                        aria-label={`Remove ${item.file.name}`}
                        className="-mr-1.5 shrink-0 rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="h-4 w-4" aria-hidden="true">
                          <path d="M6 6l12 12M18 6 6 18" />
                        </svg>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {languageWarning && (
              <p className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
                {languageWarning}
              </p>
            )}
          </Card>

          <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <h2>
              <button
                type="button"
                onClick={() => setAdvancedOpen((open) => !open)}
                aria-expanded={advancedOpen}
                aria-controls={advancedPanelId}
                className="flex w-full items-center justify-between gap-4 rounded-xl px-6 py-4 text-left hover:bg-slate-50/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500"
              >
                <span className="min-w-0">
                  <span className="block text-base font-semibold text-slate-900">Advanced settings</span>
                  <span className="mt-1 block text-sm text-slate-500">
                    k = {form.k || '?'} · w = {form.w || '?'} · token {form.token || '?'}% / structure {form.structure || '?'}%
                    {isDefaultSettings ? (defaults.trained ? ' (trained defaults)' : ' (defaults)') : ''}
                  </span>
                </span>
                <Chevron open={advancedOpen} />
              </button>
            </h2>

            <div id={advancedPanelId} hidden={!advancedOpen} className="space-y-8 border-t border-slate-200 px-6 py-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm text-slate-600" aria-live="polite">
                  {defaults.status === 'loading' && 'Loading the server’s default settings…'}
                  {defaults.status === 'loaded' && 'Defaults come from the analysis server. Most classes need no changes.'}
                  {defaults.status === 'fallback' &&
                    'The server’s defaults could not be loaded, so the engine’s built-in defaults are shown.'}
                </p>
                <Button variant="ghost" size="sm" onClick={resetSettings} disabled={busy || isDefaultSettings}>
                  Reset to defaults
                </Button>
              </div>

              <fieldset className="space-y-6" disabled={busy}>
                <legend className="text-xs font-semibold uppercase tracking-wider text-slate-500">Token fingerprinting</legend>
                <div>
                  <RangeField
                    label="k-gram length (k)"
                    description="How many consecutive normalized tokens form one fingerprint. Smaller values catch shorter copied fragments, but also more coincidental matches."
                    value={form.k}
                    onChange={(text) => updateSettings({ k: text })}
                    range={K_RANGE}
                    invalid={showValidation && Boolean(kError)}
                    errorId={kErrorId}
                  />
                  <FieldError id={kErrorId}>{showValidation && kError}</FieldError>
                </div>
                <div>
                  <RangeField
                    label="Winnowing window (w)"
                    description="One fingerprint is kept from every w consecutive k-grams. Larger windows store fewer fingerprints."
                    value={form.w}
                    onChange={(text) => updateSettings({ w: text })}
                    range={W_RANGE}
                    invalid={showValidation && Boolean(wError)}
                    errorId={wErrorId}
                  />
                  <FieldError id={wErrorId}>{showValidation && wError}</FieldError>
                </div>
                {guaranteedLength !== null && (
                  <p className="rounded-lg bg-indigo-50 px-4 py-3 text-sm leading-6 text-indigo-900">
                    Any identical run of at least <span className="font-semibold">w + k − 1 = {guaranteedLength}</span>{' '}
                    normalized tokens is guaranteed to share a fingerprint.
                  </p>
                )}
              </fieldset>

              <fieldset className="space-y-6" disabled={busy}>
                <legend className="text-xs font-semibold uppercase tracking-wider text-slate-500">Score fusion</legend>
                <RangeField
                  label="Token weight"
                  description="Share of the final score taken from token fingerprint similarity."
                  value={form.token}
                  onChange={setTokenWeight}
                  range={PERCENT_RANGE}
                  unit="%"
                  invalid={showValidation && Boolean(weightError)}
                  errorId={weightErrorId}
                />
                <RangeField
                  label="Structure weight"
                  description="Share taken from structural (syntax tree) similarity. The two weights always add up to 100%."
                  value={form.structure}
                  onChange={setStructureWeight}
                  range={PERCENT_RANGE}
                  unit="%"
                  invalid={showValidation && Boolean(weightError)}
                  errorId={weightErrorId}
                />
                <FieldError id={weightErrorId}>{showValidation && weightError}</FieldError>
                {!weightError && (
                  <div>
                    <div className="flex h-2.5 overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
                      <div className="bg-indigo-600 transition-[width] duration-200" style={{ width: `${form.token}%` }} />
                      <div className="bg-indigo-300 transition-[width] duration-200" style={{ width: `${form.structure}%` }} />
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                      Final score = <span className="font-medium text-slate-900">{form.token}%</span> × token similarity +{' '}
                      <span className="font-medium text-slate-900">{form.structure}%</span> × structural similarity
                    </p>
                  </div>
                )}
              </fieldset>
            </div>
          </section>
        </div>

        <div className="min-w-0 lg:sticky lg:top-6">
          <Card title="Start the analysis">
            <div className="space-y-6">
              <div>
                <label htmlFor={nameId} className="text-sm font-medium text-slate-900">
                  Run name <span className="font-normal text-slate-500">(optional)</span>
                </label>
                <input
                  id={nameId}
                  type="text"
                  value={runName}
                  onChange={(event) => setRunName(event.target.value)}
                  maxLength={120}
                  placeholder="e.g. Assignment 3, Section B"
                  disabled={busy}
                  className={`${INPUT_BASE} mt-2 block h-10 w-full border-slate-300 px-3 focus-visible:ring-indigo-500`}
                />
                <p className="mt-1.5 text-xs text-slate-500">Helps you find this run on the dashboard later.</p>
              </div>

              <dl className="grid grid-cols-2 gap-3">
                {[
                  ['Files', items.length],
                  ['Total size', formatBytes(totalBytes)],
                  ['Python', counts.python],
                  ['C', counts.c],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-lg bg-slate-50 px-3 py-2.5">
                    <dt className="text-xs text-slate-500">{label}</dt>
                    <dd className="mt-0.5 text-lg font-semibold tabular-nums text-slate-900">{value}</dd>
                  </div>
                ))}
              </dl>
              {counts.archive > 0 && (
                <p className="-mt-3 text-xs text-slate-500">
                  Plus {plural(counts.archive, 'archive')}; the server extracts the .py, .c and .h files inside.
                </p>
              )}

              <ul className="space-y-2 text-sm" aria-label="Requirements">
                <Requirement met={hasEnoughFiles}>Two or more source files, or a .zip archive</Requirement>
                <Requirement met={items.length <= MAX_FILES}>
                  At most {MAX_FILES} files ({items.length} selected)
                </Requirement>
                <Requirement met={withinTotalSize}>Total upload up to 60 MB</Requirement>
              </ul>

              <ErrorBanner title="The analysis cannot start yet" message={validationMessage} />
              <ErrorBanner title="The analysis failed" message={submitError} onDismiss={() => setSubmitError(null)} />

              {busy && (
                <div aria-live="polite">
                  <UploadProgress phase={phase} progress={progress} fileCount={items.length} />
                </div>
              )}

              <Button type="submit" size="lg" className="w-full" loading={busy}>
                {buttonLabel}
              </Button>

              <p className="text-xs leading-5 text-slate-500">
                The files are uploaded, every same-language pair is compared on tokens and structure, and the results page
                opens automatically when the analysis finishes.
              </p>
            </div>
          </Card>
        </div>
      </form>
    </>
  )
}
