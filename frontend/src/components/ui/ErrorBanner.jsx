// ErrorBanner — red alert box for a failed request or invalid input. Renders nothing without a message.
// Props:
//   message   the error text (typically errorMessage(err) from api/client.js); falsy -> renders nothing
//   title     bold first line (default "Something went wrong")
//   onRetry   optional callback — shows a "Try again" button
//   onDismiss optional callback — shows a close button
//   className extra classes for the outer element
import Button from './Button.jsx'

export default function ErrorBanner({ message, title = 'Something went wrong', onRetry, onDismiss, className = '' }) {
  if (!message) return null

  return (
    <div role="alert" className={`flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 ${className}`}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 h-5 w-5 shrink-0 text-red-600" aria-hidden="true">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7.5v5.5M12 16.5h.01" />
      </svg>
      <div className="min-w-0 flex-1 text-sm">
        <p className="font-semibold text-red-800">{title}</p>
        <p className="mt-1 break-words text-red-700">{message}</p>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} className="shrink-0">
          Try again
        </Button>
      )}
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss error"
          className="-m-1 shrink-0 rounded-md p-1 text-red-500 hover:bg-red-100 hover:text-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="h-4 w-4" aria-hidden="true">
            <path d="M6 6l12 12M18 6 6 18" />
          </svg>
        </button>
      )}
    </div>
  )
}
