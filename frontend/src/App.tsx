import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api, MOCK_MODE } from './api/client'
import { groupTriage } from './lib/triage'
import Invoices from './pages/Invoices'
import FixQueue from './pages/FixQueue'

export default function App() {
  const invoices = useQuery({ queryKey: ['invoices', {}], queryFn: () => api.invoices() })
  const stuck = invoices.data ? groupTriage(invoices.data).reduce((s, g) => s + g.rows.length, 0) : null

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="side-brand">
          HealthCode <span className="tick">Connect</span>
          <span className="side-sub">Practice billing</span>
        </div>

        <div className="side-group-label">Work</div>
        <NavLink to="/" end className={({ isActive }) => `side-link${isActive ? ' active' : ''}`}>
          Invoices
        </NavLink>
        <NavLink to="/fix" className={({ isActive }) => `side-link${isActive ? ' active' : ''}`}>
          Fix queue
          {stuck != null && (
            <span className={`side-badge ${stuck > 0 ? 'crit' : 'ok'}`}>{stuck > 0 ? stuck : '✓'}</span>
          )}
        </NavLink>

        <div className="side-foot">
          <span>
            <span className="side-dot" style={{ background: MOCK_MODE ? 'var(--overdue)' : 'var(--paid)' }} />
            Xero · {MOCK_MODE ? 'demo data' : 'connected'}
          </span>
          <span>
            <span className="side-dot" style={{ background: 'var(--overdue)' }} />
            Medserv · simulated
          </span>
          <span className="data-badge" style={{ alignSelf: 'flex-start' }}>4 Jul 2026</span>
        </div>
      </aside>

      <div className="content">
        <main className="page-wrap">
          <Routes>
            <Route path="/" element={<Invoices />} />
            <Route path="/fix" element={<FixQueue />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
