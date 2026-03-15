import { useEffect, useState } from 'react'
import { getHealth } from '../api'

export default function Dashboard({ onNavigate }) {
  const [health, setHealth] = useState(null)
  const [stats, setStats] = useState({
    totalSatellites: 0,
    activeTracking: 0,
    highRiskEvents: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    try {
      const healthResponse = await getHealth()
      setHealth(healthResponse)

      const satResponse = await fetch('http://localhost:5000/api/satellites/manage')
      const satData = await satResponse.json()
      if (satData && satData.satellites) {
        setStats(prev => ({ ...prev, totalSatellites: satData.count, activeTracking: satData.count }))
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
        <button onClick={loadData} className="refresh-btn">🔄 Refresh</button>
      </div>

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
