import { useEffect, useState } from 'react'
import { listManagedSatellites, addManagedSatellite, removeManagedSatellite } from '../api'

function formatDate(iso) {
  if (!iso) return 'N/A'
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function SatelliteManager() {
  const [activeTab, setActiveTab] = useState('satellites')
  const [satellites, setSatellites] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)
  const [expanded, setExpanded] = useState(null)

  const [satNorad, setSatNorad] = useState('')
  const [satName, setSatName] = useState('')
  const [satType, setSatType] = useState('')
  const [addingSat, setAddingSat] = useState(false)

  useEffect(() => {
    if (activeTab === 'satellites') loadSatellites()
  }, [activeTab])

  async function loadSatellites() {
    setLoading(true); setError(null)
    try {
      const data = await listManagedSatellites(false)
      setSatellites(data.satellites || [])
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  function showSuccess(msg) {
    setSuccessMsg(msg)
    setTimeout(() => setSuccessMsg(null), 4000)
  }

  async function handleAddSatellite(e) {
    e.preventDefault()
    if (!satNorad.trim()) return
    setAddingSat(true); setError(null)
    try {
      await addManagedSatellite({ norad_id: satNorad.trim(), name: satName.trim() || undefined, type: satType.trim() || undefined })
      showSuccess(`Satellite NORAD ${satNorad} added successfully`)
      setSatNorad(''); setSatName(''); setSatType('')
      loadSatellites()
    } catch (err) { setError(err.message) }
    finally { setAddingSat(false) }
  }

  async function handleRemoveSatellite(noradId, name) {
    if (!confirm(`Remove ${name || noradId} from tracking?`)) return
    try {
      await removeManagedSatellite(noradId)
      showSuccess(`Removed ${name || noradId}`)
      setSatellites(prev => prev.filter(s => s.norad_id !== noradId))
    } catch (err) { setError(err.message) }
  }

  return (
    <div className="satellite-manager">
      <div className="manager-header">
        <h2>🛰️ Satellite Manager</h2>
        <p>Manage tracked satellites and add objects by NORAD ID</p>
      </div>

      <div className="view-tabs">
        <button className={`view-tab ${activeTab === 'satellites' ? 'active' : ''}`} onClick={() => setActiveTab('satellites')}>🛰️ Tracked Satellites</button>
        <button className={`view-tab ${activeTab === 'add-satellite' ? 'active' : ''}`} onClick={() => setActiveTab('add-satellite')}>➕ Add Satellite</button>
      </div>

      {successMsg && <div className="success-message">✅ {successMsg}</div>}
      {error && <div className="error-message">❌ {error}</div>}

      {activeTab === 'satellites' && (
        <div className="satellites-section">
          <div className="section-info">
            <h3>Tracked Satellites ({satellites.length})</h3>
            <button className="refresh-btn" onClick={loadSatellites} disabled={loading}>
              {loading ? '⏳ Loading...' : '🔄 Refresh'}
            </button>
          </div>
          {loading ? (
            <div className="loading-container"><div className="spinner"></div><p>Loading satellites...</p></div>
          ) : satellites.length === 0 ? (
            <div className="empty-message">No satellites tracked yet. Add one using the "Add Satellite" tab.</div>
          ) : (
            <div className="sat-cards-grid">
              {satellites.map((sat, idx) => {
                const isOpen = expanded === (sat.norad_id || idx)
                return (
                  <div key={sat.norad_id || idx} className={`sat-card ${isOpen ? 'sat-card--open' : ''}`}>
                    <div className="sat-card-header" onClick={() => setExpanded(isOpen ? null : (sat.norad_id || idx))}>
                      <div className="sat-card-title">
                        <span className="sat-card-icon">🛰️</span>
                        <div>
                          <h4>{sat.name || `NORAD ${sat.norad_id}`}</h4>
                          <span className="sat-card-norad">ID: {sat.norad_id}</span>
                        </div>
                      </div>
                      <div className="sat-card-right">
                        <span className="debris-badge">{sat.type || 'Satellite'}</span>
                        <span className="sat-card-chevron">{isOpen ? '▲' : '▼'}</span>
                      </div>
                    </div>

                    {isOpen && (
                      <div className="sat-card-body">
                        <div className="sat-detail-grid">
                          <div className="sat-detail-item">
                            <span className="sat-detail-label">NORAD ID</span>
                            <span className="sat-detail-value">{sat.norad_id}</span>
                          </div>
                          <div className="sat-detail-item">
                            <span className="sat-detail-label">Type</span>
                            <span className="sat-detail-value">{sat.type || 'N/A'}</span>
                          </div>
                          <div className="sat-detail-item">
                            <span className="sat-detail-label">Operator</span>
                            <span className="sat-detail-value">{sat.operator || 'N/A'}</span>
                          </div>
                          <div className="sat-detail-item">
                            <span className="sat-detail-label">Launch Date</span>
                            <span className="sat-detail-value">{formatDate(sat.launch_date)}</span>
                          </div>
                          <div className="sat-detail-item">
                            <span className="sat-detail-label">TLE Epoch</span>
                            <span className="sat-detail-value">{formatDate(sat.tle_epoch)}</span>
                          </div>
                          <div className="sat-detail-item">
                            <span className="sat-detail-label">Added</span>
                            <span className="sat-detail-value">{formatDate(sat.added_at)}</span>
                          </div>
                          <div className="sat-detail-item">
                            <span className="sat-detail-label">Last Updated</span>
                            <span className="sat-detail-value">{formatDate(sat.last_updated)}</span>
                          </div>
                          <div className="sat-detail-item">
                            <span className="sat-detail-label">Status</span>
                            <span className={`sat-detail-value ${sat.active ? 'sat-status-active' : 'sat-status-inactive'}`}>
                              {sat.active ? '● Active' : '○ Inactive'}
                            </span>
                          </div>
                        </div>
                        {sat.description && (
                          <div className="sat-description">{sat.description}</div>
                        )}
                        <button className="remove-btn" onClick={() => handleRemoveSatellite(sat.norad_id, sat.name)}>
                          🗑️ Remove from Tracking
                        </button>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {activeTab === 'add-satellite' && (
        <div className="add-section">
          <div className="section-info">
            <h3>Add Satellite by NORAD ID</h3>
            <p>Enter a NORAD catalog number to start tracking a satellite. Only NORAD ID is required.</p>
          </div>
          <form onSubmit={handleAddSatellite} className="add-form">
            <div className="form-group">
              <label>NORAD ID *</label>
              <input type="text" value={satNorad} onChange={e => setSatNorad(e.target.value)} placeholder="e.g. 25544 (ISS)" className="search-input" required />
            </div>
            <div className="form-group">
              <label>Name (optional)</label>
              <input type="text" value={satName} onChange={e => setSatName(e.target.value)} placeholder="e.g. ISS (ZARYA)" className="search-input" />
            </div>
            <div className="form-group">
              <label>Type (optional)</label>
              <input type="text" value={satType} onChange={e => setSatType(e.target.value)} placeholder="e.g. Space Station, Weather Satellite" className="search-input" />
            </div>
            <button type="submit" className="search-btn" disabled={addingSat}>
              {addingSat ? '⏳ Adding...' : '➕ Add Satellite'}
            </button>
          </form>
          <div className="norad-hint">
            <h4>Common NORAD IDs</h4>
            <div className="hint-grid">
              {[
                { id: '25544', name: 'ISS' },
                { id: '20580', name: 'NOAA-19' },
                { id: '43013', name: 'Hubble' },
                { id: '28654', name: 'NOAA-18' },
                { id: '33591', name: 'NOAA-19' },
                { id: '27424', name: 'XMM-Newton' },
              ].map(s => (
                <button key={s.id} className="hint-chip" onClick={() => { setSatNorad(s.id); setSatName(s.name) }}>
                  {s.name} ({s.id})
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
