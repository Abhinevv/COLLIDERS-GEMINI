import { useState, useEffect } from 'react';
import { getAlerts, dismissAlert, resolveAlert, subscribeToAlerts } from '../api';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showSubscribe, setShowSubscribe] = useState(false);
  const [subscribeForm, setSubscribeForm] = useState({
    email: '',
    satellite_ids: [],
    min_probability: 0.001
  });

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadAlerts = async () => {
    try {
      const data = await getAlerts();
      setAlerts(data.alerts || []);
    } catch (error) {
      console.error('Failed to load alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = async (alertId) => {
    try {
      await dismissAlert(alertId);
      loadAlerts();
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
    }
  };

  const handleResolve = async (alertId) => {
    try {
      await resolveAlert(alertId);
      loadAlerts();
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  const handleSubscribe = async (e) => {
    e.preventDefault();
    try {
      await subscribeToAlerts(subscribeForm);
      alert('Subscription created successfully!');
      setShowSubscribe(false);
      setSubscribeForm({ email: '', satellite_ids: [], min_probability: 0.001 });
    } catch (error) {
      console.error('Failed to subscribe:', error);
      alert('Failed to create subscription');
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'CRITICAL': return '#ff4444';
      case 'HIGH': return '#ff8800';
      case 'MODERATE': return '#ffbb00';
      case 'LOW': return '#00cc88';
      default: return '#666';
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div className="spinner"></div>
        <p>Loading alerts...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <div>
          <h2 style={{ margin: 0 }}>⚠️ Collision Alerts</h2>
          <p style={{ margin: '5px 0 0 0', opacity: 0.7 }}>
            {alerts.length} active alert{alerts.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => setShowSubscribe(!showSubscribe)}
          style={{
            padding: '12px 24px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            border: 'none',
            borderRadius: '8px',
            color: 'white',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '600'
          }}
        >
          🔔 Subscribe to Alerts
        </button>
      </div>

      {showSubscribe && (
        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          padding: '20px',
          borderRadius: '12px',
          marginBottom: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <h3>Subscribe to Alert Notifications</h3>
          <form onSubmit={handleSubscribe}>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Email</label>
              <input
                type="email"
                value={subscribeForm.email}
                onChange={(e) => setSubscribeForm({ ...subscribeForm, email: e.target.value })}
                required
                style={{
                  width: '100%',
                  padding: '10px',
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '6px',
                  color: 'white'
                }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>
                Minimum Probability Threshold
              </label>
              <input
                type="number"
                step="0.0001"
                value={subscribeForm.min_probability}
                onChange={(e) => setSubscribeForm({ ...subscribeForm, min_probability: parseFloat(e.target.value) })}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '6px',
                  color: 'white'
                }}
              />
            </div>
            <button
              type="submit"
              style={{
                padding: '10px 20px',
                background: '#00cc88',
                border: 'none',
                borderRadius: '6px',
                color: 'white',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              Subscribe
            </button>
          </form>
        </div>
      )}

      {alerts.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>✅</div>
          <h3>No Active Alerts</h3>
          <p style={{ opacity: 0.7 }}>All satellites are safe. No collision risks detected.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '20px' }}>
          {alerts.map((alert) => (
            <div
              key={alert.id}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                padding: '20px',
                borderRadius: '12px',
                border: `2px solid ${getRiskColor(alert.risk_level)}`,
                position: 'relative'
              }}
            >
              <div style={{
                position: 'absolute',
                top: '15px',
                right: '15px',
                padding: '6px 12px',
                background: getRiskColor(alert.risk_level),
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: '700'
              }}>
                {alert.risk_level}
              </div>

              <h3 style={{ margin: '0 0 15px 0' }}>
                🛰️ Satellite {alert.satellite_id} ↔️ 🛸 Debris {alert.debris_id}
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
                <div>
                  <div style={{ opacity: 0.7, fontSize: '12px', marginBottom: '5px' }}>Collision Probability</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: getRiskColor(alert.risk_level) }}>
                    {(alert.probability * 100).toFixed(4)}%
                  </div>
                </div>

                {alert.closest_distance_km && (
                  <div>
                    <div style={{ opacity: 0.7, fontSize: '12px', marginBottom: '5px' }}>Closest Distance</div>
                    <div style={{ fontSize: '20px', fontWeight: '600' }}>
                      {alert.closest_distance_km.toFixed(2)} km
                    </div>
                  </div>
                )}

                {alert.closest_approach_time && (
                  <div>
                    <div style={{ opacity: 0.7, fontSize: '12px', marginBottom: '5px' }}>Closest Approach</div>
                    <div style={{ fontSize: '14px' }}>
                      {new Date(alert.closest_approach_time).toLocaleString()}
                    </div>
                  </div>
                )}

                <div>
                  <div style={{ opacity: 0.7, fontSize: '12px', marginBottom: '5px' }}>Created</div>
                  <div style={{ fontSize: '14px' }}>
                    {new Date(alert.created_at).toLocaleString()}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={() => handleResolve(alert.id)}
                  style={{
                    padding: '10px 20px',
                    background: '#00cc88',
                    border: 'none',
                    borderRadius: '6px',
                    color: 'white',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  ✓ Resolve
                </button>
                <button
                  onClick={() => handleDismiss(alert.id)}
                  style={{
                    padding: '10px 20px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '6px',
                    color: 'white',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
