import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { BarChart3, Film, Ticket, LayoutDashboard, QrCode } from 'lucide-react';

export default function AdminDashboard() {
  const [metricas, setMetricas] = useState({ ventasTotales: 0, tiquetesVendidos: 0, peliculasActivas: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetricas = async () => {
      try {
        const res = await api.get('/metricas');
        setMetricas(res.data);
      } catch (err) {
        console.error("Error", err);
      } finally {
        setLoading(false);
      }
    };
    fetchMetricas();
  }, []);

  if (loading) return <div className="container" style={{ textAlign: 'center' }}><h2>Cargando panel...</h2></div>;

  return (
    <div className="container animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 className="title-gradient" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <LayoutDashboard /> Panel Administrativo
        </h1>
        <Link to="/admin/validar">
          <button className="btn btn-secondary">
            <QrCode size={20} /> Validar Tiquetes
          </button>
        </Link>
      </div>

      <div className="grid grid-cols-3" style={{ marginBottom: '3rem' }}>
        <div className="glass-panel" style={{ padding: '2rem', display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: '50%', color: 'var(--color-teal-dark)' }}>
            <BarChart3 size={32} />
          </div>
          <div>
            <p style={{ color: 'var(--color-text)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>Ventas Totales</p>
            <h2 style={{ fontSize: '2rem', margin: 0 }}>${parseFloat(metricas.ventasTotales).toFixed(2)}</h2>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '2rem', display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: '50%', color: 'var(--color-teal-dark)' }}>
            <Ticket size={32} />
          </div>
          <div>
            <p style={{ color: 'var(--color-text)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>Tiquetes Vendidos</p>
            <h2 style={{ fontSize: '2rem', margin: 0 }}>{metricas.tiquetesVendidos}</h2>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '2rem', display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: '50%', color: 'var(--color-teal-dark)' }}>
            <Film size={32} />
          </div>
          <div>
            <p style={{ color: 'var(--color-text)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>Películas en Cartelera</p>
            <h2 style={{ fontSize: '2rem', margin: 0 }}>{metricas.peliculasActivas}</h2>
          </div>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '2rem' }}>
        <h2 style={{ marginBottom: '1.5rem' }}>Opciones Administrativas V1</h2>
        <p>En la versión actual puedes consultar las métricas generales y validar los tiquetes que compran los usuarios utilizando el botón superior derecho.</p>
        <p style={{ marginTop: '1rem', color: 'var(--color-teal-main)' }}>Para próximas expansiones, aquí se agregará la interfaz gráfica para el CRUD de Películas y Programación de Funciones.</p>
      </div>
    </div>
  );
}
