import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Calendar, Clock, Ticket } from 'lucide-react';

export default function Home() {
  const [funciones, setFunciones] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFunciones = async () => {
      try {
        const res = await api.get('/funciones');
        setFunciones(res.data);
      } catch (err) {
        console.error("Error cargando funciones:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchFunciones();
  }, []);

  if (loading) {
    return <div className="container" style={{ textAlign: 'center', marginTop: '4rem' }}><h2>Cargando cartelera caribeña...</h2></div>;
  }

  return (
    <div className="container animate-fade-in">
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }} className="title-gradient">Cartelera Tropical</h1>
        <p style={{ fontSize: '1.2rem', color: 'var(--color-teal-dark)' }}>Descubre las mejores películas bajo el sol caribeño</p>
      </div>

      <div className="grid grid-cols-3">
        {funciones.map(fn => (
          <div key={fn.id} className="glass-panel" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ height: '300px', width: '100%', overflow: 'hidden' }}>
              <img 
                src={fn.imagen_url} 
                alt={fn.titulo} 
                style={{ width: '100%', height: '100%', objectFit: 'cover', transition: 'transform 0.3s' }}
                onMouseOver={e => e.currentTarget.style.transform = 'scale(1.05)'}
                onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}
              />
            </div>
            <div style={{ padding: '1.5rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
              <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>{fn.titulo}</h3>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--color-teal-dark)' }}>
                <Calendar size={18} />
                <span>{new Date(fn.fecha_hora).toLocaleDateString()}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--color-teal-dark)' }}>
                <Clock size={18} />
                <span>{new Date(fn.fecha_hora).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                <span style={{ marginLeft: 'auto', fontWeight: 'bold' }}>{fn.duracion_minutos} min</span>
              </div>
              
              <div style={{ marginTop: 'auto', paddingTop: '1rem' }}>
                <Link to={`/funcion/${fn.id}/asientos`} style={{ textDecoration: 'none' }}>
                  <button className="btn btn-primary" style={{ width: '100%' }}>
                    <Ticket size={20} /> Comprar Entrada - ${fn.precio_base}
                  </button>
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {funciones.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <h3>No hay funciones programadas por el momento.</h3>
        </div>
      )}
    </div>
  );
}
