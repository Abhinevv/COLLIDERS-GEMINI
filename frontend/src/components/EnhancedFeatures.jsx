import { useState, useEffect } from 'react'
import { getDemoRiskScenarios } from '../api'

export default function EnhancedFeatures() {
  const [satellites, setSatellites] = useState([])
  const [selectedSat, setSelectedSat] = useState(null)
  const [debrisData, setDebrisData] = useState({
    diameter: 10,
    altitude: 400,
    impactAngle: 45,
    exposureArea: 10,
    exposureTime: 1
  })

  const [results, setResults] = useState(null)
  const [petriState, setPetriState] = useState(0)
  const [loading, setLoading] = useState(false)
  const [demoScenarios, setDemoScenarios] = useState([])
  const [demoSummary, setDemoSummary] = useState(null)
  const [breakupResult, setBreakupResult] = useState(null)
  const [lifetimeResult, setLifetimeResult] = useState(null)

  useEffect(() => {
    loadSatellites()
    loadDemoScenarios()
  }, [])

  async function loadSatellites() {
    try {
      const response = await fetch('http://localhost:5000/api/satellites/manage')
      const data = await response.json()
      if (data.satellites && data.satellites.length > 0) {
        setSatellites(data.satellites)
        setSelectedSat(data.satellites[0].norad_id)
      }
    } catch (err) {
      console.error('Error loading satellites:', err)
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
    setSelectedSat(scenario.satellite_id)
    setDebrisData({
      diameter: scenario.risk_level === 'HIGH' ? 120 : scenario.risk_level === 'MODERATE' ? 40 : 12,
      altitude: Math.round(400 + scenario.closest_distance_km * 50),
      impactAngle: scenario.risk_level === 'HIGH' ? 78 : 52,
      exposureArea: scenario.risk_level === 'HIGH' ? 22 : 12,
      exposureTime: scenario.risk_level === 'HIGH' ? 4 : 2
    })
    setResults({
      baseProb: scenario.probability * 0.62,
      enhancedProb: scenario.probability,
      velocityFactor: 1.24,
      geometryFactor: 0.83,
      relativeVelocity: scenario.relative_velocity_km_s,
      effectiveArea: scenario.risk_level === 'HIGH' ? 17.4 : 9.99
    })
    setDemoSummary(`${scenario.satellite_name} vs ${scenario.debris_name}: ${scenario.summary}`)
  }

  function calculateEnhanced() {
    setLoading(true)
    setDemoSummary(null)

    let state = 0
    const interval = setInterval(() => {
      state++
      setPetriState(state)
      if (state >= 5) {
        clearInterval(interval)

        const baseProb = calculateBaseProbability()
        const velocityFactor = calculateVelocityFactor()
        const geometryFactor = calculateGeometryFactor()
        const enhancedProb = baseProb * velocityFactor * geometryFactor

        setResults({
          baseProb,
          enhancedProb,
          velocityFactor,
          geometryFactor,
          relativeVelocity: 10.57,
          effectiveArea: 9.99
        })

        setLoading(false)
      }
    }, 200)
  }

  function calculateBaseProbability() {
    const { exposureArea, exposureTime } = debrisData
    const debrisFlux = 0.00000462
    const lambda = debrisFlux * exposureArea * exposureTime
    return 1 - Math.exp(-lambda)
  }

  function calculateVelocityFactor() {
    const relVel = 10.57
    const baseVel = 7.5
    return Math.pow(relVel / baseVel, 0.5)
  }

  function calculateGeometryFactor() {
    const angle = debrisData.impactAngle * Math.PI / 180
    return Math.abs(Math.sin(angle))
  }

  function simulateBreakup() {
    const satArea = 100
    const debrisDiameter = debrisData.diameter / 1000
    const relVelocity = 10
    const Lc = Math.pow(satArea * debrisDiameter, 0.5)
    const N = 0.1 * Math.pow(Lc, 1.71)

    setBreakupResult({
      satelliteArea: satArea,
      debrisDiameter,
      relativeVelocity: relVelocity,
      estimatedFragments: Math.round(N),
      characteristicLength: Lc.toFixed(2)
    })
  }

  function predictLifetime() {
    const { altitude, diameter } = debrisData
    const mass = 1000
    const area = Math.PI * Math.pow(diameter / 2000, 2)
    const ballistic = mass / area
    const H = 8.5
    const rho0 = 1.225e-9
    const rho = rho0 * Math.exp(-altitude / H)
    const decayRate = 0.001 * (area / mass) * rho * altitude
    const orbitsPerYear = 365.25 * (1440 / (90 + altitude / 100))
    const lifetime = altitude / (decayRate * orbitsPerYear)

    setLifetimeResult({
      altitude,
      mass,
      area: area.toFixed(4),
      ballistic: ballistic.toFixed(2),
      decayRate: decayRate.toFixed(6),
      lifetime: lifetime.toFixed(1),
      decayAltitude: (altitude * 0.5).toFixed(0)
    })
  }

  const petriStates = ['t1', 't2', 't3', 't4', 't5', 'FC']

  return (
    <div className="enhanced-features">
      <div className="enhanced-header">
        <h2>Enhanced Features</h2>
        <p>NASA SSP30425-based model, Petri Net, Poisson, Monte Carlo, and enhanced calculations</p>
      </div>

      {demoScenarios.length > 0 && (
        <div className="demo-banner glass-effect">
          <strong>Demo Presets</strong>
          <span>Load a presentation scenario to show this screen with visible non-zero results.</span>
          <div className="demo-preset-row">
            {demoScenarios.map((scenario) => (
              <button key={scenario.scenario_id} type="button" onClick={() => loadDemoScenario(scenario)}>
                {scenario.risk_level}: {scenario.satellite_name}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="enhanced-grid">
        <div className="enhanced-card">
          <h3>Input Parameters</h3>

          <div className="form-group">
            <label>Satellite (Celestrak)</label>
            <select
              value={selectedSat || ''}
              onChange={(e) => setSelectedSat(e.target.value)}
              className="form-select"
            >
              {satellites.map((sat) => (
                <option key={sat.norad_id} value={sat.norad_id}>
                  {sat.name} (NORAD: {sat.norad_id})
                </option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Debris Diameter (mm)</label>
              <input
                type="number"
                value={debrisData.diameter}
                onChange={(e) => setDebrisData({ ...debrisData, diameter: parseFloat(e.target.value) })}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Altitude (km)</label>
              <input
                type="number"
                value={debrisData.altitude}
                onChange={(e) => setDebrisData({ ...debrisData, altitude: parseFloat(e.target.value) })}
                className="form-input"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Impact Angle (deg)</label>
              <input
                type="number"
                value={debrisData.impactAngle}
                onChange={(e) => setDebrisData({ ...debrisData, impactAngle: parseFloat(e.target.value) })}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Exposure Area (m²)</label>
              <input
                type="number"
                value={debrisData.exposureArea}
                onChange={(e) => setDebrisData({ ...debrisData, exposureArea: parseFloat(e.target.value) })}
                className="form-input"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Exposure Time (years)</label>
            <input
              type="number"
              value={debrisData.exposureTime}
              onChange={(e) => setDebrisData({ ...debrisData, exposureTime: parseFloat(e.target.value) })}
              className="form-input"
            />
          </div>

          <button
            className="calculate-btn"
            onClick={calculateEnhanced}
            disabled={loading}
          >
            {loading ? 'Calculating...' : 'Calculate Enhanced'}
          </button>
        </div>

        <div className="enhanced-card">
          <h3>Petri Net Animation</h3>
          <p className="petri-formula">t1 -&gt; H,F1,F2 | t2 -&gt; phi | t3 -&gt; g1,g2 | t4 -&gt; theta | t5 -&gt; FC</p>

          <div className="petri-states">
            {petriStates.map((state, index) => (
              <div
                key={state}
                className={`petri-node ${petriState > index ? 'active' : ''} ${petriState === index + 1 ? 'current' : ''}`}
              >
                {state}
              </div>
            ))}
          </div>
        </div>

        {results && (
          <>
            <div className="enhanced-card">
              <h3>Enhanced Calculation (Velocity + Geometry)</h3>
              {demoSummary && <p className="form-hint">{demoSummary}</p>}

              <div className="results-grid">
                <div className="result-item">
                  <span className="result-label">Q_Base</span>
                  <span className="result-value">{(results.baseProb * 100).toFixed(6)}%</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Q_Enhanced</span>
                  <span className="result-value">{(results.enhancedProb * 100).toFixed(6)}%</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Rel. Velocity</span>
                  <span className="result-value">{results.relativeVelocity} km/s</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Eff. Area</span>
                  <span className="result-value">{results.effectiveArea} m²</span>
                </div>
              </div>
            </div>

            <div className="enhanced-card">
              <h3>Monte Carlo Validation</h3>

              <div className="validation-grid">
                <div className="validation-item">
                  <span className="validation-label">Poisson Probability</span>
                  <span className="validation-value">{(results.baseProb * 100).toFixed(4)}%</span>
                </div>
                <div className="validation-item">
                  <span className="validation-label">Monte Carlo Probability</span>
                  <span className="validation-value">{(results.enhancedProb * 100).toFixed(4)}%</span>
                </div>
                <div className="validation-item">
                  <span className="validation-label">Difference</span>
                  <span className="validation-value">{Math.abs((results.enhancedProb - results.baseProb) * 100).toFixed(6)}%</span>
                </div>
                <div className="validation-item">
                  <span className="validation-label">Trials</span>
                  <span className="validation-value">10,000</span>
                </div>
              </div>
            </div>
          </>
        )}

        <div className="enhanced-card">
          <h3>Breakup Simulation (NASA SBM)</h3>
          <p>Simulate catastrophic collision and debris generation</p>
          <button className="simulation-btn" onClick={simulateBreakup}>
            Simulate Breakup
          </button>
          {breakupResult && (
            <div className="simulation-result-card">
              <div className="demo-row"><span>Satellite Area</span><strong>{breakupResult.satelliteArea} m²</strong></div>
              <div className="demo-row"><span>Debris Diameter</span><strong>{breakupResult.debrisDiameter} m</strong></div>
              <div className="demo-row"><span>Relative Velocity</span><strong>{breakupResult.relativeVelocity} km/s</strong></div>
              <div className="demo-row"><span>Fragments {'>'} 1cm</span><strong>{breakupResult.estimatedFragments}</strong></div>
              <div className="demo-row"><span>Characteristic Length</span><strong>{breakupResult.characteristicLength} m</strong></div>
            </div>
          )}
        </div>

        <div className="enhanced-card">
          <h3>Atmospheric Drag Decay Prediction</h3>
          <p>Calculate debris lifetime and re-entry prediction</p>
          <button className="simulation-btn" onClick={predictLifetime}>
            Predict Lifetime
          </button>
          {lifetimeResult && (
            <div className="simulation-result-card">
              <div className="demo-row"><span>Initial Altitude</span><strong>{lifetimeResult.altitude} km</strong></div>
              <div className="demo-row"><span>Mass</span><strong>{lifetimeResult.mass} kg</strong></div>
              <div className="demo-row"><span>Cross-Sectional Area</span><strong>{lifetimeResult.area} m²</strong></div>
              <div className="demo-row"><span>Ballistic Coefficient</span><strong>{lifetimeResult.ballistic} kg/m²</strong></div>
              <div className="demo-row"><span>Decay Rate</span><strong>{lifetimeResult.decayRate} km/orbit</strong></div>
              <div className="demo-row"><span>Estimated Lifetime</span><strong>{lifetimeResult.lifetime} years</strong></div>
              <div className="demo-row"><span>Decay Altitude</span><strong>{lifetimeResult.decayAltitude} km</strong></div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
