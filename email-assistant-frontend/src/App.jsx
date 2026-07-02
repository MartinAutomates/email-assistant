import { useState, useEffect } from 'react'
import './App.css'

const API = 'http://127.0.0.1:8000'

function connectGmail(token) {
  window.location.href = `${API}/auth/google/login?token=${encodeURIComponent(token)}`
}

function CategoryBadge({ category }) {
  const cat = category || 'none'
  return (
    <span className={`badge cat-${cat}`}>
      {category || 'unclassified'}
    </span>
  )
}

function ComposeForm({ token }) {
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)

  async function classify() {
    if (!subject.trim() || !body.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch(`${API}/classify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ subject, body })
      })
      const data = await res.json()
      setResult(data.category)
    } catch (e) {
      setResult('error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="compose-card">
      <div className="compose-toggle" onClick={() => setOpen(o => !o)}>
        <span>✍️ Classify any email</span>
        <span>{open ? '▲' : '▼'}</span>
      </div>

      {open && (
        <>
          <div className="form-group" style={{ marginTop: '16px' }}>
            <label>Subject</label>
            <input
              type="text"
              value={subject}
              onChange={e => setSubject(e.target.value)}
              placeholder="Email subject..."
            />
          </div>
          <div className="form-group">
            <label>Body</label>
            <textarea
              value={body}
              onChange={e => setBody(e.target.value)}
              placeholder="Paste email body here..."
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={classify}
            disabled={loading || !subject.trim() || !body.trim()}
          >
            {loading ? 'Classifying...' : 'Classify with AI ✨'}
          </button>

          {result && (
            <div className="classify-result">
              <span>Result:</span>
              <CategoryBadge category={result === 'error' ? null : result} />
              {result === 'error' && (
                <span style={{ color: '#dc2626' }}>Classification failed</span>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function EmailCard({ email, token, onReclassify }) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState(null)
  const [summarizing, setSummarizing] = useState(false)
  const [reply, setReply] = useState(null)
  const [replying, setReplying] = useState(false)
  const [tone, setTone] = useState('professional')

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

  async function summarize() {
    setSummarizing(true)
    setSummary(null)
    try {
      const res = await fetch(`${API}/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          subject: email.subject,
          body: email.body || email.subject,
          max_sentences: 3
        })
      })
      const data = await res.json()
      setSummary(data.summary)
    } catch (e) {
      setSummary('Failed to summarize.')
    } finally {
      setSummarizing(false)
    }
  }

  async function suggestReply() {
    setReplying(true)
    setReply(null)
    try {
      const res = await fetch(`${API}/suggest-reply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          subject: email.subject,
          body: email.body || email.subject,
          tone
        })
      })
      const data = await res.json()
      setReply(data.suggested_reply)
    } catch (e) {
      setReply('Failed to generate reply.')
    } finally {
      setReplying(false)
    }
  }

  return (
    <div className="email-card">
      <div className="email-header">
        <div className="email-subject" onClick={() => setOpen(o => !o)}>
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
        <div className="email-detail">
          <div className="email-body">
            {(email.body || '').substring(0, 1000)}
            {email.body && email.body.length > 1000 ? '\n...(truncated)' : ''}
          </div>

          <div className="detail-actions">
            <button
              className="btn btn-sm"
              onClick={summarize}
              disabled={summarizing}
            >
              {summarizing ? 'Summarizing...' : '📝 Summarize'}
            </button>

            <select
              className="tone-select"
              value={tone}
              onChange={e => setTone(e.target.value)}
            >
              <option value="professional">Professional</option>
              <option value="friendly">Friendly</option>
              <option value="brief">Brief</option>
            </select>
            <button
              className="btn btn-sm"
              onClick={suggestReply}
              disabled={replying}
            >
              {replying ? 'Drafting...' : '💬 Suggest Reply'}
            </button>
          </div>

          {summary && (
            <div className="ai-result">
              <div className="ai-result-label">📝 Summary</div>
              <div className="ai-result-text">{summary}</div>
            </div>
          )}

          {reply && (
            <div className="ai-result">
              <div className="ai-result-label">
                💬 Suggested Reply ({tone})
                  <button
                    className="btn btn-sm copy-btn"
                    onClick={() => navigator.clipboard.writeText(reply)}
                  >
                📋 Copy
                  </button>
              </div>
             <div className="ai-result-text">{reply}</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

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

function EmailList({ token, onLogout }) {
  const [emails, setEmails] = useState([])
  const [status, setStatus] = useState('Loading...')
  const [syncing, setSyncing] = useState(false)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    loadEmails()
  }, [])

async function loadEmails() {
    setStatus('Loading...')
    try {
      const res = await fetch(`${API}/emails?limit=50`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.status === 401) {
        onLogout()
        return
      }

      if (!res.ok) {
        setStatus('Failed to load.')
        return
      }

      const data = await res.json()
      setEmails(data.emails || [])
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

      if (res.status === 401) {
        onLogout()
        return
      }

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

  const visible = filter === 'all'
    ? emails
    : emails.filter(e => (e.category || 'none') === filter)

  return (
    <div>
      <header className="app-header">
          <h1>📧 Email Assistant</h1>
          <div className="header-actions">
              <button
                  className="btn"
                  onClick={() => connectGmail(token)}
              >
                  🔗 Connect Gmail
              </button>
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
        <ComposeForm token={token} />

        <div className="toolbar">
          <button className="btn btn-sm btn-primary" onClick={loadEmails}>
            ↻ Refresh
          </button>
          <select
            className="filter-select"
            value={filter}
            onChange={e => setFilter(e.target.value)}
          >
            <option value="all">All</option>
            <option value="urgent">Urgent</option>
            <option value="work">Work</option>
            <option value="newsletter">Newsletter</option>
            <option value="spam">Spam</option>
            <option value="other">Other</option>
            <option value="none">Unclassified</option>
          </select>
          <span className="status">{status}</span>
        </div>

        {visible.length === 0 && status !== 'Loading...' ? (
          <div className="empty-state">
            {filter === 'all'
              ? 'No emails yet. Click "Sync Gmail" to import your inbox.'
              : `No emails with category "${filter}".`
            }
          </div>
        ) : (
          visible.map(email => (
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

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'))

  function handleLogin(newToken) {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }

  function handleLogout() {
    localStorage.removeItem('token')
    setToken(null)
  }

  if (!token) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return <EmailList token={token} onLogout={handleLogout} />
}