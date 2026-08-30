import { useEffect, useRef, useState } from 'react'
import './App.css'

const COLORS = ['#4f46e5', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2']

const STATUS_STYLES = {
  completed: { bg: '#d1fae5', color: '#065f46' },
  failed: { bg: '#fee2e2', color: '#991b1b' },
  pending: { bg: '#fef3c7', color: '#92400e' },
  processing: { bg: '#dbeafe', color: '#1e40af' },
  dead_letter: { bg: '#f3e8ff', color: '#6b21a8' },
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString()
  } catch {
    return '-'
  }
}

// --- Login Page ---

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Login failed')
      }
      const data = await res.json()
      localStorage.setItem('token', data.access_token)
      onLogin(data.access_token)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>Call Analyzer</h2>
        <p className="login-subtitle">Sign in to continue</p>
        {error && <div className="login-error">{error}</div>}
        <input
          className="login-input"
          type="text"
          placeholder="Username"
          value={username}
          onChange={e => setUsername(e.target.value)}
          autoFocus
          required
        />
        <input
          className="login-input"
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
        />
        <button className="login-btn" type="submit" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
    </div>
  )
}

// --- Dashboard Components ---

function Card({ title, value, subtitle, color }) {
  return (
    <div className="card" style={{ borderTopColor: color }}>
      <div className="card-value">{value}</div>
      <div className="card-title">{title}</div>
      {subtitle && <div className="card-subtitle">{subtitle}</div>}
    </div>
  )
}

function Bar({ label, count, total, color }) {
  const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0
  return (
    <div className="bar-row">
      <span className="bar-label">{label}</span>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="bar-count">{count} ({pct}%)</span>
    </div>
  )
}

function SortIcon({ sortKey, currentKey, direction }) {
  if (sortKey !== currentKey) return null
  return direction === 'asc' ? ' ▲' : ' ▼'
}

function buildInsightCards(insights) {
  if (!insights) return []
  const { total_calls, avg_confidence, category_counts, status_counts } = insights
  const categories = Object.keys(category_counts)
  const total = total_calls || 0
  return [
    { title: 'Total Transcripts', value: total, subtitle: 'all time', color: COLORS[0] },
    { title: 'Avg Confidence', value: avg_confidence ?? '-', subtitle: 'average score', color: COLORS[1] },
    { title: 'Categories', value: categories.length, subtitle: categories.join(', '), color: COLORS[2] },
    {
      title: 'Completion Rate',
      value: status_counts?.completed ? ((status_counts.completed / total) * 100).toFixed(1) + '%' : '0%',
      subtitle: `${total - (status_counts?.completed || 0)} not completed`,
      color: COLORS[3],
    },
  ]
}

function Pagination({ pagination, onPageChange }) {
  if (!pagination || pagination.total_pages <= 1) return null
  const { page, total_pages, has_prev, has_next, total } = pagination

  const pages = []
  const start = Math.max(1, page - 2)
  const end = Math.min(total_pages, page + 2)
  for (let i = start; i <= end; i++) pages.push(i)

  return (
    <div className="pagination">
      <span className="pagination-info">Page {page} of {total_pages} ({total} total)</span>
      <div className="pagination-controls">
        <button disabled={!has_prev} onClick={() => onPageChange(page - 1)}>« Prev</button>
        {start > 1 && <button onClick={() => onPageChange(1)}>1</button>}
        {start > 2 && <span className="pagination-ellipsis">…</span>}
        {pages.map(p => (
          <button key={p} className={p === page ? 'active' : ''} onClick={() => onPageChange(p)}>
            {p}
          </button>
        ))}
        {end < total_pages - 1 && <span className="pagination-ellipsis">…</span>}
        {end < total_pages && <button onClick={() => onPageChange(total_pages)}>{total_pages}</button>}
        <button disabled={!has_next} onClick={() => onPageChange(page + 1)}>Next »</button>
      </div>
    </div>
  )
}

