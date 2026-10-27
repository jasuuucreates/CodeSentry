// ScoreBreakdown — every score of one pair with a plain-English line saying what it measures.
// Props:
//   scores    PairResult.scores   { token, containment, structure, ted, subtree, fused, text_baseline, tfidf_baseline }
//   stats     PairResult.stats    { a_tokens, b_tokens, a_fingerprints, b_fingerprints, shared_fingerprints,
//                                   a_nodes, b_nodes, k_effective, structure_method }
//   warnings  PairResult.warnings (strings)
//   config    optional EngineConfig of the run ({ k, w_token, w_structure, high_threshold, ... }); when it
//             has not arrived yet the card still renders, just without the exact fusion weights
//   className extra classes for the outer card
//
// Colour carries meaning here: CodeSentry's own signals are indigo, the fused score uses the verdict
// colours (it is the number the verdict is based on), and the naive baselines are grey because they are
// shown only for comparison and never influence the verdict.
import { palette } from '../lib/colors.js'
import { pct } from '../lib/format.js'
import Card from './ui/Card.jsx'
import ScoreBar from './ui/ScoreBar.jsx'

// Engine defaults (engine/models.py EngineConfig), used for bar colouring until the run config is known.
const DEFAULT_HIGH = 0.75
const DEFAULT_MODERATE = 0.5

const METHOD_LABELS = {
  'zhang-shasha': 'exact Zhang–Shasha tree edit distance',
  'preorder-sequence-approximation': 'a pre-order sequence approximation, used when a tree is too large for the exact algorithm',
}

function isNumber(x) {
  return typeof x === 'number' && Number.isFinite(x)
}

function count(x) {
  return isNumber(x) ? x.toLocaleString() : '—'
}

function SectionHeading({ title, description }) {
  return (
    <div className="mb-4">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</h3>
      {description && <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>}
    </div>
  )
}

/**
 * One labelled score. `nested` indents the row under the score it is a part of; `unavailableText`
 * replaces the bar when the value could not be computed, because an empty bar would read as "0%".
 */
function ScoreRow({ label, value, description, color, nested = false, unavailableText, high, moderate }) {
  const unavailable = !isNumber(value)
  return (
    <div className={nested ? 'border-l-2 border-slate-100 pl-4' : ''}>
      {unavailable ? (
        <>
          <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
            <span className="min-w-0 truncate text-slate-600">{label}</span>
            <span className="shrink-0 text-xs font-medium text-slate-500">{unavailableText ?? 'Unavailable'}</span>
          </div>
          <div className="h-2.5 rounded-full border border-dashed border-slate-300" aria-hidden="true" />
        </>
      ) : (
        <ScoreBar label={label} value={value} color={color} high={high} moderate={moderate} />
      )}
      {description && <div className="mt-1.5 text-xs leading-5 text-slate-500">{description}</div>}
    </div>
  )
}

