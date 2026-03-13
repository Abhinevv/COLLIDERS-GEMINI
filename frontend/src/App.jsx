import { useState } from 'react'
import Dashboard from './components/Dashboard'
import DebrisTracker from './components/DebrisTracker'
import CollisionAnalysis from './components/CollisionAnalysis'
import RiskRanking from './components/RiskRanking'
import SatelliteRiskProfile from './components/SatelliteRiskProfile'
import EnhancedFeatures from './components/EnhancedFeatures'
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
          <h1>🛰️ COLLIDERS</h1>
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
            className={`nav-tab ${activeTab === 'enhanced' ? 'active' : ''}`}
            onClick={() => setActiveTab('enhanced')}
          >
            🔬 Enhanced Features
          </button>
          <button 
            className={`nav-tab ${activeTab === 'alerts' ? 'active' : ''}`}
            onClick={() => setActiveTab('alerts')}
          >
            🔔 Alerts
          </button>
        </nav>
      </header>

      <main className="app-main">
        <ErrorBoundary>
          <div style={{ display: activeTab === 'dashboard' ? 'block' : 'none' }}>
            <Dashboard onNavigate={setActiveTab} />
          </div>
          <div style={{ display: activeTab === 'debris' ? 'block' : 'none' }}>
            <DebrisTracker />
          </div>
          <div style={{ display: activeTab === 'collision' ? 'block' : 'none' }}>
            <CollisionAnalysis />
          </div>
          <div style={{ display: activeTab === 'ranking' ? 'block' : 'none' }}>
            <RiskRanking />
          </div>
          <div style={{ display: activeTab === 'profile' ? 'block' : 'none' }}>
            <SatelliteRiskProfile />
          </div>
          <div style={{ display: activeTab === 'enhanced' ? 'block' : 'none' }}>
            <EnhancedFeatures />
          </div>
          <div style={{ display: activeTab === 'alerts' ? 'block' : 'none' }}>
            <Alerts />
          </div>
          <div style={{ display: activeTab === 'maneuver' ? 'block' : 'none' }}>
            <ManeuverPlanner />
          </div>
        </ErrorBoundary>
      </main>

      <footer className="app-footer">
        <p>COLLIDERS - Making space safer through intelligent collision avoidance</p>
        <p className="footer-links">
          <a href="http://localhost:5000/api/docs" target="_blank" rel="noopener noreferrer">API Docs</a>
          {' • '}
          <a href="https://www.space-track.org" target="_blank" rel="noopener noreferrer">Space-Track.org</a>
        </p>
      </footer>
    </div>
  )
}
