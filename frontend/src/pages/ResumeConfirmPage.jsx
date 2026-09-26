import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { api, friendlyError } from '../api/client'
import { useAuth } from '../context/AuthContext'

const emptyProject = { title: '', description: '' }
const emptyCertificate = { name: '', issuing_organization: '' }

export default function ResumeConfirmPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { student, setStudent } = useAuth()
  const incoming = location.state?.draft
  const [draft, setDraft] = useState(() => incoming || { skills: [], education: {}, projects: [], certificates: [] })
  const [skillInput, setSkillInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  if (!incoming && !location.state?.draft) {
    return <div className="narrow-page empty-state"><h1>No draft to review</h1><p>Upload a resume first and we’ll bring the extracted details here.</p><Link className="button button-primary" to="/resume">Upload resume</Link></div>
  }

  function updateEducation(field, value) {
    setDraft((current) => ({ ...current, education: { ...current.education, [field]: value } }))
  }
  function updateList(key, index, field, value) {
    setDraft((current) => ({ ...current, [key]: current[key].map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item) }))
  }
  function addSkill(event) {
    event.preventDefault()
    const skill = skillInput.trim()
    if (!skill || draft.skills.some((item) => item.toLowerCase() === skill.toLowerCase())) return
    setDraft((current) => ({ ...current, skills: [...current.skills, skill] }))
    setSkillInput('')
  }
  function removeSkill(skill) {
    setDraft((current) => ({ ...current, skills: current.skills.filter((item) => item !== skill) }))
  }
  function removeItem(key, index) {
    setDraft((current) => ({ ...current, [key]: current[key].filter((_, itemIndex) => itemIndex !== index) }))
  }

  async function confirm() {
    setSaving(true); setError('')
    try {
      const result = await api.confirmResume(student.id, draft)
      setStudent(result.student)
      navigate('/profile', { replace: true, state: { notice: 'Your reviewed resume details are now part of your profile.' } })
    } catch (requestError) {
      setError(friendlyError(requestError, 'We could not save your reviewed profile.'))
    } finally { setSaving(false) }
  }

  return (
    <div className="confirm-page">
      <div className="page-heading"><div><Link className="back-link" to="/resume">← Upload a different resume</Link><p className="eyebrow">Review before saving</p><h1>Here’s what we found.</h1><p>AI extraction is a helpful first pass, not a final answer. Please review and correct anything that doesn’t look right.</p></div><button className="button button-primary" onClick={confirm} disabled={saving}>{saving ? 'Saving profile…' : 'Confirm and save'} <span aria-hidden="true">✓</span></button></div>
      {error && <div className="page-alert error" role="alert">{error}</div>}
      <div className="confirm-grid">
        <section className="panel review-panel"><div className="panel-heading"><div><span className="section-number">01</span><h2>Skills</h2></div><span className="muted-copy">{draft.skills.length} detected</span></div><div className="chip-list editable-chips">{draft.skills.map((skill) => <span className="chip" key={skill}>{skill}<button type="button" onClick={() => removeSkill(skill)} aria-label={`Remove ${skill}`}>×</button></span>)}</div><form className="inline-add" onSubmit={addSkill}><input value={skillInput} onChange={(e) => setSkillInput(e.target.value)} placeholder="Add a skill the resume missed" /><button className="button button-outline button-small">+ Add</button></form></section>
        <section className="panel review-panel"><div className="panel-heading"><div><span className="section-number">02</span><h2>Education</h2></div></div><div className="form-grid"><label>Degree<input value={draft.education.degree || ''} onChange={(e) => updateEducation('degree', e.target.value)} placeholder="e.g. B.Tech" /></label><label>Institution<input value={draft.education.institution || ''} onChange={(e) => updateEducation('institution', e.target.value)} placeholder="e.g. University name" /></label><label>Field<input value={draft.education.field || ''} onChange={(e) => updateEducation('field', e.target.value)} placeholder="e.g. Computer Science" /></label><label>Year of study<input type="number" min="1" max="10" value={draft.education.year_of_study || ''} onChange={(e) => updateEducation('year_of_study', e.target.value === '' ? null : Number(e.target.value))} placeholder="3" /></label></div></section>
        <section className="panel review-panel"><div className="panel-heading"><div><span className="section-number">03</span><h2>Projects</h2></div><button className="text-button" type="button" onClick={() => setDraft((current) => ({ ...current, projects: [...current.projects, { ...emptyProject }] }))}>+ Add project</button></div>{draft.projects.length === 0 && <p className="empty-copy">No projects were detected. Add one if you’d like it included.</p>}{draft.projects.map((project, index) => <div className="repeat-item" key={`project-${index}`}><div className="repeat-title"><span>Project {index + 1}</span><button type="button" className="remove-button" onClick={() => removeItem('projects', index)}>Remove</button></div><label>Title<input value={project.title} onChange={(e) => updateList('projects', index, 'title', e.target.value)} /></label><label>Description<textarea value={project.description} onChange={(e) => updateList('projects', index, 'description', e.target.value)} rows="3" /></label></div>)}</section>
        <section className="panel review-panel"><div className="panel-heading"><div><span className="section-number">04</span><h2>Certificates</h2></div><button className="text-button" type="button" onClick={() => setDraft((current) => ({ ...current, certificates: [...current.certificates, { ...emptyCertificate }] }))}>+ Add certificate</button></div>{draft.certificates.length === 0 && <p className="empty-copy">No certificates were detected. Add one if you’d like it included.</p>}{draft.certificates.map((certificate, index) => <div className="repeat-item" key={`certificate-${index}`}><div className="repeat-title"><span>Certificate {index + 1}</span><button type="button" className="remove-button" onClick={() => removeItem('certificates', index)}>Remove</button></div><label>Name<input value={certificate.name} onChange={(e) => updateList('certificates', index, 'name', e.target.value)} /></label><label>Issuing organization<input value={certificate.issuing_organization || ''} onChange={(e) => updateList('certificates', index, 'issuing_organization', e.target.value)} /></label></div>)}</section>
      </div>
      <div className="mobile-save"><button className="button button-primary button-full" onClick={confirm} disabled={saving}>{saving ? 'Saving profile…' : 'Confirm and save'}</button></div>
    </div>
  )
}
