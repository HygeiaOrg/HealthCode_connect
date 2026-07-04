import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { MOCK_MODE } from './api/client'
import Overview from './pages/Overview'
import Invoices from './pages/Invoices'
import Compare from './pages/Compare'

function Settings() {
  return (
    <>
      <h1 className="page-title">Settings</h1>
      <p className="page-sub">Connections and practice details.</p>
      <div className="card">
        <div className="queue-item">
          <span className={`queue-count ${MOCK_MODE ? 'warn' : 'info'}`}>{MOCK_MODE ? '○' : '●'}</span>
          <span className="qtext">
            <b>Xero</b> · {MOCK_MODE ? 'not connected in demo mode; set VITE_API_URL to use the backend' : 'connected via backend custom connection'}
          </span>
        </div>
        <div className="queue-item">
          <span className="queue-count warn">○</span>
          <span className="qtext"><b>Semble</b> · integration planned; invoices arrive via Xero for now</span>
        </div>
        <div className="queue-item">
          <span className="queue-count warn">○</span>
          <span className="qtext"><b>Healthcode</b> · status tracking simulated from seed data in the demo</span>
        </div>
      </div>
    </>
  )
}

export default function App() {
  return (
    <>
      <header className="app-header">
        <span className="brand">
          HealthCode <span className="tick">Connect</span>
        </span>
        <nav className="app-nav" aria-label="Main">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
            Overview
          </NavLink>
          <NavLink to="/invoices" className={({ isActive }) => (isActive ? 'active' : '')}>
            Invoices
          </NavLink>
          <NavLink to="/compare" className={({ isActive }) => (isActive ? 'active' : '')}>
            Compare
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => (isActive ? 'active' : '')}>
            Settings
          </NavLink>
        </nav>
        <span className="data-badge">{MOCK_MODE ? 'Demo data · 4 Jul 2026' : 'Live · Xero demo company'}</span>
      </header>
      <main className="page-wrap">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/invoices" element={<Invoices />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  )
}
