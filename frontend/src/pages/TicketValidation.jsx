import { useState } from 'react';
import api from '../services/api';
import { QrCode, CheckCircle, XCircle } from 'lucide-react';

export default function TicketValidation() {
  const [codigo, setCodigo] = useState('');
  const [resultado, setResultado] = useState(null); // { message, estado, error: boolean }
  const [loading, setLoading] = useState(false);

  const handleValidar = async (e) => {
    e.preventDefault();
    if (!codigo.trim()) return;
    setLoading(true);
    setResultado(null);

    try {
      const res = await api.post('/tiquetes/validar', { codigo: codigo.trim() });
      setResultado({ message: res.data.message, estado: res.data.estado, error: false });
      setCodigo('');
    } catch (err) {
      setResultado({ 
        message: err.response?.data?.message || 'Error al validar tiquete.', 
        estado: err.response?.data?.estado || 'ERROR',
        error: true 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container animate-fade-in" style={{ maxWidth: '600px' }}>
      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
        <QrCode size={48} color="var(--color-teal-dark)" style={{ marginBottom: '1rem' }} />
        <h1 className="title-gradient" style={{ marginBottom: '1.5rem' }}>Validación de Ingreso</h1>
        
        <form onSubmit={handleValidar} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
          <input 
            type="text" 
            value={codigo}
            onChange={e => setCodigo(e.target.value)}
            placeholder="Ingresa el código del tiquete..."
            style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #ccc', fontSize: '1.1rem', textAlign: 'center' }}
            disabled={loading}
          />
          <button type="submit" className="btn btn-secondary" disabled={loading || !codigo.trim()}>
            {loading ? 'Validando...' : 'Validar Tiquete'}
          </button>
        </form>

        {resultado && (
          <div style={{ 
            padding: '1.5rem', 
            borderRadius: '0.5rem', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            gap: '1rem',
            background: resultado.error ? 'rgba(216, 67, 21, 0.1)' : 'rgba(0, 137, 123, 0.1)',
            color: resultado.error ? 'var(--color-coral-dark)' : 'var(--color-teal-dark)'
          }}>
            {resultado.error ? <XCircle size={32} /> : <CheckCircle size={32} />}
            <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{resultado.message}</span>
          </div>
        )}
      </div>
    </div>
  );
}
