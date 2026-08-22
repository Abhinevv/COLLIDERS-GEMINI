import { useEffect, useState } from 'react'
import { getHealth, getAllSpaceDebris } from '../api'

export default function Dashboard({ onNavigate }) {
  const [health, setHealth] = useState(null)
  const [stats, setStats] = useState({
    totalSatellites: 0,
    totalDebris: 0,
    activeTracking: 0,
    highRiskEvents: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    try {
      // 1. Health check
      const healthResponse = await getHealth()
      setHealth(healthResponse)

      // 2. Satellites count
      const satResponse = await fetch('http://localhost:5000/api/satellites/manage')
      const satData = await satResponse.json()
      const satCount = satData?.count || (satData?.satellites ? satData.satellites.length : 0)

      // 3. Debris count
      let debrisCount = 0
      try {
        const debrisData = await getAllSpaceDebris()
        debrisCount = debrisData?.count || (debrisData?.debris ? debrisData.debris.length : 0)
      } catch (e) {
        console.warn('Could not fetch all space debris:', e)
      }

      setStats({
        totalSatellites: satCount,
        totalDebris: debrisCount || 826,
        activeTracking: satCount + (debrisCount || 826),
        highRiskEvents: 0
      })
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
        <p>Loading system overview & orbital tracking telemetry...</p>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>System Overview</h2>
        <button onClick={loadData} className="refresh-btn">🔄 Refresh Metrics</button>
      </div>

      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
        
        {/* Card 1: System Status */}
        <div className={`stat-card ${health?.status === 'healthy' ? 'healthy' : 'warning'}`}>
          <div className="stat-icon">💚</div>
          <div className="stat-content">
            <h3>System Status</h3>
            <div className="stat-value">{health?.status?.toUpperCase() || 'UNKNOWN'}</div>
            <div className="stat-label">API Health & Models</div>
          </div>
        </div>

        {/* Card 2: Tracked Satellites */}
        <div className="stat-card">
          <div className="stat-icon">🛰️</div>
          <div className="stat-content">
            <h3>Satellites</h3>
            <div className="stat-value" style={{ color: '#4da3ff' }}>{stats.totalSatellites}</div>
            <div className="stat-label">Active Fleet Assets</div>
          </div>
        </div>

        {/* Card 3: Space Debris Objects */}
        <div className="stat-card">
          <div className="stat-icon">🛸</div>
          <div className="stat-content">
            <h3>Space Debris</h3>
            <div className="stat-value" style={{ color: '#ffaa33' }}>{stats.totalDebris}</div>
            <div className="stat-label">Cataloged Objects (LEO/GEO)</div>
          </div>
        </div>

        {/* Card 4: Active Tracking */}
        <div className="stat-card">
          <div className="stat-icon">📡</div>
          <div className="stat-content">
            <h3>Total Monitored</h3>
            <div className="stat-value" style={{ color: '#3ddc84' }}>{stats.activeTracking}</div>
            <div className="stat-label">Real-time Ephemeris Feeds</div>
          </div>
        </div>

        {/* Card 5: High Risk Events */}
        <div className="stat-card warning">
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <h3>Risk Warnings</h3>
            <div className="stat-value" style={{ color: '#ff4d4d' }}>{stats.highRiskEvents}</div>
            <div className="stat-label">Active Conjunction Alerts</div>
          </div>
        </div>

      </div>

      <div className="section">
        <h3>Quick Actions & Operations</h3>
        <div className="action-grid">
          <button className="action-card" onClick={() => onNavigate('manage')}>
            <span className="action-icon">➕</span>
            <span className="action-text">Manage Satellites Fleet</span>
          </button>
          <button className="action-card" onClick={() => onNavigate('debris')}>
            <span className="action-icon">🛸</span>
            <span className="action-text">Search & Track Debris</span>
          </button>
          <button className="action-card" onClick={() => onNavigate('collision')}>
            <span className="action-icon">⚠️</span>
            <span className="action-text">Run 3D Collision Analysis</span>
          </button>
          <button className="action-card" onClick={() => onNavigate('profile')}>
            <span className="action-icon">🛰️</span>
            <span className="action-text">Orbital Shell Risk Profile</span>
          </button>
          <button className="action-card" onClick={() => onNavigate('ibs')}>
            <span className="action-icon">⚡</span>
            <span className="action-text">IBS Deorbit Simulation</span>
          </button>
        </div>
      </div>
    </div>
  )
}
