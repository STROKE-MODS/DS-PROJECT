import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, friendlyError } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function ResumeUploadPage() {
  const { student } = useAuth()
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)
  const navigate = useNavigate()

  function selectFile(event) {
    const next = event.target.files?.[0]
    setError('')
    if (next && next.type !== 'application/pdf' && !next.name.toLowerCase().endsWith('.pdf')) {
      setFile(null)
      setError('Please choose a PDF file. We only support PDF resumes for now.')
      return
    }
    setFile(next || null)
  }

  async function upload(event) {
    event.preventDefault()
    if (!file) { setError('Choose your PDF resume before uploading.'); return }
    setLoading(true); setError('')
    try {
      const result = await api.uploadResume(student.id, file)
      navigate('/resume/confirm', { state: { draft: result.draft_profile, preview: result.resume_text_preview, method: result.extraction_method } })
    } catch (requestError) {
      setError(friendlyError(requestError, 'We could not process that resume. Please try another PDF.'))
    } finally { setLoading(false) }
  }

  return (
    <div className="narrow-page">
      <Link className="back-link" to="/profile">← Back to profile</Link>
      <section className="upload-hero"><p className="eyebrow">Profile upgrade</p><h1>Bring your experience with you.</h1><p>Upload your resume and we’ll turn it into a draft profile. You stay in control of what gets saved.</p></section>
      <form className="panel upload-card" onSubmit={upload}>
        <div className="upload-icon">↑</div>
        <h2>Drop your resume here</h2>
        <p>PDF only · We’ll extract skills, education, projects, and certificates.</p>
        <input ref={inputRef} className="sr-only" type="file" accept="application/pdf,.pdf" onChange={selectFile} />
        <button type="button" className="button button-outline" onClick={() => inputRef.current?.click()}>Choose PDF</button>
        {file && <div className="selected-file"><span>PDF</span><div><strong>{file.name}</strong><small>{(file.size / 1024 / 1024).toFixed(2)} MB</small></div><button type="button" aria-label="Remove selected file" onClick={() => { setFile(null); inputRef.current.value = '' }}>×</button></div>}
        {error && <div className="form-alert" role="alert">{error}</div>}
        <button className="button button-primary button-full" disabled={loading}>{loading ? 'Reading your resume…' : 'Upload and extract'} <span aria-hidden="true">↗</span></button>
        {loading && <p className="loading-note">This can take a few seconds while InternAI reads your experience.</p>}
      </form>
      <p className="privacy-note centered">Your resume is used to build your InternAI profile. You’ll review every extracted detail before saving.</p>
    </div>
  )
}
