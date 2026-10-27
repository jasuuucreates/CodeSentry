// How It Works page (route "/how-it-works") — explains the five stages of the detection pipeline in
// plain English, then lets the viewer run the real engine on two snippets step by step.
import { useEffect, useState } from 'react'
import { getDefaults } from '../api/client.js'
import PipelineExplainer from '../components/PipelineExplainer.jsx'
import Button from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'

// Built-in engine defaults, shown until GET /api/config/defaults answers (or if it fails).
const FALLBACK_SETTINGS = { w_token: 0.5, w_structure: 0.5, high_threshold: 0.75, moderate_threshold: 0.5, trained: false }

/** 0.9 -> "0.9", 0.583333 -> "0.58" */
function num(x) {
  return String(Math.round(x * 100) / 100)
}

/** 0.54 -> "54%" */
function percent(x) {
  return `${Math.round(x * 1000) / 10}%`
}

// Each stage: what happens (plain English), which disguises it defeats, and where it lives in the code.
// A paragraph may be a function of the live settings, so quoted numbers match what the server uses.
const STAGES = [
  {
    id: 'preprocessing',
    title: 'Preprocessing',
    summary: 'Get every submission ready to be compared fairly.',
    paragraphs: [
      'CodeSentry first works out which language each file is written in from its extension: .py is Python, .c and .h are C. Each language has its own reader in the next steps, because the same idea is written differently in the two.',
      "The text is kept exactly as submitted, together with its line numbers. Nothing is thrown away yet: every match found later must point back to real lines in the student's file, so a reviewer can see where the copied part is.",
      'In a class batch every file is prepared exactly once and reused for every pair it takes part in. Thirty students make 435 pairs, so doing this work once per file instead of once per pair keeps a whole-class analysis fast. A file that cannot be read as valid code is still listed, with a warning, instead of stopping the batch.',
    ],
    handles: ['Mixed Python and C uploads (only same-language pairs are compared)', 'Zip archives of a whole class', 'Broken files, reported instead of crashing the run'],
    modules: ['engine/lang.py', 'engine/pipeline.py'],
  },
  {
    id: 'tokenisation',
    title: 'Tokenisation',
    summary: 'Split the code into tokens and forget the details a copier can change for free.',
    paragraphs: [
      'The code is split into tokens, its smallest meaningful pieces: keywords such as for and return, names such as total, numbers, strings and operators such as +=. Python uses the standard library tokenizer; C uses a hand-written lexer that always takes the longest operator it can match, so >>= is read as one operator rather than >> followed by =.',
      'Each token is then normalised into a symbol. Every variable or function name becomes ID, every number NUM, every string STR. Keywords and operators stay as they are, because they are the shape of the program. Comments and preprocessor lines are removed, and spaces and blank lines were never tokens in the first place.',
      'A student who renames every variable and rewrites every comment therefore produces exactly the same symbol stream as the original.',
    ],
    handles: ['Renamed variables and functions', 'Changed, added or deleted comments', 'Re-indentation, blank lines and brace style'],
    modules: ['engine/tokenizer_python.py', 'engine/tokenizer_c.py', 'engine/normalizer.py'],
  },
  {
    id: 'fingerprinting',
    title: 'Fingerprinting (winnowing)',
    summary: 'Turn the symbol stream into a small set of fingerprints that copied code must share.',
    paragraphs: [
      'The symbol stream is cut into overlapping windows of k consecutive symbols called k-grams (k = 5 by default). Each k-gram is turned into a 64-bit number with the BLAKE2b hash. Identical pieces of code give identical numbers, and comparing numbers is far faster than comparing text.',
      'Keeping every hash would be wasteful, so winnowing (Schleimer, Wilkerson and Aiken, 2003) slides a window over w consecutive hashes (w = 4 by default) and keeps only the smallest hash in each window, taking the rightmost one on a tie. The kept hashes are the file’s fingerprints.',
      'Winnowing comes with a guarantee: any matching run of at least w + k − 1 symbols (8 by default) is certain to produce a shared fingerprint. The token score is the Jaccard similarity of the two fingerprint sets, shared fingerprints divided by all distinct fingerprints, and the positions of shared fingerprints become the matched line regions in the report.',
    ],
    handles: ['Copied blocks moved elsewhere in the file', 'Copying only part of another submission', 'Small edits between long copied runs'],
    modules: ['engine/winnowing.py'],
  },
  {
    id: 'structure',
    title: 'Structural analysis (AST)',
    summary: 'Compare the shape of the programs, not the order of their symbols.',
    paragraphs: [
      "Token matching can be weakened by edits that change the order of symbols, such as turning a for loop into a while loop or inserting unused statements. So each file is also parsed into its abstract syntax tree (Python's ast module, tree-sitter for C) and reduced to a skeleton that keeps only the kind of each node, never names or values.",
      'Both languages map onto one shared vocabulary of node labels, and every loop form (for, while, do-while) becomes the same Loop node. Top-level functions are put into a canonical order, so shuffling functions around does not change the tree.',
      'Two skeletons are compared in two ways: the Zhang–Shasha tree edit distance, which counts the node insertions, deletions and relabels needed to turn one tree into the other (very large trees use a fast sequence-based approximation), and the overlap of their bags of identical subtrees. The structure score is the average of the two.',
    ],
    handles: ['for loops rewritten as while loops', 'Functions shuffled into a different order', 'Dead code inserted between real statements'],
    modules: ['engine/structure_python.py', 'engine/structure_c.py', 'engine/structure_common.py', 'engine/tree_similarity.py'],
  },
  {
    id: 'fusion',
    title: 'Score fusion and reporting',
    summary: 'Combine both views into one score, a verdict and evidence a reviewer can check.',
    paragraphs: [
      // These two paragraphs quote the settings the server actually uses (GET /api/config/defaults),
      // which may be trained values rather than the built-in 0.5 / 0.5 weights and 75% / 50% thresholds.
      (d) =>
        `The two views are combined into a fused score: a weighted average of the token score and the structure score, weighted ${num(d.w_token)} and ${num(d.w_structure)} by default${d.trained ? ' (weights learned from the labelled dataset)' : ''} and adjustable for each analysis. If a file cannot be parsed into a tree, the token score is used on its own and a warning is shown.`,
      (d) =>
        `The fused score becomes a verdict: High at ${percent(d.high_threshold)} or more, Moderate from ${percent(d.moderate_threshold)}, otherwise Low${d.trained ? ' (thresholds learned from the labelled dataset)' : ''}. A verdict is a signal for a teacher to look closer, not an automatic accusation.`,
      'The report ranks every pair, draws a similarity heat map of the whole class and shows matched regions side by side. It also lists two baselines, plain text matching and TF-IDF cosine similarity, so a reviewer can see how much normalisation and structure added.',
    ],
    handles: ['A disguise that fools one view but not the other', 'Several disguises combined', 'Explaining a result to the student concerned'],
    modules: ['engine/fusion.py', 'engine/pipeline.py', 'backend/routes.py'],
  },
]

