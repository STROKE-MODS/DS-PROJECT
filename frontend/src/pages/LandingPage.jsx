import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

export default function LandingPage() {
  const [connected, setConnected] = useState(null)

  useEffect(() => {
    api.health().then((data) => setConnected(data.status === 'ok')).catch(() => setConnected(false))
  }, [])

  return (
    <main className="landing-page">
      <nav className="landing-nav">
        <Link className="brand" to="/">
          <span className="brand-mark">I</span>
          <span>Intern<span className="brand-accent">AI</span></span>
        </Link>
        <Link className="button button-ghost" to="/auth">Sign in</Link>
      </nav>
      <section className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">Your next step, made clearer</p>
          <h1>Find internships that fit <em>your future.</em></h1>
          <p className="hero-description">InternAI connects your skills, goals, and potential to opportunities worth pursuing — with a clear plan to help you get there.</p>
          <div className="hero-actions">
            <Link className="button button-primary button-large" to="/auth">Get started <span aria-hidden="true">↗</span></Link>
            <span className="hero-note">No password. Just your email.</span>
          </div>
        </div>
        <div className="hero-visual" aria-label="InternAI career path preview">
          <div className="visual-glow" />
          <div className="opportunity-card">
            <div className="card-topline"><span className="status-dot" /> Personalised for you</div>
            <div className="opportunity-icon">✦</div>
            <p className="opportunity-label">Your next opportunity</p>
            <h2>Data Science Intern</h2>
            <p className="opportunity-company">with Northstar Labs</p>
            <div className="match-row"><span>Match strength</span><strong>92%</strong></div>
            <div className="match-bar"><span /></div>
            <div className="tag-row"><span>Python</span><span>Machine learning</span><span>Remote</span></div>
          </div>
          <div className="floating-note note-top"><span>↗</span><div><strong>Build with confidence</strong><small>Know what to learn next</small></div></div>
          <div className="floating-note note-bottom"><span>✓</span><div><strong>Goals, aligned</strong><small>Recommendations that grow with you</small></div></div>
        </div>
      </section>
      <footer className="landing-footer">
        <span>Made for students who are ready for what’s next.</span>
        <span className={`health-badge ${connected === true ? 'health-good' : connected === false ? 'health-bad' : ''}`}><i /> {connected === true ? 'Backend connected' : connected === false ? 'Backend unavailable' : 'Checking connection'}</span>
      </footer>
    </main>
  )
}
