// Card — white surface with a subtle border that groups related content.
// Props:
//   title         optional heading shown in a header row
//   subtitle      optional muted line under the title
//   actions       optional element(s) aligned to the right of the header (buttons, filters)
//   children      card body
//   className     extra classes for the outer <section> (e.g. 'h-full')
//   bodyClassName classes for the body wrapper (default 'p-6'; pass 'p-0' for edge-to-edge tables)
//   every other prop is passed to the <section>

export default function Card({ title, subtitle, actions, children, className = '', bodyClassName = 'p-6', ...rest }) {
  const hasHeader = Boolean(title || subtitle || actions)

  return (
    <section className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`} {...rest}>
      {hasHeader && (
        <header className="flex flex-wrap items-start justify-between gap-x-4 gap-y-3 border-b border-slate-200 px-6 py-4">
          <div className="min-w-0">
            {title && <h2 className="text-base font-semibold text-slate-900">{title}</h2>}
            {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
          </div>
          {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
        </header>
      )}
      {children != null && children !== false && <div className={bodyClassName}>{children}</div>}
    </section>
  )
}
