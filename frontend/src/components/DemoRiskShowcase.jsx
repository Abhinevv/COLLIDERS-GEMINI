import { useEffect, useState } from 'react'
import { getDemoRiskScenarios } from '../api'

function formatProbability(probability) {
  const percentage = probability * 100
  if (percentage < 0.0001) {
    return `${percentage.toFixed(7)}%`
  }
  return `${percentage.toFixed(4)}%`
}

export default function DemoRiskShowcase() {
  const [scenarios, setScenarios] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadScenarios()
  }, [])

  async function loadScenarios() {
    setLoading(true)
    setError(null)
    try {
      const data = await getDemoRiskScenarios()
      setScenarios(data.scenarios || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading demo risk scenarios...</p>
      </div>
    )
  }

  return (
    <div className="demo-risk-showcase">
      <div className="ranking-header">
        <h2>Demo Risk Analysis</h2>
        <p>Presentation-only sample scenarios with curated non-zero probabilities.</p>
      </div>

      <div className="demo-banner glass-effect">
        <strong>Demo Mode</strong>
        <span>These examples are curated for presentation and do not affect real tracking, ranking, or database analysis.</span>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="demo-grid">
        {scenarios.map((scenario) => (
          <div key={scenario.scenario_id} className="demo-card glass-effect">
            <div className="demo-card-top">
              <div>
                <h3>{scenario.satellite_name}</h3>
                <p>NORAD {scenario.satellite_id}</p>
              </div>
              <span className={`demo-risk-pill ${scenario.risk_level.toLowerCase()}`}>
                {scenario.risk_level}
              </span>
            </div>

            <div className="demo-row">
              <span>Debris</span>
              <strong>{scenario.debris_name}</strong>
            </div>
            <div className="demo-row">
              <span>Demo ID</span>
              <strong>{scenario.debris_id}</strong>
            </div>
            <div className="demo-row">
              <span>Probability</span>
              <strong>{formatProbability(scenario.probability)}</strong>
            </div>
            <div className="demo-row">
              <span>Closest Distance</span>
              <strong>{scenario.closest_distance_km} km</strong>
            </div>
            <div className="demo-row">
              <span>Relative Velocity</span>
              <strong>{scenario.relative_velocity_km_s} km/s</strong>
            </div>
            <div className="demo-row">
              <span>Time to Approach</span>
              <strong>{scenario.time_to_approach_minutes} min</strong>
            </div>

            <p className="demo-summary">{scenario.summary}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
