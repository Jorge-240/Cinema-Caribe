import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import SeatSelection from './pages/SeatSelection';
import Checkout from './pages/Checkout';
import AdminDashboard from './pages/AdminDashboard';
import TicketValidation from './pages/TicketValidation';
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        {/* Rutas Públicas */}
        <Route path="/" element={<Home />} />
        <Route path="/funcion/:id/asientos" element={<SeatSelection />} />
        <Route path="/checkout" element={<Checkout />} />
        <Route path="/admin/login" element={<Login />} />

        {/* Rutas Protegidas (Requieren Login/JWT) */}
        <Route element={<ProtectedRoute />}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/validar" element={<TicketValidation />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
