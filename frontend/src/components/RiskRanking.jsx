import { useEffect, useState } from 'react'
import { getHighRiskDebris, startDebrisJob, getDebrisJob } from '../api'

export default function RiskRanking() {
  const [satellites, setSatellites] = useState([])
  const [debrisList, setDebrisList] = useState([])
  const [riskMatrix, setRiskMatrix] = useState([])
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [analysisMode, setAnalysisMode] = useState('fast') // 'fast' or 'full'

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      // Fetch managed satellites and debris
      const satResponse = await fetch('http://localhost:5000/api/satellites/manage')
      const satData = await satResponse.json()
      
      const debrisData = await getHighRiskDebris(200, 2000, 2000) // Get 2000 debris objects (good balance)
      
      if (satData.satellites) {
        setSatellites(satData.satellites)
      }
      
      if (debrisData.high_risk_debris) {
        // Sort debris by RCS size (larger objects are more dangerous)
        const sortedDebris = debrisData.high_risk_debris
          .sort((a, b) => {
            const sizeOrder = { 'LARGE': 3, 'MEDIUM': 2, 'SMALL': 1 }
            const sizeA = sizeOrder[a.rcs_size] || 0
            const sizeB = sizeOrder[b.rcs_size] || 0
            return sizeB - sizeA
          })
        
        setDebrisList(sortedDebris) // Use all 2000 debris objects
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function analyzeAllRisks(mode = 'fast') {
    if (satellites.length === 0 || debrisList.length === 0) {
      setError('No satellites or debris data available')
      return
    }

    setAnalyzing(true)
    setAnalysisMode(mode)
    setError(null)
    setProgress(0)
    
    const results = []
    
    // Choose subset based on mode
    const selectedSatellites = mode === 'fast' ? satellites.slice(0, 10) : satellites
    const selectedDebris = mode === 'fast' ? debrisList.slice(0, 100) : debrisList // Fast: top 100, Full: all 2000
    const total = selectedSatellites.length * selectedDebris.length
    let completed = 0

    // Analysis parameters based on mode
    const params = mode === 'fast' 
      ? { duration: 10, step: 120, samples: 100, batchSize: 5, pollInterval: 500 }
      : { duration: 15, step: 90, samples: 200, batchSize: 3, pollInterval: 1000 }

    try {
      // Process in batches for better performance
      const allCombinations = []
      
      for (const sat of selectedSatellites) {
        for (const debris of selectedDebris) {
          allCombinations.push({ sat, debris })
        }
      }

      for (let i = 0; i < allCombinations.length; i += params.batchSize) {
        const batch = allCombinations.slice(i, i + params.batchSize)
        
        // Process batch in parallel
        const batchPromises = batch.map(async ({ sat, debris }) => {
          try {
            const payload = {
              debris: debris.norad_id,
              satellite_norad: sat.norad_id,
              duration_minutes: params.duration,
              step_seconds: params.step,
              samples: params.samples,
              position_uncertainty_km: 2.0,  // High accuracy: realistic TLE uncertainty
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
            const maxAttempts = mode === 'fast' ? 60 : 120
            while ((jobStatus.status === 'running' || jobStatus.status === 'queued') && attempts < maxAttempts) {
              await new Promise(resolve => setTimeout(resolve, params.pollInterval))
              jobStatus = await getDebrisJob(jobId)
              attempts++
            }

            if (jobStatus.status === 'completed' && jobStatus.result) {
              return {
                satellite: sat.name,
                satelliteId: sat.norad_id,
                debris: debris.name || debris.norad_id,
                debrisId: debris.norad_id,
                probability: jobStatus.result.probability || 0,
                riskLevel: getRiskLevel(jobStatus.result.probability || 0).level
              }
            }
          } catch (err) {
            console.error(`Error analyzing ${sat.name} vs ${debris.norad_id}:`, err)
          }
          return null
        })

        const batchResults = await Promise.all(batchPromises)
        results.push(...batchResults.filter(r => r !== null))
        
        completed += batch.length
        setProgress(Math.round((completed / total) * 100))
      }

      // Sort by probability (highest first)
      results.sort((a, b) => b.probability - a.probability)
      setRiskMatrix(results)
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

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading satellites and debris data...</p>
      </div>
    )
  }

  return (
    <div className="risk-ranking">
      <div className="ranking-header">
        <h2>Collision Risk Ranking</h2>
        <p>Analyze and rank collision probabilities between satellites and space debris</p>
      </div>

      <div className="ranking-controls">
        <div className="data-summary">
          <div className="summary-item">
            <span className="summary-label">Satellites:</span>
            <span className="summary-value">{satellites.length}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Debris Objects:</span>
            <span className="summary-value">{debrisList.length}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Total Combinations:</span>
            <span className="summary-value">{satellites.length * debrisList.length}</span>
          </div>
        </div>

        <div className="analysis-buttons">
          <button 
            className="analyze-btn fast-btn"
            onClick={() => analyzeAllRisks('fast')}
            disabled={analyzing || satellites.length === 0 || debrisList.length === 0}
          >
            {analyzing && analysisMode === 'fast' ? (
              <>
                <span className="spinner"></span>
                Fast Mode... {progress}%
              </>
            ) : (
              '⚡ Fast Mode (Top 10 x 100)'
            )}
          </button>
          
          <button 
            className="analyze-btn full-btn"
            onClick={() => analyzeAllRisks('full')}
            disabled={analyzing || satellites.length === 0 || debrisList.length === 0}
          >
            {analyzing && analysisMode === 'full' ? (
              <>
                <span className="spinner"></span>
                Full Analysis... {progress}%
              </>
            ) : (
              `🚀 Full Analysis (All ${satellites.length * debrisList.length})`
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {analyzing && (
        <div className="progress-container">
          <h3>{analysisMode === 'fast' ? 'Fast Analysis' : 'Full Analysis'} in Progress</h3>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p>{progress}% complete - Analyzing {analysisMode === 'fast' ? '1,000 combinations (10 x 100)' : `${satellites.length * debrisList.length} combinations (${satellites.length} x ${debrisList.length})`}</p>
          <p className="progress-note">
            {analysisMode === 'fast' 
              ? 'Fast mode: 100 samples, 10 min duration, batch size 5 (~10-15 minutes)'
              : 'Full mode: 200 samples, 15 min duration, batch size 3 - This will take 4-6 hours!'
            }
          </p>
        </div>
      )}

      {riskMatrix.length > 0 && (
        <div className="risk-matrix-container">
          <h3>Risk Matrix Results</h3>
          <p className="matrix-subtitle">Ranked by collision probability (highest risk first)</p>
          
          <div className="risk-table">
            <div className="table-header">
              <div className="header-cell rank">Rank</div>
              <div className="header-cell satellite">Satellite</div>
              <div className="header-cell debris">Debris Object</div>
              <div className="header-cell probability">Probability</div>
              <div className="header-cell risk">Risk Level</div>
            </div>
            
            {riskMatrix.map((item, index) => {
              const risk = getRiskLevel(item.probability)
              return (
                <div key={index} className="table-row">
                  <div className="table-cell rank">
                    <span className="rank-badge">{index + 1}</span>
                  </div>
                  <div className="table-cell satellite">
                    <div className="cell-content">
                      <strong>{item.satellite}</strong>
                      <span className="cell-id">NORAD: {item.satelliteId}</span>
                    </div>
                  </div>
                  <div className="table-cell debris">
                    <div className="cell-content">
                      <strong>{item.debris}</strong>
                      <span className="cell-id">ID: {item.debrisId}</span>
                    </div>
                  </div>
                  <div className="table-cell probability">
                    <span className="probability-value">
                      {(item.probability * 100).toFixed(4)}%
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

          {riskMatrix.filter(r => r.probability > 0).length === 0 && (
            <div className="no-risk-message">
              ✅ Excellent news! No collision risks detected for any satellite-debris combinations.
            </div>
          )}
        </div>
      )}

      {!analyzing && riskMatrix.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h3>No Analysis Yet</h3>
          <p>Click "Analyze All Risks" to calculate collision probabilities for all satellite-debris combinations.</p>
          <p className="empty-note">Note: This analysis may take several minutes to complete.</p>
        </div>
      )}
    </div>
  )
}
