import { useState } from 'react'
import { motion } from 'framer-motion'

const API_BASE = ''

const styles = {
  form: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: '1rem',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.35rem',
  },
  label: {
    fontSize: '0.85rem',
    color: 'var(--text-muted)',
    fontWeight: 500,
  },
  input: {
    padding: '0.5rem 0.75rem',
    borderRadius: '8px',
    border: '1px solid var(--border)',
    background: 'var(--bg-dark)',
    color: 'var(--text)',
    fontSize: '0.95rem',
  },
  btn: {
    padding: '0.75rem 1.5rem',
    borderRadius: '8px',
    border: 'none',
    background: 'var(--accent)',
    color: 'var(--bg-dark)',
    fontWeight: 600,
    cursor: 'pointer',
    fontSize: '1rem',
    marginTop: '0.5rem',
  },
  btnSecondary: {
    padding: '0.75rem 1.5rem',
    borderRadius: '8px',
    border: '1px solid var(--accent)',
    background: 'transparent',
    color: 'var(--accent)',
    fontWeight: 600,
    cursor: 'pointer',
    fontSize: '1rem',
    marginTop: '0.5rem',
    marginLeft: '0.5rem',
  },
  btnTertiary: {
    padding: '0.5rem 1rem',
    borderRadius: '8px',
    border: '1px solid var(--border)',
    background: 'transparent',
    color: 'var(--text-muted)',
    fontWeight: 500,
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
}