function Stepper({ active, onSelect }) {
  return (
    <nav aria-label="Pipeline stages">
      <ol className="grid gap-2 sm:grid-cols-5 sm:gap-0">
        {STAGES.map((stage, i) => {
          const current = i === active
          const done = i < active
          return (
            <li key={stage.id} className="relative">
              {/* Connector line to the next stage on wide screens. */}
              {i < STAGES.length - 1 && (
                <span
                  className={`absolute left-[calc(50%+1.5rem)] right-[calc(-50%+1.5rem)] top-5 hidden h-0.5 rounded-full sm:block ${
                    done ? 'bg-indigo-300' : 'bg-slate-200'
                  }`}
                  aria-hidden="true"
                />
              )}
              <button
                type="button"
                onClick={() => onSelect(i)}
                aria-current={current ? 'step' : undefined}
                aria-controls="stage-panel"
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 sm:flex-col sm:gap-2 sm:px-2 sm:py-1 sm:text-center ${
                  current ? 'bg-indigo-50 sm:bg-transparent' : 'hover:bg-slate-100 sm:hover:bg-transparent'
                }`}
              >
                <span
                  className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold ring-4 ring-slate-50 transition-colors ${
                    current
                      ? 'bg-indigo-600 text-white'
                      : done
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'border border-slate-300 bg-white text-slate-500'
                  }`}
                >
                  {i + 1}
                </span>
                <span className={`text-sm font-medium leading-5 ${current ? 'text-indigo-700' : 'text-slate-600'}`}>{stage.title}</span>
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

function StagePanel({ index, onSelect, settings }) {
  const stage = STAGES[index]
  const previous = STAGES[index - 1]
  const next = STAGES[index + 1]

  return (
    <Card
      id="stage-panel"
      title={`Stage ${index + 1} of ${STAGES.length}: ${stage.title}`}
      subtitle={stage.summary}
    >
      <div className="grid gap-8 lg:grid-cols-3">
        <div className="space-y-4 text-sm leading-7 text-slate-700 lg:col-span-2">
          {stage.paragraphs
            .map((paragraph) => (typeof paragraph === 'function' ? paragraph(settings) : paragraph))
            .map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
        </div>
        <aside className="space-y-6">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">What this stage handles</h3>
            <ul className="mt-2 space-y-2 text-sm text-slate-700">
              {stage.handles.map((item) => (
                <li key={item} className="flex gap-2">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600" aria-hidden="true">
                    <path d="m5 12.5 4.5 4.5L19 7.5" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Where it lives in the code</h3>
            <ul className="mt-2 flex flex-wrap gap-2">
              {stage.modules.map((module) => (
                <li key={module}>
                  <code className="rounded-md bg-slate-100 px-2 py-1 font-mono text-xs text-slate-700">{module}</code>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>

      <div className="mt-8 flex items-center justify-between gap-3 border-t border-slate-200 pt-4">
        {previous ? (
          <Button variant="secondary" size="sm" onClick={() => onSelect(index - 1)}>
            Previous: {previous.title}
          </Button>
        ) : (
          <span />
        )}
        {next && (
          <Button size="sm" onClick={() => onSelect(index + 1)}>
            Next: {next.title}
          </Button>
        )}
      </div>
    </Card>
  )
}

export default function HowItWorks() {
  const [active, setActive] = useState(0)
  const [settings, setSettings] = useState(FALLBACK_SETTINGS)

  useEffect(() => {
    let alive = true
    getDefaults()
      .then((d) => {
        if (!alive || !d) return
        const valid = ['w_token', 'w_structure', 'high_threshold', 'moderate_threshold'].every(
          (key) => typeof d[key] === 'number' && Number.isFinite(d[key]),
        )
        if (valid) setSettings({ ...d, trained: d.trained === true })
      })
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [])

  return (
    <>
      <PageHeader
        title="How It Works"
        subtitle="CodeSentry compares submissions in five stages. Each one removes a trick a copier might use to disguise borrowed code. Read the stages, then run the real engine on your own snippets below."
      />

      <div className="space-y-10">
        <section aria-labelledby="stages-heading" className="space-y-6">
          <h2 id="stages-heading" className="text-lg font-semibold text-slate-900">
            The detection pipeline
          </h2>
          <Stepper active={active} onSelect={setActive} />
          <StagePanel index={active} onSelect={setActive} settings={settings} />
        </section>

        <section aria-labelledby="try-heading">
          <Card
            title={
              <span id="try-heading" className="text-lg">
                Try it: run the pipeline step by step
              </span>
            }
            subtitle="Snippet B starts as a disguised copy of snippet A: renamed variables, a for loop rewritten as a while loop and an added comment. Edit either snippet, or paste your own, then run the engine to see what every stage produces."
          >
            <PipelineExplainer />
          </Card>
        </section>
      </div>
    </>
  )
}
