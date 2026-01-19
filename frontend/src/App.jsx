import { useState, useEffect } from 'react';
import { supabase } from "./lib/supabase";

export default function App() {
  const [session, setSession] = useState(null)
  const [file, setFile] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [segregationResult, setSegregationResult] = useState(null)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
  }, [])

  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
    })
    if (error) console.error('Error logging in:', error.message)
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    setJobStatus(null)
    setFile(null)
    setSegregationResult(null)
  }

  const handleCreateJob = async () => {
    if (!session?.access_token) return
    setLoading(true)
    setJobStatus('Processing...')
    setSegregationResult(null)

    try {
      const formData = new FormData()
      formData.append('page_count_estimate', 1)
      if (file) {
        formData.append('file', file)
      } else {
        formData.append('content', "Test pasted text content")
      }

      const response = await fetch('http://localhost:8000/jobs/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        },
        body: formData
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(`Error: ${err.detail || response.statusText}`)
      }

      const data = await response.json()
      setJobStatus(`Job Created! ID: ${data.job_id}`)
      setSegregationResult(data.segregation)

    } catch (err) {
      setJobStatus(`Failed: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  if (!session) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column', gap: '20px' }}>
        <h1>swrite.ai</h1>
        <button onClick={handleGoogleLogin} style={{ padding: '10px 20px', fontSize: '16px' }}>
          Sign in with Google
        </button>
      </div>
    )
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
        <h1>swrite.ai Dashboard</h1>
        <button onClick={handleLogout}>Sign Out</button>
      </header>

      <main>
        <h3>Welcome, {session.user.email}</h3>

        <div style={{ marginTop: '20px', border: '1px solid #ccc', padding: '20px', borderRadius: '8px' }}>
          <h4>Segregator Test Zone</h4>
          <p>Select a file (PDF or Image) to test classification. If no file is selected, it sends text.</p>

          <div style={{ marginBottom: '15px' }}>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files[0])}
            />
          </div>

          <button
            onClick={handleCreateJob}
            disabled={loading}
            style={{ padding: '10px 20px', fontSize: '16px', backgroundColor: '#0070f3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            {loading ? 'Analyzing...' : 'Upload & Classify'}
          </button>

          {jobStatus && (
            <div style={{ marginTop: '20px', padding: '10px', background: '#f5f5f5', borderRadius: '4px', color: '#333' }}>
              <strong>Status:</strong> {jobStatus}
            </div>
          )}


        </div>
      </main>
    </div>
  )
}
