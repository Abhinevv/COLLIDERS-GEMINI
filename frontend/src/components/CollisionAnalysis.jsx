import { useState, useEffect } from 'react'
import { startDebrisJob, getDebrisJob, getDemoRiskScenarios } from '../api'

export default function CollisionAnalysis() {
  const [satellites, setSatellites] = useState([])
  const [selectedSatellite, setSelectedSatellite] = useState('25544')
  const [debrisId, setDebrisId] = useState('')
  const [duration, setDuration] = useState(60)
  const [samples, setSamples] = useState(1000)
  const [analyzing, setAnalyzing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [demoScenarios, setDemoScenarios] = useState([])
  const [demoMode, setDemoMode] = useState(false)

  // Format probability with scientific notation for very small values
  function formatProbability(prob) {
    const percentage = prob * 100
    if (percentage === 0) {
      return '0 (no collision)'
    } else if (percentage < 0.0000001) {
      return `${percentage.toExponential(2)}%`
    } else {
      return `${percentage.toFixed(7)}%`
    }
  }

  useEffect(() => {
    loadSatellites()
    loadDemoScenarios()
  }, [])

  useEffect(() => {
    let interval
    if (jobId && jobStatus?.status === 'running') {
      interval = setInterval(async () => {
        try {
          const status = await getDebrisJob(jobId)
          setJobStatus(status)
          
          if (status.status === 'completed') {
            setResult(status.result)
            setAnalyzing(false)
            clearInterval(interval)
          } else if (status.status === 'failed') {
            setError(status.error || 'Analysis failed')
            setAnalyzing(false)
            clearInterval(interval)
          }
        } catch (err) {
          setError(err.message)
          setAnalyzing(false)
          clearInterval(interval)
        }
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [jobId, jobStatus?.status])

  async function loadSatellites() {
    try {
      // Fetch managed satellites from database
      const response = await fetch('http://localhost:5000/api/satellites/manage')
      const data = await response.json()
      if (data.satellites) {
        setSatellites(data.satellites)
        // Set first satellite as default if available
        if (data.satellites.length > 0) {
          setSelectedSatellite(data.satellites[0].norad_id)
        }
      }
    } catch (err) {
      setError(err.message)
    }
  }

  async function loadDemoScenarios() {
    try {
      const data = await getDemoRiskScenarios()
      setDemoScenarios(data.scenarios || [])
    } catch (err) {
      console.error('Error loading demo scenarios:', err)
    }
  }

  function loadDemoScenario(scenario) {
    setDemoMode(true)
    setSelectedSatellite(scenario.satellite_id)
    setDebrisId(scenario.debris_id)
    setDuration(Math.max(15, scenario.time_to_approach_minutes * 2))
    setSamples(10000)
    setJobId(null)
    setJobStatus({
      status: 'completed',
      visualization_url: null
    })
    setResult({
      probability: scenario.probability,
      min_distance_km: scenario.closest_distance_km,
      relative_velocity_km_s: scenario.relative_velocity_km_s,
      total_samples: 10000,
      demo_only: true,
      summary: scenario.summary
    })
    setError(null)
  }

  async function handleAnalyze(e) {
    e.preventDefault()
    
    if (!debrisId.trim()) {
      setError('Please enter a debris ID')
      return
    }

    setAnalyzing(true)
    setError(null)
    setResult(null)
    setJobStatus(null)
    setDemoMode(false)

    try {
      const payload = {
        debris: debrisId,
        satellite_norad: selectedSatellite,
        duration_minutes: duration,
        step_seconds: 60,
        samples: samples,
        position_uncertainty_km: 2.0,  // High accuracy: realistic TLE uncertainty
        debris_radius_km: 0.5,
        satellite_radius_km: 0.01,
        use_improved_accuracy: true,  // Enable high accuracy mode
        visualize: true
      }

      const response = await startDebrisJob(payload)
      setJobId(response.job_id)
      setJobStatus({ status: 'running', progress: 0 })
    } catch (err) {
      setError(err.message)
      setAnalyzing(false)
    }
  }

  function getRiskLevel(probability) {
    if (probability === 0) return { level: 'SAFE', color: '#4caf50' }
    if (probability < 0.001) return { level: 'LOW', color: '#8bc34a' }
    if (probability < 0.01) return { level: 'MODERATE', color: '#ff9800' }
    if (probability < 0.1) return { level: 'HIGH', color: '#ff5722' }
    return { level: 'CRITICAL', color: '#f44336' }
  }

  return (
    <div className="collision-analysis">
      <div className="analysis-header">
        <h2>Collision Analysis</h2>
        <p>Analyze collision probability between satellites and space debris</p>
      </div>

      {demoScenarios.length > 0 && (
        <div className="demo-banner collision-demo-banner glass-effect">
          <strong>Demo Presets</strong>
          <span>Use these curated scenarios to present how this screen looks with visible non-zero risk values.</span>
          <div className="demo-preset-row">
            {demoScenarios.map((scenario) => (
              <button
                key={scenario.scenario_id}
                type="button"
                className="demo-preset-btn"
                onClick={() => loadDemoScenario(scenario)}
              >
                {scenario.satellite_name} vs {scenario.debris_name}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="analysis-form-container">
        <form onSubmit={handleAnalyze} className="analysis-form">
          <div className="form-section">
            <h3>Select Satellite</h3>
            <select 
              value={selectedSatellite} 
              onChange={(e) => setSelectedSatellite(e.target.value)}
              className="form-select"
            >
              {satellites.map(sat => (
                <option key={sat.norad_id} value={sat.norad_id}>
                  {sat.name} (NORAD: {sat.norad_id})
                </option>
              ))}
            </select>
          </div>

          <div className="form-section">
            <h3>Debris Information</h3>
            <input
              type="text"
              value={debrisId}
              onChange={(e) => setDebrisId(e.target.value)}
              placeholder="Enter debris ID (e.g., 433 for Eros)"
              className="form-input"
            />
            <p className="form-hint">
              Use JPL Horizons IDs (e.g., 433 for asteroid Eros) or NORAD IDs for tracked objects
            </p>
          </div>

          <div className="form-section">
            <h3>Analysis Parameters</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Duration (minutes)</label>
                <input
                  type="number"
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  min="10"
                  max="1440"
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Monte Carlo Samples</label>
                <input
                  type="number"
                  value={samples}
                  onChange={(e) => setSamples(parseInt(e.target.value))}
                  min="100"
                  max="10000"
                  step="100"
                  className="form-input"
                />
              </div>
            </div>
          </div>

          <button 
            type="submit" 
            className="analyze-btn"
            disabled={analyzing}
          >
            {analyzing ? (
              <>
                <span className="spinner"></span>
                Analyzing...
              </>
            ) : (
              '🚀 Run Analysis'
            )}
          </button>
        </form>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {jobStatus && jobStatus.status === 'running' && (
          <div className="progress-container">
            <h3>Analysis in Progress</h3>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${jobStatus.progress || 0}%` }}
              ></div>
            </div>
            <p>{jobStatus.progress || 0}% complete</p>
          </div>
        )}

        {result && (
          <div className="results-container">
            <h3>Analysis Results</h3>
            {demoMode && (
              <div className="demo-note">
                Demo scenario loaded for presentation. Real collision analysis remains unchanged.
              </div>
            )}
            
            <div className="result-card">
              <div className="result-header">
                <h4>Collision Probability</h4>
              </div>
              <div className="probability-display">
                <div 
                  className="probability-value"
                  style={{ color: getRiskLevel(result.probability).color }}
                >
                  {formatProbability(result.probability)}
                </div>
                <div 
                  className="risk-badge"
                  style={{ 
                    backgroundColor: getRiskLevel(result.probability).color,
                    color: 'white'
                  }}
                >
                  {getRiskLevel(result.probability).level} RISK
                </div>
              </div>
              
              <div className="result-details">
                <div className="detail-item">
                  <span className="detail-label">Samples Analyzed:</span>
                  <span className="detail-value">{(result.total_samples || samples).toLocaleString()}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Duration:</span>
                  <span className="detail-value">{duration} minutes</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Satellite:</span>
                  <span className="detail-value">
                    {satellites.find(s => s.norad_id === selectedSatellite)?.name}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Debris ID:</span>
                  <span className="detail-value">{debrisId}</span>
                </div>
                {result.min_distance_km && (
                  <div className="detail-item">
                    <span className="detail-label">Closest Distance:</span>
                    <span className="detail-value">{result.min_distance_km} km</span>
                  </div>
                )}
              </div>

              {jobStatus?.visualization_url && (
                <div className="visualization-link">
                  <a 
                    href={jobStatus.visualization_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="view-viz-btn"
                  >
                    📊 View 3D Visualization
                  </a>
                </div>
              )}
            </div>

            <div className="interpretation">
              <h4>Interpretation</h4>
              {demoMode && result.summary && (
                <p className="form-hint">{result.summary}</p>
              )}
              {result.probability === 0 ? (
                <p className="safe-message">
                  ✅ No collision detected. The objects maintain safe separation throughout the analysis period.
                </p>
              ) : result.probability < 0.001 ? (
                <p className="low-message">
                  ⚠️ Low collision risk detected. Continue monitoring but no immediate action required.
                </p>
              ) : result.probability < 0.01 ? (
                <p className="moderate-message">
                  ⚠️ Moderate collision risk. Consider collision avoidance maneuvers.
                </p>
              ) : (
                <p className="high-message">
                  🚨 High collision risk! Immediate collision avoidance maneuvers recommended.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
