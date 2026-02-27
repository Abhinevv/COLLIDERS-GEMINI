import { useEffect, useState } from 'react'
import { getHealth } from '../api'

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
        <h2>System Overview</h2>
        <button onClick={loadData} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      {/* Status Cards */}
      <div className="stats-grid">
        <div className={`stat-card ${health?.status === 'healthy' ? 'healthy' : 'warning'}`}>
          <div className="stat-icon">💚</div>
          <div className="stat-content">
            <h3>System Status</h3>
            <div className="stat-value">{health?.status?.toUpperCase() || 'UNKNOWN'}</div>
            <div className="stat-label">API Health</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🛰️</div>
          <div className="stat-content">
            <h3>Satellites</h3>
            <div className="stat-value">{stats.totalSatellites}</div>
            <div className="stat-label">Tracked Objects</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📡</div>
          <div className="stat-content">
            <h3>Active Tracking</h3>
            <div className="stat-value">{stats.activeTracking}</div>
            <div className="stat-label">Real-time Monitoring</div>
          </div>
        </div>

        <div className="stat-card warning">
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <h3>High Risk Events</h3>
            <div className="stat-value">{stats.highRiskEvents}</div>
            <div className="stat-label">Collision Warnings</div>
          </div>
        </div>
      </div>

      {/* Satellite List */}
      <div className="section">
        <h3>Tracked Satellites</h3>
        <div className="satellite-grid">
          {satellites.map(sat => (
            <div key={sat.norad_id} className="satellite-card">
              <div className="satellite-header">
                <h4>{sat.name}</h4>
                <span className="satellite-badge">{sat.type}</span>
              </div>
              <div className="satellite-details">
                <div className="detail-row">
                  <span className="detail-label">NORAD ID:</span>
                  <span className="detail-value">{sat.norad_id}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Type:</span>
                  <span className="detail-value">{sat.type}</span>
                </div>
                <p className="satellite-description">{sat.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="section">
        <h3>Quick Actions</h3>
        <div className="action-grid">
          <button className="action-card" onClick={() => onNavigate('debris')}>
            <span className="action-icon">🔍</span>
            <span className="action-text">Search Debris</span>
          </button>
          <button className="action-card" onClick={() => window.open('/api/visualization/', '_blank')}>
            <span className="action-icon">📊</span>
            <span className="action-text">View Visualizations</span>
          </button>
          <button className="action-card" onClick={() => onNavigate('collision')}>
            <span className="action-icon">⚡</span>
            <span className="action-text">Run Analysis</span>
          </button>
          <button className="action-card" onClick={() => window.open('/api/docs', '_blank')}>
            <span className="action-icon">📥</span>
            <span className="action-text">API Documentation</span>
          </button>
        </div>
      </div>
    </div>
  )
}
