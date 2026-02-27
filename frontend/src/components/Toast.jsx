import { useState, useEffect } from 'react';

let toastCallback = null;

export function showToast(message, type = 'info') {
  if (toastCallback) {
    toastCallback(message, type);
  }
}

export default function Toast() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    toastCallback = (message, type) => {
      const id = Date.now();
      setToasts(prev => [...prev, { id, message, type }]);
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, 4000);
    };
    return () => { toastCallback = null; };
  }, []);

  const getColor = (type) => {
    switch (type) {
      case 'success': return '#00cc88';
      case 'error': return '#ff4444';
      case 'warning': return '#ffbb00';
      default: return '#667eea';
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'success': return '✓';
      case 'error': return '✗';
      case 'warning': return '⚠';
      default: return 'ℹ';
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      zIndex: 10000,
      display: 'flex',
      flexDirection: 'column',
      gap: '10px'
    }}>
      {toasts.map(toast => (
        <div
          key={toast.id}
          style={{
            background: 'rgba(0, 0, 0, 0.9)',
            padding: '15px 20px',
            borderRadius: '8px',
            border: `2px solid ${getColor(toast.type)}`,
            color: 'white',
            minWidth: '300px',
            maxWidth: '400px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
            animation: 'slideIn 0.3s ease-out'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '20px', color: getColor(toast.type) }}>
              {getIcon(toast.type)}
            </span>
            <span>{toast.message}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
