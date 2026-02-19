import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const API_BASE = ''

const nodeStyle = (active) => ({
  width: '64px',
  height: '64px',
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontWeight: 700,
  fontSize: '1.1rem',
  background: active ? 'var(--accent)' : 'var(--bg-dark)',
  color: active ? 'var(--bg-dark)' : 'var(--text-muted)',
  border: `2px solid ${active ? 'var(--accent)' : 'var(--border)'}`,
})

export default function PetriNetAnimation({ payload, runTrigger }) {
  const [result, setResult] = useState(null)
  const [activeStep, setActiveStep] = useState(-1)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    if (!payload || !runTrigger) return
    setRunning(true)
    setActiveStep(-1)
    setResult(null)

    const steps = [0, 1, 2, 3, 4]
    let idx = 0

    const advance = () => {
      if (idx < steps.length) {
        setActiveStep(steps[idx])
        idx++
        setTimeout(advance, 600)
      } else {
        fetch(`${API_BASE}/petri-net`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
          .then((r) => r.json())
          .then((data) => {
            setResult(data)
            setActiveStep(-1)
            setRunning(false)
          })
          .catch(() => setRunning(false))
      }
    }
    setTimeout(advance, 300)
  }, [payload, runTrigger])

  const transitions = ['t1', 't2', 't3', 't4', 't5']

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{
        background: 'var(--bg-card)',
        borderRadius: '12px',
        padding: '1.5rem',
        border: '1px solid var(--border)',
      }}
    >
      <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>
        Petri Net Animation
      </h2>
      <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
        t1 → H,F1,F2 • t2 → φ • t3 → g1,g2 • t4 → θ • t5 → FC
      </p>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
          flexWrap: 'wrap',
          marginBottom: '1.5rem',
        }}
      >
        {transitions.map((t, i) => (
          <div key={t} style={{ display: 'flex', alignItems: 'center' }}>
            <motion.div
              style={nodeStyle(activeStep === i)}
              animate={activeStep === i ? { scale: [1, 1.1, 1] } : {}}
              transition={{ duration: 0.3 }}
            >
              {t}
            </motion.div>
            {i < 4 && (
              <div
                style={{
                  width: '24px',
                  height: '2px',
                  background: 'var(--border)',
                }}
              />
            )}
          </div>
        ))}
      </div>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
              gap: '1rem',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '0.85rem',
            }}
          >
            {['t1','t2','t3','t4','t5'].map((k) => {
              const v = result[k]
              if (!v || typeof v !== 'object') return null
              return (
                <div key={k} style={{ padding: '0.5rem', background: 'rgba(0,212,170,0.08)', borderRadius: '8px' }}>
                  <div style={{ color: 'var(--accent)', fontWeight: 600, marginBottom: '0.25rem' }}>{k}</div>
                  {Object.entries(v).map(([kk, vv]) => (
                    <div key={kk} style={{ color: 'var(--text-muted)' }}>
                      {kk}={Number(vv).toFixed(6)}
                    </div>
                  ))}
                </div>
              )
            })}
            {result.FC != null && (
              <div style={{ padding: '0.5rem', background: 'rgba(0,212,170,0.15)', borderRadius: '8px' }}>
                <div style={{ color: 'var(--accent)', fontWeight: 600 }}>FC</div>
                <div style={{ fontSize: '1.1rem' }}>{Number(result.FC).toFixed(8)}</div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {running && (
        <p style={{ color: 'var(--accent)', fontSize: '0.9rem', marginTop: '1rem' }}>
          Running model…
        </p>
      )}
    </motion.div>
  )
}
