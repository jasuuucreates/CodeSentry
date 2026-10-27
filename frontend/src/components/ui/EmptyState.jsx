// EmptyState — friendly placeholder shown when a view has nothing to display yet.
// Props:
//   title       short headline, e.g. "No analysis runs yet"
//   description optional sentence explaining what to do next
//   action      optional element, usually a <Button>
//   icon        optional inline <svg> element; a neutral document icon is used when omitted
//   className   extra classes for the outer element

const DEFAULT_ICON = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6" aria-hidden="true">
    <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
    <path d="M14 3v5h5" />
    <path d="M9 13h6M9 17h4" />
  </svg>
)

export default function EmptyState({ title, description, action, icon, className = '' }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center ${className}`}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
        {icon ?? DEFAULT_ICON}
      </div>
      {title && <h3 className="mt-4 text-base font-semibold text-slate-900">{title}</h3>}
      {description && <p className="mt-1 max-w-md text-sm leading-6 text-slate-500">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
