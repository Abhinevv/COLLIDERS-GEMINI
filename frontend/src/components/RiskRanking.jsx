import { useEffect, useState } from 'react'
import { getHighRiskDebris, startDebrisJob, getDebrisJob } from '../api'

export default function RiskRanking() {
  const [satellites, setSatellites] = useState([])
  const [debrisList, setDebrisList] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('fast')
  
  // Separate state for each analysis mode
  const [fastAnalysis, setFastAnalysis] = useState({
    analyzing: false,
    progress: 0,
    results: [],
    complete: false
  })
  
  const [smartAnalysis, setSmartAnalysis] = useState({
    analyzing: false,
    progress: 0,
    results: [],
    complete: false
  })

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
    loadData()
  }, [])

  // Auto-start both analyses after data loads
  useEffect(() => {
    if (satellites.length > 0 && debrisList.length > 0 && !fastAnalysis.complete && !smartAnalysis.complete) {
      console.log('Auto-starting parallel analyses...')
      // Start both analyses simultaneously
      analyzeRisks('fast')
      analyzeRisks('smart')
    }
  }, [satellites, debrisList])

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const satResponse = await fetch('http://localhost:5000/api/satellites/manage')
      const satData = await satResponse.json()
      
      const debrisData = await getHighRiskDebris(200, 2000, 2000)
      
      if (satData.satellites) {
        setSatellites(satData.satellites)
      }
      
      if (debrisData.high_risk_debris) {
        const sortedDebris = debrisData.high_risk_debris
          .sort((a, b) => {
            const sizeOrder = { 'LARGE': 3, 'MEDIUM': 2, 'SMALL': 1 }
            const sizeA = sizeOrder[a.rcs_size] || 0
            const sizeB = sizeOrder[b.rcs_size] || 0
            return sizeB - sizeA
          })
        
        setDebrisList(sortedDebris)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function analyzeRisks(mode) {
    if (satellites.length === 0 || debrisList.length === 0) {
      setError('No satellites or debris data available')
      return
    }

    // Set analyzing state for the specific mode
    const setAnalysisState = mode === 'fast' ? setFastAnalysis : setSmartAnalysis
    
    setAnalysisState(prev => ({ ...prev, analyzing: true, progress: 0 }))
    
    const results = []
    let allCombinations = []
    
    // Choose combinations based on mode
    if (mode === 'smart') {
      for (const sat of satellites) {
        for (const debris of debrisList) {
          allCombinations.push({ sat, debris })
        }
      }
    } else {
      // Fast Mode: Use intelligent screening to find close pairs
      try {
        setAnalysisState(prev => ({ ...prev, progress: 5 }))
        
        const screeningResponse = await fetch('http://localhost:5000/api/find_close_pairs?threshold_km=25&max_satellites=50&max_debris=2000')
        const screeningData = await screeningResponse.json()
        
        if (screeningData.status === 'success' && screeningData.close_pairs) {
          // Build combinations from close pairs only
          for (const pair of screeningData.close_pairs) {
            const sat = pair.satellite
            for (const debrisInfo of pair.close_debris) {
              allCombinations.push({ 
                sat, 
                debris: { norad_id: debrisInfo.norad_id, name: debrisInfo.name },
                initialDistance: debrisInfo.distance_km
              })
            }
          }
          
          console.log(`Fast Mode: Found ${allCombinations.length} close pairs to analyze`)
          setAnalysisState(prev => ({ ...prev, progress: 10 }))
        } else {
          setError('No close satellite-debris pairs found within 25km')
          setAnalysisState(prev => ({ ...prev, analyzing: false }))
          return
        }
      } catch (err) {
        setError(`Screening failed: ${err.message}`)
        setAnalysisState(prev => ({ ...prev, analyzing: false }))
        return
      }
    }
    
    if (allCombinations.length === 0) {
      setError('No combinations to analyze')
      setAnalysisState(prev => ({ ...prev, analyzing: false }))
      return
    }
    
    const total = allCombinations.length
    let completed = 0

    // Analysis parameters based on mode
    const params = mode === 'smart'
      ? { duration: 15, step: 90, samples: 200, batchSize: 10, pollInterval: 500, screeningThreshold: 50.0 }
      : { duration: 10, step: 120, samples: 100, batchSize: 5, pollInterval: 500, screeningThreshold: 1000.0 }

    try {
      for (let i = 0; i < allCombinations.length; i += params.batchSize) {
        const batch = allCombinations.slice(i, i + params.batchSize)
        
        const batchPromises = batch.map(async ({ sat, debris, initialDistance }) => {
          try {
            const payload = {
              debris: debris.norad_id,
              satellite_norad: sat.norad_id,
              duration_minutes: params.duration,
              step_seconds: params.step,
              samples: params.samples,
              position_uncertainty_km: 2.0,
              screening_threshold_km: params.screeningThreshold,
              debris_radius_km: 0.5,
              satellite_radius_km: 0.01,
              visualize: false,
              use_improved_accuracy: true
            }

            const jobResponse = await startDebrisJob(payload)
            const jobId = jobResponse.job_id

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
                riskLevel: getRiskLevel(jobStatus.result.probability || 0).level,
                initialDistance: initialDistance || null
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
        const progressPercent = Math.round((completed / total) * 100)
        setAnalysisState(prev => ({ ...prev, progress: progressPercent }))
      }

      // Sort by probability (highest first)
      results.sort((a, b) => b.probability - a.probability)
      setAnalysisState(prev => ({ 
        ...prev, 
        analyzing: false, 
        results, 
        complete: true 
      }))
    } catch (err) {
      setError(err.message)
      setAnalysisState(prev => ({ ...prev, analyzing: false }))
    }
  }

  function getRiskLevel(probability) {
    if (probability === 0) return { level: 'SAFE', color: '#4caf50', icon: '✅' }
    if (probability < 0.001) return { level: 'LOW', color: '#8bc34a', icon: '⚠️' }
    if (probability < 0.01) return { level: 'MODERATE', color: '#ff9800', icon: '⚠️' }
    if (probability < 0.1) return { level: 'HIGH', color: '#ff5722', icon: '🔴' }
    return { level: 'CRITICAL', color: '#f44336', icon: '🚨' }
  }

  function renderResults(results, mode) {
    if (results.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h3>Analysis Running</h3>
          <p>Results will appear here as the analysis progresses...</p>
        </div>
      )
    }

    return (
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
          
          {results.map((item, index) => {
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
                    {formatProbability(item.probability)}
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

        {results.filter(r => r.probability > 0).length === 0 && (
          <div className="no-risk-message">
            ✅ Excellent news! No collision risks detected for any satellite-debris combinations.
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading satellites and debris data...</p>
      </div>
    )
  }

  const currentAnalysis = activeTab === 'fast' ? fastAnalysis : smartAnalysis
  const modeInfo = activeTab === 'fast' 
    ? { name: 'Fast Mode', combinations: 'Variable (close pairs only)', threshold: '25km', duration: '5-10 min' }
    : { name: 'Smart Analysis', combinations: `${satellites.length * debrisList.length} (${satellites.length} x ${debrisList.length})`, threshold: '50km', duration: '1-2 hrs' }

  return (
    <div className="risk-ranking">
      <div className="ranking-header">
        <h2>Collision Risk Ranking</h2>
        <p>Parallel analysis of collision probabilities - both modes running simultaneously</p>
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
        </div>

        {/* Tab Navigation */}
        <div className="analysis-tabs">
          <button 
            className={`tab-btn ${activeTab === 'fast' ? 'active' : ''}`}
            onClick={() => setActiveTab('fast')}
          >
            <span className="tab-icon">⚡</span>
            <span className="tab-label">Fast Mode (Top 50, 25km)</span>
            {fastAnalysis.analyzing && (
              <span className="tab-progress">{fastAnalysis.progress}%</span>
            )}
            {fastAnalysis.complete && !fastAnalysis.analyzing && (
              <span className="tab-complete">✓</span>
            )}
          </button>
          
          <button 
            className={`tab-btn ${activeTab === 'smart' ? 'active' : ''}`}
            onClick={() => setActiveTab('smart')}
          >
            <span className="tab-icon">🎯</span>
            <span className="tab-label">Smart Analysis (50km)</span>
            {smartAnalysis.analyzing && (
              <span className="tab-progress">{smartAnalysis.progress}%</span>
            )}
            {smartAnalysis.complete && !smartAnalysis.analyzing && (
              <span className="tab-complete">✓</span>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Progress indicator for current tab */}
      {currentAnalysis.analyzing && (
        <div className="progress-container">
          <h3>{modeInfo.name} in Progress</h3>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${currentAnalysis.progress}%` }}
            ></div>
          </div>
          <p>{currentAnalysis.progress}% complete - Analyzing {modeInfo.combinations} combinations</p>
          <p className="progress-note">
            {activeTab === 'fast' 
              ? 'Fast mode: Top 50 satellites with debris within 25km - Only real threats analyzed'
              : 'Smart mode: 200 samples, 15 min duration, 50km screening (~1-2 hours)'
            }
          </p>
        </div>
      )}

      {/* Status banner when complete */}
      {currentAnalysis.complete && !currentAnalysis.analyzing && (
        <div className="analysis-status">
          <span className="status-icon">✓</span>
          <span className="status-text">
            {modeInfo.name} Complete: {currentAnalysis.results.length} combinations analyzed
          </span>
        </div>
      )}

      {/* Results for current tab */}
      {renderResults(currentAnalysis.results, activeTab)}
    </div>
  )
}
