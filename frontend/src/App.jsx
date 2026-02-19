import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import InputForm from './components/InputForm'
import CollisionGraph from './components/CollisionGraph'
import PetriNetAnimation from './components/PetriNetAnimation'
import MonteCarloResult from './components/MonteCarloResult'
import EnhancedCalculation from './components/EnhancedCalculation'
import BreakupSimulation from './components/BreakupSimulation'
import OrbitalDecay from './components/OrbitalDecay'
import SGP4Propagation from './components/SGP4Propagation'

const API_BASE = ''

const cardStyle = {
  background: 'var(--bg-card)',
  borderRadius: '12px',
  padding: '1.5rem',
  border: '1px solid var(--border)',
}

const gridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
  gap: '1rem',
}

export default function App() {
  const [calcResult, setCalcResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [graphPayload, setGraphPayload] = useState(null)
  const [petriPayload, setPetriPayload] = useState(null)
  const [petriTrigger, setPetriTrigger] = useState(0)
  const [monteCarloData, setMonteCarloData] = useState(null)
  const [activeTab, setActiveTab] = useState('basic')

  const handleCalculate = useCallback(async (payload) => {
    setLoading(true)
    setCalcResult(null)
    setMonteCarloData(null)
    try {
      const res = await fetch(`${API_BASE}/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      setCalcResult(data)
      setGraphPayload(payload)

      const mcRes = await fetch(`${API_BASE}/monte-carlo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload, trials: 10000 }),
      })
      const mcData = await mcRes.json()
      setMonteCarloData(mcData)
    } catch (e) {
      setCalcResult({ error: e.message })
    } finally {
      setLoading(false)
    }
  }, [])

  const handleRunPetriNet = useCallback((payload) => {
    setPetriPayload(payload)
    setPetriTrigger((t) => t + 1)
  }, [])

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        style={{ marginBottom: '2rem' }}
      >
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--accent)' }}>
          Space Debris Collision Probability Prediction
        </h1>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          NASA SSP30425-based model • Petri Net • Poisson • Monte Carlo • Enhanced Features
        </p>
      </motion.header>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', borderBottom: '1px solid var(--border)' }}>
        <button
          onClick={() => setActiveTab('basic')}
          style={{
            padding: '0.5rem 1rem',
            border: 'none',
            background: activeTab === 'basic' ? 'var(--accent)' : 'transparent',
            color: activeTab === 'basic' ? 'var(--bg-dark)' : 'var(--text-muted)',
            cursor: 'pointer',
            fontWeight: activeTab === 'basic' ? 600 : 400,
            borderRadius: '6px 6px 0 0',
          }}
        >
          Basic Calculation
        </button>
        <button
          onClick={() => setActiveTab('enhanced')}
          style={{
            padding: '0.5rem 1rem',
            border: 'none',
            background: activeTab === 'enhanced' ? 'var(--accent)' : 'transparent',
            color: activeTab === 'enhanced' ? 'var(--bg-dark)' : 'var(--text-muted)',
            cursor: 'pointer',
            fontWeight: activeTab === 'enhanced' ? 600 : 400,
            borderRadius: '6px 6px 0 0',
          }}
        >
          Enhanced Features
        </button>
      </div>

      {activeTab === 'basic' && (
        <>
          <InputForm
        onCalculate={handleCalculate}
        onRunPetriNet={handleRunPetriNet}
        loading={loading}
      />

      {calcResult && !calcResult.error && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          style={{ ...cardStyle, marginTop: '1.5rem' }}
        >
          <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>Results</h2>
          <div style={gridStyle}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Debris Flux FC</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent)', fontFamily: 'JetBrains Mono' }}>
                {Number(calcResult.DebrisFlux).toFixed(8)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Orbit Length</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent)', fontFamily: 'JetBrains Mono' }}>
                {Number(calcResult.OrbitLength).toFixed(0)} km
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Expected Collisions</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent)', fontFamily: 'JetBrains Mono' }}>
                {Number(calcResult.NTotal).toFixed(4)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>P₀ (no collision)</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent)', fontFamily: 'JetBrains Mono' }}>
                {(calcResult.P0 * 100).toFixed(4)}%
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Collision Probability Q</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent)', fontFamily: 'JetBrains Mono' }}>
                {(calcResult.Q * 100).toFixed(4)}%
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {calcResult?.error && (
        <div style={{ ...cardStyle, marginTop: '1rem', color: '#f87171' }}>
          Error: {calcResult.error}
        </div>
      )}

      <div style={{ marginTop: '1.5rem', display: 'grid', gap: '1.5rem' }}>
        <CollisionGraph payload={graphPayload} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem', alignItems: 'start' }}>
          <PetriNetAnimation payload={petriPayload} runTrigger={petriTrigger} />
          <MonteCarloResult data={monteCarloData} />
        </div>
      </div>
        </>
      )}

      {activeTab === 'enhanced' && (
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <EnhancedCalculation />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
            <BreakupSimulation />
            <OrbitalDecay />
          </div>
          <SGP4Propagation />
        </div>
      )}
    </div>
  )
}
