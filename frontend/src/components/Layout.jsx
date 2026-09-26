import { Link, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute() {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  return isAuthenticated ? <Outlet /> : <Navigate to="/auth" replace state={{ from: location.pathname }} />
}

export default function Layout() {
  const { student, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <div className="app-frame">
      <header className="site-nav">
        <Link className="brand" to="/profile" aria-label="InternAI profile">
          <span className="brand-mark">I</span>
          <span>Intern<span className="brand-accent">AI</span></span>
        </Link>
        <div className="nav-actions">
          <Link className="nav-link" to="/profile">Profile</Link>
          <span className="nav-user">{student?.name}</span>
          <button className="button button-ghost button-small" onClick={handleLogout}>Log out</button>
        </div>
      </header>
      <main className="page-shell"><Outlet /></main>
    </div>
  )
}
