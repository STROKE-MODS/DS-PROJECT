const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : 'Something went wrong. Please try again.'
    throw new ApiError(detail, response.status)
  }
  return data
}

export async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (options.body && !(options.body instanceof FormData)) headers['Content-Type'] = 'application/json'
  const response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers })
  return parseResponse(response)
}

export const api = {
  health: () => apiFetch('/api/health'),
  login: (email) => apiFetch('/api/auth/login', { method: 'POST', body: JSON.stringify({ email }) }),
  signup: (profile) => apiFetch('/api/students', { method: 'POST', body: JSON.stringify(profile) }),
  updateProfile: (studentId, profile) => apiFetch(`/api/students/${studentId}`, { method: 'PATCH', body: JSON.stringify(profile) }),
  updateCareerGoal: (studentId, careerGoalId) => apiFetch(`/api/students/${studentId}/career-goal`, { method: 'PATCH', body: JSON.stringify({ career_goal_id: careerGoalId }) }),
  careerPaths: () => apiFetch('/api/career-paths'),
  uploadResume: (studentId, file) => {
    const body = new FormData()
    body.append('file', file)
    return apiFetch(`/api/students/${studentId}/resume/upload`, { method: 'POST', body })
  },
  confirmResume: (studentId, draft) => apiFetch(`/api/students/${studentId}/resume/confirm`, { method: 'POST', body: JSON.stringify(draft) }),
}

export function friendlyError(error, fallback = 'Something went wrong. Please try again.') {
  if (error?.status === 404) return 'No account found with this email — try signing up instead.'
  if (error?.status === 409) return 'An account with this email already exists — try logging in instead.'
  if (error?.message?.toLowerCase().includes('pdf')) return 'Please choose a valid PDF resume and try again.'
  return error?.message || fallback
}
