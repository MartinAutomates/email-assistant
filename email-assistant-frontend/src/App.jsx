import { useState, useEffect } from 'react'
import './App.css'

const API = 'http://127.0.0.1:8000'

// ── Small reusable components ──────────────────────────────────────

function CategoryBadge({ category }) {
  const cat = category || 'none'
  return (
    <span className={`badge cat-${cat}`}>
      {category || 'unclassified'}
    </span>
  )
}

function EmailCard({ email, token, onReclassify }) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  async function classify() {
    setLoading(true)
    try {
      const res = await fetch(`${API}/classify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          subject: email.subject,
          body: email.body || email.subject
        })
      })
      const data = await res.json()
      onReclassify(email.email_id, data.category)
    } catch (e) {
      console.error('Classify failed', e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="email-card">
      <div className="email-header">
        <div
          className="email-subject"
          onClick={() => setOpen(o => !o)}
        >
          {email.subject}
        </div>
        <div className="email-actions">
          <CategoryBadge category={email.category} />
          <button
            className="btn btn-sm"
            onClick={classify}
            disabled={loading}
          >
            {loading ? '...' : 'AI ✨'}
          </button>
        </div>
      </div>
      {open && (
        <div className="email-body">
          {(email.body || '').substring(0, 1000)}
          {email.body && email.body.length > 1000 ? '\n...(truncated)' : ''}
        </div>
      )}
    </div>
  )
}

// ── Login Screen ───────────────────────────────────────────────────

function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState('martin@example.com')
  const [password, setPassword] = useState('supersecret123')
  const [error, setError] = useState('')

  async function handleLogin() {
    setError('')
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)

    try {
      const res = await fetch(`${API}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form
      })
      if (!res.ok) { setError('Invalid email or password.'); return }
      const data = await res.json()
      onLogin(data.access_token)
    } catch (e) {
      setError('Connection failed. Is the server running?')
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <h2>📧 Email Assistant</h2>
        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleLogin()}
          />
        </div>
        {error && <div className="error">{error}</div>}
        <button className="btn btn-primary btn-full" onClick={handleLogin}>
          Sign in
        </button>
      </div>
    </div>
  )
}

// ── Main App ───────────────────────────────────────────────────────

function EmailList({ token, onLogout }) {
  const [emails, setEmails] = useState([])
  const [status, setStatus] = useState('Loading...')
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    loadEmails()
  }, [])

  async function loadEmails() {
    setStatus('Loading...')
    try {
      const res = await fetch(`${API}/emails?limit=50`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      setEmails(data.emails)
      setStatus(`${data.count} email${data.count !== 1 ? 's' : ''}`)
    } catch (e) {
      setStatus('Failed to load.')
    }
  }

  async function syncGmail() {
    setSyncing(true)
    setStatus('Syncing Gmail...')
    try {
      const res = await fetch(`${API}/sync-gmail?max_emails=20`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      setStatus(`Synced ${data.synced} new, skipped ${data.skipped}`)
      if (data.synced > 0) loadEmails()
    } catch (e) {
      setStatus('Sync failed.')
    } finally {
      setSyncing(false)
    }
  }

  function handleReclassify(emailId, newCategory) {
    setEmails(prev =>
      prev.map(e =>
        e.email_id === emailId ? { ...e, category: newCategory } : e
      )
    )
  }

  return (
    <div>
      <header className="app-header">
        <h1>📧 Email Assistant</h1>
        <div className="header-actions">
          <button
            className="btn"
            onClick={syncGmail}
            disabled={syncing}
          >
            {syncing ? 'Syncing...' : '🔄 Sync Gmail'}
          </button>
          <button className="btn btn-sm" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="app-main">
        <div className="toolbar">
          <button className="btn btn-sm btn-primary" onClick={loadEmails}>
            ↻ Refresh
          </button>
          <span className="status">{status}</span>
        </div>

        {emails.length === 0 && status !== 'Loading...' ? (
          <div className="empty-state">
            No emails yet. Click "Sync Gmail" to import your inbox.
          </div>
        ) : (
          emails.map(email => (
            <EmailCard
              key={email.email_id}
              email={email}
              token={token}
              onReclassify={handleReclassify}
            />
          ))
        )}
      </main>
    </div>
  )
}

// ── Root ───────────────────────────────────────────────────────────

export default function App() {
  const [token, setToken] = useState(null)

  function handleLogout() {
    setToken(null)
  }

  if (!token) {
    return <LoginScreen onLogin={setToken} />
  }

  return <EmailList token={token} onLogout={handleLogout} />
}