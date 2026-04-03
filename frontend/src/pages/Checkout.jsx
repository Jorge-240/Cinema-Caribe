import { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { CheckCircle, AlertCircle } from 'lucide-react';

export default function Checkout() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { funcion, seleccionados } = state || {};

  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState('');

  if (!funcion || !seleccionados) {
    return (
        <div className="container" style={{textAlign: 'center', marginTop: '3rem'}}>
            <h2>No hay datos de compra. Regresa al inicio.</h2>
            <Link to="/" className="btn btn-primary" style={{marginTop: '1rem'}}>Ir al Inicio</Link>
        </div>
    );
  }

  const handleCheckout = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const payload = {
        nombre_cliente: nombre,
        email_cliente: email,
        funcion_id: funcion.id,
        asientos: seleccionados,
        precio_pagado_por_asiento: funcion.precio_base
      };

      const res = await api.post('/tiquetes', payload);
      setSuccess(res.data.codigo);
    } catch (err) {
        if(err.response?.status === 409) {
            setError('Lo sentimos, uno de los asientos ha sido comprado por alguien más mientras completabas el pago. Por favor, vuelve a seleccionar asientos.');
        } else {
            setError(err.response?.data?.message || 'Error al procesar la compra.');
        }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="container animate-fade-in" style={{ textAlign: 'center', maxWidth: '600px' }}>
        <div className="glass-panel" style={{ padding: '3rem' }}>
          <CheckCircle size={64} color="var(--color-teal-main)" style={{ marginBottom: '1rem' }} />
          <h1 className="title-gradient" style={{ marginBottom: '1rem' }}>¡Compra Exitosa!</h1>
          <p style={{ fontSize: '1.2rem', marginBottom: '2rem' }}>Gracias por tu compra, {nombre}.</p>
          
          <div style={{ background: 'var(--color-bg)', padding: '1.5rem', borderRadius: '0.5rem', marginBottom: '2rem' }}>
            <h3 style={{ color: 'var(--color-teal-dark)', marginBottom: '0.5rem' }}>Código de tu Tiquete</h3>
            <p style={{ fontSize: '1.5rem', fontWeight: 'bold', letterSpacing: '2px', wordBreak: 'break-all' }}>{success}</p>
            <p style={{ fontSize: '0.9rem', color: 'var(--color-text)', marginTop: '0.5rem' }}>Presenta este código al ingresar a la sala.</p>
          </div>

          <Link to="/">
            <button className="btn btn-primary" style={{ width: '100%' }}>Volver a la Cartelera</button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container animate-fade-in">
      <h1 className="title-gradient" style={{ textAlign: 'center', marginBottom: '2rem' }}>Checkout Tropical</h1>
      
      <div className="grid grid-cols-2">
        <div className="glass-panel" style={{ padding: '2rem' }}>
          <h2 style={{ marginBottom: '1.5rem' }}>Resumen de Compra</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(0,0,0,0.1)', paddingBottom: '0.5rem' }}>
              <span>Película:</span>
              <strong>{funcion.titulo}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(0,0,0,0.1)', paddingBottom: '0.5rem' }}>
              <span>Fecha:</span>
              <strong>{new Date(funcion.fecha_hora).toLocaleString()}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(0,0,0,0.1)', paddingBottom: '0.5rem' }}>
              <span>Asientos ({seleccionados.length}):</span>
              <strong>{seleccionados.join(', ')}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '1rem' }}>
              <span style={{ fontSize: '1.2rem' }}>Total a pagar:</span>
              <strong style={{ fontSize: '1.5rem', color: 'var(--color-coral-dark)' }}>
                ${(seleccionados.length * funcion.precio_base).toFixed(2)}
              </strong>
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '2rem' }}>
          <h2 style={{ marginBottom: '1.5rem' }}>Datos del Cliente</h2>
          {error && (
            <div style={{ 
              padding: '1rem', 
              background: 'rgba(216, 67, 21, 0.1)', 
              color: 'var(--color-coral-dark)', 
              borderRadius: '0.5rem',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertCircle size={20} />
              {error}
            </div>
          )}
          <form onSubmit={handleCheckout} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Nombre Completo</label>
              <input 
                type="text" 
                required 
                value={nombre} 
                onChange={e => setNombre(e.target.value)} 
                style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid #ccc', fontFamily: 'inherit' }}
                placeholder="Ej. Carlos Pérez"
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Correo Electrónico</label>
              <input 
                type="email" 
                required 
                value={email} 
                onChange={e => setEmail(e.target.value)} 
                style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid #ccc', fontFamily: 'inherit' }}
                placeholder="carlos@ejemplo.com"
              />
            </div>
            
            <button 
              type="submit" 
              className="btn btn-secondary" 
              disabled={loading}
              style={{ marginTop: '1rem' }}
            >
              {loading ? 'Procesando...' : 'Pagar y Generar Tiquete'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
