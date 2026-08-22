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

      {selectedDebris && (() => {
        const clsInfo = (() => {
          const typeStr = (selectedDebris.classification || selectedDebris.type || '').toUpperCase()
          const nameStr = (selectedDebris.name || '').toUpperCase()
          if (typeStr.includes('ROCKET') || typeStr.includes('R/B') || nameStr.includes(' R/B') || nameStr.includes('STAGE') || nameStr.includes('TRANSTAGE') || nameStr.includes('ARIANE R/B') || nameStr.includes('PSLV R/B') || nameStr.includes('GSLV R/B')) {
            return { icon: '🚀', className: 'Rocket Body', meaning: 'Spent upper stage / launch vehicle body', color: '#ff9800' }
          }
          if (typeStr.includes('FRAGMENT') || typeStr.includes('DEB') || nameStr.includes('DEB') || nameStr.includes('OBJ-') || nameStr.includes('BREAKUP') || nameStr.includes('COLLISION')) {
            return { icon: '🔹', className: 'Fragment', meaning: 'Pieces created by breakup/collision', color: '#4fc3f7' }
          }
          if (typeStr.includes('DEFUNCT') || typeStr.includes('DERELICT') || nameStr.includes('DEFUNCT') || nameStr.includes('DERELICT') || nameStr.includes('ENVISAT')) {
            return { icon: '⚫', className: 'Defunct Satellite', meaning: 'Satellite no longer operational', color: '#b0bec5' }
          }
          if (typeStr.includes('SATELLITE') || typeStr.includes('PAYLOAD') || typeStr.includes('WEATHER') || typeStr.includes('EARTH OBSERVATION') || typeStr.includes('NAVIGATION') || typeStr.includes('COMMUNICATION') || typeStr.includes('SPACE SCIENCE')) {
            return { icon: '🛰️', className: 'Active Satellite', meaning: 'Currently operational spacecraft', color: '#00e676' }
          }
          if (!typeStr || typeStr === 'UNKNOWN' || typeStr === 'UNASSIGNED' || typeStr === 'N/A') {
            return { icon: '❓', className: 'Unknown Object', meaning: 'Insufficient information for classification', color: '#ba68c8' }
          }
          return { icon: '🔹', className: 'Fragment', meaning: 'Pieces created by breakup/collision', color: '#4fc3f7' }
        })()

        return (
          <div className="modal-overlay" onClick={() => setSelectedDebris(null)}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>{clsInfo.icon} Debris Details & Classification</h3>
                <button className="modal-close" onClick={() => setSelectedDebris(null)}>×</button>
              </div>
              <div className="modal-body">
                {/* Classification Highlight Card */}
                <div style={{
                  padding: '12px 16px',
                  marginBottom: '16px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${clsInfo.color}55`,
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px'
                }}>
                  <div style={{ fontSize: '2rem' }}>{clsInfo.icon}</div>
                  <div>
                    <div style={{ color: clsInfo.color, fontWeight: 'bold', fontSize: '1.05rem' }}>
                      {clsInfo.className}
                    </div>
                    <div style={{ color: '#aaa', fontSize: '0.85rem' }}>
                      {clsInfo.meaning}
                    </div>
                  </div>
                </div>

                <div className="details-grid">
                  <div className="detail-item"><span className="detail-label">Name / Classification:</span><span className="detail-value" style={{ color: '#64ffda' }}>{selectedDebris.name_classification || `${selectedDebris.name} / ${clsInfo.icon} ${clsInfo.className}`}</span></div>
                  <div className="detail-item"><span className="detail-label">NORAD ID:</span><span className="detail-value">{selectedDebris.norad_id}</span></div>
                  <div className="detail-item"><span className="detail-label">Primary Class:</span><span className="detail-value" style={{ color: clsInfo.color }}>{clsInfo.icon} {clsInfo.className}</span></div>
                  <div className="detail-item"><span className="detail-label">Meaning:</span><span className="detail-value">{clsInfo.meaning}</span></div>
                  <div className="detail-item"><span className="detail-label">Country:</span><span className="detail-value">{selectedDebris.country || 'N/A'}</span></div>
                  <div className="detail-item"><span className="detail-label">Altitude / Perigee & Apogee:</span><span className="detail-value">{selectedDebris.mean_altitude != null ? `${Number(selectedDebris.mean_altitude).toFixed(1)} km (Perigee: ${selectedDebris.perigee_km != null ? Number(selectedDebris.perigee_km).toFixed(1) : '—'} km / Apogee: ${selectedDebris.apogee_km != null ? Number(selectedDebris.apogee_km).toFixed(1) : '—'} km)` : (selectedDebris.apogee_km != null ? `Perigee: ${selectedDebris.perigee_km} km / Apogee: ${selectedDebris.apogee_km} km` : 'N/A')}</span></div>
                  <div className="detail-item"><span className="detail-label">Inclination:</span><span className="detail-value">{selectedDebris.inclination_deg != null ? `${Number(selectedDebris.inclination_deg).toFixed(2)}°` : 'N/A'}</span></div>
                  <div className="detail-item"><span className="detail-label">Period:</span><span className="detail-value">{selectedDebris.period_minutes != null ? `${Number(selectedDebris.period_minutes).toFixed(2)} min` : 'N/A'}</span></div>
                  <div className="detail-item"><span className="detail-label">Eccentricity:</span><span className="detail-value" style={{ fontFamily: 'monospace' }}>{selectedDebris.eccentricity != null ? (typeof selectedDebris.eccentricity === 'number' ? selectedDebris.eccentricity.toFixed(6) : selectedDebris.eccentricity) : 'N/A'}</span></div>
                  <div className="detail-item"><span className="detail-label">RCS Size:</span><span className="detail-value">{selectedDebris.rcs_size || 'N/A'}</span></div>
                  <div className="detail-item"><span className="detail-label">Launch Date:</span><span className="detail-value">{selectedDebris.launch_date || 'N/A'}</span></div>
                </div>
              </div>
            </div>
          </div>
        )
      })()}
    </div>
  )
}
