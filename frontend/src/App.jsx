import { useEffect, useState } from 'react'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [connected, setConnected] = useState(null)

  useEffect(() => {
    fetch(`${apiBaseUrl}/api/health`)
      .then((response) => {
        if (!response.ok) throw new Error('Backend request failed')
        return response.json()
      })
      .then((data) => setConnected(data.status === 'ok'))
      .catch(() => setConnected(false))
  }, [])

  const statusLabel = connected === null
    ? 'Checking backend…'
    : connected
      ? 'Backend Connected'
      : 'Backend Disconnected'

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-16 text-white">
      <div className="mx-auto flex min-h-[70vh] max-w-3xl flex-col items-center justify-center text-center">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.3em] text-cyan-400">InternAI</p>
        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">Find the internship that fits your future.</h1>
        <p className="mt-6 max-w-xl text-lg text-slate-300">An AI-powered internship recommendation engine for students.</p>
        <div className={`mt-10 rounded-full border px-5 py-2 text-sm font-medium ${connected === true ? 'border-emerald-400/40 bg-emerald-400/10 text-emerald-300' : connected === false ? 'border-red-400/40 bg-red-400/10 text-red-300' : 'border-slate-400/40 bg-slate-400/10 text-slate-300'}`}>
          {statusLabel}
        </div>
      </div>
    </main>
  )
}

export default App
