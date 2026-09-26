import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { api, friendlyError } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function AuthPage() {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { setStudent } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
    setError('')
  }

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const student = mode === 'login' ? await api.login(form.email) : await api.signup({ name: form.name, email: form.email })
      setStudent(student)
      navigate(location.state?.from || '/profile', { replace: true })
    } catch (requestError) {
      setError(friendlyError(requestError))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <Link className="brand auth-brand" to="/">
        <span className="brand-mark">I</span>
        <span>Intern<span className="brand-accent">AI</span></span>
      </Link>
      <section className="auth-card">
        <div className="auth-intro">
          <p className="eyebrow">A small step forward</p>
          <h1>Let’s make your next move count.</h1>
          <p>Use your email to pick up where you left off, or create a profile in under a minute.</p>
        </div>
        <div className="auth-tabs" role="tablist">
          <button className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setError('') }}>I have an account</button>
          <button className={mode === 'signup' ? 'active' : ''} onClick={() => { setMode('signup'); setError('') }}>I’m new here</button>
        </div>
        <form onSubmit={submit} className="form-stack">
          {mode === 'signup' && <label>Name<input autoComplete="name" value={form.name} onChange={(event) => update('name', event.target.value)} placeholder="e.g. Aisha Khan" required /></label>}
          <label>Email address<input autoComplete="email" type="email" value={form.email} onChange={(event) => update('email', event.target.value)} placeholder="you@example.com" required /></label>
          {error && <div className="form-alert" role="alert">{error}</div>}
          <button className="button button-primary button-full" disabled={loading}>{loading ? 'One moment…' : mode === 'login' ? 'Continue with email' : 'Create my profile'} <span aria-hidden="true">↗</span></button>
        </form>
        <p className="privacy-note">No passwords, no noise. Your email is only used to find your profile.</p>
      </section>
    </main>
  )
}
