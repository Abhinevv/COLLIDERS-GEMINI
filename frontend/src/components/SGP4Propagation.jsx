import { useState } from 'react'
import { motion } from 'framer-motion'

const API_BASE = ''

const cardStyle = {
  background: 'var(--bg-card)',
  borderRadius: '12px',
  padding: '1.5rem',
  border: '1px solid var(--border)',
}

export default function SGP4Propagation() {
  const [form, setForm] = useState({
    tle_line1: '1 25544U 98067A   24050.12345678  .00001234  00000+0  12345-4 0  9999',
    tle_line2: '2 25544  51.6323 161.9142 0008604 112.9152 247.2745 15.48140240123456',
    start_time: new Date().toISOString().slice(0, 16),
    end_time: new Date(Date.now() + 3600 * 1000).toISOString().slice(0, 16), // 1 hour instead of 24
    step_seconds: 300, // 5 minutes for faster testing
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((f) => ({
      ...f,
      [name]: name === 'tle_line1' || name === 'tle_line2' ? value : (name.includes('time') ? value : parseFloat(value) || 0),
    }))
  }

  const handlePropagate = async () => {
    setLoading(true)
    setResult(null)
    try {
      // Convert datetime-local to ISO format
      // datetime-local gives "YYYY-MM-DDTHH:mm" format
      const startISO = new Date(form.start_time + ':00').toISOString()
      const endISO = new Date(form.end_time + ':00').toISOString()
      
      const res = await fetch(`${API_BASE}/propagate-orbit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tle_line1: form.tle_line1.trim(),
          tle_line2: form.tle_line2.trim(),
          start_time: startISO,
          end_time: endISO,
          step_seconds: form.step_seconds,
        }),
      })
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(errorData.detail || `HTTP ${res.status}`)
      }
      
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setResult({ error: e.message || 'Failed to propagate orbit' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={cardStyle}
    >
      <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem', color: 'var(--accent)' }}>
        SGP4 Orbit Propagation
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>TLE Line 1</label>
          <input
            type="text"
            name="tle_line1"
            value={form.tle_line1}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)', fontFamily: 'monospace', fontSize: '0.85rem' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>TLE Line 2</label>
          <input
            type="text"
            name="tle_line2"
            value={form.tle_line2}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)', fontFamily: 'monospace', fontSize: '0.85rem' }}
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem' }}>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Start Time</label>
            <input
              type="datetime-local"
              name="start_time"
              value={form.start_time}
              onChange={handleChange}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>End Time</label>
            <input
              type="datetime-local"
              name="end_time"
              value={form.end_time}
              onChange={handleChange}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Step (seconds)</label>
            <input
              type="number"
              name="step_seconds"
              value={form.step_seconds}
              onChange={handleChange}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
            />
          </div>
        </div>
      </div>
      <button
        onClick={handlePropagate}
        disabled={loading}
        style={{
          marginTop: '1rem',
          padding: '0.5rem 1rem',
          borderRadius: '6px',
          border: 'none',
          background: 'var(--accent)',
          color: 'var(--bg-dark)',
          fontWeight: 600,
          cursor: loading ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? 'Propagating...' : 'Propagate Orbit'}
      </button>
      {result && result.error && (
        <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(248,113,113,0.1)', borderRadius: '8px', color: '#f87171' }}>
          <strong>Error:</strong> {result.error}
        </div>
      )}
      {result && !result.error && (
        <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0,212,170,0.1)', borderRadius: '8px' }}>
          <div style={{ marginBottom: '0.5rem', color: 'var(--accent)', fontWeight: 600 }}>
            {result.num_states} states computed
          </div>
          {result.states && result.states.length > 0 ? (
            <div style={{ maxHeight: '300px', overflowY: 'auto', fontSize: '0.8rem', fontFamily: 'JetBrains Mono' }}>
              {result.states.slice(0, 10).map((state, i) => (
                <div key={i} style={{ padding: '0.5rem', marginBottom: '0.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '4px' }}>
                  <div style={{ color: 'var(--accent)' }}>{state.time}</div>
                  <div style={{ color: 'var(--text-muted)' }}>
                    Alt: {state.altitude_km?.toFixed(2) || 'N/A'} km | Inc: {state.inclination_deg?.toFixed(2) || 'N/A'}°
                  </div>
                </div>
              ))}
              {result.states.length > 10 && (
                <div style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                  ... and {result.states.length - 10} more states
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)' }}>No states computed</div>
          )}
        </div>
      )}
    </motion.div>
  )
}
