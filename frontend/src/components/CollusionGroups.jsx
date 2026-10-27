// CollusionGroups — "suspected collusion groups" of a run, one small network diagram per group.
//
// Props:
//   clusters  run.clusters from GET /api/runs/:id: [{members: [{id, name}], edges: [{a_id, b_id, fused, verdict}], max_score}]
//   runId     id of the run (edge links go to /runs/:runId/pairs/:a/:b)
//   config    run.config (its moderate_threshold is the linking threshold)
//
// A group is every set of files connected by pairs scoring at or above the Moderate threshold, so
// A–B and B–C put A, B and C in one group even if A–C scored low (chains of copying). Nodes sit on
// a circle; an edge's thickness and colour show its fused score, and clicking it opens the pair.
import { useNavigate } from 'react-router-dom'
import { palette } from '../lib/colors.js'
import { pct } from '../lib/format.js'

const W = 300
const H = 200

function shortName(name) {
  const text = String(name)
  return text.length > 18 ? `${text.slice(0, 17)}…` : text
}

function layout(members, h) {
  const n = members.length
  const cx = W / 2
  const cy = n === 2 ? h / 2 - 8 : h / 2 - 4
  if (n === 2) {
    return [
      { ...members[0], x: cx - 80, y: cy, dy: 1 },
      { ...members[1], x: cx + 80, y: cy, dy: 1 },
    ]
  }
  const r = n <= 4 ? 58 : 66
  return members.map((m, i) => {
    const angle = -Math.PI / 2 + (2 * Math.PI * i) / n
    return { ...m, x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle), dy: Math.sin(angle) }
  })
}

function edgeColor(verdict) {
  if (verdict === 'High') return palette.red
  if (verdict === 'Moderate') return palette.amber
  return palette.green
}

function GroupDiagram({ cluster, runId, index }) {
  const navigate = useNavigate()
  // A pair needs no circle: a shorter drawing avoids an empty band above and below the link.
  const h = cluster.members.length === 2 ? 110 : H
  const nodes = layout(cluster.members, h)
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const open = (edge) => navigate(`/runs/${runId}/pairs/${edge.a_id}/${edge.b_id}`)

  return (
    <svg viewBox={`0 0 ${W} ${h}`} className="h-auto w-full" role="group" aria-label={`Collusion group ${index + 1}`}>
      {cluster.edges.map((edge) => {
        const a = byId.get(edge.a_id)
        const b = byId.get(edge.b_id)
        if (!a || !b) return null
        const label = `${a.name} vs ${b.name}: ${pct(edge.fused)} (${edge.verdict}). Open the side-by-side comparison.`
        const mx = (a.x + b.x) / 2
        const my = (a.y + b.y) / 2
        return (
          <g
            key={`${edge.a_id}-${edge.b_id}`}
            role="link"
            tabIndex={0}
            aria-label={label}
            className="cursor-pointer focus:outline-none [&:focus-visible>line.hit]:stroke-indigo-300"
            onClick={() => open(edge)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault()
                open(edge)
              }
            }}
          >
            <title>{label}</title>
            <line className="hit" x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="transparent" strokeWidth={16} strokeLinecap="round" />
            <line
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={edgeColor(edge.verdict)}
              strokeOpacity={0.35 + 0.65 * edge.fused}
              strokeWidth={1.5 + 6 * edge.fused}
              strokeLinecap="round"
            />
            <text
              x={mx}
              y={my - 6}
              textAnchor="middle"
              className="fill-slate-700 text-[12px] font-semibold tabular-nums"
              style={{ paintOrder: 'stroke', stroke: 'white', strokeWidth: 4 }}
            >
              {pct(edge.fused, 0)}
            </text>
          </g>
        )
      })}
      {nodes.map((node) => (
        <g key={node.id}>
          <circle cx={node.x} cy={node.y} r={10} fill="white" stroke={palette.indigo} strokeWidth={2.5} />
          <circle cx={node.x} cy={node.y} r={3.5} fill={palette.indigo} />
          <text
            x={node.x}
            y={node.dy < -0.3 ? node.y - 15 : node.y + 24}
            textAnchor="middle"
            className="fill-slate-900 font-mono text-[12px]"
            style={{ paintOrder: 'stroke', stroke: 'white', strokeWidth: 4 }}
          >
            {shortName(node.name)}
          </text>
        </g>
      ))}
    </svg>
  )
}

export default function CollusionGroups({ clusters = [], runId, config }) {
  const threshold = config?.moderate_threshold ?? 0.5

  if (!clusters.length) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 px-6 py-8 text-center">
        <p className="text-sm font-semibold text-slate-900">No groups above the moderate threshold</p>
        <p className="mt-1 text-sm text-slate-500">
          No pair of files reached {pct(threshold, 0)}, so no submissions are linked into a suspected group.
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {clusters.map((cluster, index) => (
        <figure key={cluster.members.map((m) => m.id).join("-")} className="flex flex-col rounded-xl border border-slate-200 bg-white p-4">
          <figcaption>
            <span className="block text-sm font-semibold text-slate-900">Group {index + 1}</span>
            <span className="mt-0.5 block text-xs text-slate-500">
              {cluster.members.length} students · strongest link{' '}
              <span className="font-semibold text-slate-900">{pct(cluster.max_score)}</span>
            </span>
          </figcaption>
          <div className="mt-2 flex flex-1 items-center">
            <GroupDiagram cluster={cluster} runId={runId} index={index} />
          </div>
        </figure>
      ))}
    </div>
  )
}
