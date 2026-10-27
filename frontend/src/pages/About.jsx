// About page (route "/about") — project identity for the report and the viva: abstract, objectives,
// technology stack and team. All content is static, so the page makes no API calls and works even
// when the analysis server is not running.
import Card from '../components/ui/Card.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'

const OBJECTIVES = [
  {
    title: 'Normalize source code',
    text: 'Tokenize Python and C submissions and replace identifiers, literals and layout with abstract symbols, so renaming, comments and formatting cannot change the result.',
  },
  {
    title: 'Fingerprint with winnowing',
    text: 'Hash k-grams of normalized tokens and select a compact set of fingerprints with the winnowing algorithm to measure token-level overlap efficiently.',
  },
  {
    title: 'Compare program structure',
    text: 'Parse submissions into canonical abstract syntax tree skeletons and compare them with tree edit distance and shared subtrees, so reordered functions and loop rewrites are still recognized.',
  },
  {
    title: 'Fuse the evidence into a verdict',
    text: 'Combine the token and structural scores with configurable weights into one similarity score and a High, Moderate or Low verdict.',
  },
  {
    title: 'Explain every result',
    text: 'Show matched line regions side by side, a breakdown of every score and a class-wide similarity matrix, so each flagged pair can be verified by a teacher.',
  },
  {
    title: 'Evaluate against baselines',
    text: 'Measure precision, recall, F1 score and ROC AUC on a labelled dataset of obfuscated and independently written solutions, compared with plain text matching and TF-IDF cosine similarity.',
  },
  {
    title: 'Deliver a usable offline tool',
    text: 'Provide batch uploads, stored analysis runs and a documented REST API behind a web interface that runs without an internet connection.',
  },
]

const STACK = [
  {
    layer: 'Detection engine',
    technology: 'Python 3.11, standard library',
    role: 'Tokenizers, winnowing, tree edit distance and score fusion, with every formula written out explicitly',
  },
  {
    layer: 'Parsing',
    technology: 'Python ast and tokenize; tree-sitter with tree-sitter-c',
    role: 'Tokens and syntax trees for Python and C submissions',
  },
  { layer: 'Backend', technology: 'Flask, Flask-CORS', role: 'REST API for uploads, runs, pair details and explanations' },
  {
    layer: 'Database',
    technology: 'SQLAlchemy 2 (synchronous ORM), SQLite',
    role: 'Stores analysis runs, submissions and pair scores',
  },
  { layer: 'Frontend', technology: 'React 19, React Router 7', role: 'Single-page web interface' },
  { layer: 'Styling and build', technology: 'Tailwind CSS 4, Vite 8', role: 'Design system and production build' },
  {
    layer: 'Charts and HTTP',
    technology: 'Chart.js 4 with react-chartjs-2, Axios',
    role: 'Evaluation charts and API calls with upload progress',
  },
  { layer: 'Testing', technology: 'pytest', role: 'Unit tests for the engine and integration tests for the API' },
]

const TEAM = [
  { name: 'Jasman Singh', registration: '2427030131', programme: 'B.Tech CSE' },
  { name: 'Tapish Thakur', registration: '2427030132', programme: 'B.Tech CSE' },
]

const DETAILS = [
  ['Institution', 'Manipal University Jaipur'],
  ['Department', 'Department of Computer Science and Engineering'],
  ['Course', 'Software Engineering Lab (CSE3132)'],
  ['Programme', 'B.Tech Computer Science and Engineering'],
  ['Duration', 'July–November 2026'],
  ['Project guide', 'To be filled'],
]

const TH = 'px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500'

