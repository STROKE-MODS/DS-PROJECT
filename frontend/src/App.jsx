import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout, { ProtectedRoute } from './components/Layout'
import { AuthProvider } from './context/AuthContext'
import AuthPage from './pages/AuthPage'
import LandingPage from './pages/LandingPage'
import ProfilePage from './pages/ProfilePage'
import ResumeConfirmPage from './pages/ResumeConfirmPage'
import ResumeUploadPage from './pages/ResumeUploadPage'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/resume" element={<ResumeUploadPage />} />
              <Route path="/resume/confirm" element={<ResumeConfirmPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
