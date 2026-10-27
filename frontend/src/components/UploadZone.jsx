// UploadZone — the drop area where submissions are added: drag and drop, click, or keyboard.
// Props:
//   onFiles   called with an array of File objects every time files are dropped or picked
//   accept    comma-separated extensions offered by the browse dialog (default '.py,.c,.h,.zip')
//   disabled  boolean — ignore drops and clicks, e.g. while an upload is in progress
//   hint      optional text under the main message, e.g. the upload limits
//
// The zone only collects files; it does not decide which ones are acceptable. The page that owns
// the file list applies the rules, so every validation message comes from one place.
import { useEffect, useId, useRef, useState } from 'react'

/** Browsers report dragged files with the "Files" type; dragged text or links are left alone. */
function isFileDrag(event) {
  return Array.from(event.dataTransfer?.types ?? []).includes('Files')
}

function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6" aria-hidden="true">
      <path d="M12 15V4" />
      <path d="m7.5 8.5 4.5-4.5 4.5 4.5" />
      <path d="M4 14.5V18a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3.5" />
    </svg>
  )
}

export default function UploadZone({ onFiles, accept = '.py,.c,.h,.zip', disabled = false, hint }) {
  const inputRef = useRef(null)
  // dragenter/dragleave also fire when the pointer crosses the zone's own child elements, so a
  // simple true/false flag would flicker. Counting enters minus leaves tells when it truly left.
  const dragDepth = useRef(0)
  const [dragging, setDragging] = useState(false)
  const hintId = useId()

  // A file dropped just outside the zone would make the browser open that file and navigate away,
  // throwing away the whole selection. While the zone is on screen such stray drops are cancelled.
  useEffect(() => {
    const cancelStrayDrop = (event) => {
      if (isFileDrag(event)) event.preventDefault()
    }
    window.addEventListener('dragover', cancelStrayDrop)
    window.addEventListener('drop', cancelStrayDrop)
    return () => {
      window.removeEventListener('dragover', cancelStrayDrop)
      window.removeEventListener('drop', cancelStrayDrop)
    }
  }, [])

  const openPicker = () => {
    if (!disabled) inputRef.current?.click()
  }

  const handleKeyDown = (event) => {
    // role="button" promises button behaviour, and native buttons activate on Enter and Space.
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openPicker()
    }
  }

  const handleDragEnter = (event) => {
    if (!isFileDrag(event)) return
    event.preventDefault()
    dragDepth.current += 1
    if (!disabled) setDragging(true)
  }

  const handleDragOver = (event) => {
    if (!isFileDrag(event)) return
    // Without preventDefault on dragover the browser refuses the drop.
    event.preventDefault()
    event.dataTransfer.dropEffect = disabled ? 'none' : 'copy'
  }

  const handleDragLeave = (event) => {
    if (!isFileDrag(event)) return
    dragDepth.current = Math.max(0, dragDepth.current - 1)
    if (dragDepth.current === 0) setDragging(false)
  }

  const handleDrop = (event) => {
    if (!isFileDrag(event)) return
    event.preventDefault()
    dragDepth.current = 0
    setDragging(false)
    if (disabled) return
    const files = Array.from(event.dataTransfer.files ?? [])
    if (files.length) onFiles(files)
  }

  const handleInputChange = (event) => {
    const files = Array.from(event.target.files ?? [])
    // Clearing the input lets the user pick the same file again after removing it from the list.
    event.target.value = ''
    if (files.length) onFiles(files)
  }

  let stateClasses = 'cursor-pointer border-slate-300 bg-slate-50/70 hover:border-indigo-400 hover:bg-indigo-50/40'
  if (disabled) stateClasses = 'cursor-not-allowed border-slate-200 bg-slate-50 opacity-60'
  else if (dragging) stateClasses = 'cursor-copy border-indigo-500 bg-indigo-50'

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled || undefined}
      aria-label="Add submission files: drop files here, or press Enter to browse"
      aria-describedby={hint ? hintId : undefined}
      onClick={openPicker}
      onKeyDown={handleKeyDown}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`group flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 ${stateClasses}`}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={accept}
        onChange={handleInputChange}
        className="hidden"
        tabIndex={-1}
        aria-hidden="true"
      />
      <span
        className={`flex h-12 w-12 items-center justify-center rounded-full bg-white shadow-sm ring-1 transition-colors ${
          dragging ? 'text-indigo-700 ring-indigo-300' : 'text-indigo-600 ring-slate-200'
        }`}
      >
        <UploadIcon />
      </span>
      <p className="mt-4 text-sm font-semibold text-slate-900">
        {dragging ? 'Release to add these files' : 'Drag and drop submissions here'}
      </p>
      <p className="mt-1 text-sm text-slate-600">
        or{' '}
        <span className="font-medium text-indigo-600 underline-offset-2 group-hover:underline">browse your computer</span>
      </p>
      {hint && (
        <p id={hintId} className="mt-3 max-w-md text-xs leading-5 text-slate-500">
          {hint}
        </p>
      )}
    </div>
  )
}
