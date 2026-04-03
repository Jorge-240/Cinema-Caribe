import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Lock, User } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.post('/login', { email, password });
      // Guardar token en localStorage
      localStorage.setItem('token', res.data.token);
      localStorage.setItem('usuario', JSON.stringify(res.data.usuario));
      // Redirigir al dashboard
      navigate('/admin');
    } catch (err) {
      setError(err.response?.data?.message || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container animate-fade-in" style={{ maxWidth: '400px', marginTop: '4rem' }}>
      <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center' }}>
        <div style={{ display: 'inline-flex', padding: '1rem', background: 'var(--color-bg)', borderRadius: '50%', color: 'var(--color-teal-dark)', marginBottom: '1.5rem' }}>
          <Lock size={32} />
        </div>
        
        <h2 className="title-gradient" style={{ marginBottom: '2rem' }}>Acceso Administrativo</h2>

        {error && (
          <div style={{ background: 'rgba(216, 67, 21, 0.1)', color: 'var(--color-coral-dark)', padding: '0.75rem', borderRadius: '0.5rem', marginBottom: '1.5rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ textAlign: 'left' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Email</label>
            <div style={{ position: 'relative' }}>
              <User size={18} style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', left: '1rem', color: '#666' }} />
              <input 
                type="email" 
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                style={{ width: '100%', padding: '0.75rem 1rem 0.75rem 2.5rem', borderRadius: '0.5rem', border: '1px solid #ccc' }}
                placeholder="admin@cinemacaribe.com"
              />
            </div>
          </div>
          
          <div style={{ textAlign: 'left' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Contraseña</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', left: '1rem', color: '#666' }} />
              <input 
                type="password" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                style={{ width: '100%', padding: '0.75rem 1rem 0.75rem 2.5rem', borderRadius: '0.5rem', border: '1px solid #ccc' }}
                placeholder="********"
              />
            </div>
          </div>

          <button type="submit" className="btn btn-secondary" style={{ marginTop: '1rem', width: '100%' }} disabled={loading}>
            {loading ? 'Iniciando...' : 'Ingresar'}
          </button>
        </form>
      </div>
    </div>
  );
}
