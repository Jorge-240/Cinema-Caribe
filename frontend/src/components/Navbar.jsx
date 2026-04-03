import { Link, useLocation } from 'react-router-dom';
import { Film, User } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();

  return (
    <nav className="navbar glass-panel">
      <div className="nav-content">
        <Link to="/" className="nav-logo">
          <Film size={28} color="var(--color-coral-main)" />
          <span className="title-gradient">Cinema Caribe</span>
        </Link>
        <div className="nav-links">
          <Link to="/" style={{ color: location.pathname === '/' ? 'var(--color-coral-main)' : '' }}>
            Cartelera
          </Link>
          <Link to="/admin" className="btn btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
            <User size={16} /> Admin
          </Link>
        </div>
      </div>
    </nav>
  );
}
