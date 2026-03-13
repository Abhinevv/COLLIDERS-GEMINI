import { useState, useEffect } from 'react'
import { getRelevantDebrisForSatellite, startDebrisJob, getDebrisJob } from '../api'

function Icon({ children }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" style={{ width: '100%', height: '100%' }} aria-hidden="true">
      {children}
    </svg>
  )
}

export default function SatelliteRiskProfile() {
  const [satellites, setSatellites] = useState([])
  const [selectedSatellite, setSelectedSatellite] = useState(null)
  const [debrisList, setDebrisList] = useState([])
  const [analyzing, setAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [debrisLimit, setDebrisLimit] = useState(50)
  const [matchingMode, setMatchingMode] = useState('strict_orbital_match')

  function formatProbability(prob) {
    const percentage = prob * 100
    if (percentage === 0) return '0.00e+0%'
    return `${percentage.toExponential(2)}%`
  }

  function formatOdds(num) {
    if (num >= 1e12) return (num / 1e12).toFixed(1) + 'T'
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B'
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M'
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K'
    return num.toLocaleString()
  }

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (selectedSatellite) {
      loadDebrisForSatellite()
    }
  }, [selectedSatellite, debrisLimit])

  async function loadData() {
    setLoading(true)
    try {
      const satResponse = await fetch('http://localhost:5000/api/satellites/manage')
      const satData = await satResponse.json()

      if (satData.satellites && satData.satellites.length > 0) {
        setSatellites(satData.satellites)
        setSelectedSatellite(satData.satellites[0].norad_id)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadDebrisForSatellite() {
    if (!selectedSatellite) return

    try {
      setLoading(true)
      const debrisData = await getRelevantDebrisForSatellite(selectedSatellite, debrisLimit)
      if (debrisData.high_risk_debris) {
        setDebrisList(debrisData.high_risk_debris)
        setMatchingMode(debrisData.matching_mode || 'strict_orbital_match')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function analyzeSatellite() {
    if (!selectedSatellite) {
      setError('Please select a satellite')
      return
    }

    if (debrisList.length === 0) {
      setError('No debris data loaded. Please wait for debris to load or try selecting a different satellite.')
      return
    }

    setAnalyzing(true)
    setError(null)
    setProgress(0)
    setResults([])

    const relevantDebris = debrisList
    const total = relevantDebris.length
    let completed = 0
    const analysisResults = []

    try {
      const batchSize = 3

      for (let i = 0; i < relevantDebris.length; i += batchSize) {
        const batch = relevantDebris.slice(i, i + batchSize)

        const batchPromises = batch.map(async (debris) => {
          try {
            const payload = {
              debris: debris.norad_id,
              satellite_norad: selectedSatellite,
              duration_minutes: 1440,
              step_seconds: 120,
              samples: 5000,
              position_uncertainty_km: 2.0,
              debris_radius_km: 0.5,
              satellite_radius_km: 0.01,
              visualize: false,
              use_improved_accuracy: true
            }

            const jobResponse = await startDebrisJob(payload)
            const jobId = jobResponse.job_id

            let jobStatus = await getDebrisJob(jobId)
            let attempts = 0
            const maxAttempts = 300
            while ((jobStatus.status === 'running' || jobStatus.status === 'queued') && attempts < maxAttempts) {
              await new Promise((resolve) => setTimeout(resolve, 1000))
              jobStatus = await getDebrisJob(jobId)
              attempts++
            }

            if (jobStatus.status === 'completed' && jobStatus.result) {
              return {
                debris_id: debris.norad_id,
                debris_name: debris.name || debris.norad_id,
                debris_size: debris.rcs_size,
                probability: jobStatus.result.probability || 0,
                confidence_interval: jobStatus.result.confidence_interval_95,
                min_distance: jobStatus.result.min_distance_km,
                risk_level: getRiskLevel(jobStatus.result.probability || 0).level
              }
            }
          } catch (err) {
            console.error(`Error analyzing debris ${debris.norad_id}:`, err)
          }
          return null
        })

        const batchResults = await Promise.all(batchPromises)
        analysisResults.push(...batchResults.filter((r) => r !== null))

        completed += batch.length
        setProgress(Math.round((completed / total) * 100))
      }

      analysisResults.sort((a, b) => b.probability - a.probability)
      setResults(analysisResults)
    } catch (err) {
      setError(err.message)
    } finally {
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

  const selectedSatInfo = satellites.find((s) => s.norad_id === selectedSatellite)
  const threatsDetected = results.filter((r) => r.probability > 0).length
  const relevantDebrisCount = debrisList.length

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading data...</p>
      </div>
    )
  }

  return (
    <div className="satellite-risk-profile">
      <div className="profile-header">
        <h2>Satellite Risk Profile</h2>
        <p>Analyze collision threats for a specific satellite</p>
        <p className="form-hint">
          {matchingMode === 'nearest_fallback'
            ? 'No strict orbital matches found, so the nearest debris objects are shown instead.'
            : 'Showing debris selected by strict orbital similarity.'}
        </p>
      </div>

      <div className="profile-controls">
        <div className="satellite-selector">
          <label>Select Satellite:</label>
          <select
            value={selectedSatellite || ''}
            onChange={(e) => setSelectedSatellite(e.target.value)}
            className="form-select"
          >
            {satellites.map((sat) => (
              <option key={sat.norad_id} value={sat.norad_id}>
                {sat.name} (NORAD: {sat.norad_id})
              </option>
            ))}
          </select>
        </div>

        <div className="analysis-info">
          <div className="info-item">
            <span className="info-label">Relevant Debris:</span>
            <span className="info-value">{relevantDebrisCount}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Estimated Time:</span>
            <span className="info-value">~{Math.ceil(relevantDebrisCount * 2 / 3)} min</span>
          </div>
        </div>

        <button
          className="analyze-profile-btn"
          onClick={analyzeSatellite}
          disabled={analyzing || !selectedSatellite}
        >
          {analyzing ? `Analyzing... ${progress}%` : 'Analyze All Threats'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {analyzing && (
        <div className="progress-container">
          <h3>Scanning for Threats</h3>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <p>{progress}% complete - Analyzing {selectedSatInfo?.name} against {debrisList.length} debris objects</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="results-container">
          <div className="results-summary">
            <h3>Risk Assessment for {selectedSatInfo?.name}</h3>
            <div className="summary-stats">
              <div className="stat-card threat">
                <div className="stat-value">{threatsDetected}</div>
                <div className="stat-label">Threats Detected</div>
              </div>
              <div className="stat-card analyzed">
                <div className="stat-value">{results.length}</div>
                <div className="stat-label">Objects Analyzed</div>
              </div>
              <div className="stat-card safe">
                <div className="stat-value">{results.length - threatsDetected}</div>
                <div className="stat-label">Safe Passes</div>
              </div>
            </div>
          </div>

          {threatsDetected > 0 ? (
            <div className="threats-list">
              <h4>Detected Threats (Sorted by Risk)</h4>
              <div className="threat-table">
                <div className="table-header">
                  <div className="header-cell rank">Rank</div>
                  <div className="header-cell debris">Debris Object</div>
                  <div className="header-cell size">Size</div>
                  <div className="header-cell probability">Probability</div>
                  <div className="header-cell risk">Risk Level</div>
                </div>

                {results.filter((r) => r.probability > 0).map((result, index) => {
                  const risk = getRiskLevel(result.probability)
                  return (
                    <div key={index} className="table-row">
                      <div className="table-cell rank">
                        <span className="rank-badge">{index + 1}</span>
                      </div>
                      <div className="table-cell debris">
                        <div className="cell-content">
                          <strong>{result.debris_name}</strong>
                          <span className="cell-id">ID: {result.debris_id}</span>
                        </div>
                      </div>
                      <div className="table-cell size">
                        <span className={`size-badge ${result.debris_size?.toLowerCase()}`}>
                          {result.debris_size || 'UNKNOWN'}
                        </span>
                      </div>
                      <div className="table-cell probability">
                        <span className="probability-value">{formatProbability(result.probability)}</span>
                      </div>
                      <div className="table-cell risk">
                        <span className="risk-badge" style={{ backgroundColor: risk.color }}>
                          <span style={{ display: 'inline-flex', width: 14, height: 14, marginRight: 6 }}>
                            {risk.level === 'SAFE' && (
                              <Icon>
                                <path d="m5 12 4 4L19 6" />
                              </Icon>
                            )}
                            {risk.level === 'LOW' && (
                              <Icon>
                                <circle cx="12" cy="12" r="8" />
                              </Icon>
                            )}
                            {risk.level === 'MODERATE' && (
                              <Icon>
                                <path d="M12 4v8" />
                                <path d="M12 16h.01" />
                                <circle cx="12" cy="12" r="8" />
                              </Icon>
                            )}
                            {risk.level === 'HIGH' && (
                              <Icon>
                                <path d="M12 3 2 20h20L12 3z" />
                                <path d="M12 9v4" />
                                <path d="M12 17h.01" />
                              </Icon>
                            )}
                            {risk.level === 'CRITICAL' && (
                              <Icon>
                                <circle cx="12" cy="12" r="9" />
                                <path d="m8.5 8.5 7 7" />
                                <path d="m15.5 8.5-7 7" />
                              </Icon>
                            )}
                          </span>
                          {risk.level}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ) : (
            <div className="no-threats-message">
              <div className="success-icon">
                <Icon>
                  <circle cx="12" cy="12" r="9" />
                  <path d="m7 12 3 3 7-7" />
                </Icon>
              </div>
              <h3>All Clear!</h3>
              <p>No collision threats detected for {selectedSatInfo?.name}</p>
              <p className="sub-message">All {results.length} debris objects analyzed show safe separation</p>
            </div>
          )}
        </div>
      )}

      {!analyzing && results.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">
            <Icon>
              <path d="M4 12h5" />
              <path d="M15 12h5" />
              <circle cx="12" cy="12" r="3" />
              <path d="M12 4v5" />
              <path d="M12 15v5" />
            </Icon>
          </div>
          <h3>Ready to Analyze</h3>
          <p>Select a satellite and click "Analyze All Threats" to scan for collision risks</p>
          <p className="empty-note">Smart filtering first, with nearest-debris fallback when needed.</p>
        </div>
      )}
    </div>
  )
}
