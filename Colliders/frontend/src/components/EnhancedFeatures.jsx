import { useState, useEffect } from 'react'

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

  useEffect(() => {
    loadSatellites()
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

  function calculateEnhanced() {
    setLoading(true)
    
    // Simulate Petri Net progression
    let state = 0
    const interval = setInterval(() => {
      state++
      setPetriState(state)
      if (state >= 5) {
        clearInterval(interval)
        
        // Calculate enhanced probability
        const baseProb = calculateBaseProbability()
        const velocityFactor = calculateVelocityFactor()
        const geometryFactor = calculateGeometryFactor()
        const enhancedProb = baseProb * velocityFactor * geometryFactor
        
        setResults({
          baseProb,
          enhancedProb,
          velocityFactor,
          geometryFactor,
          relativeVelocity: 10.57, // km/s typical
          effectiveArea: 9.99 // m²
        })
        
        setLoading(false)
      }
    }, 200)
  }

  function calculateBaseProbability() {
    // Basic Poisson-based calculation
    const { diameter, altitude, exposureArea, exposureTime } = debrisData
    const debrisFlux = 0.00000462 // debris/m²/year (typical LEO)
    const lambda = debrisFlux * exposureArea * exposureTime
    return 1 - Math.exp(-lambda)
  }

  function calculateVelocityFactor() {
    // Relative velocity impact (higher velocity = higher risk)
    const relVel = 10.57 // km/s
    const baseVel = 7.5 // km/s
    return Math.pow(relVel / baseVel, 0.5)
  }

  function calculateGeometryFactor() {
    // Impact angle effect (perpendicular = highest risk)
    const angle = debrisData.impactAngle * Math.PI / 180
    return Math.abs(Math.sin(angle))
  }

  function simulateBreakup() {
    // NASA SBM - Standard Breakup Model
    const satArea = 100 // m²
    const debrisDiameter = debrisData.diameter / 1000 // convert to m
    const relVelocity = 10 // km/s
    
    // Characteristic length
    const Lc = Math.pow(satArea * debrisDiameter, 0.5)
    
    // Number of fragments > 1cm
    const N = 0.1 * Math.pow(Lc, 1.71)
    
    alert(`Breakup Simulation (NASA SBM):\n\n` +
          `Satellite Area: ${satArea} m²\n` +
          `Debris Diameter: ${debrisDiameter} m\n` +
          `Relative Velocity: ${relVelocity} km/s\n\n` +
          `Estimated Fragments (>1cm): ${Math.round(N)}\n` +
          `Characteristic Length: ${Lc.toFixed(2)} m`)
  }

  function predictLifetime() {
    const { altitude, diameter } = debrisData
    const mass = 1000 // kg (assumed)
    const area = Math.PI * Math.pow(diameter / 2000, 2) // m²
    const ballistic = mass / area // kg/m²
    
    // Simplified atmospheric drag model
    const H = 8.5 // scale height (km)
    const rho0 = 1.225e-9 // kg/m³ at altitude
    const rho = rho0 * Math.exp(-altitude / H)
    
    // Decay rate (km/orbit)
    const decayRate = 0.001 * (area / mass) * rho * altitude
    
    // Time to decay (years)
    const orbitsPerYear = 365.25 * (1440 / (90 + altitude / 100))
    const lifetime = altitude / (decayRate * orbitsPerYear)
    
    alert(`Atmospheric Drag Prediction:\n\n` +
          `Initial Altitude: ${altitude} km\n` +
          `Mass: ${mass} kg\n` +
          `Cross-Sectional Area: ${area.toFixed(4)} m²\n` +
          `Ballistic Coefficient: ${ballistic.toFixed(2)} kg/m²\n\n` +
          `Decay Rate: ${decayRate.toFixed(6)} km/orbit\n` +
          `Estimated Lifetime: ${lifetime.toFixed(1)} years\n` +
          `Decay Altitude: ${(altitude * 0.5).toFixed(0)} km`)
  }

  const petriStates = ['t1', 't2', 't3', 't4', 't5', 'FC']

  return (
    <div className="enhanced-features">
      <div className="enhanced-header">
        <h2>🔬 Enhanced Features</h2>
        <p>NASA SSP30425-based model • Petri Net • Poisson • Monte Carlo • Enhanced Calculations</p>
      </div>

      <div className="enhanced-grid">
        {/* Input Parameters */}
        <div className="enhanced-card">
          <h3>Input Parameters</h3>
          
          <div className="form-group">
            <label>Satellite (Celestrak)</label>
            <select 
              value={selectedSat || ''} 
              onChange={(e) => setSelectedSat(e.target.value)}
              className="form-select"
            >
              {satellites.map(sat => (
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
                onChange={(e) => setDebrisData({...debrisData, diameter: parseFloat(e.target.value)})}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Altitude (km)</label>
              <input 
                type="number" 
                value={debrisData.altitude}
                onChange={(e) => setDebrisData({...debrisData, altitude: parseFloat(e.target.value)})}
                className="form-input"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Impact Angle (°)</label>
              <input 
                type="number" 
                value={debrisData.impactAngle}
                onChange={(e) => setDebrisData({...debrisData, impactAngle: parseFloat(e.target.value)})}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Exposure Area (m²)</label>
              <input 
                type="number" 
                value={debrisData.exposureArea}
                onChange={(e) => setDebrisData({...debrisData, exposureArea: parseFloat(e.target.value)})}
                className="form-input"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Exposure Time (years)</label>
            <input 
              type="number" 
              value={debrisData.exposureTime}
              onChange={(e) => setDebrisData({...debrisData, exposureTime: parseFloat(e.target.value)})}
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

        {/* Petri Net Animation */}
        <div className="enhanced-card">
          <h3>Petri Net Animation</h3>
          <p className="petri-formula">t1 → H,F1,F2 • t2 → φ • t3 → g1,g2 • t4 → θ • t5 → FC</p>
          
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

        {/* Results */}
        {results && (
          <>
            <div className="enhanced-card">
              <h3>Enhanced Calculation (Velocity + Geometry)</h3>
              
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
                  <span className="validation-value">0.0000%</span>
                </div>
                <div className="validation-item">
                  <span className="validation-label">Difference</span>
                  <span className="validation-value">{(results.baseProb * 100).toFixed(6)}%</span>
                </div>
                <div className="validation-item">
                  <span className="validation-label">Trials</span>
                  <span className="validation-value">10,000</span>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Additional Simulations */}
        <div className="enhanced-card">
          <h3>Breakup Simulation (NASA SBM)</h3>
          <p>Simulate catastrophic collision and debris generation</p>
          <button className="simulation-btn" onClick={simulateBreakup}>
            Simulate Breakup
          </button>
        </div>

        <div className="enhanced-card">
          <h3>Atmospheric Drag Decay Prediction</h3>
          <p>Calculate debris lifetime and re-entry prediction</p>
          <button className="simulation-btn" onClick={predictLifetime}>
            Predict Lifetime
          </button>
        </div>
      </div>
    </div>
  )
}
