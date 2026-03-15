import { useEffect, useState } from 'react'
import { searchSpaceDebris, getHighRiskDebris, getRecentDebris, getDebrisDetails, addDebrisByNorad } from '../api'

export default function DebrisTracker() {
  const [activeView, setActiveView] = useState('search')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [highRiskDebris, setHighRiskDebris] = useState([])
  const [recentDebris, setRecentDebris] = useState([])
  const [selectedDebris, setSelectedDebris] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Add debris by NORAD
  const [debrisNorad, setDebrisNorad] = useState('')
  const [addingDebris, setAddingDebris] = useState(false)
  const [debrisResult, setDebrisResult] = useState(null)
  const [addSuccess, setAddSuccess] = useState(null)

  useEffect(() => {
    if (activeView === 'high-risk') loadHighRiskDebris()
    else if (activeView === 'recent') loadRecentDebris()
    else if (activeView === 'add') { setDebrisResult(null); setAddSuccess(null); setError(null) }
  }, [activeView])

  async function loadHighRiskDebris() {
    setLoading(true); setError(null)
    try {
      const data = await getHighRiskDebris()
      setHighRiskDebris(data.high_risk_debris || [])
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function loadRecentDebris() {
    setLoading(true); setError(null)
    try {
      const data = await getRecentDebris()
      setRecentDebris(data.recent_debris || [])
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function handleSearch(e) {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setLoading(true); setError(null)
    try {
      const data = await searchSpaceDebris(searchQuery)
      setSearchResults(data.debris || [])
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function viewDebrisDetails(noradId) {
    setLoading(true); setError(null)
    try {
      const data = await getDebrisDetails(noradId)
      setSelectedDebris(data.debris)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function handleAddDebris(e) {
    e.preventDefault()
    if (!debrisNorad.trim()) return
    setAddingDebris(true); setError(null); setDebrisResult(null); setAddSuccess(null)
    try {
      const data = await addDebrisByNorad(debrisNorad.trim())
      setDebrisResult(data)
      setAddSuccess(`Debris NORAD ${debrisNorad} verified successfully`)
      setDebrisNorad('')
    } catch (err) { setError(err.message) }
    finally { setAddingDebris(false) }
  }

  function renderDebrisList(debrisList) {
    if (loading) return (
      <div className="loading-container"><div className="spinner"></div><p>Loading debris data...</p></div>
    )
    if (error) return <div className="error-message">Error: {error}</div>
    if (!debrisList || debrisList.length === 0) return <div className="empty-message">No debris found</div>

    return (
      <div className="debris-list">
        {debrisList.map((debris, idx) => (
          <div key={debris.norad_id || idx} className="debris-item">
            <div className="debris-header">
              <h4>{debris.name || 'Unknown'}</h4>
              <span className="debris-badge">{debris.type || 'N/A'}</span>
            </div>
            <div className="debris-details">
              <div className="detail-row"><span className="detail-label">NORAD ID:</span><span className="detail-value">{debris.norad_id || 'N/A'}</span></div>
              <div className="detail-row"><span className="detail-label">Country:</span><span className="detail-value">{debris.country || 'N/A'}</span></div>
              <div className="detail-row"><span className="detail-label">Inclination:</span><span className="detail-value">{debris.inclination_deg ? `${debris.inclination_deg}°` : 'N/A'}</span></div>
              <div className="detail-row"><span className="detail-label">Period:</span><span className="detail-value">{debris.period_minutes ? `${debris.period_minutes} min` : 'N/A'}</span></div>
            </div>
            <button className="view-details-btn" onClick={() => viewDebrisDetails(debris.norad_id)}>View Details</button>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="debris-tracker">
      <div className="tracker-header">
        <h2>Space Debris Tracker</h2>
        <p>Real-time orbital debris tracking powered by Space-Track.org</p>
      </div>

      <div className="view-tabs">
        <button className={`view-tab ${activeView === 'search' ? 'active' : ''}`} onClick={() => setActiveView('search')}>🔍 Search</button>
        <button className={`view-tab ${activeView === 'high-risk' ? 'active' : ''}`} onClick={() => setActiveView('high-risk')}>⚠️ High Risk</button>
        <button className={`view-tab ${activeView === 'recent' ? 'active' : ''}`} onClick={() => setActiveView('recent')}>🆕 Recent</button>
        <button className={`view-tab ${activeView === 'add' ? 'active' : ''}`} onClick={() => setActiveView('add')}>🪨 Add by NORAD</button>
      </div>

      {activeView === 'search' && (
        <div className="search-section">
          <form onSubmit={handleSearch} className="search-form">
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search by type (debris, rocket_body, payload)..." className="search-input" />
            <button type="submit" className="search-btn">Search</button>
          </form>
          {renderDebrisList(searchResults)}
        </div>
      )}

      {activeView === 'high-risk' && (
        <div className="high-risk-section">
          <div className="section-info"><h3>High-Risk Debris in LEO</h3><p>Debris objects in Low Earth Orbit (200-2000 km altitude)</p></div>
          {renderDebrisList(highRiskDebris)}
        </div>
      )}

      {activeView === 'recent' && (
        <div className="recent-section">
          <div className="section-info"><h3>Recently Cataloged Debris</h3><p>Newly tracked debris objects from the last 30 days</p></div>
          {renderDebrisList(recentDebris)}
        </div>
      )}

      {activeView === 'add' && (
        <div className="add-section">
          <div className="section-info">
            <h3>Look Up Debris by NORAD ID</h3>
            <p>Verify a debris object exists in Space-Track and get its TLE data for collision analysis.</p>
          </div>
          {addSuccess && <div className="success-message">✅ {addSuccess}</div>}
          {error && <div className="error-message">❌ {error}</div>}
          <form onSubmit={handleAddDebris} className="add-form">
            <div className="form-group">
              <label>NORAD ID</label>
              <input type="text" value={debrisNorad} onChange={e => setDebrisNorad(e.target.value)} placeholder="e.g. 48274" className="search-input" required />
            </div>
            <button type="submit" className="search-btn" disabled={addingDebris}>
              {addingDebris ? '⏳ Looking up...' : '🔍 Look Up Debris'}
            </button>
          </form>
          {debrisResult && (
            <div className="debris-result-card">
              <h4>✅ Debris Found</h4>
              <div className="debris-details">
                <div className="detail-row"><span className="detail-label">NORAD ID:</span><span className="detail-value">{debrisResult.norad_id}</span></div>
                <div className="detail-row"><span className="detail-label">TLE Line 1:</span><span className="detail-value tle-line">{debrisResult.tle?.line1}</span></div>
                <div className="detail-row"><span className="detail-label">TLE Line 2:</span><span className="detail-value tle-line">{debrisResult.tle?.line2}</span></div>
              </div>
              <p className="result-hint">Use this NORAD ID in the Satellite Profile tab to run a collision analysis.</p>
            </div>
          )}
          <div className="norad-hint">
            <h4>How to find NORAD IDs</h4>
            <p>Search for debris objects on <a href="https://www.space-track.org" target="_blank" rel="noopener noreferrer">Space-Track.org</a> or use the Search tab above to browse and find NORAD IDs.</p>
          </div>
        </div>
      )}

      {selectedDebris && (
        <div className="modal-overlay" onClick={() => setSelectedDebris(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Debris Details</h3>
              <button className="modal-close" onClick={() => setSelectedDebris(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="details-grid">
                <div className="detail-item"><span className="detail-label">Name:</span><span className="detail-value">{selectedDebris.name}</span></div>
                <div className="detail-item"><span className="detail-label">NORAD ID:</span><span className="detail-value">{selectedDebris.norad_id}</span></div>
                <div className="detail-item"><span className="detail-label">Type:</span><span className="detail-value">{selectedDebris.type}</span></div>
                <div className="detail-item"><span className="detail-label">Country:</span><span className="detail-value">{selectedDebris.country}</span></div>
                <div className="detail-item"><span className="detail-label">Launch Date:</span><span className="detail-value">{selectedDebris.launch_date || 'N/A'}</span></div>
                <div className="detail-item"><span className="detail-label">Epoch:</span><span className="detail-value">{selectedDebris.epoch || 'N/A'}</span></div>
                <div className="detail-item"><span className="detail-label">Period:</span><span className="detail-value">{selectedDebris.period_minutes ? `${selectedDebris.period_minutes} min` : 'N/A'}</span></div>
                <div className="detail-item"><span className="detail-label">Inclination:</span><span className="detail-value">{selectedDebris.inclination_deg ? `${selectedDebris.inclination_deg}°` : 'N/A'}</span></div>
                <div className="detail-item"><span className="detail-label">Eccentricity:</span><span className="detail-value">{selectedDebris.eccentricity || 'N/A'}</span></div>
                <div className="detail-item"><span className="detail-label">Mean Motion:</span><span className="detail-value">{selectedDebris.mean_motion || 'N/A'}</span></div>
                <div className="detail-item"><span className="detail-label">RCS Size:</span><span className="detail-value">{selectedDebris.rcs_size || 'N/A'}</span></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
