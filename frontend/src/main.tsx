import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Log all failed fetch requests (dev only)
if (import.meta.env.DEV) {
  const originalFetch = window.fetch
  window.fetch = async (...args: Parameters<typeof fetch>) => {
    const response = await originalFetch(...args)
    if (!response.ok) {
      const url = typeof args[0] === 'string' ? args[0] : (args[0] as Request)?.url
      console.log(`FAILED: ${url} → ${response.status}`)
    }
    return response
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
