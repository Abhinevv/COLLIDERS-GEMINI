import { useState, useEffect, useRef, useMemo } from 'react'

export default function IBSDeorbitDashboard() {
  const [simulationData, setSimulationData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Full Debris Catalog state (826 objects)
  const [debrisCatalog, setDebrisCatalog] = useState([])
  const [selectedDebrisNorad, setSelectedDebrisNorad] = useState('')
  const [catalogSearch, setCatalogSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('ALL')

  // Simulation playback state
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(true)
  const [playbackSpeed, setPlaybackSpeed] = useState(1) // 0.5x, 1x, 2x, 5x, 10x

  // Canvas ref for animated orbit view
  const canvasRef = useRef(null)
  const animationFrameRef = useRef(null)
  const lastFrameTimeRef = useRef(performance.now())

  // Default Mission Parameters (matching reference specification)
  const [params, setParams] = useState({
    debris_name: 'Generic Space Debris',
    norad_id: null,
    debris_type: 'DEBRIS',
    rcs_size: 'MEDIUM',
    inclination_deg: 51.6,
    debris_mass_kg: 500,
    mass_estimated: false,
    based_on: null,
    initial_altitude_km: 800,
    initial_speed_kms: 7.35,
    ion_beam_force_mN: 20.0,
    ion_mass_flow_rate_mg_s: 1.00,
    ion_exhaust_velocity_kms: 20.0,
    shepherd_mass_kg: 1500,
    drag_area_m2: 2.0,
    drag_coefficient_cd: 2.2,
  })

  // Load complete debris catalog on mount
  useEffect(() => {
    loadFullDebrisCatalog()
    fetchSimulation()
  }, [])

  async function loadFullDebrisCatalog() {
    try {
      const res = await fetch('http://localhost:5000/api/space_debris/all')
      if (res.ok) {
        const data = await res.json()
        setDebrisCatalog(data.debris || data.recent_debris || [])
      } else {
        const fallbackRes = await fetch('http://localhost:5000/api/space_debris/recent?limit=2000')
        if (fallbackRes.ok) {
          const fallbackData = await fallbackRes.json()
          setDebrisCatalog(fallbackData.debris || fallbackData.recent_debris || [])
        }
      }
    } catch (err) {
      console.warn('Could not load full debris catalog:', err)
    }
  }

  async function fetchSimulation(customPayload = null) {
    setLoading(true)
    setError(null)
    setIsPlaying(false)
    try {
      const payload = customPayload || (selectedDebrisNorad ? { norad_id: selectedDebrisNorad } : params)
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
      if (data.mission_parameters) {
        setParams(prev => ({
          ...prev,
          ...data.mission_parameters
        }))
      }
      setCurrentIndex(0)
      setIsPlaying(true)
    } catch (err) {
      console.error('Error loading IBS simulation:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleSelectDebris(noradId) {
    setSelectedDebrisNorad(noradId)
    if (!noradId) {
      fetchSimulation({
        debris_mass_kg: 500,
        initial_altitude_km: 800,
        initial_speed_kms: 7.35,
        ion_beam_force_mN: 20.0,
        ion_mass_flow_rate_mg_s: 1.00,
        ion_exhaust_velocity_kms: 20.0,
        shepherd_mass_kg: 1500,
        drag_area_m2: 2.0,
        drag_coefficient_cd: 2.2,
      })
    } else {
      fetchSimulation({ norad_id: noradId })
    }
  }

  // Animation loop driving time stepping
  useEffect(() => {
    if (!simulationData || !isPlaying) return

    const timeSeries = simulationData.time_series
    if (!timeSeries || timeSeries.length === 0) return

    const animate = (now) => {
      const delta = now - lastFrameTimeRef.current
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

  // Filtered debris list for catalog picker
  const filteredDebris = useMemo(() => {
    let list = debrisCatalog

    if (categoryFilter !== 'ALL') {
      list = list.filter(d => {
        const typeStr = (d.type || '').toUpperCase()
        if (categoryFilter === 'FRAGMENT') return typeStr.includes('FRAG') || typeStr.includes('DEB')
        if (categoryFilter === 'ROCKET') return typeStr.includes('ROCKET') || typeStr.includes('R/B') || typeStr.includes('STAGE')
        if (categoryFilter === 'DEFUNCT') return typeStr.includes('DEFUNCT') || typeStr.includes('PAYLOAD') || typeStr.includes('SAT')
        return true
      })
    }

    if (catalogSearch.trim()) {
      const q = catalogSearch.toLowerCase()
      list = list.filter(d =>
        (d.name && d.name.toLowerCase().includes(q)) ||
        (d.norad_id && String(d.norad_id).includes(q)) ||
        (d.type && d.type.toLowerCase().includes(q))
      )
    }

    return list
  }, [debrisCatalog, catalogSearch, categoryFilter])

  // Draw main orbital view on Canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !simulationData || !currentStep) return

    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height
    const centerX = width / 2 - 20
    const centerY = height / 2

    // Clear canvas
    ctx.clearRect(0, 0, width, height)

    // Deep space background
    const bgGrad = ctx.createRadialGradient(centerX, centerY, 40, centerX, centerY, width * 0.6)
    bgGrad.addColorStop(0, '#040b18')
    bgGrad.addColorStop(0.6, '#02060e')
    bgGrad.addColorStop(1, '#000000')
    ctx.fillStyle = bgGrad
    ctx.fillRect(0, 0, width, height)

    // Scaling
    const initialAlt = params.initial_altitude_km || 800
    const maxRadiusKm = 6371 + Math.max(initialAlt, 800) + 120
    const canvasMaxR = Math.min(width, height) * 0.44
    const kmToPx = canvasMaxR / maxRadiusKm

    const rEarthPx = 6371 * kmToPx
    const rInitialPx = (6371 + initialAlt) * kmToPx
    const rCurrentPx = (6371 + currentStep.altitude_km) * kmToPx
    const rReentryPx = (6371 + 100) * kmToPx

    // 1. Distance Grid Circles
    ctx.strokeStyle = 'rgba(77, 163, 255, 0.07)'
    ctx.lineWidth = 1
    for (let alt = 200; alt <= 1000; alt += 200) {
      const rGrid = (6371 + alt) * kmToPx
      ctx.beginPath()
      ctx.arc(centerX, centerY, rGrid, 0, 2 * Math.PI)
      ctx.stroke()
    }

    // 2. Re-entry Threshold (100 km) Dashed Red Circle (#ff4d4d)
    ctx.beginPath()
    ctx.setLineDash([4, 4])
    ctx.strokeStyle = 'rgba(255, 77, 77, 0.6)'
    ctx.lineWidth = 1.5
    ctx.arc(centerX, centerY, rReentryPx, 0, 2 * Math.PI)
    ctx.stroke()
    ctx.setLineDash([])

    // 3. Initial Orbit Dashed Blue Circle (#4da3ff)
    ctx.beginPath()
    ctx.setLineDash([6, 6])
    ctx.strokeStyle = 'rgba(77, 163, 255, 0.7)'
    ctx.lineWidth = 1.8
    ctx.arc(centerX, centerY, rInitialPx, 0, 2 * Math.PI)
    ctx.stroke()
    ctx.setLineDash([])

    // 4. Decayed Orbit Spiral History (#3ddc84)
    const series = simulationData.time_series
    if (series && series.length > 0) {
      ctx.beginPath()
      ctx.strokeStyle = 'rgba(61, 220, 132, 0.3)'
      ctx.lineWidth = 1.4
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

    // 5. Current Decaying Orbit (Solid Green Ring #3ddc84)
    ctx.beginPath()
    ctx.strokeStyle = '#3ddc84'
    ctx.lineWidth = 2.2
    ctx.shadowColor = '#3ddc84'
    ctx.shadowBlur = 8
    ctx.arc(centerX, centerY, rCurrentPx, 0, 2 * Math.PI)
    ctx.stroke()
    ctx.shadowBlur = 0

    // 6. Earth Globe
    const earthGrad = ctx.createRadialGradient(centerX - rEarthPx * 0.3, centerY - rEarthPx * 0.3, 8, centerX, centerY, rEarthPx)
    earthGrad.addColorStop(0, '#4da3ff')
    earthGrad.addColorStop(0.3, '#1e3a8a')
    earthGrad.addColorStop(0.7, '#0f172a')
    earthGrad.addColorStop(1, '#020617')

    ctx.save()
    ctx.beginPath()
    ctx.arc(centerX, centerY, rEarthPx, 0, 2 * Math.PI)
    ctx.fillStyle = earthGrad
    ctx.fill()

    // Atmosphere Glow (#4da3ff)
    ctx.strokeStyle = 'rgba(77, 163, 255, 0.6)'
    ctx.lineWidth = 3
    ctx.shadowColor = 'rgba(77, 163, 255, 0.9)'
    ctx.shadowBlur = 16
    ctx.stroke()
    ctx.restore()

    // Earth Text
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 12px "Rajdhani", sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('EARTH', centerX, centerY - 4)
    ctx.font = '10px "Exo 2", sans-serif'
    ctx.fillStyle = '#8aafd4'
    ctx.fillText('R = 6371 km', centerX, centerY + 12)

    // 7. Debris and Shepherd Positions
    const theta = currentStep.theta_rad || 0
    const debrisX = centerX + rCurrentPx * Math.cos(theta)
    const debrisY = centerY + rCurrentPx * Math.sin(theta)

    const leadAngle = theta + 0.22
    const shepherdX = centerX + rCurrentPx * Math.cos(leadAngle)
    const shepherdY = centerY + rCurrentPx * Math.sin(leadAngle)

    // 8. Directed Ion Beam Vector (#ff4d4d)
    ctx.save()
    ctx.beginPath()
    ctx.moveTo(shepherdX, shepherdY)
    ctx.lineTo(debrisX, debrisY)
    ctx.strokeStyle = '#ff4d4d'
    ctx.lineWidth = 2.5
    ctx.shadowColor = '#ff4d4d'
    ctx.shadowBlur = 10
    ctx.stroke()

    // Plasma particle
    const pulseT = (Date.now() % 1000) / 1000
    const beamPulseX = shepherdX + (debrisX - shepherdX) * pulseT
    const beamPulseY = shepherdY + (debrisY - shepherdY) * pulseT
    ctx.fillStyle = '#ff8a80'
    ctx.beginPath()
    ctx.arc(beamPulseX, beamPulseY, 3, 0, 2 * Math.PI)
    ctx.fill()
    ctx.restore()

    // 9. Shepherd Spacecraft (#4da3ff)
    ctx.save()
    ctx.fillStyle = '#4da3ff'
    ctx.shadowColor = '#4da3ff'
    ctx.shadowBlur = 12
    ctx.fillRect(shepherdX - 6, shepherdY - 6, 12, 12)
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 1.5
    ctx.strokeRect(shepherdX - 6, shepherdY - 6, 12, 12)
    ctx.restore()

    ctx.fillStyle = '#4da3ff'
    ctx.font = 'bold 10px "Exo 2", sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText('IBS Shepherd', shepherdX + 10, shepherdY - 6)

    // 10. Debris Object (#ffaa33)
    ctx.save()
    ctx.beginPath()
    ctx.arc(debrisX, debrisY, 6, 0, 2 * Math.PI)
    ctx.fillStyle = '#ffaa33'
    ctx.shadowColor = '#ffaa33'
    ctx.shadowBlur = 15
    ctx.fill()
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 1.5
    ctx.stroke()
    ctx.restore()

    const labelName = params.debris_name ? params.debris_name.slice(0, 18) : 'Debris'
    ctx.fillStyle = '#ffaa33'
    ctx.font = 'bold 10px "Exo 2", sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(`${labelName} (${params.debris_mass_kg}kg)`, debrisX + 10, debrisY + 14)

    // 11. Right-side Atmospheric Density Colorbar
    const barX = width - 40
    const barY = 80
    const barW = 14
    const barH = 220

    const barGrad = ctx.createLinearGradient(barX, barY, barX, barY + barH)
    barGrad.addColorStop(0, '#0f172a')
    barGrad.addColorStop(0.35, '#1e3a8a')
    barGrad.addColorStop(0.7, '#ffaa33')
    barGrad.addColorStop(1, '#ff4d4d')

    ctx.fillStyle = barGrad
    ctx.fillRect(barX, barY, barW, barH)
    ctx.strokeStyle = 'rgba(77, 163, 255, 0.3)'
    ctx.strokeRect(barX, barY, barW, barH)

    ctx.fillStyle = '#8aafd4'
    ctx.font = '8px monospace'
    ctx.textAlign = 'left'
    ctx.fillText('1e-14', barX - 32, barY + 8)
    ctx.fillText('1e-8', barX - 26, barY + barH * 0.5)
    ctx.fillText('1e-2', barX - 26, barY + barH - 2)

    const logRho = Math.log10(Math.max(1e-14, currentStep.atmospheric_density_kg_m3))
    const normRho = Math.min(1, Math.max(0, (logRho - (-14)) / 12))
    const ptrY = barY + normRho * barH

    ctx.fillStyle = '#ffffff'
    ctx.beginPath()
    ctx.moveTo(barX - 4, ptrY)
    ctx.lineTo(barX - 10, ptrY - 4)
    ctx.lineTo(barX - 10, ptrY + 4)
    ctx.closePath()
    ctx.fill()

    ctx.fillStyle = '#ffaa33'
    ctx.font = 'bold 9px "Rajdhani", sans-serif'
    ctx.textAlign = 'center'
    ctx.save()
    ctx.translate(barX + 26, barY + barH / 2)
    ctx.rotate(Math.PI / 2)
    ctx.fillText('ATMOSPHERIC DENSITY (kg/m³)', 0, 0)
    ctx.restore()

  }, [simulationData, currentStep, currentIndex, params])

  if (loading && !simulationData) {
    return (
      <div className="dashboard-container" style={{ padding: '60px 20px', textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto 20px' }}></div>
        <h2 style={{ color: '#4da3ff', fontFamily: 'Rajdhani, sans-serif', letterSpacing: '3px' }}>
          INITIALIZING ION BEAM SHEPHERD (IBS) SIMULATION...
        </h2>
        <p style={{ color: '#8aafd4' }}>Integrating continuous thrust and atmospheric decay equations...</p>
      </div>
    )
  }

  if (error && !simulationData) {
    return (
      <div className="dashboard-container" style={{ padding: '60px 20px', textAlign: 'center' }}>
        <div style={{ color: '#ff4d4d', fontSize: '1.5rem', marginBottom: '16px' }}>❌ Simulation Error</div>
        <p style={{ color: '#8aafd4', marginBottom: '20px' }}>{error}</p>
        <button className="search-btn" onClick={() => fetchSimulation()}>🔄 Retry Simulation</button>
      </div>
    )
  }

  const summary = simulationData?.ibs_summary || {}
  const totalSteps = simulationData?.total_steps || 1

  return (
    <div className="dashboard-container">
      
      {/* 1. Header / Title Bar */}
      <div className="header">
        <h1>ION BEAM SHEPHERD (IBS) DEORBIT SIMULATION</h1>
        <p>Non-contact Active Space Debris Removal</p>
      </div>

      {/* 2. Main Top Grid: Left Sidebar + Center Orbit Canvas */}
      <div className="ibs-layout-grid">
        
        {/* Left Sidebar */}
        <div className="ibs-sidebar">
          
          {/* Debris Target Selector Card */}
          <div className="ibs-panel ibs-panel-target">
            <div className="ibs-panel-header">
              <span>🎯 SELECT TARGET DEBRIS</span>
              <span style={{ fontSize: '0.7rem', color: '#8aafd4' }}>
                {debrisCatalog.length} Total
              </span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {/* Search Filter Input */}
              <input
                type="text"
                className="ibs-search-input"
                placeholder="🔍 Filter by name or NORAD ID..."
                value={catalogSearch}
                onChange={(e) => setCatalogSearch(e.target.value)}
              />

              {/* Category Filter Pills */}
              <div className="ibs-filter-row">
                {[
                  { key: 'ALL', label: `All (${debrisCatalog.length})` },
                  { key: 'FRAGMENT', label: 'Fragments' },
                  { key: 'ROCKET', label: 'Rocket Bodies' },
                  { key: 'DEFUNCT', label: 'Defunct Sats' },
                ].map(cat => (
                  <button
                    key={cat.key}
                    type="button"
                    className={`ibs-filter-pill ${categoryFilter === cat.key ? 'active' : ''}`}
                    onClick={() => setCategoryFilter(cat.key)}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>

              {/* Comprehensive Dropdown List with all 826 debris */}
              <select
                className="ibs-select-input"
                value={selectedDebrisNorad}
                onChange={(e) => handleSelectDebris(e.target.value)}
              >
                <option value="">⚙️ Custom / Manual Parameters (800 km Default)</option>
                {filteredDebris.map((d) => {
                  const avgAlt = d.apogee_km && d.perigee_km ? Math.round((d.apogee_km + d.perigee_km) / 2) : (d.apogee_km || 800)
                  return (
                    <option key={d.norad_id} value={d.norad_id}>
                      {d.name} ({d.norad_id} • {d.type || 'DEBRIS'} • {avgAlt}km • {d.rcs_size || 'MED'})
                    </option>
                  )
                })}
              </select>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#8aafd4' }}>
                <span>Showing {filteredDebris.length} debris</span>
                {selectedDebrisNorad && (
                  <span style={{ color: '#4da3ff', cursor: 'pointer' }} onClick={() => handleSelectDebris('')}>
                    Reset to Default ↺
                  </span>
                )}
              </div>

              {/* Quick Select Chips for Featured Debris */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {[
                  { id: '44120', name: 'PSLV C-45 DEB' },
                  { id: '44858', name: 'PSLV R/B' },
                  { id: '28944', name: 'Resourcesat DEB' },
                  { id: '33760', name: 'Cosmos 2251' },
                ].map(item => (
                  <button
                    key={item.id}
                    type="button"
                    className={`ibs-chip-btn ${selectedDebrisNorad === item.id ? 'active' : ''}`}
                    onClick={() => handleSelectDebris(item.id)}
                  >
                    {item.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Box 1: Mission Parameters */}
          <div className="ibs-panel">
            <div className="ibs-panel-header">
              🛠️ MISSION PARAMETERS
            </div>
            <div className="ibs-panel-body">
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Target Object:</span>
                <strong style={{ color: '#ffaa33', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={params.debris_name}>
                  {params.debris_name}
                </strong>
              </div>
              {params.norad_id && (
                <div className="ibs-panel-row">
                  <span className="ibs-panel-label">NORAD ID:</span>
                  <strong style={{ color: '#4da3ff' }}>{params.norad_id}</strong>
                </div>
              )}
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Debris Mass:</span>
                <strong className="ibs-panel-value">
                  {params.debris_mass_kg} kg {params.mass_estimated ? '(RCS est.)' : ''}
                </strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Initial Altitude:</span>
                <strong className="ibs-panel-value">{params.initial_altitude_km.toFixed(1)} km</strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Inclination:</span>
                <strong className="ibs-panel-value">{params.inclination_deg.toFixed(1)}°</strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Initial Speed:</span>
                <strong className="ibs-panel-value">{params.initial_speed_kms.toFixed(3)} km/s</strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Ion Beam Force:</span>
                <strong style={{ color: '#ff4d4d' }}>{params.ion_beam_force_mN} mN</strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Shepherd Mass:</span>
                <strong className="ibs-panel-value">{params.shepherd_mass_kg} kg</strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Drag Area:</span>
                <strong className="ibs-panel-value">{params.drag_area_m2} m²</strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Drag Coeff (Cd):</span>
                <strong className="ibs-panel-value">{params.drag_coefficient_cd}</strong>
              </div>
            </div>
          </div>

          {/* Box 2: Environment */}
          <div className="ibs-panel">
            <div className="ibs-panel-header">
              🌍 ENVIRONMENT
            </div>
            <div className="ibs-panel-body">
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Earth Radius:</span>
                <strong className="ibs-panel-value">6,371 km</strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Grav Parameter (μ):</span>
                <strong className="ibs-panel-value" style={{ fontFamily: 'monospace' }}>3.986 × 10¹⁴ m³/s²</strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Sea-Level Density (ρ₀):</span>
                <strong className="ibs-panel-value">1.225 kg/m³</strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Scale Height (H):</span>
                <strong className="ibs-panel-value">8,500 m</strong>
              </div>
            </div>
          </div>

          {/* Box 3: Simulation Status (Live) */}
          <div className="ibs-panel ibs-panel-live">
            <div className="ibs-panel-header ibs-panel-header-live">
              📡 SIMULATION STATUS (LIVE)
            </div>
            <div className="ibs-panel-body">
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Elapsed Time:</span>
                <strong style={{ color: '#4da3ff', fontFamily: 'monospace' }}>
                  {currentStep ? `${currentStep.elapsed_time_days.toFixed(2)} days` : '0.00 days'}
                </strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Altitude:</span>
                <strong style={{ color: currentStep && currentStep.altitude_km <= 120 ? '#ff4d4d' : '#3ddc84', fontSize: '0.95rem' }}>
                  {currentStep ? `${currentStep.altitude_km.toFixed(1)} km` : `${params.initial_altitude_km.toFixed(1)} km`}
                </strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Orbital Speed:</span>
                <strong className="ibs-panel-value" style={{ fontFamily: 'monospace' }}>
                  {currentStep ? `${currentStep.speed_kms.toFixed(3)} km/s` : `${params.initial_speed_kms.toFixed(3)} km/s`}
                </strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Range from Center:</span>
                <strong className="ibs-panel-value" style={{ fontFamily: 'monospace' }}>
                  {currentStep ? `${currentStep.range_from_earth_center_km.toFixed(1)} km` : `${(6371 + params.initial_altitude_km).toFixed(1)} km`}
                </strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Atmospheric Density:</span>
                <strong style={{ color: '#ffaa33', fontFamily: 'monospace' }}>
                  {currentStep ? `${currentStep.atmospheric_density_kg_m3.toExponential(2)} kg/m³` : '0.0'}
                </strong>
              </div>
              <div className="ibs-panel-row">
                <span className="ibs-panel-label">Time Step Index:</span>
                <strong style={{ color: '#4da3ff' }}>{currentIndex + 1} / {totalSteps}</strong>
              </div>
            </div>
          </div>

          {/* Box 4: Deorbit Target */}
          <div className="ibs-panel ibs-panel-target-reentry">
            <div className="ibs-panel-header ibs-panel-header-danger">
              🎯 DEORBIT TARGET
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '1.15rem', fontWeight: 'bold', color: '#ffffff' }}>100.0 km</div>
                <div style={{ fontSize: '0.74rem', color: '#8aafd4' }}>Atmospheric Re-entry Threshold</div>
              </div>
              <div style={{
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '0.72rem',
                fontWeight: 'bold',
                background: currentStep && currentStep.altitude_km <= 100.1 ? 'rgba(61, 220, 132, 0.2)' : 'rgba(255, 170, 51, 0.2)',
                color: currentStep && currentStep.altitude_km <= 100.1 ? '#3ddc84' : '#ffaa33',
                border: currentStep && currentStep.altitude_km <= 100.1 ? '1px solid #3ddc84' : '1px solid #ffaa33'
              }}>
                {currentStep && currentStep.altitude_km <= 100.1 ? 'RE-ENTRY REACHED' : 'IN DESCENT'}
              </div>
            </div>
          </div>

        </div>

        {/* Center Main Animated Orbit View */}
        <div className="ibs-panel" style={{ padding: '14px', position: 'relative', display: 'flex', flexDirection: 'column' }}>
          
          <div className="ibs-canvas-wrapper">
            <canvas
              ref={canvasRef}
              width={860}
              height={480}
              style={{ width: '100%', height: '100%', display: 'block' }}
            />

            {/* Top-Left Legend Box */}
            <div className="ibs-legend-overlay">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#ffaa33', fontSize: '0.9rem' }}>🟡</span> <span>{params.debris_name} ({params.debris_mass_kg} kg)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#4da3ff', fontSize: '0.9rem' }}>🟦</span> <span>IBS Shepherd Craft ({params.shepherd_mass_kg} kg)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#ff4d4d', fontWeight: 'bold' }}>━►</span> <span>Directed Ion Beam ({params.ion_beam_force_mN} mN)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#3ddc84', fontWeight: 'bold' }}>━━</span> <span>Decaying Orbit ({currentStep ? currentStep.altitude_km.toFixed(0) : params.initial_altitude_km.toFixed(0)} km)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#4da3ff' }}>- -</span> <span>Initial Orbit ({params.initial_altitude_km.toFixed(0)} km)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#ff4d4d' }}>- -</span> <span>Re-entry Threshold (100 km)</span>
              </div>
            </div>

            {/* Top-Right Large Live HUD Readout */}
            <div className="ibs-hud-overlay">
              <div style={{ fontSize: '0.72rem', color: '#8aafd4', letterSpacing: '1px', textTransform: 'uppercase' }}>Live Mission Clock</div>
              <div style={{ fontSize: '1.3rem', color: '#3ddc84', fontWeight: 'bold', fontFamily: 'monospace' }}>
                ALT: {currentStep ? currentStep.altitude_km.toFixed(1) : params.initial_altitude_km.toFixed(1)} KM
              </div>
              <div style={{ fontSize: '1.05rem', color: '#4da3ff', fontFamily: 'monospace' }}>
                TIME: {currentStep ? currentStep.elapsed_time_days.toFixed(1) : '0.0'} DAYS
              </div>
            </div>

          </div>

          {/* Scrubber and Playback Bar */}
          <div className="ibs-scrubber-container">
            {/* Play/Pause Button */}
            <button
              className="search-btn"
              style={{
                padding: '6px 14px',
                fontSize: '0.85rem',
                minWidth: '76px',
                background: isPlaying ? 'rgba(255, 170, 51, 0.2)' : 'rgba(61, 220, 132, 0.2)',
                borderColor: isPlaying ? '#ffaa33' : '#3ddc84',
                color: isPlaying ? '#ffaa33' : '#3ddc84'
              }}
              onClick={() => setIsPlaying(!isPlaying)}
            >
              {isPlaying ? '⏸ Pause' : '▶ Play'}
            </button>

            {/* Step Controls */}
            <button
              className="ibs-btn-ctrl"
              onClick={() => { setIsPlaying(false); setCurrentIndex(0); }}
              title="Jump to Start"
            >
              ⏮
            </button>
            <button
              className="ibs-btn-ctrl"
              onClick={() => { setIsPlaying(false); setCurrentIndex(p => Math.max(0, p - 1)); }}
              title="Step Back"
            >
              ◀
            </button>
            <button
              className="ibs-btn-ctrl"
              onClick={() => { setIsPlaying(false); setCurrentIndex(p => Math.min(totalSteps - 1, p + 1)); }}
              title="Step Forward"
            >
              ▶
            </button>
            <button
              className="ibs-btn-ctrl"
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
                  accentColor: '#3ddc84',
                  cursor: 'pointer',
                  height: '6px'
                }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#8aafd4' }}>
                <span>Day 0.0 ({params.initial_altitude_km.toFixed(0)} km)</span>
                <span style={{ color: '#3ddc84', fontWeight: 'bold' }}>
                  {currentStep ? `Day ${currentStep.elapsed_time_days.toFixed(1)} (${currentStep.altitude_km.toFixed(0)} km)` : ''}
                </span>
                <span>Day {summary.estimated_deorbit_time_days || '97.4'} (100 km)</span>
              </div>
            </div>

            {/* Playback Speed Multipliers */}
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: '#8aafd4', marginRight: '2px' }}>Speed:</span>
              {[0.5, 1, 2, 5, 10].map((s) => (
                <button
                  key={s}
                  className={`ibs-speed-btn ${playbackSpeed === s ? 'active' : ''}`}
                  onClick={() => setPlaybackSpeed(s)}
                >
                  {s}x
                </button>
              ))}
            </div>

          </div>

        </div>

      </div>

      {/* 3. Bottom Row: 3 Panels */}
      <div className="ibs-bottom-grid">
        
        {/* Bottom-Left: Altitude vs Time Chart */}
        <div className="ibs-panel">
          <div className="ibs-panel-header">
            📉 ALTITUDE VS. TIME PROFILE
          </div>
          <div style={{ height: '175px', position: 'relative' }}>
            {(() => {
              const pts = simulationData?.time_series || []
              if (pts.length < 2) return null
              
              const svgW = 420
              const svgH = 160
              const padX = 42
              const padY = 16

              const maxT = pts[pts.length - 1].elapsed_time_days || 100
              const minAlt = 0
              const maxAlt = Math.max(800, params.initial_altitude_km || 800)

              const scaleX = (t) => padX + (t / maxT) * (svgW - padX - 10)
              const scaleY = (a) => svgH - padY - ((a - minAlt) / (maxAlt - minAlt)) * (svgH - padY - 10)

              const pathD = pts.reduce((acc, p, idx) => {
                const x = scaleX(p.elapsed_time_days)
                const y = scaleY(p.altitude_km)
                return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`
              }, '')

              const reEntryY = scaleY(100)
              const curX = currentStep ? scaleX(currentStep.elapsed_time_days) : padX
              const curY = currentStep ? scaleY(currentStep.altitude_km) : scaleY(params.initial_altitude_km)

              return (
                <svg viewBox={`0 0 ${svgW} ${svgH}`} style={{ width: '100%', height: '100%' }}>
                  {/* Grid lines */}
                  <line x1={padX} y1={padY} x2={padX} y2={svgH - padY} stroke="rgba(77,163,255,0.15)" />
                  <line x1={padX} y1={svgH - padY} x2={svgW - 10} y2={svgH - padY} stroke="rgba(77,163,255,0.15)" />

                  <line x1={padX} y1={reEntryY} x2={svgW - 10} y2={reEntryY} stroke="#ff4d4d" strokeDasharray="3,3" strokeWidth="1.5" />
                  <text x={padX + 6} y={reEntryY - 4} fill="#ff4d4d" fontSize="9" fontFamily="sans-serif">Re-entry Threshold (100 km)</text>

                  <path d={pathD} fill="none" stroke="#3ddc84" strokeWidth="2.5" />

                  <circle cx={curX} cy={curY} r="5" fill="#ffaa33" stroke="#ffffff" strokeWidth="1.5" />
                  <line x1={curX} y1={padY} x2={curX} y2={svgH - padY} stroke="rgba(255, 170, 51, 0.4)" strokeDasharray="2,2" />

                  <text x={padX - 6} y={padY + 6} fill="#8aafd4" fontSize="8" textAnchor="end">{maxAlt.toFixed(0)}km</text>
                  <text x={padX - 6} y={reEntryY + 3} fill="#ff4d4d" fontSize="8" textAnchor="end">100km</text>
                  <text x={padX - 6} y={svgH - padY} fill="#8aafd4" fontSize="8" textAnchor="end">0km</text>
                  <text x={padX} y={svgH - 2} fill="#8aafd4" fontSize="8">Day 0</text>
                  <text x={svgW - 12} y={svgH - 2} fill="#8aafd4" fontSize="8" textAnchor="end">{maxT.toFixed(1)}d</text>
                </svg>
              )
            })()}
          </div>
        </div>

        {/* Bottom-Center: Orbital Trajectory Top-View X/Y Plot */}
        <div className="ibs-panel">
          <div className="ibs-panel-header">
            🌀 ORBITAL TRAJECTORY (X/Y PROJECTION)
          </div>
          <div style={{ height: '175px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {(() => {
              const pts = simulationData?.time_series || []
              if (pts.length < 2) return null
              const svgSize = 160
              const center = svgSize / 2
              const maxR = 6371 + Math.max(800, params.initial_altitude_km || 800)
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
                  <line x1={0} y1={center} x2={svgSize} y2={center} stroke="rgba(77,163,255,0.12)" />
                  <line x1={center} y1={0} x2={center} y2={svgSize} stroke="rgba(77,163,255,0.12)" />

                  <circle cx={center} cy={center} r={rEarth} fill="#1e3a8a" stroke="#4da3ff" strokeWidth="1" />
                  
                  <circle cx={center} cy={center} r={(6371 + params.initial_altitude_km) * scale} fill="none" stroke="#4da3ff" strokeDasharray="3,3" strokeWidth="1" />

                  <path d={spiralD} fill="none" stroke="rgba(61, 220, 132, 0.4)" strokeWidth="1" />

                  <circle cx={curX} cy={curY} r="4" fill="#ffaa33" stroke="#ffffff" strokeWidth="1" />
                </svg>
              )
            })()}
          </div>
        </div>

        {/* Bottom-Right: Orbital Elements & IBS Summary Boxes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          
          {/* Orbital Elements */}
          <div className="ibs-panel">
            <div className="ibs-panel-header">
              🌐 OSCULATING ORBITAL ELEMENTS
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.76rem' }}>
              <div><span className="ibs-panel-label">Semi-Major Axis:</span> <strong className="ibs-panel-value">{currentStep ? `${currentStep.semi_major_axis_km.toFixed(1)} km` : '—'}</strong></div>
              <div><span className="ibs-panel-label">Period:</span> <strong className="ibs-panel-value">{currentStep ? `${currentStep.period_min.toFixed(2)} min` : '—'}</strong></div>
              <div><span className="ibs-panel-label">Eccentricity:</span> <strong className="ibs-panel-value" style={{ fontFamily: 'monospace' }}>{currentStep ? currentStep.eccentricity.toFixed(6) : '—'}</strong></div>
              <div><span className="ibs-panel-label">Specific Energy:</span> <strong className="ibs-panel-value">{currentStep ? `${currentStep.specific_energy_MJ_kg.toFixed(2)} MJ/kg` : '—'}</strong></div>
            </div>
          </div>

          {/* IBS Propulsion Summary */}
          <div className="ibs-panel">
            <div className="ibs-panel-header" style={{ color: '#ffaa33', borderBottomColor: 'rgba(255, 170, 51, 0.25)' }}>
              ⚡ ION BEAM SHEPHERD SUMMARY
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.76rem' }}>
              <div><span className="ibs-panel-label">Accel on Debris:</span> <strong style={{ color: '#3ddc84' }}>{summary.acceleration_on_debris_um_s2 || '40.0'} μm/s²</strong></div>
              <div><span className="ibs-panel-label">Total Impulse:</span> <strong className="ibs-panel-value">{summary.total_impulse_MNs || '0.168'} MN·s</strong></div>
              <div><span className="ibs-panel-label">Momentum Transfer:</span> <strong className="ibs-panel-value">{summary.momentum_transfer_rate_mN || '20.0'} mN</strong></div>
              <div><span className="ibs-panel-label">Fuel Consumed:</span> <strong style={{ color: '#ffaa33' }}>{summary.total_fuel_consumed_kg || '8.41'} kg</strong></div>
            </div>
          </div>

        </div>

      </div>

      {/* 4. Bottom Status Bar */}
      <div className="ibs-bottom-status-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ color: '#8aafd4' }}>STATUS:</span>
          <span style={{
            color: currentStep && currentStep.altitude_km <= 100.1 ? '#3ddc84' : '#4da3ff',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: currentStep && currentStep.altitude_km <= 100.1 ? '#3ddc84' : '#4da3ff' }}></span>
            {currentStep && currentStep.altitude_km <= 100.1 ? 'ATMOSPHERIC RE-ENTRY THRESHOLD REACHED' : 'ACTIVE CONTINUOUS SHEPHERDING IN PROGRESS'}
          </span>
        </div>

        <div style={{ color: '#f0f6ff' }}>
          <span style={{ color: '#8aafd4', marginRight: '6px' }}>ESTIMATED TIME TO RE-ENTRY:</span>
          <strong style={{ color: '#ffaa33' }}>
            {summary.estimated_deorbit_time_days ? `${summary.estimated_deorbit_time_days} Days (~${summary.estimated_deorbit_time_years} Years)` : '97.4 Days'}
          </strong>
        </div>

        <div style={{ color: '#8aafd4', fontSize: '0.74rem' }}>
          * Simulation time is scaled for interactive playback. Continuous thrust accelerates orbital decay.
        </div>
      </div>

    </div>
  )
}