export default function InputForm({ onCalculate, onRunPetriNet, loading }) {
  const [form, setForm] = useState({
    debris_diameter: 10,
    altitude: 400,
    inclination: 51.6,
    year: 2024,
    solar_flux: 200,
    exposure_area: 10,
    exposure_time: 1,
    orbit_type: 'circular',
    perigee_km: 400,
    apogee_km: 500,
  })
  const [noradId, setNoradId] = useState('25544')
  const [celestrakLoading, setCelestrakLoading] = useState(false)
  const [celestrakName, setCelestrakName] = useState(null)
  const [celestrakError, setCelestrakError] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((f) => ({
      ...f,
      [name]: name.includes('_km') || ['debris_diameter','altitude','inclination','year','solar_flux','exposure_area','exposure_time'].includes(name)
        ? parseFloat(value) || 0
        : value,
    }))
  }

  const buildPayload = () => {
    const op = {
      orbit_type: form.orbit_type,
      altitude_km: form.orbit_type === 'circular' ? form.altitude : form.perigee_km,
    }
    if (form.orbit_type === 'elliptical') {
      op.perigee_km = form.perigee_km
      op.apogee_km = form.apogee_km
    }
    return {
      debris_diameter: form.debris_diameter,
      altitude: form.altitude,
      inclination: form.inclination,
      year: form.year,
      solar_flux: form.solar_flux,
      exposure_area: form.exposure_area,
      exposure_time: form.exposure_time,
      orbit_params: op,
    }
  }

  const handleSubmit = async () => {
    onCalculate(buildPayload())
  }

  const handleRunPetriNet = async () => {
    onRunPetriNet(buildPayload())
  }

  const handleLoadCelestrak = async () => {
    const id = parseInt(noradId, 10)
    if (!id || id < 1) {
      setCelestrakError('Enter a valid NORAD ID (e.g. 25544 for ISS)')
      return
    }
    setCelestrakError(null)
    setCelestrakName(null)
    setCelestrakLoading(true)
    try {
      const res = await fetch(`${API_BASE}/celestrak/satellite/${id}`)
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || res.statusText)
      }
      const data = await res.json()
      setForm((f) => ({
        ...f,
        altitude: data.altitude_km,
        inclination: data.inclination,
        orbit_type: data.orbit_type || 'circular',
        perigee_km: data.perigee_km ?? f.perigee_km,
        apogee_km: data.apogee_km ?? f.apogee_km,
      }))
      setCelestrakName(data.name || `NORAD ${id}`)
    } catch (e) {
      setCelestrakError(e.message || 'Failed to fetch from Celestrak')
    } finally {
      setCelestrakLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{
        background: 'var(--bg-card)',
        borderRadius: '12px',
        padding: '1.5rem',
        border: '1px solid var(--border)',
      }}
    >
      <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>Input Parameters</h2>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={styles.field}>
          <label style={styles.label}>NORAD ID (Celestrak)</label>
          <input
            type="text"
            placeholder="e.g. 25544"
            value={noradId}
            onChange={(e) => setNoradId(e.target.value)}
            style={{ ...styles.input, width: '120px' }}
          />
        </div>
        <button
          type="button"
          style={styles.btnTertiary}
          onClick={handleLoadCelestrak}
          disabled={celestrakLoading}
        >
          {celestrakLoading ? 'Loading…' : 'Load orbit from Celestrak'}
        </button>
        {celestrakName && (
          <span style={{ color: 'var(--accent)', fontSize: '0.9rem' }}>Loaded: {celestrakName}</span>
        )}
        {celestrakError && (
          <span style={{ color: '#f87171', fontSize: '0.85rem' }}>{celestrakError}</span>
        )}
      </div>
      <div style={styles.form}>
        <div style={styles.field}>
          <label style={styles.label}>Debris Diameter (mm)</label>
          <input
            type="number"
            name="debris_diameter"
            value={form.debris_diameter}
            onChange={handleChange}
            min={0.1}
            step={0.1}
            style={styles.input}
          />
        </div>
        <div style={styles.field}>
          <label style={styles.label}>Altitude (km)</label>
          <input
            type="number"
            name="altitude"
            value={form.altitude}
            onChange={handleChange}
            min={0}
            max={2000}
            step={10}
            style={styles.input}
          />
        </div>
        <div style={styles.field}>
          <label style={styles.label}>Inclination (°)</label>
          <input
            type="number"
            name="inclination"
            value={form.inclination}
            onChange={handleChange}
            min={0}
            max={180}
            step={0.1}
            style={styles.input}
          />
        </div>
        <div style={styles.field}>
          <label style={styles.label}>Year</label>
          <input
            type="number"
            name="year"
            value={form.year}
            onChange={handleChange}
            min={1988}
            max={2100}
            step={1}
            style={styles.input}
          />
        </div>
        <div style={styles.field}>
          <label style={styles.label}>Solar Flux S</label>
          <input
            type="number"
            name="solar_flux"
            value={form.solar_flux}
            onChange={handleChange}
            min={0}
            step={1}
            style={styles.input}
          />
        </div>
        <div style={styles.field}>
          <label style={styles.label}>Exposure Area (m²)</label>
          <input
            type="number"
            name="exposure_area"
            value={form.exposure_area}
            onChange={handleChange}
            min={0.01}
            step={0.1}
            style={styles.input}
          />
        </div>
        <div style={styles.field}>
          <label style={styles.label}>Exposure Time (years)</label>
          <input
            type="number"
            name="exposure_time"
            value={form.exposure_time}
            onChange={handleChange}
            min={0.01}
            step={0.1}
            style={styles.input}
          />
        </div>
        <div style={styles.field}>
          <label style={styles.label}>Orbit Type</label>
          <select
            name="orbit_type"
            value={form.orbit_type}
            onChange={handleChange}
            style={styles.input}
          >
            <option value="circular">Circular</option>
            <option value="elliptical">Elliptical</option>
          </select>
        </div>
        {form.orbit_type === 'elliptical' && (
          <>
            <div style={styles.field}>
              <label style={styles.label}>Perigee (km)</label>
              <input
                type="number"
                name="perigee_km"
                value={form.perigee_km}
                onChange={handleChange}
                min={0}
                max={2000}
                step={10}
                style={styles.input}
              />
            </div>
            <div style={styles.field}>
              <label style={styles.label}>Apogee (km)</label>
              <input
                type="number"
                name="apogee_km"
                value={form.apogee_km}
                onChange={handleChange}
                min={0}
                max={2000}
                step={10}
                style={styles.input}
              />
            </div>
          </>
        )}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '1rem' }}>
        <button
          style={styles.btn}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? 'Calculating…' : 'Calculate'}
        </button>
        <button
          style={styles.btnSecondary}
          onClick={handleRunPetriNet}
          disabled={loading}
        >
          Run Model (Petri Net)
        </button>
      </div>
    </motion.div>
  )
}
