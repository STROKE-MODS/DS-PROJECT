import { createContext, useContext, useMemo, useState } from 'react'

const STORAGE_KEY = 'internai_student'
const AuthContext = createContext(null)

function readStudent() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [student, setStudentState] = useState(readStudent)

  const value = useMemo(() => ({
    student,
    isAuthenticated: Boolean(student?.id),
    setStudent(nextStudent) {
      setStudentState(nextStudent)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextStudent))
    },
    logout() {
      setStudentState(null)
      localStorage.removeItem(STORAGE_KEY)
    },
  }), [student])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
