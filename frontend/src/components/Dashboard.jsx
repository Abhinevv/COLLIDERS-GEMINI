import { useEffect, useState } from 'react'
import { getHealth, getManagedSatellites, getCatalogSatellites, addManagedSatellite } from '../api'
import { addStaggeredAnimations } from '../utils/useIntersectionObserver'

function Icon({ children }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="ui-icon-svg" aria-hidden="true">
      {children}
    </svg>
  )
}

function IconShell({ tone = 'primary', children }) {
  return <span className={`ui-icon-shell ui-icon-${tone}`}>{children}</span>
}

export default function Dashboard({ onNavigate }) {
  const [health, setHealth] = useState(null)
  const [satellites, setSatellites] = useState([])
  const [stats, setStats] = useState({
    totalSatellites: 0,
    activeTracking: 0,
    debrisObjects: 0,
    highRiskEvents: 0
  })
  const [loading, setLoading] = useState(true)
  const [catalogQuery, setCatalogQuery] = useState('')
  const [catalogResults, setCatalogResults] = useState([])
  const [catalogLoading, setCatalogLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [workingSatelliteId, setWorkingSatelliteId] = useState(null)

  useEffect(() => {
    loadData()
    loadCatalogSatellites()
  }, [])

  useEffect(() => {
    if (!loading) {
      const cleanupStats = addStaggeredAnimations('.stat-card', 100)
      const cleanupSatellites = addStaggeredAnimations('.satellite-card', 100)
      const cleanupActions = addStaggeredAnimations('.action-card', 100)

      return () => {
        cleanupStats?.()
        cleanupSatellites?.()
        cleanupActions?.()
      }
    }
  }, [loading])

  async function loadData() {
    setLoading(true)
    try {
      const healthResponse = await getHealth()
      setHealth(healthResponse)

      const satData = await getManagedSatellites()
      if (satData?.satellites) {
        setSatellites(satData.satellites)
        setStats((prev) => ({
          ...prev,
          totalSatellites: satData.count,
          activeTracking: satData.count
        }))
      }
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  async function loadCatalogSatellites(query = '') {
    setCatalogLoading(true)
    try {
      const data = await getCatalogSatellites(query, 8)
      setCatalogResults(data.satellites || [])
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setCatalogLoading(false)
    }
  }

  async function handleCatalogSearch(e) {
    e.preventDefault()
    setMessage(null)
    await loadCatalogSatellites(catalogQuery)
  }

  async function handleAddSatellite(satellite) {
    setWorkingSatelliteId(satellite.norad_id)
    setMessage(null)
    try {
      await addManagedSatellite({
        norad_id: satellite.norad_id,
        name: satellite.name,
        type: satellite.type,
        description: satellite.description,
        operator: satellite.operator
      })
      setMessage({ type: 'success', text: `${satellite.name} added to tracking.` })
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setWorkingSatelliteId(null)
    }
  }

  async function handleRemoveSatellite(noradId, name) {
    setWorkingSatelliteId(noradId)
    setMessage(null)
    try {
      const res = await fetch(`http://localhost:5000/api/satellites/manage/${noradId}`, {
        method: 'DELETE'
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Remove satellite failed: ${res.status} ${text}`)
      }
      setMessage({ type: 'success', text: `${name} removed from tracking.` })
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setWorkingSatelliteId(null)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="header-title-section">
          <h2 className="gradient-text">System Overview</h2>
          <p className="header-subtitle">Real-time monitoring and control center</p>
        </div>
        <button onClick={loadData} className="refresh-btn modern-btn">
          <IconShell tone="neutral">
            <Icon>
              <path d="M20 12a8 8 0 1 1-2.35-5.65" />
              <path d="M20 5v5h-5" />
            </Icon>
          </IconShell>
          <span>Refresh Data</span>
        </button>
      </div>

      <div className="stats-grid">
        <div className={`stat-card glass-effect ${health?.status === 'healthy' ? 'healthy' : 'warning'}`}>
          <div className="stat-icon-wrapper">
            <div className="stat-icon">
              {health?.status === 'healthy' ? (
                <IconShell tone="success">
                  <Icon>
                    <circle cx="12" cy="12" r="8.5" />
                    <path d="m8.5 12 2.5 2.5 4.5-5" />
                  </Icon>
                </IconShell>
              ) : (
                <IconShell tone="warning">
                  <Icon>
                    <path d="M12 3 2.5 19h19L12 3z" />
                    <path d="M12 9v4" />
                    <circle cx="12" cy="16.5" r=".7" fill="currentColor" stroke="none" />
                  </Icon>
                </IconShell>
              )}
            </div>
          </div>
          <div className="stat-content">
            <h3>System Status</h3>
            <div className="stat-value gradient-text">
              {health?.status ? health.status.charAt(0).toUpperCase() + health.status.slice(1) : 'Unknown'}
            </div>
            <div className="stat-label">API Health Check</div>
          </div>
        </div>

        <div className="stat-card glass-effect">
          <div className="stat-icon-wrapper">
            <div className="stat-icon">
              <IconShell tone="primary">
                <Icon>
                  <ellipse cx="12" cy="12" rx="7.5" ry="3.5" />
                  <path d="M12 6.5v11" />
                  <path d="M7.5 9.5 16.5 14.5" />
                  <path d="M16.5 9.5 7.5 14.5" />
                </Icon>
              </IconShell>
            </div>
          </div>
          <div className="stat-content">
            <h3>Total Satellites</h3>
            <div className="stat-value gradient-text">{stats.totalSatellites}</div>
            <div className="stat-label">Tracked Objects</div>
          </div>
        </div>

        <div className="stat-card glass-effect">
          <div className="stat-icon-wrapper">
            <div className="stat-icon">
              <IconShell tone="info">
                <Icon>
                  <path d="M4 14a8 8 0 0 1 16 0" />
                  <path d="M7.5 14a4.5 4.5 0 0 1 9 0" />
                  <circle cx="12" cy="14" r="1.3" />
                </Icon>
              </IconShell>
            </div>
          </div>
          <div className="stat-content">
            <h3>Active Tracking</h3>
            <div className="stat-value gradient-text">{stats.activeTracking}</div>
            <div className="stat-label">Real-time Monitoring</div>
          </div>
        </div>

        <div className="stat-card glass-effect warning">
          <div className="stat-icon-wrapper">
            <div className="stat-icon">
              <IconShell tone="danger">
                <Icon>
                  <path d="M12 3 2.5 19h19L12 3z" />
                  <path d="M12 9v4" />
                  <circle cx="12" cy="16.5" r=".7" fill="currentColor" stroke="none" />
                </Icon>
              </IconShell>
            </div>
          </div>
          <div className="stat-content">
            <h3>Risk Events</h3>
            <div className="stat-value gradient-text">{stats.highRiskEvents}</div>
            <div className="stat-label">Collision Warnings</div>
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-header">
          <h3 className="gradient-text">Tracked Satellites</h3>
          <span className="section-badge">{satellites.length} Active</span>
        </div>
        {satellites.length > 0 ? (
          <div className="satellite-grid">
            {satellites.map((sat) => (
              <div key={sat.norad_id} className="satellite-card glass-effect hover-lift">
                <div className="satellite-header">
                  <h4>{sat.name}</h4>
                  <span className="satellite-badge">{sat.type}</span>
                </div>
                <div className="satellite-details">
                  <div className="detail-row">
                    <span className="detail-label">NORAD ID</span>
                    <span className="detail-value">{sat.norad_id}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Type</span>
                    <span className="detail-value">{sat.type}</span>
                  </div>
                  {sat.description && <p className="satellite-description">{sat.description}</p>}
                </div>
                <button
                  type="button"
                  className="remove-satellite-btn"
                  disabled={workingSatelliteId === sat.norad_id}
                  onClick={() => handleRemoveSatellite(sat.norad_id, sat.name)}
                >
                  {workingSatelliteId === sat.norad_id ? 'Removing...' : 'Remove'}
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state glass-effect">
            <div className="empty-icon">
              <IconShell tone="neutral">
                <Icon>
                  <ellipse cx="12" cy="12" rx="7.5" ry="3.5" />
                  <path d="M12 6.5v11" />
                  <path d="M7.5 9.5 16.5 14.5" />
                  <path d="M16.5 9.5 7.5 14.5" />
                </Icon>
              </IconShell>
            </div>
            <h3>No Satellites Tracked</h3>
            <p>Add satellites to start monitoring</p>
          </div>
        )}

        <div className="dashboard-manage glass-effect">
          <div className="dashboard-manage-header">
            <div>
              <h3 className="gradient-text">Manage Satellites</h3>
              <p>Search the live catalog, add satellites to tracking, or remove tracked ones.</p>
            </div>
            <form className="catalog-search" onSubmit={handleCatalogSearch}>
              <input
                type="text"
                value={catalogQuery}
                onChange={(e) => setCatalogQuery(e.target.value)}
                placeholder="Search NORAD ID or satellite name"
                className="catalog-search-input"
              />
              <button type="submit" disabled={catalogLoading}>
                {catalogLoading ? 'Searching...' : 'Search'}
              </button>
            </form>
          </div>

          {message && (
            <div className={message.type === 'success' ? 'success-message' : 'error-message'}>
              {message.text}
            </div>
          )}

          <div className="catalog-grid">
            {catalogResults.map((sat) => {
              const alreadyManaged = satellites.some((tracked) => tracked.norad_id === sat.norad_id)
              return (
                <div key={sat.norad_id} className="catalog-card">
                  <div className="catalog-card-copy">
                    <strong>{sat.name}</strong>
                    <span>NORAD {sat.norad_id}</span>
                    <span>{sat.type || 'SATELLITE'}</span>
                  </div>
                  <button
                    type="button"
                    disabled={alreadyManaged || workingSatelliteId === sat.norad_id}
                    onClick={() => handleAddSatellite(sat)}
                  >
                    {alreadyManaged ? 'Added' : workingSatelliteId === sat.norad_id ? 'Adding...' : 'Add'}
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-header">
          <h3 className="gradient-text">Quick Actions</h3>
          <span className="section-badge">4 Available</span>
        </div>
        <div className="action-grid">
          <button className="action-card glass-effect hover-lift" onClick={() => onNavigate('debris')}>
            <div className="action-icon-wrapper">
              <span className="action-icon">
                <IconShell tone="primary">
                  <Icon>
                    <circle cx="10.5" cy="10.5" r="5.5" />
                    <path d="m15 15 4 4" />
                    <path d="M10.5 7.5v6" />
                    <path d="M7.5 10.5h6" />
                  </Icon>
                </IconShell>
              </span>
            </div>
            <span className="action-text">Search Debris</span>
            <span className="action-description">Find and track space debris</span>
          </button>
          <button className="action-card glass-effect hover-lift" onClick={() => window.open('/api/visualization/', '_blank')}>
            <div className="action-icon-wrapper">
              <span className="action-icon">
                <IconShell tone="info">
                  <Icon>
                    <path d="M2.5 12s3.5-5.5 9.5-5.5 9.5 5.5 9.5 5.5-3.5 5.5-9.5 5.5S2.5 12 2.5 12z" />
                    <circle cx="12" cy="12" r="2.5" />
                  </Icon>
                </IconShell>
              </span>
            </div>
            <span className="action-text">Visualizations</span>
            <span className="action-description">View orbital data charts</span>
          </button>
          <button className="action-card glass-effect hover-lift" onClick={() => onNavigate('collision')}>
            <div className="action-icon-wrapper">
              <span className="action-icon">
                <IconShell tone="success">
                  <Icon>
                    <circle cx="12" cy="12" r="8.5" />
                    <path d="m10 8 6 4-6 4V8z" />
                  </Icon>
                </IconShell>
              </span>
            </div>
            <span className="action-text">Run Analysis</span>
            <span className="action-description">Collision risk assessment</span>
          </button>
          <button className="action-card glass-effect hover-lift" onClick={() => window.open('/api/docs', '_blank')}>
            <div className="action-icon-wrapper">
              <span className="action-icon">
                <IconShell tone="neutral">
                  <Icon>
                    <path d="M7 3.5h7l3 3V20H7z" />
                    <path d="M14 3.5V7h3" />
                    <path d="M9.5 11h5" />
                    <path d="M9.5 14h5" />
                    <path d="M9.5 17h3.5" />
                  </Icon>
                </IconShell>
              </span>
            </div>
            <span className="action-text">API Docs</span>
            <span className="action-description">Developer documentation</span>
          </button>
        </div>
      </div>
    </div>
  )
}
