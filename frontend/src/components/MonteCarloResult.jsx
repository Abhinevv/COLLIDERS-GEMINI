import { motion } from 'framer-motion'

const cardStyle = {
  background: 'var(--bg-card)',
  borderRadius: '12px',
  padding: '1.5rem',
  border: '1px solid var(--border)',
}

const gridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
  gap: '1rem',
}

const valueStyle = {
  fontSize: '1.5rem',
  fontWeight: 700,
  color: 'var(--accent)',
  fontFamily: 'JetBrains Mono, monospace',
}

const labelStyle = {
  fontSize: '0.85rem',
  color: 'var(--text-muted)',
  marginBottom: '0.25rem',
}

export default function MonteCarloResult({ data }) {
  if (!data) return null
  const { MonteCarloProbability, PoissonProbability, Trials, Difference } = data

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={cardStyle}
    >
      <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>
        Monte Carlo Validation
      </h2>
      <div style={gridStyle}>
        <div>
          <div style={labelStyle}>Poisson Probability</div>
          <div style={valueStyle}>
            {(PoissonProbability * 100).toFixed(4)}%
          </div>
        </div>
        <div>
          <div style={labelStyle}>Monte Carlo Probability</div>
          <div style={valueStyle}>
            {(MonteCarloProbability * 100).toFixed(4)}%
          </div>
        </div>
        <div>
          <div style={labelStyle}>Difference</div>
          <div style={{ ...valueStyle, fontSize: '1.25rem' }}>
            {(Difference * 100).toFixed(6)}%
          </div>
        </div>
        <div>
          <div style={labelStyle}>Trials</div>
          <div style={valueStyle}>{Trials.toLocaleString()}</div>
        </div>
      </div>
    </motion.div>
  )
}
