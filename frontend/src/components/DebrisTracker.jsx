import { useEffect, useState } from 'react'
import { searchSpaceDebris, getHighRiskDebris, getRecentDebris, getDebrisDetails, refreshSpaceDebris } from '../api'
import { addStaggeredAnimations } from '../utils/useIntersectionObserver'

export default function DebrisTracker() {
  const [activeView, setActiveView] = useState('search')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [highRiskDebris, setHighRiskDebris] = useState([])
  const [recentDebris, setRecentDebris] = useState([])
  const [selectedDebris, setSelectedDebris] = useState(null)
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [refreshMessage, setRefreshMessage] = useState('')

  useEffect(() => {
    if (activeView === 'high-risk') {
      loadHighRiskDebris()
    } else if (activeView === 'recent') {
      loadRecentDebris()
    }
  }, [activeView])

  useEffect(() => {
    // Add entrance animations to debris items
    if (!loading) {
      const cleanup = addStaggeredAnimations('.debris-item', 100)
      return () => cleanup?.()
    }
  }, [loading, searchResults, highRiskDebris, recentDebris])

  async function loadHighRiskDebris() {
    setLoading(true)
    setError(null)
    try {
      const data = await getHighRiskDebris()
      setHighRiskDebris(data.high_risk_debris || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadRecentDebris() {
    setLoading(true)
    setError(null)
    try {
      const data = await getRecentDebris()
      setRecentDebris(data.recent_debris || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSearch(e) {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setLoading(true)
    setError(null)
    try {
      const data = await searchSpaceDebris(searchQuery)
      setSearchResults(data.debris || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function viewDebrisDetails(noradId) {
    setLoading(true)
    setError(null)
    try {
      const data = await getDebrisDetails(noradId)
      setSelectedDebris(data.debris)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleRefresh() {
    setRefreshing(true)
    setError(null)
    setRefreshMessage('')
    try {
      const data = await refreshSpaceDebris()

      if (activeView === 'high-risk') {
        await loadHighRiskDebris()
      } else if (activeView === 'recent') {
        await loadRecentDebris()
      } else if (searchQuery.trim()) {
        const searchData = await searchSpaceDebris(searchQuery)
        setSearchResults(searchData.debris || [])
      }

      setRefreshMessage(data.message || 'Debris data refreshed')
    } catch (err) {
      setError(err.message)
    } finally {
      setRefreshing(false)
    }
  }

  function renderDebrisList(debrisList) {
    if (loading) {
      return (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading debris data...</p>
        </div>
      )
    }

    if (error) {
      return <div className="error-message">Error: {error}</div>
    }

    if (!debrisList || debrisList.length === 0) {
      return <div className="empty-message">No debris found</div>
    }

    return (
      <div className="debris-list">
        {debrisList.map((debris, idx) => (
          <div key={debris.norad_id || idx} className="debris-item">
            <div className="debris-header">
              <h4>{debris.name || 'Unknown'}</h4>
              <span className="debris-badge">{debris.type || 'N/A'}</span>
            </div>
            <div className="debris-details">
              <div className="detail-row">
                <span className="detail-label">NORAD ID:</span>
                <span className="detail-value">{debris.norad_id || 'N/A'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Country:</span>
                <span className="detail-value">{debris.country || 'N/A'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Inclination:</span>
                <span className="detail-value">{debris.inclination_deg ? `${debris.inclination_deg}°` : 'N/A'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Period:</span>
                <span className="detail-value">{debris.period_minutes ? `${debris.period_minutes} min` : 'N/A'}</span>
              </div>
            </div>
            <button 
              className="view-details-btn"
              onClick={() => viewDebrisDetails(debris.norad_id)}
            >
              View Details
            </button>
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
        <button
          className="search-btn"
          onClick={handleRefresh}
          disabled={refreshing}
          type="button"
        >
          {refreshing ? 'Refreshing...' : 'Refresh Debris'}
        </button>
        {refreshMessage && <div className="success-message">{refreshMessage}</div>}
      </div>

      <div className="view-tabs">
        <button 
          className={`view-tab ${activeView === 'search' ? 'active' : ''}`}
          onClick={() => setActiveView('search')}
        >
          🔍 Search
        </button>
        <button 
          className={`view-tab ${activeView === 'high-risk' ? 'active' : ''}`}
          onClick={() => setActiveView('high-risk')}
        >
          ⚠️ High Risk
        </button>
        <button 
          className={`view-tab ${activeView === 'recent' ? 'active' : ''}`}
          onClick={() => setActiveView('recent')}
        >
          🆕 Recent
        </button>
      </div>

      {activeView === 'search' && (
        <div className="search-section">
          <form onSubmit={handleSearch} className="search-form">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by type (debris, rocket_body, payload)..."
              className="search-input"
            />
            <button type="submit" className="search-btn">
              Search
            </button>
          </form>
          {renderDebrisList(searchResults)}
        </div>
      )}

      {activeView === 'high-risk' && (
        <div className="high-risk-section">
          <div className="section-info">
            <h3>High-Risk Debris in LEO</h3>
            <p>Debris objects in Low Earth Orbit (200-2000 km altitude)</p>
          </div>
          {renderDebrisList(highRiskDebris)}
        </div>
      )}

      {activeView === 'recent' && (
        <div className="recent-section">
          <div className="section-info">
            <h3>Recently Cataloged Debris</h3>
            <p>Newly tracked debris objects from the last 30 days</p>
          </div>
          {renderDebrisList(recentDebris)}
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
                <div className="detail-item">
                  <span className="detail-label">Name:</span>
                  <span className="detail-value">{selectedDebris.name}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">NORAD ID:</span>
                  <span className="detail-value">{selectedDebris.norad_id}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Type:</span>
                  <span className="detail-value">{selectedDebris.type}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Country:</span>
                  <span className="detail-value">{selectedDebris.country}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Launch Date:</span>
                  <span className="detail-value">{selectedDebris.launch_date || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Epoch:</span>
                  <span className="detail-value">{selectedDebris.epoch || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Period:</span>
                  <span className="detail-value">{selectedDebris.period_minutes ? `${selectedDebris.period_minutes} min` : 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Inclination:</span>
                  <span className="detail-value">{selectedDebris.inclination_deg ? `${selectedDebris.inclination_deg}°` : 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Eccentricity:</span>
                  <span className="detail-value">{selectedDebris.eccentricity || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Mean Motion:</span>
                  <span className="detail-value">{selectedDebris.mean_motion || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">RCS Size:</span>
                  <span className="detail-value">{selectedDebris.rcs_size || 'N/A'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
