# CodeSentry web interface

React 19 single-page app (Vite 8, Tailwind CSS 4, Chart.js 4, React Router 7, axios) for the
CodeSentry plagiarism detector. It talks only to the Flask REST API under the relative path `/api`.

```bash
npm install          # once
npm run build        # production build -> dist/ (served by Flask: python run_server.py)
npm run dev          # development server on http://localhost:5173, proxies /api to 127.0.0.1:5000
```

`dist/` is committed so that the application runs from a fresh clone with only the Python
dependencies installed. Rebuild it after changing anything in `src/`.

| Folder | Contents |
|---|---|
| `src/pages/` | one component per route: Dashboard, NewAnalysis, RunResults, PairView, Evaluation, HowItWorks, About |
| `src/components/` | heat map, histogram, pairs table, side-by-side code panes, score breakdown, pipeline explainer, app layout |
| `src/components/ui/` | small shared building blocks (Card, Button, Badge, StatCard, ScoreBar, ...) |
| `src/api/client.js` | every API call in one place |
| `src/lib/` | number formatting and colour scales |

See the project [README](../README.md) for the whole system.
