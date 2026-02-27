import { useState } from 'react'
import Dashboard from './components/Dashboard'
import DebrisTracker from './components/DebrisTracker'
import CollisionAnalysis from './components/CollisionAnalysis'
import RiskRanking from './components/RiskRanking'
import SatelliteRiskProfile from './components/SatelliteRiskProfile'
import Alerts from './components/Alerts'
import ManeuverPlanner from './components/ManeuverPlanner'
import ErrorBoundary from './components/ErrorBoundary'
import Toast from './components/Toast'
import './styles.css'

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="app">
      <Toast />
      <header className="app-header">
        <div className="header-content">
          <h1>🛰️ AstroCleanAI</h1>
          <p>Space Debris Tracking & Collision Avoidance System</p>
        </div>
        <nav className="nav-tabs">
          <button 
            className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={`nav-tab ${activeTab === 'debris' ? 'active' : ''}`}
            onClick={() => setActiveTab('debris')}
          >
            🛸 Debris Tracker
          </button>
          <button 
            className={`nav-tab ${activeTab === 'collision' ? 'active' : ''}`}
            onClick={() => setActiveTab('collision')}
          >
            ⚠️ Collision Analysis
          </button>
          <button 
            className={`nav-tab ${activeTab === 'ranking' ? 'active' : ''}`}
            onClick={() => setActiveTab('ranking')}
          >
            🏆 Risk Ranking
          </button>
          <button 
            className={`nav-tab ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            🛰️ Satellite Profile
          </button>
          <button 
            className={`nav-tab ${activeTab === 'alerts' ? 'active' : ''}`}
            onClick={() => setActiveTab('alerts')}
          >
            🔔 Alerts
          </button>
          <button 
            className={`nav-tab ${activeTab === 'maneuver' ? 'active' : ''}`}
            onClick={() => setActiveTab('maneuver')}
          >
            🚀 Maneuvers
          </button>
        </nav>
      </header>

      <main className="app-main">
        <ErrorBoundary>
          {activeTab === 'dashboard' && <Dashboard onNavigate={setActiveTab} />}
          {activeTab === 'debris' && <DebrisTracker />}
          {activeTab === 'collision' && <CollisionAnalysis />}
          {activeTab === 'ranking' && <RiskRanking />}
          {activeTab === 'profile' && <SatelliteRiskProfile />}
          {activeTab === 'alerts' && <Alerts />}
          {activeTab === 'maneuver' && <ManeuverPlanner />}
        </ErrorBoundary>
      </main>

      <footer className="app-footer">
        <p>AstroCleanAI - Making space safer through intelligent collision avoidance</p>
        <p className="footer-links">
          <a href="http://localhost:5000/api/docs" target="_blank" rel="noopener noreferrer">API Docs</a>
          {' • '}
          <a href="https://www.space-track.org" target="_blank" rel="noopener noreferrer">Space-Track.org</a>
        </p>
      </footer>
    </div>
  )
}
