// App — the router. Every URL of the single-page application is declared here (contract section 8).
//
// BrowserRouter uses real paths such as /runs/3 instead of #/runs/3. That works because Flask
// answers any non-/api GET with index.html, letting React decide which page to show.
// All pages are nested inside <Layout>, so the sidebar stays mounted while only the page changes.
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Button from './components/ui/Button.jsx'
import EmptyState from './components/ui/EmptyState.jsx'
import PageHeader from './components/ui/PageHeader.jsx'
import About from './pages/About.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Evaluation from './pages/Evaluation.jsx'
import HowItWorks from './pages/HowItWorks.jsx'
import NewAnalysis from './pages/NewAnalysis.jsx'
import PairView from './pages/PairView.jsx'
import RunResults from './pages/RunResults.jsx'
import Training from './pages/Training.jsx'

/** Shown for any URL that matches no route, instead of a blank screen. */
function NotFound() {
  return (
    <>
      <PageHeader title="Page not found" subtitle="The address you opened does not match any page in CodeSentry." />
      <EmptyState
        title="Nothing here"
        description="The link may be mistyped, or the analysis run it pointed to may have been deleted."
        action={<Button to="/">Go to Dashboard</Button>}
      />
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="new" element={<NewAnalysis />} />
          <Route path="runs/:runId" element={<RunResults />} />
          <Route path="runs/:runId/pairs/:aId/:bId" element={<PairView />} />
          <Route path="evaluation" element={<Evaluation />} />
          <Route path="training" element={<Training />} />
          <Route path="how-it-works" element={<HowItWorks />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
