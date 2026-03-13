import { useEffect, useState } from 'react'
import { getHealth } from '../api'
import { addStaggeredAnimations } from '../utils/useIntersectionObserver'

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

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    // Add entrance animations to stat cards and satellite cards
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
      // Fetch health and managed satellites
      const healthResponse = await getHealth()
      setHealth(healthResponse)
      
      // Fetch managed satellites from database
      const satResponse = await fetch('http://localhost:5000/api/satellites/manage')
      const satData = await satResponse.json()
      
      if (satData && satData.satellites) {
        setSatellites(satData.satellites)
        setStats(prev => ({
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
          <span>🔄</span>
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Status Cards */}
      <div className="stats-grid">
        <div className={`stat-card glass-effect ${health?.status === 'healthy' ? 'healthy' : 'warning'}`}>
          <div className="stat-icon-wrapper">
            <div className="stat-icon">{health?.status === 'healthy' ? '✅' : '⚠️'}</div>
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
            <div className="stat-icon">🛰️</div>
          </div>
          <div className="stat-content">
            <h3>Total Satellites</h3>
            <div className="stat-value gradient-text">{stats.totalSatellites}</div>
            <div className="stat-label">Tracked Objects</div>
          </div>
        </div>

        <div className="stat-card glass-effect">
          <div className="stat-icon-wrapper">
            <div className="stat-icon">📡</div>
          </div>
          <div className="stat-content">
            <h3>Active Tracking</h3>
            <div className="stat-value gradient-text">{stats.activeTracking}</div>
            <div className="stat-label">Real-time Monitoring</div>
          </div>
        </div>

        <div className="stat-card glass-effect warning">
          <div className="stat-icon-wrapper">
            <div className="stat-icon">⚠️</div>
          </div>
          <div className="stat-content">
            <h3>Risk Events</h3>
            <div className="stat-value gradient-text">{stats.highRiskEvents}</div>
            <div className="stat-label">Collision Warnings</div>
          </div>
        </div>
      </div>

      {/* Satellite List */}
      <div className="section">
        <div className="section-header">
          <h3 className="gradient-text">Tracked Satellites</h3>
          <span className="section-badge">{satellites.length} Active</span>
        </div>
        {satellites.length > 0 ? (
          <div className="satellite-grid">
            {satellites.map(sat => (
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
                  {sat.description && (
                    <p className="satellite-description">{sat.description}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state glass-effect">
            <div className="empty-icon">🛰️</div>
            <h3>No Satellites Tracked</h3>
            <p>Add satellites to start monitoring</p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="section">
        <div className="section-header">
          <h3 className="gradient-text">Quick Actions</h3>
          <span className="section-badge">4 Available</span>
        </div>
        <div className="action-grid">
          <button className="action-card glass-effect hover-lift" onClick={() => onNavigate('debris')}>
            <div className="action-icon-wrapper">
              <span className="action-icon">🔍</span>
            </div>
            <span className="action-text">Search Debris</span>
            <span className="action-description">Find and track space debris</span>
          </button>
          <button className="action-card glass-effect hover-lift" onClick={() => window.open('/api/visualization/', '_blank')}>
            <div className="action-icon-wrapper">
              <span className="action-icon">📊</span>
            </div>
            <span className="action-text">Visualizations</span>
            <span className="action-description">View orbital data charts</span>
          </button>
          <button className="action-card glass-effect hover-lift" onClick={() => onNavigate('collision')}>
            <div className="action-icon-wrapper">
              <span className="action-icon">⚡</span>
            </div>
            <span className="action-text">Run Analysis</span>
            <span className="action-description">Collision risk assessment</span>
          </button>
          <button className="action-card glass-effect hover-lift" onClick={() => window.open('/api/docs', '_blank')}>
            <div className="action-icon-wrapper">
              <span className="action-icon">📚</span>
            </div>
            <span className="action-text">API Docs</span>
            <span className="action-description">Developer documentation</span>
          </button>
        </div>
      </div>
    </div>
  )
}