export default function ScoreBreakdown({ scores = {}, stats = {}, warnings = [], config, className = '' }) {
  const high = isNumber(config?.high_threshold) ? config.high_threshold : DEFAULT_HIGH
  const moderate = isNumber(config?.moderate_threshold) ? config.moderate_threshold : DEFAULT_MODERATE
  const structureMissing = !isNumber(scores.structure)

  // The fusion weights are normalised to sum to 1 by the engine (engine/fusion.py), so the same is
  // done here before showing them as percentages.
  const weightSum = (config?.w_token ?? 0) + (config?.w_structure ?? 0)
  let fusedDescription = 'Weighted mean of the token fingerprint and structural similarity scores.'
  if (structureMissing) {
    fusedDescription = 'Structure unavailable, so the fused score is the token fingerprint similarity on its own.'
  } else if (weightSum > 0) {
    fusedDescription = `Weighted mean: ${pct(config.w_token / weightSum, 0)} token fingerprint similarity + ${pct(
      config.w_structure / weightSum,
      0,
    )} structural similarity, using this run's settings.`
  }

  const method = stats.structure_method
  const tedDescription = (
    <>
      How few edits (insert, delete, relabel) turn one skeleton into the other.
      {method && (
        <>
          {' '}Computed with {METHOD_LABELS[method] ?? 'the method'}{' '}
          <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[11px] text-slate-700">{method}</code>.
        </>
      )}
    </>
  )

  const configuredK = config?.k
  const kHint =
    isNumber(configuredK) && isNumber(stats.k_effective) && stats.k_effective !== configuredK
      ? `reduced from ${configuredK} for a short file`
      : 'k-gram length in tokens'

  const statItems = [
    { label: 'Tokens', value: `${count(stats.a_tokens)} / ${count(stats.b_tokens)}`, hint: 'A / B, after normalisation' },
    { label: 'Fingerprints', value: `${count(stats.a_fingerprints)} / ${count(stats.b_fingerprints)}`, hint: 'A / B, kept by winnowing' },
    { label: 'Shared fingerprints', value: count(stats.shared_fingerprints), hint: 'present in both files' },
    {
      label: 'AST nodes',
      value: stats.a_nodes == null && stats.b_nodes == null ? '—' : `${count(stats.a_nodes)} / ${count(stats.b_nodes)}`,
      hint: 'A / B, skeleton size',
    },
    { label: 'k used', value: count(stats.k_effective), hint: kHint },
  ]

  // A missing skeleton is explained even if the engine's own warning is worded differently, because
  // it changes how the fused score must be read.
  const notices = [
    ...(structureMissing
      ? ['Structural comparison was skipped because a syntax tree could not be built for at least one file; the verdict rests on the token score alone.']
      : []),
    ...warnings,
  ]

  return (
    <Card
      title="Score breakdown"
      subtitle="What each signal measured, and what simpler checkers would report for the same pair."
      className={className}
    >
      <div className="grid gap-8 md:grid-cols-2">
        <div>
          <SectionHeading title="CodeSentry signals" />
          <div className="space-y-5">
            <ScoreRow
              label="Token fingerprint similarity"
              value={scores.token}
              color={palette.indigo}
              description="Jaccard similarity of the winnowed fingerprints: the share of code sequences both files contain, immune to renaming and formatting."
            />
            <ScoreRow
              label="Containment"
              value={scores.containment}
              color={palette.indigo}
              description="How much of the smaller file appears in the larger one, so code copied into a bigger program still shows up."
            />
            <ScoreRow
              label="Structural similarity"
              value={scores.structure}
              color={palette.indigo}
              unavailableText="Structure unavailable"
              description="Compares program skeletons (syntax trees without names or values): immune to renaming and to swapping for and while loops."
            />
            <ScoreRow label="Tree edit similarity" value={scores.ted} color={palette.indigoLight} nested description={tedDescription} />
            <ScoreRow
              label="Subtree overlap"
              value={scores.subtree}
              color={palette.indigoLight}
              nested
              description="Share of identical sub-trees (loops, conditions, calls) the two skeletons have in common."
            />
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <ScoreRow label="Fused score" value={scores.fused} high={high} moderate={moderate} description={fusedDescription} />
            </div>
            {isNumber(scores.ml_probability) && (
              <div className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-4">
                <ScoreRow
                  label="Trained model (logistic regression)"
                  value={scores.ml_probability}
                  color={palette.indigo}
                  description="Probability of plagiarism learned from 290 labelled pairs, grouped cross-validation."
                />
              </div>
            )}
          </div>
        </div>

        <div className="space-y-8 border-t border-slate-200 pt-8 md:border-l md:border-t-0 md:pl-8 md:pt-0">
          <div>
            <SectionHeading
              title="Baselines for comparison"
              description="What naive checkers see. They are shown for contrast only and never affect the verdict."
            />
            <div className="space-y-5">
              <ScoreRow
                label="Plain text similarity"
                value={scores.text_baseline}
                color={palette.slate}
                description="Line-by-line diff of the raw files: renaming variables or reformatting makes it drop sharply."
              />
              <ScoreRow
                label="TF-IDF cosine"
                value={scores.tfidf_baseline}
                color={palette.slate}
                description="Compares how often each word appears, identifiers included, the way simple document checkers do."
              />
            </div>
          </div>

          <div>
            <SectionHeading title="Engine statistics" />
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3 md:grid-cols-2">
              {statItems.map((item) => (
                <div key={item.label} className="min-w-0">
                  <dt className="text-xs text-slate-500">{item.label}</dt>
                  <dd className="text-sm font-semibold text-slate-900 tabular-nums">{item.value}</dd>
                  <dd className="text-[11px] leading-4 text-slate-400">{item.hint}</dd>
                </div>
              ))}
            </dl>
          </div>

          {notices.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4" role="note">
              <p className="text-sm font-semibold text-amber-900">{notices.length === 1 ? 'Warning' : 'Warnings'}</p>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-sm leading-6 text-amber-800">
                {notices.map((notice, index) => (
                  <li key={index}>{notice}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
