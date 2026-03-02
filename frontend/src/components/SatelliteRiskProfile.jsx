import { useState, useEffect } from 'react'
import { getRelevantDebrisForSatellite, startDebrisJob, getDebrisJob } from '../api'

export default function SatelliteRiskProfile() {
  const [satellites, setSatellites] = useState([])
  const [selectedSatellite, setSelectedSatellite] = useState(null)
  const [debrisList, setDebrisList] = useState([])
  const [analyzing, setAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [debrisLimit, setDebrisLimit] = useState(50) // Changed from 100 to 50

  // Format probability - Scientific notation only
  function formatProbability(prob) {
    const percentage = prob * 100
    
    if (percentage === 0) {
      return '0.00e+0%'
    }
    
    // Always use scientific notation
    return `${percentage.toExponential(2)}%`
  }
  
  // Helper to format large numbers (1M, 1B, etc)
  function formatOdds(num) {
    if (num >= 1e12) return (num/1e12).toFixed(1) + 'T'
    if (num >= 1e9) return (num/1e9).toFixed(1) + 'B'
    if (num >= 1e6) return (num/1e6).toFixed(1) + 'M'
    if (num >= 1e3) return (num/1e3).toFixed(1) + 'K'
    return num.toLocaleString()
  }

  useEffect(() => {
    loadData()
  }, [])

  // Load debris when satellite changes
  useEffect(() => {
    if (selectedSatellite) {
      loadDebrisForSatellite()
    }
  }, [selectedSatellite, debrisLimit])

  async function loadData() {
    setLoading(true)
    try {
      // Load satellites
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
      // Load debris relevant to this specific satellite's orbit
      const debrisData = await getRelevantDebrisForSatellite(selectedSatellite, debrisLimit)
      if (debrisData.high_risk_debris) {
        setDebrisList(debrisData.high_risk_debris)
        console.log(`Loaded ${debrisData.high_risk_debris.length} relevant debris for satellite ${selectedSatellite}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function filterRelevantDebris(satelliteNorad, allDebris) {
    // No longer needed - API does the filtering
    return allDebris
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
    
    // Use the debris list (already filtered by API)
    const relevantDebris = debrisList
    
    const total = relevantDebris.length
    let completed = 0
    const analysisResults = []

    console.log(`Starting analysis of ${total} debris objects for satellite ${selectedSatellite}`)

    try {
      // Process in batches - HIGH ACCURACY MODE
      const batchSize = 3  // Smaller batches for more accurate processing
      
      for (let i = 0; i < relevantDebris.length; i += batchSize) {
        const batch = relevantDebris.slice(i, i + batchSize)
        
        const batchPromises = batch.map(async (debris) => {
          try {
            console.log(`Starting analysis for debris ${debris.norad_id}`)
            const payload = {
              debris: debris.norad_id,
              satellite_norad: selectedSatellite,
              duration_minutes: 1440,  // 24 hours (increased from 10 min)
              step_seconds: 120,
              samples: 5000,  // Increased from 100 for better accuracy
              position_uncertainty_km: 2.0,  // Realistic TLE uncertainty (was 1000)
              debris_radius_km: 0.5,
              satellite_radius_km: 0.01,
              visualize: false,
              use_improved_accuracy: true  // Enable high accuracy mode
            }

            const jobResponse = await startDebrisJob(payload)
            const jobId = jobResponse.job_id

            // Poll for completion
            let jobStatus = await getDebrisJob(jobId)
            let attempts = 0
            const maxAttempts = 300  // 5 minutes timeout (was 120 = 2 min)
            while ((jobStatus.status === 'running' || jobStatus.status === 'queued') && attempts < maxAttempts) {
              await new Promise(resolve => setTimeout(resolve, 1000))  // Check every second
              jobStatus = await getDebrisJob(jobId)
              attempts++
            }

            if (jobStatus.status === 'completed' && jobStatus.result) {
              const result = {
                debris_id: debris.norad_id,
                debris_name: debris.name || debris.norad_id,
                debris_size: debris.rcs_size,
                probability: jobStatus.result.probability || 0,
                confidence_interval: jobStatus.result.confidence_interval_95,
                min_distance: jobStatus.result.min_distance_km,
                risk_level: getRiskLevel(jobStatus.result.probability || 0).level
              }
              console.log(`Result for debris ${debris.norad_id}:`, result)
              return result
            } else if (jobStatus.status === 'failed') {
              console.error(`Job ${jobId} failed:`, jobStatus.error)
              return null
            } else {
              console.warn(`Job ${jobId} timed out after ${maxAttempts}s, status: ${jobStatus.status}`)
              return null
            }
          } catch (err) {
            console.error(`Error analyzing debris ${debris.norad_id}:`, err)
          }
          return null
        })

        const batchResults = await Promise.all(batchPromises)
        const validResults = batchResults.filter(r => r !== null)
        console.log(`Batch completed: ${validResults.length} valid results out of ${batchResults.length}`)
        analysisResults.push(...validResults)
        
        completed += batch.length
        setProgress(Math.round((completed / total) * 100))
      }

      console.log(`Analysis complete! Total results: ${analysisResults.length}`)

      // Sort by probability (highest first)
      analysisResults.sort((a, b) => b.probability - a.probability)
      setResults(analysisResults)
      
      console.log(`Results set:`, analysisResults)
      
    } catch (err) {
      setError(err.message)
    } finally {
      setAnalyzing(false)
    }
  }

  function getRiskLevel(probability) {
    if (probability === 0) return { level: 'SAFE', color: '#4caf50', icon: '✅' }
    if (probability < 0.001) return { level: 'LOW', color: '#8bc34a', icon: '⚠️' }
    if (probability < 0.01) return { level: 'MODERATE', color: '#ff9800', icon: '⚠️' }
    if (probability < 0.1) return { level: 'HIGH', color: '#ff5722', icon: '🔴' }
    return { level: 'CRITICAL', color: '#f44336', icon: '🚨' }
  }

  const selectedSatInfo = satellites.find(s => s.norad_id === selectedSatellite)
  const threatsDetected = results.filter(r => r.probability > 0).length
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
        <h2>🛰️ Satellite Risk Profile</h2>
        <p>Analyze collision threats for a specific satellite</p>
      </div>

      <div className="profile-controls">
        <div className="satellite-selector">
          <label>Select Satellite:</label>
          <select 
            value={selectedSatellite || ''} 
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
          {analyzing ? (
            <>
              <span className="spinner"></span>
              Analyzing... {progress}%
            </>
          ) : (
            '🔍 Analyze All Threats'
          )}
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
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
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
              <h4>⚠️ Detected Threats (Sorted by Risk)</h4>
              <div className="threat-table">
                <div className="table-header">
                  <div className="header-cell rank">Rank</div>
                  <div className="header-cell debris">Debris Object</div>
                  <div className="header-cell size">Size</div>
                  <div className="header-cell probability">Probability</div>
                  <div className="header-cell risk">Risk Level</div>
                </div>
                
                {results.filter(r => r.probability > 0).map((result, index) => {
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
                        <span className="probability-value">
                          {formatProbability(result.probability)}
                        </span>
                      </div>
                      <div className="table-cell risk">
                        <span 
                          className="risk-badge"
                          style={{ backgroundColor: risk.color }}
                        >
                          {risk.icon} {risk.level}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ) : (
            <div className="no-threats-message">
              <div className="success-icon">✅</div>
              <h3>All Clear!</h3>
              <p>No collision threats detected for {selectedSatInfo?.name}</p>
              <p className="sub-message">All {results.length} debris objects analyzed show safe separation</p>
            </div>
          )}
        </div>
      )}

      {!analyzing && results.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">🛰️</div>
          <h3>Ready to Analyze</h3>
          <p>Select a satellite and click "Analyze All Threats" to scan for collision risks</p>
          <p className="empty-note">Smart filtering: Analyzes debris in similar orbits (altitude ±500km, inclination ±30°)</p>
        </div>
      )}
    </div>
  )
}
