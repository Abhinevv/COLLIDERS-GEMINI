import { useState } from 'react'
import Dashboard from './components/Dashboard'
import DebrisTracker from './components/DebrisTracker'
import CollisionAnalysis from './components/CollisionAnalysis'
import RiskRanking from './components/RiskRanking'
import DemoRiskShowcase from './components/DemoRiskShowcase'
import SatelliteRiskProfile from './components/SatelliteRiskProfile'
import EnhancedFeatures from './components/EnhancedFeatures'
import Alerts from './components/Alerts'
import ManeuverPlanner from './components/ManeuverPlanner'
import ErrorBoundary from './components/ErrorBoundary'
import Toast from './components/Toast'
import './styles.css'

function NavIcon({ children }) {
  return (
    <span className="nav-icon-shell" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="nav-icon-svg">
        {children}
      </svg>
    </span>
  )
}

function BrandIcon() {
  return (
    <span className="brand-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="brand-icon-svg">
        <path d="M6 9.5a3.5 3.5 0 1 1 3.5 3.5" />
        <path d="M14.5 11a3.5 3.5 0 1 1 3.5 3.5" />
        <path d="M9.5 11.5h5" />
        <path d="M8.5 6.2V4.5" />
        <path d="M15.5 19.5v-1.7" />
      </svg>
    </span>
  )
}

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="app">
      <Toast />
      <header className="app-header">
        <div className="header-content">
          <h1>
            <BrandIcon />
            COLLIDERS
          </h1>
          <p>Space Debris Tracking & Collision Avoidance System</p>
        </div>
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <NavIcon>
              <path d="M4 11.5 12 5l8 6.5" />
              <path d="M6.5 10.5V19h11v-8.5" />
              <path d="M10 19v-4.5h4V19" />
            </NavIcon>
            Dashboard
          </button>
          <button
            className={`nav-tab ${activeTab === 'debris' ? 'active' : ''}`}
            onClick={() => setActiveTab('debris')}
          >
            <NavIcon>
              <circle cx="10.5" cy="10.5" r="5.5" />
              <path d="m15 15 4 4" />
              <path d="M10.5 7.5v6" />
              <path d="M7.5 10.5h6" />
            </NavIcon>
            Debris Tracker
          </button>
          <button
            className={`nav-tab ${activeTab === 'collision' ? 'active' : ''}`}
            onClick={() => setActiveTab('collision')}
          >
            <NavIcon>
              <circle cx="8" cy="12" r="2.5" />
              <circle cx="16" cy="12" r="2.5" />
              <path d="M10.5 10l3-3" />
              <path d="M10.5 14l3 3" />
            </NavIcon>
            Collision Analysis
          </button>
          <button
            className={`nav-tab ${activeTab === 'ranking' ? 'active' : ''}`}
            onClick={() => setActiveTab('ranking')}
          >
            <NavIcon>
              <path d="M5.5 18v-5" />
              <path d="M12 18V7" />
              <path d="M18.5 18V10" />
              <path d="M4 18h16" />
            </NavIcon>
            Risk Ranking
          </button>
          <button
            className={`nav-tab ${activeTab === 'demo' ? 'active' : ''}`}
            onClick={() => setActiveTab('demo')}
          >
            <NavIcon>
              <rect x="5" y="5" width="14" height="14" rx="2.5" />
              <path d="M8 9h8" />
              <path d="M8 12.5h8" />
              <path d="M8 16h5" />
            </NavIcon>
            Demo Analysis
          </button>
          <button
            className={`nav-tab ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            <NavIcon>
              <circle cx="12" cy="8" r="3" />
              <path d="M6.5 18c1.7-2.6 3.7-4 5.5-4s3.8 1.4 5.5 4" />
            </NavIcon>
            Satellite Profile
          </button>
          <button
            className={`nav-tab ${activeTab === 'enhanced' ? 'active' : ''}`}
            onClick={() => setActiveTab('enhanced')}
          >
            <NavIcon>
              <path d="M13.5 3 6 13h4l-1 8 8-10h-4.5z" />
            </NavIcon>
            Enhanced Features
          </button>
          <button
            className={`nav-tab ${activeTab === 'alerts' ? 'active' : ''}`}
            onClick={() => setActiveTab('alerts')}
          >
            <NavIcon>
              <path d="M12 3 2 20h20L12 3z" />
              <path d="M12 9v4" />
              <circle cx="12" cy="17" r=".7" fill="currentColor" stroke="none" />
            </NavIcon>
            Alerts
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
          <div style={{ display: activeTab === 'demo' ? 'block' : 'none' }}>
            <DemoRiskShowcase />
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
          {' | '}
          <a href="https://www.space-track.org" target="_blank" rel="noopener noreferrer">Space-Track.org</a>
        </p>
      </footer>
    </div>
  )
}
