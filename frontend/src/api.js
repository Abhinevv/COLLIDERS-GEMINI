export const BASE = 'http://localhost:5000'

export async function getHealth() {
  const res = await fetch(`${BASE}/health`)
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`)
  return res.json()
}

export async function getSatellites() {
  const res = await fetch(`${BASE}/api/satellites`)
  if (!res.ok) throw new Error(`Get satellites failed: ${res.status}`)
  return res.json()
}

export async function getManagedSatellites() {
  const res = await fetch(`${BASE}/api/satellites/manage`)
  if (!res.ok) throw new Error(`Get managed satellites failed: ${res.status}`)
  return res.json()
}

export async function addManagedSatellite(payload) {
  const res = await fetch(`${BASE}/api/satellites/manage/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const txt = await res.text()
    throw new Error(`Add managed satellite failed: ${res.status} ${txt}`)
  }
  return res.json()
}

export async function getCatalogSatellites(query = '', limit = 8) {
  const params = new URLSearchParams({ limit: String(limit) })
  if (query.trim()) params.set('q', query.trim())
  const res = await fetch(`${BASE}/api/catalog/satellites?${params.toString()}`)
  if (!res.ok) throw new Error(`Get catalog satellites failed: ${res.status}`)
  return res.json()
}

export async function getDemoRiskScenarios() {
  const res = await fetch(`${BASE}/api/demo/risk_scenarios`)
  if (!res.ok) throw new Error(`Get demo risk scenarios failed: ${res.status}`)
  return res.json()
}

export async function postAnalyze(payload) {
  const res = await fetch(`${BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Analyze failed: ${res.status}`)
  return res.json()
}

export async function postVisualize(payload) {
  const res = await fetch(`${BASE}/api/visualize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Visualize failed: ${res.status}`)
  return res.json()
}

export async function postDebrisAnalyze(payload) {
  const res = await fetch(`${BASE}/api/debris_analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const txt = await res.text()
    throw new Error(`Debris analyze failed: ${res.status} ${txt}`)
  }
  return res.json()
}

export async function startDebrisJob(payload) {
  const res = await fetch(`${BASE}/api/debris_job`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const txt = await res.text()
    throw new Error(`Start job failed: ${res.status} ${txt}`)
  }
  return res.json()
}

export async function getDebrisJob(jobId) {
  const res = await fetch(`${BASE}/api/debris_job/${jobId}`)
  if (!res.ok) throw new Error(`Get job failed: ${res.status}`)
  return res.json()
}

export async function searchDebris(q) {
  const res = await fetch(`${BASE}/api/debris_search?q=${encodeURIComponent(q)}`)
  if (!res.ok) throw new Error(`Debris search failed: ${res.status}`)
  return res.json()
}

// Space-Track API endpoints
export async function searchSpaceDebris(type = 'debris', limit = 50) {
  const res = await fetch(`${BASE}/api/space_debris/search?type=${encodeURIComponent(type)}&limit=${limit}`)
  if (!res.ok) throw new Error(`Space debris search failed: ${res.status}`)
  return res.json()
}

export async function getHighRiskDebris(altitudeMin = 200, altitudeMax = 2000, limit = 50) {
  const res = await fetch(`${BASE}/api/space_debris/high_risk?altitude_min=${altitudeMin}&altitude_max=${altitudeMax}&limit=${limit}`)
  if (!res.ok) throw new Error(`Get high risk debris failed: ${res.status}`)
  return res.json()
}

export async function getRecentDebris(days = 30, limit = 50) {
  const res = await fetch(`${BASE}/api/space_debris/recent?days=${days}&limit=${limit}`)
  if (!res.ok) throw new Error(`Get recent debris failed: ${res.status}`)
  return res.json()
}

export async function getDebrisDetails(noradId) {
  const res = await fetch(`${BASE}/api/space_debris/${noradId}`)
  if (!res.ok) throw new Error(`Get debris details failed: ${res.status}`)
  return res.json()
}

export async function refreshSpaceDebris() {
  const res = await fetch(`${BASE}/api/space_debris/refresh`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error(`Refresh debris failed: ${res.status}`)
  return res.json()
}

export async function getDebrisTLE(noradId) {
  const res = await fetch(`${BASE}/api/space_debris/${noradId}/tle`)
  if (!res.ok) throw new Error(`Get debris TLE failed: ${res.status}`)
  return res.json()
}

export async function getRelevantDebrisForSatellite(satelliteId, limit = 50) {
  const res = await fetch(`${BASE}/api/satellite/${satelliteId}/relevant_debris?limit=${limit}`)
  if (!res.ok) throw new Error(`Get relevant debris failed: ${res.status}`)
  return res.json()
}

export default {
  BASE,
  getHealth,
  getSatellites,
  getManagedSatellites,
  addManagedSatellite,
  getCatalogSatellites,
  getDemoRiskScenarios,
  postAnalyze,
  postVisualize,
  postDebrisAnalyze,
  startDebrisJob,
  getDebrisJob,
  searchDebris,
  searchSpaceDebris,
  getHighRiskDebris,
  getRecentDebris,
  getDebrisDetails,
  refreshSpaceDebris,
  getDebrisTLE,
  getRelevantDebrisForSatellite
}

// Phase 2: Alerts API
export async function getAlerts(satelliteId = null, minRisk = null) {
  let url = `${BASE}/api/alerts`
  const params = new URLSearchParams()
  if (satelliteId) params.append('satellite_id', satelliteId)
  if (minRisk) params.append('min_risk_level', minRisk)
  if (params.toString()) url += `?${params.toString()}`
  
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Get alerts failed: ${res.status}`)
  return res.json()
}

export async function dismissAlert(alertId, notes = null) {
  const res = await fetch(`${BASE}/api/alerts/${alertId}/dismiss`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  })
  if (!res.ok) throw new Error(`Dismiss alert failed: ${res.status}`)
  return res.json()
}

export async function resolveAlert(alertId, notes = null) {
  const res = await fetch(`${BASE}/api/alerts/${alertId}/resolve`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  })
  if (!res.ok) throw new Error(`Resolve alert failed: ${res.status}`)
  return res.json()
}

export async function subscribeToAlerts(payload) {
  const res = await fetch(`${BASE}/api/alerts/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Subscribe to alerts failed: ${res.status}`)
  return res.json()
}

// Phase 2: Maneuver API
export async function calculateManeuver(payload) {
  const res = await fetch(`${BASE}/api/maneuver/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Calculate maneuver failed: ${res.status}`)
  return res.json()
}

export async function simulateManeuver(payload) {
  const res = await fetch(`${BASE}/api/maneuver/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Simulate maneuver failed: ${res.status}`)
  return res.json()
}