export default function About() {
  return (
    <>
      <PageHeader
        eyebrow="Software Engineering Lab · CSE3132"
        title="About CodeSentry"
        subtitle="A hybrid source-code plagiarism detection system for programming assignments, combining token fingerprinting with structural comparison of abstract syntax trees."
      />

      <div className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-3">
          <Card title="Abstract" className="lg:col-span-2">
            <p className="text-sm leading-7 text-slate-700 sm:text-[15px]">
              Programming assignments are easy to copy and just as easy to disguise: renaming variables, reformatting the
              code, rewriting comments, reordering functions or turning a for loop into a while loop is enough to defeat
              plain text comparison. CodeSentry detects such plagiarism in Python and C submissions by examining every
              program from two complementary views. The token view normalizes source code into a stream of abstract
              symbols and selects k-gram fingerprints with the winnowing algorithm, measuring their overlap with Jaccard
              similarity. The structural view parses each submission into a canonical abstract syntax tree skeleton and
              compares skeletons using Zhang–Shasha tree edit distance and shared-subtree matching. The two scores are
              fused into one similarity score with configurable weights and a High, Moderate or Low verdict, and every
              flagged pair is backed by evidence: matched line regions shown side by side and a breakdown of each score.
              The approach is evaluated on a purpose-built dataset of original, obfuscated and independently written
              solutions against plain text matching and TF-IDF cosine baselines using precision, recall, F1 score and ROC
              AUC. The system is delivered as a Flask REST API with a React web interface that runs fully offline.
            </p>
          </Card>

          <Card title="Project details">
            <dl className="space-y-4 text-sm">
              {DETAILS.map(([term, value]) => (
                <div key={term}>
                  <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500">{term}</dt>
                  <dd className={`mt-1 ${term === 'Project guide' ? 'italic text-slate-500' : 'text-slate-800'}`}>{value}</dd>
                </div>
              ))}
            </dl>
          </Card>
        </div>

        <Card title="Objectives" subtitle="The seven objectives the project set out to achieve.">
          <ol className="grid gap-x-8 gap-y-5 md:grid-cols-2">
            {OBJECTIVES.map((objective, index) => (
              <li key={objective.title} className="flex gap-4">
                <span
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-sm font-semibold text-indigo-700 ring-1 ring-inset ring-indigo-600/20"
                  aria-hidden="true"
                >
                  {index + 1}
                </span>
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-slate-900">{objective.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{objective.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </Card>

        <div className="grid gap-6 xl:grid-cols-5">
          <Card title="Technology stack" className="xl:col-span-3" bodyClassName="p-0">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <caption className="sr-only">Technologies used in CodeSentry</caption>
                <thead className="bg-slate-50">
                  <tr>
                    <th scope="col" className={TH}>
                      Layer
                    </th>
                    <th scope="col" className={TH}>
                      Technology
                    </th>
                    <th scope="col" className={TH}>
                      Role
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {STACK.map((row) => (
                    <tr key={row.layer} className="align-top">
                      <th scope="row" className="whitespace-nowrap px-6 py-3 text-left font-medium text-slate-900">
                        {row.layer}
                      </th>
                      <td className="px-6 py-3 text-slate-700">{row.technology}</td>
                      <td className="px-6 py-3 text-slate-500">{row.role}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Team" className="xl:col-span-2" bodyClassName="p-0">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <caption className="sr-only">Project team members</caption>
                <thead className="bg-slate-50">
                  <tr>
                    <th scope="col" className={TH}>
                      Name
                    </th>
                    <th scope="col" className={TH}>
                      Registration no.
                    </th>
                    <th scope="col" className={TH}>
                      Programme
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {TEAM.map((member) => (
                    <tr key={member.registration}>
                      <th scope="row" className="whitespace-nowrap px-6 py-3 text-left font-medium text-slate-900">
                        {member.name}
                      </th>
                      <td className="whitespace-nowrap px-6 py-3 tabular-nums text-slate-700">{member.registration}</td>
                      <td className="whitespace-nowrap px-6 py-3 text-slate-700">{member.programme}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="space-y-1 border-t border-slate-200 px-6 py-4 text-sm">
              <p className="text-slate-700">
                <span className="font-medium text-slate-900">Project guide:</span>{' '}
                <span className="italic text-slate-500">to be filled</span>
              </p>
              <p className="text-slate-500">
                Department of CSE, Manipal University Jaipur · Software Engineering Lab (CSE3132) · July–November 2026
              </p>
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
