export default function SatelliteList({ satellites, selected, onToggle }) {
  return (
    <div className="satellite-cards">
      {satellites.map(s => {
        const id = s.norad_id ?? s.id
        const isSelected = selected.includes(id)
        return (
          <div className="satellite-card" key={id}>
            <label className="satellite-checkbox-label">
              <input type="checkbox" checked={isSelected} onChange={() => onToggle(id)} />
            </label>
            <h3>{s.name ?? 'Unnamed'}</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">NORAD ID:</span>
                <span className="info-value">{id ?? 'Unknown'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Type:</span>
                <span className="info-value">{s.type ?? 'Unknown'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Description:</span>
                <span className="info-value">{s.description ?? '—'}</span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
