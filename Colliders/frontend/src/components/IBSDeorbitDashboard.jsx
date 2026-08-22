import { useState, useEffect, useRef, useMemo } from 'react'

export default function IBSDeorbitDashboard() {
  const [simulationData, setSimulationData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Simulation playback state
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(true)
  const [playbackSpeed, setPlaybackSpeed] = useState(1) // 0.5x, 1x, 2x, 5x, 10x

  // Canvas ref for animated orbit view
  const canvasRef = useRef(null)
  const animationFrameRef = useRef(null)
  const lastFrameTimeRef = useRef(performance.now())

  // Editable mission parameters (with defaults)
  const [params, setParams] = useState({
    debris_mass_kg: 500,
    initial_altitude_km: 800,
    initial_speed_kms: 7.35,
    ion_beam_force_mN: 20.0,
    ion_mass_flow_rate_mg_s: 1.0,
    ion_exhaust_velocity_kms: 20.0,
    shepherd_mass_kg: 1500,
    drag_area_m2: 2.0,
    drag_coefficient_cd: 2.2,
  })

  // Fetch simulation data on mount
  useEffect(() => {
    fetchSimulation()
  }, [])

  async function fetchSimulation(customParams = null) {
    setLoading(true)
    setError(null)
    try {
      const payload = customParams || params
      const response = await fetch('http://localhost:5000/api/ibs-deorbit-simulation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!response.ok) {
        throw new Error(`Simulation failed with status ${response.status}`)
      }
      const data = await response.json()
      setSimulationData(data)
      setCurrentIndex(0)
      setIsPlaying(true)
    } catch (err) {
      console.error('Error loading IBS simulation:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Animation loop driving time stepping
  useEffect(() => {
    if (!simulationData || !isPlaying) return

    const timeSeries = simulationData.time_series
    if (!timeSeries || timeSeries.length === 0) return

    const animate = (now) => {
      const delta = now - lastFrameTimeRef.current
      // Update roughly every 30-50ms scaled by playback speed
      const stepInterval = 40 / playbackSpeed

      if (delta >= stepInterval) {
        lastFrameTimeRef.current = now
        setCurrentIndex((prev) => {
          if (prev >= timeSeries.length - 1) {
            setIsPlaying(false)
            return timeSeries.length - 1
          }
          return prev + 1
        })
      }
      animationFrameRef.current = requestAnimationFrame(animate)
    }

    lastFrameTimeRef.current = performance.now()
    animationFrameRef.current = requestAnimationFrame(animate)

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [simulationData, isPlaying, playbackSpeed])

  // Current step telemetry
  const currentStep = useMemo(() => {
    if (!simulationData || !simulationData.time_series) return null
    return simulationData.time_series[currentIndex] || simulationData.time_series[0]
  }, [simulationData, currentIndex])

  // Draw main orbital view on Canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !simulationData || !currentStep) return

    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height
    const centerX = width / 2
    const centerY = height / 2

    // Clear canvas with space backdrop
    ctx.clearRect(0, 0, width, height)

    // Background gradient
    const bgGrad = ctx.createRadialGradient(centerX, centerY, 50, centerX, centerY, width / 2)
    bgGrad.addColorStop(0, '#06101e')
    bgGrad.addColorStop(1, '#02060d')
    ctx.fillStyle = bgGrad
    ctx.fillRect(0, 0, width, height)

    // Orbital scale: Map Earth radius + 900km into canvas radius
    const maxRadiusKm = 6371 + (params.initial_altitude_km || 800) + 150
    const canvasMaxR = Math.min(width, height) * 0.44
    const kmToPx = canvasMaxR / maxRadiusKm

    const rEarthPx = 6371 * kmToPx
    const rInitialPx = (6371 + (params.initial_altitude_km || 800)) * kmToPx
    const rCurrentPx = (6371 + currentStep.altitude_km) * kmToPx
    const rReentryPx = (6371 + 100) * kmToPx

    // 1. Draw Grid Lines / Distance Circles
    ctx.strokeStyle = 'rgba(77, 163, 255, 0.08)'
    ctx.lineWidth = 1
    for (let alt = 200; alt <= 1000; alt += 200) {
      const rGrid = (6371 + alt) * kmToPx
      ctx.beginPath()
      ctx.arc(centerX, centerY, rGrid, 0, 2 * Math.PI)
      ctx.stroke()
    }

    // 2. Draw Re-entry Threshold (100 km) Dashed Red Circle
    ctx.beginPath()
    ctx.setLineDash([4, 4])
    ctx.strokeStyle = 'rgba(255, 68, 68, 0.4)'
    ctx.lineWidth = 1.5
    ctx.arc(centerX, centerY, rReentryPx, 0, 2 * Math.PI)
    ctx.stroke()
    ctx.setLineDash([])

    // 3. Draw Initial Orbit (800 km) Dashed Blue Circle
    ctx.beginPath()
    ctx.setLineDash([6, 6])
    ctx.strokeStyle = '#2979ff'
    ctx.lineWidth = 1.8
    ctx.arc(centerX, centerY, rInitialPx, 0, 2 * Math.PI)
    ctx.stroke()
    ctx.setLineDash([])

    // 4. Draw Decayed Orbit Spiral History up to Current Step
    const series = simulationData.time_series
    if (series && series.length > 0) {
      ctx.beginPath()
      ctx.strokeStyle = 'rgba(0, 230, 118, 0.3)'
      ctx.lineWidth = 1.5
      for (let i = 0; i <= currentIndex; i++) {
        const pt = series[i]
        const rPt = (6371 + pt.altitude_km) * kmToPx
        const thPt = pt.theta_rad || 0
        const px = centerX + rPt * Math.cos(thPt)
        const py = centerY + rPt * Math.sin(thPt)
        if (i === 0) ctx.moveTo(px, py)
        else ctx.lineTo(px, py)
      }
      ctx.stroke()
    }

    // 5. Draw Current Orbit (Solid Green Ring)
    ctx.beginPath()
    ctx.strokeStyle = '#00e676'
    ctx.lineWidth = 2.2
    ctx.shadowColor = '#00e676'
    ctx.shadowBlur = 8
    ctx.arc(centerX, centerY, rCurrentPx, 0, 2 * Math.PI)
    ctx.stroke()
    ctx.shadowBlur = 0

    // 6. Draw Earth Globe in Center
    const earthGrad = ctx.createRadialGradient(centerX - rEarthPx * 0.3, centerY - rEarthPx * 0.3, 5, centerX, centerY, rEarthPx)
    earthGrad.addColorStop(0, '#4fc3f7')
    earthGrad.addColorStop(0.5, '#0288d1')
    earthGrad.addColorStop(0.85, '#01579b')
    earthGrad.addColorStop(1, '#002f6c')

    ctx.save()
    ctx.beginPath()
    ctx.arc(centerX, centerY, rEarthPx, 0, 2 * Math.PI)
    ctx.fillStyle = earthGrad
    ctx.fill()

    // Atmosphere halo glow
    ctx.strokeStyle = 'rgba(100, 255, 218, 0.5)'
    ctx.lineWidth = 3
    ctx.shadowColor = 'rgba(100, 255, 218, 0.8)'
    ctx.shadowBlur = 15
    ctx.stroke()
    ctx.restore()

    // Earth Label
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 12px "Rajdhani", sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('EARTH', centerX, centerY - 4)
    ctx.font = '10px "Exo 2", sans-serif'
    ctx.fillStyle = '#81d4fa'
    ctx.fillText('R = 6371 km', centerX, centerY + 12)

    // 7. Calculate Debris and Shepherd Positions
    const theta = currentStep.theta_rad || 0
    const debrisX = centerX + rCurrentPx * Math.cos(theta)
    const debrisY = centerY + rCurrentPx * Math.sin(theta)

    // Shepherd orbits slightly ahead (e.g. +12 degrees lead angle)
    const leadAngle = theta + 0.22
    const shepherdX = centerX + rCurrentPx * Math.cos(leadAngle)
    const shepherdY = centerY + rCurrentPx * Math.sin(leadAngle)

    // 8. Draw Directed Ion Beam (Red Pulsing Beam from Shepherd to Debris)
    ctx.save()
    ctx.beginPath()
    ctx.moveTo(shepherdX, shepherdY)
    ctx.lineTo(debrisX, debrisY)
    ctx.strokeStyle = '#ff1744'
    ctx.lineWidth = 2.5
    ctx.shadowColor = '#ff1744'
    ctx.shadowBlur = 10
    ctx.stroke()

    // Draw Ion Beam particles / arrow
    const midX = (shepherdX + debrisX) / 2
    const midY = (shepherdY + debrisY) / 2
    ctx.fillStyle = '#ff5252'
    ctx.beginPath()
    ctx.arc(midX, midY, 3, 0, 2 * Math.PI)
    ctx.fill()
    ctx.restore()

    // 9. Draw Shepherd Spacecraft (Blue Square with Glow)
    ctx.save()
    ctx.fillStyle = '#00e5ff'
    ctx.shadowColor = '#00e5ff'
    ctx.shadowBlur = 12
    ctx.fillRect(shepherdX - 6, shepherdY - 6, 12, 12)
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 1.5
    ctx.strokeRect(shepherdX - 6, shepherdY - 6, 12, 12)
    ctx.restore()

    ctx.fillStyle = '#00e5ff'
    ctx.font = 'bold 10px "Exo 2", sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText('IBS Shepherd', shepherdX + 10, shepherdY - 6)

    // 10. Draw Debris Object (Yellow Dot with Pulse)
    ctx.save()
    ctx.beginPath()
    ctx.arc(debrisX, debrisY, 6, 0, 2 * Math.PI)
    ctx.fillStyle = '#ffd600'
    ctx.shadowColor = '#ffd600'
    ctx.shadowBlur = 15
    ctx.fill()
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 1.5
    ctx.stroke()
    ctx.restore()

    ctx.fillStyle = '#ffd600'
    ctx.font = 'bold 10px "Exo 2", sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText('Debris (500kg)', debrisX + 10, debrisY + 12)

  }, [simulationData, currentStep, currentIndex, params])

  if (loading && !simulationData) {
    return (
      <div className="dashboard-container" style={{ padding: '40px', textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto 20px' }}></div>
        <h2 style={{ color: '#4da3ff', fontFamily: 'Rajdhani, sans-serif', letterSpacing: '2px' }}>
          INITIALIZING ION BEAM SHEPHERD (IBS) SIMULATOR...
        </h2>
        <p style={{ color: '#888' }}>Integrating orbital decay equations of motion...</p>
      </div>
    )
  }

  if (error && !simulationData) {
    return (
      <div className="dashboard-container" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ color: '#ff5252', fontSize: '1.5rem', marginBottom: '16px' }}>❌ Simulation Error</div>
        <p style={{ color: '#ccc', marginBottom: '20px' }}>{error}</p>
        <button className="search-btn" onClick={() => fetchSimulation()}>🔄 Retry Simulation</button>
      </div>
    )
  }

  const summary = simulationData?.ibs_summary || {}
  const totalSteps = simulationData?.total_steps || 1
  const progressPct = totalSteps > 1 ? ((currentIndex / (totalSteps - 1)) * 100).toFixed(1) : 0

  return (
    <div className="dashboard-container" style={{ maxWidth: '1680px', margin: '0 auto', padding: '10px 20px' }}>
      
      {/* 1. Header / Title Bar */}
      <div className="header" style={{ marginBottom: '16px', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ textAlign: 'left' }}>
          <h1 style={{ fontSize: '1.8rem', margin: 0, letterSpacing: '4px', color: '#ffffff' }}>
            ⚡ ION BEAM SHEPHERD (IBS) DEORBIT SIMULATION
          </h1>
          <p style={{ margin: '4px 0 0', color: '#4da3ff', fontSize: '0.9rem', letterSpacing: '1px' }}>
            Non-contact Active Space Debris Removal via Plasma Momentum Transfer & Atmospheric Drag
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button 
            className="search-btn" 
            style={{ padding: '8px 16px', fontSize: '0.85rem', background: 'rgba(77, 163, 255, 0.2)', borderColor: '#4da3ff' }}
            onClick={() => fetchSimulation()}
          >
            🔄 Rerun Simulation
          </button>
        </div>
      </div>

      {/* 2. Main Dashboard Grid (Sidebar + Center Canvas) */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '16px', marginBottom: '16px' }}>
        
        {/* Left Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          
          {/* Mission Parameters Card */}
          <div className="stat-card" style={{ padding: '14px' }}>
            <h3 style={{ borderBottom: '1px solid rgba(77, 163, 255, 0.2)', paddingBottom: '6px', marginBottom: '10px', fontSize: '0.85rem' }}>
              🛠️ MISSION PARAMETERS
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.8rem' }}>
              <div><span style={{ color: '#888' }}>Debris Mass:</span> <strong style={{ color: '#f0f6ff' }}>{params.debris_mass_kg} kg</strong></div>
              <div><span style={{ color: '#888' }}>Shepherd Mass:</span> <strong style={{ color: '#f0f6ff' }}>{params.shepherd_mass_kg} kg</strong></div>
              <div><span style={{ color: '#888' }}>Initial Alt:</span> <strong style={{ color: '#f0f6ff' }}>{params.initial_altitude_km} km</strong></div>
              <div><span style={{ color: '#888' }}>Ion Force:</span> <strong style={{ color: '#ff5252' }}>{params.ion_beam_force_mN} mN</strong></div>
              <div><span style={{ color: '#888' }}>Mass Flow:</span> <strong style={{ color: '#f0f6ff' }}>{params.ion_mass_flow_rate_mg_s} mg/s</strong></div>
              <div><span style={{ color: '#888' }}>Exhaust Vel:</span> <strong style={{ color: '#f0f6ff' }}>{params.ion_exhaust_velocity_kms} km/s</strong></div>
              <div><span style={{ color: '#888' }}>Drag Area:</span> <strong style={{ color: '#f0f6ff' }}>{params.drag_area_m2} m²</strong></div>
              <div><span style={{ color: '#888' }}>Drag Cd:</span> <strong style={{ color: '#f0f6ff' }}>{params.drag_coefficient_cd}</strong></div>
            </div>
          </div>

          {/* Environment Card */}
          <div className="stat-card" style={{ padding: '14px' }}>
            <h3 style={{ borderBottom: '1px solid rgba(77, 163, 255, 0.2)', paddingBottom: '6px', marginBottom: '10px', fontSize: '0.85rem' }}>
              🌍 ENVIRONMENT
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.8rem' }}>
              <div><span style={{ color: '#888' }}>Earth Radius:</span> <strong style={{ color: '#f0f6ff' }}>6,371 km</strong></div>
              <div><span style={{ color: '#888' }}>Scale Height:</span> <strong style={{ color: '#f0f6ff' }}>8.5 km</strong></div>
              <div><span style={{ color: '#888' }}>Grav Parameter μ:</span> <strong style={{ color: '#f0f6ff' }}>3.986e14</strong></div>
              <div><span style={{ color: '#888' }}>Sea-Level ρ₀:</span> <strong style={{ color: '#f0f6ff' }}>1.225 kg/m³</strong></div>
            </div>
          </div>

          {/* Live Simulation Status */}
          <div className="stat-card" style={{ padding: '14px', border: '1px solid rgba(0, 230, 118, 0.3)', background: 'rgba(4, 16, 28, 0.95)' }}>
            <h3 style={{ borderBottom: '1px solid rgba(0, 230, 118, 0.3)', paddingBottom: '6px', marginBottom: '10px', color: '#00e676', fontSize: '0.85rem' }}>
              📡 SIMULATION STATUS (LIVE)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#aaa' }}>Elapsed Mission Time:</span>
                <strong style={{ color: '#00e5ff', fontFamily: 'monospace' }}>
                  {currentStep ? `${currentStep.elapsed_time_days.toFixed(2)} days` : '0.00 days'}
                </strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#aaa' }}>Altitude:</span>
                <strong style={{ color: currentStep && currentStep.altitude_km <= 150 ? '#ff5252' : '#00e676', fontSize: '1rem' }}>
                  {currentStep ? `${currentStep.altitude_km.toFixed(1)} km` : '800.0 km'}
                </strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#aaa' }}>Orbital Speed:</span>
                <strong style={{ color: '#f0f6ff', fontFamily: 'monospace' }}>
                  {currentStep ? `${currentStep.speed_kms.toFixed(3)} km/s` : '7.456 km/s'}
                </strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#aaa' }}>Range from Earth Center:</span>
                <strong style={{ color: '#f0f6ff', fontFamily: 'monospace' }}>
                  {currentStep ? `${currentStep.range_from_earth_center_km.toFixed(1)} km` : '7171.0 km'}
                </strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#aaa' }}>Atmospheric Density ρ:</span>
                <strong style={{ color: '#ffb74d', fontFamily: 'monospace' }}>
                  {currentStep ? `${currentStep.atmospheric_density_kg_m3.toExponential(2)} kg/m³` : '0.0'}
                </strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#aaa' }}>Timeline Progress:</span>
                <strong style={{ color: '#64ffda' }}>{progressPct}% ({currentIndex + 1}/{totalSteps})</strong>
              </div>
            </div>
          </div>

          {/* Deorbit Target Threshold Card */}
          <div className="stat-card" style={{ padding: '14px', background: 'rgba(255, 23, 68, 0.08)', border: '1px solid rgba(255, 23, 68, 0.3)' }}>
            <h3 style={{ color: '#ff5252', fontSize: '0.85rem', marginBottom: '8px' }}>
              🎯 DEORBIT TARGET (RE-ENTRY)
            </h3>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#ffffff' }}>100.0 km</div>
                <div style={{ fontSize: '0.75rem', color: '#aaa' }}>Karman Line Atmospheric Re-entry</div>
              </div>
              <div style={{
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: 'bold',
                background: currentStep && currentStep.altitude_km <= 100.1 ? 'rgba(0, 230, 118, 0.2)' : 'rgba(255, 152, 0, 0.2)',
                color: currentStep && currentStep.altitude_km <= 100.1 ? '#00e676' : '#ff9800',
                border: currentStep && currentStep.altitude_km <= 100.1 ? '1px solid #00e676' : '1px solid #ff9800'
              }}>
                {currentStep && currentStep.altitude_km <= 100.1 ? 'RE-ENTRY REACHED' : 'IN DESCENT'}
              </div>
            </div>
          </div>

        </div>

        {/* Center Main Animated Orbit View */}
        <div className="stat-card" style={{ padding: '16px', position: 'relative', display: 'flex', flexDirection: 'column', background: 'rgba(2, 6, 13, 0.95)' }}>
          
          <div style={{ position: 'relative', width: '100%', height: '480px', borderRadius: '8px', overflow: 'hidden' }}>
            <canvas
              ref={canvasRef}
              width={820}
              height={480}
              style={{ width: '100%', height: '100%', display: 'block' }}
            />

            {/* Top-Right HUD Readout */}
            <div style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              background: 'rgba(4, 10, 22, 0.85)',
              border: '1px solid rgba(0, 230, 118, 0.4)',
              borderRadius: '6px',
              padding: '10px 14px',
              backdropFilter: 'blur(4px)',
              pointerEvents: 'none'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#aaa', textTransform: 'uppercase' }}>Current Mission State</div>
              <div style={{ fontSize: '1.2rem', color: '#00e676', fontWeight: 'bold', fontFamily: 'monospace' }}>
                ALT: {currentStep ? currentStep.altitude_km.toFixed(1) : '800.0'} KM
              </div>
              <div style={{ fontSize: '0.85rem', color: '#00e5ff', fontFamily: 'monospace' }}>
                TIME: {currentStep ? currentStep.elapsed_time_days.toFixed(1) : '0.0'} DAYS
              </div>
            </div>

            {/* Bottom-Left Legend Box */}
            <div style={{
              position: 'absolute',
              bottom: '12px',
              left: '12px',
              background: 'rgba(4, 10, 22, 0.85)',
              border: '1px solid rgba(77, 163, 255, 0.25)',
              borderRadius: '6px',
              padding: '8px 12px',
              fontSize: '0.75rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              backdropFilter: 'blur(4px)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#ffd600' }}>🟡</span> <span>Debris Target ({params.debris_mass_kg} kg)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#00e5ff' }}>🟦</span> <span>IBS Shepherd Craft ({params.shepherd_mass_kg} kg)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#ff1744' }}>━►</span> <span>Directed Ion Beam ({params.ion_beam_force_mN} mN)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#00e676' }}>━━</span> <span>Decaying Orbit (Current: {currentStep ? currentStep.altitude_km.toFixed(0) : '800'} km)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#2979ff' }}>- -</span> <span>Initial Reference Orbit ({params.initial_altitude_km} km)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#ff5252' }}>- -</span> <span>Re-entry Threshold (100 km)</span>
              </div>
            </div>

            {/* Right Atmospheric Density Scale */}
            <div style={{
              position: 'absolute',
              bottom: '12px',
              right: '12px',
              background: 'rgba(4, 10, 22, 0.85)',
              border: '1px solid rgba(255, 183, 77, 0.3)',
              borderRadius: '6px',
              padding: '8px 12px',
              fontSize: '0.75rem',
              textAlign: 'right'
            }}>
              <div style={{ color: '#ffb74d', fontWeight: 'bold' }}>ATMOSPHERE DENSITY</div>
              <div style={{ fontFamily: 'monospace', color: '#ffffff', marginTop: '2px' }}>
                {currentStep ? currentStep.atmospheric_density_kg_m3.toExponential(2) : '1.63e-41'} kg/m³
              </div>
              <div style={{ fontSize: '0.7rem', color: '#888', marginTop: '2px' }}>
                Drag Accel: {currentStep ? currentStep.drag_acceleration_um_s2.toFixed(1) : '0.0'} μm/s²
              </div>
              <div style={{ fontSize: '0.7rem', color: '#ff5252', marginTop: '1px' }}>
                Ion Accel: {currentStep ? currentStep.ion_acceleration_um_s2.toFixed(1) : '40.0'} μm/s²
              </div>
            </div>

          </div>

          {/* Scrubber and Playback Bar */}
          <div style={{
            marginTop: '12px',
            padding: '10px 14px',
            background: 'rgba(4, 10, 22, 0.9)',
            border: '1px solid rgba(77, 163, 255, 0.3)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px'
          }}>
            {/* Play/Pause Button */}
            <button
              className="search-btn"
              style={{
                padding: '6px 14px',
                fontSize: '0.9rem',
                minWidth: '70px',
                background: isPlaying ? 'rgba(255, 152, 0, 0.2)' : 'rgba(0, 230, 118, 0.2)',
                borderColor: isPlaying ? '#ff9800' : '#00e676',
                color: isPlaying ? '#ff9800' : '#00e676'
              }}
              onClick={() => setIsPlaying(!isPlaying)}
            >
              {isPlaying ? '⏸ Pause' : '▶ Play'}
            </button>

            {/* Step Controls */}
            <button
              style={{ background: 'transparent', border: 'none', color: '#888', cursor: 'pointer', fontSize: '1rem' }}
              onClick={() => { setIsPlaying(false); setCurrentIndex(0); }}
              title="Jump to Start"
            >
              ⏮
            </button>
            <button
              style={{ background: 'transparent', border: 'none', color: '#888', cursor: 'pointer', fontSize: '1rem' }}
              onClick={() => { setIsPlaying(false); setCurrentIndex(p => Math.max(0, p - 1)); }}
              title="Step Back"
            >
              ◀
            </button>
            <button
              style={{ background: 'transparent', border: 'none', color: '#888', cursor: 'pointer', fontSize: '1rem' }}
              onClick={() => { setIsPlaying(false); setCurrentIndex(p => Math.min(totalSteps - 1, p + 1)); }}
              title="Step Forward"
            >
              ▶
            </button>
            <button
              style={{ background: 'transparent', border: 'none', color: '#888', cursor: 'pointer', fontSize: '1rem' }}
              onClick={() => { setIsPlaying(false); setCurrentIndex(totalSteps - 1); }}
              title="Jump to Re-entry"
            >
              ⏭
            </button>

            {/* Draggable Scrubber Slider */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <input
                type="range"
                min={0}
                max={Math.max(1, totalSteps - 1)}
                value={currentIndex}
                onChange={(e) => {
                  setIsPlaying(false)
                  setCurrentIndex(parseInt(e.target.value, 10))
                }}
                style={{
                  width: '100%',
                  accentColor: '#00e676',
                  cursor: 'pointer',
                  height: '6px'
                }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#888' }}>
                <span>Day 0.0 (800 km)</span>
                <span style={{ color: '#00e676', fontWeight: 'bold' }}>
                  {currentStep ? `Day ${currentStep.elapsed_time_days.toFixed(1)} (${currentStep.altitude_km.toFixed(0)} km)` : ''}
                </span>
                <span>Day {summary.estimated_deorbit_time_days || '97.4'} (100 km)</span>
              </div>
            </div>

            {/* Playback Speed Multipliers */}
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: '#888', marginRight: '4px' }}>Speed:</span>
              {[0.5, 1, 2, 5, 10].map((s) => (
                <button
                  key={s}
                  style={{
                    background: playbackSpeed === s ? 'rgba(77, 163, 255, 0.3)' : 'rgba(255, 255, 255, 0.05)',
                    border: playbackSpeed === s ? '1px solid #4da3ff' : '1px solid rgba(255, 255, 255, 0.1)',
                    color: playbackSpeed === s ? '#ffffff' : '#aaa',
                    padding: '3px 6px',
                    borderRadius: '3px',
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                  onClick={() => setPlaybackSpeed(s)}
                >
                  {s}x
                </button>
              ))}
            </div>

          </div>

        </div>

      </div>

      {/* 3. Bottom Row: Altitude vs Time Chart + Trajectory Plot + Elements & Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1.2fr', gap: '16px', marginBottom: '16px' }}>
        
        {/* Chart 1: Altitude vs Time */}
        <div className="stat-card" style={{ padding: '14px', position: 'relative' }}>
          <h3 style={{ fontSize: '0.85rem', marginBottom: '8px', color: '#4da3ff' }}>
            📉 ALTITUDE VS. TIME PROFILE
          </h3>
          <div style={{ height: '180px', position: 'relative' }}>
            {(() => {
              const pts = simulationData?.time_series || []
              if (pts.length < 2) return null
              
              const svgW = 400
              const svgH = 160
              const padX = 40
              const padY = 20

              const maxT = pts[pts.length - 1].elapsed_time_days || 100
              const minAlt = 0
              const maxAlt = params.initial_altitude_km || 800

              const scaleX = (t) => padX + (t / maxT) * (svgW - padX - 10)
              const scaleY = (a) => svgH - padY - ((a - minAlt) / (maxAlt - minAlt)) * (svgH - padY - 10)

              const pathD = pts.reduce((acc, p, idx) => {
                const x = scaleX(p.elapsed_time_days)
                const y = scaleY(p.altitude_km)
                return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`
              }, '')

              const reEntryY = scaleY(100)
              const curX = currentStep ? scaleX(currentStep.elapsed_time_days) : padX
              const curY = currentStep ? scaleY(currentStep.altitude_km) : scaleY(800)

              return (
                <svg viewBox={`0 0 ${svgW} ${svgH}`} style={{ width: '100%', height: '100%' }}>
                  {/* Grid lines */}
                  <line x1={padX} y1={padY} x2={padX} y2={svgH - padY} stroke="rgba(255,255,255,0.15)" />
                  <line x1={padX} y1={svgH - padY} x2={svgW - 10} y2={svgH - padY} stroke="rgba(255,255,255,0.15)" />

                  {/* 100 km Re-entry Line */}
                  <line x1={padX} y1={reEntryY} x2={svgW - 10} y2={reEntryY} stroke="#ff5252" strokeDasharray="3,3" strokeWidth="1.5" />
                  <text x={padX + 5} y={reEntryY - 4} fill="#ff5252" fontSize="9" fontFamily="sans-serif">Re-entry (100km)</text>

                  {/* Altitude Curve */}
                  <path d={pathD} fill="none" stroke="#00e676" strokeWidth="2.5" />

                  {/* Current Position Marker */}
                  <circle cx={curX} cy={curY} r="5" fill="#ffd600" stroke="#ffffff" strokeWidth="1.5" />
                  <line x1={curX} y1={padY} x2={curX} y2={svgH - padY} stroke="rgba(255, 214, 0, 0.4)" strokeDasharray="2,2" />

                  {/* Axis Labels */}
                  <text x={padX - 8} y={padY + 8} fill="#888" fontSize="8" textAnchor="end">{maxAlt}km</text>
                  <text x={padX - 8} y={reEntryY + 3} fill="#ff5252" fontSize="8" textAnchor="end">100km</text>
                  <text x={padX - 8} y={svgH - padY} fill="#888" fontSize="8" textAnchor="end">0km</text>
                  <text x={padX} y={svgH - 4} fill="#888" fontSize="8">Day 0</text>
                  <text x={svgW - 15} y={svgH - 4} fill="#888" fontSize="8" textAnchor="end">{maxT.toFixed(0)}d</text>
                </svg>
              )
            })()}
          </div>
        </div>

        {/* Chart 2: Top-Down X/Y Orbital Trajectory */}
        <div className="stat-card" style={{ padding: '14px', position: 'relative' }}>
          <h3 style={{ fontSize: '0.85rem', marginBottom: '8px', color: '#4da3ff' }}>
            🌀 ORBITAL TRAJECTORY (X/Y PROJECTION)
          </h3>
          <div style={{ height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {(() => {
              const pts = simulationData?.time_series || []
              if (pts.length < 2) return null
              const svgSize = 160
              const center = svgSize / 2
              const maxR = 6371 + (params.initial_altitude_km || 800)
              const scale = (svgSize * 0.44) / maxR

              const spiralD = pts.reduce((acc, p, idx) => {
                const px = center + p.x_km * scale
                const py = center - p.y_km * scale
                return idx === 0 ? `M ${px} ${py}` : `${acc} L ${px} ${py}`
              }, '')

              const curX = currentStep ? center + currentStep.x_km * scale : center
              const curY = currentStep ? center - currentStep.y_km * scale : center
              const rEarth = 6371 * scale

              return (
                <svg viewBox={`0 0 ${svgSize} ${svgSize}`} style={{ width: '160px', height: '160px' }}>
                  {/* Earth */}
                  <circle cx={center} cy={center} r={rEarth} fill="#0288d1" stroke="#4fc3f7" strokeWidth="1" />
                  
                  {/* Initial Orbit */}
                  <circle cx={center} cy={center} r={maxR * scale} fill="none" stroke="#2979ff" strokeDasharray="3,3" strokeWidth="1" />

                  {/* Spiral Path */}
                  <path d={spiralD} fill="none" stroke="rgba(0, 230, 118, 0.4)" strokeWidth="1" />

                  {/* Current Position */}
                  <circle cx={curX} cy={curY} r="4" fill="#ffd600" stroke="#ffffff" strokeWidth="1" />
                </svg>
              )
            })()}
          </div>
        </div>

        {/* Box 3: Orbital Elements & IBS Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          
          {/* Orbital Elements */}
          <div className="stat-card" style={{ padding: '12px' }}>
            <h3 style={{ fontSize: '0.8rem', marginBottom: '6px', color: '#64ffda' }}>
              🌐 OSCULATING ORBITAL ELEMENTS
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.78rem' }}>
              <div><span style={{ color: '#888' }}>Semi-Major Axis:</span> <strong style={{ color: '#f0f6ff' }}>{currentStep ? `${currentStep.semi_major_axis_km.toFixed(1)} km` : '—'}</strong></div>
              <div><span style={{ color: '#888' }}>Period:</span> <strong style={{ color: '#f0f6ff' }}>{currentStep ? `${currentStep.period_min.toFixed(2)} min` : '—'}</strong></div>
              <div><span style={{ color: '#888' }}>Eccentricity:</span> <strong style={{ color: '#f0f6ff', fontFamily: 'monospace' }}>{currentStep ? currentStep.eccentricity.toFixed(6) : '—'}</strong></div>
              <div><span style={{ color: '#888' }}>Energy:</span> <strong style={{ color: '#f0f6ff' }}>{currentStep ? `${currentStep.specific_energy_MJ_kg.toFixed(2)} MJ/kg` : '—'}</strong></div>
            </div>
          </div>

          {/* IBS Propulsion Summary */}
          <div className="stat-card" style={{ padding: '12px' }}>
            <h3 style={{ fontSize: '0.8rem', marginBottom: '6px', color: '#ffb74d' }}>
              ⚡ IBS PROPULSION SUMMARY
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.78rem' }}>
              <div><span style={{ color: '#888' }}>Acceleration:</span> <strong style={{ color: '#00e676' }}>{summary.acceleration_on_debris_um_s2 || '40.0'} μm/s²</strong></div>
              <div><span style={{ color: '#888' }}>Total Impulse:</span> <strong style={{ color: '#f0f6ff' }}>{summary.total_impulse_MNs || '0.168'} MN·s</strong></div>
              <div><span style={{ color: '#888' }}>Momentum Transfer:</span> <strong style={{ color: '#f0f6ff' }}>{summary.momentum_transfer_rate_mN || '20.0'} mN</strong></div>
              <div><span style={{ color: '#888' }}>Fuel Consumed:</span> <strong style={{ color: '#ffb74d' }}>{summary.total_fuel_consumed_kg || '8.41'} kg</strong></div>
            </div>
          </div>

        </div>

      </div>

      {/* 4. Bottom Status Bar */}
      <div style={{
        padding: '10px 18px',
        background: 'rgba(4, 10, 22, 0.95)',
        border: '1px solid rgba(77, 163, 255, 0.25)',
        borderRadius: '8px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '0.85rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ color: '#aaa' }}>STATUS:</span>
          <span style={{
            color: currentStep && currentStep.altitude_km <= 100.1 ? '#00e676' : '#64ffda',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: currentStep && currentStep.altitude_km <= 100.1 ? '#00e676' : '#64ffda' }}></span>
            {currentStep && currentStep.altitude_km <= 100.1 ? 'ATMOSPHERIC RE-ENTRY THRESHOLD REACHED' : 'ACTIVE CONTINUOUS SHEPHERDING IN PROGRESS'}
          </span>
        </div>

        <div style={{ color: '#f0f6ff' }}>
          <span style={{ color: '#888', marginRight: '6px' }}>ESTIMATED TIME TO RE-ENTRY:</span>
          <strong style={{ color: '#ffd600' }}>
            {summary.estimated_deorbit_time_days ? `${summary.estimated_deorbit_time_days} Days (~${summary.estimated_deorbit_time_years} Years)` : '97.4 Days'}
          </strong>
        </div>

        <div style={{ color: '#888', fontSize: '0.75rem' }}>
          * Simulation time is scaled for real-time visualization. Continuous thrust accelerates decay.
        </div>
      </div>

    </div>
  )
}
