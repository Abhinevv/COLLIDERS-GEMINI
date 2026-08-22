import { useEffect, useState, useMemo } from 'react'
import { searchSpaceDebris, getHighRiskDebris, getRecentDebris, getDebrisDetails, addDebrisByNorad, getAllSpaceDebris } from '../api'

export default function DebrisTracker({ onNavigate }) {
  const [activeView, setActiveView] = useState('all') // 'all', 'search', 'high-risk', 'recent', 'add'
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [highRiskDebris, setHighRiskDebris] = useState([])
  const [recentDebris, setRecentDebris] = useState([])
  const [allDebris, setAllDebris] = useState([])
  const [selectedDebris, setSelectedDebris] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [categoryFilter, setCategoryFilter] = useState('ALL')

  // Add debris by NORAD
  const [debrisNorad, setDebrisNorad] = useState('')
  const [addingDebris, setAddingDebris] = useState(false)
  const [debrisResult, setDebrisResult] = useState(null)
  const [addSuccess, setAddSuccess] = useState(null)

  useEffect(() => {
    if (activeView === 'all') loadAllDebris()
    else if (activeView === 'high-risk') loadHighRiskDebris()
    else if (activeView === 'recent') loadRecentDebris()
    else if (activeView === 'add') { setDebrisResult(null); setAddSuccess(null); setError(null) }
  }, [activeView])

  async function loadAllDebris() {
    setLoading(true); setError(null)
    try {
      const data = await getAllSpaceDebris()
      setAllDebris(data.debris || data.recent_debris || [])
    } catch (err) {
      console.warn('Could not fetch all debris:', err)
      loadRecentDebris()
    } finally { setLoading(false) }
  }

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
      setAddSuccess(`Debris NORAD ${debrisNorad} verified successfully in database`)
      setDebrisNorad('')
      loadAllDebris()
    } catch (err) { setError(err.message) }
    finally { setAddingDebris(false) }
  }

  const filteredAllDebris = useMemo(() => {
    let list = allDebris

    if (categoryFilter !== 'ALL') {
      list = list.filter(d => {
        const typeStr = (d.type || '').toUpperCase()
        if (categoryFilter === 'FRAGMENT') return typeStr.includes('FRAG') || typeStr.includes('DEB')
        if (categoryFilter === 'ROCKET') return typeStr.includes('ROCKET') || typeStr.includes('R/B') || typeStr.includes('STAGE')
        if (categoryFilter === 'DEFUNCT') return typeStr.includes('DEFUNCT') || typeStr.includes('PAYLOAD') || typeStr.includes('SAT')
        return true
      })
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      list = list.filter(d =>
        (d.name && d.name.toLowerCase().includes(q)) ||
        (d.norad_id && String(d.norad_id).includes(q)) ||
        (d.type && d.type.toLowerCase().includes(q)) ||
        (d.country && d.country.toLowerCase().includes(q))
      )
    }

    return list
  }, [allDebris, categoryFilter, searchQuery])

  function renderDebrisList(debrisList) {
    if (loading) return (
      <div className="loading-container"><div className="spinner"></div><p>Loading space debris catalog...</p></div>
    )
    if (error) return <div className="error-message">Error: {error}</div>
    if (!debrisList || debrisList.length === 0) return <div className="empty-message">No debris objects found</div>

    return (
      <div className="debris-list">
        {debrisList.map((debris, idx) => (
          <div key={debris.norad_id || idx} className="debris-item">
            <div className="debris-header">
              <h4>{debris.name || 'Unknown'}</h4>
              <span className="debris-badge">{debris.type || 'DEBRIS'}</span>
            </div>
            <div className="debris-details">
              <div className="detail-row"><span className="detail-label">NORAD ID:</span><span className="detail-value">{debris.norad_id || 'N/A'}</span></div>
              <div className="detail-row"><span className="detail-label">Country:</span><span className="detail-value">{debris.country || 'N/A'}</span></div>
              <div className="detail-row"><span className="detail-label">Inclination:</span><span className="detail-value">{debris.inclination_deg ? `${debris.inclination_deg}°` : 'N/A'}</span></div>
              <div className="detail-row"><span className="detail-label">Period:</span><span className="detail-value">{debris.period_minutes ? `${Number(debris.period_minutes).toFixed(1)} min` : 'N/A'}</span></div>
            </div>
            
            <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
              <button className="view-details-btn" style={{ flex: 1 }} onClick={() => viewDebrisDetails(debris.norad_id)}>
                View Details
              </button>
              {onNavigate && (
                <button
                  className="search-btn"
                  style={{
                    padding: '6px 10px',
                    fontSize: '0.78rem',
                    background: 'rgba(61, 220, 132, 0.15)',
                    borderColor: '#3ddc84',
                    color: '#3ddc84'
                  }}
                  onClick={() => onNavigate('ibs')}
                  title="Simulate IBS deorbit removal for this debris"
                >
                  ⚡ Deorbit
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="debris-tracker">
      <div className="tracker-header">
        <h2>🛸 Space Debris Tracker & Catalog</h2>
        <p>Comprehensive orbital debris tracking catalog powered by Space-Track.org</p>
      </div>

      <div className="view-tabs">
        <button className={`view-tab ${activeView === 'all' ? 'active' : ''}`} onClick={() => setActiveView('all')}>
          🌐 Catalog Debris ({allDebris.length || 826})
        </button>
        <button className={`view-tab ${activeView === 'search' ? 'active' : ''}`} onClick={() => setActiveView('search')}>
          🔍 Search
        </button>
        <button className={`view-tab ${activeView === 'high-risk' ? 'active' : ''}`} onClick={() => setActiveView('high-risk')}>
          ⚠️ High Risk
        </button>
        <button className={`view-tab ${activeView === 'recent' ? 'active' : ''}`} onClick={() => setActiveView('recent')}>
          🆕 Recent
        </button>
        <button className={`view-tab ${activeView === 'add' ? 'active' : ''}`} onClick={() => setActiveView('add')}>
          🪨 Add by NORAD
        </button>
      </div>

      {activeView === 'all' && (
        <div className="search-section">
          {/* Filter Bar */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="🔍 Instant filter by name, NORAD ID, type, or country..."
                className="search-input"
                style={{ flex: 1 }}
              />
              <button className="refresh-btn" onClick={loadAllDebris} disabled={loading}>
                {loading ? '⏳ Loading...' : '🔄 Refresh Catalog'}
              </button>
            </div>

            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {[
                { key: 'ALL', label: `All Objects (${allDebris.length || 826})` },
                { key: 'FRAGMENT', label: '🔹 Fragments' },
                { key: 'ROCKET', label: '🚀 Rocket Bodies' },
                { key: 'DEFUNCT', label: '⚫ Defunct Satellites' },
              ].map(cat => (
                <button
                  key={cat.key}
                  type="button"
                  className={`view-tab ${categoryFilter === cat.key ? 'active' : ''}`}
                  style={{ padding: '4px 12px', fontSize: '0.78rem', margin: 0 }}
                  onClick={() => setCategoryFilter(cat.key)}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: '10px', fontSize: '0.85rem', color: '#8aafd4' }}>
            Showing <strong>{filteredAllDebris.length}</strong> cataloged debris objects
          </div>

          {renderDebrisList(filteredAllDebris)}
        </div>
      )}

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
            <h4>Quick Debris Examples</h4>
            <div className="hint-grid" style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '10px' }}>
              {[
                { id: '44120', name: 'PSLV C-45 DEB (🔹 Fragment)' },
                { id: '44858', name: 'PSLV R/B Stage-4 (🚀 Rocket Body)' },
                { id: '28944', name: 'Resourcesat-1 DEB (🔹 Fragment)' },
                { id: '44100', name: 'Microsat-R DEB (🔹 Fragment)' },
                { id: '27386', name: 'ENVISAT Derelict (⚫ Defunct Sat)' },
                { id: '33760', name: 'Cosmos 2251 DEB (🔹 Fragment)' },
              ].map(d => (
                <button 
                  key={d.id} 
                  type="button"
                  className="hint-chip" 
                  style={{
                    background: 'rgba(77, 163, 255, 0.12)',
                    border: '1px solid rgba(77, 163, 255, 0.35)',
                    color: '#4da3ff',
                    padding: '6px 12px',
                    borderRadius: '20px',
                    cursor: 'pointer',
                    fontSize: '0.85rem'
                  }}
                  onClick={() => setDebrisNorad(d.id)}
                >
                  {d.name} ({d.id})
                </button>
              ))}
            </div>
            <p style={{ marginTop: '12px', fontSize: '0.85rem', color: '#8aafd4' }}>
              Or enter any catalog ID from the database / <a href="https://www.space-track.org" target="_blank" rel="noopener noreferrer" style={{ color: '#4da3ff' }}>Space-Track.org</a>.
            </p>
          </div>
        </div>
      )}

      {selectedDebris && (() => {
        const clsInfo = (() => {
          const typeStr = (selectedDebris.classification || selectedDebris.type || '').toUpperCase()
          const nameStr = (selectedDebris.name || '').toUpperCase()
          if (typeStr.includes('ROCKET') || typeStr.includes('R/B') || nameStr.includes(' R/B') || nameStr.includes('STAGE') || nameStr.includes('TRANSTAGE') || nameStr.includes('ARIANE R/B') || nameStr.includes('PSLV R/B') || nameStr.includes('GSLV R/B')) {
            return { icon: '🚀', className: 'Rocket Body', meaning: 'Spent upper stage / launch vehicle body', color: '#ffaa33' }
          }
          if (typeStr.includes('FRAGMENT') || typeStr.includes('DEB') || nameStr.includes('DEB') || nameStr.includes('OBJ-') || nameStr.includes('BREAKUP') || nameStr.includes('COLLISION')) {
            return { icon: '🔹', className: 'Fragment', meaning: 'Pieces created by breakup/collision', color: '#4da3ff' }
          }
          if (typeStr.includes('DEFUNCT') || typeStr.includes('DERELICT') || nameStr.includes('DEFUNCT') || nameStr.includes('DERELICT') || nameStr.includes('ENVISAT')) {
            return { icon: '⚫', className: 'Defunct Satellite', meaning: 'Satellite no longer operational', color: '#8aafd4' }
          }
          if (typeStr.includes('SATELLITE') || typeStr.includes('PAYLOAD') || typeStr.includes('WEATHER') || typeStr.includes('EARTH OBSERVATION') || typeStr.includes('NAVIGATION') || typeStr.includes('COMMUNICATION') || typeStr.includes('SPACE SCIENCE')) {
            return { icon: '🛰️', className: 'Active Satellite', meaning: 'Currently operational spacecraft', color: '#3ddc84' }
          }
          return { icon: '🔹', className: 'Fragment', meaning: 'Pieces created by breakup/collision', color: '#4da3ff' }
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
                  background: 'rgba(4, 10, 22, 0.95)',
                  border: `1px solid ${clsInfo.color}66`,
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
                    <div style={{ color: '#8aafd4', fontSize: '0.85rem' }}>
                      {clsInfo.meaning}
                    </div>
                  </div>
                </div>

                <div className="details-grid">
                  <div className="detail-item"><span className="detail-label">Name / Classification:</span><span className="detail-value" style={{ color: '#4da3ff' }}>{selectedDebris.name_classification || `${selectedDebris.name} / ${clsInfo.icon} ${clsInfo.className}`}</span></div>
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
