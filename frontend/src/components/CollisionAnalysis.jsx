import { useState, useEffect } from 'react'
import { startDebrisJob, getDebrisJob } from '../api'

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

  useEffect(() => {
    loadSatellites()
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
            
            <div className="result-card">
              <div className="result-header">
                <h4>Collision Probability</h4>
              </div>
              <div className="probability-display">
                <div 
                  className="probability-value"
                  style={{ color: getRiskLevel(result.probability).color }}
                >
                  {(result.probability * 100).toFixed(4)}%
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
                  <span className="detail-value">{samples.toLocaleString()}</span>
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
