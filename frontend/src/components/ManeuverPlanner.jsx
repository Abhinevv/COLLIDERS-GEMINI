import { useState } from 'react';
import { calculateManeuver, simulateManeuver } from '../api';

export default function ManeuverPlanner() {
  const [formData, setFormData] = useState({
    satellite_position: [6800, 0, 0],
    satellite_velocity: [0, 7.5, 0],
    debris_position: [6805, 10, 0],
    debris_velocity: [0, 7.4, 0]
  });
  const [maneuvers, setManeuvers] = useState(null);
  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async () => {
    setLoading(true);
    try {
      const data = await calculateManeuver(formData);
      setManeuvers(data);
      setSimulation(null);
    } catch (error) {
      console.error('Failed to calculate maneuvers:', error);
      alert('Failed to calculate maneuvers');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulate = async (maneuver) => {
    setLoading(true);
    try {
      const data = await simulateManeuver({
        position: formData.satellite_position,
        velocity: formData.satellite_velocity,
        delta_v_vector: maneuver.delta_v_vector,
        duration_hours: 24
      });
      setSimulation(data.simulation);
    } catch (error) {
      console.error('Failed to simulate maneuver:', error);
      alert('Failed to simulate maneuver');
    } finally {
      setLoading(false);
    }
  };

  const updatePosition = (type, index, value) => {
    const key = type === 'sat' ? 'satellite_position' : 'debris_position';
    const newPos = [...formData[key]];
    newPos[index] = parseFloat(value) || 0;
    setFormData({ ...formData, [key]: newPos });
  };

  const updateVelocity = (type, index, value) => {
    const key = type === 'sat' ? 'satellite_velocity' : 'debris_velocity';
    const newVel = [...formData[key]];
    newVel[index] = parseFloat(value) || 0;
    setFormData({ ...formData, [key]: newVel });
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>🚀 Maneuver Planner</h2>
      <p style={{ opacity: 0.7, marginBottom: '30px' }}>
        Calculate collision avoidance maneuvers and simulate their effects
      </p>

      <div style={{
        background: 'rgba(255, 255, 255, 0.05)',
        padding: '20px',
        borderRadius: '12px',
        marginBottom: '20px',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <h3>Input Parameters</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
          <div>
            <h4>🛰️ Satellite</h4>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', opacity: 0.7 }}>
                Position (X, Y, Z) km
              </label>
              <div style={{ display: 'flex', gap: '5px' }}>
                {formData.satellite_position.map((val, i) => (
                  <input
                    key={i}
                    type="number"
                    value={val}
                    onChange={(e) => updatePosition('sat', i, e.target.value)}
                    style={{
                      flex: 1,
                      padding: '8px',
                      background: 'rgba(0, 0, 0, 0.3)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '6px',
                      color: 'white'
                    }}
                  />
                ))}
              </div>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', opacity: 0.7 }}>
                Velocity (X, Y, Z) km/s
              </label>
              <div style={{ display: 'flex', gap: '5px' }}>
                {formData.satellite_velocity.map((val, i) => (
                  <input
                    key={i}
                    type="number"
                    step="0.1"
                    value={val}
                    onChange={(e) => updateVelocity('sat', i, e.target.value)}
                    style={{
                      flex: 1,
                      padding: '8px',
                      background: 'rgba(0, 0, 0, 0.3)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '6px',
                      color: 'white'
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          <div>
            <h4>🛸 Debris</h4>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', opacity: 0.7 }}>
                Position (X, Y, Z) km
              </label>
              <div style={{ display: 'flex', gap: '5px' }}>
                {formData.debris_position.map((val, i) => (
                  <input
                    key={i}
                    type="number"
                    value={val}
                    onChange={(e) => updatePosition('debris', i, e.target.value)}
                    style={{
                      flex: 1,
                      padding: '8px',
                      background: 'rgba(0, 0, 0, 0.3)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '6px',
                      color: 'white'
                    }}
                  />
                ))}
              </div>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', opacity: 0.7 }}>
                Velocity (X, Y, Z) km/s
              </label>
              <div style={{ display: 'flex', gap: '5px' }}>
                {formData.debris_velocity.map((val, i) => (
                  <input
                    key={i}
                    type="number"
                    step="0.1"
                    value={val}
                    onChange={(e) => updateVelocity('debris', i, e.target.value)}
                    style={{
                      flex: 1,
                      padding: '8px',
                      background: 'rgba(0, 0, 0, 0.3)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '6px',
                      color: 'white'
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        <button
          onClick={handleCalculate}
          disabled={loading}
          style={{
            padding: '12px 24px',
            background: loading ? '#666' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            border: 'none',
            borderRadius: '8px',
            color: 'white',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: '600'
          }}
        >
          {loading ? '⏳ Calculating...' : '🚀 Calculate Maneuvers'}
        </button>
      </div>

      {maneuvers && (
        <div>
          <h3>Maneuver Options</h3>
          <div style={{ display: 'grid', gap: '15px', marginBottom: '20px' }}>
            {maneuvers.options.map((maneuver, index) => {
              const isRecommended = maneuver.name === maneuvers.comparison.recommended.name;
              return (
                <div
                  key={index}
                  style={{
                    background: isRecommended ? 'rgba(0, 204, 136, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                    padding: '20px',
                    borderRadius: '12px',
                    border: isRecommended ? '2px solid #00cc88' : '1px solid rgba(255, 255, 255, 0.1)',
                    position: 'relative'
                  }}
                >
                  {isRecommended && (
                    <div style={{
                      position: 'absolute',
                      top: '15px',
                      right: '15px',
                      padding: '6px 12px',
                      background: '#00cc88',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: '700'
                    }}>
                      ⭐ RECOMMENDED
                    </div>
                  )}

                  <h4 style={{ margin: '0 0 15px 0' }}>{maneuver.name}</h4>
                  <p style={{ opacity: 0.7, marginBottom: '15px' }}>{maneuver.description}</p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px', marginBottom: '15px' }}>
                    <div>
                      <div style={{ opacity: 0.7, fontSize: '12px', marginBottom: '5px' }}>ΔV Magnitude</div>
                      <div style={{ fontSize: '18px', fontWeight: '600' }}>
                        {(maneuver.delta_v_magnitude * 1000).toFixed(2)} m/s
                      </div>
                    </div>

                    <div>
                      <div style={{ opacity: 0.7, fontSize: '12px', marginBottom: '5px' }}>Fuel Cost</div>
                      <div style={{ fontSize: '18px', fontWeight: '600' }}>
                        {maneuver.fuel_cost_estimate.fuel_mass_kg.toFixed(2)} kg
                      </div>
                    </div>

                    <div>
                      <div style={{ opacity: 0.7, fontSize: '12px', marginBottom: '5px' }}>Execution Time</div>
                      <div style={{ fontSize: '18px', fontWeight: '600' }}>
                        {maneuver.execution_time_minutes.toFixed(1)} min
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleSimulate(maneuver)}
                    disabled={loading}
                    style={{
                      padding: '10px 20px',
                      background: loading ? '#666' : '#667eea',
                      border: 'none',
                      borderRadius: '6px',
                      color: 'white',
                      cursor: loading ? 'not-allowed' : 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    📊 Simulate This Maneuver
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {simulation && (
        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <h3>Simulation Results</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <div>
              <div style={{ opacity: 0.7, fontSize: '12px', marginBottom: '5px' }}>Trajectory Points</div>
              <div style={{ fontSize: '20px', fontWeight: '600' }}>
                {simulation.original_trajectory.length}
              </div>
            </div>

            <div>
              <div style={{ opacity: 0.7, fontSize: '12px', marginBottom: '5px' }}>Duration</div>
              <div style={{ fontSize: '20px', fontWeight: '600' }}>
                {simulation.duration_hours} hours
              </div>
            </div>

            <div>
              <div style={{ opacity: 0.7, fontSize: '12px', marginBottom: '5px' }}>Max Separation</div>
              <div style={{ fontSize: '20px', fontWeight: '600' }}>
                {simulation.max_separation_km.toFixed(2)} km
              </div>
            </div>
          </div>

          <p style={{ marginTop: '15px', opacity: 0.7 }}>
            ✅ Maneuver successfully increases separation between satellite and debris
          </p>
        </div>
      )}
    </div>
  );
}