// --- Main App ---

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortKey, setSortKey] = useState('created_at')
  const [sortDir, setSortDir] = useState('desc')
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(20)
  const tableRef = useRef(null)

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    async function fetchData() {
      setLoading(true)
      try {
        const res = await fetch(`/api/call-analytics?page=${page}&per_page=${perPage}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.status === 401) {
          localStorage.removeItem('token')
          setToken(null)
          setError(null)
          return
        }
        if (!res.ok) {
          const text = await res.text()
          throw new Error(text)
        }
        const json = await res.json()
        setData(json)
        setError(null)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [token, page, perPage])

  useEffect(() => {
    if (data && tableRef.current) {
      tableRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [page, data])

  function handleLogout() {
    localStorage.removeItem('token')
    setToken(null)
    setData(null)
  }

  function handleLogin(newToken) {
    setToken(newToken)
    setError(null)
    setLoading(true)
  }

  if (!token) return <LoginPage onLogin={handleLogin} />

  function handleSort(key) {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const rows = data?.data || []
  const pagination = data?.pagination || null
  const filtered = rows.filter(row =>
    !searchQuery || Object.values(row).some(v => String(v ?? '').toLowerCase().includes(searchQuery.toLowerCase()))
  )
  const sorted = [...filtered].sort((a, b) => {
    const va = a[sortKey] ?? ''
    const vb = b[sortKey] ?? ''
    return sortDir === 'asc'
      ? String(va).localeCompare(String(vb))
      : String(vb).localeCompare(String(va))
  })

  if (!data && loading) return <div className="center"><h2>Loading...</h2></div>
  if (error && !data) return <div className="center"><h2>Error: {error}</h2><button className="logout-btn" onClick={handleLogout}>Logout</button></div>
  if (!data) return <div className="center"><h2>No data</h2></div>

  const { insights } = data
  const total = insights.total_calls || 1
  const categories = Object.entries(insights.category_counts || {})
  const statuses = Object.entries(insights.status_counts || {})

  return (
    <div className="container">
      <header className="header">
        <h1>Transcript Analytics Dashboard</h1>
        <button className="logout-btn" onClick={handleLogout}>Logout</button>
      </header>

      <section className="cards">
        {buildInsightCards(insights).map((c, i) => <Card key={i} {...c} />)}
      </section>

      <div className="grid-2">
        <div className="panel">
          <h3>Status</h3>
          {statuses.map(([k, v], i) => <Bar key={k} label={k} count={v} total={total} color={COLORS[i]} />)}
        </div>
        <div className="panel">
          <h3>Category</h3>
          {categories.map(([k, v], i) => <Bar key={k} label={k} count={v} total={total} color={COLORS[i % COLORS.length]} />)}
        </div>
      </div>

      <section className="panel" ref={tableRef}>
        <div className="table-header">
          <h3>Transcripts ({pagination?.total ?? sorted.length})</h3>
          <input className="search-input" placeholder="Search..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th onClick={() => handleSort('id')}>ID<SortIcon sortKey={sortKey} currentKey="id" direction={sortDir} /></th>
                <th onClick={() => handleSort('filename')}>Filename<SortIcon sortKey={sortKey} currentKey="filename" direction={sortDir} /></th>
                <th onClick={() => handleSort('category')}>Category<SortIcon sortKey={sortKey} currentKey="category" direction={sortDir} /></th>
                <th onClick={() => handleSort('status')}>Status<SortIcon sortKey={sortKey} currentKey="status" direction={sortDir} /></th>
                <th onClick={() => handleSort('confidence')}>Confidence<SortIcon sortKey={sortKey} currentKey="confidence" direction={sortDir} /></th>
                <th onClick={() => handleSort('created_at')}>Created<SortIcon sortKey={sortKey} currentKey="created_at" direction={sortDir} /></th>
              </tr>
            </thead>
            <tbody>
              {sorted.map(row => {
                const st = STATUS_STYLES[row.status] || {}
                return (
                  <tr key={row.id}>
                    <td>{row.id}</td>
                    <td>{row.filename}</td>
                    <td><span className="badge">{row.category}</span></td>
                    <td><span className="badge" style={{ backgroundColor: st.bg, color: st.color }}>{row.status}</span></td>
                    <td>{row.confidence != null ? row.confidence : '-'}</td>
                    <td>{formatDate(row.created_at)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <Pagination pagination={pagination} onPageChange={setPage} />
      </section>
    </div>
  )
}
