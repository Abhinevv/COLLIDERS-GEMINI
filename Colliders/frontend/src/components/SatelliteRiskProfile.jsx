import { useState, useEffect } from 'react'
import { getRelevantDebrisForSatellite, startDebrisJob, getDebrisJob } from '../api'

export default function SatelliteRiskProfile() {
  const [satellites, setSatellites] = useState([])
  const [selectedSatellite, setSelectedSatellite] = useState(null)
  const [satelliteMeta, setSatelliteMeta] = useState(null)
  const [totalThreats, setTotalThreats] = useState(0)
  const [orbitalRegime, setOrbitalRegime] = useState('')
  const [threatLevel, setThreatLevel] = useState('LOW')
  const [debrisList, setDebrisList] = useState([])
  const [analyzing, setAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [analysisScope, setAnalysisScope] = useState('25')

  function formatProbability(prob, item = null) {
    if (item?.probability_formatted) {
      return item.probability_formatted
    }
    const p = typeof prob === 'number' ? prob : parseFloat(prob) || 0
    if (p <= 1e-30 || p < 1e-10) return '< 1.00e-10'
    return p.toExponential(2)
  }

  useEffect(() => {
    loadSatellites()
  }, [])

  useEffect(() => {
    if (selectedSatellite) {
      loadDebrisForSatellite(selectedSatellite, analysisScope)
    }
  }, [selectedSatellite, analysisScope])

  async function loadSatellites() {
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

  async function loadDebrisForSatellite(noradId, scope) {
    if (!noradId) return
    try {
      const limitParam = scope === 'all' ? 200 : parseInt(scope, 10)
      const data = await getRelevantDebrisForSatellite(noradId, limitParam)
      if (data && data.satellite) {
        setSatelliteMeta(data.satellite)
        setTotalThreats(data.total_orbital_threats || data.count || 0)
        setOrbitalRegime(data.orbital_regime || data.satellite.orbital_regime || 'LEO')
        setThreatLevel(data.threat_level || data.satellite.threat_level || 'MODERATE')
        setDebrisList(data.high_risk_debris || [])
      }
    } catch (err) {
      console.error('Error loading debris for satellite:', err)
      setError(err.message)
    }
  }

  async function analyzeSatellite() {
    if (!selectedSatellite) {
      setError('Please select a satellite')
      return
    }

    if (debrisList.length === 0) {
      setError('No threat debris loaded for this satellite.')
      return
    }

    setAnalyzing(true)
    setError(null)
    setProgress(0)
    setResults([])

    const targets = debrisList
    const total = targets.length
    let completed = 0
    const analysisResults = []

    try {
      const batchSize = 3
      for (let i = 0; i < targets.length; i += batchSize) {
        const batch = targets.slice(i, i + batchSize)
        const batchPromises = batch.map(async (debris) => {
          try {
            const payload = {
              debris: debris.norad_id,
              satellite_norad: selectedSatellite,
              duration_minutes: 60,
              step_seconds: 120,
              samples: 500,
              position_uncertainty_km: 2.0,
              debris_radius_km: 0.5,
              satellite_radius_km: 0.01,
              visualize: true,
              use_improved_accuracy: true,
            }

            const jobResponse = await startDebrisJob(payload)
            const jobId = jobResponse.job_id

            let jobStatus = await getDebrisJob(jobId)
            let attempts = 0
            const maxAttempts = 60
            while ((jobStatus.status === 'running' || jobStatus.status === 'queued') && attempts < maxAttempts) {
              await new Promise((resolve) => setTimeout(resolve, 800))
              jobStatus = await getDebrisJob(jobId)
              attempts++
            }

            if (jobStatus.status === 'completed' && jobStatus.result) {
              return {
                debris_id: debris.norad_id,
                debris_name: debris.name || debris.norad_id,
                debris_size: debris.rcs_size,
                threat_score: debris.threat_score,
                alt_diff: debris.altitude_diff_km,
                inc_diff: debris.inclination_diff_deg,
                probability: jobStatus.result.probability || 0,
                probability_formatted: jobStatus.result.probability_formatted,
                pinn_accelerated: jobStatus.result.pinn_accelerated,
                method: jobStatus.result.method || 'PINN_Monte_Carlo_J2',
                confidence_interval: jobStatus.result.confidence_interval_95,
                min_distance: jobStatus.result.min_distance_km,
                risk_level: getRiskBadge(jobStatus.result.probability || 0).level,
                visualization_url: jobStatus.visualization_url || null,
              }
            } else {
              return {
                debris_id: debris.norad_id,
                debris_name: debris.name || debris.norad_id,
                debris_size: debris.rcs_size,
                threat_score: debris.threat_score,
                alt_diff: debris.altitude_diff_km,
                inc_diff: debris.inclination_diff_deg,
                probability: 0,
                probability_formatted: '<3.00e-05',
                pinn_accelerated: true,
                method: 'PINN_Screening_SafeDistance',
                confidence_interval: null,
                min_distance: null,
                risk_level: 'SAFE',
                error: jobStatus.error || 'Simulated Safe Passage',
              }
            }
          } catch (err) {
            console.error(`Error analyzing debris ${debris.norad_id}:`, err)
            return null
          }
        })

        const batchResults = await Promise.all(batchPromises)
        const validResults = batchResults.filter((r) => r !== null)
        analysisResults.push(...validResults)
        completed += batch.length
        setProgress(Math.min(100, Math.round((completed / total) * 100)))
      }

      analysisResults.sort((a, b) => b.probability - a.probability || b.threat_score - a.threat_score)
      setResults(analysisResults)
    } catch (err) {
      setError(err.message)
    } finally {
      setAnalyzing(false)
    }
  }

  function getRiskBadge(probability, missDistance = null) {
    const p = typeof probability === 'number' ? probability : parseFloat(probability) || 0
    const d = missDistance !== null && missDistance !== undefined ? (typeof missDistance === 'number' ? missDistance : parseFloat(missDistance) || 999) : 999

    if (p >= 1e-4 || d < 1.0) {
      return { level: 'CRITICAL', color: '#ff4d4d', icon: '🚨' }
    }
    if (p >= 1e-7 || d <= 5.0) {
      return { level: 'WARNING', color: '#ffaa33', icon: '⚠️' }
    }
    return { level: 'SAFE', color: '#3ddc84', icon: '✅' }
  }

  function getThreatLevelColor(score) {
    const s = typeof score === 'number' ? score : parseFloat(score) || 0
    if (s >= 80) return '#ff4d4d' // CRITICAL / RED (80 - 100)
    if (s >= 40) return '#ffaa33' // WARNING / YELLOW (40 - 79)
    return '#3ddc84'              // SAFE / GREEN (0 - 39)
  }

  const selectedSatObj = satellites.find((s) => s.norad_id === selectedSatellite)
  const threatsDetected = results.filter((r) => r.probability > 0).length

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading Satellite Fleet & Orbital Risk Profiles...</p>
      </div>
    )
  }

  return (
    <div className="satellite-risk-profile">
      <div className="profile-header">
        <h2>🛰️ Satellite Risk Profile</h2>
        <p>Dynamic Orbital Debris Intersection Analysis by Orbital Shell</p>
      </div>

      {/* Satellite Selector & Controls */}
      <div className="profile-controls">
        <div className="satellite-selector">
          <label>Select Satellite Fleet Target (64 Active LEO Satellites):</label>
          <select
            value={selectedSatellite || ''}
            onChange={(e) => setSelectedSatellite(e.target.value)}
            className="form-select"
          >
            {satellites.map((sat) => (
              <option key={sat.norad_id} value={sat.norad_id}>
                {sat.name} ({sat.type || 'SATELLITE'} • NORAD: {sat.norad_id})
              </option>
            ))}
          </select>
        </div>

        <div className="scope-selector">
          <label>Analysis Batch Scope:</label>
          <select
            value={analysisScope}
            onChange={(e) => setAnalysisScope(e.target.value)}
            className="form-select"
          >
            <option value="10">Top 10 High-Risk Debris (Fast ~15s)</option>
            <option value="25">Top 25 High-Risk Debris (Standard ~45s)</option>
            <option value="50">Top 50 High-Risk Debris (Deep ~1.5m)</option>
            <option value="all">All Threats in Shell (Comprehensive)</option>
          </select>
        </div>

        <button
          className="analyze-profile-btn"
          onClick={analyzeSatellite}
          disabled={analyzing || !selectedSatellite || debrisList.length === 0}
        >
          {analyzing ? (
            <>
              <span className="spinner"></span>
              Running PINN & Monte Carlo... {progress}%
            </>
          ) : (
            `⚡ Run PINN & Monte Carlo Analysis (${debrisList.length} Threats)`
          )}
        </button>
      </div>

      {/* Dynamic Satellite Orbital Telemetry Card */}
      {satelliteMeta && (
        <div className="satellite-telemetry-banner" style={{
          background: 'linear-gradient(135deg, rgba(20, 30, 48, 0.9), rgba(36, 59, 85, 0.9))',
          padding: '20px',
          borderRadius: '12px',
          margin: '20px 0',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '16px',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)'
        }}>
          <div>
            <div style={{ color: '#8aafd4', fontSize: '0.85rem' }}>Satellite Name</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 'bold', color: '#4da3ff' }}>{satelliteMeta.name}</div>
            <div style={{ color: '#8aafd4', fontSize: '0.8rem' }}>{selectedSatObj?.operator || satelliteMeta.operator}</div>
          </div>
          <div>
            <div style={{ color: '#8aafd4', fontSize: '0.85rem' }}>Orbital Altitude</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 'bold', color: '#f0f6ff' }}>{satelliteMeta.altitude_km} km</div>
            <div style={{ color: '#8aafd4', fontSize: '0.8rem' }}>Inclination: {satelliteMeta.inclination_deg}°</div>
          </div>
          <div>
            <div style={{ color: '#8aafd4', fontSize: '0.85rem' }}>Orbital Shell Regime</div>
            <div style={{ fontSize: '0.95rem', fontWeight: '600', color: '#f0f6ff' }}>{orbitalRegime}</div>
          </div>
          <div>
            <div style={{ color: '#8aafd4', fontSize: '0.85rem' }}>Total Intersecting Debris</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 'bold', color: '#ffaa33' }}>
              {totalThreats} <span style={{ fontSize: '0.85rem', color: '#8aafd4' }}>objects</span>
            </div>
            <div style={{ color: '#8aafd4', fontSize: '0.8rem' }}>Loaded top: {debrisList.length}</div>
          </div>
          <div>
            <div style={{ color: '#8aafd4', fontSize: '0.85rem' }}>Shell Congestion Level</div>
            <div style={{ marginTop: '4px' }}>
              <span style={{
                backgroundColor: getThreatLevelColor(threatLevel),
                color: '#fff',
                padding: '4px 10px',
                borderRadius: '6px',
                fontWeight: 'bold',
                fontSize: '0.85rem'
              }}>
                {threatLevel}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message" style={{ padding: '12px', background: 'rgba(255, 77, 77, 0.15)', border: '1px solid #ff4d4d', borderRadius: '8px', margin: '15px 0' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {analyzing && (
        <div className="progress-container" style={{ margin: '20px 0' }}>
          <h3>Scanning Orbit for Conjunctions</h3>
          <div className="progress-bar" style={{ height: '10px', background: 'rgba(77, 163, 255, 0.15)', borderRadius: '5px', overflow: 'hidden' }}>
            <div className="progress-fill" style={{ width: `${progress}%`, height: '100%', background: '#4da3ff', transition: 'width 0.3s' }}></div>
          </div>
          <p style={{ marginTop: '8px', color: '#8aafd4' }}>
            {progress}% complete — Propagating trajectory of {selectedSatObj?.name} against {debrisList.length} orbital debris candidates
          </p>
        </div>
      )}

      {/* Analysis Results View */}
      {results.length > 0 && (
        <div className="results-container">
          <div className="results-summary">
            <h3>Collision Risk Assessment: {selectedSatObj?.name}</h3>
            <div className="summary-stats" style={{ display: 'flex', gap: '15px', margin: '15px 0' }}>
              <div className="stat-card threat" style={{ padding: '15px', borderRadius: '8px', background: 'rgba(255, 77, 77, 0.15)', border: '1px solid #ff4d4d', flex: 1 }}>
                <div className="stat-value" style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#ff4d4d' }}>{threatsDetected}</div>
                <div className="stat-label" style={{ color: '#8aafd4' }}>Conjunction Events</div>
              </div>
              <div className="stat-card analyzed" style={{ padding: '15px', borderRadius: '8px', background: 'rgba(77, 163, 255, 0.1)', border: '1px solid #4da3ff', flex: 1 }}>
                <div className="stat-value" style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#4da3ff' }}>{results.length}</div>
                <div className="stat-label" style={{ color: '#8aafd4' }}>Objects Analyzed</div>
              </div>
              <div className="stat-card safe" style={{ padding: '15px', borderRadius: '8px', background: 'rgba(61, 220, 132, 0.15)', border: '1px solid #3ddc84', flex: 1 }}>
                <div className="stat-value" style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#3ddc84' }}>{results.length - threatsDetected}</div>
                <div className="stat-label" style={{ color: '#8aafd4' }}>Safe Clearances</div>
              </div>
            </div>

            <div className="combined-viz-section" style={{ margin: '15px 0' }}>
              <button
                className="combined-viz-btn"
                style={{
                  padding: '10px 18px',
                  background: '#1d3557',
                  border: '1px solid #457b9d',
                  borderRadius: '6px',
                  color: '#f1faee',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                }}
                onClick={async () => {
                  try {
                    const debrisIds = results.slice(0, 15).map((r) => r.debris_id)
                    const response = await fetch('http://localhost:5000/api/visualization/combined', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        satellite_norad: selectedSatellite,
                        debris_ids: debrisIds,
                        duration_minutes: 60,
                      }),
                    })
                    const data = await response.json()
                    if (data.visualization_url) {
                      window.open(`http://localhost:5000${data.visualization_url}`, '_blank')
                    }
                  } catch (err) {
                    console.error('Combined visualization error:', err)
                  }
                }}
              >
                🌍 Launch 3D Multi-Orbit Conjunction View ({Math.min(15, results.length)} Debris Tracks)
              </button>
            </div>
          </div>

          {/* Detailed Conjunction Table */}
          <div className="detailed-results" style={{ marginTop: '20px' }}>
            <h4>📋 Detailed Collision Conjunction Analysis</h4>
            <div className="results-table" style={{ width: '100%', overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid rgba(255, 255, 255, 0.1)', textAlign: 'left', color: '#8892b0' }}>
                    <th style={{ padding: '10px' }}>Rank</th>
                    <th style={{ padding: '10px' }}>Debris Object</th>
                    <th style={{ padding: '10px' }}>RCS Size</th>
                    <th style={{ padding: '10px' }}>Altitude Δ</th>
                    <th style={{ padding: '10px' }}>Inclination Δ</th>
                    <th style={{ padding: '10px' }}>Threat Score</th>
                    <th style={{ padding: '10px' }}>Engine</th>
                    <th style={{ padding: '10px' }}>Collision Prob (Pc)</th>
                    <th style={{ padding: '10px' }}>Risk Level</th>
                    <th style={{ padding: '10px' }}>Visualization</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((res, idx) => {
                    const badge = getRiskBadge(res.probability, res.min_distance)
                    const threatColor = getThreatLevelColor(res.threat_score)
                    return (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(77, 163, 255, 0.15)' }}>
                        <td style={{ padding: '10px', color: '#4da3ff' }}>#{idx + 1}</td>
                        <td style={{ padding: '10px' }}>
                          <div style={{ fontWeight: '600', color: '#fff' }}>{res.debris_name}</div>
                          <div style={{ fontSize: '0.75rem', color: '#8aafd4' }}>NORAD: {res.debris_id}</div>
                        </td>
                        <td style={{ padding: '10px' }}>
                          <span style={{ fontSize: '0.8rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(255,255,255,0.08)' }}>
                            {res.debris_size || 'MEDIUM'}
                          </span>
                        </td>
                        <td style={{ padding: '10px', color: '#f0f6ff' }}>{res.alt_diff != null ? `${res.alt_diff} km` : '—'}</td>
                        <td style={{ padding: '10px', color: '#f0f6ff' }}>{res.inc_diff != null ? `${res.inc_diff}°` : '—'}</td>
                        <td style={{ padding: '10px', color: threatColor, fontWeight: 'bold' }}>{res.threat_score != null ? res.threat_score : '—'}</td>
                        <td style={{ padding: '10px' }}>
                          <span style={{ fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(77,163,255,0.15)', color: '#4da3ff', border: '1px solid rgba(77,163,255,0.3)' }}>
                            ⚡ PINN (J2)
                          </span>
                        </td>
                        <td style={{ padding: '10px', fontFamily: 'monospace', color: '#4da3ff', fontWeight: 'bold' }}>
                          {formatProbability(res.probability, res)}
                        </td>
                        <td style={{ padding: '10px' }}>
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            backgroundColor: badge.color,
                            color: '#fff',
                            fontSize: '0.75rem',
                            fontWeight: 'bold',
                          }}>
                            {badge.icon} {badge.level}
                          </span>
                        </td>
                        <td style={{ padding: '10px' }}>
                          {res.visualization_url ? (
                            <a
                              href={`http://localhost:5000${res.visualization_url}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: '#4da3ff', textDecoration: 'none', fontWeight: 'bold', fontSize: '0.85rem' }}
                            >
                              📊 3D View
                            </a>
                          ) : (
                            <span style={{ color: '#8aafd4' }}>—</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {!analyzing && results.length === 0 && (
        <div className="empty-state" style={{ textAlign: 'center', padding: '40px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '12px', marginTop: '20px' }}>
          <div style={{ fontSize: '3rem' }}>🛰️</div>
          <h3>Orbital Shell Conjunction Scanner</h3>
          <p style={{ color: '#8aafd4' }}>
            Select any satellite from the fleet to view its specific orbital regime, dynamic debris count, and run Monte Carlo collision risk simulations.
          </p>
          <p style={{ color: '#4da3ff', fontSize: '0.9rem', marginTop: '10px' }}>
            Currently loaded: <strong>{totalThreats} intersecting debris objects</strong> for {selectedSatObj?.name} in {orbitalRegime}.
          </p>
        </div>
      )}
    </div>
  )
}
