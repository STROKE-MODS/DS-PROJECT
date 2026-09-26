import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { api, friendlyError } from '../api/client'
import { useAuth } from '../context/AuthContext'

const editableFields = ['education_level', 'degree', 'branch', 'year_of_study', 'location']

export default function ProfilePage() {
  const { student, setStudent } = useAuth()
  const location = useLocation()
  const [form, setForm] = useState(() => Object.fromEntries(editableFields.map((field) => [field, student?.[field] ?? ''])))
  const [paths, setPaths] = useState([])
  const [goal, setGoal] = useState(student?.career_goal_id ?? '')
  const [saving, setSaving] = useState(false)
  const [goalSaving, setGoalSaving] = useState(false)
  const [notice, setNotice] = useState(location.state?.notice || '')
  const [error, setError] = useState('')

  useEffect(() => {
    api.careerPaths().then(setPaths).catch(() => setError('Career paths could not be loaded right now.'))
  }, [])

  useEffect(() => {
    setForm(Object.fromEntries(editableFields.map((field) => [field, student?.[field] ?? ''])))
    setGoal(student?.career_goal_id ?? '')
  }, [student])

  const careerGoalName = paths.find((path) => path.id === student?.career_goal_id)?.name || 'Not set yet'

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
    setNotice('')
    setError('')
  }

  async function saveProfile(event) {
    event.preventDefault()
    setSaving(true); setNotice(''); setError('')
    try {
      const updated = await api.updateProfile(student.id, { ...form, year_of_study: form.year_of_study === '' ? null : Number(form.year_of_study) })
      setStudent(updated)
      setNotice('Profile details saved.')
    } catch (requestError) {
      setError(friendlyError(requestError, 'We could not save those details.'))
    } finally { setSaving(false) }
  }

  async function saveGoal(event) {
    const value = event.target.value
    setGoal(value)
    setGoalSaving(true); setNotice(''); setError('')
    try {
      const updated = await api.updateCareerGoal(student.id, value === '' ? null : Number(value))
      setStudent({ ...student, ...updated })
      setNotice('Career direction updated.')
    } catch (requestError) {
      setError(friendlyError(requestError, 'We could not update your career direction.'))
    } finally { setGoalSaving(false) }
  }

  return (
    <div className="profile-page">
      <div className="page-heading"><div><p className="eyebrow">Your workspace</p><h1>Welcome back, {student.name.split(' ')[0]}.</h1><p>Keep your profile current so InternAI can make better calls for your next step.</p></div><Link className="button button-primary" to="/resume">Upload resume <span aria-hidden="true">↗</span></Link></div>
      {(notice || error) && <div className={error ? 'page-alert error' : 'page-alert'} role="status">{error || notice}</div>}
      <div className="profile-grid">
        <section className="panel profile-main">
          <div className="panel-heading"><div><span className="section-number">01</span><h2>About you</h2></div><span className="editable-label">Editable</span></div>
          <form className="profile-form" onSubmit={saveProfile}>
            <div className="form-grid">
              <label>Education level<input value={form.education_level} onChange={(e) => update('education_level', e.target.value)} placeholder="Undergraduate" /></label>
              <label>Year of study<input type="number" min="1" max="10" value={form.year_of_study} onChange={(e) => update('year_of_study', e.target.value)} placeholder="3" /></label>
              <label>Degree<input value={form.degree} onChange={(e) => update('degree', e.target.value)} placeholder="B.Tech" /></label>
              <label>Field of study<input value={form.branch} onChange={(e) => update('branch', e.target.value)} placeholder="Computer Science" /></label>
              <label className="span-two">Location<input value={form.location} onChange={(e) => update('location', e.target.value)} placeholder="Bengaluru" /></label>
            </div>
            <button className="button button-dark" disabled={saving}>{saving ? 'Saving…' : 'Save profile details'}</button>
          </form>
        </section>
        <aside className="profile-side">
          <section className="panel identity-card"><div className="avatar">{student.name.slice(0, 1).toUpperCase()}</div><h2>{student.name}</h2><p>{student.email}</p><div className="identity-line"><span>Current direction</span><strong>{careerGoalName}</strong></div></section>
          <section className="panel goal-card"><div className="panel-heading"><div><span className="section-number">02</span><h2>Career direction</h2></div></div><p>Choose the path you want your recommendations to grow toward.</p><select value={goal} onChange={saveGoal} disabled={goalSaving}><option value="">Not set yet</option>{paths.map((path) => <option key={path.id} value={path.id}>{path.name}</option>)}</select>{goalSaving && <small className="saving-copy">Updating…</small>}</section>
        </aside>
      </div>
      <section className="panel profile-lower"><div className="panel-heading"><div><span className="section-number">03</span><h2>What you bring</h2></div><span className="muted-copy">From your confirmed profile</span></div><div className="profile-columns"><div><h3>Skills</h3><div className="chip-list">{student.skills?.length ? student.skills.map((skill) => <span className="chip" key={skill}>{skill}</span>) : <span className="empty-copy">Add a resume to surface your skills.</span>}</div></div><div><h3>Certificates</h3>{student.certificates?.length ? <ul className="simple-list">{student.certificates.map((certificate, index) => <li key={`${certificate.name}-${index}`}><strong>{certificate.name}</strong><small>{certificate.issuing_organization || 'Issuing organization not listed'}</small></li>)}</ul> : <span className="empty-copy">No certificates added yet.</span>}</div><div><h3>Projects</h3>{student.projects?.length ? <ul className="simple-list">{student.projects.map((project, index) => <li key={`${project.title}-${index}`}><strong>{project.title}</strong><small>{project.description}</small></li>)}</ul> : <span className="empty-copy">No projects added yet.</span>}</div></div></section>
    </div>
  )
}
