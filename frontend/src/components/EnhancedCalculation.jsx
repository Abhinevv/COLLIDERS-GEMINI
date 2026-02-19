import { useState } from 'react'
import { motion } from 'framer-motion'

const API_BASE = ''

const cardStyle = {
  background: 'var(--bg-card)',
  borderRadius: '12px',
  padding: '1.5rem',
  border: '1px solid var(--border)',
}

export default function EnhancedCalculation({ onCalculate }) {
  const [form, setForm] = useState({
    debris_diameter: 10,
    altitude: 400,
    inclination: 51.6,
    year: 2024,
    solar_flux: 200,
    exposure_area: 10,
    exposure_time: 1,
    impact_angle_deg: 90,
    include_velocity: true,
    include_geometry: true,
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm((f) => ({
      ...f,
      [name]: type === 'checkbox' ? checked : parseFloat(value) || 0,
    }))
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/calculate-enhanced`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      setResult(data)
      if (onCalculate) onCalculate(data)
    } catch (e) {
      setResult({ error: e.message })
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
        Enhanced Calculation (Velocity + Geometry)
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.75rem' }}>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Debris Diameter (mm)</label>
          <input
            type="number"
            name="debris_diameter"
            value={form.debris_diameter}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Altitude (km)</label>
          <input
            type="number"
            name="altitude"
            value={form.altitude}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Impact Angle (°)</label>
          <input
            type="number"
            name="impact_angle_deg"
            value={form.impact_angle_deg}
            onChange={handleChange}
            min={0}
            max={180}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Exposure Area (m²)</label>
          <input
            type="number"
            name="exposure_area"
            value={form.exposure_area}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Exposure Time (years)</label>
          <input
            type="number"
            name="exposure_time"
            value={form.exposure_time}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--text)' }}
          />
        </div>
      </div>
      <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', alignItems: 'center' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
          <input
            type="checkbox"
            name="include_velocity"
            checked={form.include_velocity}
            onChange={handleChange}
          />
          <span style={{ fontSize: '0.9rem' }}>Include Velocity</span>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
          <input
            type="checkbox"
            name="include_geometry"
            checked={form.include_geometry}
            onChange={handleChange}
          />
          <span style={{ fontSize: '0.9rem' }}>Include Geometry</span>
        </label>
        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '6px',
            border: 'none',
            background: 'var(--accent)',
            color: 'var(--bg-dark)',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Calculating...' : 'Calculate Enhanced'}
        </button>
      </div>
      {result && !result.error && (
        <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0,212,170,0.1)', borderRadius: '8px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0.75rem', fontFamily: 'JetBrains Mono', fontSize: '0.85rem' }}>
            <div>
              <div style={{ color: 'var(--text-muted)' }}>Q Base</div>
              <div style={{ color: 'var(--accent)', fontWeight: 700 }}>{(result.Q_base * 100).toFixed(6)}%</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)' }}>Q Enhanced</div>
              <div style={{ color: 'var(--accent)', fontWeight: 700 }}>{(result.Q_enhanced * 100).toFixed(6)}%</div>
            </div>
            {result.relative_velocity_km_s && (
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Rel. Velocity</div>
                <div style={{ color: 'var(--accent)' }}>{result.relative_velocity_km_s.toFixed(2)} km/s</div>
              </div>
            )}
            <div>
              <div style={{ color: 'var(--text-muted)' }}>Eff. Area</div>
              <div style={{ color: 'var(--accent)' }}>{result.effective_area_m2.toFixed(2)} m²</div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  )
}
