// HTTP client for the CodeSentry Flask API (contract section 7).
//
// Every page talks to the backend only through these functions, so URLs live in one place and
// each call returns the parsed JSON body (response.data) rather than the raw axios response.
// The base URL is the relative path "/api": in production Flask serves the SPA and the API from
// the same origin, and in development vite.config.js proxies /api to http://127.0.0.1:5000.
import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  headers: { Accept: 'application/json' },
})

/** GET /api/health -> {status, version, languages} */
export async function getHealth() {
  const response = await api.get('/health')
  return response.data
}

/** GET /api/config/defaults -> EngineConfig as a plain object */
export async function getDefaults() {
  const response = await api.get('/config/defaults')
  return response.data
}

/** GET /api/runs -> RunSummary[] (newest first) */
export async function listRuns() {
  const response = await api.get('/runs')
  return response.data
}

/** GET /api/runs/:id -> RunSummary fields + files, matrix, pairs, config */
export async function getRun(id) {
  const response = await api.get(`/runs/${encodeURIComponent(id)}`)
  return response.data
}

/** GET /api/runs/:runId/pairs/:aId/:bId -> PairResult + a_source, b_source */
export async function getPair(runId, aId, bId) {
  const path = [runId, 'pairs', aId, bId].map((part) => encodeURIComponent(part)).join('/')
  const response = await api.get(`/runs/${path}`)
  return response.data
}

/**
 * POST /api/runs (multipart) -> RunSummary.
 * `formData` carries repeated "files" entries plus optional name, k, w, w_token, w_structure.
 * The Content-Type header is deliberately not set: the browser must add the multipart boundary.
 * `onUploadProgress` receives axios progress events ({loaded, total}) for an upload bar.
 */
export async function createRun(formData, onUploadProgress) {
  const response = await api.post('/runs', formData, { onUploadProgress })
  return response.data
}

/** POST /api/runs/demo -> RunSummary of the bundled demo class batch */
export async function createDemoRun() {
  const response = await api.post('/runs/demo')
  return response.data
}

/** DELETE /api/runs/:id -> no content (resolves to an empty value) */
export async function deleteRun(id) {
  const response = await api.delete(`/runs/${encodeURIComponent(id)}`)
  return response.data
}

/** POST /api/explain -> step-by-step explanation of how two snippets are compared */
export async function explain({ code_a, code_b, language }) {
  const response = await api.post('/explain', { code_a, code_b, language })
  return response.data
}

/** GET /api/evaluation -> contents of evaluation/results/evaluation.json */
export async function getEvaluation() {
  const response = await api.get('/evaluation')
  return response.data
}

/**
 * Turns any failure from the functions above into one sentence a user can read.
 * The backend reports every error as JSON {"error": "..."}, so that message is preferred; the
 * fallbacks cover cases where no JSON body exists (server down, proxy failure, cancelled call).
 */
export function errorMessage(err, fallback = 'Something went wrong. Please try again.') {
  if (axios.isCancel(err)) {
    return 'The request was cancelled.'
  }

  const response = err?.response
  if (response) {
    const body = response.data
    if (body && typeof body === 'object' && typeof body.error === 'string' && body.error.trim()) {
      return body.error
    }
    if (response.status === 404) return 'The requested item was not found.'
    if (response.status === 413) return 'The upload is too large for the server to accept.'
    if (response.status >= 500) {
      return `The server could not complete the request (HTTP ${response.status}). Check that the backend is running.`
    }
    return `The request failed (HTTP ${response.status}).`
  }

  // A request that was sent but never answered means the backend is unreachable.
  if (err?.request) {
    return 'Cannot reach the CodeSentry server. Start it with "python run_server.py" and try again.'
  }

  if (typeof err === 'string' && err) return err
  if (err instanceof Error && err.message) return err.message
  return fallback
}
