import { useEffect, useState } from 'react'
import './App.css'

const RUN_DATE = '2026-08-07'
const API = '/api'

function useFetch(url) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [url])

  return { data, loading, error }
}

// Renders Python-style stringified lists as plain comma-separated values.
// "['SE', 'LU', 'IE']" → "SE, LU, IE"
function formatValue(v) {
  if (v == null) return '—'
  const s = String(v).trim()
  if (s.startsWith('[') && s.endsWith(']')) {
    try {
      const parsed = JSON.parse(s.replace(/'/g, '"'))
      if (Array.isArray(parsed)) return parsed.join(', ')
    } catch {}
  }
  return s || '—'
}

function StatusBadge({ status }) {
  return (
    <span className={`badge badge-${status.toLowerCase()}`}>{status}</span>
  )
}

function SummaryCards({ summary }) {
  const cards = [
    { label: 'Compliant', key: 'COMPLIANT', cls: 'compliant' },
    { label: 'Breaches',  key: 'BREACH',    cls: 'breach'    },
    { label: 'Unknown',   key: 'UNKNOWN',   cls: 'unknown'   },
  ]
  return (
    <div className="cards">
      {cards.map(({ label, key, cls }) => (
        <div key={key} className={`card card-${cls}`}>
          <div className="card-count">{summary[key] ?? 0}</div>
          <div className="card-label">{label}</div>
        </div>
      ))}
    </div>
  )
}

function NewHoldingsSection({ date }) {
  const { data, loading, error } = useFetch(`${API}/new-holdings/${date}`)

  return (
    <section className="section">
      <h2 className="section-title">New holdings</h2>
      {loading && <p className="state-msg">Loading…</p>}
      {error   && <p className="state-msg state-error">Could not load new holdings: {error}</p>}
      {data && data.length === 0 && <p className="state-msg">No new holdings on {date}.</p>}
      {data && data.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Account</th>
              <th>ISIN</th>
              <th>Rule</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((f, i) => (
              <tr key={i}>
                <td>{f.account_id}</td>
                <td className="mono">{f.isin}</td>
                <td>{f.rule_id}</td>
                <td><StatusBadge status={f.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

function EventsSection({ date }) {
  const { data, loading, error } = useFetch(`${API}/events/${date}`)
  const { data: findingsData } = useFetch(`${API}/findings/${date}`)

  const heldIsins = new Set(findingsData ? findingsData.map(f => f.isin) : [])

  return (
    <section className="section">
      <h2 className="section-title">Corporate events</h2>
      {loading && <p className="state-msg">Loading…</p>}
      {error   && <p className="state-msg state-error">Could not load events: {error}</p>}
      {data && data.length === 0 && <p className="state-msg">No events on {date}.</p>}
      {data && data.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>ISIN</th>
              <th>Event type</th>
              <th>Old value</th>
              <th>New value</th>
            </tr>
          </thead>
          <tbody>
            {data.map((e, i) => (
              <tr key={i}>
                <td className="mono">
                  {e.isin}
                  {findingsData && !heldIsins.has(e.isin) && (
                    <span className="not-held-label">not held</span>
                  )}
                </td>
                <td>{e.event_type.replace(/_/g, ' ')}</td>
                <td className="val-old">{e.old_value}</td>
                <td className="val-new">{e.new_value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

// Groups findings by ISIN so one downgrade affecting four accounts
// reads as a single block rather than four unrelated rows.
function RequiresActionSection({ date }) {
  const { data: allData, loading, error } = useFetch(`${API}/findings/${date}`)
  const { data: explanationsData } = useFetch(`${API}/explanations/${date}`)

  const data = allData
    ? allData.filter(f => f.status === 'BREACH' || f.status === 'UNKNOWN')
    : null

  const explanations = {}
  if (explanationsData) {
    for (const e of explanationsData) {
      explanations[`${e.isin}|${e.rule_id}`] = e.explanation
    }
  }

  // Build groups: ISIN -> list of findings (ordered by account)
  const groups = data
    ? Object.entries(
        data.reduce((acc, f) => {
          if (!acc[f.isin]) acc[f.isin] = []
          acc[f.isin].push(f)
          return acc
        }, {})
      )
    : []

  return (
    <section className="section">
      <h2 className="section-title">Requires action</h2>
      {loading && <p className="state-msg">Loading…</p>}
      {error   && <p className="state-msg state-error">Could not load findings: {error}</p>}
      {data && data.length === 0 && <p className="state-msg state-ok">Nothing requires action on {date}.</p>}
      {groups.length > 0 && (
        <div className="isin-groups">
          {groups.map(([isin, findings]) => {
            const ruleIds = [...new Set(findings.map(f => f.rule_id))]
            const groupExplanations = ruleIds
              .map(ruleId => explanations[`${isin}|${ruleId}`])
              .filter(Boolean)
            return (
              <div key={isin} className="isin-group">
                <div className="isin-group-header">
                  <span className="isin-label">{isin}</span>
                  <span className="isin-rule-hint">
                    {ruleIds.join(', ')}
                    {' · '}
                    {findings.length} account{findings.length !== 1 ? 's' : ''}
                  </span>
                </div>
                {groupExplanations.map((text, idx) => (
                  <p key={idx} className="explanation-text">{text}</p>
                ))}
                <table className="table table-nested">
                  <thead>
                    <tr>
                      <th>Account</th>
                      <th>Rule</th>
                      <th>Status</th>
                      <th>Threshold</th>
                      <th>Actual</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {findings.map((f, i) => (
                      <tr key={i}>
                        <td>{f.account_id}</td>
                        <td>{f.rule_id}</td>
                        <td><StatusBadge status={f.status} /></td>
                        <td>{formatValue(f.threshold)}</td>
                        <td>{formatValue(f.actual)}</td>
                        <td className="reason-cell">{f.reason ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

export default function App() {
  const { data: summary, loading: sLoading, error: sError } =
    useFetch(`${API}/summary/${RUN_DATE}`)

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="header-brand">
            <span className="header-logo">◈</span>
            <span className="header-title">Portfolio Monitor</span>
          </div>
          <div className="header-date">Run date: <strong>{RUN_DATE}</strong></div>
        </div>
      </header>

      <main className="main">
        {sLoading && <p className="state-msg">Loading summary…</p>}
        {sError   && (
          <div className="api-error">
            <strong>API unreachable</strong>
            <p>Could not connect to the backend: {sError}</p>
            <p>Make sure the server is running on <code>http://localhost:8000</code>.</p>
          </div>
        )}
        {summary && <SummaryCards summary={summary} />}

        <NewHoldingsSection    date={RUN_DATE} />
        <EventsSection         date={RUN_DATE} />
        <RequiresActionSection date={RUN_DATE} />
      </main>
    </div>
  )
}
