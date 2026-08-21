import { useState, useEffect } from 'react'
import { startDebrisJob, getDebrisJob, getDebrisDetails } from '../api'

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

  // Format probability with clean scientific notation and negligible clamping (< 1.00e-10)
  function formatProbability(prob, res = null) {
    if (res?.probability_formatted) {
      return res.probability_formatted
    }
    const p = typeof prob === 'number' ? prob : parseFloat(prob) || 0
    if (p <= 1e-30 || p < 1e-10) {
      return '< 1.00e-10'
    }
    return p.toExponential(2)
  }

  useEffect(() => {
    loadSatellites()
  }, [])

  useEffect(() => {
    let interval
    if (jobId && jobStatus?.status === 'running') {
      interval = setInterval(async () => {
        try {
          const status = await getDebrisJob(jobId)
          console.log('Job status update:', status)
          setJobStatus(status)
          
          if (status.status === 'completed') {
            console.log('Job completed! Visualization URL:', status.visualization_url)
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

  function getRiskLevel(probability, missDistance = null) {
    const p = typeof probability === 'number' ? probability : parseFloat(probability) || 0
    const d = missDistance !== null && missDistance !== undefined ? (typeof missDistance === 'number' ? missDistance : parseFloat(missDistance) || 999) : 999

    if (p >= 1e-4 || d < 1.0) {
      return { level: 'CRITICAL', color: '#ff4444' }
    }
    if (p >= 1e-7 || d <= 5.0) {
      return { level: 'WARNING', color: '#ffaa00' }
    }
    return { level: 'SAFE', color: '#00e676' }
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
              <div className="result-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4>Collision Probability</h4>
                {result.pinn_accelerated && (
                  <span style={{ 
                    fontSize: '0.78rem', 
                    padding: '3px 8px', 
                    borderRadius: '6px', 
                    background: 'rgba(100, 255, 218, 0.15)', 
                    color: '#64ffda', 
                    border: '1px solid rgba(100, 255, 218, 0.3)' 
                  }}>
                    ⚡ PINN-Accelerated (J2 + Kepler)
                  </span>
                )}
              </div>
              <div className="probability-display">
                <div 
                  className="probability-value"
                  style={{ color: getRiskLevel(result.probability).color }}
                >
                  {formatProbability(result.probability, result)}
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
                  <span className="detail-value">{samples.toLocaleString()} (Batched Cholesky)</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Propagation Engine:</span>
                  <span className="detail-value" style={{ color: '#64ffda' }}>{result.method || 'PINN_Monte_Carlo_J2'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Log10(Pc):</span>
                  <span className="detail-value" style={{ fontFamily: 'monospace' }}>
                    {result.log10_probability != null ? result.log10_probability.toFixed(2) : '—'}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Min Miss Distance:</span>
                  <span className="detail-value">
                    {result.min_distance_km != null ? `${result.min_distance_km.toFixed(2)} km` : '—'}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Satellite:</span>
                  <span className="detail-value">
                    {satellites.find(s => s.norad_id === selectedSatellite)?.name}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Debris Catalog ID:</span>
                  <span className="detail-value">{debrisId}</span>
                </div>
              </div>

              {/* Debris Telemetry & Orbital Elements Card */}
              {(() => {
                const deb = result?.debris_info || jobStatus?.debris_info || {}
                const classification = deb.classification || deb.type || 'Debris'
                const nameDisplay = deb.name || `Object ${debrisId}`
                const nameClassDisplay = deb.name_classification || `${nameDisplay} / ${classification}`
                
                const incDisplay = deb.inclination_deg != null 
                  ? `${Number(deb.inclination_deg).toFixed(2)}°` 
                  : (deb.inclination != null ? `${Number(deb.inclination).toFixed(2)}°` : 'TLE Derived')
                
                const meanAlt = deb.mean_altitude ?? deb.mean_altitude_km ?? deb.altitude_km
                const pe = deb.perigee ?? deb.perigee_km
                const ap = deb.apogee ?? deb.apogee_km
                
                let altDisplay = 'N/A'
                if (meanAlt != null && pe != null && ap != null) {
                  altDisplay = `${Number(meanAlt).toFixed(1)} km (Perigee: ${Number(pe).toFixed(1)} km / Apogee: ${Number(ap).toFixed(1)} km)`
                } else if (meanAlt != null) {
                  altDisplay = `${Number(meanAlt).toFixed(1)} km`
                } else if (pe != null && ap != null) {
                  altDisplay = `Perigee: ${Number(pe).toFixed(1)} km / Apogee: ${Number(ap).toFixed(1)} km`
                }

                const periodDisplay = deb.period_minutes != null 
                  ? `${Number(deb.period_minutes).toFixed(2)} min`
                  : (deb.orbital_period != null ? `${Number(deb.orbital_period).toFixed(2)} min` : 'N/A')

                let eccDisplay = '0.000000'
                if (deb.eccentricity != null) {
                  eccDisplay = typeof deb.eccentricity === 'number' ? deb.eccentricity.toFixed(6) : String(deb.eccentricity)
                }

                return (
                  <div className="debris-telemetry-card" style={{
                    marginTop: '20px',
                    padding: '16px',
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(100, 255, 218, 0.2)',
                    borderRadius: '10px'
                  }}>
                    <h4 style={{ color: '#64ffda', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      🛸 Debris Orbital Telemetry & Classification
                    </h4>
                    <div className="result-details" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
                      <div className="detail-item">
                        <span className="detail-label">Object Name / Classification:</span>
                        <span className="detail-value" style={{ color: '#64ffda' }}>{nameClassDisplay}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-label">NORAD ID:</span>
                        <span className="detail-value">{deb.norad_id || debrisId}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-label">Inclination:</span>
                        <span className="detail-value">{incDisplay}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-label">Altitude / Perigee & Apogee:</span>
                        <span className="detail-value">{altDisplay}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-label">Orbital Period:</span>
                        <span className="detail-value">{periodDisplay}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-label">Eccentricity:</span>
                        <span className="detail-value" style={{ fontFamily: 'monospace' }}>{eccDisplay}</span>
                      </div>
                    </div>
                  </div>
                )
              })()}

              <div className="visualization-section">
                <h4>3D Visualization</h4>
                {(result.visualization_url || jobStatus?.visualization_url) ? (
                  <a 
                    href={`http://localhost:5000${result.visualization_url || jobStatus?.visualization_url}`}
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="view-viz-btn"
                  >
                    📊 View 3D Orbit Visualization
                  </a>
                ) : (
                  <p className="viz-note">Visualization will be available when analysis completes</p>
                )}
              </div>
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
