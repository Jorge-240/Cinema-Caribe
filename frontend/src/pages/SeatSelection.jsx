import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Armchair, CreditCard } from 'lucide-react';

export default function SeatSelection() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [asientos, setAsientos] = useState([]);
  const [seleccionados, setSeleccionados] = useState([]);
  const [funcion, setFuncion] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const defaultData = async () => {
      try {
        // Fetch funcion detail (from /api/funciones and filter local or add endpoint, we'll fetch all and find it for simplicity)
        const resFunc = await api.get('/funciones');
        const fn = resFunc.data.find(f => f.id === parseInt(id));
        setFuncion(fn);

        // Fetch asientos
        const resAsientos = await api.get(`/funciones/${id}/asientos`);
        setAsientos(resAsientos.data);
      } catch (err) {
        console.error("Error", err);
      } finally {
        setLoading(false);
      }
    };
    defaultData();
  }, [id]);

  const toggleAsiento = (asientoId) => {
    const asiento = asientos.find(a => a.id === asientoId);
    if (asiento.estado === 'ocupado') return;

    if (seleccionados.includes(asientoId)) {
      setSeleccionados(prev => prev.filter(a => a !== asientoId));
    } else {
      setSeleccionados(prev => [...prev, asientoId]);
    }
  };

  const btnContinuar = () => {
    if (seleccionados.length === 0) return alert('Selecciona al menos un asiento');
    // Save to state or localstorage to pass to checkout
    navigate('/checkout', { state: { funcion, seleccionados } });
  };

  if (loading || !funcion) return <div className="container" style={{ textAlign: 'center' }}><h2>Cargando asientos...</h2></div>;

  return (
    <div className="container animate-fade-in">
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 className="title-gradient">Selección de Asientos</h1>
        <h2 style={{ marginTop: '0.5rem' }}>{funcion.titulo}</h2>
        <p>Fecha: {new Date(funcion.fecha_hora).toLocaleString()}</p>
      </div>

      <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <div style={{ 
          background: 'linear-gradient(90deg, transparent, rgba(0,0,0,0.1), transparent)', 
          padding: '0.5rem', 
          textAlign: 'center', 
          marginBottom: '3rem',
          borderRadius: '0.5rem',
          boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <strong>PANTALLA</strong>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(15, 1fr)', gap: '0.5rem', justifyContent: 'center' }}>
          {asientos.map(asiento => (
            <button
              key={asiento.id}
              onClick={() => toggleAsiento(asiento.id)}
              disabled={asiento.estado === 'ocupado'}
              style={{
                padding: '0.5rem',
                border: 'none',
                borderRadius: '0.25rem',
                cursor: asiento.estado === 'ocupado' ? 'not-allowed' : 'pointer',
                background: asiento.estado === 'ocupado' 
                  ? 'var(--color-coral-dark)' 
                  : seleccionados.includes(asiento.id)
                    ? 'var(--color-teal-main)'
                    : 'var(--color-sand)',
                color: (asiento.estado === 'ocupado' || seleccionados.includes(asiento.id)) ? 'white' : 'var(--color-text)',
                transition: 'all 0.2s'
              }}
              title={asiento.id}
            >
              <Armchair size={16} />
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ width: '20px', height: '20px', background: 'var(--color-sand)' }}></div> <span>Disponible</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ width: '20px', height: '20px', background: 'var(--color-teal-main)' }}></div> <span>Seleccionado</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ width: '20px', height: '20px', background: 'var(--color-coral-dark)' }}></div> <span>Ocupado</span>
          </div>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ marginBottom: '0.5rem' }}>Resumen</h3>
          <p>Asientos: <strong>{seleccionados.join(', ') || 'Ninguno'}</strong></p>
          <p>Total: <strong style={{ fontSize: '1.25rem', color: 'var(--color-teal-dark)' }}>${(seleccionados.length * funcion.precio_base).toFixed(2)}</strong></p>
        </div>
        <button onClick={btnContinuar} className="btn btn-primary" disabled={seleccionados.length === 0}>
          Continuar Pago <CreditCard size={20} />
        </button>
      </div>
    </div>
  );
}
