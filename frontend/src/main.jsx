// Entry point: mounts the React application into <div id="root"> from index.html.
// StrictMode double-invokes effects in development only, which surfaces missing cleanups early.
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
